"""
LabMind AI — User Repository
Pure data access layer — no business logic.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: UUID) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def list_all(self, skip: int = 0, limit: int = 50) -> list[User]:
        stmt = select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
        return list(self.db.execute(stmt).scalars().all())

    def list_by_roles(self, roles: list) -> list[User]:
        """Return all active users whose role is in the given list."""
        stmt = (
            select(User)
            .where(User.role.in_(roles))
            .where(User.is_active == True)  # noqa: E712
        )
        return list(self.db.execute(stmt).scalars().all())

    def update(self, user: User, updates: dict) -> User:
        for key, value in updates.items():
            if value is not None:
                setattr(user, key, value)
        self.db.commit()
        self.db.refresh(user)
        return user
