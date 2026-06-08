"""Recommendation history persistence — MongoDB with in-memory fallback."""

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


class RecommendationHistoryRepo:
    """Stores recommendation history for dedup and feedback tracking."""

    COLLECTION = "recommendation_history"

    async def save(self, student_id: str, problem: dict, anchor: dict, mode: str) -> None:
        """Save a recommendation record."""
        doc = {
            "student_id": student_id,
            "problem_text": getattr(problem, "problem_text", str(problem))[:200],
            "answer": getattr(problem, "answer", ""),
            "difficulty": getattr(problem, "difficulty", 0),
            "related_kps": getattr(problem, "related_kps", []),
            "method_used": getattr(problem, "method_used", ""),
            "anchor_type": anchor.get("type", ""),
            "anchor_kps": anchor.get("kps", []),
            "generation_mode": mode,
            "created_at": datetime.now(timezone.utc),
            "accepted": None,
            "feedback_at": None,
        }
        try:
            from app.infrastructure.database.mongodb import get_mongodb
            db = get_mongodb().database
            await db[self.COLLECTION].insert_one(doc)
        except Exception:
            logger.warning("Failed to persist recommendation, using memory only")

    async def get_recent(self, student_id: str, limit: int = 10) -> list[dict]:
        """Get recent recommendations for a student."""
        try:
            from app.infrastructure.database.mongodb import get_mongodb
            db = get_mongodb().database
            cursor = db[self.COLLECTION].find(
                {"student_id": student_id}
            ).sort("created_at", -1).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception:
            return []

    async def record_feedback(self, student_id: str, generated_id: str, accepted: bool) -> None:
        """Record whether student accepted the recommendation."""
        try:
            from app.infrastructure.database.mongodb import get_mongodb
            db = get_mongodb().database
            await db[self.COLLECTION].update_one(
                {"student_id": student_id, "problem_text": {"$regex": generated_id[:8]}},
                {"$set": {"accepted": accepted, "feedback_at": datetime.now(timezone.utc)}},
            )
        except Exception:
            pass
