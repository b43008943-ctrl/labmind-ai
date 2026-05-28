"""
LabMind AI — Auth Pydantic Schemas
Request/response contracts for authentication endpoints.
"""

from pydantic import BaseModel, EmailStr


class TokenRequest(BaseModel):
    """JSON login request body (email + password)."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT access token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class ChangePasswordRequest(BaseModel):
    """Change password request body."""
    current_password: str
    new_password: str
    confirm_password: str


class RegisterRequest(BaseModel):
    """New user registration request."""
    email: EmailStr
    password: str
    full_name: str
