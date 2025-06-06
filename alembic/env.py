# chs_backend/alembic/env.py

from logging.config import fileConfig
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine # Ensure create_async_engine is here
from sqlalchemy import pool # You might not need this if not used elsewhere for pool config
# from sqlalchemy import engine_from_config # Not typically used with async engines directly for URL
from alembic import context

import os
from dotenv import load_dotenv # Used here to load .env for local Alembic commands
# from sqlalchemy.engine import url as sa_url # Not needed for direct string URL anymore

# --- Import your settings and Base ---
import sys
# Adjust this path if your settings.py and models (with Base) are structured differently
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
# Assuming Base is defined in main.py, or app.models if you moved it
from app.models import Base # Or from app.models import Base if you put models in app/models.py
# --- End Import ---

# --- Configure logging from alembic.ini ---
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- Load .env for local Alembic commands ---
# Ensure the path to your .env file is correct relative to env.py
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
# --- End Load .env ---

# --- Set SQLAlchemy URL in Alembic config ---
# Use the DATABASE_URL loaded via your settings
config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))

# --- Point Alembic to your Base.metadata ---
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    # ... (no changes needed here) ...
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # Set render_as_batch=True for databases that don't support transactional DDL
        # render_as_batch=True # Uncomment if needed for your database
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # --- CRUCIAL CHANGE HERE: SIMPLIFY connectable creation ---
    # Pass the DATABASE_URL string directly to create_async_engine
    connectable = create_async_engine(
        os.getenv("DATABASE_URL"),
        # Optionally, add async_fallback=True if you encounter sync/async connection issues
        # during migration generation (though usually not needed if env.py is correct)
        # async_fallback=True
    )
    # --- END CRUCIAL CHANGE ---

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    # Ensure asyncio is imported and used to run the async function
    import asyncio
    asyncio.run(run_migrations_online())