"""
LabMind AI — Rasha AI Chat Message ORM Model
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import RashaRole
from app.db.database import Base


class RashaMessage(Base):
    __tablename__ = "rasha_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rasha_sessions.id"), nullable=False, index=True
    )
    role: Mapped[RashaRole] = mapped_column(
        Enum(RashaRole, name="rasha_role_enum", create_constraint=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    session = relationship("RashaSession", back_populates="messages", lazy="joined")

    def __repr__(self) -> str:
        return f"<RashaMessage {self.role.value} session={self.session_id}>"

