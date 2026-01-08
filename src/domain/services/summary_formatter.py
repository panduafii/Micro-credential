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

    # Opening headline based on score
    if overall_pct >= 80:
        headline = (
            f"**Excellent work!** You demonstrated strong aptitude for the "
            f"{role_title} role with an overall score of **{overall_pct}%**."
        )
    elif overall_pct >= 60:
        headline = (
            f"**Good job!** Your assessment for the {role_title} role shows solid "
            f"foundations with room for growth. Overall score: **{overall_pct}%**."
        )
    else:
        headline = (
            f"**Thank you for completing the {role_title} assessment.** "
            f"Your results highlight areas for development. Overall score: **{overall_pct}%**."
        )

    lines.append(headline)
    lines.append("")

    # Detailed score breakdown with insights
    lines.append("**📊 Score Breakdown & Insights**")
    lines.append("")

    # Technical Knowledge analysis
    if theoretical_pct >= 80:
        tech_insight = "Strong grasp of core concepts! You're ready to tackle real-world problems."
    elif theoretical_pct >= 60:
        tech_insight = "Good foundation, but some concepts need reinforcement."
    else:
        tech_insight = "Focus on strengthening fundamental concepts through practice."
    lines.append(f"**Technical Knowledge:** {theoretical_pct}%")
    lines.append(f"  → {tech_insight}")
    lines.append("")

    # Profile alignment analysis
    if profile_pct >= 80:
        profile_insight = "Your experience aligns well with the role requirements."
    elif profile_pct >= 60:
        profile_insight = "You have relevant experience, with room to deepen expertise."
    else:
        profile_insight = "Building more hands-on experience will strengthen your profile."
    lines.append(f"**Profile Alignment:** {profile_pct}%")
    lines.append(f"  → {profile_insight}")
    lines.append("")

    # Essay quality analysis (if applicable)
    if has_essay:
        if essay_pct >= 80:
            essay_insight = "Excellent communication and problem-solving skills demonstrated."
        elif essay_pct >= 60:
            essay_insight = "Good explanations, consider adding more specific examples and details."
        else:
            essay_insight = (
                "Work on articulating technical concepts more clearly and comprehensively."
            )
        lines.append(f"**Essay Quality:** {essay_pct}%")
        lines.append(f"  → {essay_insight}")
        lines.append("")

    # Learning path recommendations
    recs = list(recommendations)
    if recs:
        lines.append("")
        lines.append("**🎯 Recommended Learning Path**")
        lines.append("")
        lines.append("Based on your results, these courses will help you level up your skills:")
        lines.append("")
        for idx, rec in enumerate(recs[:3], start=1):
            lines.append(f"**{idx}. {rec.course_title}**")
            if rec.match_reason:
                lines.append(f"   💡 Why this course: {rec.match_reason}")
            # Add relevance indicator
            relevance_stars = "⭐" * min(int(rec.relevance_score * 5), 5)
            lines.append(f"   Relevance: {relevance_stars} ({rec.relevance_score:.2f})")
            lines.append("")

    if degraded:
        lines.append("")
        lines.append(
            "_Note: Some recommendations may be limited due to temporary service constraints._"
        )

    return "\n".join(lines)
