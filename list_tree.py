#!/usr/bin/env python3
"""
list_tree.py – Print a clean file structure of the project,
excluding common noise like __pycache__, venv, logs, .git, etc.
"""

import os

# Directories and files to ignore
IGNORE_DIRS = {
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    "env",
    ".mypy_cache",
    ".pytest_cache",
    "logs",
    "dist",
    "build",
}
IGNORE_FILES = {
    ".DS_Store",
    "poetry.lock",  # optional, remove if you want to include
}

def print_tree(root_dir: str, prefix: str = ""):
    # Filtered entries
    entries = [
        e for e in os.listdir(root_dir)
        if e not in IGNORE_FILES
        and not any(e == d or e.startswith(d) for d in IGNORE_DIRS)
    ]
    entries.sort()

    for idx, entry in enumerate(entries):
        path = os.path.join(root_dir, entry)
        connector = "└── " if idx == len(entries) - 1 else "├── "
        print(prefix + connector + entry)

        if os.path.isdir(path):
            extension = "    " if idx == len(entries) - 1 else "│   "
            print_tree(path, prefix + extension)

if __name__ == "__main__":
    root = os.path.abspath(os.path.dirname(__file__))
    print(os.path.basename(root) + "/")
    print_tree(root)
