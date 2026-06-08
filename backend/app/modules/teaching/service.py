"""Teaching strategy selector — Module 5."""

import logging
from typing import Optional, TYPE_CHECKING
from app.modules.teaching.models import TeachingStrategy

if TYPE_CHECKING:
    from app.modules.student_model.service import ProfileManager

logger = logging.getLogger(__name__)


class StrategySelector:
    """Selects teaching strategy based on student cognitive profile.

    Considers:
    - dimension_ratio: R/M bias
    - total_interventions: experience level
    - ratio_trend: whether student is improving or worsening
    """

    def __init__(self, profile_manager: Optional["ProfileManager"] = None):
        self._profile_manager = profile_manager

    async def select_strategy(self, student_id: str) -> TeachingStrategy:
        ratio = 0.5
        interventions = 0
        trend = "stable"

        if self._profile_manager:
            try:
                profile = await self._profile_manager.get_profile(student_id)
                ratio = profile.dimension_ratio
                interventions = profile.total_interventions
                trend = profile.ratio_trend
            except Exception:
                logger.exception("Failed to get profile, using defaults")

        # Determine experience level
        if interventions < 3:
            experience = "new"
        elif interventions < 10:
            experience = "learning"
        else:
            experience = "experienced"

        # Base strategy on dimension_ratio
        if ratio > 0.65:
            # R-dominant: knowledge gaps → more lecture, less discussion
            if trend == "rising":
                # Getting worse — urgent intervention needed
                strategy = TeachingStrategy(
                    student_id=student_id,
                    lecture_ratio=0.45, practice_ratio=0.40, discussion_ratio=0.15,
                    dimension_ratio=ratio,
                    strategy_label="R_dominant_worsening",
                    description="知识缺口持续扩大，需要加强讲授建立基础，配合针对性练习",
                )
            else:
                strategy = TeachingStrategy(
                    student_id=student_id,
                    lecture_ratio=0.35, practice_ratio=0.45, discussion_ratio=0.20,
                    dimension_ratio=ratio,
                    strategy_label="R_dominant",
                    description="知识缺口明显，以讲授+练习为主帮助建立知识框架",
                )
        elif ratio < 0.35:
            # M-dominant: strategy gaps → more discussion, less lecture
            if trend == "falling":
                strategy = TeachingStrategy(
                    student_id=student_id,
                    lecture_ratio=0.20, practice_ratio=0.40, discussion_ratio=0.40,
                    dimension_ratio=ratio,
                    strategy_label="M_dominant_improving",
                    description="策略能力正在恢复，保持讨论和反思为主的训练",
                )
            else:
                strategy = TeachingStrategy(
                    student_id=student_id,
                    lecture_ratio=0.20, practice_ratio=0.35, discussion_ratio=0.45,
                    dimension_ratio=ratio,
                    strategy_label="M_dominant",
                    description="策略调用能力弱，通过讨论和反思引导元认知训练",
                )
        else:
            # Balanced
            strategy = TeachingStrategy(
                student_id=student_id,
                lecture_ratio=0.30, practice_ratio=0.50, discussion_ratio=0.20,
                dimension_ratio=ratio,
                strategy_label="balanced",
                description="维度均衡，以练习为主配合适度讲授",
            )

        # Adjust for experience
        if experience == "new":
            strategy.lecture_ratio = min(strategy.lecture_ratio + 0.05, 0.50)
            strategy.practice_ratio = max(strategy.practice_ratio - 0.05, 0.30)
            strategy.description += "（新学生，适当增加引导）"
        elif experience == "experienced":
            strategy.lecture_ratio = max(strategy.lecture_ratio - 0.05, 0.15)
            strategy.practice_ratio = min(strategy.practice_ratio + 0.05, 0.55)
            strategy.description += "（有经验学生，增加自主练习）"

        return strategy
