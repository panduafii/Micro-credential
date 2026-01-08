"""Test RAG accuracy with specific user profile."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.domain.services.rag import RAGService


def test_rag_with_golang_preference():
    """Test RAG with:
    - Profile: Beginner
    - Tech preference: Golang
    - Payment: Any (free or paid)
    """
    print("=" * 60)
    print("Testing RAG Accuracy with User Preferences")
    print("=" * 60)

    # Create mock RAG service (without DB session for simple test)
    class MockSession:
        pass

    rag = RAGService(MockSession())  # type: ignore

    # Load courses to check dataset
    courses = rag._load_courses()
    print(f"\n📊 Total courses in dataset: {len(courses)}")

    # Count actual Golang courses (exact match)
    golang_courses = [c for c in courses if "golang" in c.get("course_title", "").lower()]
    print(f"📊 Courses with 'golang' in title: {len(golang_courses)}")

    for c in golang_courses[:5]:
        print(f"   - {c.get("course_title")}")

    # User profile signals
    profile_signals = {
        "tech-preferences": "golang",  # Q8: User wants to learn Golang
        "content-duration": "any",  # Q9: Any duration
        "payment-preference": "any",  # Q10: Free or paid
    }

    print("\n👤 User Profile:")
    print(f"   - Tech preferences: {profile_signals["tech-preferences"]}")
    print(f"   - Duration: {profile_signals["content-duration"]}")
    print(f"   - Payment: {profile_signals["payment-preference"]}")

    # Build query
    role_slug = "backend-engineer"
    query = rag._build_query(
        role_slug=role_slug, profile_signals=profile_signals, essay_keywords=[], missed_topics=[]
    )
    print(f"\n🔍 Built query: {query}")

    # Retrieve courses
    matches = rag._retrieve_courses(
        query=query, top_k=5, missed_topics=[], profile_signals=profile_signals
    )

    print("\n📚 Top 5 Recommendations:")
    print("-" * 60)

    golang_in_results = 0
    for i, match in enumerate(matches, 1):
        title = match.title
        # More strict check - must have 'golang' or 'go ' followed by programming context
        is_golang = "golang" in title.lower() or (
            "go " in title.lower()
            and any(
                kw in title.lower() for kw in ["programming", "language", "development", "google"]
            )
        )
        if is_golang:
            golang_in_results += 1
            marker = "✅ GOLANG"
        else:
            marker = "❌ NOT GOLANG"

        print(f"\n{i}. {title}")
        print(f"   {marker}")
        print(f"   Relevance: {match.relevance_score:.3f}")
        print(f"   Reason: {match.match_reason}")
        print(f"   Level: {match.metadata.get("level", "N/A")}")
        print(f"   Paid: {match.metadata.get("is_paid", "N/A")}")

    print("\n" + "=" * 60)
    print(f"ACCURACY: {golang_in_results}/5 courses match 'golang' preference")
    print(f"Note: Dataset only has {len(golang_courses)} Golang courses total")
    print("=" * 60)


def test_rag_with_python_beginner():
    """Test RAG for Python beginner wanting free courses."""
    print("\n\n" + "=" * 60)
    print("TEST 2: Python Beginner (Free Courses Only)")
    print("=" * 60)

    class MockSession:
        pass

    rag = RAGService(MockSession())  # type: ignore

    profile_signals = {
        "tech-preferences": "python",
        "content-duration": "short",  # Beginner = short courses
        "payment-preference": "free",
    }

    print("\n👤 User Profile:")
    print(f"   - Tech preferences: {profile_signals["tech-preferences"]}")
    print(f"   - Duration: {profile_signals["content-duration"]} (beginner)")
    print(f"   - Payment: {profile_signals["payment-preference"]}")

    role_slug = "backend-engineer"
    query = rag._build_query(
        role_slug=role_slug, profile_signals=profile_signals, essay_keywords=[], missed_topics=[]
    )
    print(f"\n🔍 Built query: {query}")

    matches = rag._retrieve_courses(
        query=query, top_k=5, missed_topics=[], profile_signals=profile_signals
    )

    print("\n📚 Top 5 Recommendations:")
    print("-" * 60)

    python_count = 0
    free_count = 0
    beginner_count = 0

    for i, match in enumerate(matches, 1):
        title = match.title
        is_python = "python" in title.lower()
        is_free = str(match.metadata.get("is_paid", "True")).lower() == "false"
        is_beginner = "beginner" in match.metadata.get("level", "").lower()

        if is_python:
            python_count += 1
        if is_free:
            free_count += 1
        if is_beginner:
            beginner_count += 1

        markers = []
        if is_python:
            markers.append("✅ Python")
        else:
            markers.append("❌ Not Python")
        if is_free:
            markers.append("✅ Free")
        else:
            markers.append("❌ Paid")
        if is_beginner:
            markers.append("✅ Beginner")

        print(f"\n{i}. {title}")
        print(f"   {" | ".join(markers)}")
        print(f"   Relevance: {match.relevance_score:.3f}")
        print(f"   Reason: {match.match_reason}")

    print("\n" + "=" * 60)
    print(f"RESULTS: Python={python_count}/5, Free={free_count}/5, Beginner={beginner_count}/5")
    print("=" * 60)


if __name__ == "__main__":
    test_rag_with_golang_preference()
    test_rag_with_python_beginner()
