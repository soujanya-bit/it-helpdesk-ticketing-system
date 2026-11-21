from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ticket import Ticket, TicketPriority, TicketStatus
from app.models.ticket_history import (
    TicketHistory,
    TicketHistoryEvent,
)
from app.models.user import User, UserRole
from app.schemas.ticket import TicketCreate, TicketUpdate

# --------------------------------------------------
# AUTHORIZATION
# --------------------------------------------------


def ensure_ticket_access(
    ticket: Ticket,
    current_user: User,
) -> None:
    """
    Verify that a user is allowed to access a ticket.

    Employees: their own tickets.
    Agents: tickets assigned to them.
    Administrators: all tickets.

    Raises LookupError when access is denied.
    """

    if current_user.role == UserRole.ADMIN:
        return

    if (
        current_user.role == UserRole.EMPLOYEE
        and ticket.requester_id == current_user.id
    ):
        return

    if current_user.role == UserRole.AGENT and ticket.assignee_id == current_user.id:
        return

    raise LookupError("Ticket not found.")


# --------------------------------------------------
# TICKET HISTORY
# --------------------------------------------------


def _record_history(
    db: Session,
    ticket: Ticket,
    actor: User,
    event_type: TicketHistoryEvent,
    old_values: dict | None = None,
    new_values: dict | None = None,
) -> None:
    """Add an audit-history entry to the current transaction."""

    history = TicketHistory(
        ticket_id=ticket.id,
        actor_id=actor.id,
        event_type=event_type,
        old_values=old_values,
        new_values=new_values,
    )

    db.add(history)


# --------------------------------------------------
# CREATE TICKET
# --------------------------------------------------


def create_ticket(
    db: Session,
    requester: User,
    ticket_data: TicketCreate,
) -> Ticket:
    """Create a ticket and record its creation."""

    ticket = Ticket(
        requester_id=requester.id,
        subject=ticket_data.subject,
        description=ticket_data.description,
        category=ticket_data.category,
        priority=ticket_data.priority,
    )

    try:
        db.add(ticket)
        db.flush()

        _record_history(
            db=db,
            ticket=ticket,
            actor=requester,
            event_type=TicketHistoryEvent.CREATED,
            new_values={
                "subject": ticket.subject,
                "status": ticket.status.value,
                "priority": ticket.priority.value,
            },
        )

        db.commit()
        db.refresh(ticket)

        return ticket

    except Exception:
        db.rollback()
        raise


# --------------------------------------------------
# LIST TICKETS
# --------------------------------------------------


def list_tickets(
    db: Session,
    current_user: User,
    skip: int = 0,
    limit: int = 20,
    status: TicketStatus | None = None,
    priority: TicketPriority | None = None,
    category: str | None = None,
    search: str | None = None,
    assignee_id: UUID | None = None,
) -> list[Ticket]:
    """List tickets visible to the current user."""

    query = select(Ticket).order_by(Ticket.created_at.desc())

    # Apply role-based visibility first.
    if current_user.role == UserRole.EMPLOYEE:
        query = query.where(Ticket.requester_id == current_user.id)

    elif current_user.role == UserRole.AGENT:
        query = query.where(Ticket.assignee_id == current_user.id)

    elif current_user.role != UserRole.ADMIN:
        return []

    # Apply optional filters.
    if status is not None:
        query = query.where(Ticket.status == status)

    if priority is not None:
        query = query.where(Ticket.priority == priority)

    if category is not None:
        query = query.where(Ticket.category.ilike(f"%{category}%"))

    if search is not None:
        query = query.where(Ticket.subject.ilike(f"%{search}%"))

    # Only administrators can filter by arbitrary assignees.
    if assignee_id is not None:
        if current_user.role != UserRole.ADMIN:
            raise PermissionError("Only administrators can filter by assignee.")

        query = query.where(Ticket.assignee_id == assignee_id)

    query = query.offset(skip).limit(limit)

    return list(db.scalars(query).all())


# --------------------------------------------------
# GET SINGLE TICKET
# --------------------------------------------------


def get_ticket(
    db: Session,
    ticket_id: UUID,
    current_user: User,
) -> Ticket:
    """Retrieve a ticket after checking access permissions."""

    ticket = db.get(Ticket, ticket_id)

    if ticket is None:
        raise LookupError("Ticket not found.")

    ensure_ticket_access(ticket, current_user)

    return ticket


# --------------------------------------------------
# UPDATE TICKET DETAILS
# --------------------------------------------------


def update_ticket_details(
    db: Session,
    ticket: Ticket,
    actor: User,
    ticket_data: TicketUpdate,
) -> Ticket:
    """
    Update ticket details with role- and status-based permissions.

    Employees can edit their own tickets when status is:
    - open
    - waiting_on_employee

    Assigned agents can edit their tickets regardless of status.
    Administrators can edit any ticket regardless of status.
    """

    # Independently verify ticket access.
    ensure_ticket_access(ticket, actor)

    if actor.role == UserRole.EMPLOYEE:
        allowed_statuses = {
            TicketStatus.OPEN,
            TicketStatus.WAITING_ON_EMPLOYEE,
        }

        if ticket.status not in allowed_statuses:
            raise PermissionError(
                "Employees can only edit tickets that are open "
                "or waiting for their response."
            )

    changes = {
        key: value
        for key, value in ticket_data.model_dump(exclude_unset=True).items()
        if value is not None
    }

    if not changes:
        return ticket

    old_values = {field: getattr(ticket, field) for field in changes}

    try:
        for field, value in changes.items():
            setattr(ticket, field, value)

        new_values = {field: getattr(ticket, field) for field in changes}

        _record_history(
            db=db,
            ticket=ticket,
            actor=actor,
            event_type=TicketHistoryEvent.UPDATED,
            old_values=old_values,
            new_values=new_values,
        )

        db.commit()
        db.refresh(ticket)

        return ticket

    except Exception:
        db.rollback()
        raise


