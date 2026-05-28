"""
LabMind AI — Database Engine & Session Factory
SQLAlchemy 2.0 style with synchronous psycopg (v3) driver.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


engine = create_engine(
    get_settings().DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=get_settings().DEBUG,
)

# ── psycopg v3 enum adapter registration ──
# psycopg v3 does NOT auto-adapt Python str-Enum subclasses to PostgreSQL
# native enum types. We register a TextDumper for each enum class so that
# psycopg sends enum values as plain text, which PostgreSQL can implicitly
# cast to the native enum type.

@event.listens_for(engine, "connect")
def _register_enum_adapters(dbapi_connection, connection_record):
    """Register text dumpers for all app enum types with the psycopg3 connection."""
    try:
        from psycopg.adapt import Dumper
        from app.core.constants import (
            Department, CasePriority, CaseStatus, AssetType,
            Gender, RashaRole, UserRole, AnalysisStatus,
            ReportStatus, ReviewDecision, AlertType, AlertPriority,
            AuditAction,
        )

        class StrEnumDumper(Dumper):
            """Dump Python str-Enum values as raw text bytes."""
            def dump(self, obj):
                return obj.value.encode("utf-8") if hasattr(obj, "value") else str(obj).encode("utf-8")

        for enum_cls in [
            Department, CasePriority, CaseStatus, AssetType,
            Gender, RashaRole, UserRole, AnalysisStatus,
            ReportStatus, ReviewDecision, AlertType, AlertPriority,
            AuditAction,
        ]:
            dbapi_connection.adapters.register_dumper(enum_cls, StrEnumDumper)
    except Exception:
        pass


SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    """
    FastAPI dependency — yields a DB session per request,
    ensuring proper cleanup via try/finally.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
