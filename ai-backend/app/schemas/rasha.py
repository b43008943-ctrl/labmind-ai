"""
LabMind AI — Rasha AI Pydantic Schemas
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RashaRequest(BaseModel):
    session_id: UUID | None = None
    message: str
    context: dict | None = None


class RashaResponse(BaseModel):
    session_id: UUID
    reply: str
    tokens_used: int | None = None


class RashaMessageItem(BaseModel):
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RashaSessionResponse(BaseModel):
    id: UUID
    context_screen: str | None = None
    started_at: datetime
    ended_at: datetime | None = None

    model_config = {"from_attributes": True}
