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
    """
    lines: list[str] = []
    profile_signals = profile_signals or {}
    missed_topics = missed_topics or []

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

    # Extract user preferences for personalized profile insight
    tech_prefs = profile_signals.get("tech-preferences", "")
    duration_pref = profile_signals.get("content-duration", "any").lower()
    payment_pref = profile_signals.get("payment-preference", "any").lower()

    # Map duration preference to readable text
    duration_text_map = {
        "short": "kursus singkat",
        "medium": "kursus menengah",
        "long": "kursus lengkap/komprehensif",
        "any": "berbagai durasi",
    }
    duration_text = duration_text_map.get(duration_pref, "berbagai durasi")

    # Map payment preference to readable text
    payment_text_map = {
        "free": "gratis",
        "paid": "berbayar (premium)",
        "any": "gratis maupun berbayar",
    }
    payment_text = payment_text_map.get(payment_pref, "gratis maupun berbayar")

    # Build personalized profile insight based on scores and preferences
    if profile_pct >= 80:
        if tech_prefs:
            profile_insight = (
                f"Berdasarkan pengalamanmu yang solid dan skor profil **{profile_pct}%**, "
                f"kamu sudah memiliki fondasi yang kuat untuk role {role_title}. "
                f"Keinginanmu untuk mempelajari **{tech_prefs}** sangat tepat dan efektif "
                f"karena sesuai dengan kompetensimu saat ini. "
                f"Dengan preferensi {duration_text} dan opsi {payment_text}, "
                f"saya merekomendasikan kursus advanced untuk memperdalam keahlianmu."
            )
        else:
            profile_insight = (
                f"Pengalamanmu sangat sesuai dengan kebutuhan {role_title}. "
                f"Skor profil **{profile_pct}%** menunjukkan kesiapan untuk level lanjutan. "
                f"Fokuskan pembelajaran pada spesialisasi yang lebih mendalam."
            )
    elif profile_pct >= 60:
        if tech_prefs:
            profile_insight = (
                f"Berdasarkan hasil profilmu ({profile_pct}%), "
                f"kamu memiliki pengalaman yang cukup namun masih ada ruang untuk berkembang. "
                f"Keinginanmu untuk belajar **{tech_prefs}** cukup efektif. "
                f"Dengan preferensi {duration_text} dan opsi {payment_text}, "
                f"saya merekomendasikan kursus intermediate yang fokus pada praktik hands-on "
                f"untuk memperkuat skill {tech_prefs}."
            )
        else:
            profile_insight = (
                f"Skor profil {profile_pct}% menunjukkan pengalaman yang relevan. "
                f"Fokus pada kursus yang memberikan praktik langsung untuk memperdalam kompetensi."
            )
    else:
        # User has weak foundation - prioritize missed topics first!
        missed_topics_text = ""
        if missed_topics:
            # Format missed topics for display
            if len(missed_topics) == 1:
                missed_topics_text = f"**{missed_topics[0]}**"
            elif len(missed_topics) == 2:
                missed_topics_text = f"**{missed_topics[0]}** dan **{missed_topics[1]}**"
            else:
                missed_topics_text = (
                    f"**{", ".join(missed_topics[:-1])}**, dan **{missed_topics[-1]}**"
                )

        if tech_prefs:
            # Check if tech preference matches role or is realistic for beginner
            is_advanced_topic = any(
                adv in tech_prefs.lower()
                for adv in ["kubernetes", "microservices", "ml", "machine learning", "ai"]
            )

            if missed_topics and is_advanced_topic and theoretical_pct < 60:
                # User wants advanced topic but has weak foundation AND missed topics
                profile_insight = (
                    f"Berdasarkan hasil tesmu (teori: {theoretical_pct}%, profil: {profile_pct}%), "
                    f"kamu masih perlu memperkuat beberapa area dasar untuk role {role_title}. "
                    f"Hasil tesmu menunjukkan kamu perlu memperkuat pemahaman tentang "
                    f"{missed_topics_text} terlebih dahulu. "
                    f"Keinginanmu untuk belajar **{tech_prefs}** sangat baik, namun sebaiknya "
                    f"pelajari dulu {missed_topics_text}, baru kemudian lanjut ke {tech_prefs}. "
                    f"Dengan preferensi {duration_text} ({payment_text}), "
                    f"saya merekomendasikan kursus yang menguatkan fondasi dasarmu."
                )
            elif missed_topics:
                # User has missed topics, recommend fixing those first
                profile_insight = (
                    f"Berdasarkan skor profilmu ({profile_pct}%) dan tes teori "
                    f"({theoretical_pct}%), kamu sedang dalam tahap membangun fondasi "
                    f"sebagai {role_title}. Hasil tesmu menunjukkan kamu perlu "
                    f"memperkuat pemahaman tentang {missed_topics_text}. "
                    f"Keinginanmu untuk belajar **{tech_prefs}** adalah langkah yang baik! "
                    f"Saya merekomendasikan: pertama kuatkan dulu {missed_topics_text}, "
                    f"lalu lanjut ke {tech_prefs}. Dengan preferensi {duration_text} dan opsi "
                    f"{payment_text}, pilih kursus yang membangun fondasi kokoh."
                )
            elif is_advanced_topic and theoretical_pct < 60:
                # User wants advanced topic but has weak foundation (no specific missed topics)
                profile_insight = (
                    f"Berdasarkan hasil tesmu (teori: {theoretical_pct}%, profil: {profile_pct}%), "
                    f"kamu masih dalam tahap membangun fondasi untuk role {role_title}. "
                    f"Keinginanmu untuk belajar **{tech_prefs}** mungkin **kurang efektif** "
                    f"karena memerlukan pemahaman dasar yang kuat terlebih dahulu. "
                    f"Saya merekomendasikan kursus fundamental dulu, lalu bertahap menuju "
                    f"{tech_prefs}. Dengan preferensi {duration_text} ({payment_text}), "
                    f"pilih kursus beginner-friendly."
                )
            else:
                profile_insight = (
                    f"Berdasarkan skor profilmu ({profile_pct}%) dan tes teori "
                    f"({theoretical_pct}%), kamu sedang dalam tahap awal perjalanan "
                    f"sebagai {role_title}. Keinginanmu untuk belajar **{tech_prefs}** "
                    f"adalah langkah yang baik. Dengan preferensi {duration_text} dan opsi "
                    f"{payment_text}, saya merekomendasikan kursus dasar yang memberikan "
                    f"praktik hands-on untuk membangun fondasi yang kuat."
                )
        else:
            # No tech preferences specified
            if missed_topics:
                profile_insight = (
                    f"Skor profil {profile_pct}% menunjukkan kamu masih di awal perjalanan "
                    f"{role_title}. Hasil tesmu menunjukkan kamu perlu memperkuat "
                    f"pemahaman tentang {missed_topics_text}. "
                    f"Mulailah dengan kursus yang membahas topik tersebut, "
                    f"lalu bangun portfolio dengan proyek nyata untuk memperkuat pengalaman."
                )
            else:
                profile_insight = (
                    f"Skor profil {profile_pct}% menunjukkan kamu masih di awal perjalanan "
                    f"{role_title}. Mulailah dengan kursus foundational yang memberikan praktik "
                    f"langsung. Bangun portfolio dengan proyek nyata untuk memperkuat pengalaman."
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

    # Personalization preferences section
    tech_prefs = profile_signals.get("tech-preferences", "")
    duration_pref = profile_signals.get("content-duration", "any").lower()
    payment_pref = profile_signals.get("payment-preference", "any").lower()

    has_preferences = tech_prefs or duration_pref != "any" or payment_pref != "any"
    if has_preferences:
        lines.append("**Personalisasi Rekomendasi**")
        lines.append("")
        lines.append("Berdasarkan preferensi yang Anda pilih:")

        if tech_prefs:
            lines.append(f"• **Topik yang ingin dipelajari:** {tech_prefs}")

        if duration_pref != "any":
            duration_text = {
                "short": "Kursus singkat (< 2 jam)",
                "medium": "Kursus menengah (2-10 jam)",
                "long": "Kursus lengkap (> 10 jam)",
            }.get(duration_pref, duration_pref)
            lines.append(f"• **Durasi konten:** {duration_text}")

        if payment_pref != "any":
            payment_text = "Gratis" if payment_pref == "free" else "Berbayar"
            lines.append(f"• **Preferensi pembayaran:** {payment_text}")

        lines.append("")
        lines.append(
            "Rekomendasi kursus di bawah telah diprioritaskan berdasarkan preferensi Anda."
        )
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
                lines.append(f"   • Alasan rekomendasi: {rec.match_reason}")

            # Add personalization match info
            metadata = rec.course_metadata or {}
            personalization_matches = []

            # Check tech preference match
            if tech_prefs:
                course_title_lower = rec.course_title.lower()
                tech_keywords = [t.strip().lower() for t in tech_prefs.replace(",", " ").split()]
                matched_techs = [t for t in tech_keywords if t in course_title_lower]
                if matched_techs:
                    personalization_matches.append("Sesuai minat: " + ", ".join(matched_techs))

            # Check duration match
            level = metadata.get("level", "").lower()
            if duration_pref == "short" and "beginner" in level:
                personalization_matches.append("Cocok untuk pemula (durasi singkat)")
            elif duration_pref == "medium" and "intermediate" in level:
                personalization_matches.append("Level menengah sesuai preferensi")
            elif duration_pref == "long" and ("advanced" in level or "all levels" in level):
                personalization_matches.append("Konten lengkap/advanced sesuai preferensi")

            # Check payment match
            is_paid = str(metadata.get("is_paid", "True")).lower() == "true"
            if payment_pref == "free" and not is_paid:
                personalization_matches.append("Gratis sesuai preferensi")
            elif payment_pref == "paid" and is_paid:
                personalization_matches.append("Kursus premium sesuai preferensi")

            if personalization_matches:
                lines.append("   • Kecocokan preferensi: " + "; ".join(personalization_matches))

            # Add course metadata for better understanding
            if level:
                lines.append(f"   • Tingkat kesulitan: {level.title()}")

            # Add relevance with interpretation
            rel_score = rec.relevance_score
            if rel_score >= 0.8:
                rel_text = f"{rel_score:.2f}/1.0 (Sangat Relevan)"
            elif rel_score >= 0.6:
                rel_text = f"{rel_score:.2f}/1.0 (Relevan)"
            else:
                rel_text = f"{rel_score:.2f}/1.0 (Cukup Relevan)"
            lines.append(f"   • Skor kecocokan: {rel_text}")

            lines.append("")

    if degraded:
        lines.append("")
        lines.append(
            "_Note: Some recommendations may be limited due to temporary service constraints._"
        )

    return "\n".join(lines)
