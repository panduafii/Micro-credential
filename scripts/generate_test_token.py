#!/usr/bin/env python3
"""Generate test JWT tokens for API testing."""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.auth import create_access_token

# Generate admin token
admin_token = create_access_token("admin-test", roles=["admin"])
print(f"Admin Token:\n{admin_token}\n")

# Generate student token
student_token = create_access_token("student-test", roles=["student"])
print(f"Student Token:\n{student_token}")
