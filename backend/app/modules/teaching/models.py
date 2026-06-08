"""Teaching strategy data models."""

from pydantic import BaseModel, Field


class TeachingStrategy(BaseModel):
    """Teaching strategy configuration based on student profile."""

    student_id: str
    lecture_ratio: float = 0.3   # 讲授比例
    practice_ratio: float = 0.5  # 练习比例
    discussion_ratio: float = 0.2  # 讨论比例

    dimension_ratio: float = 0.5
    strategy_label: str = "balanced"
    description: str = ""


class StrategyRequest(BaseModel):
    """Request for strategy recommendation."""

    student_id: str
