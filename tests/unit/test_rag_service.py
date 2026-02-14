"""
Unit tests for Story 3.1: RAG Retrieval Service.

Tests the keyword-based course recommendation system.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from src.domain.services.rag import CourseMatch, RAGService
from src.infrastructure.repositories.course_enrichment import EnrichedCourseMetadata


class TestRAGService:
    """Tests for RAGService."""

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def rag_service(self, mock_session):
        """Create RAGService instance."""
        return RAGService(mock_session)

    def test_build_query_for_backend_engineer(self, rag_service):
        """Test query building for backend-engineer role."""
        query = rag_service._build_query("backend-engineer")

        # Should contain backend role keywords
        assert any(kw in query.lower() for kw in ["python", "api", "java", "node", "database"])

    def test_build_query_for_frontend_engineer(self, rag_service):
        """Test query building for frontend-engineer role."""
        query = rag_service._build_query("frontend-engineer")

        # Should contain frontend role keywords
        assert any(kw in query.lower() for kw in ["javascript", "react", "vue", "angular", "css"])

    def test_build_query_for_data_scientist(self, rag_service):
        """Test query building for data-scientist role."""
        query = rag_service._build_query("data-scientist")

        assert "data" in query.lower() or "python" in query.lower()

    def test_build_query_for_unknown_role(self, rag_service):
        """Test query building for unknown role returns empty or generic."""
        query = rag_service._build_query("unknown-role")

        # Unknown role may return empty or use profile signals
        assert isinstance(query, str)

    def test_build_query_with_profile_signals(self, rag_service):
        """Test query includes profile signals."""
        profile_signals = {"skill1": "database optimization", "skill2": "python"}
        query = rag_service._build_query("backend-engineer", profile_signals=profile_signals)

        # Query should incorporate profile signals
        assert "database" in query.lower() or "python" in query.lower()

    def test_build_query_with_essay_keywords(self, rag_service):
        """Test query includes essay keywords."""
        essay_keywords = ["microservices", "kubernetes"]
        query = rag_service._build_query("backend-engineer", essay_keywords=essay_keywords)

        # Should include essay keywords
        assert "microservices" in query.lower() or "kubernetes" in query.lower()

    def test_calculate_relevance_with_matches(self, rag_service):
        """Test relevance calculation with keyword matches."""
        course = {
            "course_title": "Python Backend Development Masterclass",
            "subject": "Web Development",
        }
        query_terms = ["python", "backend", "development"]

        score = rag_service._calculate_relevance(course, query_terms)

        assert score > 0  # Should have some relevance

    def test_calculate_relevance_no_match(self, rag_service):
        """Test relevance calculation with no keyword match."""
        course = {
            "course_title": "Cooking Basics",
            "subject": "Lifestyle",
        }
        query_terms = ["python", "backend", "api"]

        score = rag_service._calculate_relevance(course, query_terms)

        assert score == 0  # No matches

    def test_readiness_policy_forces_foundation_when_not_meeting_kkm(self, rag_service):
        """Advanced target should be gated to foundational courses when score is low."""
        policy = rag_service._build_readiness_policy(
            role_slug="backend-engineer",
            profile_signals={"tech-preferences": "aws, graphql"},
            score_metrics={
                "overall_pct": 52.0,
                "theoretical_pct": 58.0,
                "profile_pct": 38.0,
                "essay_pct": 0.0,
                "has_essay_scores": False,
            },
        )

        assert policy["targeting_advanced"] is True
        assert policy["advanced_eligible"] is False
        assert policy["force_foundation"] is True
        assert policy["difficulty_pref"] == "beginner"

    def test_readiness_policy_allows_advanced_when_score_is_strong(self, rag_service):
        """Advanced track is allowed when score passes KKM."""
        policy = rag_service._build_readiness_policy(
            role_slug="backend-engineer",
            profile_signals={"tech-preferences": "aws, graphql"},
            score_metrics={
                "overall_pct": 82.0,
                "theoretical_pct": 80.0,
                "profile_pct": 72.0,
                "essay_pct": 76.0,
                "has_essay_scores": True,
            },
        )

        assert policy["targeting_advanced"] is True
        assert policy["advanced_eligible"] is True
        assert policy["force_foundation"] is False

    def test_difficulty_gate_filters_out_advanced_courses(self, rag_service):
        """Beginner difficulty gate should exclude intermediate/advanced courses."""
        beginner_course = {
            "course_id": "c1",
            "course_title": "AWS Basics for Beginners",
            "subject": "Web Development",
            "url": "http://test.com/c1",
            "level": "Beginner Level",
            "content_duration": 4.0,
            "is_paid": "False",
            "price": 0.0,
            "num_subscribers": 1000,
            "num_reviews": 100,
            "_vector": rag_service._hash_embedding(["aws", "basics"]),
            "_enriched": EnrichedCourseMetadata(
                course_id="c1",
                title="AWS Basics for Beginners",
                tech_tags=["aws"],
                difficulty="beginner",
                is_free=True,
                payment_type="free",
                price=0.0,
                duration_hours=4.0,
                duration_category="short",
                num_subscribers=1000,
                num_reviews=100,
                num_lectures=20,
                quality_score=0.6,
                popularity_score=0.2,
                engagement_score=0.4,
                level="Beginner Level",
                subject="Web Development",
                url="http://test.com/c1",
                published_timestamp="2025-01-01T00:00:00Z",
            ),
        }
        advanced_course = {
            "course_id": "c2",
            "course_title": "AWS Advanced Architecture",
            "subject": "Web Development",
            "url": "http://test.com/c2",
            "level": "Expert Level",
            "content_duration": 15.0,
            "is_paid": "True",
            "price": 49.0,
            "num_subscribers": 2000,
            "num_reviews": 150,
            "_vector": rag_service._hash_embedding(["aws", "advanced"]),
            "_enriched": EnrichedCourseMetadata(
                course_id="c2",
                title="AWS Advanced Architecture",
                tech_tags=["aws"],
                difficulty="advanced",
                is_free=False,
                payment_type="paid",
                price=49.0,
                duration_hours=15.0,
                duration_category="medium",
                num_subscribers=2000,
                num_reviews=150,
                num_lectures=50,
                quality_score=0.7,
                popularity_score=0.3,
                engagement_score=0.4,
                level="Expert Level",
                subject="Web Development",
                url="http://test.com/c2",
                published_timestamp="2025-01-01T00:00:00Z",
            ),
        }

        matches = rag_service._score_and_filter_courses(
            courses=[beginner_course, advanced_course],
            role_slug="backend-engineer",
            query_terms=["aws"],
            query_vec=rag_service._hash_embedding(["aws"]),
            missed_topics=[],
            tech_pref_keywords=["aws"],
            payment_pref="any",
            duration_pref="any",
            top_k=5,
            difficulty_pref="beginner",
            strict_payment=True,
        )

        assert len(matches) == 1
        assert matches[0].course_id == "c1"

    def test_role_fallback_keywords_exclude_advanced_bias(self, rag_service):
        """Role fallback keywords should not be dominated by advanced targets."""
        fallback = rag_service._get_role_fallback_keywords("backend-engineer")

        lowered = [item.lower() for item in fallback]
        assert "api" in lowered
        assert "database" in lowered
        assert "sql" in lowered
        assert "aws" not in lowered

    def test_min_keyword_guard_filters_irrelevant_foundation_fill(self, rag_service):
        """Low-signal irrelevant courses should be filtered during broad foundation fallback."""
        relevant_course = {
            "course_id": "backend-1",
            "course_title": "REST API with Python Flask",
            "subject": "Web Development",
            "url": "http://test.com/backend-1",
            "level": "Beginner Level",
            "content_duration": 5.0,
            "is_paid": "False",
            "price": 0.0,
            "num_subscribers": 500,
            "num_reviews": 50,
            "_vector": rag_service._hash_embedding(["rest", "api", "python"]),
            "_enriched": EnrichedCourseMetadata(
                course_id="backend-1",
                title="REST API with Python Flask",
                tech_tags=["python", "api"],
                difficulty="beginner",
                is_free=True,
                payment_type="free",
                price=0.0,
                duration_hours=5.0,
                duration_category="medium",
                num_subscribers=500,
                num_reviews=50,
                num_lectures=20,
                quality_score=0.4,
                popularity_score=0.1,
                engagement_score=0.3,
                level="Beginner Level",
                subject="Web Development",
                url="http://test.com/backend-1",
                published_timestamp="2025-01-01T00:00:00Z",
            ),
        }
        irrelevant_course = {
            "course_id": "music-1",
            "course_title": "Piano for Beginners",
            "subject": "Musical Instruments",
            "url": "http://test.com/music-1",
            "level": "Beginner Level",
            "content_duration": 30.0,
            "is_paid": "True",
            "price": 19.0,
            "num_subscribers": 70000,
            "num_reviews": 2000,
            "_vector": rag_service._hash_embedding(["piano", "music"]),
            "_enriched": EnrichedCourseMetadata(
                course_id="music-1",
                title="Piano for Beginners",
                tech_tags=["music", "instruments"],
                difficulty="beginner",
                is_free=False,
                payment_type="paid",
                price=19.0,
                duration_hours=30.0,
                duration_category="long",
                num_subscribers=70000,
                num_reviews=2000,
                num_lectures=120,
                quality_score=0.9,
                popularity_score=0.8,
                engagement_score=0.7,
                level="Beginner Level",
                subject="Musical Instruments",
                url="http://test.com/music-1",
                published_timestamp="2025-01-01T00:00:00Z",
            ),
        }

        matches = rag_service._score_and_filter_courses(
            courses=[relevant_course, irrelevant_course],
            role_slug="backend-engineer",
            query_terms=["python", "api", "backend"],
            query_vec=rag_service._hash_embedding(["python", "api", "backend"]),
            missed_topics=[],
            tech_pref_keywords=[],
            payment_pref="any",
            duration_pref="any",
            top_k=5,
            difficulty_pref="beginner",
            min_keyword_score=0.05,
            strict_payment=False,
        )

        assert len(matches) == 1
        assert matches[0].course_id == "backend-1"

    def test_tag_matches_with_learning_path_sets_metadata(self, rag_service):
        """Learning path tags should be embedded in metadata and reason."""
        source = [
            CourseMatch(
                course_id="course-1",
                title="API Fundamentals",
                url="http://example.com/course-1",
                relevance_score=0.77,
                match_reason="Matches your interest in: api",
                metadata={"level": "Beginner Level"},
            )
        ]

        tagged = rag_service._tag_matches_with_learning_path(
            source,
            path_key="mandatory_foundation",
            path_label="Mandatory Foundation",
        )

        assert len(tagged) == 1
        assert tagged[0].metadata["learning_path"] == "mandatory_foundation"
        assert tagged[0].metadata["learning_path_label"] == "Mandatory Foundation"
        assert tagged[0].match_reason.startswith("Mandatory Foundation")

    def test_merge_unique_matches_prioritizes_primary_then_secondary(self, rag_service):
        """Primary list order should win, with secondary filling remaining slots uniquely."""
        primary = [
            CourseMatch("c1", "Course 1", None, 0.9, "r1", {}),
            CourseMatch("c2", "Course 2", None, 0.8, "r2", {}),
        ]
        secondary = [
            CourseMatch("c2", "Course 2 Duplicate", None, 0.7, "r2b", {}),
            CourseMatch("c3", "Course 3", None, 0.6, "r3", {}),
        ]

        merged = rag_service._merge_unique_matches(primary, secondary, limit=3)

        assert [m.course_id for m in merged] == ["c1", "c2", "c3"]


class TestRAGServiceRetrieval:
    """Integration-style tests for RAG retrieval."""

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_retrieve_recommendations_returns_rag_result(self, mock_session):
        """Test retrieve returns a RAGResult with matches."""
        from src.domain.services.rag import RAGResult

        service = RAGService(mock_session)

        # Mock loading courses
        with patch.object(
            service,
            "_load_courses",
            return_value=[
                {
                    "course_id": "1",
                    "course_title": "Python Basics",
                    "subject": "Programming",
                    "url": "http://test.com/1",
                },
                {
                    "course_id": "2",
                    "course_title": "Java Advanced",
                    "subject": "Programming",
                    "url": "http://test.com/2",
                },
            ],
        ):
            result = await service.retrieve_recommendations(
                assessment_id="test-123",
                role_slug="backend-engineer",
                top_k=5,
            )

            assert isinstance(result, RAGResult)
            assert isinstance(result.matches, list)

    @pytest.mark.asyncio
    async def test_retrieve_recommendations_respects_top_k(self, mock_session):
        """Test retrieve returns at most top_k recommendations."""
        service = RAGService(mock_session)

        # Mock many courses
        mock_courses = [
            {
                "course_id": str(i),
                "course_title": f"Python Course {i}",
                "subject": "Programming",
                "url": f"http://test.com/{i}",
            }
            for i in range(100)
        ]

        with patch.object(service, "_load_courses", return_value=mock_courses):
            result = await service.retrieve_recommendations(
                assessment_id="test-123",
                role_slug="backend-engineer",
                top_k=5,
            )

            assert len(result.matches) <= 5


class TestRAGServiceFallback:
    """Tests for RAG fallback behavior."""

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_empty_courses_returns_fallback(self, mock_session):
        """Test fallback when no courses loaded."""
        from src.domain.services.rag import RAGResult

        service = RAGService(mock_session)

        with patch.object(service, "_load_courses", return_value=[]):
            result = await service.retrieve_recommendations(
                assessment_id="test-123",
                role_slug="backend-engineer",
                top_k=5,
            )

            # Should return RAGResult (possibly with fallback/degraded)
            assert isinstance(result, RAGResult)

    @pytest.mark.asyncio
    async def test_no_matches_returns_degraded(self, mock_session):
        """Test degraded flag when no matching courses found."""
        service = RAGService(mock_session)

        # Courses with no relevant keywords
        with patch.object(
            service,
            "_load_courses",
            return_value=[
                {
                    "course_id": "1",
                    "course_title": "Cooking 101",
                    "subject": "Lifestyle",
                    "url": "http://test.com/1",
                },
            ],
        ):
            result = await service.retrieve_recommendations(
                assessment_id="test-123",
                role_slug="backend-engineer",
                top_k=5,
            )

            # Should be degraded since no matches
            assert result.degraded is True

    @pytest.mark.asyncio
    async def test_no_matches_without_fallback_returns_empty_non_degraded(self, mock_session):
        """No-fallback mode should return empty results without degraded flag."""
        service = RAGService(mock_session)

        with patch.object(
            service,
            "_load_courses",
            return_value=[
                {
                    "course_id": "1",
                    "course_title": "Cooking 101",
                    "subject": "Lifestyle",
                    "url": "http://test.com/1",
                },
            ],
        ):
            result = await service.retrieve_recommendations(
                assessment_id="test-123",
                role_slug="backend-engineer",
                top_k=5,
                enable_fallback=False,
            )

            assert result.degraded is False
            assert result.matches == []
