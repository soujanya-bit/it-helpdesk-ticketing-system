import pytest
from sqlalchemy import select

from app.models.comment import Comment
from app.models.ticket import (
    Ticket,
    TicketPriority,
    TicketStatus,
)
from app.models.user import User, UserRole
from app.services.comment_service import create_comment
from app.services.ticket_service import (
    ensure_ticket_access,
    update_ticket_priority,
    update_ticket_status,
)


@pytest.fixture
def service_users(db_session):
    employee = User(
        email="service_employee@example.com",
        full_name="Service Employee",
        password_hash="test-hash",
        role=UserRole.EMPLOYEE,
        is_active=True,
    )

    assigned_agent = User(
        email="assigned_agent@example.com",
        full_name="Assigned Agent",
        password_hash="test-hash",
        role=UserRole.AGENT,
        is_active=True,
    )

    unassigned_agent = User(
        email="unassigned_agent@example.com",
        full_name="Unassigned Agent",
        password_hash="test-hash",
        role=UserRole.AGENT,
        is_active=True,
    )

    admin = User(
        email="service_admin@example.com",
        full_name="Service Admin",
        password_hash="test-hash",
        role=UserRole.ADMIN,
        is_active=True,
    )

    db_session.add_all(
        [
            employee,
            assigned_agent,
            unassigned_agent,
            admin,
        ]
    )

    db_session.commit()

    return {
        "employee": employee,
        "assigned_agent": assigned_agent,
        "unassigned_agent": unassigned_agent,
        "admin": admin,
    }


@pytest.fixture
def service_ticket(db_session, service_users):
    ticket = Ticket(
        requester_id=service_users["employee"].id,
        assignee_id=service_users["assigned_agent"].id,
        subject="Service authorization test",
        description="Testing service-layer permissions.",
        category="hardware",
        status=TicketStatus.OPEN,
        priority=TicketPriority.NORMAL,
    )

    db_session.add(ticket)
    db_session.commit()
    db_session.refresh(ticket)

    return ticket


def test_employee_can_access_own_ticket(
    service_ticket,
    service_users,
):
    ensure_ticket_access(
        service_ticket,
        service_users["employee"],
    )


def test_assigned_agent_can_access_ticket(
    service_ticket,
    service_users,
):
    ensure_ticket_access(
        service_ticket,
        service_users["assigned_agent"],
    )


def test_admin_can_access_any_ticket(
    service_ticket,
    service_users,
):
    ensure_ticket_access(
        service_ticket,
        service_users["admin"],
    )


def test_unassigned_agent_cannot_access_ticket(
    service_ticket,
    service_users,
):
    with pytest.raises(LookupError):
        ensure_ticket_access(
            service_ticket,
            service_users["unassigned_agent"],
        )


def test_unassigned_agent_cannot_change_status_directly(
    db_session,
    service_ticket,
    service_users,
):
    with pytest.raises(LookupError):
        update_ticket_status(
            db=db_session,
            ticket=service_ticket,
            new_status=TicketStatus.IN_PROGRESS,
            actor=service_users["unassigned_agent"],
        )

    db_session.refresh(service_ticket)

    assert service_ticket.status == TicketStatus.OPEN


def test_unassigned_agent_cannot_change_priority_directly(
    db_session,
    service_ticket,
    service_users,
):
    with pytest.raises(LookupError):
        update_ticket_priority(
            db=db_session,
            ticket=service_ticket,
            new_priority=TicketPriority.HIGH,
            actor=service_users["unassigned_agent"],
        )

    db_session.refresh(service_ticket)

    assert service_ticket.priority == TicketPriority.NORMAL


def test_employee_cannot_comment_on_another_employees_ticket(
    db_session,
    service_ticket,
):
    another_employee = User(
        email="another_employee@example.com",
        full_name="Another Employee",
        password_hash="test-hash",
        role=UserRole.EMPLOYEE,
        is_active=True,
    )

    db_session.add(another_employee)
    db_session.commit()

    with pytest.raises(LookupError):
        create_comment(
            db=db_session,
            ticket=service_ticket,
            author=another_employee,
            body="Unauthorized comment",
            is_internal=False,
        )

    # Confirm that the unauthorized comment was not saved.
    saved_comment = db_session.scalar(
        select(Comment).where(Comment.ticket_id == service_ticket.id)
    )

    assert saved_comment is None
