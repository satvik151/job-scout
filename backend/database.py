"""SQLAlchemy database configuration and session management."""
import logging
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

logger = logging.getLogger(__name__)

# Build database path dynamically using Path
# This ensures the path is correct regardless of where uvicorn is launched from
db_path = Path(__file__).parent / "jobs.db"
DATABASE_URL = f"sqlite:///{db_path}"

# SQLite requires check_same_thread=False because FastAPI handles requests
# across multiple threads. In production, you'd use PostgreSQL which handles
# multi-threading natively.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,  # Set to True for SQL query logging
)

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
    logger.info(f"Database initialized at {db_path}")
