"""
Alembic Environment Configuration.
Reads DATABASE_URL from the app's config so we don't duplicate it.
"""

import sys
from pathlib import Path

# Ensure the project root (ai-backend/) is on sys.path so `app` is importable.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Load our app's settings to get the DATABASE_URL
from app.core.config import get_settings

# Import Base and ALL models so Alembic can detect them for autogenerate
from app.db.database import Base
from app.db.models.user import User  # noqa: F401
from app.db.models.audit_log import AuditLog  # noqa: F401
from app.db.models.patient import Patient  # noqa: F401
from app.db.models.lab_case import LabCase  # noqa: F401
from app.db.models.case_asset import CaseAsset  # noqa: F401
from app.db.models.rasha_session import RashaSession  # noqa: F401
from app.db.models.rasha_message import RashaMessage  # noqa: F401
from app.db.models.analysis_run import AnalysisRun  # noqa: F401
from app.db.models.analysis_result import AnalysisResult  # noqa: F401
from app.db.models.diagnostic_report import DiagnosticReport  # noqa: F401
from app.db.models.report_review import ReportReview  # noqa: F401
from app.db.models.alert import Alert  # noqa: F401

# Alembic Config object
config = context.config

# Override sqlalchemy.url from our app settings
config.set_main_option("sqlalchemy.url", get_settings().DATABASE_URL)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target_metadata for autogenerate support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
