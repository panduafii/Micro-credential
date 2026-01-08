#!/usr/bin/env python3
"""
Test production API with multiple choice questions.

Usage:
    poetry run python scripts/test_production_with_mc.py
"""

import random
import string
import time

import requests

API_URL = "https://microcred-api.onrender.com"


def generate_test_email() -> str:
    """Generate random test email."""
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_{suffix}@test.com"


def test_assessment_flow() -> None:
    """Test complete assessment flow with multiple choice answers."""
    
    # 1. Register
    email = generate_test_email()
    password = "TestPass123!"
    
    print(f"1️⃣ Registering: {email}")
    resp = requests.post(
        f"{API_URL}/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Test User",
            "role": "student",
        },
        timeout=30,
    )
    resp.raise_for_status()
    token = resp.json()["tokens"]["access_token"]
    print(f"   ✅ Token: {token[:20]}...")
    
    # 2. Start assessment
    print("\n2️⃣ Starting backend-engineer assessment...")
    resp = requests.post(
        f"{API_URL}/assessments/start",
        json={"role_slug": "backend-engineer"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    assessment_id = data["assessment_id"]
    questions = data["questions"]
    
    print(f"   ✅ Assessment ID: {assessment_id}")
    print(f"   📝 Questions: {len(questions)} total")
    
    # Display questions with options
    for q in questions:
        print(f"\n   Q{q['sequence']} ({q['question_type']}): {q['prompt'][:50]}...")
        if q.get('options'):
            for opt in q['options']:
                print(f"      {opt['id']}. {opt['text'][:60]}...")
    
    # 3. Prepare responses
    responses = []
    for q in questions:
        if q['question_type'] == 'theoretical':
            # Multiple choice - pick A
            responses.append({
                "question_id": q["id"],
                "answer_text": None,
                "selected_option_id": "A"
            })
        elif q['question_type'] == 'essay':
            # Essay answer
            responses.append({
                "question_id": q["id"],
                "answer_text": "This is a test answer for essay question.",
                "selected_option_id": None
            })
        elif q['question_type'] == 'profile':
            # Profile - pick C (middle option)
            responses.append({
                "question_id": q["id"],
                "answer_text": None,
                "selected_option_id": "C"
            })
    
    # 4. Submit
    print("\n3️⃣ Submitting responses...")
    resp = requests.post(
        f"{API_URL}/assessments/{assessment_id}/submit",
        json={"responses": responses},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    resp.raise_for_status()
    submit_data = resp.json()
    print(f"   ✅ Submitted! Jobs: {submit_data.get('jobs_queued', [])}")
    
    # 5. Poll status
    print("\n4️⃣ Polling status...")
    max_polls = 30
    for i in range(max_polls):
        time.sleep(2)
        resp = requests.get(
            f"{API_URL}/assessments/{assessment_id}/status",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        resp.raise_for_status()
        status_data = resp.json()
        progress = status_data.get("overall_progress", 0)
        
        stages = status_data.get("stages", {})
        stage_status = " | ".join([
            f"{k.split('_')[0]}:{v.get('status', 'unknown')}"
            for k, v in stages.items()
        ])
        
        print(f"   [{i+1}] {progress:.0f}% | {stage_status}")
        
        if progress >= 100:
            print("   ✅ Processing completed!")
            break
    
    # 6. Get results
    print("\n5️⃣ Fetching results...")
    resp = requests.get(
        f"{API_URL}/assessments/{assessment_id}/result",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    resp.raise_for_status()
    result = resp.json()
    
    print("\n📊 RESULTS:")
    print(f"   Status: {result['status']}")
    print(f"   Summary: {result.get('summary', 'N/A')[:100]}...")
    
    breakdown = result.get('score_breakdown', {})
    print("\n   Score Breakdown:")
    for category, scores in breakdown.items():
        if isinstance(scores, dict):
            pct = scores.get('percentage', 0)
            score = scores.get('score', 0)
            max_score = scores.get('max', 0)
            print(f"   - {category.title()}: {score:.1f}/{max_score} ({pct:.1f}%)")
    
    print(f"\n📚 RECOMMENDATIONS ({len(result.get('recommendations', []))}):")
    for rec in result.get('recommendations', [])[:3]:
        print(f"   [{rec['rank']}] {rec['course_title']}")
        print(f"       URL: {rec['course_url']}")
        print(f"       Relevance: {rec['relevance_score']:.3f}")
        print(f"       Match: {rec['match_reason']}")
    
    print("\n✅ Test completed successfully!")


if __name__ == "__main__":
    test_assessment_flow()
