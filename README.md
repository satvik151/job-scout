# Job Scout

Scrape, score, and send ranked job listings via email using AI-powered candidate profile matching.

## How It Works

- **Scrape**: Fetches job listings from Internshala (up to 5 pages, ~250 jobs) with deduplication and rate limiting
- **Score**: Analyzes each job against your candidate profile using Groq LLM API (llama-3.1-8b-instant)
- **Return**: Structured scoring for each job: overall score (0-10), skills match %, missing skills, seniority fit, and reasoning
- **Email**: Formats top jobs into a plain-text digest and sends via Resend API

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.x | Core runtime |
| FastAPI | HTTP API framework & endpoints |
| BeautifulSoup4 | HTML parsing for Internshala scraping |
| Groq API | LLM for job scoring against candidate profile |
| Resend | Email service provider |
| python-dotenv | Environment variable management |

## Project Structure

```
job-scout/
├── backend/
│   ├── main.py              # FastAPI app, endpoints, orchestration
│   ├── scraper.py           # Internshala scraper with pagination & dedup
│   ├── scorer.py            # Groq LLM scoring logic
│   ├── digest.py            # Email formatting & Resend integration
│   ├── .env                 # Environment secrets (keys, emails)
│   ├── __init__.py          # Package marker
│   └── requirements.txt     # Python dependencies (for reference)
├── requirements.txt         # Python package list
├── .venv/                   # Virtual environment (git-ignored)
├── .gitignore               # Git exclusions
└── README.md                # This file
```

## Setup Instructions

### 1. Clone & Navigate
```bash
cd job-scout
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
# Windows:
.venv\Scripts\Activate.ps1
# Mac/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
Create `backend/.env` with your API keys:
```dotenv
GROQ_API_KEY=sk_...your_groq_key...
RESEND_API_KEY=re_...your_resend_key...
SENDER_EMAIL=onboarding@resend.dev
DIGEST_EMAIL=your-email@example.com
DEBUG_LIMIT=3
```

**Key Notes:**
- `GROQ_API_KEY`: Get from [console.groq.com](https://console.groq.com)
- `RESEND_API_KEY`: Get from [resend.com](https://resend.com)
- `SENDER_EMAIL`: Must be a verified domain in Resend (use `onboarding@resend.dev` for testing)
- `DIGEST_EMAIL`: Recipient address for job digests
- `DEBUG_LIMIT=3`: Limits scoring to 3 jobs for fast development; set to 0 for production

### 5. Run the Server
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

Server runs at `http://localhost:8000`

## API Endpoints

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| GET | `/` | Health check | Returns `{"status": "job-scout is alive"}` |
| GET | `/jobs?pages=2` | Scrape & score jobs | Returns array of scored job objects |
| POST | `/send-digest` | Scrape → Score (limited) → Format → Email | Returns `{"sent": true, "recipient": "...", "jobs_in_digest": 3}` |

### Example Request
```bash
curl "http://localhost:8000/jobs?pages=2"
```

### Example Response
```json
{
  "total_scraped": 100,
  "returned": 10,
  "jobs": [
    {
      "title": "Backend Engineer",
      "company": "TechCorp",
      "description": "Build APIs with Python & PostgreSQL...",
      "skills": ["Python", "FastAPI", "PostgreSQL"],
      "url": "https://internshala.com/...",
      "score": 8.5,
      "skills_match_pct": 85,
      "missing_skills": ["Docker"],
      "seniority_fit": "good fit",
      "reason": "Strong match on core tech stack; Docker experience would be beneficial."
    }
  ]
}
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | Groq API key for LLM access |
| `RESEND_API_KEY` | Yes | Resend API key for email sending |
| `SENDER_EMAIL` | Yes | Verified sender email in Resend (e.g., `onboarding@resend.dev`) |
| `DIGEST_EMAIL` | Yes | Recipient email for job digest (defaults to `satvikislegendary@gmail.com`) |
| `DEBUG_LIMIT` | No | Limit scoring to N jobs (0 = no limit, default for production) |

## What's Coming Next (Phase 3)

Phase 2 (database, deduplication, and persistence) is complete — jobs are now
stored in `backend/jobs.db`, deduplicated by an MD5 `url_hash`, and flagged as
`is_new` until included in a sent digest.

Planned Phase 3 work:

- **Scheduler**: Automatic scraping & digest sending (cron/worker)
- **Multi-User**: User accounts, per-user candidate profiles, and subscriptions
- **Web UI**: React frontend for browsing ranked jobs and managing profiles
- **Advanced Filtering**: Location, salary, experience, and skill filters
- **Analytics**: Store historical scores and show trends / match rates
- **Integrations**: Slack/Discord notifications and calendar sync for interviews

## Development Notes

- Jobs are scraped from [Internshala](https://internshala.com/jobs/) with a 1-second rate limit between pages
- Scoring uses Groq's `llama-3.1-8b-instant` model for fast, cost-effective analysis
- The `/send-digest` endpoint limits scraping to 1 page and scoring to 3 jobs for safety (prevents long-running requests)
- Change `DEBUG_LIMIT` in `.env` to disable scoring limits for full pipelines
- Email fallback: If the official Resend library fails, requests are sent directly to the Resend HTTP API

## License

MIT
