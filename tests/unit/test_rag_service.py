"""
Unit tests for Story 3.1: RAG Retrieval Service.

Tests the keyword-based course recommendation system.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from src.domain.services.rag import RAGService


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
