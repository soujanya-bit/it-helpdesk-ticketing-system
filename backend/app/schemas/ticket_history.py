from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.ticket_history import TicketHistoryEvent


class TicketHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ticket_id: UUID
    actor_id: UUID | None
    event_type: TicketHistoryEvent
    old_values: dict[str, Any] | None
    new_values: dict[str, Any] | None
    created_at: datetime
