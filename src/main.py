# src/main.py
from fastapi import FastAPI

app = FastAPI(title="the_board")

@app.get("/")
async def root():
    return {"status": "ok", "message": "the_board is running"}
