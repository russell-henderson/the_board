"""
System validation script - checks what's working without external dependencies.
"""

import sys
from pathlib import Path

# Add repo to path
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))

def check_models():
    """Check if model system is working."""
    try:
        from src.models.dataModel import AgentType, AgentResponse, TaskStatus, FinalPlan
        print("✓ Models package working")
        
        # Test enum functionality
        agents = list(AgentType)
        statuses = list(TaskStatus)
        print(f"✓ {len(agents)} agent types available: {[a.value for a in agents]}")
        print(f"✓ {len(statuses)} task statuses available")
        
        # Test object creation
        response = AgentResponse("CFO", "task_123", {"test": "data"}, 0.8)
        plan = FinalPlan("plan_456", "Test strategy", ["CFO"], ["Risk 1"], 0.9)
        print("✓ Model object creation working")
        
        return True
    except Exception as e:
        print(f"✗ Models package failed: {e}")
        return False

def check_agents():
    """Check if agent system is working."""
    try:
        from src.agents.specialists import BaseAgent, agent_registry
        from src.models.dataModel import AgentType
        
        print("✓ Agents package working")
        
        # Test agent registry
        print(f"✓ {len(agent_registry)} agents in registry: {[t.value for t in agent_registry.keys()]}")
        
        # Test agent execution
        if AgentType.CFO in agent_registry:
            agent = agent_registry[AgentType.CFO]
            response = agent.execute("Test task for validation")
            print(f"✓ Agent execution working (confidence: {response.confidence})")
            
        return True
    except Exception as e:
        print(f"✗ Agents package failed: {e}")
        return False

def check_orchestration():
    """Check if orchestration components can be imported."""
    try:
        from src.orchestration.runner import run_plan
        print("✓ Orchestration runner importable")
        return True
    except Exception as e:
        print(f"✗ Orchestration failed: {e}")
        return False

def check_structure():
    """Check if project structure is correct."""
    try:
        required_files = [
            "src/models/__init__.py",
            "src/models/dataModel.py", 
            "src/agents/__init__.py",
            "src/agents/specialists.py",
            "src/orchestration/__init__.py",
            "src/orchestration/runner.py",
            "src/main.py",
            "pyproject.toml",
            "QUICKSTART.md",
            ".env.example"
        ]
        
        missing = []
        for file_path in required_files:
            if not (repo_root / file_path).exists():
                missing.append(file_path)
        
        if missing:
            print(f"✗ Missing files: {missing}")
            return False
        else:
            print(f"✓ All {len(required_files)} required files present")
            return True
            
    except Exception as e:
        print(f"✗ Structure check failed: {e}")
        return False

def main():
    print("the_board System Validation")
    print("=" * 40)
    
    checks = [
        ("Project Structure", check_structure),
        ("Models System", check_models),
        ("Agents System", check_agents), 
        ("Orchestration", check_orchestration),
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        print(f"\n{name}:")
        if check_func():
            passed += 1
        
    print("\n" + "=" * 40)
    print(f"System Status: {passed}/{total} components working")
    
    if passed == total:
        print("🎉 System is fully functional!")
        print("\nNext steps:")
        print("1. Install FastAPI: pip install fastapi uvicorn")
        print("2. Start the server: uvicorn src.main:app --reload")
        print("3. Visit http://localhost:8000/docs for API documentation")
    else:
        print("⚠️ Some components need attention.")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)