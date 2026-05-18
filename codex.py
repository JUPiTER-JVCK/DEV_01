#!/usr/bin/env python3
"""CODEX — Interactive Terminal Learning Reference.

Usage:
    python codex.py

Update:
    git pull

Requirements:
    pip install rich prompt_toolkit pyyaml pygments
"""

import sys

# Ensure minimum Python version
if sys.version_info < (3, 11):
    print("CODEX requires Python 3.11+")
    sys.exit(1)

from codex.app import main

if __name__ == "__main__":
    main()
