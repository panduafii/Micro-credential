"""
Script Template for MicroCred-genAI Project

IMPORTANT: This template includes required path setup for importing src package.
Always use this template when creating new scripts in the scripts/ directory.
"""

from __future__ import annotations

import sys
from pathlib import Path

# CRITICAL: Add parent directory to Python path
# This allows importing from src package when script runs in any directory
sys.path.insert(0, str(Path(__file__).parent.parent))

# Now you can safely import from src
from src.core.config import get_settings


def main() -> None:
    """Main script logic goes here."""
    settings = get_settings()
    print(f"Environment: {settings.environment}")
    # Your script logic here


if __name__ == "__main__":
    main()
