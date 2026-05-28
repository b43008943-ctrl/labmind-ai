"""
LabMind AI — Auth Service
Business logic for registration, login, and token management.
"""

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.constants import AuditAction, UserRole
from app.core.exceptions import ConflictException, CredentialsException
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterRequest, TokenResponse
from app.services.audit_service import AuditService


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.audit = AuditService(db)

    def register(self, data: RegisterRequest, ip: str | None = None) -> User:
        """Register a new user account."""
        existing = self.user_repo.get_by_email(data.email)
        if existing:
            raise ConflictException(detail="An account with this email already exists.")

        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role=UserRole.STUDENT,
        )
        created_user = self.user_repo.create(user)

        self.audit.log(
            action=AuditAction.USER_REGISTERED,
            user_id=created_user.id,
            entity_type="user",
            entity_id=created_user.id,
            details={"email": data.email, "full_name": data.full_name},
            ip_address=ip,
        )
        return created_user

    # Dummy hash used for constant-time comparison when user doesn't exist.
    # Prevents timing attacks that leak whether an email is registered.
    # Lazy-initialised to avoid import-time bcrypt crash.
    _DUMMY_HASH: str | None = None

    @classmethod
    def _get_dummy_hash(cls) -> str:
        if cls._DUMMY_HASH is None:
            cls._DUMMY_HASH = hash_password("__timing_safe_placeholder__")
        assert cls._DUMMY_HASH is not None
        return cls._DUMMY_HASH

    def login(self, email: str, password: str, ip: str | None = None) -> TokenResponse:
        """Authenticate user and return a JWT access token."""
        user = self.user_repo.get_by_email(email)

        # Always run verify_password to prevent timing-based user enumeration
        target_hash = user.hashed_password if user else self._get_dummy_hash()
        password_valid = verify_password(password, target_hash)

        if not user or not password_valid:
            self.audit.log(
                action=AuditAction.USER_LOGIN_FAILED,
                user_id=user.id if user else None,
                details={"email": email, "reason": "invalid_credentials"},
                ip_address=ip,
            )
            raise CredentialsException(detail="Incorrect email or password.")

        if not user.is_active:
            self.audit.log(
                action=AuditAction.USER_LOGIN_FAILED,
                user_id=user.id,
                details={"email": email, "reason": "account_disabled"},
                ip_address=ip,
            )
            raise CredentialsException(detail="Account is disabled.")

        settings = get_settings()
        token = create_access_token(
            subject=str(user.id),
            extra_claims={"role": user.role.value},
        )

        # Log successful login
        self.audit.log(
            action=AuditAction.USER_LOGIN,
            user_id=user.id,
            entity_type="user",
            entity_id=user.id,
            ip_address=ip,
        )

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
