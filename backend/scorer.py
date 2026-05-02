import json
import logging
import os
import re
import time
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

    # Sort by score descending
    scored_jobs.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    logger.info(f"Jobs sorted by score (descending)")
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
