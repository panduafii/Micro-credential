from __future__ import annotations

from collections.abc import Iterable

from src.infrastructure.db.models import RecommendationItem


def format_assessment_summary(
    role_title: str,
    overall_pct: float,
    theoretical_pct: float,
    profile_pct: float,
    essay_pct: float,
    has_essay: bool,
    recommendations: Iterable[RecommendationItem],
    degraded: bool,
) -> str:
    """Build a markdown summary for assessment results."""
    lines: list[str] = []

    if overall_pct >= 80:
        headline = (
            f"**Excellent work!** You demonstrated strong aptitude for the " f"{role_title} role."
        )
    elif overall_pct >= 60:
        headline = (
            f"**Good job!** Your assessment for the {role_title} role shows solid "
            "foundations with room for growth."
        )
    else:
        headline = (
            f"**Thank you for completing the {role_title} assessment.** "
            "Your results highlight areas for development."
        )

    lines.append(f"{headline} Overall score: **{overall_pct}%**")
    lines.append("")
    lines.append("**Score Breakdown**")
    lines.append(f"- Technical Knowledge: **{theoretical_pct}%**")
    lines.append(f"- Profile Alignment: **{profile_pct}%**")
    if has_essay:
        lines.append(f"- Essay Quality: **{essay_pct}%**")

    recs = list(recommendations)
    if recs:
        lines.append("")
        lines.append("**Recommended Courses**")
        for idx, rec in enumerate(recs[:3], start=1):
            lines.append(f"{idx}. {rec.course_title}")
            if rec.match_reason:
                lines.append(f"   _{rec.match_reason}_")

    if degraded:
        lines.append("")
        lines.append(
            "_Note: Some recommendations may be limited due to temporary service constraints._"
        )

    return "\n".join(lines)