# --------------------------------------------------
# ASSIGN TICKET
# --------------------------------------------------


def assign_ticket(
    db: Session,
    ticket: Ticket,
    agent_id: UUID,
    actor: User,
) -> Ticket:
    """Assign a ticket to an active agent. Administrators only."""

    if actor.role != UserRole.ADMIN:
        raise PermissionError("Only administrators can assign tickets.")

    ensure_ticket_access(ticket, actor)

    agent = db.get(User, agent_id)

    if agent is None or not agent.is_active or agent.role != UserRole.AGENT:
        raise ValueError("The selected user is not an active agent.")

    old_assignee_id = ticket.assignee_id

    try:
        ticket.assignee_id = agent.id

        _record_history(
            db=db,
            ticket=ticket,
            actor=actor,
            event_type=TicketHistoryEvent.ASSIGNED,
            old_values={
                "assignee_id": (str(old_assignee_id) if old_assignee_id else None)
            },
            new_values={"assignee_id": str(agent.id)},
        )

        db.commit()
        db.refresh(ticket)

        return ticket

    except Exception:
        db.rollback()
        raise


# --------------------------------------------------
# UPDATE TICKET STATUS
# --------------------------------------------------


def update_ticket_status(
    db: Session,
    ticket: Ticket,
    new_status: TicketStatus,
    actor: User,
) -> Ticket:
    """Update ticket status and record the lifecycle event."""

    if actor.role not in (
        UserRole.AGENT,
        UserRole.ADMIN,
    ):
        raise PermissionError(
            "Only agents and administrators can change ticket status."
        )

    # Agents must be assigned to this ticket.
    ensure_ticket_access(ticket, actor)

    allowed_transitions = {
        TicketStatus.OPEN: {
            TicketStatus.IN_PROGRESS,
        },
        TicketStatus.IN_PROGRESS: {
            TicketStatus.WAITING_ON_EMPLOYEE,
            TicketStatus.RESOLVED,
        },
        TicketStatus.WAITING_ON_EMPLOYEE: {
            TicketStatus.IN_PROGRESS,
            TicketStatus.RESOLVED,
        },
        TicketStatus.RESOLVED: {
            TicketStatus.CLOSED,
            TicketStatus.IN_PROGRESS,
        },
        TicketStatus.CLOSED: set(),
    }

    current_status = ticket.status

    if new_status == current_status:
        raise ValueError("Ticket is already in the requested status.")

    if new_status not in allowed_transitions[current_status]:
        raise ValueError(
            f"Cannot transition ticket from "
            f"'{current_status.value}' to '{new_status.value}'."
        )

    now = datetime.now(UTC)

    old_values = {
        "status": current_status.value,
    }

    new_values = {
        "status": new_status.value,
    }

    event_type = TicketHistoryEvent.STATUS_CHANGED

    try:
        ticket.status = new_status

        if new_status == TicketStatus.RESOLVED:
            ticket.resolved_at = now
            event_type = TicketHistoryEvent.RESOLVED

        elif new_status == TicketStatus.CLOSED:
            ticket.closed_at = now
            event_type = TicketHistoryEvent.CLOSED

        elif new_status == TicketStatus.IN_PROGRESS:
            ticket.resolved_at = None
            ticket.closed_at = None

        _record_history(
            db=db,
            ticket=ticket,
            actor=actor,
            event_type=event_type,
            old_values=old_values,
            new_values=new_values,
        )

        db.commit()
        db.refresh(ticket)

        return ticket

    except Exception:
        db.rollback()
        raise


# --------------------------------------------------
# UPDATE TICKET PRIORITY
# --------------------------------------------------


def update_ticket_priority(
    db: Session,
    ticket: Ticket,
    new_priority: TicketPriority,
    actor: User,
) -> Ticket:
    """Update ticket priority and record the change."""

    if actor.role not in (
        UserRole.AGENT,
        UserRole.ADMIN,
    ):
        raise PermissionError(
            "Only agents and administrators can change ticket priority."
        )

    # Agents must be assigned to this ticket.
    ensure_ticket_access(ticket, actor)

    current_priority = ticket.priority

    if new_priority == current_priority:
        raise ValueError("Ticket already has the requested priority.")

    old_values = {
        "priority": current_priority.value,
    }

    new_values = {
        "priority": new_priority.value,
    }

    try:
        ticket.priority = new_priority

        _record_history(
            db=db,
            ticket=ticket,
            actor=actor,
            event_type=TicketHistoryEvent.PRIORITY_CHANGED,
            old_values=old_values,
            new_values=new_values,
        )

        db.commit()
        db.refresh(ticket)

        return ticket

    except Exception:
        db.rollback()
        raise


# --------------------------------------------------
# GET TICKET HISTORY
# --------------------------------------------------


def get_ticket_history(
    db: Session,
    ticket_id: UUID,
) -> list[TicketHistory]:
    """Return ticket history in chronological order."""

    query = (
        select(TicketHistory)
        .where(TicketHistory.ticket_id == ticket_id)
        .order_by(TicketHistory.created_at.asc())
    )

    return list(db.scalars(query).all())
