"""
LabMind AI — FastAPI Dependencies
Shared injectable dependencies for DB sessions, authenticated user, and role checks.
"""

from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.constants import UserRole
from app.core.exceptions import CredentialsException, ForbiddenException
from app.core.security import decode_access_token
from app.db.database import get_db
from app.db.models.user import User
from app.repositories.user_repository import UserRepository

# Extracts "Bearer <token>" from the Authorization header
_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Decode the JWT from the Authorization header, look up the user,
    and return the active User ORM instance.
    Raises 401 on any failure.
    """
    if credentials is None:
        raise CredentialsException(detail="Authorization header missing.")

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise CredentialsException(detail="Token is invalid or expired.")

    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        raise CredentialsException(detail="Token payload missing subject.")

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise CredentialsException(detail="Token contains invalid user ID.")

    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise CredentialsException(detail="User not found.")
    if not user.is_active:
        raise CredentialsException(detail="Account is disabled.")

    return user


def require_role(*allowed_roles: UserRole):
    """
    Factory that returns a dependency enforcing the user has one of the allowed roles.
    Usage: Depends(require_role(UserRole.ADMIN, UserRole.CLINICIAN))
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise ForbiddenException(
                detail=f"Role '{current_user.role.value}' is not authorized for this action."
            )
        return current_user
    return role_checker


def get_client_ip(request: Request) -> str | None:
    """Extract client IP from the request for audit logging."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None
