"""Authentication module: JWT tokens, password hashing, and user schemas."""
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .models import User

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

SECRET_KEY = os.getenv("SECRET_KEY", "changeme-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# ============================================================================
# PASSWORD HASHING
# ============================================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
	"""Hash a plain text password using bcrypt.
	
	Args:
		plain: Plain text password
	
	Returns:
		Hashed password (bcrypt format, ~60 chars)
	"""
	return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
	"""Verify a plain text password against a hashed password.
	
	Args:
		plain: Plain text password to verify
		hashed: Hashed password from database
	
	Returns:
		True if password is correct, False otherwise
	"""
	return pwd_context.verify(plain, hashed)


# ============================================================================
# JWT TOKEN FUNCTIONS
# ============================================================================


def create_access_token(data: dict) -> str:
	"""Create a signed JWT access token.
	
	Args:
		data: Dictionary to encode in token (e.g., {"sub": user_email})
	
	Returns:
		Encoded JWT token string
	"""
	to_encode = data.copy()
	expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
	to_encode.update({"exp": expire})
	
	encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
	logger.debug(f"Created access token for {data.get('sub', 'unknown')}")
	return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
	"""Decode and validate a JWT access token.
	
	Args:
		token: JWT token string to decode
	
	Returns:
		Payload dictionary if valid, None if expired or invalid
	"""
	try:
		payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
		return payload
	except JWTError as e:
		logger.debug(f"Token validation failed: {e}")
		return None


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================


class UserCreate(BaseModel):
	"""Schema for user registration request."""
	email: str
	password: str


class UserLogin(BaseModel):
	"""Schema for user login request."""
	email: str
	password: str


class TokenResponse(BaseModel):
	"""Schema for token response."""
	access_token: str
	token_type: str = "bearer"


class UserResponse(BaseModel):
	"""Schema for user info response."""
	id: int
	email: str
	has_resume: bool
	
	@property
	def has_resume(self) -> bool:
		"""Computed property: True if user has uploaded a resume."""
		return self.resume_text is not None
	
	class Config:
		from_attributes = True


# ============================================================================
# DATABASE HELPERS (using models.py functions)
# ============================================================================


def get_user_by_email(db: Session, email: str) -> Optional[User]:
	"""Retrieve a user by email address.
	
	Args:
		db: SQLAlchemy session
		email: User's email address
	
	Returns:
		User object if found, None otherwise
	"""
	from .models import get_user_by_email as db_get_user_by_email
	return db_get_user_by_email(db, email)


def create_user(db: Session, email: str, password: str) -> User:
	"""Create a new user with hashed password.
	
	Args:
		db: SQLAlchemy session
		email: User's email address (must be unique)
		password: Plain text password (will be hashed)
	
	Returns:
		New User object
	
	Raises:
		Exception: If email already exists or database error
	"""
	hashed_pwd = hash_password(password)
	from .models import create_user as db_create_user
	return db_create_user(db, email, hashed_pwd)


# ============================================================================
# UTILITY: Authenticate user
# ============================================================================


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
	"""Authenticate a user by email and password.
	
	Args:
		db: SQLAlchemy session
		email: User's email
		password: Plain text password
	
	Returns:
		User object if authentication successful, None otherwise
	"""
	user = get_user_by_email(db, email)
	if not user:
		return None
	if not verify_password(password, user.hashed_password):
		return None
	return user
