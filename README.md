# 🎯 Job Scout

AI-powered internship tracker that scores jobs against your resume automatically.

<!-- Badges -->
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi) ![Python](https://img.shields.io/badge/Python-3776AB?logo=python) ![React](https://img.shields.io/badge/React-20232A?logo=react) ![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?logo=postgresql) ![Railway](https://img.shields.io/badge/Railway-000000) ![Vercel](https://img.shields.io/badge/Vercel-000000)

Live demo: https://job-scout-black.vercel.app

## Short description
Job Scout is a full-stack internship portfolio project that automatically scrapes internship listings from Internshala, scores them against a user’s resume using an LLM, and delivers a personalized daily digest email. It targets students and early-career developers who want a data-driven way to discover internships that match their skills and experience.

## Features
- 🔍 Automated scraping from Internshala (Selenium + Requests)
- 🤖 LLM-based resume scoring via Groq API — each job gets a score out of 10
- 📊 Skills match %, missing skills analysis, and seniority-fit detection
- 📧 Daily digest email with top-matched internship listings
- ⚙️ Background pipeline runs automatically at 9 AM IST via APScheduler
- 🔐 JWT-based authentication with per-user resume upload (multi-user support)
- 🎨 Polished dark UI with 3D animated background and smooth transitions (Framer Motion + React Three Fiber)

## Architecture
The pipeline is designed for reliability and extensibility: scraping → scoring → storage → delivery.

```
Scrape (Selenium + Requests)
    ↓
Deduplicate & Normalize
    ↓
LLM Score (Groq) ↔ Resume Text Extract (PyMuPDF)
    ↓
Store results in PostgreSQL
    ↓
Serve via FastAPI (REST) → Frontend (React + Vite)
    ↓
Daily digest email scheduler (APScheduler) delivers top matches
```

## API Endpoints

| Method | Endpoint | Description | Auth |
|---|---:|---|---:|
| POST | `/auth/register` | Register a new user | No |
| POST | `/auth/login` | Obtain JWT token | No |
| GET | `/auth/me` | Fetch current user profile | Yes |
| POST | `/auth/upload-resume` | Upload PDF resume (extract text) | Yes |
| GET | `/jobs?pages=N` | Trigger/preview job scrape pages | Yes |
| POST | `/send-digest` | Send a digest email to a user | Yes |
| POST | `/run-pipeline` | Run full scrape → score pipeline (admin) | Yes |
| GET | `/pipeline/status` | Check last run status | Yes |

## Local development

### Backend
```bash
git clone <repo-url>
cd backend
python -m venv venv
# macOS / Linux
source venv/bin/activate
# Windows
# venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # fill in values
uvicorn main:app --reload
```

Required `.env` variables:
- `DATABASE_URL`
- `GROQ_API_KEY`
- `JWT_SECRET`
- `EMAIL_USER`
- `EMAIL_PASS`
- `FRONTEND_URL`

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Deployment
- Backend: deployed on Railway (live)
- Frontend: deployed on Vercel (live)
- CORS configured to allow the frontend origin to access API endpoints

## Project structure

Backend (high level):
```
backend/
├─ main.py
├─ scraper.py
├─ scorer.py
├─ scheduler.py
├─ models.py
├─ auth.py
├─ database.py
└─ requirements.txt
```

Frontend (high level):
```
frontend/
├─ src/
│  ├─ components/
│  ├─ pages/
│  ├─ store/
│  ├─ hooks/
│  └─ lib/api.ts
├─ vite.config.ts
└─ package.json
```

## What I learned
- I built a production-grade async API with FastAPI and background scheduling.
- I integrated LLMs into a data pipeline to score and rank job listings.
- I designed a multi-user system with JWT authentication and secure resume uploads.
- I handled web scraping at scale with Selenium, including anti-bot considerations and deduplication.
- I deployed a full-stack application using Railway (backend) and Vercel (frontend), and configured CORS and environment variables securely.
- I implemented modern frontend state management with Zustand and React Query, and improved UX using Framer Motion and React Three Fiber.

## Built by
Satvik Kashibhatla — 3rd year BTech CSE

⭐ Star this repo if you found it useful
# Job Scout

**Intelligent, multi-user job discovery platform with LLM-powered ranking and automated email digests.**

---

## How It Works

Job Scout is a full-stack job aggregation and ranking system that helps candidates find the most relevant job postings tailored to their profile.

**End-to-End Flow:**

1. **User Registration & Authentication** — Create account, register with email/password. JWT tokens (24-hour expiry) secure all subsequent requests.
2. **Resume Upload** — Upload PDF resume. Text is extracted, validated (≥50 chars), and stored per user for personalized scoring.
3. **Job Scraping** — Scrape Internshala job board (up to 250 jobs across 5 pages). Deduplication by URL hash + user ID ensures each user sees fresh listings.
4. **LLM Scoring** — Send job description + user's resume to Groq (llama-3.1-8b-instant). Returns JSON: score/10, skill match %, missing skills, seniority fit.
5. **Hybrid Ranking** — Combine LLM score (60%) + freshness bonus (40%). Fresher postings weighted higher. Final score: 0–10.
6. **Email Digest** — Fetch top 10 ranked jobs, format digest, send via Resend API. Mark jobs as seen to avoid duplicates.

**Scheduling:**
- **Automatic**: Daily at 9 AM IST (APScheduler). Runs pipeline for all active users with uploaded resumes.
- **Manual**: `POST /run-pipeline` — Authenticated users can trigger on-demand.

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | FastAPI | Async REST API, automatic OpenAPI docs |
| **Database** | SQLite + SQLAlchemy ORM | Persistent job/user storage, multi-tenant isolation |
| **Authentication** | JWT (python-jose) + bcrypt | Stateless auth, password hashing |
| **Scraping** | BeautifulSoup4 | HTML parsing, job listing extraction |
| **LLM** | Groq API (llama-3.1-8b) | Job scoring, skill analysis |
| **Job Ranking** | Custom hybrid algorithm | 60% LLM + 40% freshness weighting |
| **Email** | Resend API | Digest delivery |
| **Scheduling** | APScheduler | Daily 9 AM IST pipeline execution |
| **Rate Limiting** | slowapi | Login protection: 5 attempts/minute |
| **PDF Parsing** | PyPDF2 | Resume text extraction |
| **Validation** | Pydantic | Schema validation, automatic error handling |
| **Env Config** | python-dotenv | API key & secret management |

---

## Project Structure

```
job-scout/
├── backend/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app, endpoints, scheduler
│   ├── models.py               # SQLAlchemy ORM: Job, User models + queries
│   ├── database.py             # SQLite config, session management, init_db()
│   ├── auth.py                 # JWT, password hashing, auth schemas
│   ├── scorer.py               # Groq LLM integration, scoring algorithm
│   ├── scraper.py              # Internshala scraping, pagination
│   ├── digest.py               # Email formatting, Resend API client
│   ├── jobs.db                 # SQLite database (auto-created)
│   └── .env                    # API keys (not committed)
├── requirements.txt            # Python dependencies
├── .gitignore
├── README.md                   # This file
└── .venv/                      # Virtual environment
```

### Key Files

- **main.py** — 7 endpoints (auth, jobs, pipeline). Scheduler initialization. Per-user data isolation.
- **models.py** — Job & User ORM models. Multi-tenant queries (filter by user_id). Deduplication by (url_hash, user_id).
- **scorer.py** — Groq API integration. JSON parsing with markdown fallback. Score validation (0–10 clamp).
- **auth.py** — JWT token lifecycle, bcrypt hashing, Pydantic schemas (never expose hashed_password).
- **scraper.py** — BeautifulSoup4 parsing. Extracts title, company, URL, skills, description.
- **digest.py** — Email HTML formatting. Resend API + fallback error handling.

---

## Setup Instructions

### Prerequisites

- **Python 3.14+** (or 3.10+)
- **Groq API Key** — [Get one free](https://console.groq.com) (includes monthly free tier)
- **Resend API Key** — [Sign up free](https://resend.com)
- **Email Address** — For digest recipient (can be any valid email)

### Installation

#### 1. Clone & Navigate

```bash
git clone https://github.com/yourusername/job-scout.git
cd job-scout
```

#### 2. Create & Activate Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Configure Environment Variables

Create `backend/.env`:

```env
# Required API Keys
GROQ_API_KEY=gsk_your_groq_api_key_here
RESEND_API_KEY=re_your_resend_api_key_here

# Email Configuration
SENDER_EMAIL=onboarding@resend.dev          # Resend sandbox email
DIGEST_EMAIL=your.email@example.com         # Where digests are sent

# Security (required, generate with: python -c "import secrets; print(secrets.token_hex(32))")
SECRET_KEY=your_64_char_hex_key_here

# Optional
DEBUG_LIMIT=0                               # Set >0 to score only first N jobs (for testing)
```

#### 5. Initialize Database

```bash
python -m backend.database
# Or let it auto-initialize on first server start
```

#### 6. Start Development Server

```bash
uvicorn backend.main:app --reload
```

Server starts at `http://localhost:8000`  
API docs: `http://localhost:8000/docs`

---

## API Endpoints

| Method | Endpoint | Auth Required | Description |
|--------|----------|---|---|
| POST | `/auth/register` | ❌ | Register new user (email + password) |
| POST | `/auth/login` | ❌ | Get JWT token (rate limited: 5/minute) |
| GET | `/auth/me` | ✅ | Get current user info |
| POST | `/auth/upload-resume` | ✅ | Upload PDF resume, extract text |
| GET | `/jobs?pages=N` | ✅ | Scrape + score + return ranked jobs (top 10) |
| POST | `/send-digest` | ✅ | Scrape + score + email top jobs |
| POST | `/run-pipeline` | ✅ | Trigger full pipeline in background thread |

### Example Usage

**Register:**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com", "password":"SecurePass123"}'
```

**Login:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com", "password":"SecurePass123"}'
# Response: {"access_token":"eyJ0eXAi...", "token_type":"bearer"}
```

**Upload Resume:**
```bash
curl -X POST http://localhost:8000/auth/upload-resume \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/resume.pdf"
```

**Get Ranked Jobs:**
```bash
curl -X GET "http://localhost:8000/jobs?pages=2" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|---|
| `GROQ_API_KEY` | ✅ Yes | API key from [console.groq.com](https://console.groq.com) |
| `RESEND_API_KEY` | ✅ Yes | API key from [resend.com](https://resend.com) |
| `SENDER_EMAIL` | ✅ Yes | Resend sandbox email (usually `onboarding@resend.dev`) |
| `DIGEST_EMAIL` | ✅ Yes | Email address for job digest delivery |
| `SECRET_KEY` | ✅ Yes | 64-char hex string for JWT signing. Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DEBUG_LIMIT` | ❌ No | (Dev only) Score only first N jobs. Default: 0 (no limit) |

---

## Architecture Highlights

### Multi-Tenant Isolation

- Every job is tied to a `user_id` foreign key.
- All queries filtered by authenticated user: `Job.user_id == current_user.id`
- Same URL can exist for multiple users (no global unique constraints).
- Deduplication happens at app level: check `(url_hash, user_id)` combo.

### Authentication & Security

- **JWT Tokens** — 24-hour expiry, HS256 algorithm
- **Password Hashing** — bcrypt (160+ rounds default)
- **Rate Limiting** — Login endpoint: 5 attempts/minute by IP
- **Never Expose** — Hashed passwords excluded from API responses

### Scoring Algorithm

```
LLM Score       → 0–10 (from Groq)
Freshness Bonus → 0–1.0 (decays over 3+ days)

Final Score = (LLM Score × 0.6) + (Freshness Bonus × 10 × 0.4)
Result Range: 0–10
```

### Scheduled Pipeline

- **Trigger:** Daily at 9:00 AM Asia/Kolkata
- **Scope:** All users where `is_active=True` AND `resume_text IS NOT NULL`
- **Isolation:** Each user runs independently. If one fails, others unaffected.
- **Send:** Email digest to user's registered email address

---

## What's Next

### Phase 6: Database & Deployment (In Progress)
- Migrate from SQLite → PostgreSQL for production
- Deploy to Railway.app (CI/CD pipeline)
- Add database backups & monitoring

### Frontend Deployment
- Deploy the frontend from `frontend/` to Vercel
- Set `VITE_API_BASE` on Vercel to your Railway API URL
- Add your Vercel production URL to `FRONTEND_URL` on Railway for CORS
- Keep the Vercel rewrite config so client-side routes like `/dashboard` work on refresh

---

## Vercel + Railway Setup

1. In Vercel, import the `frontend/` folder as the project root.
2. Set the build command to `npm run build` and the output directory to `dist/client`.
3. Add an environment variable:
  - `VITE_API_BASE=https://web-production-5b114.up.railway.app`
4. In Railway, set `FRONTEND_URL` to your Vercel production domain, for example:
  - `https://job-scout.vercel.app`
5. Redeploy Railway after changing `FRONTEND_URL`.
6. Use `frontend/vercel.json` so direct links like `/login` and `/dashboard` resolve correctly.

## Troubleshooting

**"IntegrityError: UNIQUE constraint failed"**
- The old `jobs.db` has outdated schema. Delete and restart:
  ```bash
  rm backend/jobs.db          # Linux/Mac
  del backend\jobs.db         # Windows
  ```
  Server will auto-recreate with correct schema on next startup.

**"GROQ_API_KEY not loaded"**
- Missing from `backend/.env` or `.env` not in correct location.
- Verify: `cat backend/.env | grep GROQ_API_KEY`

**"No resume uploaded" error on GET /jobs**
- Upload a PDF first: `POST /auth/upload-resume`

**Scoring takes too long**
- Set `DEBUG_LIMIT=5` in `.env` to test with first 5 jobs only.

---

## Contributing

Pull requests welcome. For major changes, open an issue first.

---

## License

MIT

---

## Contact

Built as a demonstration of full-stack Python development with async APIs, multi-tenant database design, and LLM integration.

Questions? Open an issue or reach out.
