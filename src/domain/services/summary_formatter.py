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
    name_greeting = f"**Halo, {user_name}!** " if user_name else ""

    # Opening headline based on score with personalization
    if overall_pct >= 80:
        headline = (
            f"{name_greeting}**Excellent work!** Kamu menunjukkan kemampuan yang kuat "
            f"untuk role {role_title} dengan skor keseluruhan **{overall_pct}%**."
        )
        if tech_prefs:
            headline += f" Minatmu untuk mempelajari **{tech_prefs}** sangat tepat untuk tahap ini."
    elif overall_pct >= 60:
        headline = (
            f"{name_greeting}**Good job!** Penilaianmu untuk role {role_title} menunjukkan "
            f"fondasi yang solid. Skor keseluruhan: **{overall_pct}%**."
        )
        if tech_prefs:
            headline += f" Fokusmu pada **{tech_prefs}** akan membantu meningkatkan skillmu."
    else:
        headline = (
            f"{name_greeting}**Terima kasih telah menyelesaikan assessment {role_title}.** "
            f"Skor keseluruhan: **{overall_pct}%**."
        )
        if tech_prefs:
            headline += f" Keinginanmu untuk belajar **{tech_prefs}** adalah langkah yang baik!"

    lines.append(headline)
    lines.append("")

    # Detailed score breakdown with insights
    lines.append("**Score Breakdown & Insights**")
    lines.append("")

    # Technical Knowledge analysis with actionable recommendations (now personalized)
    if theoretical_pct >= 80:
        if tech_prefs:
            tech_insight = (
                f"Pemahaman teorimu sangat baik! Kamu siap untuk masalah dunia nyata. "
                f"Dengan minatmu di **{tech_prefs}**, fokuskan pada kursus advanced "
                f"yang memperdalam keahlian tersebut."
            )
        else:
            tech_insight = (
                "Pemahaman teorimu sangat baik! Kamu siap untuk masalah dunia nyata. "
                "Pertimbangkan kursus advanced untuk memperdalam keahlian di area spesialisasi."
            )
    elif theoretical_pct >= 60:
        if tech_prefs:
            tech_insight = (
                f"Fondasi teorimu cukup solid. Untuk meningkatkan skill di **{tech_prefs}**, "
                f"fokuskan pada area yang skormu lebih rendah dan praktikkan lewat "
                f"proyek hands-on. Kursus di bawah menargetkan gap pengetahuanmu."
            )
        else:
            tech_insight = (
                "Fondasi teorimu cukup solid. Untuk meningkatkan lebih lanjut, "
                "fokuskan pada area yang skormu lebih rendah dan praktikkan lewat proyek "
                "hands-on. Kursus di bawah menargetkan gap pengetahuanmu."
            )
    else:
        if tech_prefs:
            tech_insight = (
                f"Fondasi teorimu perlu diperkuat. Meskipun kamu ingin belajar "
                f"**{tech_prefs}**, mulailah dengan kursus fundamental yang mencakup "
                f"dasar-dasar, lalu bangun dengan latihan praktis. Jangan terburu-buru - "
                f"menguasai dasar adalah kunci kesuksesan jangka panjang."
            )
        else:
            tech_insight = (
                "Fondasi teorimu perlu diperkuat. Mulailah dengan kursus beginner-friendly "
                "yang mencakup fundamental, lalu bangun dengan latihan praktis. "
                "Jangan terburu-buru - menguasai dasar adalah kunci kesuksesan jangka panjang."
            )
    lines.append(f"• **Technical Knowledge:** {theoretical_pct}%")
    lines.append(f"  {tech_insight}")
    lines.append("")

    # Extract user preferences for personalized profile insight (tech_prefs already extracted above)
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
                joined = ", ".join(missed_topics[:-1])
                missed_topics_text = f"**{joined}**, dan **{missed_topics[-1]}**"

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

    # Essay quality analysis (if applicable) with detailed feedback - now more personal
    if has_essay:
        if essay_pct >= 80:
            essay_insight = (
                "Kemampuan komunikasi dan problem-solving yang sangat baik! "
                "Jawabanmu menunjukkan artikulasi konsep teknis yang jelas, penalaran logis, "
                "dan kemampuan menjelaskan ide kompleks secara efektif. Ini skill berharga "
                "untuk kolaborasi dan peran technical leadership."
            )
        elif essay_pct >= 60:
            essay_insight = (
                "Penjelasanmu cukup baik dengan pemahaman yang jelas. "
                "Untuk meningkatkan, pertimbangkan menambahkan contoh lebih spesifik, "
                "detail teknis lebih dalam, dan penjelasan yang lebih terstruktur. "
                "Praktik menulis dokumentasi teknis dapat membantu meningkatkan skill ini."
            )
        else:
            essay_insight = (
                "Perlu meningkatkan kemampuan mengartikulasikan konsep teknis. "
                "Fokuskan pada mengorganisir pikiranmu secara logis, memberikan contoh "
                "spesifik, dan menjelaskan 'mengapa' di balik keputusan teknis. "
                "Membaca blog teknis dan dokumentasi dapat membantu meningkatkan skill ini."
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
        lines.append("Berdasarkan preferensi yang kamu pilih:")

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
        lines.append("Rekomendasi kursus di bawah telah diprioritaskan berdasarkan preferensimu.")
        lines.append("")

    # Personalized learning path recommendations
    recs = list(recommendations)
    if recs:
        lines.append("")
        lines.append("**Learning Path yang Dipersonalisasi**")
        lines.append("")

        # Add personalized intro based on overall performance and tech preferences
        if overall_pct >= 80:
            if tech_prefs:
                path_intro = (
                    f"Berdasarkan performa kuat dan minatmu di **{tech_prefs}**, "
                    f"kursus advanced ini akan membantumu mencapai level expert di {role_title}:"
                )
            else:
                path_intro = (
                    f"Berdasarkan performa kuat, kursus advanced ini akan membantumu "
                    f"spesialisasi dan mencapai level expert di {role_title}:"
                )
        elif overall_pct >= 60:
            if tech_prefs:
                path_intro = (
                    f"Untuk berkembang dari level intermediate-mu dan menguasai **{tech_prefs}**, "
                    f"kursus ini menargetkan area pertumbuhanmu:"
                )
            else:
                path_intro = (
                    "Untuk berkembang dari level intermediate-mu, kursus ini menargetkan "
                    "area pertumbuhanmu dan membangun di atas kekuatan yang ada:"
                )
        else:
            if tech_prefs:
                path_intro = (
                    f"Untuk membangun fondasi kuat menuju **{tech_prefs}**, mulailah dengan "
                    f"kursus ini yang sesuai dengan level-mu dan bertahap mengembangkan skillmu:"
                )
            else:
                path_intro = (
                    "Untuk membangun fondasi kuat, mulailah dengan kursus ini yang sesuai "
                    "dengan level-mu dan secara bertahap mengembangkan skillmu:"
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
