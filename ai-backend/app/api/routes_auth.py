"""
LabMind AI — Auth API Routes
Endpoints: register, login (token), and current user profile.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.dependencies import get_client_ip, get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import get_db
from app.db.models.user import User
from app.schemas.auth import ChangePasswordRequest, RegisterRequest, TokenRequest, TokenResponse
from app.schemas.user import UserResponse, UserUpdate
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
    summary="Register a new user account",
)
def register(
    body: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    ip = get_client_ip(request)
    service = AuthService(db)
    user = service.register(body, ip=ip)
    return user


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Login and receive a JWT access token",
)
def login(
    body: TokenRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    ip = get_client_ip(request)
    service = AuthService(db)
    return service.login(email=body.email, password=body.password, ip=ip)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the currently authenticated user's profile",
)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put(
    "/profile",
    response_model=UserResponse,
    summary="Update the authenticated user's profile",
)
def update_profile(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update profile fields (full_name, rank_title, avatar_url).
    Only provided (non-None) fields are updated.
    Cannot change: email, password, role, is_active.
    """
    updates = body.model_dump(exclude_none=True)
    if not updates:
        return current_user

    repo = UserRepository(db)
    updated_user = repo.update(current_user, updates)
    return updated_user


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh JWT token — extends session without re-login",
)
def refresh_token(current_user: User = Depends(get_current_user)):
    """Issue a fresh JWT for the authenticated user.

    Call this before the current token expires (e.g. when < 10 min remain)
    to silently extend the session by another full expiry window.
    """
    new_token = create_access_token(subject=str(current_user.id))
    return {"access_token": new_token, "token_type": "bearer"}


@router.put(
    "/change-password",
    summary="Change the authenticated user's password",
)
def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verify current password, validate new password, then update."""
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    if body.new_password != body.confirm_password:
        raise HTTPException(status_code=400, detail="New passwords do not match")

    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    current_user.hashed_password = hash_password(body.new_password)
    db.commit()
    return {"message": "Password changed successfully"}


@router.delete(
    "/account",
    summary="Permanently delete the authenticated user's account",
)
def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Hard-delete the user record from the database."""
    db.delete(current_user)
    db.commit()
    return {"message": "Account deleted successfully"}

