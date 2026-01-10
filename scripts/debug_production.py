#!/usr/bin/env python
"""Debug production assessment to find why tech preferences not showing."""

import asyncio
import json

import asyncpg


async def main():
    conn = await asyncpg.connect(
        "postgresql://microcred_user:3i1doEdivimrYo1RaXr6ANlJE7il4Pfb@dpg-d59hv62li9vc73al72ug-a.singapore-postgres.render.com/microcred",
        timeout=10,
    )

    sep = "=" * 80
    print(sep)
    print("SEARCHING FOR ASSESSMENT WITH Profile=43.8%, Theory=100%, Essay=15.4%")
    print(sep)

    # Search for assessments
    assessments = await conn.fetch("""
        SELECT a.id, a.owner_id, a.status, a.completed_at,
               r.overall_score,
               r.score_breakdown,
               r.created_at as rec_created
        FROM assessments a
        LEFT JOIN recommendations r ON r.assessment_id = a.id
        WHERE a.status = 'completed'
          AND r.score_breakdown IS NOT NULL
        ORDER BY a.created_at DESC
        LIMIT 10
    """)

    print(f"\nChecking {len(assessments)} recent assessments...\n")

    # Find the one with matching scores
    found = False
    for a in assessments:
        breakdown = a["score_breakdown"]
        if isinstance(breakdown, str):
            breakdown = json.loads(breakdown)

        profile_pct = breakdown.get("profile", {}).get("percentage", 0)
        theory_pct = breakdown.get("theoretical", {}).get("percentage", 0)
        essay_pct = breakdown.get("essay", {}).get("percentage", 0)
        overall_pct = breakdown.get("overall", {}).get("percentage", 0)

        # Match the scores from screenshot
        if abs(profile_pct - 43.8) < 1 and abs(theory_pct - 100) < 1 and abs(essay_pct - 15.4) < 1:
            found = True
            print("🎯 FOUND IT!")
            print(f'   Assessment ID: {a["id"]}')
            print(f'   Owner: {a["owner_id"]}')
            print(f'   Completed: {a["completed_at"]}')
            print(f"   Scores: Theory={theory_pct}% Essay={essay_pct}% Profile={profile_pct}%")
            print(f"   Overall: {overall_pct}%")

            assessment_id = a["id"]

            # Check ALL profile responses
            print(f"\n{sep}")
            print("PROFILE RESPONSES (Q7-Q10):")
            print(sep)

            profile_qs = await conn.fetch(
                """
                SELECT aqs.sequence, ar.response_data, s.score,
                       aqs.metadata
                FROM assessment_question_snapshots aqs
                LEFT JOIN assessment_responses ar ON ar.question_snapshot_id = aqs.id
                LEFT JOIN scores s ON s.question_snapshot_id = aqs.id
                WHERE aqs.assessment_id = $1
                  AND aqs.question_type = 'profile'
                ORDER BY aqs.sequence
            """,
                assessment_id,
            )

            for q in profile_qs:
                resp = q["response_data"]
                val = resp.get("value") if isinstance(resp, dict) else str(resp)
                metadata = q["metadata"]
                dimension = metadata.get("dimension") if isinstance(metadata, dict) else None

                print(f'\nQ{q["sequence"]} ({dimension}):')
                print(f'  Response: "{val}"')
                print(f'  Score: {q["score"]}/100')

            # Check recommendation summary
            print(f"\n{sep}")
            print("RECOMMENDATION SUMMARY CHECK:")
            print(sep)

            rec = await conn.fetchrow(
                """
                SELECT summary
                FROM recommendations
                WHERE assessment_id = $1
            """,
                assessment_id,
            )

            if rec:
                summary = rec["summary"]
                print(f"\nSummary length: {len(summary)} chars")

                # Check key phrases
                if "golang" in summary.lower():
                    print('✅ Mentions "golang"')
                else:
                    print('❌ Does NOT mention "golang"')

                if "microservice" in summary.lower():
                    print('✅ Mentions "microservice"')
                else:
                    print('❌ Does NOT mention "microservice"')

                if "redis" in summary.lower():
                    print('✅ Mentions "redis"')
                else:
                    print('❌ Does NOT mention "redis"')

                if "haven't specified" in summary.lower():
                    print("❌ Says user HASN'T specified tech preferences")
                    # Print that part
                    idx = summary.lower().find("haven't specified")
                    print("\nProblematic section:")
                    print(summary[max(0, idx - 100) : idx + 200])

            break

    if not found:
        print("❌ No assessment found with exact scores!")
        print("\nShowing all recent assessments:")
        for i, a in enumerate(assessments, 1):
            breakdown = a["score_breakdown"]
            if isinstance(breakdown, str):
                breakdown = json.loads(breakdown)

            profile_pct = breakdown.get("profile", {}).get("percentage", 0)
            theory_pct = breakdown.get("theoretical", {}).get("percentage", 0)
            essay_pct = breakdown.get("essay", {}).get("percentage", 0)

            print(
                f"\n{i}. {a["id"][:8]}... "
                f"Theory={theory_pct}% "
                f"Essay={essay_pct}% "
                f"Profile={profile_pct}%"
            )

    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
