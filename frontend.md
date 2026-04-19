# PIEMR Auto-Uploader — Frontend Specification

## Overview

A minimal two-page web UI that lets a student configure and monitor the PIEMR assignment
automation script without ever touching the command line. Built with **React + Tailwind CSS**,
communicates with the FastAPI backend over a REST API.

---

## Page 1 — Configuration (`/` or `/setup`)

### Purpose
Collect the three inputs the script needs, let the user pick a schedule, and trigger
an immediate run or save the configuration for the scheduler.

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│  🎓  PIEMR Assignment Auto-Uploader                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Portal Credentials                                        │
│   ┌──────────────────────────────┐                         │
│   │ Enrollment Number            │  ← text input           │
│   └──────────────────────────────┘                         │
│   ┌──────────────────────────────┐                         │
│   │ Password            👁        │  ← password input       │
│   └──────────────────────────────┘                         │
│                                                             │
│   Assignment File                                           │
│   ┌──────────────────────────────────────────────────────┐ │
│   │  📄  Drop PDF / file here, or  [ Browse ]            │ │
│   │      Selected: AllinOneC.pdf  (1.2 MB)               │ │
│   └──────────────────────────────────────────────────────┘ │
│                                                             │
│   Schedule (optional)                                       │
│   ┌──────────────────────────────┐                         │
│   │  Run daily at  [  08:00  ]   │  ← time picker          │
│   └──────────────────────────────┘                         │
│   ☑  Enable daily auto-run                                  │
│                                                             │
│   [ ▶ Run Now ]          [ 💾 Save & Schedule ]             │
│                                                             │
│   ⚠  Credentials are stored encrypted on the server.       │
└─────────────────────────────────────────────────────────────┘
```

### Field Details

| Field | Type | Validation | Notes |
|---|---|---|---|
| Enrollment Number | `<input type="text">` | Required, non-empty | Maps to `CONFIG["username"]` |
| Password | `<input type="password">` | Required, non-empty | Toggle visibility icon |
| Assignment File | File drag-drop zone | Required, any file type | Sent as multipart upload |
| Daily Run Time | `<input type="time">` | HH:MM, 24-hr | Defaults to `08:00` |
| Enable Daily Auto-run | Checkbox | — | Toggles the scheduler ON/OFF |

### Buttons

**Run Now**
- POSTs credentials + file to `POST /api/run` immediately.
- Disables button and shows a spinner while running.
- On completion, automatically switches to the Status page.

**Save & Schedule**
- POSTs config to `POST /api/config` (saves credentials + file + schedule time).
- If "Enable daily auto-run" is checked, also calls `POST /api/schedule/enable`.
- Shows a toast: *"Configuration saved. Next run at 08:00 tomorrow."*

### Inline Feedback
- After "Run Now" is clicked, a collapsible live-log panel slides open below the buttons.
- Each log line streamed from `GET /api/run/stream` (SSE) is appended in real time.
- Colors: green for `✓`, red for `✗`, yellow for `⚠`.

---

## Page 2 — Status Dashboard (`/status`)

### Purpose
Show the outcome of the most recent run, the next scheduled run time, and a full
run history table.

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│  🎓  PIEMR Auto-Uploader  ·  Status                         │
├──────────────────────┬──────────────────────────────────────┤
│  Last Run            │  Next Scheduled Run                   │
│  ✅  SUCCESS         │  Tomorrow  08:00                      │
│  18 Apr 2026 07:55   │  Scheduler: ACTIVE 🟢                 │
│  4 file(s) uploaded  │  [ Disable ]                          │
├──────────────────────┴──────────────────────────────────────┤
│  Run History                                                │
│  ┌────────────┬────────────┬────────┬───────────────────┐  │
│  │  Date/Time │  Triggered │ Result │ Uploads / Subject  │  │
│  ├────────────┼────────────┼────────┼───────────────────┤  │
│  │ 18 Apr 07  │ Scheduler  │ ✅ OK  │ 4 total            │  │
│  │ 17 Apr 07  │ Manual     │ ✅ OK  │ 2 total            │  │
│  │ 16 Apr 07  │ Scheduler  │ ❌ ERR │ Login failed       │  │
│  └────────────┴────────────┴────────┴───────────────────┘  │
│                                                             │
│  [ View Full Log — 18 Apr ]  [ ⚙ Edit Config ]             │
└─────────────────────────────────────────────────────────────┘
```

### Stat Cards (top row)

| Card | Data Source |
|---|---|
| Last Run status + timestamp | `GET /api/status/last` |
| Uploads count | Parsed from last run log |
| Next Scheduled Run | `GET /api/schedule` |
| Scheduler Active toggle | `POST /api/schedule/enable` or `/disable` |

### History Table

- Pulled from `GET /api/runs?limit=20`.
- Clicking a row expands a collapsible raw-log viewer (monospace font, dark bg).
- Rows are color-coded: green row = success, red row = error.

### Buttons

**View Full Log** — Opens a modal with the complete timestamped log for that run.  
**Edit Config** — Navigates back to Page 1, pre-filled with saved values (password field blank for security).  
**Disable / Enable Scheduler** — Inline toggle, calls schedule API, updates the card in place.

---

## Shared Components

### Navbar / Header
- App name + PIEMR logo placeholder on the left.
- Two nav links: **Setup** | **Status**.
- A small colored dot indicating scheduler state (🟢 active / 🔴 disabled / ⚪ not configured).

### Toast Notifications
- Success: green, bottom-right, auto-dismiss 4 s.
- Error: red, stays until dismissed.
- Info: blue, auto-dismiss 3 s.

### Loading Spinner
- Shown while any API call is in-flight.
- Overlay on the button that triggered the action (not full-page).

---

## API Calls the Frontend Makes

| Action | Method | Endpoint | Payload |
|---|---|---|---|
| Submit run | POST | `/api/run` | `multipart/form-data`: username, password, file |
| Save config | POST | `/api/config` | JSON: username, password, schedule_time, enabled |
| Get last status | GET | `/api/status/last` | — |
| Get run history | GET | `/api/runs` | `?limit=20` |
| Stream live logs | GET | `/api/run/stream` | SSE (EventSource) |
| Get schedule info | GET | `/api/schedule` | — |
| Enable scheduler | POST | `/api/schedule/enable` | JSON: time (HH:MM) |
| Disable scheduler | POST | `/api/schedule/disable` | — |

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Framework | React 18 (Vite) | Simple SPA, fast dev server |
| Styling | Tailwind CSS | Utility-first, minimal setup |
| HTTP client | `axios` | Cleaner than fetch for multipart |
| SSE streaming | Native `EventSource` | Built-in browser API, no lib needed |
| Routing | `react-router-dom` v6 | Two pages only |
| State | `useState` + `useEffect` | No Redux needed for this scope |

---

## File Structure

```
frontend/
├── index.html
├── vite.config.js
├── tailwind.config.js
├── src/
│   ├── main.jsx
│   ├── App.jsx              # Router setup
│   ├── api.js               # All axios calls in one place
│   ├── pages/
│   │   ├── Setup.jsx        # Page 1
│   │   └── Status.jsx       # Page 2
│   └── components/
│       ├── Navbar.jsx
│       ├── Toast.jsx
│       ├── LiveLog.jsx      # SSE log stream panel
│       ├── RunHistory.jsx   # History table + expand
│       └── FileDropZone.jsx # Drag-and-drop file picker
```

---

## Environment Variable

```
VITE_API_BASE_URL=http://localhost:8000
```

Set to the FastAPI server URL. In production, proxy through Nginx so both frontend
and backend share the same origin (no CORS issues).
