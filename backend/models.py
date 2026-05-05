"""SQLAlchemy models for job-scout database."""
import hashlib
import json
import logging
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, Index
from sqlalchemy.orm import declarative_base, Session

logger = logging.getLogger(__name__)

Base = declarative_base()


class Job(Base):
    """SQLAlchemy model for job listings."""
    
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    url = Column(String, unique=True, nullable=False)
    url_hash = Column(String(32), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    skills = Column(Text, nullable=True)  # Stored as JSON string
    score = Column(Float, nullable=True)
    skills_match_pct = Column(Integer, nullable=True)
    missing_skills = Column(Text, nullable=True)  # Stored as JSON string
    seniority_fit = Column(String(20), nullable=True)
    reason = Column(String(300), nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_new = Column(Boolean, default=True, nullable=False)
    
    def __repr__(self) -> str:
        return f"<Job id={self.id} title={self.title} company={self.company}>"


class User(Base):
    """SQLAlchemy model for user accounts."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    resume_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} active={self.is_active}>"


def upsert_job(db: Session, job_data: dict) -> tuple[Job, bool]:
    """Upsert a job into the database.
    
    Computes URL hash and checks for duplicates.
    Converts skills lists to JSON before storing.
    
    Args:
        db: SQLAlchemy session
        job_data: Dictionary with job details (must include 'url' and 'skills')
    
    Returns:
        Tuple of (job_object, is_new)
        - is_new=True if job was just created
        - is_new=False if job already existed
    
    Note: This function does NOT commit. Call db.commit() once after the loop.
    """
    # Compute URL hash for deduplication
    url_hash = hashlib.md5(job_data["url"].encode()).hexdigest()
    
    # Check if job already exists by URL hash
    existing_job = db.query(Job).filter(Job.url_hash == url_hash).first()
    if existing_job:
        return (existing_job, False)
    
    # Job is new — create and add to session
    try:
        new_job = Job(
            title=job_data.get("title", ""),
            company=job_data.get("company", ""),
            url=job_data.get("url", ""),
            url_hash=url_hash,
            description=job_data.get("description", ""),
            skills=json.dumps(job_data.get("skills", [])),
            score=job_data.get("score"),
            skills_match_pct=job_data.get("skills_match_pct"),
            missing_skills=json.dumps(job_data.get("missing_skills", [])),
            seniority_fit=job_data.get("seniority_fit"),
            reason=job_data.get("reason"),
        )
        db.add(new_job)
        return (new_job, True)
    except Exception as e:
        logger.error(f"Failed to upsert job: {e}")
        db.rollback()
        raise


def get_new_jobs(db: Session, limit: int = 50) -> list[Job]:
    """Retrieve all new jobs (is_new=True) ordered by most recent.
    
    Args:
        db: SQLAlchemy session
        limit: Maximum number of jobs to return
    
    Returns:
        List of Job objects
    """
    return (
        db.query(Job)
        .filter(Job.is_new == True)
        .order_by(Job.scraped_at.desc())
        .limit(limit)
        .all()
    )


def mark_jobs_as_seen(db: Session, job_ids: list[int]) -> None:
    """Mark jobs as seen (is_new=False) after they've been sent in a digest.
    
    Args:
        db: SQLAlchemy session
        job_ids: List of job IDs to mark as seen
    """
    if not job_ids:
        return
    
    try:
        db.query(Job).filter(Job.id.in_(job_ids)).update({Job.is_new: False})
        logger.info(f"Marked {len(job_ids)} jobs as seen")
    except Exception as e:
        logger.error(f"Failed to mark jobs as seen: {e}")
        db.rollback()
        raise


def get_user_by_email(db: Session, email: str) -> User | None:
    """Retrieve a user by email address.
    
    Args:
        db: SQLAlchemy session
        email: User's email address
    
    Returns:
        User object if found, None otherwise
    """
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, email: str, hashed_password: str) -> User:
    """Create a new user in the database.
    
    Args:
        db: SQLAlchemy session
        email: User's email address (must be unique)
        hashed_password: Pre-hashed password (use passlib to hash before calling)
    
    Returns:
        New User object
    
    Raises:
        Exception: If email already exists or database error
    """
    try:
        user = User(email=email, hashed_password=hashed_password)
        db.add(user)
        db.commit()
        logger.info(f"Created user: {email}")
        return user
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        db.rollback()
        raise
