# PIEMR Auto-Uploader — Backend

## Quick Start

```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
cp .env.example .env

# 4. Generate and set FERNET_KEY in .env
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Paste the output as the value of FERNET_KEY in .env

# 5. Start the server
python main.py
```

Server runs at: http://localhost:8000  
API docs at:    http://localhost:8000/docs

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/run | Start a run (multipart: username, password, file) |
| GET  | /api/run/stream?run_id=N | SSE live log stream |
| GET  | /api/runs | Run history (last 20) |
| GET  | /api/runs/{id} | Single run with full log |
| GET  | /api/status/last | Most recent run summary |
| POST | /api/config | Save credentials + schedule |
| GET  | /api/config | Load saved config (no password) |
| GET  | /api/schedule | Schedule status + next run time |
| POST | /api/schedule/enable | Enable with body: {"time": "08:00"} |
| POST | /api/schedule/disable | Disable scheduler |

---

## Production (no display / server)

Set `HEADLESS=true` in `.env` and install Chrome:

```bash
# Ubuntu / Debian
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo apt-get install -y google-chrome-stable
```

Run with gunicorn (single worker required):

```bash
gunicorn main:app -k uvicorn.workers.UvicornWorker -w 1 --bind 0.0.0.0:8000
```

---

## Serving the Frontend

Build the React app (`npm run build` in `/frontend`), then copy the `dist/` folder
into `backend/static/`. FastAPI will serve it automatically at `/`.

---

## Notes

- **Single worker only** — APScheduler and the SSE queue are in-process. Multiple
  workers would spawn duplicate scheduled jobs.
- **SQLite** — fine for single-user use. `runs.db` is created automatically on first start.
- **Temp config files** — credentials are written to `/tmp/piemr_*.json` and deleted
  immediately after the subprocess exits (try/finally guaranteed).
