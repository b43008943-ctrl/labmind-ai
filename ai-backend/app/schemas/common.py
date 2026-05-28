"""
LabMind AI — Common Pydantic Schemas
Shared response wrappers used across all endpoints.
"""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str


class MessageResponse(BaseModel):
    message: str
