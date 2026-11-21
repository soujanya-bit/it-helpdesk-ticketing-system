
import uuid

from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Any

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    JSON,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.ticket import Ticket
from app.models.user import User


class TicketHistoryEvent(str, PyEnum):
    """Types of events that can be recorded for a ticket."""

    CREATED = "created"
    UPDATED = "updated"
    ASSIGNED = "assigned"
    STATUS_CHANGED = "status_changed"
    PRIORITY_CHANGED = "priority_changed"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketHistory(Base):
    """SQLAlchemy model representing a ticket audit-history entry."""

    __tablename__ = "ticket_history"

    __table_args__ = (
        Index(
            "ix_ticket_history_ticket_created_at",
            "ticket_id",
            "created_at",
        ),
    )

    # Unique identifier for each history entry.
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Ticket associated with this event.
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
    )

    # User who performed the action.
    # NULL is allowed for system-generated events or when
    # the original actor account is no longer available.
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Type of event, such as status_changed or assigned.
    event_type: Mapped[TicketHistoryEvent] = mapped_column(
    Enum(
        TicketHistoryEvent,
        name="ticket_history_event",
        native_enum=False,
        length=30,
        values_callable=lambda enum_class: [
            member.value for member in enum_class
        ],
    ),
    nullable=False,
)

    # Values before the operation.
    old_values: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # Values after the operation.
    new_values: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # When the event occurred.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Associated ticket.
    ticket: Mapped["Ticket"] = relationship(
        Ticket,
        foreign_keys=[ticket_id],
    )

    # User who performed the action, if available.
    actor: Mapped["User | None"] = relationship(
        User,
        foreign_keys=[actor_id],
    )

    def __repr__(self) -> str:
        return (
            f"<TicketHistory(id={self.id}, "
            f"ticket_id={self.ticket_id}, "
            f"event_type='{self.event_type.value}', "
            f"actor_id={self.actor_id})>"
        )
