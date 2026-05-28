"""
LabMind AI — Alert Pydantic Schemas
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.core.constants import AlertPriority, AlertType


class AlertResponse(BaseModel):
    id: UUID
    user_id: UUID
    alert_type: AlertType
    priority: AlertPriority
    title: str
    message: str | None = None
    entity_type: str | None = None
    entity_id: UUID | None = None
    is_read: bool
    dismissed: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertDismissRequest(BaseModel):
    dismissed: bool = True
