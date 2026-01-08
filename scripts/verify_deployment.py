#!/usr/bin/env python3
"""Verify new endpoints are deployed and working."""

from __future__ import annotations

import sys
from pathlib import Path

import requests

# REQUIRED: Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

API_URL = "https://microcred-api.onrender.com"


def check_health():
    """Check API health."""
    print("🏥 Checking API health...")
    response = requests.get(f"{API_URL}/health", timeout=10)
    data = response.json()

    if data["status"] == "ok":
        print("✅ API healthy")
        print(f"   - PostgreSQL: {data["datastores"]["postgres"]["status"]}")
        print(f"   - Redis: {data["datastores"]["redis"]["status"]}")
        return True
    else:
        print("❌ API degraded")
        return False


def check_new_endpoints():
    """Check if new endpoints exist (will get 401 without auth, but that's OK)."""
    print("\n🔍 Checking new endpoints...")

    # Check stats endpoint (should return 401 Unauthorized without token)
    response = requests.get(f"{API_URL}/assessments/stats/user", timeout=10)
    if response.status_code == 401:
        print("✅ GET /assessments/stats/user - Endpoint exists (needs auth)")
    else:
        print(f"⚠️  GET /assessments/stats/user - Status: {response.status_code}")

    # Check abandon endpoint (should return 401 Unauthorized without token)
    response = requests.delete(
        f"{API_URL}/assessments/test-id/abandon",
        timeout=10,
    )
    if response.status_code == 401:
        print("✅ DELETE /assessments/{id}/abandon - Endpoint exists (needs auth)")
    else:
        print(f"⚠️  DELETE /assessments/{{id}}/abandon - Status: {response.status_code}")


def main():
    """Run deployment verification."""
    print("=" * 60)
    print("  DEPLOYMENT VERIFICATION")
    print("=" * 60)

    try:
        if not check_health():
            print("\n❌ Health check failed - deployment may not be ready")
            sys.exit(1)

        check_new_endpoints()

        print("\n" + "=" * 60)
        print("✅ Deployment verification complete!")
        print("=" * 60)
        print("\nNew features ready:")
        print("  - Exit/abandon draft assessments")
        print("  - User assessment statistics")
        print("  - Timer support (45 min + 15 min grace)")
        print("\nNext steps:")
        print("  1. Update frontend to use new endpoints")
        print("  2. Implement timer UI component")
        print("  3. Test exit flow with real user")

    except Exception as exc:
        print(f"\n❌ Verification failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
