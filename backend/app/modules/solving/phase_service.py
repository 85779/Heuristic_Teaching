"""Phase service: orchestrates the 4-phase problem-solving workflow."""

import json
import re
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from app.modules.solving.models import (
    SolvingSession,
    OrientationResult,
    ReconstructionResult,
    TransformationResult,
    VerificationResult,
)
from app.modules.solving.prompts.orientation import OrientationPrompt
from app.modules.solving.prompts.reconstruction import ReconstructionPrompt
from app.modules.solving.prompts.transformation import TransformationPrompt
from app.modules.solving.prompts.verification import VerificationPrompt
from app.infrastructure.llm.base_client import Message

if TYPE_CHECKING:
    from app.infrastructure.llm.dashscope_client import DashScopeClient

SYSTEM_MSG = "你是高中数学老师。带领学生按定向→重构→变换→验证四个阶段系统解题。输出严格的JSON。"


class PhaseService:
    """Orchestrates the 4-phase solving workflow.

    Phases:
      1. Orientation  — understand problem, identify concepts
      2. Reconstruction — break down components, find relationships
      3. Transformation — choose strategies, plan steps
      4. Verification  — validate solution, check correctness
    """

    def __init__(self, llm_client: "DashScopeClient"):
        self._llm = llm_client
        # In-memory session store (production: MongoDB)
        self._sessions: dict[str, dict] = {}

    # ===== Session CRUD =====

    def create_session(self, problem_id: str) -> SolvingSession:
        import uuid
        sid = f"solve_{uuid.uuid4().hex[:8]}"
        session = SolvingSession(
            session_id=sid,
            problem_id=problem_id,
            status="started",
            current_phase="orientation",
        )
        self._sessions[sid] = {
            "session": session,
            "problem": "",
            "orientation": None,
            "reconstruction": None,
            "transformation": None,
            "verification": None,
        }
        return session

    def get_session(self, session_id: str) -> Optional[SolvingSession]:
        data = self._sessions.get(session_id)
        return data["session"] if data else None

    # ===== Phase Execution =====

    async def process_orientation(self, session_id: str, problem: str) -> OrientationResult:
        prompt = OrientationPrompt().get_prompt(problem)
        response = await self._llm.chat(
            messages=[Message(role="system", content=SYSTEM_MSG), Message(role="user", content=prompt)],
            temperature=0.5, max_tokens=512, response_format={"type": "json_object"},
        )
        data = self._parse_json(response)
        result = OrientationResult(
            session_id=session_id,
            understanding=data.get("understanding", ""),
            key_concepts=data.get("key_concepts", []),
            goals=data.get("goals", []),
        )
        self._update_session(session_id, "orientation", result, "reconstruction")
        return result

    async def process_reconstruction(self, session_id: str) -> ReconstructionResult:
        data = self._sessions.get(session_id)
        if not data:
            raise ValueError(f"Session {session_id} not found")
        orientation = data.get("orientation")
        orientation_text = orientation.understanding if orientation else ""

        prompt = ReconstructionPrompt().get_prompt(
            problem=data["problem"], orientation=orientation_text,
        )
        response = await self._llm.chat(
            messages=[Message(role="system", content=SYSTEM_MSG), Message(role="user", content=prompt)],
            temperature=0.5, max_tokens=512, response_format={"type": "json_object"},
        )
        resp = self._parse_json(response)
        result = ReconstructionResult(
            session_id=session_id,
            components=resp.get("components", []),
            relationships=resp.get("relationships", {}),
            breakdown=resp.get("breakdown", ""),
        )
        self._update_session(session_id, "reconstruction", result, "transformation")
        return result

    async def process_transformation(self, session_id: str) -> TransformationResult:
        data = self._sessions.get(session_id)
        if not data:
            raise ValueError(f"Session {session_id} not found")

        prompt = TransformationPrompt().get_prompt(
            problem=data["problem"],
            orientation=data["orientation"].understanding if data["orientation"] else "",
            reconstruction=data["reconstruction"].breakdown if data["reconstruction"] else "",
        )
        response = await self._llm.chat(
            messages=[Message(role="system", content=SYSTEM_MSG), Message(role="user", content=prompt)],
            temperature=0.5, max_tokens=512, response_format={"type": "json_object"},
        )
        resp = self._parse_json(response)
        result = TransformationResult(
            session_id=session_id,
            strategies=resp.get("strategies", []),
            approach=resp.get("approach", ""),
            steps=resp.get("steps", []),
        )
        self._update_session(session_id, "transformation", result, "verification")
        return result

    async def process_verification(self, session_id: str) -> VerificationResult:
        data = self._sessions.get(session_id)
        if not data:
            raise ValueError(f"Session {session_id} not found")

        prompt = VerificationPrompt().get_prompt(
            problem=data["problem"],
            orientation=data["orientation"].understanding if data["orientation"] else "",
            reconstruction=data["reconstruction"].breakdown if data["reconstruction"] else "",
            transformation=data["transformation"].approach if data["transformation"] else "",
        )
        response = await self._llm.chat(
            messages=[Message(role="system", content=SYSTEM_MSG), Message(role="user", content=prompt)],
            temperature=0.5, max_tokens=512, response_format={"type": "json_object"},
        )
        resp = self._parse_json(response)
        result = VerificationResult(
            session_id=session_id,
            is_valid=resp.get("is_valid", True),
            issues=resp.get("issues", []),
            corrections=resp.get("corrections", []),
            confidence=resp.get("confidence", 0.8),
        )
        self._update_session(session_id, "verification", result, "completed")
        return result

    async def complete_session(self, session_id: str) -> SolvingSession:
        data = self._sessions.get(session_id)
        if not data:
            raise ValueError(f"Session {session_id} not found")
        session = data["session"]
        session.status = "completed"
        session.updated_at = datetime.now(timezone.utc)
        return session

    # ===== Helpers =====

    def _update_session(self, session_id: str, phase: str, result, next_phase: str):
        data = self._sessions.get(session_id)
        if data:
            data[phase] = result
            data["session"].current_phase = next_phase
            data["session"].updated_at = datetime.now(timezone.utc)
            if phase == "orientation":
                data["problem"] = getattr(result, 'understanding', '')[:200]

    def _parse_json(self, text: str) -> dict:
        t = text.strip()
        t = re.sub(r"^```(?:json)?\s*", "", t)
        t = re.sub(r"\s*```$", "", t)
        try:
            return json.loads(t)
        except json.JSONDecodeError:
            return {}
