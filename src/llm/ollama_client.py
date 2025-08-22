# in src/llm/ollama_client.py
import requests
import os

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
PRIMARY_LLM = os.environ.get("PRIMARY_LLM", "llama3.2")

def generate_text(prompt: str, model: str = PRIMARY_LLM) -> str:
    """
    Generates text using the Ollama API.
    """
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=60 # Add a timeout
        )
        response.raise_for_status()
        return response.json()["response"]
    except requests.RequestException as e:
        # Handle errors (e.g., Ollama not running)
        print(f"Error calling Ollama: {e}")
        return f"Error: Could not get a response from the model. Details: {e}"
