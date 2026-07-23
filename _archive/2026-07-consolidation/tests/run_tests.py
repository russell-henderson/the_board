#!/usr/bin/env python3
"""
Test runner for the_board.

This script runs all tests and provides a summary of results.
"""

import sys
import subprocess
from pathlib import Path

def run_tests():
    """Run all tests using pytest."""
    print("🧪 Running the_board test suite...")
    print("=" * 50)
    
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    
    try:
        # Run pytest
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/",
            "-v",
            "--tb=short",
            "--color=yes"
        ], cwd=project_root, capture_output=True, text=True)
        
        # Print output
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Print summary
        print("=" * 50)
        if result.returncode == 0:
            print("✅ All tests passed!")
        else:
            print(f"❌ Some tests failed (exit code: {result.returncode})")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def run_specific_test(test_file: str):
    """Run a specific test file."""
    print(f"🧪 Running specific test: {test_file}")
    print("=" * 50)
    
    project_root = Path(__file__).parent.parent
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            f"tests/{test_file}",
            "-v",
            "--tb=short",
            "--color=yes"
        ], cwd=project_root, capture_output=True, text=True)
        
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:", result.stderr)
        
        print("=" * 50)
        if result.returncode == 0:
            print("✅ Test passed!")
        else:
            print(f"❌ Test failed (exit code: {result.returncode})")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Run specific test
        test_file = sys.argv[1]
        success = run_specific_test(test_file)
    else:
        # Run all tests
        success = run_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
