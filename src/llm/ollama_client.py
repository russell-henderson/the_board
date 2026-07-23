"""Small, optional client for a local Ollama server."""
from __future__ import annotations

import os
from typing import Optional

import requests


def generate_text(prompt: str) -> Optional[str]:
    """Generate text locally, returning ``None`` when Ollama is unavailable."""
    try:
        response = requests.post(
            f"{os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}/api/generate",
            json={"model": os.getenv("PRIMARY_LLM", "llama3.2"), "prompt": prompt, "stream": False},
            timeout=float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "60")),
        )
        response.raise_for_status()
        text = response.json().get("response", "").strip()
        return text or None
    except (requests.RequestException, ValueError):
        return None
