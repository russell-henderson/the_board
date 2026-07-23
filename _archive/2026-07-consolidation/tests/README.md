# 🧪 Testing Suite for the_board

This directory contains comprehensive tests for all components of the **the_board** multi-agent orchestration system.

## 📋 Test Coverage

### **Core Components Tested**

- ✅ **State Management** (`test_state_store.py`)
  - Database initialization and schema
  - Plan and task CRUD operations
  - Event recording and retrieval
  - Final plan storage and retrieval

- ✅ **Data Models** (`test_models.py`)
  - Model validation and constraints
  - Serialization/deserialization
  - Enum values and edge cases
  - Data integrity checks

- ✅ **API Endpoints** (`test_api.py`)
  - Health check endpoints
  - Plan creation and management
  - State monitoring and inspection
  - Task cancellation and retry
  - Error handling and validation

- ✅ **Agent Tools** (`test_agent_tools.py`)
  - Code interpreter tool safety
  - Financial calculator functions
  - Tool registry and execution
  - Parameter validation

## 🚀 Running Tests

### **Prerequisites**

Ensure you have the development dependencies installed:

```bash
# Install dev dependencies (pytest, etc.)
poetry install --with dev

# Or if using pip
pip install pytest pytest-asyncio httpx
```

### **Running All Tests**

```bash
# Using poetry
poetry run test

# Using pytest directly
pytest tests/ -v

# Using the test runner script
python tests/run_tests.py
```

### **Running Specific Test Files**

```bash
# Test specific components
pytest tests/test_state_store.py -v
pytest tests/test_models.py -v
pytest tests/test_api.py -v
pytest tests/test_agent_tools.py -v

# Using the test runner
python tests/run_tests.py test_state_store.py
```

### **Running Specific Test Classes**

```bash
# Test specific test classes
pytest tests/test_state_store.py::TestStateStore -v
pytest tests/test_agent_tools.py::TestCodeInterpreterTool -v
```

### **Running Specific Test Methods**

```bash
# Test specific methods
pytest tests/test_state_store.py::TestStateStore::test_create_plan -v
pytest tests/test_agent_tools.py::TestFinancialCalculatorTool::test_roi_calculation -v
```

## 🎯 Test Categories

### **Unit Tests**
- **StateStore Tests**: Database operations, CRUD functionality
- **Model Tests**: Data validation, serialization
- **Tool Tests**: Individual tool functionality, safety features

### **Integration Tests**
- **API Tests**: Endpoint functionality, request/response handling
- **Workflow Tests**: Complete plan execution flows

### **Performance Tests**
- **Database Tests**: Connection management, query performance
- **Tool Tests**: Execution time, memory usage

## 🔧 Test Configuration

### **pytest.ini**
The test configuration is defined in `pytest.ini` at the project root:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --color=yes
```

### **Test Markers**
Tests can be categorized using markers:

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run tests excluding slow ones
pytest -m "not slow"
```

## 📊 Test Results

### **Expected Output**
When tests pass successfully, you should see:

```
🧪 Running the_board test suite...
==================================================
tests/test_state_store.py::TestStateStore::test_init_db PASSED
tests/test_state_store.py::TestStateStore::test_create_plan PASSED
tests/test_state_store.py::TestStateStore::test_create_task PASSED
...
==================================================
✅ All tests passed!
```

### **Test Statistics**
- **Total Tests**: 50+ comprehensive test cases
- **Coverage Areas**: Core functionality, edge cases, error handling
- **Execution Time**: Typically under 30 seconds for full suite

## 🐛 Debugging Tests

### **Verbose Output**
```bash
# Increase verbosity
pytest -vvv

# Show local variables on failure
pytest -l

# Show full traceback
pytest --tb=long
```

### **Running Failed Tests Only**
```bash
# Run only the last failed tests
pytest --lf

# Run tests that failed in the last run
pytest --ff
```

### **Debug Mode**
```bash
# Drop into debugger on failures
pytest --pdb

# Drop into debugger on errors
pytest --pdbcls=IPython.terminal.debugger:Pdb
```

## 🧹 Test Cleanup

### **Database Cleanup**
Tests use temporary databases that are automatically cleaned up:

```python
@pytest.fixture
def temp_db_path(self):
    """Create a temporary database path for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_path = f.name
    yield temp_path
    # Cleanup
    try:
        os.unlink(temp_path)
    except:
        pass
```

### **Resource Management**
- Temporary files are automatically removed
- Database connections are properly closed
- Memory is cleaned up after each test

## 📈 Adding New Tests

### **Test File Structure**
```python
#!/usr/bin/env python3
"""
Tests for [Component Name].

This module tests [component] functionality including:
- [Feature 1]
- [Feature 2]
- [Edge cases]
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.[module] import [Class]

class Test[ClassName]:
    """Test suite for [ClassName] functionality."""
    
    def test_[feature_name](self):
        """Test [specific functionality]."""
        # Arrange
        # Act
        # Assert
        pass
```

### **Test Naming Conventions**
- **Test files**: `test_[module_name].py`
- **Test classes**: `Test[ClassName]`
- **Test methods**: `test_[feature_description]`

### **Assertion Best Practices**
```python
# Use descriptive assertions
assert result.success is True, "Tool execution should succeed"
assert len(items) == 3, f"Expected 3 items, got {len(items)}"
assert "error" in result.error.lower(), "Error message should contain 'error'"
```

## 🚨 Common Issues

### **Import Errors**
If you encounter import errors:

```bash
# Ensure you're in the project root
cd /path/to/the_board

# Install dependencies
poetry install --with dev

# Run tests from project root
poetry run pytest tests/
```

### **Database Connection Issues**
Tests use temporary databases, but if you encounter issues:

```bash
# Check if SQLite is available
python -c "import sqlite3; print('SQLite available')"

# Verify database permissions
ls -la tests/
```

### **Test Environment Issues**
```bash
# Check Python version
python --version

# Verify pytest installation
pytest --version

# Check test discovery
pytest --collect-only
```

## 📚 Additional Resources

### **pytest Documentation**
- [pytest Official Docs](https://docs.pytest.org/)
- [pytest Fixtures](https://docs.pytest.org/en/stable/explanation/fixtures.html)
- [pytest Markers](https://docs.pytest.org/en/stable/how-to/mark.html)

### **Testing Best Practices**
- [Python Testing with pytest](https://pytest-book.readthedocs.io/)
- [Test-Driven Development](https://en.wikipedia.org/wiki/Test-driven_development)

---

**🎯 Goal**: Maintain 100% test coverage for all critical system components to ensure reliability and robustness.

**📊 Status**: Comprehensive test suite covering all major system components with automated execution and reporting.
