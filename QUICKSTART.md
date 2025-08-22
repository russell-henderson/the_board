# 🚀 Quick Development Setup

## Prerequisites

- Python 3.11 or 3.12
- Git

## Getting Started

1. **Clone and navigate to the repository:**

   ```bash
   git clone https://github.com/russell-henderson/the_board.git
   cd the_board
   ```

2. **Create and activate a virtual environment:**

   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**

   ```bash
   # For full installation (requires internet):
   pip install -e .
   
   # For minimal setup (core functionality only):
   pip install fastapi uvicorn pydantic sqlalchemy python-dotenv
   ```

4. **Run basic functionality tests:**

   ```bash
   python test_core_functionality.py
   ```

5. **Start the development server:**

   ```bash
   # Method 1: Using the built-in start script
   python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   
   # Method 2: Using the project script (if dependencies are installed)
   python -m scripts.dev
   ```

6. **Test the API:**

   ```bash
   # Check health
   curl http://localhost:8000/health
   
   # View API documentation
   # Open http://localhost:8000/docs in your browser
   ```

## Basic Usage

### Create a Strategic Plan

```bash
curl -X POST "http://localhost:8000/plan" \
  -H "Content-Type: application/json" \
  -d '{"goal": "Expand into European markets", "priority": "high"}'
```

### Check Plan Status

```bash
curl "http://localhost:8000/state/plans/{plan_id}"
```

## What's Working

✅ **Core System Components:**
- Multi-agent architecture with CFO, CTO, CMO, COO agents
- SQLite-based state management
- FastAPI REST API with health checks
- Task orchestration system
- Basic test suite

✅ **Fixed Issues:**
- Import errors resolved
- Python version constraints updated
- Basic models working without external dependencies
- Code quality configuration added

## Next Steps for Development

1. **Install LLM Dependencies:** Add Ollama or OpenAI integration
2. **Enhance Agent Logic:** Replace stub implementations with actual AI
3. **Add Authentication:** Implement API security
4. **Expand Testing:** Add comprehensive test coverage
5. **Performance:** Add caching and parallel execution

## Common Issues

**Import Errors:** Make sure you're in the project root and have activated your virtual environment.

**Port Already in Use:** Change the port number in the uvicorn command (e.g., `--port 8001`).

**Database Issues:** Delete `state/the_board_state.db` to reset the database.

For more detailed information, see the full [README.md](README.md) and [documentation](docs/).