"""
LabMind AI — Rasha AI Repository
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.rasha_message import RashaMessage
from app.db.models.rasha_session import RashaSession


class RashaRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── Sessions ──
    def create_session(self, session: RashaSession) -> RashaSession:
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session(self, session_id: UUID) -> RashaSession | None:
        return self.db.get(RashaSession, session_id)

    def list_sessions(self, user_id: UUID) -> list[RashaSession]:
        stmt = (
            select(RashaSession)
            .where(RashaSession.user_id == user_id)
            .order_by(RashaSession.started_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    # ── Messages ──
    def add_message(self, message: RashaMessage) -> RashaMessage:
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_messages(self, session_id: UUID) -> list[RashaMessage]:
        stmt = (
            select(RashaMessage)
            .where(RashaMessage.session_id == session_id)
            .order_by(RashaMessage.created_at.asc())
        )
        return list(self.db.execute(stmt).scalars().all())
