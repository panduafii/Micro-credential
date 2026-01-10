#!/usr/bin/env python
"""Check and fix question_templates metadata for profile questions."""

import asyncio

import asyncpg


async def main():
    conn = await asyncpg.connect(
        "postgresql://microcred_user:3i1doEdivimrYo1RaXr6ANlJE7il4Pfb@dpg-d59hv62li9vc73al72ug-a.singapore-postgres.render.com/microcred",
        timeout=10,
    )

    # Check profile question templates
    templates = await conn.fetch("""
        SELECT id, sequence, role_slug, prompt, metadata
        FROM question_templates
        WHERE question_type = 'profile'
        ORDER BY sequence
    """)

    print("=" * 80)
    print("PROFILE QUESTION TEMPLATES IN DB:")
    print("=" * 80)

    for t in templates:
        print(f'\nQ{t["sequence"]} (ID:{t["id"]}):')
        print(f'  Role: {t["role_slug"]}')
        print(f'  Prompt: {t["prompt"][:60]}...')
        print(f'  Metadata: {t["metadata"]}')

    # Fix metadata
    print("\n" + "=" * 80)
    print("FIXING QUESTION TEMPLATES METADATA:")
    print("=" * 80)

    # Map sequence to dimension
    sequence_dimension_map = {
        7: "experience-level",
        8: "tech-preferences",
        9: "content-duration",
        10: "payment-preference",
    }

    for seq, dimension in sequence_dimension_map.items():
        await conn.execute(
            """
            UPDATE question_templates
            SET metadata = '{"dimension": "' || $1 || '"}'::jsonb
            WHERE sequence = $2 AND question_type = 'profile'
        """,
            dimension,
            seq,
        )
        print(f"✅ Updated Q{seq} templates: dimension={dimension}")

    # Verify
    print("\n" + "=" * 80)
    print("VERIFYING:")
    print("=" * 80)

    templates = await conn.fetch("""
        SELECT id, sequence, role_slug, metadata
        FROM question_templates
        WHERE question_type = 'profile'
        ORDER BY sequence
    """)

    for t in templates:
        print(f'\nQ{t["sequence"]}: {t["metadata"]}')

    print("\n✅ Question templates metadata fixed!")
    print("New assessments will now have proper metadata dimension fields.")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
