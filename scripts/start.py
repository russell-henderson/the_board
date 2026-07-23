"""Production-style local API launcher."""
import uvicorn


def main() -> None:
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000)
