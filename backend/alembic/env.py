from logging.config import fileConfig
import os
import sys

from sqlalchemy import engine_from_config, pool
from alembic import context

# Make imports work when running from repo root
sys.path.append("backend")

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from backend.app.core.config import settings  # noqa: E402
from backend.app.db.base import Base  # noqa: E402
# Import models here (NOT in Base) so metadata includes them
from backend.app.models.series import Series  # noqa: F401,E402
from backend.app.models.observation import Observation  # noqa: F401,E402

target_metadata = Base.metadata

def get_url() -> str:
    return settings.database_url

def run_migrations_offline() -> None:
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
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
