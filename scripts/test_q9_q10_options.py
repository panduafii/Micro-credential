#!/usr/bin/env python3
"""Test Q9 and Q10 actual options returned by API."""

import requests

API_URL = "https://microcred-api.onrender.com"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"


def login():
    """Login and get token."""
    response = requests.post(
        f"{API_URL}/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        timeout=30,
    )
    data = response.json()
    if "tokens" in data:
        return data["tokens"]["access_token"]
    else:
        print(f"❌ Login failed: {data}")
        raise Exception("Login failed")


def check_role_options(role_slug: str, token: str):
    """Check Q9 and Q10 options for a role."""
    print(f"\n{"=" * 60}")
    print(f"  {role_slug.upper()} - Q9 & Q10 OPTIONS")
    print("=" * 60)

    # Start assessment
    response = requests.post(
        f"{API_URL}/assessments/start",
        headers={"Authorization": f"Bearer {token}"},
        json={"role_slug": role_slug},
        timeout=30,
    )
    data = response.json()

    questions = data.get("questions", [])

    # Find Q9 and Q10
    for q in questions:
        if q["sequence"] in [9, 10]:
            print(f"\n{"─" * 60}")
            print(f"Q{q["sequence"]}: {q["prompt"]}")
            print("─" * 60)

            # Show options (the actual dropdown choices)
            if q.get("options"):
                print("\n📋 OPTIONS (what user sees in dropdown):")
                for opt in q["options"]:
                    print(f"   {opt["id"]}. {opt["text"]}")
            else:
                print("\n⚠️  No options found (should have options!)")

            # Show expected_values (for validation)
            if q.get("expected_values"):
                print("\n✨ EXPECTED VALUES (backend validation):")
                ev = q["expected_values"]
                print(f"   Accepted: {ev.get("accepted_values", [])}")
                print(f"   Allow Custom: {ev.get("allow_custom", False)}")
            else:
                print("\n⚠️  No expected_values found")

            # Validation
            if q["sequence"] == 9:
                if q.get("options"):
                    texts = [opt["text"] for opt in q["options"]]
                    has_duration = any("jam" in t.lower() or "hour" in t.lower() for t in texts)
                    if has_duration:
                        print("\n✅ Q9 OPTIONS CORRECT - Duration preference")
                    else:
                        print("\n❌ Q9 OPTIONS WRONG!")
                        print(f"   Got: {texts}")
                else:
                    print("\n❌ Q9 has no options!")

            elif q["sequence"] == 10:
                if q.get("options"):
                    texts = [opt["text"] for opt in q["options"]]
                    has_payment = any("paid" in t.lower() or "free" in t.lower() for t in texts)
                    if has_payment:
                        print("\n✅ Q10 OPTIONS CORRECT - Payment preference")
                    else:
                        print("\n❌ Q10 OPTIONS WRONG!")
                        print(f"   Got: {texts}")
                else:
                    print("\n❌ Q10 has no options!")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  Q9 & Q10 OPTIONS TEST - PRODUCTION API")
    print("=" * 60)
    print(f"API: {API_URL}")
    print(f"User: {TEST_EMAIL}")

    # Login
    print("\n🔐 Logging in...")
    token = login()
    print("✅ Token obtained")

    # Check both roles
    check_role_options("backend-engineer", token)
    check_role_options("data-analyst", token)

    print("\n" + "=" * 60)
    print("  TEST COMPLETE")
    print("=" * 60)
    print(
        "\n💡 Check that options show duration (Short/Medium/Long)" " and payment (Paid/Free/Any)\n"
    )
