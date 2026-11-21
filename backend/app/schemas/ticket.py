from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.models.ticket import TicketPriority, TicketStatus


class TicketCreate(BaseModel):
    subject: str = Field(min_length=5, max_length=200)
    description: str = Field(min_length=10)
    category: str = Field(
        default="general",
        min_length=2,
        max_length=100,
    )
    priority: TicketPriority = TicketPriority.NORMAL

    @field_validator(
        "subject",
        "description",
        "category",
        mode="before",
    )
    @classmethod
    def strip_whitespace(cls, value):
        if isinstance(value, str):
            return value.strip()

        return value


class TicketUpdate(BaseModel):
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
        min_length=2,
        max_length=100,
    )

    @field_validator(
        "subject",
        "description",
        "category",
        mode="before",
    )
    @classmethod
    def strip_whitespace(cls, value):
        if isinstance(value, str):
            return value.strip()

        return value

    @model_validator(mode="after")
    def validate_at_least_one_field(self):
        fields = (
            self.subject,
            self.description,
            self.category,
        )

        if not any(value is not None for value in fields):
            raise ValueError("At least one non-null field must be provided.")

        return self


class TicketStatusUpdate(BaseModel):
    status: TicketStatus


class TicketPriorityUpdate(BaseModel):
    priority: TicketPriority


class TicketAssignment(BaseModel):
    assignee_id: UUID


class TicketResponse(BaseModel):
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
