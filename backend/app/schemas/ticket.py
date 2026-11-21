
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.ticket import TicketPriority, TicketStatus


class TicketCreate(BaseModel):
    """Fields required to create a new helpdesk ticket."""

    subject: str = Field(min_length=5, max_length=200)
    description: str = Field(min_length=10)
    category: str = Field(default="general", max_length=100)
    priority: TicketPriority = TicketPriority.NORMAL


class TicketUpdate(BaseModel):
    """Fields that an employee or authorized user can update."""

    subject: str | None = Field(
        default=None,
        min_length=5,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        min_length=10,
    )

    category: str | None = Field(
        default=None,
        max_length=100,
    )


class TicketStatusUpdate(BaseModel):
    """Schema for changing a ticket's status."""

    status: TicketStatus


class TicketPriorityUpdate(BaseModel):
    """Schema for changing a ticket's priority."""

    priority: TicketPriority


class TicketAssignment(BaseModel):
    """Schema for assigning a ticket to an agent."""

    assignee_id: UUID


class TicketResponse(BaseModel):
    """Ticket information returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    requester_id: UUID
    assignee_id: UUID | None

    subject: str
    description: str
    category: str

    status: TicketStatus
    priority: TicketPriority

    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
    closed_at: datetime | None
