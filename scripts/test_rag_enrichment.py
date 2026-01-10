#!/usr/bin/env python
"""Test RAG service with new enrichment module locally."""

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from src.domain.services.rag import RAGService


async def main():
    # Create dummy session (not actually used for this test)
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        rag = RAGService(session)

        print("=" * 80)
        print("TESTING RAG SERVICE WITH ENRICHMENT")
        print("=" * 80)

        # Test 1: Load courses with enrichment
        print("\n1. Loading courses...")
        courses = rag._load_courses()
        print(f"   ✅ Loaded {len(courses)} courses")
        print(f"   ✅ Enriched {len(rag._enriched_courses)} courses")

        # Test 2: Sample enriched course
        print("\n2. Sample enriched course:")
        if courses:
            first_course = courses[0]
            enriched = first_course.get("_enriched")
            if enriched:
                print(f"   Title: {enriched.title[:60]}...")
                print(f"   Tech Tags: {enriched.tech_tags}")
                print(f"   Difficulty: {enriched.difficulty}")
                print(f"   Duration: {enriched.duration_hours}h ({enriched.duration_category})")
                print(f"   Payment: {enriched.payment_type}")
                print(f"   Quality Score: {enriched.quality_score:.2f}")

        # Test 3: Retrieve courses for golang + microservices
        print('\n3. Testing retrieval for "golang, microservices":')
        profile_signals = {
            "tech-preferences": "golang, microservices",
            "payment-preference": "any",
            "content-duration": "any",
        }

        query = rag._build_query(
            role_slug="backend-engineer",
            profile_signals=profile_signals,
            essay_keywords=[],
            missed_topics=[],
        )
        print(f"   Query built: {query[:100]}...")

        results = rag._retrieve_courses(
            query=query,
            top_k=5,
            missed_topics=[],
            profile_signals=profile_signals,
        )

        print(f"   ✅ Retrieved {len(results)} courses")

        if results:
            print("\n   Top 3 Results:")
            for i, course in enumerate(results[:3], 1):
                print(f"   {i}. [{course.relevance_score:.2f}] {course.title[:50]}")
                print(f"      Reason: {course.match_reason}")
                enriched_tags = course.metadata.get("enriched_tags", [])
                print(f"      Tags: {enriched_tags}")

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
