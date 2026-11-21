import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.ticket import Ticket
from app.models.user import User


class Comment(Base):
    """SQLAlchemy model representing a comment on a helpdesk ticket."""

    __tablename__ = "comments"

    __table_args__ = (
        Index(
            "ix_comments_ticket_created_at",
            "ticket_id",
            "created_at",
        ),
    )

    # Unique identifier for each comment.
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Ticket to which this comment belongs.
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
    )

    # User who wrote the comment.
    author_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Actual comment content.
    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # True means the comment is visible only to support staff.
    is_internal: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Comment creation timestamp.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Associated ticket.
    ticket: Mapped["Ticket"] = relationship(
        Ticket,
        foreign_keys=[ticket_id],
    )

    # User who authored the comment.
    author: Mapped["User"] = relationship(
        User,
        foreign_keys=[author_id],
    )

    def __repr__(self) -> str:
        return (
            f"<Comment(id={self.id}, "
            f"ticket_id={self.ticket_id}, "
            f"author_id={self.author_id}, "
            f"is_internal={self.is_internal})>"
        )
