# Backend (FastAPI)

## Setup

```bash
# From backend folder
py -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set `DATABASE_PASSWORD`, `GOOGLE_CLIENT_ID`, `JWT_SECRET`. See `db/README_SETUP.md` for PostgreSQL setup.

## Run

```bash
cd backend
py run.py
```

Server runs at **http://127.0.0.1:5000**. API docs: **http://127.0.0.1:5000/docs**

## Structure

- `app/` – FastAPI app (`main.py`), config, validation
- `db/` – PostgreSQL helpers, migrations (`workflow.sql`), auth (`googleAuth.py`)
- `run.py` – Entry point (uvicorn)

## Test event (PowerShell)

```powershell
$ts = [int](Get-Date -UFormat %s)
$body = @{ device_id = "esp32_001"; event_type = "door_open"; count = 1; timestamp = $ts } | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:5000/api/events -Method POST -ContentType "application/json" -Body $body
```
