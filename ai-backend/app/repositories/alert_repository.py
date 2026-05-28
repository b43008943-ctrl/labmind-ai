"""
LabMind AI — Alert Repository
"""

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.db.models.alert import Alert


class AlertRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, alert: Alert) -> Alert:
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def get_by_id(self, alert_id: UUID) -> Alert | None:
        return self.db.get(Alert, alert_id)

    def list_by_user(self, user_id: UUID, include_dismissed: bool = False) -> list[Alert]:
        stmt = (
            select(Alert)
            .where(Alert.user_id == user_id)
            .order_by(Alert.created_at.desc())
        )
        if not include_dismissed:
            stmt = stmt.where(Alert.dismissed == False)  # noqa: E712
        return list(self.db.execute(stmt).scalars().all())

    def mark_read(self, alert_id: UUID) -> None:
        stmt = update(Alert).where(Alert.id == alert_id).values(is_read=True)
        self.db.execute(stmt)
        self.db.commit()

    def dismiss(self, alert: Alert) -> Alert:
        alert.dismissed = True
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def count_unread(self, user_id: UUID) -> int:
        stmt = (
            select(Alert)
            .where(Alert.user_id == user_id)
            .where(Alert.is_read == False)  # noqa: E712
            .where(Alert.dismissed == False)  # noqa: E712
        )
        return len(list(self.db.execute(stmt).scalars().all()))
