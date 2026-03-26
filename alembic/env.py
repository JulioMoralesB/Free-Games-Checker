"""Alembic environment configuration for free-games-notifier.

Reads PostgreSQL connection parameters from config.py and applies
migrations within the ``free_games`` schema.
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, text
from alembic import context

# Make the project root importable so we can use config.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD  # noqa: E402

# Alembic Config object, providing access to values from alembic.ini
alembic_config = context.config

# Interpret the config file for Python logging if present
if alembic_config.config_file_name is not None:
    fileConfig(alembic_config.config_file_name)

# We do not use SQLAlchemy ORM metadata — all migrations use raw SQL via
# op.execute(), so target_metadata remains None.
target_metadata = None


def get_url() -> str:
    """Build the SQLAlchemy connection URL from environment-derived config."""
    from urllib.parse import quote_plus

    user = quote_plus(DB_USER or "")
    password = quote_plus(DB_PASSWORD or "")
    host = DB_HOST or "localhost"
    port = DB_PORT or 5432
    dbname = DB_NAME or ""
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no live DB connection required)."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode against a live database connection."""
    configuration = dict(alembic_config.get_section(alembic_config.config_ini_section) or {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # All migrations operate within the free_games schema.
        connection.execute(text("SET search_path TO free_games, public"))
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
