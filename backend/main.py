import json
import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .database import init_db, get_db
from .models import upsert_job, get_new_jobs, mark_jobs_as_seen
from .scraper import scrape_internshala_jobs
from .scorer import score_jobs
from .digest import format_digest, send_digest

# Load environment variables FIRST before any other imports
load_dotenv(Path(__file__).parent / ".env")


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
	"""FastAPI lifespan context manager for startup/shutdown events.
	
	Replaces deprecated @app.on_event("startup") pattern.
	init_db() is called before the app starts serving requests.
	"""
	init_db()
	yield
	# Shutdown logic would go here if needed


app = FastAPI(lifespan=lifespan)

# Enable CORS for frontend to call this API from browser
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

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

# TODO: replace with real resume text or load from file
CANDIDATE_PROFILE = """
Software Engineer with experience in Python, FastAPI, SQL, and cloud platforms.
Interested in backend and full-stack roles.
"""

MAX_JOBS = 10


@app.get("/")
def root():
	return {"status": "job-scout is alive"}


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
	# Use explicit field extraction to avoid leaking SQLAlchemy's _sa_instance_state
	new_jobs_as_dicts = [
		{
			"id": j.id,
			"title": j.title,
			"company": j.company,
			"url": j.url,
			"url_hash": j.url_hash,
			"description": j.description,
			"skills": json.loads(j.skills or "[]"),
			"missing_skills": json.loads(j.missing_skills or "[]"),
			"score": j.score,
			"skills_match_pct": j.skills_match_pct,
			"seniority_fit": j.seniority_fit,
			"reason": j.reason,
			"scraped_at": j.scraped_at,
			"is_new": j.is_new,
		}
		for j in new_db_jobs
	]

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
	# Use explicit field extraction to avoid leaking SQLAlchemy's _sa_instance_state
	jobs_to_score = [
		{
			"id": j.id,
			"title": j.title,
			"company": j.company,
			"url": j.url,
			"url_hash": j.url_hash,
			"description": j.description,
			"skills": json.loads(j.skills or "[]"),
			"missing_skills": json.loads(j.missing_skills or "[]"),
			"score": j.score,
			"skills_match_pct": j.skills_match_pct,
			"seniority_fit": j.seniority_fit,
			"reason": j.reason,
			"scraped_at": j.scraped_at,
			"is_new": j.is_new,
		}
		for j in new_db_jobs
	]

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
			logger.info(f"Marked {len(seen_ids)} jobs as seen")
	else:
		logger.warning("Digest NOT sent to %s", recipient)

	logger.info("DIGEST PIPELINE COMPLETE — sent=%s", sent)

	return {"sent": bool(sent), "recipient": recipient, "jobs_in_digest": len(top_jobs)}
