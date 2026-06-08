"""Student profile manager — core service for Module 4."""

import logging
from datetime import datetime, timezone
from typing import Optional
from app.modules.student_model.models import (
    StudentProfile,
    InterventionRecord,
    RoutingHint,
)
from app.modules.student_model.repository import StudentProfileRepository

logger = logging.getLogger(__name__)


class ProfileManager:
    """Manages student cognitive profiles.

    Called by Module 2 (write intervention records) and
    Module 3 (read profile for recommendation).
    """

    MAX_HISTORY_SIZE = 50
    COLD_START_THRESHOLD = 3

    def __init__(self, repo: Optional[StudentProfileRepository] = None):
        self._repo = repo or StudentProfileRepository()
        self._memory_cache: dict[str, StudentProfile] = {}

    async def get_profile(self, student_id: str) -> StudentProfile:
        """Get existing profile or create a new one (cold start).

        Falls back to memory cache when MongoDB is unavailable.
        """
        # Check cache first
        if student_id in self._memory_cache:
            return self._memory_cache[student_id]

        try:
            profile = await self._repo.get(student_id)
            if profile:
                self._memory_cache[student_id] = profile
                return profile
        except Exception:
            logger.warning(f"MongoDB query failed for {student_id}, using default")

        # Cold start: create default profile
        return self._create_default(student_id)

    async def update_after_intervention(
        self,
        student_id: str,
        record: InterventionRecord,
    ) -> StudentProfile:
        """Core method: called by Module 2 when an intervention ends.

        Appends the intervention record, recomputes dimension_ratio,
        and persists to MongoDB.
        """
        profile = await self.get_profile(student_id)

        # Append to history (keep only recent MAX_HISTORY_SIZE)
        profile.intervention_history.append(record)
        if len(profile.intervention_history) > self.MAX_HISTORY_SIZE:
            profile.intervention_history = profile.intervention_history[-self.MAX_HISTORY_SIZE:]

        # Update counters
        profile.total_interventions += 1
        if record.outcome == "SOLVED":
            profile.total_solved += 1
        elif record.outcome == "MAX_ESCALATION":
            profile.total_escalation += 1

        # Recompute dimension_ratio and trend
        profile.dimension_ratio = self._compute_dimension_ratio(
            profile.intervention_history
        )
        trend, confidence = self._compute_ratio_trend(profile.intervention_history)
        profile.ratio_trend = trend
        profile.trend_confidence = confidence
        profile.updated_at = datetime.now(timezone.utc)

        # Persist
        try:
            await self._repo.upsert(profile)
            self._memory_cache[student_id] = profile
        except Exception:
            logger.exception(f"Failed to persist profile for {student_id}")
            self._memory_cache[student_id] = profile  # keep in memory

        return profile

    async def get_dimension_ratio(self, student_id: str) -> float:
        """Fast accessor for dimension_ratio."""
        profile = await self.get_profile(student_id)
        return profile.dimension_ratio

    async def get_routing_hint(self, student_id: str) -> RoutingHint:
        """Build routing hint for Module 2 dimension routing.

        Returns hints about which dimension (R vs M) the student
        is biased toward, plus trend information.
        """
        profile = await self.get_profile(student_id)

        is_new = profile.total_interventions < self.COLD_START_THRESHOLD
        ratio = profile.dimension_ratio

        if is_new:
            return RoutingHint(
                student_id=student_id,
                is_new_student=True,
                dimension_ratio=0.5,
                recommended_dimension_hint="新学生，默认RESOURCE维度起步",
                recent_intervention_summary="尚无干预历史",
            )

        # Determine bias
        if ratio > 0.65:
            bias = "R_dominant"
            hint = "学生R型断点偏多，建议METACOGNITIVE维度引导策略思考"
        elif ratio < 0.35:
            bias = "M_dominant"
            hint = "学生M型断点偏多，建议RESOURCE维度补充知识基础"
        else:
            bias = "balanced"
            hint = "维度均衡，可根据题目特征灵活选择"

        # Analyze weak dimensions from recent history
        weak = self._analyze_weak_dimensions(profile.intervention_history)

        # Build summary
        recent = profile.intervention_history[-3:]
        summary_parts = []
        for r in recent:
            summary_parts.append(f"{r.dimension}_{r.level}({r.outcome})")
        summary = " → ".join(summary_parts) if summary_parts else ""

        return RoutingHint(
            student_id=student_id,
            is_new_student=False,
            dimension_ratio=ratio,
            ratio_trend=profile.ratio_trend,
            trend_confidence=profile.trend_confidence,
            weak_dimensions=weak,
            recommended_dimension_hint=hint,
            recent_intervention_summary=summary,
            confidence=min(profile.total_interventions / 10.0, 1.0),
        )

    def _compute_dimension_ratio(
        self, history: list[InterventionRecord]
    ) -> float:
        if len(history) < self.COLD_START_THRESHOLD:
            return 0.5
        r_count = sum(1 for r in history if r.dimension == "RESOURCE")
        return r_count / len(history) if history else 0.5

    def _compute_ratio_trend(
        self, history: list[InterventionRecord], window: int = 10,
    ) -> tuple[str, float]:
        """Compute dimension_ratio trend using simple linear regression.

        Returns (trend_label, confidence).
        """
        if len(history) < 5:
            return "stable", 0.0

        recent = history[-window:]
        values = [1 if r.dimension == "RESOURCE" else 0 for r in recent]
        n = len(values)
        if n < 2:
            return "stable", 0.0

        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        slope = numerator / denominator if denominator != 0 else 0.0

        if slope > 0.1:
            trend = "rising"
        elif slope < -0.1:
            trend = "falling"
        else:
            trend = "stable"

        confidence = min(n / 10.0, 1.0)
        return trend, confidence

    def _create_default(self, student_id: str) -> StudentProfile:
        """Create a default profile for new students."""
        profile = StudentProfile(student_id=student_id)
        self._memory_cache[student_id] = profile
        return profile

    def _analyze_weak_dimensions(self, history: list[InterventionRecord]) -> list[str]:
        """Identify frequently occurring breakpoint levels in recent history."""
        if not history:
            return []

        level_counts: dict[str, int] = {}
        for record in history[-20:]:
            key = f"{record.dimension}_{record.level}"
            level_counts[key] = level_counts.get(key, 0) + 1

        return [
            level for level, count in sorted(
                level_counts.items(), key=lambda x: x[1], reverse=True
            )
            if count > 1
        ][:2]
