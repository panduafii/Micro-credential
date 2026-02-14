"""
RAG Service for Story 3.1: Role-Aware RAG Retrieval.

Uses TF-IDF based retrieval from Udemy courses dataset as a simple RAG implementation.
Can be upgraded to Chroma/PGVector for production.
"""

from __future__ import annotations

import ast
import csv
import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import select
from src.infrastructure.db.models import (
    Assessment,
    AssessmentQuestionSnapshot,
    AssessmentResponse,
    AsyncJob,
    JobStatus,
    JobType,
    QuestionType,
    Recommendation,
    RecommendationItem,
    Score,
)
from src.infrastructure.repositories.course_enrichment import (
    CourseEnricher,
    EnrichedCourseMetadata,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

# Path to courses dataset
COURSES_CSV_PATH = (
    Path(__file__).parent.parent.parent / "infrastructure/repositories/udemy_courses.csv"
)

# Role to subject/keyword mappings for better retrieval
ROLE_KEYWORDS: dict[str, list[str]] = {
    "backend-engineer": [
        "python",
        "java",
        "node",
        "api",
        "database",
        "sql",
        "backend",
        "server",
        "microservices",
        "django",
        "flask",
        "spring",
        "aws",
    ],
    "frontend-engineer": [
        "javascript",
        "react",
        "vue",
        "angular",
        "css",
        "html",
        "frontend",
        "web development",
        "typescript",
        "ui",
        "ux",
    ],
    "data-scientist": [
        "python",
        "machine learning",
        "data science",
        "statistics",
        "pandas",
        "numpy",
        "tensorflow",
        "deep learning",
        "ai",
        "analytics",
    ],
    "data-analyst": [
        "sql",
        "excel",
        "power bi",
        "tableau",
        "data analysis",
        "data analytics",
        "statistics",
        "python",
        "pandas",
        "visualization",
        "dashboard",
        "business intelligence",
    ],
    "devops-engineer": [
        "docker",
        "kubernetes",
        "aws",
        "azure",
        "devops",
        "ci/cd",
        "jenkins",
        "terraform",
        "ansible",
        "linux",
        "cloud",
    ],
    "product-manager": [
        "product management",
        "agile",
        "scrum",
        "business",
        "strategy",
        "roadmap",
        "user research",
        "analytics",
    ],
}

ROLE_FOUNDATION_KEYWORDS: dict[str, list[str]] = {
    "backend-engineer": [
        "programming fundamentals",
        "python",
        "api",
        "rest",
        "database",
        "sql",
        "backend basics",
    ],
    "data-analyst": [
        "data analysis fundamentals",
        "sql",
        "excel",
        "statistics",
        "data visualization",
        "dashboard",
    ],
}

ROLE_SUBJECTS: dict[str, list[str]] = {
    "backend-engineer": ["Web Development"],
    "frontend-engineer": ["Web Development"],
    "devops-engineer": ["Web Development"],
    "data-analyst": ["Business Finance", "Web Development"],
    "data-scientist": ["Business Finance", "Web Development"],
    "product-manager": ["Business Finance"],
}

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "api": ["api", "rest", "graphql"],
    "database": ["database", "sql", "postgres", "mysql"],
    "performance": ["cache", "caching", "performance"],
    "testing": ["test", "testing", "pytest", "unit"],
    "backend": ["backend", "server", "node", "python", "go", "java"],
    "cloud": ["aws", "gcp", "azure", "cloud", "docker", "kubernetes"],
    "data": ["data", "analytics", "statistics", "sql"],
    "visualization": ["visualization", "dashboard", "tableau", "powerbi", "power"],
}

STOPWORDS = {
    "and",
    "the",
    "for",
    "with",
    "to",
    "of",
    "in",
    "a",
    "on",
    "an",
    "your",
    "how",
    "what",
    "why",
    "is",
    "are",
    "this",
    "that",
}

# Technologies that usually require stronger fundamentals before advanced tracks.
ADVANCED_TECH_KEYWORDS = {
    "kubernetes",
    "microservices",
    "terraform",
    "aws",
    "azure",
    "gcp",
    "cloud",
    "devops",
    "kafka",
    "graphql",
    "machine learning",
    "deep learning",
}


@dataclass
class CourseMatch:
    """A matched course from RAG retrieval."""

    course_id: str
    title: str
    url: str | None
    relevance_score: float
    match_reason: str
    metadata: dict


@dataclass
class RAGResult:
    """Result from RAG retrieval."""

    query: str
    matches: list[CourseMatch]
    degraded: bool = False
    error: str | None = None
    readiness: dict | None = None


class RAGRetrievalError(Exception):
    """Raised when RAG retrieval fails."""


