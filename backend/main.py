import json
import logging
import os
import time
import threading
import io
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Body, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from PyPDF2 import PdfReader

from .database import init_db, get_db, SessionLocal
from .models import upsert_job, get_new_jobs, mark_jobs_as_seen, User
from .scraper import scrape_internshala_jobs
from .scorer import score_jobs
from .digest import format_digest, send_digest
from .auth import (
	UserCreate, UserLogin, TokenResponse, UserResponse,
	get_user_by_email, create_user, authenticate_user,
	create_access_token, decode_access_token
)

# Load environment variables FIRST before any other imports
load_dotenv(Path(__file__).parent / ".env")


logger = logging.getLogger(__name__)


def _job_to_scoring_dict(job) -> dict:
	return {
		"id": job.id,
		"title": job.title,
		"company": job.company,
		"url": job.url,
		"url_hash": job.url_hash,
		"description": job.description,
		"skills": json.loads(job.skills or "[]"),
		"missing_skills": json.loads(job.missing_skills or "[]"),
		"score": job.score,
		"skills_match_pct": job.skills_match_pct,
		"seniority_fit": job.seniority_fit,
		"reason": job.reason,
		"scraped_at": job.scraped_at,
		"is_new": job.is_new,
	}


def run_daily_pipeline() -> None:
	"""Run scrape -> upsert -> score -> digest -> mark-seen pipeline."""
	start_time = time.perf_counter()
	db = SessionLocal()
	try:
		logger.info("Daily pipeline started")
		jobs = scrape_internshala_jobs(max_pages=2)
		logger.info("Daily pipeline scraped %d jobs", len(jobs))

		new_count = 0
		for job in jobs:
			_, is_new = upsert_job(db, job)
			if is_new:
				new_count += 1
		db.commit()
		logger.info("Daily pipeline upserted %d jobs (%d new)", len(jobs), new_count)

		new_jobs = get_new_jobs(db)
		if not new_jobs:
			logger.info("No new jobs")
			return

		jobs_to_score = [_job_to_scoring_dict(job) for job in new_jobs]
		scored_jobs = score_jobs(jobs_to_score, CANDIDATE_PROFILE)
		top_jobs = scored_jobs[:MAX_JOBS]
		body = format_digest(top_jobs)

		recipient = os.getenv("DIGEST_EMAIL")
		if not recipient:
			logger.error("DIGEST_EMAIL not configured")
			return

		sent = send_digest(recipient, body, len(top_jobs))
		if sent:
			seen_ids = [job.get("id") for job in top_jobs if job.get("id") is not None]
			if seen_ids:
				mark_jobs_as_seen(db, seen_ids)
				db.commit()
				logger.info("Daily pipeline marked %d jobs as seen", len(seen_ids))
		else:
			logger.warning("Daily pipeline did not send digest")
	except Exception:
		logger.exception("Daily pipeline failed")
	finally:
		db.close()
		elapsed = time.perf_counter() - start_time
		logger.info("Daily pipeline finished in %.2fs", elapsed)


@asynccontextmanager
async def lifespan(app: FastAPI):
	"""FastAPI lifespan context manager for startup/shutdown events.
	
	Replaces deprecated @app.on_event("startup") pattern.
	init_db() is called before the scheduler to ensure tables exist.
	"""
	init_db()
	scheduler = BackgroundScheduler()
	scheduler.add_job(
		run_daily_pipeline,
		CronTrigger(hour=9, minute=0, timezone=ZoneInfo("Asia/Kolkata")),
		id="daily_pipeline",
		replace_existing=True,
	)
	scheduler.start()
	try:
		yield
	finally:
		scheduler.shutdown(wait=False)


app = FastAPI(lifespan=lifespan)

