#!/usr/bin/env python3
"""
Script to test if profiling questions (Q8-Q10) have been updated in production.
Tests both backend-engineer and data-analyst roles.
"""

import os
import sys

import httpx

# Production API base URL
API_BASE_URL = os.getenv("API_BASE_URL", "https://microcred-api.onrender.com")

# For testing, we'll use hardcoded credentials or env vars
TEST_EMAIL = os.getenv("TEST_EMAIL", "test@example.com")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "testpassword123")


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{"=" * 60}")
    print(f"  {title}")
    print("=" * 60)


def register_and_login() -> str:
    """Register a test user and get access token."""
    print("🔐 Registering/logging in to get access token...")

    # Try to register (might fail if user exists, that's ok)
    register_url = f"{API_BASE_URL}/auth/register"
    register_data = {"email": TEST_EMAIL, "password": TEST_PASSWORD, "full_name": "Test User"}

    with httpx.Client() as client:
        try:
            resp = client.post(register_url, json=register_data, timeout=30.0)
            if resp.status_code == 201:
                print("✅ User registered successfully")
        except Exception as e:
            print(f"⚠️  Registration failed (user might already exist): {e}")

        # Login to get token
        login_url = f"{API_BASE_URL}/auth/login"
        login_data = {"email": TEST_EMAIL, "password": TEST_PASSWORD}

        try:
            resp = client.post(login_url, json=login_data, timeout=30.0)
            resp.raise_for_status()
            token_data = resp.json()
            print(f"📄 Login response: {token_data}")

            # Try different possible keys
            access_token = (
                token_data.get("access_token")
                or token_data.get("token")
                or token_data.get("tokens", {}).get("access_token")
                or token_data.get("data", {}).get("access_token")
            )

            if access_token:
                print("✅ Login successful, token obtained")
                return access_token
            else:
                print("❌ Login failed: No access token in response")
                print(f"   Available keys: {list(token_data.keys())}")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Login failed: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)


def check_role_questions(role_slug: str, token: str):
    """Check profiling questions for a specific role."""
    print_section(f"Testing {role_slug.upper()} Questions")

    url = f"{API_BASE_URL}/assessments/start"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"role_slug": role_slug}

    with httpx.Client() as client:
        try:
            resp = client.post(url, json=data, headers=headers, timeout=30.0)
            resp.raise_for_status()
            assessment = resp.json()

            assessment_id = assessment.get("id")
            questions = assessment.get("questions", [])

            print(f"✅ Assessment created: ID={assessment_id}")
            print(f"📋 Total questions: {len(questions)}")

            # Find profile questions 8, 9, 10
            profile_questions = [
                q
                for q in questions
                if q.get("question_type") == "profile" and q.get("sequence") in [8, 9, 10]
            ]

            if not profile_questions:
                print("❌ No profile questions Q8-Q10 found!")
                return

            print("\n🔍 Profile Questions (Q8-Q10):")
            for q in sorted(profile_questions, key=lambda x: x.get("sequence", 0)):
                seq = q.get("sequence")
                prompt = q.get("prompt", "")
                metadata = q.get("metadata", {})
                expected_values = q.get("expected_values", {})
                dimension = metadata.get("dimension", "N/A")
                allow_custom = expected_values.get("allow_custom", False)
                accepted_values = expected_values.get("accepted_values", [])

                print(f"\n  Q{seq}:")
                print(
                    f"    Prompt: {prompt[:80]}..." if len(prompt) > 80 else f"    Prompt: {prompt}"
                )
                print(f"    Dimension: {dimension}")
                print(f"    Allow Custom: {allow_custom}")
                print(f"    Accepted Values Count: {len(accepted_values)}")
                if accepted_values:
                    sample_values = ", ".join(accepted_values[:5])
                    print(f"    Sample Values: {sample_values}...")

                # Validation
                if seq == 8:
                    if "teknologi" in prompt.lower() or "tools" in prompt.lower():
                        print("    ✅ Q8 prompt looks correct (tech preferences)")
                    else:
                        print("    ⚠️  Q8 prompt might not be updated")

                    if allow_custom:
                        print("    ✅ Q8 allows custom input")
                    else:
                        print("    ❌ Q8 should allow custom input!")

                    if len(accepted_values) >= 10:
                        print(f"    ✅ Q8 has sufficient accepted values ({len(accepted_values)})")
                    else:
                        print(f"    ⚠️  Q8 has few accepted values ({len(accepted_values)})")

                elif seq == 9:
                    if "durasi" in prompt.lower() or "duration" in prompt.lower():
                        print("    ✅ Q9 prompt looks correct (duration preference)")
                    else:
                        print("    ⚠️  Q9 prompt might not be updated")

                elif seq == 10:
                    if "payment" in prompt.lower() or "berbayar" in prompt.lower():
                        print("    ✅ Q10 prompt looks correct (payment preference)")
                    else:
                        print("    ⚠️  Q10 prompt might not be updated")

        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Error: {e.response.status_code}")
            print(f"   Response: {e.response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    """Main test function."""
    print_section("PRODUCTION PROFILING QUESTIONS TEST")
    print(f"API URL: {API_BASE_URL}")
    print(f"Test User: {TEST_EMAIL}")

    # Get access token
    token = register_and_login()

    # Test both roles
    check_role_questions("backend-engineer", token)
    check_role_questions("data-analyst", token)

    print_section("TEST COMPLETE")
    print("\n✅ Test completed! Check the output above for validation results.\n")


if __name__ == "__main__":
    main()
