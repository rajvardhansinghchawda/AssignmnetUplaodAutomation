# PIEMR Assignment Auto-Uploader — Project Description

## What This Project Is

A lightweight full-stack web application that wraps the existing PIEMR portal
Selenium automation script in a friendly browser UI. Instead of editing a Python
file to update credentials and manually running a script from the command line,
a student opens a simple webpage, fills in three fields, and clicks a button.

The system also includes a built-in daily scheduler so the uploads happen
automatically every morning at a chosen time — no manual action required.

---

## The Problem It Solves

The PIEMR academic portal (accsoft.piemr.edu.in) requires students to manually
log in, navigate to each subject, and upload assignment files one by one. If a
student has multiple subjects with pending assignments, this process is repetitive
and time-consuming.

The automation script already solves the mechanical repetition. This project solves
the usability gap around the script: no command-line knowledge needed, credentials
are stored safely, and runs can be scheduled without any cron/task-scheduler setup.

---

## How It Works (End-to-End)

```
Student opens the web app in a browser
    └─▶  Fills in: enrollment number, password, assignment PDF
    └─▶  Chooses: "Run Now" OR "Save & run daily at 08:00"

FastAPI backend receives the request
    └─▶  Saves the file to the uploads folder
    └─▶  Encrypts and stores the password in SQLite
    └─▶  Spawns the Selenium script as a child process
         (Chrome opens in background, logs in, scans subjects, uploads)
    └─▶  Streams live log output back to the browser via SSE

Browser shows live progress
    └─▶  "✓ Logged in"
    └─▶  "📌 Mathematics → 2 new assignments"
    └─▶  "✓ Uploaded (1/2)"
    └─▶  "COMPLETE — 4 total uploads"

If scheduled:
    └─▶  Every morning at the chosen time, the backend automatically
         re-runs the script using the saved credentials and file
    └─▶  Result is saved to run history, visible in the Status page
```

---

## Feature List

### Core
- **Credential input form** — enrollment number, password (masked), file picker
- **One-click upload** — triggers the full automation immediately
- **Live log viewer** — streams script output line by line as it runs
- **Status page** — shows last run result, timestamp, upload count

### Scheduling
- **Daily auto-run** — enable a fixed daily time (e.g. 08:00) for automatic uploads
- **Scheduler toggle** — enable or disable without losing the saved schedule time
- **Next run display** — shows when the next automatic run will fire
- **Timezone-aware** — uses `Asia/Kolkata` by default; configurable in `.env`

### History
- **Run history table** — date, triggered by (manual / scheduler), result, upload count
- **Full log viewer** — expand any past run to see its complete output
- **Error surfacing** — failed runs are clearly marked with the error message

### Security
- **Encrypted password storage** — Fernet symmetric encryption; key lives in `.env`
- **Temp config files** — credentials never appear on the command line or in logs
- **Upload size limit** — configurable max file size (default 50 MB)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite + Tailwind CSS |
| Backend API | FastAPI (Python 3.11+) |
| Database | SQLite via `aiosqlite` |
| Scheduler | APScheduler 3.x (AsyncIOScheduler) |
| Automation | Selenium 4 + webdriver-manager |
| Encryption | `cryptography` (Fernet) |
| Streaming | Server-Sent Events (SSE) |

---

## Project Scope & Limitations

**In scope:**
- Single-user application (one set of credentials, one file at a time)
- Windows and Linux compatible (ChromeDriver auto-managed)
- Local network deployment (student's own machine or a small home server)

**Out of scope (for this version):**
- Multi-user / multi-account management
- Subject-specific file selection (same file uploaded to all pending assignments)
- Email/SMS notifications on completion
- Docker containerization (can be added later)
- HTTPS / SSL termination (use Nginx reverse proxy for production)

---

## Directory Structure (Full Project)

```
piemr-auto-uploader/
├── backend/
│   ├── main.py
│   ├── db.py
│   ├── crypto.py
│   ├── config.py                  ← pydantic-settings, reads .env
│   ├── routers/
│   │   ├── run.py
│   │   ├── config.py
│   │   └── schedule.py
│   ├── services/
│   │   ├── runner.py
│   │   └── scheduler.py
│   ├── piemr_assignment_upload.py ← original script, patched for --config flag
│   ├── uploads/                   ← gitignored
│   ├── runs.db                    ← gitignored
│   ├── .env                       ← gitignored
│   └── requirements.txt
│
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── api.js
│   │   ├── pages/
│   │   │   ├── Setup.jsx
│   │   │   └── Status.jsx
│   │   └── components/
│   │       ├── Navbar.jsx
│   │       ├── Toast.jsx
│   │       ├── LiveLog.jsx
│   │       ├── RunHistory.jsx
│   │       └── FileDropZone.jsx
│   └── package.json
│
├── docs/
│   ├── description.md             ← this file
│   ├── frontend.md
│   ├── agenthandoverreport.md
│   └── credentials.md
│
└── README.md
```

---

## Quick Start (Development)

```bash
# 1. Backend
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # fill in FERNET_KEY at minimum
uvicorn main:app --reload --port 8000

# 2. Frontend (separate terminal)
cd frontend
npm install
npm run dev                      # runs on http://localhost:5173
```

Open `http://localhost:5173`, enter your portal credentials, upload your
assignment file, and click **Run Now**.

---

## Deployment (Single Machine, No Display)

```bash
# Install Chrome headless on Ubuntu
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo apt-get install -y google-chrome-stable

# Set in .env
HEADLESS=true

# Build frontend and serve via FastAPI static files
cd frontend && npm run build
# Copy dist/ into backend/static/
# FastAPI serves index.html at GET /

# Run backend with gunicorn (single worker — see handover report)
gunicorn main:app -k uvicorn.workers.UvicornWorker -w 1 --bind 0.0.0.0:8000
```

---

## Document Index

| File | Purpose |
|---|---|
| `description.md` | This file — overall project overview |
| `frontend.md` | Page-by-page UI spec, component list, API calls |
| `agenthandoverreport.md` | Backend architecture, module breakdown, all endpoints |
| `credentials.md` | `.env` variables, security notes, first-time checklist |