# Enable CORS for frontend to call this API from browser
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# OAuth2 scheme for JWT tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
	token: str = Depends(oauth2_scheme),
	db: Session = Depends(get_db)
) -> User:
	"""Dependency to extract and validate JWT token from Authorization header.
	
	Extract "Authorization: Bearer <token>" from request headers.
	Decode token and fetch user from database.
	
	Args:
		token: JWT token from Authorization header (extracted by oauth2_scheme)
		db: Database session
	
	Returns:
		User object if token is valid
	
	Raises:
		HTTPException 401: If token is invalid, expired, or user not found
	"""
	payload = decode_access_token(token)
	if not payload:
		raise HTTPException(
			status_code=401,
			detail="Invalid or expired token",
			headers={"WWW-Authenticate": "Bearer"},
		)
	
	email = payload.get("sub")
	if not email:
		raise HTTPException(
			status_code=401,
			detail="Token missing 'sub' claim",
			headers={"WWW-Authenticate": "Bearer"},
		)
	
	user = get_user_by_email(db, email)
	if not user:
		raise HTTPException(
			status_code=401,
			detail="User not found",
			headers={"WWW-Authenticate": "Bearer"},
		)
	
	return user


# Startup validation: check required env vars and warn if missing
REQUIRED_ENVS = [
	"GROQ_API_KEY",
	"RESEND_API_KEY",
	"SENDER_EMAIL",
	"DIGEST_EMAIL",
]
missing = [name for name in REQUIRED_ENVS if not os.getenv(name)]
if missing:
	logger.warning("Missing environment variables: %s", missing)

# Load candidate profile from file or use fallback
profile_path = Path(__file__).parent / "profile.txt"
if profile_path.exists():
	CANDIDATE_PROFILE = profile_path.read_text()
	logger.info(f"Profile loaded from {profile_path}: {len(CANDIDATE_PROFILE)} characters")
else:
	logger.warning("profile.txt not found — using fallback profile")
	CANDIDATE_PROFILE = "Python developer with backend experience"

MAX_JOBS = 10


@app.get("/")
def root():
	return {"status": "job-scout is alive"}


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/auth/register", response_model=UserResponse)
def register(payload: UserCreate, db: Session = Depends(get_db)):
	"""Register a new user.
	
	Args:
		payload: UserCreate schema (email + password)
		db: Database session
	
	Returns:
		UserResponse with new user's info (no hashed_password exposed)
	
	Raises:
		HTTPException 400: If email already registered
	"""
	logger.info(f"POST /auth/register: email={payload.email}")
	
	# Check if email already exists
	existing_user = get_user_by_email(db, payload.email)
	if existing_user:
		logger.warning(f"Registration failed: email {payload.email} already registered")
		raise HTTPException(
			status_code=400,
			detail="Email already registered"
		)
	
	# Create new user (password is hashed inside create_user)
	try:
		user = create_user(db, payload.email, payload.password)
		logger.info(f"User registered: {payload.email} (id={user.id})")
		return UserResponse(
			id=user.id,
			email=user.email,
			has_resume=user.resume_text is not None
		)
	except Exception as e:
		logger.error(f"User creation failed: {e}")
		raise HTTPException(status_code=500, detail="User creation failed")


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
	"""Authenticate user and return JWT token.
	
	Args:
		payload: UserLogin schema (email + password)
		db: Database session
	
	Returns:
		TokenResponse with access_token (JWT) and token_type="bearer"
	
	Raises:
		HTTPException 401: If email not found or password incorrect
	"""
	logger.info(f"POST /auth/login: email={payload.email}")
	
	# Authenticate user
	user = authenticate_user(db, payload.email, payload.password)
	if not user:
		logger.warning(f"Login failed: invalid credentials for {payload.email}")
		raise HTTPException(
			status_code=401,
			detail="Invalid credentials"
		)
	
	# Create JWT token
	access_token = create_access_token({
		"sub": user.email,
		"user_id": user.id
	})
	
	logger.info(f"Login successful: {payload.email}")
	return TokenResponse(access_token=access_token, token_type="bearer")


