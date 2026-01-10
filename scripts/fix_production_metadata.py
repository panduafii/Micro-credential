#!/usr/bin/env python
"""Fix metadata and regenerate fusion for production assessment."""

import asyncio

import asyncpg


async def main():
    conn = await asyncpg.connect(
        "postgresql://microcred_user:3i1doEdivimrYo1RaXr6ANlJE7il4Pfb@dpg-d59hv62li9vc73al72ug-a.singapore-postgres.render.com/microcred",
        timeout=10,
    )

    assessment_id = "d159d295-87f0-47b7-bb9c-ea3c5420d0e4"

    print("=" * 80)
    print(f"FIXING ASSESSMENT {assessment_id}")
    print("=" * 80)
    print()

    # Update metadata for profile questions
    print("🔧 Updating metadata for profile questions...")

    await conn.execute(
        """
        UPDATE assessment_question_snapshots
        SET metadata = '{"dimension": "experience-level"}'::jsonb
        WHERE assessment_id = $1 AND sequence = 7 AND question_type = 'profile'
    """,
        assessment_id,
    )
    print("✅ Q7 metadata updated: experience-level")

    await conn.execute(
        """
        UPDATE assessment_question_snapshots
        SET metadata = '{"dimension": "tech-preferences"}'::jsonb
        WHERE assessment_id = $1 AND sequence = 8 AND question_type = 'profile'
    """,
        assessment_id,
    )
    print("✅ Q8 metadata updated: tech-preferences")

    await conn.execute(
        """
        UPDATE assessment_question_snapshots
        SET metadata = '{"dimension": "content-duration"}'::jsonb
        WHERE assessment_id = $1 AND sequence = 9 AND question_type = 'profile'
    """,
        assessment_id,
    )
    print("✅ Q9 metadata updated: content-duration")

    await conn.execute(
        """
        UPDATE assessment_question_snapshots
        SET metadata = '{"dimension": "payment-preference"}'::jsonb
        WHERE assessment_id = $1 AND sequence = 10 AND question_type = 'profile'
    """,
        assessment_id,
    )
    print("✅ Q10 metadata updated: payment-preference")

    print()
    print("🔄 Deleting old recommendation...")

    # Delete old recommendation
    await conn.execute(
        """
        DELETE FROM recommendation_items
        WHERE recommendation_id IN (
            SELECT id FROM recommendations WHERE assessment_id = $1
        )
    """,
        assessment_id,
    )

    await conn.execute(
        """
        DELETE FROM recommendations WHERE assessment_id = $1
    """,
        assessment_id,
    )

    print("✅ Old recommendation deleted")

    # Verify metadata
    print()
    print("=" * 80)
    print("VERIFYING METADATA:")
    print("=" * 80)

    profile_qs = await conn.fetch(
        """
        SELECT sequence, metadata, response_data, score
        FROM assessment_question_snapshots aqs
        LEFT JOIN assessment_responses ar ON ar.question_snapshot_id = aqs.id
        LEFT JOIN scores s ON s.question_snapshot_id = aqs.id
        WHERE aqs.assessment_id = $1
          AND aqs.question_type = 'profile'
        ORDER BY sequence
    """,
        assessment_id,
    )

    for q in profile_qs:
        metadata = q["metadata"]
        dimension = metadata.get("dimension") if metadata else None
        resp = q["response_data"]
        val = resp.get("value") if isinstance(resp, dict) else str(resp)

        print(f'\nQ{q["sequence"]} ({dimension}):')
        print(f"  Response: {val}")
        print(f'  Score: {q["score"]}/100')

    print()
    print("=" * 80)
    print("✅ METADATA FIXED!")
    print("=" * 80)
    print()
    print(f"Assessment {assessment_id} is ready for fusion regeneration.")
    print("Run fusion service to generate new recommendations with tech preferences.")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
