
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ticket import Ticket, TicketStatus
from app.models.user import User, UserRole
from app.models.ticket_history import (
    TicketHistory,
    TicketHistoryEvent,
)
from app.schemas.ticket import TicketCreate, TicketUpdate


def _record_history(
    db: Session,
    ticket: Ticket,
    actor: User,
    event_type: TicketHistoryEvent,
    old_values: dict | None = None,
    new_values: dict | None = None,
) -> None:
    history = TicketHistory(
        ticket_id=ticket.id,
        actor_id=actor.id,
        event_type=event_type,
        old_values=old_values,
        new_values=new_values,
    )
    db.add(history)


def create_ticket(
    db: Session,
    requester: User,
    ticket_data: TicketCreate,
) -> Ticket:
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
    query = select(Ticket).order_by(
        Ticket.created_at.desc()
    )

    # Enforce role-based visibility first.
    if current_user.role == UserRole.EMPLOYEE:
        query = query.where(
            Ticket.requester_id == current_user.id
        )

    elif current_user.role == UserRole.AGENT:
        query = query.where(
            Ticket.assignee_id == current_user.id
        )

    elif current_user.role != UserRole.ADMIN:
        return []

    # Apply optional filters.
    if status is not None:
        query = query.where(Ticket.status == status)

    if priority is not None:
        query = query.where(Ticket.priority == priority)

    if category is not None:
        query = query.where(
            Ticket.category.ilike(f"%{category}%")
        )

    if search is not None:
        query = query.where(
            Ticket.subject.ilike(f"%{search}%")
        )

    # Only administrators can filter by arbitrary assignees.
    if assignee_id is not None:
        if current_user.role != UserRole.ADMIN:
            raise PermissionError(
                "Only administrators can filter by assignee."
            )

        query = query.where(
            Ticket.assignee_id == assignee_id
        )

    query = query.offset(skip).limit(limit)

    return list(db.scalars(query).all())



def get_ticket(
    db: Session,
    ticket_id: UUID,
    current_user: User,
) -> Ticket:
    ticket = db.get(Ticket, ticket_id)

    if ticket is None:
        raise LookupError("Ticket not found.")

    if current_user.role == UserRole.ADMIN:
        return ticket

    if (
        current_user.role == UserRole.EMPLOYEE
        and ticket.requester_id == current_user.id
    ):
        return ticket

    if (
        current_user.role == UserRole.AGENT
        and ticket.assignee_id == current_user.id
    ):
        return ticket

    raise LookupError("Ticket not found.")


def update_ticket_details(
    db: Session,
    ticket: Ticket,
    actor: User,
    ticket_data: TicketUpdate,
) -> Ticket:
    changes = {
        key: value
        for key, value in ticket_data.model_dump(
            exclude_unset=True
        ).items()
        if value is not None
    }

    if not changes:
        return ticket

    old_values = {
        field: getattr(ticket, field)
        for field in changes
    }

    try:
        for field, value in changes.items():
            setattr(ticket, field, value)

        new_values = {
            field: getattr(ticket, field)
            for field in changes
        }

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


def assign_ticket(
    db: Session,
    ticket: Ticket,
    agent_id: UUID,
    actor: User,
) -> Ticket:
    agent = db.get(User, agent_id)

    if (
        agent is None
        or not agent.is_active
        or agent.role != UserRole.AGENT
    ):
        raise ValueError(
            "The selected user is not an active agent."
        )

    old_assignee_id = ticket.assignee_id

    try:
        ticket.assignee_id = agent.id

        _record_history(
            db=db,
            ticket=ticket,
            actor=actor,
            event_type=TicketHistoryEvent.ASSIGNED,
            old_values={
                "assignee_id": (
                    str(old_assignee_id)
                    if old_assignee_id else None
                )
            },
            new_values={
                "assignee_id": str(agent.id)
            },
        )

        db.commit()
        db.refresh(ticket)
        return ticket

    except Exception:
        db.rollback()
        raise


def update_ticket_status(
    db: Session,
    ticket: Ticket,
    new_status: TicketStatus,
    actor: User,
) -> Ticket:
    if actor.role not in (UserRole.AGENT, UserRole.ADMIN):
        raise PermissionError(
            "Only agents and administrators can change ticket status."
        )

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
        raise ValueError(
            "Ticket is already in the requested status."
        )

    if new_status not in allowed_transitions[current_status]:
        raise ValueError(
            f"Cannot transition ticket from "
            f"'{current_status.value}' to '{new_status.value}'."
        )

    now = datetime.now(timezone.utc)

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

def get_ticket_history(
    db: Session,
    ticket_id: UUID,
) -> list[TicketHistory]:
    query = (
        select(TicketHistory)
        .where(TicketHistory.ticket_id == ticket_id)
        .order_by(TicketHistory.created_at.asc())
    )

    return list(db.scalars(query).all())
