import subprocess
import sys
from pathlib import Path

def main():
    root = Path(__file__).resolve().parents[1]
    script = root / "dev.sh"
    if not script.exists():
        print("[the_board|dev] dev.sh not found at project root", file=sys.stderr)
        sys.exit(1)
    # Use bash to run the script so env and PATH are respected
    try:
        subprocess.run(["bash", str(script)], check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
