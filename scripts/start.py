import subprocess
import sys
from pathlib import Path

def main():
    root = Path(__file__).resolve().parents[1]
    script = root / "start.sh"
    if not script.exists():
        print("[the_board|start] start.sh not found at project root", file=sys.stderr)
        sys.exit(1)
    try:
        subprocess.run(["bash", str(script)], check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
