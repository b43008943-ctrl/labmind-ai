"""
LabMind AI — Case Asset Pydantic Schemas
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.core.constants import AssetType


class AssetUploadResponse(BaseModel):
    id: UUID
    case_id: UUID
    uploaded_by: UUID
    asset_type: AssetType
    original_filename: str
    file_size_bytes: int | None = None
    mime_type: str | None = None
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class AssetListItem(AssetUploadResponse):
    """Same shape — alias for list endpoints."""
    pass
