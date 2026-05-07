"""SQLAlchemy database configuration and session management.

Supports both SQLite (development) and PostgreSQL (production via Railway).
Database selection is automatic based on DATABASE_URL environment variable.
"""
import logging
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE ENGINE CREATION — SQLite (local) vs PostgreSQL (Railway)
# ============================================================================

database_url = os.getenv("DATABASE_URL")

if database_url:
    # ========== POSTGRESQL (Railway Production) ==========
    # Railway injects DATABASE_URL in legacy postgres:// format.
    # SQLAlchemy 1.4+ requires postgresql:// format. Fix it automatically.
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    engine = create_engine(
        database_url,
        pool_pre_ping=True,  # Validate connections before use (prevents stale connections on Railway)
        echo=False,  # Set to True for SQL query logging
    )
    logger.info("Using database backend: PostgreSQL (Railway)")
else:
    # ========== SQLITE (Local Development) ==========
    # Build database path dynamically using Path
    # This ensures the path is correct regardless of where uvicorn is launched from
    db_path = Path(__file__).parent / "jobs.db"
    database_url = f"sqlite:///{db_path}"
    
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},  # SQLite-only: allow async request threads to share connection
        echo=False,  # Set to True for SQL query logging
    )
    logger.info(f"Using database backend: SQLite at {db_path}")

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """FastAPI dependency to provide a database session.
    
    Usage in endpoints:
        @app.get("/jobs")
        def get_jobs(db: Session = Depends(get_db)):
            ...
    
    The session is automatically closed after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize the database by creating all tables.
    
    Call this once at application startup.
    """
    from .models import Base
    
    Base.metadata.create_all(bind=engine)
    
    if database_url and database_url.startswith("postgresql"):
        logger.info("Database initialized: PostgreSQL (Railway)")
    else:
        logger.info(f"Database initialized: SQLite at {db_path}")