@app.get("/auth/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
	"""Get current authenticated user's info.
	
	Protected endpoint: requires valid JWT in Authorization header.
	
	Args:
		current_user: Current user (extracted from JWT token via dependency)
	
	Returns:
		UserResponse with user's info
	"""
	logger.info(f"GET /auth/me: user={current_user.email}")
	return UserResponse(
		id=current_user.id,
		email=current_user.email,
		has_resume=current_user.resume_text is not None
	)


@app.post("/auth/upload-resume")
async def upload_resume(
	file: UploadFile = File(...),
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db)
):
	"""Upload and extract text from a PDF resume.
	
	Protected endpoint: requires valid JWT in Authorization header.
	
	Args:
		file: PDF file upload from form-data
		current_user: Current authenticated user
		db: Database session
	
	Returns:
		JSON with success message and character count
	
	Raises:
		HTTPException 400: If not a PDF or text extraction fails
	"""
	logger.info(f"POST /auth/upload-resume: user={current_user.email}, file={file.filename}")
	
	# Validate file type
	if file.content_type != "application/pdf":
		logger.warning(f"Upload failed: wrong content-type {file.content_type}")
		raise HTTPException(
			status_code=400,
			detail="Only PDF files accepted"
		)
	
	# Read file bytes
	try:
		file_bytes = await file.read()
		logger.debug(f"File read: {len(file_bytes)} bytes")
	except Exception as e:
		logger.error(f"Failed to read file: {e}")
		raise HTTPException(status_code=400, detail="Failed to read file")
	
	# Extract text from PDF
	try:
		pdf_reader = PdfReader(io.BytesIO(file_bytes))
		extracted_text = "".join(
			page.extract_text() or "" for page in pdf_reader.pages
		)
		logger.info(f"Extracted {len(extracted_text)} characters from PDF")
	except Exception as e:
		logger.error(f"PDF extraction failed: {e}")
		raise HTTPException(
			status_code=400,
			detail="Could not extract text from PDF"
		)
	
	# Validate extracted text
	if not extracted_text or len(extracted_text) < 50:
		logger.warning(f"Extracted text too short: {len(extracted_text)} chars")
		raise HTTPException(
			status_code=400,
			detail="Could not extract text from PDF"
		)
	
	# Store in database
	try:
		current_user.resume_text = extracted_text
		db.commit()
		logger.info(f"Resume uploaded for {current_user.email}: {len(extracted_text)} chars")
		return {
			"message": "Resume uploaded",
			"characters_extracted": len(extracted_text)
		}
	except Exception as e:
		logger.error(f"Database update failed: {e}")
		db.rollback()
		raise HTTPException(status_code=500, detail="Failed to save resume")




@app.get("/jobs")
def get_jobs(pages: int = Query(default=2, ge=1, le=10), db: Session = Depends(get_db)):
	request_start = time.perf_counter()
	logger.info("/jobs endpoint called with pages=%s", pages)

	# Scrape
	scrape_start = time.perf_counter()
	jobs = scrape_internshala_jobs(max_pages=pages)
	scrape_elapsed = time.perf_counter() - scrape_start
	total_scraped = len(jobs)
	logger.info("Total jobs scraped: %s", total_scraped)
	if scrape_elapsed > 5.0:
		logger.warning("Scraper duration warning: %.2fs (>5s)", scrape_elapsed)

	if not jobs:
		logger.warning("Scraper returned 0 jobs")
		return {"total_scraped": 0, "returned": 0, "jobs": []}

	# Upsert all scraped jobs into database (deduplication happens here)
	upsert_start = time.perf_counter()
	new_count = 0
	for job in jobs:
		_, is_new = upsert_job(db, job)
		if is_new:
			new_count += 1
	db.commit()
	upsert_elapsed = time.perf_counter() - upsert_start
	logger.info(f"Upserted {len(jobs)} jobs ({new_count} new) in {upsert_elapsed:.2f}s")

	# Score only new jobs for the response
	new_db_jobs = get_new_jobs(db, limit=MAX_JOBS)
	if not new_db_jobs:
		logger.warning("No new jobs to score")
		return {"total_scraped": total_scraped, "returned": 0, "jobs": []}

	# Convert DB rows back to dicts for scorer — parse JSON fields
	new_jobs_as_dicts = [_job_to_scoring_dict(j) for j in new_db_jobs]

	try:
		logger.info("Starting job scoring for %d new jobs", len(new_jobs_as_dicts))
		score_start = time.perf_counter()
		scored_jobs = score_jobs(new_jobs_as_dicts, CANDIDATE_PROFILE)
		score_elapsed = time.perf_counter() - score_start
		logger.info("Finished job scoring in %.2fs", score_elapsed)
	except Exception as e:
		logger.error("Scoring failed: %s", e)
		raise HTTPException(status_code=500, detail="Scoring failed — check logs")

	total_elapsed = time.perf_counter() - request_start
	logger.info("Summary: Scrape: %.2fs | Upsert: %.2fs | Score: %.2fs | Total: %.2fs", 
		   scrape_elapsed, upsert_elapsed, score_elapsed, total_elapsed)

	top_jobs = scored_jobs[:MAX_JOBS]
	return {
		"total_scraped": total_scraped,
		"returned": len(top_jobs),
		"jobs": top_jobs,
	}


