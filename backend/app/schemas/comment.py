from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CommentCreate(BaseModel):
    """Fields required to add a comment to a ticket."""

    body: str = Field(min_length=1, max_length=5000)


class CommentResponse(BaseModel):
    """Comment information returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ticket_id: UUID
    author_id: UUID
    body: str
    is_internal: bool
    created_at: datetime
