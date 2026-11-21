
import uuid

from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import User


class TicketStatus(str, PyEnum):
    """Possible states of a helpdesk ticket."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_ON_EMPLOYEE = "waiting_on_employee"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, PyEnum):
    """Priority levels supported by the application."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Ticket(Base):
    """SQLAlchemy model representing a helpdesk ticket."""

    __tablename__ = "tickets"

    # Indexes for common ticket-list queries.
    __table_args__ = (
        Index("ix_tickets_status_created_at", "status", "created_at"),
        Index("ix_tickets_assignee_status", "assignee_id", "status"),
        Index("ix_tickets_requester_created_at", "requester_id", "created_at"),
    )

    # Unique ticket identifier.
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Employee who created the ticket.
    requester_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Agent assigned to handle the ticket.
    # This remains NULL until an agent is assigned.
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )

    # Short description of the issue.
    subject: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    # Detailed description of the issue.
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # General category of the IT issue.
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="general",
    )

    # Current ticket status.
    status: Mapped[TicketStatus] = mapped_column(
        Enum(
            TicketStatus,
            name="ticket_status",
            native_enum=False,
            length=30,
            values_callable=lambda enum_class: [
                member.value for member in enum_class
            ],
        ),
        default=TicketStatus.OPEN,
        nullable=False,
    )

    # Ticket priority.
    priority: Mapped[TicketPriority] = mapped_column(
        Enum(
            TicketPriority,
            name="ticket_priority",
            native_enum=False,
            length=20,
            values_callable=lambda enum_class: [
                member.value for member in enum_class
            ],
        ),
        default=TicketPriority.NORMAL,
        nullable=False,
    )

    # Ticket creation timestamp.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Automatically updated when the ticket changes.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Set when the ticket is marked as resolved.
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Set when the ticket is formally closed.
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationship to the employee who submitted the ticket.
    requester: Mapped["User"] = relationship(
        "User",
        foreign_keys=[requester_id],
    )

    # Relationship to the agent handling the ticket.
    assignee: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[assignee_id],
    )

    def __repr__(self) -> str:
        return (
            f"<Ticket(id={self.id}, "
            f"subject='{self.subject}', "
            f"status='{self.status.value}', "
            f"priority='{self.priority.value}')>"
        )
