"""
RAG Service for Story 3.1: Role-Aware RAG Retrieval.

Uses TF-IDF based retrieval from Udemy courses dataset as a simple RAG implementation.
Can be upgraded to Chroma/PGVector for production.
"""

from __future__ import annotations

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


class RAGRetrievalError(Exception):
    """Raised when RAG retrieval fails."""


class RAGService:
    """Service for RAG-based credential recommendations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._courses: list[dict] | None = None

    def _load_courses(self) -> list[dict]:
        """Load courses from CSV file."""
        if self._courses is not None:
            return self._courses

        courses = []
        try:
            with open(COURSES_CSV_PATH, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self._annotate_course(row)
                    courses.append(row)
            self._courses = courses
        except FileNotFoundError:
            logger.warning("courses_file_not_found", path=str(COURSES_CSV_PATH))
            self._courses = []

        return self._courses

    def _annotate_course(self, course: dict) -> None:
        title = course.get("course_title", "")
        subject = course.get("subject", "")
        text = f"{title} {subject}".lower()
        tags = self._extract_topic_tags(text)
        tokens = self._tokenize(text)
        course["_tags"] = tags
        course["_vector"] = self._hash_embedding(tokens)

    def _tokenize(self, text: str) -> list[str]:
        clean = re.sub(r"[^a-z0-9]+", " ", text.lower())
        return [t for t in clean.split() if len(t) > 2 and t not in STOPWORDS]

    def _extract_topic_tags(self, text: str) -> list[str]:
        tags = []
        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
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

    def _build_query(
        self,
        role_slug: str,
        profile_signals: dict | None = None,
        essay_keywords: list[str] | None = None,
        missed_topics: list[str] | None = None,
    ) -> str:
        """Build RAG query from role context and signals.

        Priority order (highest first):
        1. User's tech preferences (what they explicitly want to learn)
        2. Missed topics from assessment (areas needing improvement)
        3. Essay keywords (topics user discussed)
        4. Role keywords (general role-related terms)
        """
        query_parts = []

        # PRIORITY 1: User tech preferences first (most important)
        # User explicitly stated what they want to learn
        if profile_signals:
            tech_prefs = profile_signals.get("tech-preferences", "")
            if tech_prefs:
                pref_keywords = [
                    t.strip().lower()
                    for t in tech_prefs.replace(",", " ").split()
                    if len(t.strip()) > 2
                ]
                # Add tech preferences multiple times for higher weight
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

    def _calculate_relevance(self, course: dict, query_terms: list[str]) -> float:
        """Calculate relevance score using simple keyword matching."""
        title = course.get("course_title", "").lower()
        subject = course.get("subject", "").lower()
        text = f"{title} {subject}"

        matches = 0
        for term in query_terms:
            if term.lower() in text:
                matches += 1

        if not query_terms:
            return 0.0

        # Base score from keyword matches
        keyword_score = matches / len(query_terms)

        # Boost for popular courses
        try:
            subscribers = int(course.get("num_subscribers", 0))
            popularity_boost = min(0.2, subscribers / 100000)
        except (ValueError, TypeError):
            popularity_boost = 0

        # Boost for highly rated
        try:
            reviews = int(course.get("num_reviews", 0))
            review_boost = min(0.1, reviews / 5000)
        except (ValueError, TypeError):
            review_boost = 0

        return min(1.0, keyword_score * 0.7 + popularity_boost + review_boost)

    def _retrieve_courses(
        self,
        query: str,
        top_k: int = 5,
        missed_topics: list[str] | None = None,
        profile_signals: dict | None = None,
    ) -> list[CourseMatch]:
        """Retrieve top-K courses matching the query."""
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
        payment_pref = profile_signals.get("payment-preference", "any").lower()
        duration_pref = profile_signals.get("content-duration", "any").lower()
        tech_prefs = profile_signals.get("tech-preferences", "").lower()

        # Parse tech preferences into keywords for exact matching
        tech_pref_keywords = [
            t.strip().lower() for t in tech_prefs.replace(",", " ").split() if len(t.strip()) > 2
        ]

        scored_courses = []
        for course in courses:
            # Filter by payment preference (Q4)
            is_paid = str(course.get("is_paid", "True")).lower() == "true"
            if payment_pref == "free" and is_paid:
                continue  # Skip paid courses if user wants free
            elif payment_pref == "paid" and not is_paid:
                continue  # Skip free courses if user wants paid

            # Calculate scores
            keyword_score = self._calculate_relevance(course, query_terms)
            embedding_score = self._cosine_similarity(query_vec, course.get("_vector", []))
            tag_boost = 0.0
            course_tags = course.get("_tags", [])
            if missed_topics and any(tag in missed_topics for tag in course_tags):
                tag_boost = 0.1

            # MAJOR BOOST for exact tech preference match
            # This ensures courses matching user's explicit preference rank higher
            tech_pref_boost = 0.0
            course_title_lower = course.get("course_title", "").lower()
            tech_pref_matched = False
            matched_tech_terms = []
            for tech_term in tech_pref_keywords:
                if tech_term in course_title_lower:
                    tech_pref_boost += 0.3  # Significant boost per matched term
                    tech_pref_matched = True
                    matched_tech_terms.append(tech_term)

            # Store matched tech terms for reason generation
            course["_matched_tech_prefs"] = matched_tech_terms
            course["_tech_pref_matched"] = tech_pref_matched

            # Boost for duration preference (Q3) - requires content_duration field in CSV
            # For now, we'll infer from level as proxy:
            # - short: beginner courses
            # - medium: intermediate
            # - long: advanced/all levels
            duration_boost = 0.0
            level = course.get("level", "").lower()
            duration_matched = False
            if duration_pref == "short" and "beginner" in level:
                duration_boost = 0.05
                duration_matched = True
            elif duration_pref == "medium" and "intermediate" in level:
                duration_boost = 0.05
                duration_matched = True
            elif duration_pref == "long" and ("advanced" in level or "all levels" in level):
                duration_boost = 0.05
                duration_matched = True

            # Track payment match for match_reason
            payment_matched = (
                (payment_pref == "free" and not is_paid)
                or (payment_pref == "paid" and is_paid)
                or payment_pref == "any"
            )

            # Store preference match info for later
            course["_duration_matched"] = duration_matched
            course["_payment_matched"] = payment_matched and payment_pref != "any"
            course["_is_paid"] = is_paid

            # Calculate final score with tech preference boost having highest weight
            score = (
                keyword_score * 0.4
                + embedding_score * 0.2
                + tag_boost
                + duration_boost
                + tech_pref_boost  # Major boost for matching user's explicit tech preference
            )
            if score > 0.1:  # Minimum threshold
                scored_courses.append((course, score))

        # Sort by score descending, then by course_id for deterministic results
        scored_courses.sort(key=lambda x: (-x[1], x[0].get("course_id", "")))

        matches = []
        for _i, (course, score) in enumerate(scored_courses[:top_k]):
            # Find which terms matched
            title = course.get("course_title", "").lower()
            matched_terms = [t for t in query_terms if t.lower() in title]
            matched_topics = [t for t in (course.get("_tags", []) or []) if t in missed_topics]

            # Generate comprehensive match reason
            level = course.get("level", "").lower()
            subject = course.get("subject", "")
            num_reviews = int(course.get("num_reviews", "0") or 0)
            rating_quality = (
                "highly-rated" if num_reviews > 100 else "well-reviewed" if num_reviews > 50 else ""
            )

            reason_parts = []

            # PRIORITY: Show tech preference match first (most important to user)
            matched_tech_prefs = course.get("_matched_tech_prefs", [])
            if matched_tech_prefs:
                reason_parts.append("Matches your interest in " + ", ".join(matched_tech_prefs))

            if matched_terms:
                # Filter out terms already mentioned in tech prefs
                other_terms = [t for t in matched_terms[:3] if t not in matched_tech_prefs]
                if other_terms:
                    reason_parts.append("covers " + ", ".join(other_terms))

            if matched_topics:
                reason_parts.append("addresses " + ", ".join(matched_topics[:2]))
            if rating_quality:
                reason_parts.append(f"{rating_quality} ({num_reviews} reviews)")

            # Add personalization match reasons
            if course.get("_duration_matched"):
                if "beginner" in level:
                    reason_parts.append("matches your preference for short/beginner content")
                elif "intermediate" in level:
                    reason_parts.append("matches your preferred medium duration")
                elif "advanced" in level or "all levels" in level:
                    reason_parts.append("matches your preference for comprehensive content")

            if course.get("_payment_matched"):
                is_paid = course.get("_is_paid", True)
                if is_paid:
                    reason_parts.append("premium course as preferred")
                else:
                    reason_parts.append("free course as preferred")

            # Level description
            if "beginner" in level or "all levels" in level:
                reason_parts.append("suitable for building foundations")
            elif "intermediate" in level or "advanced" in level:
                reason_parts.append("for advancing skills")

            match_reason = (
                ". ".join(reason_parts).capitalize() + "."
                if reason_parts
                else f"Relevant course in {subject}."
            )

            matches.append(
                CourseMatch(
                    course_id=course.get("course_id", ""),
                    title=course.get("course_title", ""),
                    url=course.get("url"),
                    relevance_score=round(score, 3),
                    match_reason=match_reason,
                    metadata={
                        "subject": subject,
                        "level": course.get("level", ""),
                        "num_subscribers": course.get("num_subscribers", ""),
                        "num_reviews": course.get("num_reviews", ""),
                        "is_paid": course.get("is_paid", ""),
                        "price": course.get("price", ""),
                        "tags": course.get("_tags", []),
                    },
                )
            )

        return matches

    async def retrieve_recommendations(
        self,
        assessment_id: str,
        role_slug: str,
        profile_signals: dict | None = None,
        essay_keywords: list[str] | None = None,
        missed_topics: list[str] | None = None,
        top_k: int = 5,
    ) -> RAGResult:
        """
        Retrieve role-aware recommendations for an assessment.

        AC1: Composes RAG query from track tags, profile signals, and essay embeddings.
        AC2: Returns Top-K credentials with metadata.
        AC4: Static fallback when retrieval fails.
        """
        query = self._build_query(role_slug, profile_signals, essay_keywords, missed_topics)

        try:
            matches = self._retrieve_courses(query, top_k, missed_topics, profile_signals)

            if not matches:
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
                )

            await logger.ainfo(
                "rag_retrieval_success",
                assessment_id=assessment_id,
                query=query,
                match_count=len(matches),
            )

            return RAGResult(query=query, matches=matches)

        except Exception as e:
            await logger.aerror(
                "rag_retrieval_failed",
                assessment_id=assessment_id,
                error=str(e),
            )
            # AC4: Static fallback on error
            return RAGResult(
                query=query,
                matches=self._get_fallback_courses(role_slug, top_k),
                degraded=True,
                error=str(e),
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

        # Retrieve recommendations
        rag_result = await self.retrieve_recommendations(
            assessment_id=assessment_id,
            role_slug=assessment.role_slug,
            profile_signals=profile_signals,
            essay_keywords=essay_keywords,
            missed_topics=missed_topics,
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
        signals: dict[str, str] = {}
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
            signals[str(key)] = str(value)
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
            dimension = (snapshot.metadata_ or {}).get("dimension")
            if dimension:
                missed.append(str(dimension))
        return missed

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
                },
            )
            self.session.add(recommendation)
            await self.session.flush()

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