class RAGService:
    """Service for RAG-based credential recommendations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._courses: list[dict] | None = None
        self._enriched_courses: dict[str, EnrichedCourseMetadata] = {}  # Cache enriched metadata

    def _load_courses(self) -> list[dict]:
        """Load courses from CSV file and enrich with comprehensive metadata."""
        if self._courses is not None:
            return self._courses

        courses = []
        try:
            with open(COURSES_CSV_PATH, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Legacy annotation for backward compatibility
                    self._annotate_course(row)

                    # NEW: Enrich course with comprehensive metadata
                    enriched = CourseEnricher.enrich_course(row)
                    self._enriched_courses[enriched.course_id] = enriched

                    # Store enriched metadata in course dict for easy access
                    row["_enriched"] = enriched

                    courses.append(row)
            self._courses = courses

            logger.info(
                "courses_loaded_and_enriched",
                total_courses=len(courses),
                enriched_count=len(self._enriched_courses),
            )
        except FileNotFoundError:
            logger.warning("courses_file_not_found", path=str(COURSES_CSV_PATH))
            self._courses = []

        return self._courses

    def _annotate_course(self, course: dict) -> None:
        """Annotate course with computed features for CBF matching.

        Uses all available data fields:
        - course_title: Primary text for keyword matching
        - subject: Category classification
        - level: Difficulty level (Beginner/Intermediate/Expert/All Levels)
        - content_duration: Course length in hours
        - num_lectures: Number of lecture videos
        - num_subscribers: Popularity metric
        - num_reviews: Quality/engagement metric
        - price: Free vs paid
        - published_timestamp: Course freshness
        """
        title = course.get("course_title", "")
        subject = course.get("subject", "")
        level = course.get("level", "")

        # Combine title + subject + level for richer text representation
        text = f"{title} {subject} {level}".lower()

        # Extract topic tags from text
        tags = self._extract_topic_tags(text)

        # Tokenize for embedding
        tokens = self._tokenize(text)

        # Store computed features
        course["_tags"] = tags
        course["_vector"] = self._hash_embedding(tokens)
        course["_text"] = text  # Store combined text for matching

        # Pre-compute numeric features for scoring
        course["_quality_score"] = self._compute_quality_score(course)
        course["_freshness_score"] = self._compute_freshness_score(course)
        course["_depth_score"] = self._compute_depth_score(course)

    def _compute_quality_score(self, course: dict) -> float:
        """Compute quality score from reviews and subscribers.

        Combines:
        - num_reviews: Direct engagement metric
        - num_subscribers: Popularity metric
        - Review-to-subscriber ratio: Quality indicator
        """
        try:
            subscribers = int(course.get("num_subscribers", 0) or 0)
            reviews = int(course.get("num_reviews", 0) or 0)

            # Popularity component (normalized to 0-0.4)
            popularity = min(0.4, subscribers / 50000)

            # Review count component (normalized to 0-0.3)
            review_score = min(0.3, reviews / 2000)

            # Review-to-subscriber ratio (indicates engagement quality)
            # Higher ratio = more engaged students
            if subscribers > 0:
                engagement_ratio = reviews / subscribers
                engagement_score = min(0.3, engagement_ratio * 3)
            else:
                engagement_score = 0

            return popularity + review_score + engagement_score
        except (ValueError, TypeError):
            return 0.0

    def _compute_freshness_score(self, course: dict) -> float:
        """Compute freshness score from published timestamp.

        Newer courses get higher scores (tech content gets outdated).
        """
        try:
            from datetime import UTC, datetime

            timestamp_str = course.get("published_timestamp", "")
            if not timestamp_str:
                return 0.0

            # Parse ISO format: 2017-01-18T20:58:58Z
            published = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            now = datetime.now(UTC)

            # Calculate age in years
            age_days = (now - published).days
            age_years = age_days / 365

            # Score: newer = higher, max 0.2
            # Courses < 1 year: 0.2
            # Courses 1-3 years: 0.15
            # Courses 3-5 years: 0.1
            # Courses > 5 years: 0.05
            if age_years < 1:
                return 0.2
            elif age_years < 3:
                return 0.15
            elif age_years < 5:
                return 0.1
            else:
                return 0.05
        except Exception:
            return 0.1  # Default middle score

    def _compute_depth_score(self, course: dict) -> float:
        """Compute depth score from content_duration and num_lectures.

        Indicates how comprehensive the course is.
        """
        try:
            duration = float(course.get("content_duration", 0) or 0)
            lectures = int(course.get("num_lectures", 0) or 0)

            # Duration component (normalized to 0-0.15)
            # Longer courses = more comprehensive
            duration_score = min(0.15, duration / 50)

            # Lecture count component (normalized to 0-0.1)
            lecture_score = min(0.1, lectures / 200)

            # Average lecture length indicator
            # Good courses have balanced lecture lengths (5-15 min each)
            if lectures > 0 and duration > 0:
                avg_lecture_mins = (duration * 60) / lectures
                if 5 <= avg_lecture_mins <= 15:
                    balance_score = 0.05  # Well-structured
                else:
                    balance_score = 0.02
            else:
                balance_score = 0

            return duration_score + lecture_score + balance_score
        except (ValueError, TypeError):
            return 0.0

    def _tokenize(self, text: str) -> list[str]:
        clean = re.sub(r"[^a-z0-9]+", " ", text.lower())
        return [t for t in clean.split() if len(t) > 2 and t not in STOPWORDS]

    def _extract_topic_tags(self, text: str) -> list[str]:
        """Extract topic tags using whole-word matching."""
        tags = []
        for topic, keywords in TOPIC_KEYWORDS.items():
            # Use whole-word matching to avoid false positives
            # e.g., 'api' should not match 'Instagram'
            if any(self._word_match(keyword, text) for keyword in keywords):
                tags.append(topic)
        return tags

    def _hash_embedding(self, tokens: list[str], dim: int = 128) -> list[float]:
        vec = [0.0] * dim
        for token in tokens:
            idx = hash(token) % dim
            vec[idx] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        if not a or not b:
            return 0.0
        return sum(x * y for x, y in zip(a, b, strict=False))

    def _parse_tech_preferences(self, tech_prefs: object | None) -> list[str]:
        if not tech_prefs:
            return []

        if isinstance(tech_prefs, list):
            items = [str(item).strip() for item in tech_prefs if str(item).strip()]
        else:
            text = str(tech_prefs).strip()
            if not text:
                return []

            if text.startswith("[") and text.endswith("]"):
                try:
                    parsed = ast.literal_eval(text)
                except (ValueError, SyntaxError):
                    parsed = text
                if isinstance(parsed, list):
                    items = [str(item).strip() for item in parsed if str(item).strip()]
                else:
                    items = [str(parsed).strip()]
            else:
                normalized = text.replace("\n", ",")
                for sep in [";", "|", "/"]:
                    normalized = normalized.replace(sep, ",")
                if "," in normalized:
                    items = [t.strip() for t in normalized.split(",") if t.strip()]
                elif " and " in normalized:
                    items = [t.strip() for t in normalized.split(" and ") if t.strip()]
                elif " & " in normalized:
                    items = [t.strip() for t in normalized.split(" & ") if t.strip()]
                else:
                    items = [normalized]

        return [item.lower() for item in items if item]

    def _has_advanced_learning_target(self, tech_keywords: list[str]) -> bool:
        """Detect whether user target includes advanced technology domains."""
        if not tech_keywords:
            return False

        combined = " ".join(tech_keywords).lower()
        return any(keyword in combined for keyword in ADVANCED_TECH_KEYWORDS)

    def _build_readiness_policy(
        self,
        role_slug: str,
        profile_signals: dict | None,
        score_metrics: dict[str, float | bool],
    ) -> dict[str, object]:
        """Build KKM/readiness policy for gating recommendation difficulty."""
        tech_prefs = self._parse_tech_preferences((profile_signals or {}).get("tech-preferences"))
        targeting_advanced = self._has_advanced_learning_target(tech_prefs)

        overall_pct = float(score_metrics.get("overall_pct", 0.0) or 0.0)
        theoretical_pct = float(score_metrics.get("theoretical_pct", 0.0) or 0.0)
        profile_pct = float(score_metrics.get("profile_pct", 0.0) or 0.0)
        essay_pct = float(score_metrics.get("essay_pct", 0.0) or 0.0)
        has_essay_scores = bool(score_metrics.get("has_essay_scores", False))

        # Readiness tier from observed competence, not from user preference.
        if (
            overall_pct < 55
            or theoretical_pct < 60
            or (has_essay_scores and essay_pct < 55)
            or profile_pct < 35
        ):
            readiness_tier = "foundation"
        elif overall_pct < 75 or theoretical_pct < 72 or (has_essay_scores and essay_pct < 65):
            readiness_tier = "intermediate"
        else:
            readiness_tier = "advanced"

        # KKM for moving into advanced track.
        advanced_kkm = 70.0
        advanced_eligible = (
            overall_pct >= advanced_kkm
            and theoretical_pct >= 65
            and (not has_essay_scores or essay_pct >= 60)
            and profile_pct >= 45
        )

        force_foundation = targeting_advanced and not advanced_eligible
        if force_foundation:
            difficulty_pref = "beginner"
            reason = (
                "Target teknologi bersifat advanced, tetapi skor belum memenuhi KKM. "
                "Rekomendasi diarahkan ke fundamental terlebih dahulu."
            )
        elif readiness_tier == "foundation":
            difficulty_pref = "beginner"
            reason = "Skor dasar belum stabil, fokus ke fundamental."
        elif readiness_tier == "intermediate":
            difficulty_pref = "intermediate"  # Matcher still allows beginner.
            reason = "Skor cukup untuk jalur menengah dengan penguatan fundamental."
        else:
            difficulty_pref = None
            reason = "Skor tinggi, boleh mengejar jalur advanced."

        return {
            "role_slug": role_slug,
            "readiness_tier": readiness_tier,
            "difficulty_pref": difficulty_pref,
            "targeting_advanced": targeting_advanced,
            "advanced_eligible": advanced_eligible,
            "force_foundation": force_foundation,
            "advanced_kkm": advanced_kkm,
            "overall_pct": round(overall_pct, 1),
            "theoretical_pct": round(theoretical_pct, 1),
            "profile_pct": round(profile_pct, 1),
            "essay_pct": round(essay_pct, 1),
            "has_essay_scores": has_essay_scores,
            "reason": reason,
        }

    def _get_role_fallback_keywords(self, role_slug: str) -> list[str]:
        """Get role-safe keywords used when user tech preferences are missing/relaxed."""
        foundation = ROLE_FOUNDATION_KEYWORDS.get(role_slug, [])
        role_keywords = ROLE_KEYWORDS.get(role_slug, [])

        # Keep role keywords focused on fundamentals for fallback retrieval.
        role_safe = [kw for kw in role_keywords if kw.lower() not in ADVANCED_TECH_KEYWORDS]

        merged: list[str] = []
        seen: set[str] = set()
        for keyword in [*foundation, *role_safe]:
            normalized = keyword.strip().lower()
            if not normalized or normalized in seen:
                continue
            merged.append(keyword)
            seen.add(normalized)
        return merged[:10]

    def _is_role_subject_match(self, role_slug: str, subject: str) -> bool:
        """Validate course subject is within role scope."""
        allowed = ROLE_SUBJECTS.get(role_slug)
        if not allowed:
            return True
        subject_clean = (subject or "").strip().lower()
        return any(subject_clean == option.lower() for option in allowed)

    def _build_query(
        self,
        role_slug: str,
        profile_signals: dict | None = None,
        essay_keywords: list[str] | None = None,
        missed_topics: list[str] | None = None,
        foundation_first: bool = False,
    ) -> str:
        """Build RAG query from role context and signals.

        Priority order (highest first):
        1. User's tech preferences (what they explicitly want to learn)
        2. Missed topics from assessment (areas needing improvement)
        3. Essay keywords (topics user discussed)
        4. Role keywords (general role-related terms)
        """
        query_parts = []

        if foundation_first:
            foundation_keywords = ROLE_FOUNDATION_KEYWORDS.get(role_slug) or ROLE_KEYWORDS.get(
                role_slug, []
            )
            if foundation_keywords:
                query_parts.extend(foundation_keywords[:6])
                query_parts.extend(foundation_keywords[:3])  # Boost foundation topics

        # PRIORITY 1: User tech preferences first (most important)
        # User explicitly stated what they want to learn
        if profile_signals:
            tech_prefs = profile_signals.get("tech-preferences")
            pref_keywords = self._parse_tech_preferences(tech_prefs)
            if pref_keywords:
                if foundation_first:
                    # Keep user intent, but avoid over-dominating fundamental path.
                    query_parts.extend(pref_keywords[:3])
                else:
                    # Add tech preferences multiple times for higher weight.
                    query_parts.extend(pref_keywords[:5])
                    query_parts.extend(pref_keywords[:3])  # Repeat for boost

        # PRIORITY 2: Missed topics (areas user needs to improve)
        if missed_topics:
            query_parts.extend(missed_topics[:5])

        # PRIORITY 3: Essay keywords
        if essay_keywords:
            query_parts.extend(essay_keywords[:3])

        # PRIORITY 4: Role keywords (general context, lower priority)
        role_keywords = ROLE_KEYWORDS.get(role_slug, [])
        if role_keywords:
            # Only add role keywords if no strong user preference
            if not profile_signals or not profile_signals.get("tech-preferences"):
                query_parts.extend(role_keywords[:5])
            else:
                # Add fewer role keywords when user has preferences
                query_parts.extend(role_keywords[:2])

        return " ".join(query_parts)

    def _word_match(self, term: str, text: str) -> bool:
        """Check if term matches as whole word in text (not substring).

        Examples:
        - 'rest' in 'REST API' -> True
        - 'rest' in 'Pinterest' -> False
        - 'ruby' in 'Ruby on Rails' -> True
        """
        import re

        pattern = r"\b" + re.escape(term.lower()) + r"\b"
        return bool(re.search(pattern, text.lower()))

    def _calculate_relevance(self, course: dict, query_terms: list[str]) -> float:
        """Calculate relevance score using all available course data.

        Combines:
        - Keyword matching (title + subject + level)
        - Pre-computed quality score (subscribers + reviews + engagement)
        - Pre-computed freshness score (publication date)
        - Pre-computed depth score (duration + lectures)
        """
        # Use pre-computed combined text for matching
        text = course.get("_text", "")
        if not text:
            title = course.get("course_title", "").lower()
            subject = course.get("subject", "").lower()
            text = f"{title} {subject}"

        # Count keyword matches (whole-word)
        matches = 0
        for term in query_terms:
            if self._word_match(term, text):
                matches += 1

        if not query_terms:
            return 0.0

        # Base score from keyword matches (40% weight)
        keyword_score = (matches / len(query_terms)) * 0.4

        # Use pre-computed feature scores
        quality_score = course.get("_quality_score", 0) * 0.3  # 30% weight
        freshness_score = course.get("_freshness_score", 0) * 0.15  # 15% weight
        depth_score = course.get("_depth_score", 0) * 0.15  # 15% weight

        # Fallback to legacy calculation if pre-computed not available
        if quality_score == 0:
            try:
                subscribers = int(course.get("num_subscribers", 0))
                reviews = int(course.get("num_reviews", 0))
                quality_score = min(0.3, (subscribers / 100000 + reviews / 5000) * 0.15)
            except (ValueError, TypeError):
                quality_score = 0

        return min(1.0, keyword_score + quality_score + freshness_score + depth_score)

    def _retrieve_courses(
        self,
        query: str,
        role_slug: str,
        top_k: int = 5,
        missed_topics: list[str] | None = None,
        profile_signals: dict | None = None,
        readiness_policy: dict[str, object] | None = None,
    ) -> list[CourseMatch]:
        """Retrieve top-K courses matching the query.

        Strategy:
        1. First try with all filters (payment preference, etc.)
        2. If not enough results, relax payment filter but keep relevance requirement
        3. Only return courses that match tech preferences OR role keywords
        4. Apply readiness/KKM difficulty gate to avoid over-shoot recommendations
        """
        courses = self._load_courses()
        if not courses:
            return []

        query_terms = [t.strip() for t in query.split() if len(t.strip()) > 2]
        if not query_terms:
            return []

        query_vec = self._hash_embedding(self._tokenize(query))
        missed_topics = missed_topics or []
        profile_signals = profile_signals or {}

        # Extract preferences from profile
        payment_pref = profile_signals.get("payment-preference", "any")
        if isinstance(payment_pref, list):
            payment_pref = payment_pref[0] if payment_pref else "any"
        payment_pref = str(payment_pref).lower()

        duration_pref = profile_signals.get("content-duration", "any")
        if isinstance(duration_pref, list):
            duration_pref = duration_pref[0] if duration_pref else "any"
        duration_pref = str(duration_pref).lower()

        difficulty_pref = (
            str(readiness_policy.get("difficulty_pref"))
            if readiness_policy and readiness_policy.get("difficulty_pref")
            else None
        )
        readiness_reason = (
            str(readiness_policy.get("reason"))
            if readiness_policy and readiness_policy.get("reason")
            else None
        )

        # Parse tech preferences into keywords for exact matching.
        raw_tech_pref_keywords = self._parse_tech_preferences(
            profile_signals.get("tech-preferences")
        )
        if raw_tech_pref_keywords:
            tech_pref_keywords = raw_tech_pref_keywords
            min_keyword_score = 0.0
        else:
            # Guardrail: avoid broad/generic matches by using role-scoped fallback terms.
            tech_pref_keywords = self._get_role_fallback_keywords(role_slug)
            min_keyword_score = 0.05

        def _merge_unique(base: list[CourseMatch], extra: list[CourseMatch]) -> list[CourseMatch]:
            if not extra:
                return base
            merged = list(base)
            seen = {item.course_id for item in merged}
            for candidate in extra:
                if candidate.course_id in seen:
                    continue
                merged.append(candidate)
                seen.add(candidate.course_id)
                if len(merged) >= top_k:
                    break
            return merged

        # First pass: with payment filter
        matches = self._score_and_filter_courses(
            courses,
            role_slug,
            query_terms,
            query_vec,
            missed_topics,
            tech_pref_keywords,
            payment_pref,
            duration_pref,
            top_k,
            difficulty_pref=difficulty_pref,
            readiness_note=readiness_reason,
            min_keyword_score=min_keyword_score,
            strict_payment=True,
        )

        # If not enough relevant results, try without strict payment filter
        if len(matches) < top_k and payment_pref != "any":
            relaxed_payment_matches = self._score_and_filter_courses(
                courses,
                role_slug,
                query_terms,
                query_vec,
                missed_topics,
                tech_pref_keywords,
                payment_pref,
                duration_pref,
                top_k,
                difficulty_pref=difficulty_pref,
                readiness_note=readiness_reason,
                min_keyword_score=min_keyword_score,
                strict_payment=False,
            )
            matches = _merge_unique(matches, relaxed_payment_matches)

        # If forced to foundation and still sparse, relax tech-match to avoid empty output.
        if (
            len(matches) < top_k
            and readiness_policy
            and bool(readiness_policy.get("force_foundation"))
        ):
            foundation_fill = self._score_and_filter_courses(
                courses,
                role_slug,
                query_terms,
                query_vec,
                missed_topics,
                self._get_role_fallback_keywords(role_slug),
                "any",
                duration_pref,
                top_k,
                difficulty_pref="beginner",
                readiness_note=readiness_reason,
                min_keyword_score=0.05,
                strict_payment=False,
            )
            matches = _merge_unique(matches, foundation_fill)

        return matches

    def _score_and_filter_courses(
        self,
        courses: list[dict],
        role_slug: str,
        query_terms: list[str],
        query_vec: list[float],
        missed_topics: list[str],
        tech_pref_keywords: list[str],
        payment_pref: str,
        duration_pref: str,
        top_k: int,
        difficulty_pref: str | None = None,
        readiness_note: str | None = None,
        min_keyword_score: float = 0.0,
        strict_payment: bool = True,
    ) -> list[CourseMatch]:
        """Score and filter courses using enriched metadata for better matching."""
        scored_courses = []

        for course in courses:
            # Get enriched metadata
            enriched = course.get("_enriched")
            if not enriched:
                # Fallback to legacy method if enrichment failed
                continue

            if not self._is_role_subject_match(role_slug, enriched.subject):
                continue

            # Use enriched metadata for precise filtering
            matches, match_score = CourseEnricher.match_user_preferences(
                enriched_course=enriched,
                user_tech_prefs=tech_pref_keywords,
                payment_pref=payment_pref if strict_payment else "any",
                duration_pref=duration_pref,
                difficulty_pref=difficulty_pref,
            )

            if not matches:
                continue  # Course doesn't match user preferences

            # Legacy scoring for backward compatibility
            keyword_score = self._calculate_relevance(course, query_terms)
            embedding_score = self._cosine_similarity(query_vec, course.get("_vector", []))

            # Guardrail for low-signal fallback paths to prevent irrelevant recommendations.
            if keyword_score < min_keyword_score:
                continue

            # Boost for missed topics
            tag_boost = 0.0
            if missed_topics and any(tag in enriched.tech_tags for tag in missed_topics):
                tag_boost = 0.15

            # Build match reason
            reason_parts = []
            if enriched.tech_tags:
                pref_normalized = {CourseEnricher.normalize_term(tag) for tag in tech_pref_keywords}
                matched_tags = [
                    tag
                    for tag in enriched.tech_tags
                    if CourseEnricher.normalize_term(tag) in pref_normalized
                ]
                if matched_tags:
                    matched_display = ", ".join(matched_tags[:3])
                    reason_parts.append(f"Matches your interest in: {matched_display}")
                else:
                    covered_display = ", ".join(enriched.tech_tags[:3])
                    reason_parts.append(f"Covers: {covered_display}")

            if readiness_note:
                reason_parts.append("Readiness gate applied")

            if enriched.difficulty:
                reason_parts.append(f"{enriched.difficulty.capitalize()} level")

            if enriched.is_free:
                reason_parts.append("Free course")

            reason_parts.append(f"{enriched.duration_hours:.1f}h duration")

            if enriched.num_subscribers > 10000:
                reason_parts.append(f"{enriched.num_subscribers:,} students")

            match_reason = " • ".join(reason_parts)

            # Combine all scores
            # Priority: enriched match score > keyword/embedding > quality
            final_score = (
                match_score * 0.5  # 50% from enriched metadata matching
                + keyword_score * 0.2  # 20% from keyword relevance
                + embedding_score * 0.1  # 10% from embedding similarity
                + tag_boost  # Boost for missed topics
                + enriched.quality_score * 0.2  # 20% from quality
            )

            scored_courses.append((final_score, course, match_reason))

        # Sort by score descending
        scored_courses.sort(key=lambda x: x[0], reverse=True)

        # Return top K
        return [
            CourseMatch(
                course_id=course.get("course_id", ""),
                title=course.get("course_title", ""),
                url=course.get("url"),
                relevance_score=round(score, 3),
                match_reason=reason,
                metadata={
                    "subject": course.get("subject", ""),
                    "level": course.get("level", ""),
                    "duration_hours": float(course.get("content_duration", 0) or 0),
                    "is_paid": course.get("is_paid", False),
                    "price": float(course.get("price", 0) or 0),
                    "subscribers": int(course.get("num_subscribers", 0) or 0),
                    "enriched_tags": course.get("_enriched").tech_tags
                    if course.get("_enriched")
                    else [],
                },
            )
            for score, course, reason in scored_courses[:top_k]
        ]

    async def retrieve_recommendations(
        self,
        assessment_id: str,
        role_slug: str,
        profile_signals: dict | None = None,
        essay_keywords: list[str] | None = None,
        missed_topics: list[str] | None = None,
        top_k: int = 5,
        readiness_policy: dict[str, object] | None = None,
        enable_fallback: bool = True,
    ) -> RAGResult:
        """
        Retrieve role-aware recommendations for an assessment.

        AC1: Composes RAG query from track tags, profile signals, and essay embeddings.
        AC2: Returns Top-K credentials with metadata.
        AC4: Static fallback when retrieval fails.
        """
        query = self._build_query(
            role_slug,
            profile_signals,
            essay_keywords,
            missed_topics,
            foundation_first=bool(readiness_policy and readiness_policy.get("force_foundation")),
        )

        try:
            matches = self._retrieve_courses(
                query,
                role_slug,
                top_k,
                missed_topics,
                profile_signals,
                readiness_policy=readiness_policy,
            )

            if not matches:
                if not enable_fallback:
                    await logger.ainfo(
                        "rag_no_matches",
                        assessment_id=assessment_id,
                        query=query,
                    )
                    return RAGResult(
                        query=query,
                        matches=[],
                        readiness=readiness_policy,
                    )

                # AC4: Static fallback
                await logger.ainfo(
                    "rag_fallback_activated",
                    assessment_id=assessment_id,
                    reason="no_matches",
                )
                return RAGResult(
                    query=query,
                    matches=self._get_fallback_courses(role_slug, top_k),
                    degraded=True,
                    readiness=readiness_policy,
                )

            await logger.ainfo(
                "rag_retrieval_success",
                assessment_id=assessment_id,
                query=query,
                match_count=len(matches),
                readiness_tier=(
                    readiness_policy.get("readiness_tier") if readiness_policy else None
                ),
                forced_foundation=(
                    readiness_policy.get("force_foundation") if readiness_policy else False
                ),
            )

            return RAGResult(query=query, matches=matches, readiness=readiness_policy)

        except Exception as e:
            await logger.aerror(
                "rag_retrieval_failed",
                assessment_id=assessment_id,
                error=str(e),
            )
            if not enable_fallback:
                return RAGResult(
                    query=query,
                    matches=[],
                    error=str(e),
                    readiness=readiness_policy,
                )
            # AC4: Static fallback on error
            return RAGResult(
                query=query,
                matches=self._get_fallback_courses(role_slug, top_k),
                degraded=True,
                error=str(e),
                readiness=readiness_policy,
            )

    def _get_fallback_courses(self, role_slug: str, top_k: int = 5) -> list[CourseMatch]:
        """Get static fallback courses when RAG fails."""
        courses = self._load_courses()
        if not courses:
            return []

        # Get role subject mapping
        subject_map = {
            "backend-engineer": "Web Development",
            "frontend-engineer": "Web Development",
            "data-scientist": "Business Finance",  # Closest available
            "data-analyst": "Business Finance",
            "devops-engineer": "Web Development",
            "product-manager": "Business Finance",
        }
        target_subject = subject_map.get(role_slug, "Web Development")

        # Filter by subject and sort by subscribers
        filtered = [c for c in courses if target_subject in c.get("subject", "")]
        filtered.sort(
            key=lambda x: int(x.get("num_subscribers", 0) or 0),
            reverse=True,
        )

        matches = []
        for course in filtered[:top_k]:
            num_reviews = int(course.get("num_reviews", "0") or 0)
            num_subscribers = int(course.get("num_subscribers", "0") or 0)
            level = course.get("level", "").lower()

            reason_parts = [f"Popular {target_subject} course"]
            if num_subscribers > 10000:
                reason_parts.append(f"with {num_subscribers:,} enrolled students")
            if num_reviews > 100:
                reason_parts.append(f"{num_reviews} reviews")
            if "beginner" in level:
                reason_parts.append("ideal for getting started")
            elif "all levels" in level:
                reason_parts.append("suitable for all experience levels")

            match_reason = ". ".join(reason_parts) + "."

            matches.append(
                CourseMatch(
                    course_id=course.get("course_id", ""),
                    title=course.get("course_title", ""),
                    url=course.get("url"),
                    relevance_score=0.5,  # Fixed score for fallback
                    match_reason=match_reason,
                    metadata={
                        "subject": course.get("subject", ""),
                        "level": course.get("level", ""),
                        "num_subscribers": course.get("num_subscribers", ""),
                    },
                )
            )

        return matches

    def _tag_matches_with_learning_path(
        self,
        matches: list[CourseMatch],
        path_key: str,
        path_label: str,
    ) -> list[CourseMatch]:
        """Attach learning-path metadata to recommendation matches."""
        tagged: list[CourseMatch] = []
        for match in matches:
            metadata = dict(match.metadata or {})
            metadata["learning_path"] = path_key
            metadata["learning_path_label"] = path_label

            base_reason = (match.match_reason or "").strip()
            if base_reason:
                tagged_reason = f"{path_label} • {base_reason}"
            else:
                tagged_reason = path_label

            tagged.append(
                CourseMatch(
                    course_id=match.course_id,
                    title=match.title,
                    url=match.url,
                    relevance_score=match.relevance_score,
                    match_reason=tagged_reason,
                    metadata=metadata,
                )
            )
        return tagged

    def _merge_unique_matches(
        self,
        primary: list[CourseMatch],
        secondary: list[CourseMatch],
        limit: int,
    ) -> list[CourseMatch]:
        """Merge two ranked lists while preserving order and removing duplicates."""
        merged: list[CourseMatch] = []
        seen_ids: set[str] = set()
        for source in (primary, secondary):
            for item in source:
                if item.course_id in seen_ids:
                    continue
                merged.append(item)
                seen_ids.add(item.course_id)
                if len(merged) >= limit:
                    return merged
        return merged

    async def _retrieve_with_learning_paths(
        self,
        assessment_id: str,
        role_slug: str,
        profile_signals: dict | None,
        essay_keywords: list[str] | None,
        missed_topics: list[str] | None,
        readiness_policy: dict[str, object],
    ) -> RAGResult:
        """
        Build recommendations with two-path output when advanced target isn't ready.

        Path model:
        - Mandatory Foundation: required courses for current readiness.
        - Target Path (Aspirational): user-desired stack as next phase.
        """
        force_foundation = bool(readiness_policy.get("force_foundation"))
        if not force_foundation:
            base_result = await self.retrieve_recommendations(
                assessment_id=assessment_id,
                role_slug=role_slug,
                profile_signals=profile_signals,
                essay_keywords=essay_keywords,
                missed_topics=missed_topics,
                readiness_policy=readiness_policy,
            )
            tagged_matches = self._tag_matches_with_learning_path(
                base_result.matches,
                path_key="target_path",
                path_label="Target Path",
            )
            readiness_with_paths = dict(base_result.readiness or readiness_policy)
            readiness_with_paths["learning_paths"] = {
                "mode": "single-path",
                "target_path_count": len(tagged_matches),
                "mandatory_foundation_count": 0,
            }
            return RAGResult(
                query=base_result.query,
                matches=tagged_matches,
                degraded=base_result.degraded,
                error=base_result.error,
                readiness=readiness_with_paths,
            )

        # Two-path mode for not-yet-ready advanced targets.
        foundation_profile_signals = dict(profile_signals or {})
        foundation_profile_signals.pop("tech-preferences", None)
        foundation_result = await self.retrieve_recommendations(
            assessment_id=assessment_id,
            role_slug=role_slug,
            profile_signals=foundation_profile_signals,
            essay_keywords=essay_keywords,
            missed_topics=missed_topics,
            top_k=3,
            readiness_policy=readiness_policy,
        )
        foundation_matches = self._tag_matches_with_learning_path(
            foundation_result.matches,
            path_key="mandatory_foundation",
            path_label="Mandatory Foundation",
        )

        target_policy = dict(readiness_policy)
        target_policy["force_foundation"] = False
        target_policy["difficulty_pref"] = None
        target_policy["reason"] = None
        target_result = await self.retrieve_recommendations(
            assessment_id=assessment_id,
            role_slug=role_slug,
            profile_signals=profile_signals,
            essay_keywords=essay_keywords,
            missed_topics=missed_topics,
            top_k=2,
            readiness_policy=target_policy,
            enable_fallback=False,
        )
        target_matches = self._tag_matches_with_learning_path(
            target_result.matches,
            path_key="target_path",
            path_label="Target Path (Aspirational)",
        )

        combined = self._merge_unique_matches(foundation_matches, target_matches, limit=5)
        combined_mandatory_count = sum(
            1
            for item in combined
            if str((item.metadata or {}).get("learning_path")) == "mandatory_foundation"
        )
        combined_target_count = sum(
            1
            for item in combined
            if str((item.metadata or {}).get("learning_path")) == "target_path"
        )
        readiness_with_paths = dict(readiness_policy)
        readiness_with_paths["learning_paths"] = {
            "mode": "two-path",
            "mandatory_foundation_count": combined_mandatory_count,
            "target_path_count": combined_target_count,
            "mandatory_foundation_query": foundation_result.query,
            "target_path_query": target_result.query,
            "note": (
                "Target path bersifat aspirational. Selesaikan Mandatory Foundation "
                "terlebih dahulu agar risiko gagal belajar lebih rendah."
            ),
        }

        return RAGResult(
            query=foundation_result.query,
            matches=combined,
            degraded=foundation_result.degraded,
            error=foundation_result.error or target_result.error,
            readiness=readiness_with_paths,
        )

    async def process_rag_job(self, assessment_id: str) -> RAGResult:
        """
        Process RAG job for an assessment.

        AC3: Results persisted in recommendation_items with ranked order.
        """
        # Get assessment with role
        stmt = select(Assessment).where(Assessment.id == assessment_id)
        result = await self.session.execute(stmt)
        assessment = result.scalar_one_or_none()

        if not assessment:
            raise RAGRetrievalError(f"Assessment {assessment_id} not found")

        # Get job
        job_stmt = select(AsyncJob).where(
            AsyncJob.assessment_id == assessment_id,
            AsyncJob.job_type == JobType.RAG.value,
        )
        job_result = await self.session.execute(job_stmt)
        job = job_result.scalar_one_or_none()

        if job:
            # Mark job as in progress
            job.status = JobStatus.IN_PROGRESS.value
            job.started_at = datetime.now(UTC)
            job.attempts += 1
            await self.session.flush()

        # Extract profile signals from responses
        profile_signals = await self._extract_profile_signals(assessment_id)

        # Extract essay keywords from scores/responses
        essay_keywords = await self._extract_essay_keywords(assessment_id)
        missed_topics = await self._extract_missed_topics(assessment_id)
        score_metrics = await self._extract_score_metrics(assessment_id)
        readiness_policy = self._build_readiness_policy(
            assessment.role_slug,
            profile_signals,
            score_metrics,
        )

        # Retrieve recommendations with readiness-aware learning paths.
        rag_result = await self._retrieve_with_learning_paths(
            assessment_id=assessment_id,
            role_slug=assessment.role_slug,
            profile_signals=profile_signals,
            essay_keywords=essay_keywords,
            missed_topics=missed_topics,
            readiness_policy=readiness_policy,
        )

        # AC3: Persist results
        await self._persist_recommendation_items(assessment_id, rag_result)

        # Update job status
        if job:
            job.status = JobStatus.COMPLETED.value
            job.completed_at = datetime.now(UTC)
            if rag_result.degraded:
                job.payload = {"degraded": True, "reason": rag_result.error or "fallback"}

        await self.session.commit()

        return rag_result

    async def _extract_profile_signals(self, assessment_id: str) -> dict:
        """Extract profile signals from assessment responses."""
        stmt = (
            select(AssessmentQuestionSnapshot, AssessmentResponse)
            .join(
                AssessmentResponse,
                AssessmentResponse.question_snapshot_id == AssessmentQuestionSnapshot.id,
            )
            .where(
                AssessmentQuestionSnapshot.assessment_id == assessment_id,
                AssessmentQuestionSnapshot.question_type == QuestionType.PROFILE,
            )
        )
        rows = (await self.session.execute(stmt)).all()
        signals: dict[str, str | list[str]] = {}
        for snapshot, response in rows:
            response_data = response.response_data or {}
            # Check multiple possible keys for the response value
            # Q8 tech-preferences uses allow_custom which may store value differently
            value = (
                response_data.get("value")
                or response_data.get("selected_option")
                or response_data.get("answer")
                or response_data.get("answer_text")
                or response_data.get("custom_text")
                or response_data.get("text")
            )
            if not value:
                continue
            key = (snapshot.metadata_ or {}).get("dimension") or str(snapshot.sequence)
            if isinstance(value, list):
                cleaned = [str(item).strip() for item in value if str(item).strip()]
                if not cleaned:
                    continue
                signals[str(key)] = cleaned
            else:
                text_value = str(value).strip()
                if not text_value:
                    continue
                signals[str(key)] = text_value
        return signals

    async def _extract_essay_keywords(self, assessment_id: str) -> list[str]:
        """Extract keywords from essay responses/scores."""
        stmt = (
            select(AssessmentQuestionSnapshot, AssessmentResponse)
            .join(
                AssessmentResponse,
                AssessmentResponse.question_snapshot_id == AssessmentQuestionSnapshot.id,
            )
            .where(
                AssessmentQuestionSnapshot.assessment_id == assessment_id,
                AssessmentQuestionSnapshot.question_type == QuestionType.ESSAY,
            )
        )
        rows = (await self.session.execute(stmt)).all()
        tokens: list[str] = []
        for _snapshot, response in rows:
            essay_text = response.response_data.get("answer", "")
            tokens.extend(self._tokenize(essay_text))
        counts = Counter(tokens)
        return [token for token, _count in counts.most_common(5)]

    async def _extract_missed_topics(self, assessment_id: str) -> list[str]:
        """Extract topics from questions that scored poorly."""
        profile_dimensions = {
            "experience",
            "experience-level",
            "tech-preferences",
            "content-duration",
            "payment-preference",
        }
        stmt = (
            select(Score, AssessmentQuestionSnapshot)
            .join(
                AssessmentQuestionSnapshot,
                AssessmentQuestionSnapshot.id == Score.question_snapshot_id,
            )
            .where(Score.assessment_id == assessment_id)
        )
        rows = (await self.session.execute(stmt)).all()
        missed: list[str] = []
        for score, snapshot in rows:
            if score.max_score <= 0:
                continue
            ratio = score.score / score.max_score
            if ratio >= 0.6:
                continue
            if snapshot.question_type == QuestionType.PROFILE:
                continue
            dimension = (snapshot.metadata_ or {}).get("dimension")
            if dimension and dimension not in profile_dimensions:
                missed.append(str(dimension))
        return missed

    async def _extract_score_metrics(self, assessment_id: str) -> dict[str, float | bool]:
        """Extract score percentages used for readiness/KKM gating."""
        stmt = select(Score).where(Score.assessment_id == assessment_id)
        result = await self.session.execute(stmt)
        scores = result.scalars().all()

        totals = {
            QuestionType.THEORETICAL: {"score": 0.0, "max": 0.0},
            QuestionType.PROFILE: {"score": 0.0, "max": 0.0},
            QuestionType.ESSAY: {"score": 0.0, "max": 0.0},
        }

        for score in scores:
            bucket = totals.get(score.question_type)
            if bucket is None:
                continue
            bucket["score"] += float(score.score or 0.0)
            bucket["max"] += float(score.max_score or 0.0)

        def pct(kind: QuestionType) -> float:
            max_val = totals[kind]["max"]
            if max_val <= 0:
                return 0.0
            return round((totals[kind]["score"] / max_val) * 100, 1)

        overall_score = sum(item["score"] for item in totals.values())
        overall_max = sum(item["max"] for item in totals.values())
        overall_pct = round((overall_score / overall_max) * 100, 1) if overall_max > 0 else 0.0

        return {
            "theoretical_pct": pct(QuestionType.THEORETICAL),
            "profile_pct": pct(QuestionType.PROFILE),
            "essay_pct": pct(QuestionType.ESSAY),
            "overall_pct": overall_pct,
            "has_essay_scores": totals[QuestionType.ESSAY]["max"] > 0,
        }

    async def _persist_recommendation_items(
        self,
        assessment_id: str,
        rag_result: RAGResult,
    ) -> None:
        """Persist RAG results as recommendation items."""
        # Check if recommendation exists
        stmt = select(Recommendation).where(Recommendation.assessment_id == assessment_id)
        result = await self.session.execute(stmt)
        recommendation = result.scalar_one_or_none()

        if not recommendation:
            # Create recommendation (will be fully populated by fusion)
            recommendation = Recommendation(
                assessment_id=assessment_id,
                summary="Pending fusion processing",
                overall_score=0.0,
                degraded=rag_result.degraded,
                rag_query=rag_result.query,
                rag_traces={
                    "match_count": len(rag_result.matches),
                    "degraded": rag_result.degraded,
                    "error": rag_result.error,
                    "readiness": rag_result.readiness,
                },
            )
            self.session.add(recommendation)
            await self.session.flush()
        else:
            recommendation.rag_query = rag_result.query
            recommendation.degraded = rag_result.degraded or recommendation.degraded
            recommendation.rag_traces = {
                "match_count": len(rag_result.matches),
                "degraded": rag_result.degraded,
                "error": rag_result.error,
                "readiness": rag_result.readiness,
            }

        # Add recommendation items
        for i, match in enumerate(rag_result.matches, start=1):
            item = RecommendationItem(
                recommendation_id=recommendation.id,
                rank=i,
                course_id=match.course_id,
                course_title=match.title,
                course_url=match.url,
                relevance_score=match.relevance_score,
                match_reason=match.match_reason,
                course_metadata=match.metadata,
            )
            self.session.add(item)
