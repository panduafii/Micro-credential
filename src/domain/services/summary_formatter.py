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
    profile_signals: dict | None = None,
    missed_topics: list[str] | None = None,
    user_name: str | None = None,
) -> str:
    """Build a markdown summary for assessment results.

    Args:
        role_title: The assessment role title
        overall_pct: Overall score percentage
        theoretical_pct: Theoretical questions score percentage
        profile_pct: Profile questions score percentage
        essay_pct: Essay questions score percentage
        has_essay: Whether assessment had essay questions
        recommendations: List of course recommendations
        degraded: Whether recommendations are in degraded mode
        profile_signals: User preferences from profiling questions (Q8-Q10)
            - tech-preferences: What technologies/topics user wants to learn
            - content-duration: Preferred course duration (short/medium/long/any)
            - payment-preference: Payment preference (paid/free/any)
        missed_topics: List of topics where user scored poorly (weakness areas)
        user_name: User's display name for personalized greeting
    """
    lines: list[str] = []
    profile_signals = profile_signals or {}
    missed_topics = missed_topics or []

    # Extract tech preferences for personalized greeting
    tech_prefs = profile_signals.get("tech-preferences", "")

    # Build personalized greeting with name
    name_greeting = f"**Hello, {user_name}!** " if user_name else ""

    # Opening headline based on score with personalization
    if overall_pct >= 80:
        headline = (
            f"{name_greeting}**Excellent work!** You demonstrated strong capabilities "
            f"for the {role_title} role with an overall score of **{overall_pct}%**."
        )
        if tech_prefs:
            headline += f" Your interest in learning **{tech_prefs}** is perfect for this stage."
    elif overall_pct >= 60:
        headline = (
            f"{name_greeting}**Good job!** Your assessment for the {role_title} role shows "
            f"a solid foundation. Overall score: **{overall_pct}%**."
        )
        if tech_prefs:
            headline += f" Your focus on **{tech_prefs}** will help improve your skills."
    else:
        headline = (
            f"{name_greeting}**Thank you for completing the {role_title} assessment.** "
            f"Overall score: **{overall_pct}%**."
        )
        if tech_prefs:
            headline += f" Your desire to learn **{tech_prefs}** is a great step forward!"

    lines.append(headline)
    lines.append("")

    # Detailed score breakdown with insights
    lines.append("**Score Breakdown & Insights**")
    lines.append("")

    # Technical Knowledge analysis with actionable recommendations (now personalized)
    if theoretical_pct >= 80:
        if tech_prefs:
            tech_insight = (
                "Your theoretical understanding is excellent! "
                "You're ready for real-world challenges. "
                f"With your interest in **{tech_prefs}**, focus on advanced courses "
                "that deepen your expertise in those areas."
            )
        else:
            tech_insight = (
                "Your theoretical understanding is excellent! "
                "You're ready for real-world challenges. "
                "Consider advanced courses to deepen your expertise in specialization areas."
            )
    elif theoretical_pct >= 60:
        if tech_prefs:
            tech_insight = (
                "Your theoretical foundation is solid. "
                f"To improve your skills in **{tech_prefs}**, "
                "focus on areas where you scored lower and practice through "
                "hands-on projects. The courses below target your knowledge gaps."
            )
        else:
            tech_insight = (
                "Your theoretical foundation is solid. To improve further, "
                "focus on areas where you scored lower and practice through hands-on "
                "projects. The courses below target your knowledge gaps."
            )
    else:
        if tech_prefs:
            tech_insight = (
                "Your theoretical foundation needs strengthening. "
                f"Although you want to learn **{tech_prefs}**, start with fundamental "
                "courses that cover the basics, then build up with practical exercises. "
                "Don't rush - mastering the fundamentals is key to long-term success."
            )
        else:
            tech_insight = (
                "Your theoretical foundation needs strengthening. "
                "Start with beginner-friendly courses that cover the fundamentals, "
                "then build up with practical exercises. "
                "Don't rush - mastering the fundamentals is key to long-term success."
            )
    lines.append(f"• **Technical Knowledge:** {theoretical_pct}%")
    lines.append(f"  {tech_insight}")
    lines.append("")

    # Extract user preferences for personalized profile insight (tech_prefs already extracted above)
    duration_pref = profile_signals.get("content-duration", "any").lower()
    payment_pref = profile_signals.get("payment-preference", "any").lower()

    # Map duration preference to readable text
    duration_text_map = {
        "short": "short courses",
        "medium": "medium-length courses",
        "long": "comprehensive/long courses",
        "any": "various durations",
    }
    duration_text = duration_text_map.get(duration_pref, "various durations")

    # Map payment preference to readable text
    payment_text_map = {
        "free": "free",
        "paid": "paid (premium)",
        "any": "both free and paid",
    }
    payment_text = payment_text_map.get(payment_pref, "both free and paid")

    # Build personalized profile insight based on scores and preferences
    if profile_pct >= 80:
        if tech_prefs:
            profile_insight = (
                f"Based on your solid experience and profile score of **{profile_pct}%**, "
                f"you have a strong foundation for the {role_title} role. "
                f"Your desire to learn **{tech_prefs}** is well-suited and effective "
                f"given your current competencies. "
                f"With your preference for {duration_text} and {payment_text} options, "
                f"I recommend advanced courses to deepen your expertise."
            )
        else:
            profile_insight = (
                f"Your experience aligns well with the {role_title} requirements. "
                f"Profile score of **{profile_pct}%** indicates readiness for advanced level. "
                f"Focus your learning on deeper specialization areas."
            )
    elif profile_pct >= 60:
        if tech_prefs:
            profile_insight = (
                f"Based on your profile results ({profile_pct}%), "
                f"you have adequate experience but there's still room for growth. "
                f"Your desire to learn **{tech_prefs}** is quite effective. "
                f"With your preference for {duration_text} and {payment_text} options, "
                f"I recommend intermediate courses focusing on hands-on practice "
                f"to strengthen your {tech_prefs} skills."
            )
        else:
            profile_insight = (
                f"Profile score of {profile_pct}% indicates relevant experience. "
                f"Focus on courses that provide hands-on practice to deepen your competencies."
            )
    else:
        # User has weak foundation - prioritize missed topics first!
        missed_topics_text = ""
        if missed_topics:
            # Format missed topics for display
            if len(missed_topics) == 1:
                missed_topics_text = f"**{missed_topics[0]}**"
            elif len(missed_topics) == 2:
                missed_topics_text = f"**{missed_topics[0]}** and **{missed_topics[1]}**"
            else:
                joined = ", ".join(missed_topics[:-1])
                missed_topics_text = f"**{joined}**, and **{missed_topics[-1]}**"

        if tech_prefs:
            # Check if tech preference matches role or is realistic for beginner
            is_advanced_topic = any(
                adv in tech_prefs.lower()
                for adv in ["kubernetes", "microservices", "ml", "machine learning", "ai"]
            )

            if missed_topics and is_advanced_topic and theoretical_pct < 60:
                # User wants advanced topic but has weak foundation AND missed topics
                profile_insight = (
                    f"Based on your test results (theory: {theoretical_pct}%, "
                    f"profile: {profile_pct}%), you still need to strengthen some "
                    f"fundamental areas for the {role_title} role. "
                    f"Your results show you need to strengthen your understanding of "
                    f"{missed_topics_text} first. "
                    f"Your desire to learn **{tech_prefs}** is great, but I recommend "
                    f"learning {missed_topics_text} first, then progressing to {tech_prefs}. "
                    f"With your preference for {duration_text} ({payment_text}), "
                    f"I recommend courses that strengthen your foundational knowledge."
                )
            elif missed_topics:
                # User has missed topics, recommend fixing those first
                profile_insight = (
                    f"Based on your profile score ({profile_pct}%) and theory test "
                    f"({theoretical_pct}%), you're in the stage of building your foundation "
                    f"as a {role_title}. Your results show you need to "
                    f"strengthen your understanding of {missed_topics_text}. "
                    f"Your desire to learn **{tech_prefs}** is a good step! "
                    f"I recommend: first strengthen {missed_topics_text}, "
                    f"then proceed to {tech_prefs}. With your preference for {duration_text} and "
                    f"{payment_text} options, choose courses that build a solid foundation."
                )
            elif is_advanced_topic and theoretical_pct < 60:
                # User wants advanced topic but has weak foundation (no specific missed topics)
                profile_insight = (
                    f"Based on your test results (theory: {theoretical_pct}%, "
                    f"profile: {profile_pct}%), you're still in the stage of building "
                    f"your foundation for the {role_title} role. "
                    f"Your desire to learn **{tech_prefs}** may be **less effective** "
                    f"as it requires a strong foundational understanding first. "
                    f"I recommend starting with fundamental courses first, then gradually "
                    f"progressing to {tech_prefs}. With your preference for {duration_text} "
                    f"({payment_text}), choose beginner-friendly courses."
                )
            else:
                profile_insight = (
                    f"Based on your profile score ({profile_pct}%) and theory test "
                    f"({theoretical_pct}%), you're in the early stages of your journey "
                    f"as a {role_title}. Your desire to learn **{tech_prefs}** "
                    f"is a good step. With your preference for {duration_text} and "
                    f"{payment_text} options, I recommend foundational courses that provide "
                    f"hands-on practice to build a strong foundation."
                )
        else:
            # No tech preferences specified
            if missed_topics:
                profile_insight = (
                    f"Profile score of {profile_pct}% indicates you're still at the "
                    f"beginning of your {role_title} journey. Your results show you need "
                    f"to strengthen your understanding of {missed_topics_text}. "
                    f"Start with courses covering those topics, "
                    f"then build your portfolio with real projects to strengthen experience."
                )
            else:
                profile_insight = (
                    f"Profile score of {profile_pct}% indicates you're still at the "
                    f"beginning of your {role_title} journey. Start with foundational "
                    f"courses that provide hands-on practice. Build your portfolio with "
                    f"real projects to strengthen your experience."
                )

    lines.append(f"• **Profile Alignment:** {profile_pct}%")
    lines.append(f"  {profile_insight}")
    lines.append("")

    # Essay quality analysis (if applicable) with detailed feedback - now more personal
    if has_essay:
        if essay_pct >= 80:
            essay_insight = (
                "Excellent communication and problem-solving skills! "
                "Your answers demonstrate clear articulation of technical concepts, "
                "logical reasoning, and the ability to explain complex ideas effectively. "
                "These are valuable skills for collaboration and technical leadership roles."
            )
        elif essay_pct >= 60:
            essay_insight = (
                "Your explanations are quite good with clear understanding. "
                "To improve, consider adding more specific examples, "
                "deeper technical details, and more structured explanations. "
                "Practicing technical documentation writing can help enhance this skill."
            )
        else:
            essay_insight = (
                "There's room to improve your ability to articulate technical concepts. "
                "Focus on organizing your thoughts logically, providing specific "
                "examples, and explaining the 'why' behind technical decisions. "
                "Reading technical blogs and documentation can help improve this skill."
            )
        lines.append(f"• **Essay Quality:** {essay_pct}%")
        lines.append(f"  {essay_insight}")
        lines.append("")

    # Personalization preferences section
    tech_prefs = profile_signals.get("tech-preferences", "")
    duration_pref = profile_signals.get("content-duration", "any").lower()
    payment_pref = profile_signals.get("payment-preference", "any").lower()

    has_preferences = tech_prefs or duration_pref != "any" or payment_pref != "any"
    if has_preferences:
        lines.append("**Personalized Recommendations**")
        lines.append("")
        lines.append("Based on your selected preferences:")

        if tech_prefs:
            lines.append(f"• **Topics you want to learn:** {tech_prefs}")

        if duration_pref != "any":
            duration_text = {
                "short": "Short courses (< 2 hours)",
                "medium": "Medium courses (2-10 hours)",
                "long": "Comprehensive courses (> 10 hours)",
            }.get(duration_pref, duration_pref)
            lines.append(f"• **Content duration:** {duration_text}")

        if payment_pref != "any":
            payment_text = "Free" if payment_pref == "free" else "Paid"
            lines.append(f"• **Payment preference:** {payment_text}")

        lines.append("")
        lines.append(
            "The course recommendations below have been prioritized based on your preferences."
        )
        lines.append("")

    # Personalized learning path recommendations
    recs = list(recommendations)
    if recs:
        lines.append("")
        lines.append("**Personalized Learning Path**")
        lines.append("")

        # Add personalized intro based on overall performance and tech preferences
        if overall_pct >= 80:
            if tech_prefs:
                path_intro = (
                    f"Based on your strong performance and interest in **{tech_prefs}**, "
                    f"these advanced courses will help you reach expert level as a {role_title}:"
                )
            else:
                path_intro = (
                    f"Based on your strong performance, these advanced courses will help you "
                    f"specialize and reach expert level as a {role_title}:"
                )
        elif overall_pct >= 60:
            if tech_prefs:
                path_intro = (
                    f"To grow from your intermediate level and master **{tech_prefs}**, "
                    f"these courses target your growth areas:"
                )
            else:
                path_intro = (
                    "To grow from your intermediate level, these courses target "
                    "your growth areas and build on your existing strengths:"
                )
        else:
            if tech_prefs:
                path_intro = (
                    f"To build a strong foundation towards **{tech_prefs}**, start with "
                    f"these courses suited to your level that will gradually develop your skills:"
                )
            else:
                path_intro = (
                    "To build a strong foundation, start with these courses suited "
                    "to your level that will gradually develop your skills:"
                )

        lines.append(path_intro)
        lines.append("")

        for idx, rec in enumerate(recs[:5], start=1):  # Show top 5 instead of 3
            lines.append(f"{idx}. **{rec.course_title}**")

            # Add comprehensive explanation
            if rec.match_reason:
                lines.append(f"   • Recommendation reason: {rec.match_reason}")

            # Add personalization match info
            metadata = rec.course_metadata or {}
            personalization_matches = []

            # Check tech preference match
            if tech_prefs:
                course_title_lower = rec.course_title.lower()
                tech_keywords = [t.strip().lower() for t in tech_prefs.replace(",", " ").split()]
                matched_techs = [t for t in tech_keywords if t in course_title_lower]
                if matched_techs:
                    personalization_matches.append("Matches interest: " + ", ".join(matched_techs))

            # Check duration match
            level = metadata.get("level", "").lower()
            if duration_pref == "short" and "beginner" in level:
                personalization_matches.append("Suitable for beginners (short duration)")
            elif duration_pref == "medium" and "intermediate" in level:
                personalization_matches.append("Intermediate level matches preference")
            elif duration_pref == "long" and ("advanced" in level or "all levels" in level):
                personalization_matches.append("Comprehensive/advanced content matches preference")

            # Check payment match
            is_paid = str(metadata.get("is_paid", "True")).lower() == "true"
            if payment_pref == "free" and not is_paid:
                personalization_matches.append("Free as preferred")
            elif payment_pref == "paid" and is_paid:
                personalization_matches.append("Premium course as preferred")

            if personalization_matches:
                lines.append("   • Preference match: " + "; ".join(personalization_matches))

            # Add course metadata for better understanding
            if level:
                lines.append(f"   • Difficulty level: {level.title()}")

            # Add relevance with interpretation
            rel_score = rec.relevance_score
            if rel_score >= 0.8:
                rel_text = f"{rel_score:.2f}/1.0 (Highly Relevant)"
            elif rel_score >= 0.6:
                rel_text = f"{rel_score:.2f}/1.0 (Relevant)"
            else:
                rel_text = f"{rel_score:.2f}/1.0 (Somewhat Relevant)"
            lines.append(f"   • Match score: {rel_text}")

            lines.append("")

    if degraded:
        lines.append("")
        lines.append(
            "_Note: Some recommendations may be limited due to temporary service constraints._"
        )

    return "\n".join(lines)
