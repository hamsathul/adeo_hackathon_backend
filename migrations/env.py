# migrations/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import models and config
from app.db.base_class import Base
from app.models.auth import User, Role, Permission
from app.models.department import Department
from app.models.chat import ChatMessage
from app.models.opinion import (
    WorkflowStatus,
    OpinionRequest,
    Document,
    Category,
    SubCategory,
    Remark,
    RequestAssignment,
    Opinion,
    CommunicationType,
    InterdepartmentalCommunication,
    WorkflowHistory,
)
from app.core.config import get_settings

settings = get_settings()

# This is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the database URL in the alembic.ini file
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Add your model's MetaData object here for 'autogenerate' support
# Make sure all models are imported before this line
target_metadata = Base.metadata

def include_object(object, name, type_, reflected, compare_to):
    """Defines which objects should be included in the migration."""
    # Add any tables that should be ignored in migrations
    ignored_tables = []
    if type_ == "table" and name in ignored_tables:
        return False
    return True

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.DATABASE_URL
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()