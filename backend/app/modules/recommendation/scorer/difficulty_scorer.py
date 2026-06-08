"""Difficulty scorer for calculating target problem difficulty."""

from app.modules.recommendation.models import TriggerOutcome


class DifficultyScorer:
    """Scorer for calculating target difficulty based on trigger outcome.
    
    Strategy:
    - MAX_ESCALATION: student struggled → lower difficulty by 1
    - ABANDONED: student gave up → keep same difficulty  
    - SOLVED / MANUAL: student succeeded → increase difficulty by 1
    """

    def calculate_target(self, current: int, outcome: TriggerOutcome) -> int:
        """Calculate target difficulty based on trigger outcome.
        
        Args:
            current: Current problem difficulty (1-5).
            outcome: The trigger outcome from the session.
            
        Returns:
            Target difficulty (1-5), clamped to valid range.
        """
        if outcome == TriggerOutcome.MAX_ESCALATION:
            # Student struggled → easier problem
            return max(current - 1, 1)
        elif outcome == TriggerOutcome.ABANDONED:
            # Student gave up → same difficulty
            return max(current, 1)
        else:
            # SOLVED or MANUAL → slightly harder
            return min(current + 1, 5)