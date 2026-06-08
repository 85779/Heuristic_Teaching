"""Tests for DifficultyScorer."""

import pytest
from app.modules.recommendation.scorer.difficulty_scorer import DifficultyScorer
from app.modules.recommendation.models import TriggerOutcome


class TestDifficultyScorer:
    """Test suite for DifficultyScorer."""

    def test_max_escalation_lowers_difficulty(self, difficulty_scorer):
        """MAX_ESCALATION reduces difficulty by 1."""
        assert difficulty_scorer.calculate_target(3, TriggerOutcome.MAX_ESCALATION) == 2
        assert difficulty_scorer.calculate_target(2, TriggerOutcome.MAX_ESCALATION) == 1
        assert difficulty_scorer.calculate_target(1, TriggerOutcome.MAX_ESCALATION) == 1  # min 1

    def test_abandoned_keeps_difficulty(self, difficulty_scorer):
        """ABANDONED keeps difficulty the same."""
        assert difficulty_scorer.calculate_target(3, TriggerOutcome.ABANDONED) == 3
        assert difficulty_scorer.calculate_target(1, TriggerOutcome.ABANDONED) == 1

    def test_solved_increases_difficulty(self, difficulty_scorer):
        """SOLVED increases difficulty by 1."""
        assert difficulty_scorer.calculate_target(3, TriggerOutcome.SOLVED) == 4
        assert difficulty_scorer.calculate_target(5, TriggerOutcome.SOLVED) == 5  # max 5
        assert difficulty_scorer.calculate_target(4, TriggerOutcome.SOLVED) == 5

    def test_manual_increases_difficulty(self, difficulty_scorer):
        """MANUAL increases difficulty by 1."""
        assert difficulty_scorer.calculate_target(2, TriggerOutcome.MANUAL) == 3

    def test_difficulty_bounds(self, difficulty_scorer):
        """Difficulty stays within 1-5 bounds."""
        assert difficulty_scorer.calculate_target(1, TriggerOutcome.MAX_ESCALATION) >= 1
        assert difficulty_scorer.calculate_target(5, TriggerOutcome.SOLVED) <= 5