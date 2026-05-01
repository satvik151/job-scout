import logging

from fastapi import FastAPI, HTTPException, Query

from .scraper import scrape_internshala_jobs
from .scorer import score_jobs

logger = logging.getLogger(__name__)

app = FastAPI()

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
	logger.info("/jobs endpoint called with pages=%s", pages)

	jobs = scrape_internshala_jobs(max_pages=pages)
	total_scraped = len(jobs)
	logger.info("Total jobs scraped: %s", total_scraped)

	if not jobs:
		logger.warning("Scraper returned 0 jobs")
		return {"total_scraped": 0, "returned": 0, "jobs": []}

	try:
		logger.info("Starting job scoring")
		scored_jobs = score_jobs(jobs, CANDIDATE_PROFILE)
		logger.info("Finished job scoring")
	except Exception as e:
		logger.error("Scoring failed: %s", e)
		raise HTTPException(status_code=500, detail="Scoring failed — check logs")

	top_jobs = scored_jobs[:MAX_JOBS]
	return {
		"total_scraped": total_scraped,
		"returned": len(top_jobs),
		"jobs": top_jobs,
	}
