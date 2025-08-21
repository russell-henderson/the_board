# main.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(
    title="the_board",
    description="Hierarchical multi-agent orchestration system",
    version="1.0.0"
)

@app.get("/", tags=["system"])
async def root():
    return {"status": "ok", "message": "the_board is running"}

@app.get("/health", tags=["system"])
async def health():
    return JSONResponse(content={"status": "healthy"}, status_code=200)

@app.get("/healthz", tags=["system"])
async def healthz():
    return JSONResponse(content={"status": "ok", "service": "the_board"}, status_code=200)

@app.get("/readyz", tags=["system"])
async def readyz():
    # Here you could later add DB checks, state layer checks, etc.
    return JSONResponse(content={"status": "ready"}, status_code=200)
