# the_board — Deployment & Service Guide (Windows + Poetry + NSSM)

> **Canonical entrypoint:** `src/main.py`
> **NSSM command:** `-m uvicorn src.main:app --host 0.0.0.0 --port 8080`  

---

## 1) Paths used in this document (update if your paths differ)

- **Repo root:** `C:\Users\forlu\Desktop\_the_board\the_board`
- **Entrypoint (root-level):** `C:\Users\forlu\Desktop\_the_board\the_board\src\main.py`
- **Poetry venv Python:** `C:\Users\forlu\Desktop\_the_board\the_board\.venv\Scripts\python.exe`
- **Service name:** `the_board`
- **Port:** `8080`
- **ENV file:** `C:\Users\forlu\Desktop\_the_board\the_board\.env`
- **SQLite DB (relative to repo root):** `.\state\the_board_state.db`

---

## 2) Prerequisites

- **Python**: 3.11 or 3.12 recommended
- **Poetry**: for dependency & venv management
- **Ollama**: installed and on PATH (for local models)
- **NSSM**: Non‑Sucking Service Manager on PATH
- **PowerShell**: run as Administrator for service/firewall steps

---

## 3) Project layout (expected)

```

the_board/
├── .env
├── .gitignore
├── README.md
├── dataModel.py
├── dev.sh
├── docs
│   ├── BRAND_GUIDELINES.md
│   ├── DEPLOYMENT.md
│   ├── PROJECT_OVERVIEW.md
│   ├── TECHSPEC.md
│   ├── WORKFLOWS.md
│   ├── brand_board.png
│   └── file_structure.txt
├── example.env
├── file_structure.txt
├── generate_file_structure.py
├── main.py
├── new
├── poetry.lock
├── pyproject.toml
├── scripts
│   ├── __init__.py
│   ├── dev.py
│   └── start.py
├── src
│   ├── __init__.py
│   ├── api
│   │   ├── __init__.py
│   │   └── state_routes.py
│   ├── main.py
│   └── state
│       ├── __init__.py
│       └── store.py
├── start.sh
└── state
    ├── the_board_state.db
    ├── the_board_state.db-shm
    └── the_board_state.db-wal
```

---

## 4) Environment file (`.env`)

Create `C:\Users\forlu\Desktop\_the_board\the_board\.env`:

```
# LLM server
OLLAMA_BASE_URL=http://localhost:11434

# Models
PRIMARY_LLM=llama3.2
EMBEDDING_MODEL=mxbai-embed-large

# ChromaDB persistence
CHROMA_PERSIST_DIRECTORY=./chroma_db

# SQLite state
STATE_DB_PATH=./state/the_board_state.db
```

> If you place `.env` elsewhere, update the NSSM environment in §8.

---

## 5) Install dependencies & pull models

```powershell
cd C:\Users\forlu\Desktop\_the_board\the_board
poetry install

# (optional) pull local models
ollama pull llama3.2
ollama pull mxbai-embed-large
```

---

## 6) FastAPI entrypoint (`src/main.py` )

Create or update **`C:\Users\forlu\Desktop\_the_board\the_board\src\main.py`** exactly as below.  
This defines `/`, `/health`, `/healthz`, and `/readyz` so ops and monitors can probe correctly.

```python
# src/main.py
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ---------- Minimal .env loader (avoid extra deps here) ----------
BASE_DIR = Path(__file__).resolve().parent
ENVFILE = os.environ.get("ENVFILE", str(BASE_DIR / ".env"))

def load_env_file(path: str) -> None:
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

load_env_file(ENVFILE)

# ---------- App ----------
app = FastAPI(title="the_board", version="1.0.0")

# ---------- SQLite state (WAL) ----------
STATE_DB_PATH = os.environ.get("STATE_DB_PATH", "./state/the_board_state.db")
STATE_DB = (BASE_DIR / STATE_DB_PATH).resolve()
STATE_DB.parent.mkdir(parents=True, exist_ok=True)

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(STATE_DB, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

# Idempotent init
with get_db() as _conn:
    _conn.execute("""
        CREATE TABLE IF NOT EXISTS service_state (
            k TEXT PRIMARY KEY,
            v TEXT
        )
    """)
    _conn.commit()

# ---------- Models ----------
class Health(BaseModel):
    status: str = "ok"
    message: str = "the_board is running"

class EchoIn(BaseModel):
    text: str

class EchoOut(BaseModel):
    text: str
    model: Optional[str] = os.environ.get("PRIMARY_LLM")

# ---------- Routes ----------
@app.get("/", response_model=Health, tags=["system"])
def root():
    return Health()

@app.get("/health", tags=["system"])
def health():
    return JSONResponse({"status": "healthy"})

@app.get("/healthz", tags=["system"])
def healthz():
    return JSONResponse({"status": "ok", "service": "the_board"})

@app.get("/readyz", tags=["system"])
def readyz():
    # Add deeper readiness checks here later (DB, model server, etc.)
    return JSONResponse({"status": "ready"})

@app.post("/echo", response_model=EchoOut, tags=["demo"])
def echo(body: EchoIn):
    return EchoOut(text=body.text)
```

---

## 7) Local dev

Open two terminals.

**Terminal A — Ollama**

```powershell
ollama serve
```

**Terminal B — API**

```powershell
cd C:\Users\forlu\Desktop\_the_board\the_board
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8080
```

Verify:

- `http://localhost:8080/` → `{ "status": "ok", "message": "the_board is running" }`
- `http://localhost:8080/docs` → Swagger UI
- `http://localhost:8080/health`, `/healthz`, `/readyz` → 200

