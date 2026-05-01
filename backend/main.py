import logging
import os
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables FIRST before any other imports
load_dotenv(Path(__file__).parent / ".env")

# If dotenv didn't populate required variables (some runtimes/encodings),
# attempt a safe manual fallback to read the .env and set any missing keys.
env_path = Path(__file__).parent / ".env"
if env_path.exists():
	try:
		with env_path.open("r", encoding="utf-8") as f:
			for raw in f:
				line = raw.strip()
				if not line or line.startswith("#"):
					continue
				if "=" not in line:
					continue
				k, v = line.split("=", 1)
				k = k.strip()
				v = v.strip().strip('"').strip("'")
				if k and not os.getenv(k):
					os.environ[k] = v
        
	except Exception:
		# best-effort: don't crash the import if manual load fails
		pass

from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Body
from pydantic import BaseModel

from .scraper import scrape_internshala_jobs
from .scorer import score_jobs
from .digest import format_digest, send_digest

logger = logging.getLogger(__name__)

app = FastAPI()

# Debug: log that env vars are loaded
logger.info(f"GROQ_API_KEY loaded: {bool(os.getenv('GROQ_API_KEY'))}")
logger.info(f"RESEND_API_KEY loaded: {bool(os.getenv('RESEND_API_KEY'))}")
logger.info(f"SENDER_EMAIL loaded: {bool(os.getenv('SENDER_EMAIL'))}")
logger.info(f"DIGEST_EMAIL loaded: {bool(os.getenv('DIGEST_EMAIL'))}")

# ENV sanity-check at startup
logger.info(f"ENV CHECK: GROQ_API_KEY present = {bool(os.getenv('GROQ_API_KEY'))}")

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
	# Provide default for DIGEST_EMAIL if not set
	if "DIGEST_EMAIL" in missing:
		os.environ.setdefault("DIGEST_EMAIL", "satvikislegendary@gmail.com")
		logger.info("Defaulted DIGEST_EMAIL to satvikislegendary@gmail.com")

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
def get_jobs(pages: int = Query(default=2, ge=1, le=10)):
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

	try:
		logger.info("Starting job scoring")
		score_start = time.perf_counter()
		scored_jobs = score_jobs(jobs, CANDIDATE_PROFILE)
		score_elapsed = time.perf_counter() - score_start
		logger.info("Finished job scoring in %.2fs", score_elapsed)
	except Exception as e:
		logger.error("Scoring failed: %s", e)
		raise HTTPException(status_code=500, detail="Scoring failed — check logs")

	total_elapsed = time.perf_counter() - request_start
	logger.info("Summary: Scrape: %.2fs | Score: %.2fs | Total: %.2fs", scrape_elapsed, score_elapsed, total_elapsed)

	top_jobs = scored_jobs[:MAX_JOBS]
	return {
		"total_scraped": total_scraped,
		"returned": len(top_jobs),
		"jobs": top_jobs,
	}


class DigestRequest(BaseModel):
    recipient_email: Optional[str] = None


@app.post("/send-digest")
def send_digest_endpoint(payload: DigestRequest = Body(default=None)):
    """Run a full pipeline: scrape -> score (limited) -> format -> send digest.

    Notes: slow operation due to scraping + LLM calls. Keep limits low.
    """
    # Determine recipient
    if payload and payload.recipient_email:
        recipient = payload.recipient_email
    else:
        recipient = os.getenv("DIGEST_EMAIL", "satvikislegendary@gmail.com")

    logger.info("/send-digest called. Recipient: %s", recipient)

    # Scrape (safeguard: limit pages to 1 for debug)
    logger.info("Starting scrape for digest (max_pages=1)")
    scrape_start = time.perf_counter()
    jobs = scrape_internshala_jobs(max_pages=1)
    scrape_elapsed = time.perf_counter() - scrape_start
    logger.info("Scrape finished: %d jobs found (%.2fs)", len(jobs), scrape_elapsed)

    # Score (limit to first 3 for safety)
    jobs_to_score = jobs[:3]
    logger.info("Scoring up to %d jobs for digest", len(jobs_to_score))
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
    else:
        logger.warning("Digest NOT sent to %s", recipient)

    logger.info("DIGEST PIPELINE COMPLETE — sent=%s", sent)

    return {"sent": bool(sent), "recipient": recipient, "jobs_in_digest": len(top_jobs)}
