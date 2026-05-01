import json
import logging
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

# Load .env from the backend directory
load_dotenv(Path(__file__).parent / ".env")

logger = logging.getLogger(__name__)

# Create Groq client once at module level to reuse across function calls
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"), timeout=30.0)


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
		message = groq_client.chat.completions.create(
			model="llama-3.1-8b-instant",
			messages=[{"role": "user", "content": prompt}],
			temperature=0.2,
			max_tokens=300,
		)
		response_text = message.choices[0].message.content
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
	logger.info(f"Starting to score {len(jobs)} jobs")
	scored_jobs = []

	for idx, job in enumerate(jobs, start=1):
		job_title = job.get("title", "Unknown")
		logger.info(f"Scoring job {idx}/{len(jobs)}: {job_title} at {job.get('company', 'Unknown')}")
		scored_job = score_job(job, profile_text)
		scored_jobs.append(scored_job)

	# Sort by score descending
	scored_jobs.sort(key=lambda x: x.get("score", 0.0), reverse=True)
	logger.info(f"Scoring complete. Sorted {len(scored_jobs)} jobs by score")
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
