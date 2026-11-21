
import uuid

from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserRole(str, PyEnum):
    """
    Roles supported by the Helpdesk application.
    """

    EMPLOYEE = "employee"
    AGENT = "agent"
    ADMIN = "admin"


class User(Base):
    """
    SQLAlchemy model representing an application user.
    """

    __tablename__ = "users"

    # Unique identifier for each user.
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Unique email address used for authentication.
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    # User's display name.
    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    # Stores the password hash, never the original password.
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Determines the user's permissions within the application.
    role: Mapped[UserRole] = mapped_column(
    Enum(
        UserRole,
        name="user_role",
        native_enum=False,
        length=20,
        values_callable=lambda enum_class: [
            member.value for member in enum_class
        ],
    ),
    default=UserRole.EMPLOYEE,
    nullable=False,
)

    # Allows administrators to deactivate accounts.
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Account creation timestamp.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Automatically updated when the user record changes.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<User(id={self.id}, "
            f"email='{self.email}', "
            f"role='{self.role.value}')>"
        )
