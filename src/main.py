# src/main.py
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Optional
from fastapi import HTTPException
from fastapi import FastAPI
from pydantic import BaseModel
from src.api.state_routes import router as state_router

# Load .env (minimal loader to avoid extra deps)
BASE_DIR = Path(__file__).resolve().parents[1]
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

# Define models BEFORE using them
class Health(BaseModel):
    status: str = "ok"
    message: str = "the_board is running"

class EchoIn(BaseModel):
    text: str

class EchoOut(BaseModel):
    text: str
    model: Optional[str] = os.environ.get("PRIMARY_LLM")

app = FastAPI(title="the_board API", version="0.1.0")
app.include_router(state_router)

# SQLite state with WAL
STATE_DB_PATH = os.environ.get("STATE_DB_PATH", "./state/the_board_state.db")
STATE_DB = (BASE_DIR / STATE_DB_PATH).resolve()
STATE_DB.parent.mkdir(parents=True, exist_ok=True)

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(STATE_DB, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

with get_db() as _conn:
    _conn.execute("""
        CREATE TABLE IF NOT EXISTS service_state (
            k TEXT PRIMARY KEY,
            v TEXT
        )
    """)
    _conn.commit()

# Now define endpoints
@app.get("/", response_model=Health, tags=["root"])
def root():
    return Health()

@app.get("/health", response_model=Health, tags=["health"])
def health():
    return Health()

@app.get("/healthz", response_model=Health, tags=["health"])
def healthz():
    return Health()

@app.get("/readyz", response_model=Health, tags=["health"])
def readyz():
    try:
        # minimal dependency check: DB reachable and writable
        with get_db() as conn:
            conn.execute("PRAGMA wal_checkpoint(PASSIVE);")
        return Health(status="ready", message="dependencies ok")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"not_ready: {e}")

@app.post("/echo", response_model=EchoOut, tags=["demo"])
def echo(body: EchoIn):
    return EchoOut(text=body.text)