import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from groq import Groq

logger = logging.getLogger(__name__)

# Temporary debug limit: when >0 only the first N jobs are scored
# Loaded from environment variable, default to 0 (no limit)
DEBUG_LIMIT = int(os.getenv("DEBUG_LIMIT", "0"))

# Module-level cache for Groq client (lazy initialization)
_groq_client = None


def get_groq_client():
    """Lazily create and cache a Groq client using the environment-provided API key.

    Raises:
        ValueError: if `GROQ_API_KEY` is not present in the environment.
    """
    global _groq_client
    
    if _groq_client is not None:
        return _groq_client
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not loaded")
    
    _groq_client = Groq(api_key=api_key, timeout=30.0)
    return _groq_client


def _failed_score(job: dict) -> dict:
    """
    Return a job with safe default failure values for all score fields.
    """
    return {
        **job,
        "score": 0.0,
        "skills_match_pct": 0,
        "missing_skills": [],
        "seniority_fit": "good fit",
        "reason": "scoring failed",
    }


def validate_score_data(data: dict) -> dict:
    """
    Validate and clamp score data returned from LLM.
    
    Ensures all required keys exist with safe defaults and valid ranges.
    """
    required_keys = {
        "score": 0.0,
        "skills_match_pct": 0,
        "missing_skills": [],
        "seniority_fit": "good fit",
        "reason": "scoring failed",
    }
    
    validated = {}
    
    # Clamp score to 0.0–10.0
    score = data.get("score", required_keys["score"])
    try:
        score = float(score)
        validated["score"] = min(max(score, 0.0), 10.0)
    except (ValueError, TypeError):
        validated["score"] = required_keys["score"]
    
    # Clamp skills_match_pct to 0–100
    skills_match = data.get("skills_match_pct", required_keys["skills_match_pct"])
    try:
        skills_match = int(skills_match)
        validated["skills_match_pct"] = min(max(skills_match, 0), 100)
    except (ValueError, TypeError):
        validated["skills_match_pct"] = required_keys["skills_match_pct"]
    
    # Ensure missing_skills is a list
    missing_skills = data.get("missing_skills", required_keys["missing_skills"])
    if isinstance(missing_skills, list):
        validated["missing_skills"] = missing_skills
    else:
        validated["missing_skills"] = required_keys["missing_skills"]
    
    # Validate seniority_fit is one of three valid values
    valid_fits = {"good fit", "overqualified", "underqualified"}
    seniority_fit = data.get("seniority_fit", required_keys["seniority_fit"])
    if seniority_fit in valid_fits:
        validated["seniority_fit"] = seniority_fit
    else:
        validated["seniority_fit"] = required_keys["seniority_fit"]
    
    # Include reason as-is, fallback to default if missing
    reason = data.get("reason", required_keys["reason"])
    validated["reason"] = str(reason) if reason else required_keys["reason"]
    
    return validated


def _parse_scraped_at(scraped_at):
    """Parse scraped_at values from datetime objects or ISO strings."""
    if isinstance(scraped_at, datetime):
        return scraped_at

    if isinstance(scraped_at, str):
        text = scraped_at.strip()
        if not text:
            return None

        normalized = text.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            return None

    return None


def _freshness_bonus_from_scraped_at(scraped_at) -> float:
    """Compute a freshness bonus based on how recently a job was scraped."""
    parsed_scraped_at = _parse_scraped_at(scraped_at)
    if parsed_scraped_at is None:
        return 0.5

    today = datetime.now(timezone.utc).date()

    if parsed_scraped_at.tzinfo is None:
        scraped_date = parsed_scraped_at.date()
    else:
        scraped_date = parsed_scraped_at.astimezone(timezone.utc).date()

    days_old = (today - scraped_date).days
    if days_old <= 0:
        return 1.0
    if days_old == 1:
        return 0.8
    if days_old == 2:
        return 0.6
    return 0.2


def compute_final_score(job: dict) -> float:
    """Combine LLM score and freshness into a single ranking score."""
    try:
        llm_score = float(job.get("score", 0.0))
    except (TypeError, ValueError):
        llm_score = 0.0

    freshness_bonus = _freshness_bonus_from_scraped_at(job.get("scraped_at"))
    final_score = (llm_score * 0.6) + (freshness_bonus * 10 * 0.4)
    return round(float(final_score), 2)


