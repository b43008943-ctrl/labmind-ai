"""
LabMind AI — User Pydantic Schemas
Request/response contracts for user profile endpoints.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.core.constants import UserRole


class UserResponse(BaseModel):
    """Public user profile returned by the API."""
    id: UUID
    email: EmailStr
    full_name: str
    role: UserRole
    rank_title: str | None = None
    avatar_url: str | None = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """Partial update for user profile fields.
    Only provided (non-None) fields are applied.
    Sensitive fields (email, password, role, is_active) cannot be changed here.
    """
    full_name: str | None = Field(
        default=None, min_length=2, max_length=100,
        description="Display name (2-100 characters)"
    )
    rank_title: str | None = Field(
        default=None, max_length=100,
        description="User rank/title (max 100 characters)"
    )
    avatar_url: str | None = Field(
        default=None, max_length=500,
        description="Avatar image URL (max 500 characters)"
    )
