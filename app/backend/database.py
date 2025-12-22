"""
Database configuration and session management for VulnDash.

Supports both SQLite (development) and PostgreSQL (production) with async capabilities.
"""
import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import StaticPool

# Database URL from environment, defaulting to SQLite for development
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./vulndash.db"
)

# Convert postgres:// to postgresql+asyncpg:// if needed
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Engine configuration
engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific configuration
    engine_kwargs.update({
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    })

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    **engine_kwargs
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI routes to get database sessions.

    Usage:
        @app.get("/items")
        async def read_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """
    Initialize database tables and FTS5 indexes.

    Creates all tables and sets up SQLite FTS5 virtual table for product search.
    """
    from app.backend.models.product import Base as ProductBase

    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(ProductBase.metadata.create_all)

        # For SQLite, create FTS5 virtual table
        if DATABASE_URL.startswith("sqlite"):
            await conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS product_search_fts5 USING fts5(
                    product_id UNINDEXED,
                    vendor,
                    product_name,
                    description,
                    search_text,
                    content='product_search_index',
                    content_rowid='rowid'
                );
            """)

            # Create triggers to keep FTS5 in sync with product_search_index
            await conn.execute("""
                CREATE TRIGGER IF NOT EXISTS product_search_ai AFTER INSERT ON product_search_index BEGIN
                    INSERT INTO product_search_fts5(rowid, product_id, vendor, product_name, description, search_text)
                    VALUES (new.rowid, new.product_id, new.vendor, new.product_name, new.description, new.search_text);
                END;
            """)

            await conn.execute("""
                CREATE TRIGGER IF NOT EXISTS product_search_ad AFTER DELETE ON product_search_index BEGIN
                    INSERT INTO product_search_fts5(product_search_fts5, rowid, product_id, vendor, product_name, description, search_text)
                    VALUES('delete', old.rowid, old.product_id, old.vendor, old.product_name, old.description, old.search_text);
                END;
            """)

            await conn.execute("""
                CREATE TRIGGER IF NOT EXISTS product_search_au AFTER UPDATE ON product_search_index BEGIN
                    INSERT INTO product_search_fts5(product_search_fts5, rowid, product_id, vendor, product_name, description, search_text)
                    VALUES('delete', old.rowid, old.product_id, old.vendor, old.product_name, old.description, old.search_text);
                    INSERT INTO product_search_fts5(rowid, product_id, vendor, product_name, description, search_text)
                    VALUES (new.rowid, new.product_id, new.vendor, new.product_name, new.description, new.search_text);
                END;
            """)

        # For PostgreSQL, use built-in full-text search
        # (Implementation would use tsvector and GIN indexes)


async def close_db():
    """Clean shutdown of database connections."""
    await engine.dispose()
