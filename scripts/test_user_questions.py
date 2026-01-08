#!/usr/bin/env python3
"""Test Q9 Q10 untuk specific user email."""

import sys

import requests

API_URL = "https://microcred-api.onrender.com"


def login(email: str, password: str):
    """Login and get token."""
    response = requests.post(
        f"{API_URL}/auth/login",
        json={"email": email, "password": password},
        timeout=30,
    )
    data = response.json()
    if "tokens" in data:
        return data["tokens"]["access_token"]
    else:
        print(f"❌ Login failed: {data}")
        return None


def test_questions(role_slug: str, token: str):
    """Test questions for a role."""
    print(f"\n{"=" * 70}")
    print(f"  {role_slug.upper()}")
    print("=" * 70)

    # Start assessment
    response = requests.post(
        f"{API_URL}/assessments/start",
        headers={"Authorization": f"Bearer {token}"},
        json={"role_slug": role_slug},
        timeout=30,
    )
    data = response.json()
    questions = data.get("questions", [])

    # Show Q9 and Q10
    for q in questions:
        if q["sequence"] in [9, 10]:
            print(f"\nQ{q["sequence"]}: {q["prompt"]}")
            print("─" * 70)

            if q.get("options"):
                print("\n📋 OPTIONS:")
                for opt in q["options"]:
                    print(f"   {opt["id"]}. {opt["text"]}")

                # Check correctness
                texts = [opt["text"] for opt in q["options"]]
                if q["sequence"] == 9:
                    if any("jam" in t.lower() or "hour" in t.lower() for t in texts):
                        print("\n✅ Q9 CORRECT - Duration options")
                    else:
                        print("\n❌ Q9 WRONG OPTIONS:")
                        for t in texts:
                            print(f"      - {t}")
                elif q["sequence"] == 10:
                    if any("paid" in t.lower() or "free" in t.lower() for t in texts):
                        print("\n✅ Q10 CORRECT - Payment options")
                    else:
                        print("\n❌ Q10 WRONG OPTIONS:")
                        for t in texts:
                            print(f"      - {t}")
            else:
                print("\n⚠️  NO OPTIONS FOUND!")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  TEST SPECIFIC USER - Q9 & Q10 OPTIONS")
    print("=" * 70)

    # Get user credentials
    if len(sys.argv) >= 3:
        email = sys.argv[1]
        password = sys.argv[2]
    else:
        email = input("Email: ").strip()
        password = input("Password: ").strip()

    print(f"\n🔐 Logging in as: {email}")

    # Login
    token = login(email, password)
    if not token:
        print("❌ Failed to get token")
        sys.exit(1)

    print("✅ Login successful!")

    # Test both roles
    test_questions("backend-engineer", token)
    test_questions("data-analyst", token)

    print("\n" + "=" * 70)
    print("  TEST COMPLETE")
    print("=" * 70)
    print()