---

## 8) Install as a Windows service (NSSM)

Run **PowerShell as Administrator**:

```powershell
$ServiceName = "the_board"
$AppDir      = "C:\Users\forlu\Desktop\_the_board\the_board"
$VenvPython  = "C:\Users\forlu\Desktop\_the_board\the_board\.venv\Scripts\python.exe"
$EnvFile     = "C:\Users\forlu\Desktop\_the_board\the_board\.env"
$Port        = "8080"

# Install with Poetry's Python and the root entrypoint
nssm install the_board C:\Users\forlu\Desktop\_the_board\the_board\.venv\Scripts\python.exe -m uvicorn src.main:app --host 0.0.0.0 --port 8080


# Working directory so relative paths/imports resolve
nssm set $ServiceName AppDirectory $AppDir

# Add ENVFILE to the service environment
nssm set $ServiceName AppEnvironmentExtra "ENVFILE=$EnvFile"

# Optional logging to files
New-Item -ItemType Directory -Force "$AppDir\logs" | Out-Null
nssm set $ServiceName AppStdout "$AppDir\logs\the_board.out.log"
nssm set $ServiceName AppStderr "$AppDir\logs\the_board.err.log"

# Auto-start on boot
nssm set $ServiceName Start SERVICE_AUTO_START

# Allow inbound traffic to port 8080
netsh advfirewall firewall add rule name="the_board 8080" dir=in action=allow protocol=TCP localport=$Port
```

Start or restart the service:

```powershell
nssm start the_board
# or
nssm restart the_board
```

---

## 9) Verify the service

```powershell
# Confirm the 3 key fields
nssm get the_board Application        # -> ...\.venv\Scripts\python.exe
nssm get the_board AppDirectory       # -> C:\Users\forlu\Desktop\_the_board\the_board
nssm get the_board AppParameters      # -> -m uvicorn main:app --host 0.0.0.0 --port 8080

# Health checks
curl http://localhost:8080/
curl http://localhost:8080/health
curl http://localhost:8080/healthz
curl http://localhost:8080/readyz

# Live logs (if configured)
Get-Content -Wait C:\Users\forlu\Desktop\_the_board\the_board\logs\the_board.err.log
Get-Content -Wait C:\Users\forlu\Desktop\_the_board\the_board\logs\the_board.out.log
```

---

## 10) SQLite state (WAL) & backups

SQLite is opened with WAL mode and `synchronous=NORMAL` (see code).  
Nightly backups are **safe while the service runs** — copy the `.db` and any `-wal`/`-shm` files found in `.\state\`.

Example (PowerShell):

```powershell
$src = "C:\Users\forlu\Desktop\_the_board\the_board\state"
$dst = "E:\backups\the_board\state\$(Get-Date -Format yyyyMMdd)"
New-Item -ItemType Directory -Force $dst | Out-Null
Copy-Item "$src\the_board_state.db*" $dst
```

---

## 11) Troubleshooting quick reference

**A. `/health` or `/healthz` return 404**  

**B. `SERVICE_PAUSED` or instant stop after start**  

- Another process is bound to 8080:

  ```powershell
  netstat -ano | findstr :8080
  tasklist /FI "PID eq <PID>"
  taskkill /PID <PID> /F
  ```

- Or startup error — check `logs\the_board.err.log`.

**C. Wrong interpreter**  

- Ensure `Application` is the Poetry venv Python (not Windows Store). See §9.

**D. ENV not loading**  

- Confirm the `.env` file exists and add:

  ```powershell
  nssm set the_board AppEnvironmentExtra "ENVFILE=C:\Users\forlu\Desktop\_the_board\the_board\.env"
  ```

**E. Import error: "Could not import module 'main'"**  

- Ensure `AppDirectory` is the repo root and `AppParameters` uses `main:app` (root), not `src.main:app` unless you migrate as in §14.

---

## 12) Local test matrix (smoke)

1. Dev mode on 8080 with reload  
   `poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8080`  
2. Service restart  
   `nssm restart the_board`  
3. Tail logs and hit `/readyz`  
   `Get-Content -Wait .\logs\the_board.out.log` and `curl :8080/readyz`

---

## 13) Uninstall / reset service

```powershell
# Stop & remove
nssm stop the_board
nssm remove the_board confirm

# (Optional) clean logs and firewall rule
Remove-Item -Force -Recurse .\logs
netsh advfirewall firewall delete rule name="the_board 8080"
```

---

## 14) Optional: moving entrypoint into `src/` later

If you prefer `src/main.py`:

1) Move the file to `C:\Users\forlu\Desktop\_the_board\the_board\src\main.py`  
2) Create `C:\Users\forlu\Desktop\_the_board\the_board\src\__init__.py` (empty file)  
3) Update the service parameters:

```powershell
nssm set the_board AppParameters "-m uvicorn src.main:app --host 0.0.0.0 --port 8080"
nssm restart the_board
```

**Important:** The rest of this guide assumes the `src\main.py`.

---

## 15) API quick reference

- `GET /` → `{"status":"ok","message":"the_board is running"}`  
- `GET /health` → `{"status":"healthy"}`  
- `GET /healthz` → `{"status":"ok","service":"the_board"}`  
- `GET /readyz` → `{"status":"ready"}`  
- `POST /echo` `{ "text": "hello" }` → `{ "text":"hello","model":"<PRIMARY_LLM>" }`

---

**End of DEPLOYMENT.md**
