# the_board - GitHub Copilot Instructions

Always follow these instructions first and only search for additional context if the information provided here is incomplete or found to be in error.

## Working Effectively

### Prerequisites & Installation
- Install Python 3.11 (REQUIRED): `wget https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz` or use your system package manager
- Install Poetry: `pip install poetry`
- Install Ollama: Download from https://ollama.ai/ and follow installation instructions
- NEVER use Python 3.12+ - the project strictly requires `>=3.11,<3.12`

### Bootstrap the Repository
Run these commands in order. NEVER CANCEL any operation - some take several minutes.

```bash
# 1. Install dependencies (takes ~30-60 seconds)
poetry install --extras dev

# 2. Set up environment
cp example.env .env
# Edit .env if needed - default values work for local development

# 3. Start Ollama service (required for full functionality)
ollama serve &

# 4. Download required models (takes 5-15 minutes depending on connection)
# NEVER CANCEL: Model downloads are large (several GB)
ollama pull llama3.2
ollama pull mxbai-embed-large
```

### Development Commands

```bash
# Start development server with auto-reload
poetry run dev
# NOTE: This calls dev.sh which handles Ollama checks and environment setup

# Start production server
poetry run start

# Direct launch (canonical entry point) - useful for debugging
poetry run uvicorn src.main:app --reload --host 127.0.0.1 --port 8000

# Run tests (currently minimal test suite)
poetry run pytest

# Code formatting and linting
poetry run black src/
poetry run isort src/
poetry run mypy src/ --ignore-missing-imports
```

### Timing Expectations (NEVER CANCEL)
- `poetry install`: 30-60 seconds
- `ollama pull llama3.2`: 5-15 minutes (several GB download)
- `ollama pull mxbai-embed-large`: 2-5 minutes
- Application startup: <5 seconds
- Test suite: <5 seconds (minimal tests exist)
- Code formatting: <5 seconds
- Type checking: 10-20 seconds

## Application Structure

### Key Files and Entry Points
- **`src/main.py`** - 🎯 CANONICAL ENTRY POINT - Main FastAPI application
- **`dev.sh`** - Development startup script (called by `poetry run dev`)
- **`start.sh`** - Production startup script (called by `poetry run start`)
- **`pyproject.toml`** - Project configuration and dependencies
- **`.env`** - Environment configuration (copy from `example.env`)

### Critical Dependencies
- **Ollama**: Local LLM service (must be running for full functionality)
- **SQLite**: State persistence (automatically created in `./state/`)
- **ChromaDB**: Vector database for knowledge storage (in `./chroma_db/`)

## Validation Scenarios

### Always Test After Making Changes
1. **Basic Health Check**:
   ```bash
   # Start server
   poetry run uvicorn src.main:app --host 127.0.0.1 --port 8000
   
   # Test endpoints
   curl http://localhost:8000/          # Should return status message
   curl http://localhost:8000/health    # Should return {"status":"healthy"}
   curl http://localhost:8000/readyz    # Should return {"status":"ready"}
   ```

2. **API Functionality Test**:
   ```bash
   # Test echo endpoint
   curl -X POST "http://localhost:8000/echo" \
     -H "Content-Type: application/json" \
     -d '{"text": "Hello, the_board!"}'
   # Should echo back the message with model info
   ```

3. **Documentation Access**:
   ```bash
   # API docs should be accessible
   curl http://localhost:8000/docs
   # Should return HTML with FastAPI documentation
   ```

### Smoke Test Script
Use the PowerShell script at `scripts/smoke.ps1` for comprehensive testing:
```powershell
# Windows PowerShell
.\scripts\smoke.ps1 -Base "http://localhost:8000"
```

## Common Issues and Solutions

### Ollama Connection Failed
```bash
# Check if Ollama is running
ollama list

# Start Ollama if not running
ollama serve

# Verify Ollama API is accessible
curl http://localhost:11434/api/tags
```

### Python Version Issues
- Error: "Python version 3.12.3 is not supported"
- Solution: Install Python 3.11 exactly. The project will NOT work with 3.12+
- Verify: `python3.11 --version` should show Python 3.11.x

### Missing Models
```bash
# If you get model-related errors, ensure models are downloaded
ollama pull llama3.2
ollama pull mxbai-embed-large

# Verify models are available
ollama list
```

### Database/State Issues
```bash
# Reset state database if corrupted
rm -rf state/the_board_state.db
rm -rf chroma_db/

# The database will be recreated on next startup
```

## Development Workflow

### Making Changes
1. Always run the bootstrap commands first if starting fresh
2. Start development server: `poetry run dev`
3. Make your changes
4. Test endpoints manually or use smoke test script
5. Format code: `poetry run black src/ && poetry run isort src/`
6. Run type checking: `poetry run mypy src/ --ignore-missing-imports` (warnings acceptable)
7. Test startup: `poetry run uvicorn src.main:app --host 127.0.0.1 --port 8000`

### CI/CD Expectations
- The project uses standard Python formatting (black, isort)
- Type checking with mypy (some warnings are acceptable)
- No comprehensive test suite exists yet
- Manual testing is required for validation

## API Reference

### Core Endpoints
- `GET /` - Health check with status message
- `GET /health` - Simple health check
- `GET /healthz` - Alternative health check  
- `GET /readyz` - Readiness check (tests database connection)
- `POST /echo` - Echo endpoint for testing
- `GET /docs` - Interactive API documentation

### Future Endpoints (Implementation Pending)
- `POST /plan` - Strategic planning endpoint (requires full orchestration system)
- `GET /state/plans/{id}` - Plan status and details
- `POST /state/tasks/{id}/retry` - Task retry functionality

## Important Notes

### Environment Configuration
Default `.env` settings work for local development:
```bash
STATE_BACKEND=sqlite
STATE_DB_PATH=./state/the_board_state.db
PRIMARY_LLM=llama3.1:8b
EMBEDDING_MODEL=mxbai-embed-large:335m
OLLAMA_BASE_URL=http://localhost:11434
```

### Data Storage
- SQLite database: `./state/the_board_state.db` (created automatically)
- ChromaDB data: `./chroma_db/` (created automatically)
- Both use WAL mode for concurrent access

### Performance Tips
- Application startup is very fast (<5 seconds)
- Model downloads are one-time but large (several GB total)
- Keep Ollama running in background for best performance
- Use `--reload` flag only for development (impacts performance)

### Security Notes
- All processing happens locally (no external API calls for LLM)
- Database files contain persistent state
- Environment file may contain sensitive configuration

Always reference these instructions first before attempting to search for additional context or run exploratory commands.