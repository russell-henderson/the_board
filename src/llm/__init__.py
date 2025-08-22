"""
LLM integration package for the_board.

This package provides centralized access to language models for agent execution.
"""

from .ollama_client import generate_text, OLLAMA_BASE_URL, PRIMARY_LLM

__all__ = ["generate_text", "OLLAMA_BASE_URL", "PRIMARY_LLM"]
