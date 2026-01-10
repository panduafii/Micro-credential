"""
Test script for course enrichment module.

Tests the comprehensive metadata extraction and user preference matching.
"""

import asyncio
import csv
from pathlib import Path

from src.infrastructure.repositories.course_enrichment import (
    CourseEnricher,
)

# Path to courses CSV
COURSES_CSV = Path(__file__).parent.parent / "src/infrastructure/repositories/udemy_courses.csv"


async def main():
    """Test enrichment on sample courses."""
    print("=" * 80)
    print("COURSE ENRICHMENT TEST")
    print("=" * 80)

    # Load some sample courses
    courses = []
    with open(COURSES_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            courses.append(row)
            if i >= 20:  # Test with first 20 courses
                break

    print(f"\nLoaded {len(courses)} sample courses\n")

    # Test enrichment
    enriched_courses = []
    for course in courses:
        enriched = CourseEnricher.enrich_course(course)
        enriched_courses.append(enriched)

    print("=" * 80)
    print("SAMPLE ENRICHED COURSES:")
    print("=" * 80)

    for i, enriched in enumerate(enriched_courses[:5], 1):
        print(f"\n{i}. {enriched.title[:60]}...")
        print(f"   Tech Tags: {enriched.tech_tags}")
        print(f"   Difficulty: {enriched.difficulty}")
        print(f"   Payment: {enriched.payment_type} (${enriched.price})")
        print(f"   Duration: {enriched.duration_hours}h ({enriched.duration_category})")
        print(f"   Quality Score: {enriched.quality_score:.2f}")
        print(f"   Popularity: {enriched.num_subscribers:,} subscribers")

    # Test user preference matching
    print("\n" + "=" * 80)
    print("TESTING USER PREFERENCE MATCHING")
    print("=" * 80)

    # Scenario 1: User wants golang + microservices (like our test case)
    user_tech_prefs = ["golang", "microservices"]
    payment_pref = "any"
    duration_pref = "any"

    print("\nUser Preferences:")
    print(f"  Tech: {user_tech_prefs}")
    print(f"  Payment: {payment_pref}")
    print(f"  Duration: {duration_pref}")

    matches = []
    for enriched in enriched_courses:
        matched, score = CourseEnricher.match_user_preferences(
            enriched,
            user_tech_prefs,
            payment_pref,
            duration_pref,
        )
        if matched:
            matches.append((score, enriched))

    # Sort by score
    matches.sort(key=lambda x: x[0], reverse=True)

    print(f"\n{len(matches)} courses matched (from sample of {len(enriched_courses)})")

    if matches:
        print("\nTop Matches:")
        for i, (score, enriched) in enumerate(matches[:5], 1):
            print(f"\n{i}. [{score:.2f}] {enriched.title[:60]}...")
            print(f"   Tags: {enriched.tech_tags}")
            print(
                f"   {enriched.difficulty} | {enriched.duration_hours}h | {enriched.payment_type}"
            )

    # Scenario 2: User wants free Python courses
    print("\n" + "=" * 80)
    print("SCENARIO 2: Free Python courses")
    print("=" * 80)

    user_tech_prefs_2 = ["python"]
    payment_pref_2 = "free"

    matches_2 = []
    for enriched in enriched_courses:
        matched, score = CourseEnricher.match_user_preferences(
            enriched,
            user_tech_prefs_2,
            payment_pref_2,
            "any",
        )
        if matched:
            matches_2.append((score, enriched))

    matches_2.sort(key=lambda x: x[0], reverse=True)

    print(f"\n{len(matches_2)} courses matched")
    if matches_2:
        for i, (score, enriched) in enumerate(matches_2[:3], 1):
            print(f"\n{i}. [{score:.2f}] {enriched.title[:60]}")
            print(f"   Tags: {enriched.tech_tags}")
            print(f"   FREE | {enriched.duration_hours}h")

    print("\n" + "=" * 80)
    print("TEST COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
