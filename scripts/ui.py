#!/usr/bin/env python3
"""
Launch script for the_board Streamlit UI.

This script launches the beautiful Material Design-inspired interface for strategic planning.
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Launch the Streamlit UI."""
    # Get the path to the Streamlit app
    src_path = Path(__file__).parent.parent / "src" / "ui" / "streamlit_app.py
    
    if not src_path.exists():
        print(f"Streamlit app not found at: {src_path}")
        sys.exit(1)
    
    print("Launching the_board Streamlit UI...")
    print("Opening browser at: http://localhost:8501")
    print("Make sure the FastAPI backend is running on port 8000")
    print("Press Ctrl+C to stop the UI")
    
    try:
        # Launch Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(src_path),
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\nStreamlit UI stopped")
    except Exception as e:
        print(f"Error launching Streamlit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
