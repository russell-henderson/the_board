# 🎯 the_board

> **Multi-Agent Orchestration System for Strategic Intelligence**

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Local-First](https://img.shields.io/badge/Local--First-100%25-brightgreen.svg)](https://github.com/ollama/ollama)

**the_board** is a groundbreaking collective intelligence system that orchestrates 20 specialized AI agents, each embodying the expertise of a world-class executive leader. Transform your high-level goals into actionable, multi-faceted strategies with an AI-powered "board of directors" that runs entirely on your local machine.

## 🚀 **What is the_board?**

Imagine having access to a full C-suite team (CEO, CFO, CTO, CMO, COO, and 15 other specialists) that can collaborate to solve complex business and strategic challenges. **the_board** makes this possible through:

- **🎭 20 Specialized AI Agents** - Each with distinct roles, expertise, and decision-making styles
- **🧠 Local-First Processing** - Complete data sovereignty using Ollama and local infrastructure
- **🔄 Self-Improving System** - Continuous learning from execution outcomes and feedback
- **🎯 Strategic Orchestration** - Intelligent task decomposition and multi-agent collaboration
- **📊 Comprehensive Knowledge Base** - ChromaDB-powered memory with citation tracking

## ✨ **Key Features**

### **🤖 Multi-Agent Intelligence**

- **Odyssey (CEO)** - Master orchestrator and goal decomposer
- **Momentum (COO)** - Execution and operational excellence
- **Abacus (CFO)** - Financial modeling and budget optimization
- **Nexus (CTO)** - Technical architecture and tool evaluation
- **Muse (CMO)** - Marketing strategy and brand positioning
- **And 15 more specialized agents...**

### **🔒 Privacy & Control**

- **100% Local Processing** - No data leaves your machine without permission
- **Complete Audit Trails** - Full visibility into decision-making processes
- **Configurable Security** - Granular control over data access and sharing
- **Human-in-the-Loop** - Escalation and oversight when needed

### **📈 Strategic Capabilities**

- **Goal Decomposition** - Break complex objectives into actionable tasks
- **Parallel Execution** - Multiple agents working simultaneously
- **Conflict Resolution** - Structured debate and consensus building
- **Synthesis Engine** - Cohesive output from diverse expertise
- **Risk Assessment** - Comprehensive analysis of potential challenges

## 🏗️ **Architecture Overview**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Query   │───▶│  FastAPI Backend │───▶│  Odyssey (CEO)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   State Store    │    │ Specialist      │
                       │   (SQLite)       │    │ Agents          │
                       └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   ChromaDB       │    │  Synthesis      │
                       │  (Knowledge)     │    │   Engine        │
                       └──────────────────┘    └─────────────────┘
```

## 🚀 **Quick Start**

### **Prerequisites**

- Python 3.11+
- [Ollama](https://ollama.ai/) installed and running
- Poetry (for dependency management)

### **Installation**

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/the_board.git
   cd the_board
   ```

2. **Install dependencies**

   ```bash
   poetry install
   ```

3. **Set up environment**

   ```bash
   cp example.env .env
   # Edit .env with your preferred settings
   ```

4. **Start Ollama and download models**

   ```bash
   ollama serve
   ollama pull llama3.1:8b
   ollama pull mxbai-embed-large:335m
   ```

5. **Launch the system**

   ```bash
   poetry run start
   ```

The system will be available at `http://localhost:8000`

## 📖 **Usage Examples**

### **Basic Strategic Planning**

```bash
# Submit a strategic goal
curl -X POST "http://localhost:8000/plan" \
  -H "Content-Type: application/json" \
  -d '{
    "high_level_goal": "Launch a SaaS product for small business accounting",
    "user_context": "I have 2 years of accounting experience and $50k budget"
  }'
```

### **Monitor Progress**

```bash
# Check plan status
curl "http://localhost:8000/state/plans/{plan_id}"

# View execution events
curl "http://localhost:8000/state/plans/{plan_id}/events"
```

### **Interactive API Documentation**

Visit `http://localhost:8000/docs` for the full interactive API reference.

## ⚙️ **Configuration**

### **Environment Variables**

```bash
# Core Settings
STATE_BACKEND=sqlite                    # State persistence backend
STATE_DB_PATH=./state/the_board_state.db # SQLite database path
CHROMA_PERSIST_DIRECTORY=./chroma_db    # Knowledge base storage

# LLM Configuration
PRIMARY_LLM=llama3.1:8b                # Main reasoning model
EMBEDDING_MODEL=mxbai-embed-large:335m  # Vector embedding model
OLLAMA_BASE_URL=http://localhost:11434  # Ollama service URL

# Performance Tuning
OLLAMA_NUM_CTX=4096                    # Context window size
OLLAMA_NUM_PARALLEL=2                  # Parallel requests
OLLAMA_NUM_THREADS=6                   # CPU threads
```

### **Model Selection**

- **Reasoning Models**: `llama3.1:8b`, `mistral:7b`, `codellama:7b`
- **Embedding Models**: `mxbai-embed-large:335m`, `nomic-embed-text`
- **Performance vs. Quality**: Smaller models for faster responses, larger for better reasoning

## 🧪 **Development**

### **Project Structure**

```
the_board/
├── src/                    # Main application code
│   ├── api/               # FastAPI routes and endpoints
│   ├── state/             # State management and persistence
│   └── main.py            # Application entry point
├── scripts/                # Utility scripts
├── docs/                   # Documentation
├── state/                  # SQLite database storage
├── logs/                   # Application logs
└── pyproject.toml         # Project configuration
```

### **Development Commands**

```bash
# Start development server
poetry run dev

# Run tests
poetry run pytest

# Code formatting
poetry run black src/
poetry run isort src/

# Type checking
poetry run mypy src/
```

### **Adding New Agents**

1. Create agent class in `src/agents/`
2. Define I/O schemas using Pydantic
3. Configure role-specific parameters
4. Add to orchestration logic
5. Update documentation

## 🔧 **API Reference**

### **Core Endpoints**

- `GET /` - Health check and status
- `POST /plan` - Submit strategic goals
- `GET /state/plans/{plan_id}` - Retrieve plan details
- `GET /state/plans/{plan_id}/events` - View execution history
- `POST /state/tasks/{task_id}/retry` - Retry failed tasks
- `POST /state/tasks/{task_id}/cancel` - Cancel running tasks

### **Data Models**

- **OdysseyGoalRequest** - User goal submission
- **PlanRecord** - Plan metadata and status
- **TaskRecord** - Individual task information
- **AgentResponseRecord** - Agent output and confidence
- **EventRecord** - System event logging

## 📊 **Performance & Scaling**

### **Hardware Requirements**

- **Minimum**: 8GB RAM, 4 CPU cores
- **Recommended**: 16GB+ RAM, 8+ CPU cores
- **Storage**: 10GB+ for models and knowledge base

### **Optimization Tips**

- Use quantized models for faster inference
- Adjust `OLLAMA_NUM_PARALLEL` based on CPU cores
- Monitor memory usage during large planning sessions
- Consider SSD storage for better I/O performance

## 🚨 **Troubleshooting**

### **Common Issues**

**Ollama Connection Failed**

```bash
# Check if Ollama is running
ollama list

# Restart Ollama service
ollama serve
```

**Out of Memory**

```bash
# Reduce context window
export OLLAMA_NUM_CTX=2048

# Use smaller model
export PRIMARY_LLM=mistral:7b
```

**Database Errors**

```bash
# Reset state database
rm -rf state/the_board_state.db
rm -rf chroma_db/
```

### **Logs and Debugging**

- Application logs: `logs/the_board.out.log`
- Error logs: `logs/the_board.err.log`
- Enable debug mode: Set `LOG_LEVEL=DEBUG` in `.env`

## 🤝 **Contributing**

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### **Development Setup**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests and documentation
5. Submit a pull request

### **Code Standards**

- Follow PEP 8 style guidelines
- Use type hints throughout
- Write comprehensive docstrings
- Include unit tests for new features

## 📚 **Documentation**

- **[Technical Specification](docs/TECHSPEC.md)** - Detailed system architecture
- **[Workflows](docs/WORKFLOWS.md)** - Operational procedures and state management
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment instructions
- **[Brand Guidelines](docs/BRAND_GUIDELINES.md)** - Visual identity and messaging

## 🖼️ Brand Guidelines

See the full brand standards in [docs/BRAND_GUIDELINES.md](docs/BRAND_GUIDELINES.md).

![Brand Board](docs/brand_board.png)

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- **Ollama** - Local LLM inference framework
- **FastAPI** - Modern Python web framework
- **ChromaDB** - Vector database for knowledge storage
- **SQLite** - Reliable local data persistence

## 📞 **Support & Community**

- **Issues**: [GitHub Issues](https://github.com/yourusername/the_board/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/the_board/discussions)
- **Documentation**: [Project Wiki](https://github.com/yourusername/the_board/wiki)

## 🎯 **Roadmap**

- **[Q1 2024]** - Core agent implementation and orchestration
- **[Q2 2024]** - Knowledge base integration and advanced workflows
- **[Q3 2024]** - Performance optimization and scaling improvements
- **[Q4 2024]** - Advanced features and production readiness

---

**the_board** - Where strategic intelligence meets local privacy. 🚀

*Built with ❤️ for the open-source community*
