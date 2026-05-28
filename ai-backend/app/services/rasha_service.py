"""
LabMind AI — Rasha AI Service
Manages chat sessions and proxies messages through the Gemini provider.
"""

import uuid

from sqlalchemy.orm import Session

from app.core.constants import AuditAction, RashaRole
from app.db.models.rasha_message import RashaMessage
from app.db.models.rasha_session import RashaSession
from app.providers.gemini_provider import GeminiProvider
from app.repositories.rasha_repository import RashaRepository
from app.schemas.rasha import RashaRequest, RashaResponse
from app.services.audit_service import AuditService


class RashaService:
    def __init__(self, db: Session):
        self.repo = RashaRepository(db)
        self.gemini = GeminiProvider()
        self.audit = AuditService(db)

    def chat(
        self, data: RashaRequest, user_id: uuid.UUID, ip: str | None = None
    ) -> RashaResponse:
        # Get or create session
        if data.session_id:
            session = self.repo.get_session(data.session_id)
            if not session or session.user_id != user_id:
                session = self._create_session(user_id, data.context, ip)
        else:
            session = self._create_session(user_id, data.context, ip)

        # Build system instruction from context
        system_instruction = self._build_system_instruction(data.context)

        # Load chat history for this session
        existing_messages = self.repo.get_messages(session.id)
        history = [
            {"role": m.role.value, "content": m.content}
            for m in existing_messages
        ]

        # Call Gemini
        result = self.gemini.chat(
            user_message=data.message,
            system_instruction=system_instruction,
            history=history,
        )

        # Persist user message
        self.repo.add_message(RashaMessage(
            session_id=session.id,
            role=RashaRole.USER,
            content=data.message,
        ))

        # Persist Rasha's reply
        self.repo.add_message(RashaMessage(
            session_id=session.id,
            role=RashaRole.RASHA,
            content=result["reply"],
            tokens_used=result.get("tokens_used"),
        ))

        # Audit
        self.audit.log(
            action=AuditAction.RASHA_MESSAGE_SENT,
            user_id=user_id,
            entity_type="rasha_session",
            entity_id=session.id,
            details={"tokens_used": result.get("tokens_used")},
            ip_address=ip,
        )

        return RashaResponse(
            session_id=session.id,
            reply=result["reply"],
            tokens_used=result.get("tokens_used"),
        )

    def list_sessions(self, user_id: uuid.UUID):
        return self.repo.list_sessions(user_id)

    def get_messages(self, session_id: uuid.UUID, user_id: uuid.UUID):
        session = self.repo.get_session(session_id)
        if not session or session.user_id != user_id:
            return []
        return self.repo.get_messages(session_id)

    def _create_session(
        self, user_id: uuid.UUID, context: dict | None, ip: str | None
    ) -> RashaSession:
        session = RashaSession(
            user_id=user_id,
            context_screen=context.get("screen") if context else None,
            context_metadata=context,
        )
        created = self.repo.create_session(session)

        self.audit.log(
            action=AuditAction.RASHA_SESSION_STARTED,
            user_id=user_id,
            entity_type="rasha_session",
            entity_id=created.id,
            details={"context": context},
            ip_address=ip,
        )
        return created

    @staticmethod
    def _build_system_instruction(context: dict | None) -> str:
        base = (
            "You are Rasha, a brilliant and friendly AI lab assistant in LabMind AI, "
            "a futuristic clinical diagnostic platform. "
            "You speak in a warm, professional tone. You help clinicians and students "
            "with medical lab questions, diagnostic insights, and educational support."
        )
        if not context:
            return base

        screen = context.get("screen", "")
        if screen == "knowledge-library":
            book = context.get("book_title", "")
            page = context.get("page_text", "")
            base += (
                f"\n\nThe user is currently reading '{book}' in the Knowledge Library. "
                f"Here is the page content they're viewing:\n{page}\n"
                "Answer questions about this content specifically."
            )
        elif screen == "hematology-lab":
            base += (
                "\n\nThe user is in the Hematology Lab screen analyzing blood smear images. "
                "Provide insights about hematology, cell morphology, and sickle cell disease."
            )
        return base
