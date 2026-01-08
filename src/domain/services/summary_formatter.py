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
    lines.append("**Score Breakdown & Insights**")
    lines.append("")

    # Technical Knowledge analysis with actionable recommendations
    if theoretical_pct >= 80:
        tech_insight = (
            "Strong grasp of core concepts. You are ready to tackle real-world problems. "
            "Consider taking advanced courses to deepen your expertise in specialized areas."
        )
    elif theoretical_pct >= 60:
        tech_insight = (
            "Good foundation with solid understanding of key concepts. "
            "To improve further, focus on areas where you scored lower and practice through "
            "hands-on projects. The recommended courses below target your knowledge gaps."
        )
    else:
        tech_insight = (
            "Your technical foundation needs strengthening. Start with beginner-friendly courses "
            "covering fundamentals, then build up with practical exercises. "
            "Don't rush - mastering basics is crucial for long-term success."
        )
    lines.append(f"• **Technical Knowledge:** {theoretical_pct}%")
    lines.append(f"  {tech_insight}")
    lines.append("")

    # Profile alignment analysis with experience-based guidance
    if profile_pct >= 80:
        profile_insight = (
            f"Your experience aligns excellently with {role_title} requirements. "
            "You have demonstrated hands-on familiarity with relevant tools and practices. "
            "The courses recommended focus on advancing your existing skills to expert level."
        )
    elif profile_pct >= 60:
        profile_insight = (
            "You have relevant experience, with room to deepen expertise. "
            "Your background shows promise, and with targeted learning in specific areas, "
            "you can bridge the gap to reach professional proficiency. "
            "Focus on courses that match your current level."
        )
    else:
        profile_insight = (
            "Building more hands-on experience will strengthen your profile significantly. "
            "The assessment indicates you may benefit from foundational courses that provide "
            "practical exposure. Start with beginner to intermediate level content, "
            "and work on real projects to build your portfolio."
        )
    lines.append(f"• **Profile Alignment:** {profile_pct}%")
    lines.append(f"  {profile_insight}")
    lines.append("")

    # Essay quality analysis (if applicable) with detailed feedback
    if has_essay:
        if essay_pct >= 80:
            essay_insight = (
                "Excellent communication and problem-solving skills demonstrated. "
                "Your responses show clear articulation of technical concepts, logical reasoning, "
                "and ability to explain complex ideas effectively. This is a valuable skill "
                "for collaboration and technical leadership roles."
            )
        elif essay_pct >= 60:
            essay_insight = (
                "Good explanations with clear understanding of the topics. "
                "To improve, consider adding more specific examples, deeper technical details, "
                "and structured explanations. Practice writing technical documentation "
                "and explaining concepts to others to enhance this skill."
            )
        else:
            essay_insight = (
                "Work on articulating technical concepts more clearly and comprehensively. "
                "Focus on organizing your thoughts logically, providing specific examples, "
                "and explaining the 'why' behind technical decisions. "
                "Reading technical blogs and documentation can help improve this skill."
            )
        lines.append(f"• **Essay Quality:** {essay_pct}%")
        lines.append(f"  {essay_insight}")
        lines.append("")

    # Personalized learning path recommendations
    recs = list(recommendations)
    if recs:
        lines.append("")
        lines.append("**Personalized Learning Path**")
        lines.append("")

        # Add personalized intro based on overall performance
        if overall_pct >= 80:
            path_intro = (
                "Based on your strong performance, these advanced courses will help you "
                f"specialize and reach expert level in {role_title}:"
            )
        elif overall_pct >= 60:
            path_intro = (
                "To progress from your current intermediate level, these courses target "
                "your growth areas and build on your existing strengths:"
            )
        else:
            path_intro = (
                "To build a strong foundation, start with these courses that match "
                "your current level and progressively develop your skills:"
            )

        lines.append(path_intro)
        lines.append("")

        for idx, rec in enumerate(recs[:5], start=1):  # Show top 5 instead of 3
            lines.append(f"{idx}. **{rec.course_title}**")

            # Add comprehensive explanation
            if rec.match_reason:
                lines.append(f"   • Why recommended: {rec.match_reason}")

            # Add course metadata for better understanding
            metadata = rec.course_metadata or {}
            level = metadata.get("level", "")
            if level:
                lines.append(f"   • Difficulty: {level}")

            # Add relevance with interpretation
            rel_score = rec.relevance_score
            if rel_score >= 0.8:
                rel_text = f"{rel_score:.2f}/1.0 (Highly Relevant)"
            elif rel_score >= 0.6:
                rel_text = f"{rel_score:.2f}/1.0 (Relevant)"
            else:
                rel_text = f"{rel_score:.2f}/1.0 (Moderately Relevant)"
            lines.append(f"   • Match Score: {rel_text}")

            lines.append("")

    if degraded:
        lines.append("")
        lines.append(
            "_Note: Some recommendations may be limited due to temporary service constraints._"
        )

    return "\n".join(lines)