def score_job(job: dict, profile_text: str) -> dict:
    """
    Score a single job posting against a candidate profile using Groq API.
    
    Args:
        job: Dictionary with keys: title, company, description, skills
        profile_text: Candidate's profile/resume text
    
    Returns:
        Original job dict merged with scoring fields: score, skills_match_pct,
        missing_skills, seniority_fit, reason
    """
    # Debug: confirm key presence at call time
    logger.info(f"GROQ key present: {bool(os.getenv('GROQ_API_KEY'))}")
    try:
        client = get_groq_client()
    except Exception as e:
        logger.error(f"Failed to initialize Groq client: {e}")
        return _failed_score(job)
    
    prompt = f"""Analyze this job posting against the candidate's profile.
Return ONLY valid JSON (no markdown, no backticks, no explanation).

JOB POSTING:
Title: {job.get('title', '')}
Company: {job.get('company', '')}
Description: {job.get('description', '')}
Required Skills: {', '.join(job.get('skills', []))}

CANDIDATE PROFILE:
{profile_text}

Return strictly valid JSON only. Do not include markdown, backticks, code fences, or any explanation.
Your entire response must be parseable by json.loads()

JSON must have exactly these fields:
{{
    "score": <float 0.0 to 10.0>,
    "skills_match_pct": <integer 0 to 100>,
    "missing_skills": <list of strings>,
    "seniority_fit": <"good fit" or "overqualified" or "underqualified">,
    "reason": <string under 100 words>
}}"""

    try:
        api_start = time.perf_counter()
        message = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=300,
        )
        api_elapsed = time.perf_counter() - api_start
        response_text = message.choices[0].message.content
        logger.debug(f"Groq call for '{job.get('title')}' took {api_elapsed:.2f}s")
    except Exception as e:
        logger.error(f"Groq API error for job '{job.get('title')}': {e}")
        return _failed_score(job)

    # Try parsing as-is first
    try:
        score_data = json.loads(response_text)
    except json.JSONDecodeError:
        # Fallback: strip markdown fences with stronger regex
        logger.debug(f"JSON parse failed, attempting markdown strip for job '{job.get('title')}'")
        cleaned = re.sub(r'```(?:json)?\s*|\s*```', '', response_text).strip()
        try:
            score_data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse score data for job '{job.get('title')}' "
                f"even after markdown strip: {e}"
            )
            return _failed_score(job)

    # Validate and clamp all score fields
    validated_data = validate_score_data(score_data)
    return {**job, **validated_data}


def score_jobs(jobs: list, profile_text: str) -> list:
    """
    Score a list of jobs and return sorted by score descending.
    
    Args:
        jobs: List of job dictionaries
        profile_text: Candidate's profile/resume text
    
    Returns:
        List of jobs with scoring fields, sorted by score (descending)
    """
    total_to_score = len(jobs)
    if DEBUG_LIMIT and DEBUG_LIMIT > 0:
        logger.info(f"DEBUG_LIMIT={DEBUG_LIMIT} enabled — scoring only first {min(DEBUG_LIMIT, total_to_score)} jobs")
        jobs_to_process = jobs[:DEBUG_LIMIT]
    else:
        jobs_to_process = jobs

    logger.info(f"Starting to score {len(jobs_to_process)} jobs (original count {len(jobs)})")
    scored_jobs = []

    scoring_start = time.perf_counter()
    for idx, job in enumerate(jobs_to_process, start=1):
        job_title = job.get("title", "Unknown")
        logger.info(f"Scoring job {idx}/{len(jobs_to_process)}: {job_title} at {job.get('company', 'Unknown')}")
        job_start = time.perf_counter()
        scored_job = score_job(job, profile_text)
        job_elapsed = time.perf_counter() - job_start
        if job_elapsed > 3.0:
            logger.warning(f"Scoring job '{job_title}' took too long: {job_elapsed:.2f}s (>3s)")
        else:
            logger.debug(f"Scored job '{job_title}' in {job_elapsed:.2f}s")
        scored_jobs.append(scored_job)

    scoring_elapsed = time.perf_counter() - scoring_start
    logger.info(f"Scoring complete. Scored {len(scored_jobs)} jobs in {scoring_elapsed:.2f}s")

    for job in scored_jobs:
        job["final_score"] = compute_final_score(job)

    # Sort by final score descending
    scored_jobs.sort(key=lambda x: x.get("final_score", 0.0), reverse=True)
    logger.info("Jobs sorted by final_score (descending)")

    if scored_jobs:
        top_job = scored_jobs[0]
        top_freshness_bonus = _freshness_bonus_from_scraped_at(top_job.get("scraped_at"))
        logger.info(
            "Top ranked job: %s | llm_score=%.2f | freshness_bonus=%.2f | final_score=%.2f",
            top_job.get("title", "Unknown"),
            float(top_job.get("score", 0.0) or 0.0),
            top_freshness_bonus,
            float(top_job.get("final_score", 0.0) or 0.0),
        )
    return scored_jobs


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    sample_profile = """
    Software Engineer with 5 years experience in Python and JavaScript.
    Skilled in FastAPI, React, PostgreSQL, and AWS.
    Looking for backend or full-stack roles.
    """

    sample_jobs = [
        {
            "title": "Backend Engineer",
            "company": "Tech Startup",
            "description": "Build scalable APIs using FastAPI and PostgreSQL",
            "skills": ["Python", "FastAPI", "PostgreSQL"],
            "url": "https://example.com/job1",
        },
        {
            "title": "Frontend Developer",
            "company": "Web Agency",
            "description": "Build responsive web apps with React and Vue",
            "skills": ["React", "Vue", "CSS", "JavaScript"],
            "url": "https://example.com/job2",
        },
    ]

    results = score_jobs(sample_jobs, sample_profile)
    print(f"\nTop job: {results[0]['title']} - Score: {results[0].get('score', 'N/A')}")
