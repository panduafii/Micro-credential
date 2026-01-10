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
    tech_prefs_raw = profile_signals.get("tech-preferences", "")
    if isinstance(tech_prefs_raw, list):
        tech_prefs = ", ".join(str(item).strip() for item in tech_prefs_raw if str(item).strip())
    else:
        tech_prefs = str(tech_prefs_raw) if tech_prefs_raw is not None else ""

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

    # Theory analysis with actionable recommendations
    if theoretical_pct >= 80:
        theory_insight = (
            "Your theoretical understanding is excellent! "
            "You've mastered the fundamental concepts and are ready for real-world challenges. "
            "Consider advanced courses to deepen your expertise in specialization areas."
        )
    elif theoretical_pct >= 60:
        theory_insight = (
            "Your theoretical foundation is solid. To improve further, "
            "focus on areas where you scored lower and practice through hands-on "
            "projects. The courses below target your knowledge gaps."
        )
    else:
        theory_insight = (
            "Your theoretical foundation needs strengthening. "
            "Start with beginner-friendly courses that cover the fundamentals, "
            "then build up with practical exercises. "
            "Don't rush - mastering the fundamentals is key to long-term success."
        )
    lines.append(f"• **Theory:** {theoretical_pct}%")
    lines.append(f"  {theory_insight}")
    lines.append("")

    # Essay quality analysis (if applicable) - includes missed topics feedback
    if has_essay:
        # Format missed topics for display in essay section
        missed_topics_text = ""
        if missed_topics:
            if len(missed_topics) == 1:
                missed_topics_text = f"**{missed_topics[0]}**"
            elif len(missed_topics) == 2:
                missed_topics_text = f"**{missed_topics[0]}** and **{missed_topics[1]}**"
            else:
                joined = ", ".join(missed_topics[:-1])
                missed_topics_text = f"**{joined}**, and **{missed_topics[-1]}**"

        if essay_pct >= 80:
            essay_insight = (
                "Excellent communication and problem-solving skills! "
                "Your answers demonstrate clear articulation of technical concepts, "
                "logical reasoning, and the ability to explain complex ideas effectively. "
                "These are valuable skills for collaboration and technical leadership roles."
            )
        elif essay_pct >= 60:
            if missed_topics:
                essay_insight = (
                    "Your explanations are quite good with clear understanding. "
                    "However, your essay answers show you could strengthen "
                    f"your understanding of {missed_topics_text}. "
                    "To improve, consider adding more specific examples "
                    "and deeper technical details in those areas. "
                    "Practicing technical documentation writing can help."
                )
            else:
                essay_insight = (
                    "Your explanations are quite good with clear understanding. "
                    "To improve, consider adding more specific examples, "
                    "deeper technical details, and more structured explanations. "
                    "Practicing technical documentation writing can help enhance this skill."
                )
        else:
            if missed_topics:
                essay_insight = (
                    "There's room to improve your ability to articulate "
                    "technical concepts. Your essay answers indicate gaps in "
                    f"understanding {missed_topics_text}. Focus on studying "
                    "these topics, organizing your thoughts logically, and "
                    "explaining the 'why' behind technical decisions. "
                    "Reading technical blogs and documentation can help."
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

    # Extract user preferences for profile insight
    duration_pref_raw = profile_signals.get("content-duration", "any")
    if isinstance(duration_pref_raw, list):
        duration_pref_raw = duration_pref_raw[0] if duration_pref_raw else "any"
    duration_pref = str(duration_pref_raw).lower()

    payment_pref_raw = profile_signals.get("payment-preference", "any")
    if isinstance(payment_pref_raw, list):
        payment_pref_raw = payment_pref_raw[0] if payment_pref_raw else "any"
    payment_pref = str(payment_pref_raw).lower()

    # Map duration preference to readable text
    duration_text_map = {
        "short": "short courses (< 2 hours)",
        "medium": "medium-length courses (2-10 hours)",
        "long": "comprehensive/long courses (> 10 hours)",
        "any": "any duration",
    }
    duration_text = duration_text_map.get(duration_pref, "any duration")

    # Map payment preference to readable text
    payment_text_map = {
        "free": "free courses",
        "paid": "paid (premium) courses",
        "any": "both free and paid courses",
    }
    payment_text = payment_text_map.get(payment_pref, "both free and paid courses")

    # Profile Alignment - FINAL SECTION as conclusion
    # This discusses: experience/projects, tech preferences, duration, payment
    # Then concludes with WHY the recommendations are suitable

    # Build profile insight focusing on user's background and preferences
    profile_parts = []

    # Part 1: Experience level interpretation
    if profile_pct >= 80:
        exp_text = (
            f"With a profile score of **{profile_pct}%**, you have significant experience "
            f"in the {role_title} field. Your coding journey and project portfolio "
            "demonstrate solid practical foundations."
        )
    elif profile_pct >= 60:
        exp_text = (
            f"With a profile score of **{profile_pct}%**, you have moderate experience "
            f"as a {role_title}. You've started building your portfolio but there's "
            "room for more hands-on project experience."
        )
    else:
        exp_text = (
            f"With a profile score of **{profile_pct}%**, you're at the beginning of your "
            f"{role_title} journey. Building more projects and gaining coding experience "
            "will strengthen your foundation."
        )
    profile_parts.append(exp_text)

    # Part 2: Tech preferences - Critical for personalization
    if tech_prefs and tech_prefs.strip():
        # Parse tech preferences (may be comma-separated)
        tech_list = [t.strip() for t in tech_prefs.split(",") if t.strip()]
        if tech_list:
            if len(tech_list) == 1:
                tech_display = f"**{tech_list[0]}**"
            elif len(tech_list) == 2:
                tech_display = f"**{tech_list[0]}** and **{tech_list[1]}**"
            else:
                tech_display = ", ".join(f"**{t}**" for t in tech_list[:-1])
                tech_display += f", and **{tech_list[-1]}**"

            tech_text = f"You've expressed interest in learning {tech_display}."
            profile_parts.append(tech_text)
    else:
        # User hasn't specified tech preferences - guide them
        tech_text = (
            "**Note:** You haven't specified which technologies you want to learn. "
            "Identifying your learning goals (e.g., Python, Docker, AWS) will help us "
            "provide more targeted course recommendations."
        )
        profile_parts.append(tech_text)

    # Part 3: Learning preferences (duration + payment)
    if duration_pref != "any" or payment_pref != "any":
        pref_items = []
        if duration_pref != "any":
            pref_items.append(duration_text)
        if payment_pref != "any":
            pref_items.append(payment_text)
        pref_text = "Your learning preferences: " + ", ".join(pref_items) + "."
        profile_parts.append(pref_text)

    # Part 4: READINESS ASSESSMENT & CONCLUSION
    # Determine if user is ready for their desired tech or needs prerequisites
    has_valid_tech_prefs = tech_prefs and tech_prefs.strip()

    if has_valid_tech_prefs:
        tech_lower = tech_prefs.lower()

        # Define advanced topics that require strong fundamentals
        advanced_topics = [
            "kubernetes",
            "k8s",
            "microservices",
            "machine learning",
            "ml",
            "deep learning",
            "ai",
            "artificial intelligence",
            "docker",
            "terraform",
            "aws",
            "azure",
            "gcp",
            "cloud",
            "devops",
            "kafka",
            "redis",
            "elasticsearch",
            "graphql",
        ]

        # Define fundamental topics
        fundamental_topics = [
            "python",
            "javascript",
            "java",
            "html",
            "css",
            "sql",
            "git",
            "api",
            "rest",
            "database",
            "programming",
        ]

        is_advanced = any(adv in tech_lower for adv in advanced_topics)
        is_fundamental = any(fund in tech_lower for fund in fundamental_topics)

        # ADVANCED topics + LOW experience = Need prerequisites
        if is_advanced and profile_pct < 50 and theoretical_pct < 60:
            conclusion = (
                f"**Readiness Assessment:** Your interest in {tech_prefs} is excellent "
                "for long-term career growth! However, these are advanced topics that "
                "require solid programming fundamentals. "
                "**Recommendation:** The courses below focus on building strong foundations "
                f"(APIs, databases, backend basics). Master these first, then you'll be "
                f"ready to dive into {tech_prefs}. Estimated timeline: 3-6 months of foundation "
                "building before tackling advanced topics."
            )

        # ADVANCED topics + MODERATE experience = Can start with guided approach
        elif is_advanced and profile_pct >= 50 and theoretical_pct >= 60:
            conclusion = (
                f"**Readiness Assessment:** You have a decent foundation to start exploring "
                f"{tech_prefs}! Your theoretical knowledge ({theoretical_pct}%) shows you "
                "understand core concepts. "
                "**Recommendation:** The courses below include both foundational reinforcement "
                f"and introductory {tech_prefs} content. Take them in sequence to build "
                "confidence before diving into advanced implementations."
            )

        # FUNDAMENTAL topics + ANY level = Good match
        elif is_fundamental:
            if profile_pct >= 60:
                conclusion = (
                    f"**Readiness Assessment:** Perfect match! Your experience level "
                    f"and interest in {tech_prefs} align well. "
                    "**Recommendation:** The courses below will deepen your expertise "
                    "in these core technologies and introduce advanced patterns."
                )
            else:
                conclusion = (
                    f"**Readiness Assessment:** Great choice! {tech_prefs} are fundamental "
                    "technologies that every developer should master. "
                    "**Recommendation:** The courses below are designed for beginners "
                    "and will build your skills step by step. Focus on hands-on practice "
                    "alongside these courses."
                )

        # HIGH experience + ANY tech = Ready
        elif profile_pct >= 80:
            conclusion = (
                f"**Readiness Assessment:** You're ready to pursue {tech_prefs}! "
                "Your strong experience provides a solid base for learning new technologies. "
                "**Recommendation:** The courses below match your goals and will help you "
                "specialize quickly. Consider building projects as you learn."
            )

        # Default case
        else:
            conclusion = (
                f"**Readiness Assessment:** You're on the right path to learning {tech_prefs}. "
                "**Recommendation:** The courses below are curated based on your experience level "
                "and learning goals. Start with foundational courses, then progressively tackle "
                "more advanced topics."
            )

    else:
        # No tech preferences specified
        conclusion = (
            "**Recommendation:** Since you haven't specified your technology interests yet, "
            "the courses below cover general fundamentals for the " + role_title + " role. "
            "Once you identify specific technologies you want to learn, we can provide "
            "more targeted recommendations that match your career goals."
        )
    profile_parts.append(conclusion)

    profile_insight = " ".join(profile_parts)

    lines.append(f"• **Profile Alignment:** {profile_pct}%")
    lines.append(f"  {profile_insight}")
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
