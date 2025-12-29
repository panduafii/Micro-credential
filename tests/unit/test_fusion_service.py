"""
Unit tests for Story 3.2: Fusion Summary & Results Endpoint.

Tests the fusion service and result retrieval.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from src.domain.services.fusion import FusionService, ScoreBreakdown


class TestFusionServiceSummary:
    """Tests for FusionService summary generation."""

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def fusion_service(self, mock_session):
        """Create FusionService instance."""
        return FusionService(mock_session)

    def test_generate_summary_high_score(self, fusion_service):
        """Test summary for high scoring assessment."""
        breakdown = ScoreBreakdown(
            theoretical_score=85.0,
            theoretical_max=100.0,
            theoretical_pct=85.0,
            profile_score=80.0,
            profile_max=100.0,
            profile_pct=80.0,
            essay_score=90.0,
            essay_max=100.0,
            essay_pct=90.0,
            overall_score=255.0,
            overall_pct=85.0,
        )

        summary = fusion_service._generate_summary(
            role_title="Backend Engineer",
            breakdown=breakdown,
            recommendations=[],
            degraded=False,
        )

        # Should be encouraging for high scores
        assert "excellent" in summary.lower()
        assert "85.0%" in summary

    def test_generate_summary_low_score(self, fusion_service):
        """Test summary for low scoring assessment."""
        breakdown = ScoreBreakdown(
            theoretical_score=45.0,
            theoretical_max=100.0,
            theoretical_pct=45.0,
            profile_score=50.0,
            profile_max=100.0,
            profile_pct=50.0,
            essay_score=40.0,
            essay_max=100.0,
            essay_pct=40.0,
            overall_score=135.0,
            overall_pct=45.0,
        )

        summary = fusion_service._generate_summary(
            role_title="Frontend Engineer",
            breakdown=breakdown,
            recommendations=[],
            degraded=False,
        )

        # Should mention areas for development
        assert "development" in summary.lower() or "areas" in summary.lower()

    def test_generate_summary_medium_score(self, fusion_service):
        """Test summary for medium scoring assessment."""
        breakdown = ScoreBreakdown(
            theoretical_score=65.0,
            theoretical_max=100.0,
            theoretical_pct=65.0,
            profile_score=70.0,
            profile_max=100.0,
            profile_pct=70.0,
            essay_score=65.0,
            essay_max=100.0,
            essay_pct=65.0,
            overall_score=200.0,
            overall_pct=66.7,
        )

        summary = fusion_service._generate_summary(
            role_title="Data Scientist",
            breakdown=breakdown,
            recommendations=[],
            degraded=False,
        )

        # Should be balanced - "good" message
        assert "good" in summary.lower()

    def test_generate_summary_includes_breakdown(self, fusion_service):
        """Test summary includes score breakdown section."""
        breakdown = ScoreBreakdown(
            theoretical_score=75.0,
            theoretical_max=100.0,
            theoretical_pct=75.0,
            profile_score=80.0,
            profile_max=100.0,
            profile_pct=80.0,
            essay_score=70.0,
            essay_max=100.0,
            essay_pct=70.0,
            overall_score=225.0,
            overall_pct=75.0,
        )

        summary = fusion_service._generate_summary(
            role_title="DevOps Engineer",
            breakdown=breakdown,
            recommendations=[],
            degraded=False,
        )

        assert "Score Breakdown" in summary
        assert "Technical Knowledge" in summary

    def test_generate_summary_with_degraded_notice(self, fusion_service):
        """Test summary includes degraded mode notice."""
        breakdown = ScoreBreakdown(
            theoretical_score=75.0,
            theoretical_max=100.0,
            theoretical_pct=75.0,
            profile_score=80.0,
            profile_max=100.0,
            profile_pct=80.0,
            essay_score=0.0,
            essay_max=0.0,
            essay_pct=0.0,
            overall_score=155.0,
            overall_pct=77.5,
        )

        summary = fusion_service._generate_summary(
            role_title="Backend Engineer",
            breakdown=breakdown,
            recommendations=[],
            degraded=True,
        )

        assert "limited" in summary.lower() or "constraints" in summary.lower()


class TestFusionServiceScoreBreakdown:
    """Tests for score breakdown calculation."""

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_get_score_breakdown_returns_dataclass(self, mock_session):
        """Test score breakdown returns ScoreBreakdown dataclass."""
        from src.infrastructure.db.models import QuestionType, Score

        # Mock scores
        mock_score1 = MagicMock(spec=Score)
        mock_score1.question_type = QuestionType.THEORETICAL
        mock_score1.score = 80.0
        mock_score1.max_score = 100.0

        mock_score2 = MagicMock(spec=Score)
        mock_score2.question_type = QuestionType.PROFILE
        mock_score2.score = 70.0
        mock_score2.max_score = 100.0

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_score1, mock_score2]
        mock_session.execute.return_value = mock_result

        service = FusionService(mock_session)
        breakdown = await service._get_score_breakdown("test-assessment")

        assert isinstance(breakdown, ScoreBreakdown)
        assert breakdown.theoretical_score == 80.0
        assert breakdown.profile_score == 70.0

    @pytest.mark.asyncio
    async def test_score_breakdown_calculates_percentages(self, mock_session):
        """Test score breakdown calculates correct percentages."""
        from src.infrastructure.db.models import QuestionType, Score

        mock_score = MagicMock(spec=Score)
        mock_score.question_type = QuestionType.THEORETICAL
        mock_score.score = 50.0
        mock_score.max_score = 100.0

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_score]
        mock_session.execute.return_value = mock_result

        service = FusionService(mock_session)
        breakdown = await service._get_score_breakdown("test-assessment")

        assert breakdown.theoretical_pct == 50.0

    @pytest.mark.asyncio
    async def test_score_breakdown_handles_zero_max(self, mock_session):
        """Test score breakdown handles zero max score."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        service = FusionService(mock_session)
        breakdown = await service._get_score_breakdown("test-assessment")

        # Should not divide by zero
        assert breakdown.theoretical_pct == 0
        assert breakdown.overall_pct == 0


class TestFusionServiceGetResult:
    """Tests for result retrieval."""

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_get_result_not_found(self, mock_session):
        """Test get result for non-existent assessment."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        service = FusionService(mock_session)

        from src.domain.services.status import AssessmentNotFoundError

        with pytest.raises(AssessmentNotFoundError):
            await service.get_assessment_result("nonexistent-id", "user-123")

    @pytest.mark.asyncio
    async def test_get_result_not_owned(self, mock_session):
        """Test get result for assessment owned by another user."""
        from src.infrastructure.db.models import Assessment

        mock_assessment = MagicMock(spec=Assessment)
        mock_assessment.id = "test-123"
        mock_assessment.owner_id = "other-user"
        mock_assessment.status = "completed"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_assessment
        mock_session.execute.return_value = mock_result

        service = FusionService(mock_session)

        from src.domain.services.status import AssessmentNotOwnedError

        with pytest.raises(AssessmentNotOwnedError):
            await service.get_assessment_result("test-123", "user-123")
