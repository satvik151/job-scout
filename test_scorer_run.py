"""
Quick test run of scorer.py to verify Groq API integration.
"""
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
from scorer import score_jobs

# Load environment variables
load_dotenv(Path(__file__).parent / "backend" / ".env")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Sample profile
profile_text = """
Software Engineer with 5 years of experience in Python and backend development.
Proficient in FastAPI, PostgreSQL, AWS, and Docker.
Experienced with REST APIs and microservices architecture.
Looking for senior backend or full-stack roles.
"""

# Sample jobs to score
test_jobs = [
    {
        "title": "Senior Backend Engineer",
        "company": "TechCorp",
        "description": "Build and maintain scalable backend services using Python and FastAPI. Work with AWS, PostgreSQL, and Docker in a microservices environment.",
        "skills": ["Python", "FastAPI", "PostgreSQL", "AWS", "Docker"],
        "url": "https://example.com/job1",
    },
    {
        "title": "Junior Frontend Developer",
        "company": "WebStudio",
        "description": "Create responsive web interfaces using React and Vue.js. Work with modern CSS frameworks.",
        "skills": ["React", "Vue.js", "CSS", "JavaScript"],
        "url": "https://example.com/job2",
    },
    {
        "title": "Full Stack Developer",
        "company": "StartupXYZ",
        "description": "Build full-stack applications with FastAPI backend and React frontend. Deploy to AWS.",
        "skills": ["Python", "FastAPI", "React", "PostgreSQL", "AWS"],
        "url": "https://example.com/job3",
    },
]

print("=" * 70)
print("TESTING job-scout SCORER")
print("=" * 70)
print(f"\nProfile: {profile_text[:80]}...")
print(f"\nScoring {len(test_jobs)} test jobs...\n")

# Score jobs
results = score_jobs(test_jobs, profile_text)

# Display results
print("\n" + "=" * 70)
print("RESULTS (sorted by score, descending)")
print("=" * 70)

for idx, job in enumerate(results, 1):
    print(f"\n{idx}. {job['title']} at {job['company']}")
    print(f"   Score: {job.get('score', 'N/A')}/10.0")
    print(f"   Skills Match: {job.get('skills_match_pct', 'N/A')}%")
    print(f"   Seniority Fit: {job.get('seniority_fit', 'N/A')}")
    print(f"   Missing Skills: {job.get('missing_skills', [])}")
    print(f"   Reason: {job.get('reason', 'N/A')}")

print("\n" + "=" * 70)
print(f"Test complete. Top match: {results[0]['title']} (score: {results[0].get('score', 'N/A')})")
print("=" * 70)
