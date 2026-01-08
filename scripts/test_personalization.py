"""Test flow for personalized recommendations with updated profile questions."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# REQUIRED: Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
import pytest
import structlog

logger = structlog.get_logger(__name__)

BASE_URL = "https://microcred-api.onrender.com"
# BASE_URL = "http://localhost:8000"  # For local testing


@pytest.mark.skip(reason="Integration test - requires production API fully deployed with migration")
async def test_personalized_flow():
    """Test complete flow with personalized recommendations."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Step 0: Register new user
        print("\n=== Step 0: Register User ===")
        import random

        test_id = random.randint(1000, 9999)
        register_response = await client.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": f"test{test_id}@example.com",
                "password": "test123456",
                "full_name": f"Test User {test_id}",
            },
        )
        if register_response.status_code not in [200, 201]:
            print(f"Register failed ({register_response.status_code}): {register_response.text}")
            return

        register_data = register_response.json()
        token = register_data["tokens"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"✓ Registered as test{test_id}@example.com")

        # Step 1: Create assessment
        print("\n=== Step 1: Create Assessment ===")
        response = await client.post(
            f"{BASE_URL}/assessments/start",
            json={
                "role_slug": "backend-engineer",
            },
            headers=headers,
        )
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.text}")
            return
        assessment = response.json()
        print(f"Response: {assessment}")
        assessment_id = assessment.get("assessment_id") or assessment.get("id")
        print(f"Assessment ID: {assessment_id}")

        # Step 2: Get questions - already in start response
        print("\n=== Step 2: Get Questions ===")
        questions = assessment.get("questions", [])
        print(f"Total questions: {len(questions)}")

        # Find profile questions
        profile_questions = [q for q in questions if q["question_type"] == "profile"]
        print(f"\nProfile questions: {len(profile_questions)}")

        for q in profile_questions:
            print(f"\nQ{q["sequence"]}: {q["prompt"][:80]}...")
            if q["sequence"] == 8:
                print("  ✓ Q2 (Tech Preferences):")
                expected_values = q.get("expected_values", {})
                print(f"    - Options: {len(expected_values.get("accepted_values", []))} choices")
                print(f"    - Allow custom: {expected_values.get("allow_custom", False)}")
            elif q["sequence"] == 9:
                print("  ✓ Q3 (Duration Preference):")
                print(f"    - Options: {q.get("expected_values", {}).get("accepted_values", [])}")
            elif q["sequence"] == 10:
                print("  ✓ Q4 (Payment Preference):")
                print(f"    - Options: {q.get("expected_values", {}).get("accepted_values", [])}")

        # Step 3: Submit responses with preferences
        print("\n=== Step 3: Submit Responses with Preferences ===")

        # Group questions by type
        theoretical_qs = [q for q in questions if q["question_type"] == "theoretical"]
        essay_qs = [q for q in questions if q["question_type"] == "essay"]

        # Submit theoretical (MC) - answer A for all
        for q in theoretical_qs[:3]:
            response = await client.post(
                f"{BASE_URL}/assessments/{assessment_id}/responses",
                json={
                    "question_snapshot_id": q["id"],
                    "response_data": {"selected_option": "A"},
                },
                headers=headers,
            )
            print(f"  ✓ Submitted Q{q["sequence"]} (MC)")

        # Submit essays
        for q in essay_qs[:3]:
            response = await client.post(
                f"{BASE_URL}/assessments/{assessment_id}/responses",
                json={
                    "question_snapshot_id": q["id"],
                    "response_data": {
                        "answer": f"Sample essay answer for question {q["sequence"]}. "
                        f"This demonstrates understanding of the concept."
                    },
                },
                headers=headers,
            )
            print(f"  ✓ Submitted Q{q["sequence"]} (Essay)")

        # Submit profile with CUSTOM TECH preferences
        profile_responses = {
            7: {"value": "1-3"},  # Experience
            8: {"value": "Docker, Kubernetes, Rust"},  # Custom tech! (Rust not in list)
            9: {"value": "short"},  # Duration preference
            10: {"value": "free"},  # Payment preference - FREE only!
        }

        for q in profile_questions:
            seq = q["sequence"]
            if seq in profile_responses:
                response = await client.post(
                    f"{BASE_URL}/assessments/{assessment_id}/responses",
                    json={
                        "question_snapshot_id": q["id"],
                        "response_data": profile_responses[seq],
                    },
                    headers=headers,
                )
                print(f"  ✓ Submitted Q{seq} (Profile): {profile_responses[seq]}")

        # Step 4: Submit assessment (triggers async scoring)
        print("\n=== Step 4: Submit Assessment ===")
        response = await client.post(
            f"{BASE_URL}/assessments/{assessment_id}/submit",
            headers=headers,
        )
        print(f"Status: {response.status_code}")
        print("Assessment submitted - async jobs triggered")

        # Step 5: Poll for completion
        print("\n=== Step 5: Wait for Async Processing ===")
        for attempt in range(30):  # 2 minutes max
            await asyncio.sleep(4)
            response = await client.get(
                f"{BASE_URL}/assessments/{assessment_id}",
                headers=headers,
            )
            if response.status_code != 200:
                print(f"  Attempt {attempt + 1}: Got {response.status_code}, retrying...")
                continue

            data = response.json()
            status = data.get("status", "unknown")
            print(f"  Attempt {attempt + 1}: Status = {status}")

            if status == "completed":
                print("✓ Assessment completed!")
                break
        else:
            print("✗ Timeout waiting for completion")
            return

        # Step 6: Get result and verify personalization
        print("\n=== Step 6: Get Result (Verify Personalization) ===")
        response = await client.get(
            f"{BASE_URL}/assessments/{assessment_id}/result",
            headers=headers,
        )
        result = response.json()

        # Check recommendations
        recommendations = result.get("recommendations", [])
        print(f"\nRecommendations: {len(recommendations)} courses")

        print("\n=== Verification ===")
        print("Checking if RAG used preferences:")
        print("  1. Tech preference: Docker, Kubernetes, Rust")
        print("  2. Duration preference: short")
        print("  3. Payment preference: FREE")

        print("\nRecommended Courses:")
        for idx, rec in enumerate(recommendations, 1):
            title = rec.get("course_title", "N/A")
            is_paid = rec.get("is_paid", "N/A")
            reason = rec.get("match_reason", "N/A")
            relevance = rec.get("relevance_score", 0)

            print(f"\n{idx}. {title[:60]}")
            print(f"   Paid: {is_paid}")
            print(f"   Relevance: {relevance:.2f}")
            print(f"   Reason: {reason[:100]}")

            # Verify payment filter
            if is_paid:
                print("   ⚠️  WARNING: Found PAID course (should only show FREE!)")

        # Check if tech preferences mentioned
        summary = result.get("summary", "")
        if "docker" in summary.lower() or "kubernetes" in summary.lower():
            print("\n✓ Summary mentions user's tech preferences!")

        print("\n=== Test Complete ===")
        print(f"\nFull result URL: {BASE_URL}/assessments/{assessment_id}/result")


if __name__ == "__main__":
    asyncio.run(test_personalized_flow())
