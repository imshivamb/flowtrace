import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool, create_engine
from sqlalchemy.engine import Connection

# ---- Ensure 'app' is importable when running alembic from backend/ ----
# env.py lives at backend/app/db/migrations/env.py → project root is backend/
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.append(BACKEND_ROOT)

# ---- App imports ----
from app.core.config import settings
from app.models.base import Base
import app.models  # noqa: F401  # this populates Base.metadata by importing model modules

# Alembic Config object, provides access to values within the .ini file
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for 'autogenerate'
target_metadata = Base.metadata

# Convert DATABASE_URL from asyncpg to psycopg2 for sync migrations
database_url = settings.DATABASE_URL
if "+asyncpg" in database_url:
    database_url = database_url.replace("+asyncpg", "+psycopg2")
elif "postgresql://" in database_url and "+" not in database_url:
    # If no driver specified, add psycopg2
    database_url = database_url.replace("postgresql://", "postgresql+psycopg2://")

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = create_engine(database_url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()