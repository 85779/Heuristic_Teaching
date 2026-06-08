"""Student profile MongoDB repository."""

import logging
from typing import Optional
from app.infrastructure.database.mongodb import get_mongodb
from app.modules.student_model.models import StudentProfile

logger = logging.getLogger(__name__)


class StudentProfileRepository:
    """MongoDB access for student profiles with auto-connect."""

    COLLECTION = "students"

    async def _db(self):
        mongodb = get_mongodb()
        if not mongodb.is_connected:
            try:
                await mongodb.connect()
            except Exception:
                raise RuntimeError("MongoDB unavailable")
        return mongodb.database

    async def get(self, student_id: str) -> Optional[StudentProfile]:
        try:
            db = await self._db()
            doc = await db[self.COLLECTION].find_one({"student_id": student_id})
            if doc is None:
                return None
            doc.pop("_id", None)
            return StudentProfile(**doc)
        except Exception:
            logger.warning(f"MongoDB get failed for {student_id}")
            return None

    async def upsert(self, profile: StudentProfile) -> StudentProfile:
        profile.updated_at = __import__("datetime").datetime.now(tz=__import__("datetime").timezone.utc)
        try:
            db = await self._db()
            data = profile.model_dump(mode="json")
            await db[self.COLLECTION].update_one(
                {"student_id": profile.student_id},
                {"$set": data},
                upsert=True,
            )
        except Exception:
            logger.warning("MongoDB upsert failed, using memory only")
        return profile

    async def ensure_indexes(self) -> None:
        try:
            db = await self._db()
            await db[self.COLLECTION].create_index("student_id", unique=True)
            await db[self.COLLECTION].create_index("dimension_ratio")
            await db[self.COLLECTION].create_index("updated_at")
        except Exception:
            pass