class DigestRequest(BaseModel):
    recipient_email: Optional[str] = None


@app.post("/send-digest")
def send_digest_endpoint(payload: DigestRequest = Body(default=None), db: Session = Depends(get_db)):
	"""Run a full pipeline: scrape -> upsert -> score (limited) -> format -> send digest.
	
	After sending, marks the sent jobs as seen so they don't appear in future digests.
	Notes: slow operation due to scraping + LLM calls. Keep limits low.
	"""
	# Determine recipient
	if payload and payload.recipient_email:
		recipient = payload.recipient_email
	else:
		recipient = os.getenv("DIGEST_EMAIL")
		if not recipient:
			raise HTTPException(status_code=500, detail="DIGEST_EMAIL not configured")

	logger.info("/send-digest called. Recipient: %s", recipient)

	# Scrape (safeguard: limit pages to 1 for debug)
	logger.info("Starting scrape for digest (max_pages=1)")
	scrape_start = time.perf_counter()
	jobs = scrape_internshala_jobs(max_pages=1)
	scrape_elapsed = time.perf_counter() - scrape_start
	logger.info("Scrape finished: %d jobs found (%.2fs)", len(jobs), scrape_elapsed)

	# Upsert scraped jobs and commit
	new_count = 0
	for job in jobs:
		_, is_new = upsert_job(db, job)
		if is_new:
			new_count += 1
	db.commit()
	logger.info(f"Upserted {len(jobs)} jobs ({new_count} new) for digest")

	# Score only new jobs (limit to first 3 for safety)
	new_db_jobs = get_new_jobs(db, limit=3)
	if not new_db_jobs:
		logger.info("No new jobs available for digest")
		return {"sent": False, "recipient": recipient, "jobs_in_digest": 0}

	# Convert DB rows to dicts for scorer
	jobs_to_score = [_job_to_scoring_dict(j) for j in new_db_jobs]

	logger.info("Scoring %d jobs for digest", len(jobs_to_score))
	try:
		score_start = time.perf_counter()
		scored = score_jobs(jobs_to_score, CANDIDATE_PROFILE)
		score_elapsed = time.perf_counter() - score_start
		logger.info("Scoring finished (%.2fs)", score_elapsed)
	except Exception as e:
		logger.error("Scoring failed during /send-digest: %s", e)
		raise HTTPException(status_code=500, detail="Scoring failed — check logs")

	top_jobs = scored[:MAX_JOBS]

	# Format
	logger.info("Formatting digest for %d jobs", len(top_jobs))
	body = format_digest(top_jobs)

	# Send
	logger.info("Sending digest to %s", recipient)
	sent = send_digest(recipient, body, len(top_jobs))
	if sent:
		logger.info("Digest sent to %s", recipient)
		# Mark the sent jobs as seen so they don't appear in future digests
		seen_ids = [j.get("id") for j in top_jobs if "id" in j]
		if seen_ids:
			mark_jobs_as_seen(db, seen_ids)
			db.commit()
			logger.info(f"Marked {len(seen_ids)} jobs as seen")
	else:
		logger.warning("Digest NOT sent to %s", recipient)

	logger.info("DIGEST PIPELINE COMPLETE — sent=%s", sent)

	return {"sent": bool(sent), "recipient": recipient, "jobs_in_digest": len(top_jobs)}


@app.post("/run-pipeline")
def run_pipeline_endpoint():
	threading.Thread(target=run_daily_pipeline, daemon=True).start()
	return {"started": True}
