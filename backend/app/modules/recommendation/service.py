"""Recommendation service - main orchestration service for Module 3."""

import logging
import time
from typing import Optional, TYPE_CHECKING
from app.modules.recommendation.models import (
    RecommendResponse,
    StudentProfile,
    TriggerEvent,
    TriggerOutcome,
)
from app.modules.recommendation.knowledge_base.knowledge_api import KnowledgeBaseAPI
from app.modules.recommendation.retriever.knowledge_anchor_retriever import KnowledgeAnchorRetriever
from app.modules.recommendation.generator.problem_generator import ProblemGenerator
from app.modules.recommendation.generator.fallback_generator import FallbackGenerator
from app.modules.recommendation.generator.prompt_templates import ProblemPromptTemplates  # noqa: E402
from app.modules.recommendation.generator.problem_validator import ProblemValidator  # noqa: E402
from app.modules.recommendation.scorer.difficulty_scorer import DifficultyScorer
from app.infrastructure.llm.dashscope_client import DashScopeClient

if TYPE_CHECKING:
    from app.modules.student_model.service import ProfileManager

logger = logging.getLogger(__name__)


class RecommendationService:
    """Main recommendation service orchestrating all components.

    Flow:
    1. Load student profile (from Module 4 when available, mock otherwise)
    2. Retrieve knowledge anchor based on profile
    3. Calculate target difficulty
    4. Generate problem (LLM or Fallback)
    5. Build recommendation reason
    6. Return response
    """

    def __init__(
        self,
        kb_api: KnowledgeBaseAPI,
        anchor_retriever: KnowledgeAnchorRetriever,
        generator: ProblemGenerator,
        fallback: FallbackGenerator,
        difficulty_scorer: DifficultyScorer,
        llm_client: DashScopeClient,
        profile_manager: Optional["ProfileManager"] = None,
    ):
        """Initialize the service with all dependencies.

        Args:
            kb_api: Knowledge base API for querying KPs.
            anchor_retriever: Anchor retriever for profile-based retrieval.
            generator: LLM-based problem generator.
            fallback: Fallback generator for LLM failures.
            difficulty_scorer: Difficulty calculator.
            llm_client: DashScope LLM client.
            profile_manager: Optional Module 4 profile manager.
        """
        self._kb = kb_api
        self._retriever = anchor_retriever
        self._generator = generator
        self._fallback = fallback
        self._scorer = difficulty_scorer
        self._llm = llm_client
        self._profile_manager = profile_manager

    async def recommend(
        self,
        student_id: str,
        trigger: TriggerEvent,
    ) -> RecommendResponse:
        """Generate a personalized problem recommendation.
        
        Args:
            student_id: Student identifier.
            trigger: Trigger event with context.
            
        Returns:
            RecommendResponse with generated problem and metadata.
        """
        start_time = time.time()

        # Step 1: Load student profile (mock when Module 4 unavailable)
        profile = await self._load_profile(student_id)

        # Step 2: Retrieve knowledge anchor
        anchor = await self._retriever.retrieve(
            profile=profile,
            current_kps=trigger.current_problem_kps,
            current_method=trigger.current_method,
        )

        # Step 3: Calculate target difficulty
        target_diff = self._scorer.calculate_target(
            current=trigger.current_difficulty,
            outcome=trigger.outcome,
        )

        # Step 4: Generate problem (LLM or Fallback)
        result = await self._generator.generate(
            anchor=anchor,
            target_difficulty=target_diff,
            max_retries=2,
        )

        if result.success and result.problem:
            problem = result.problem
            mode = "LLM_GENERATED"
        else:
            # Fallback when LLM fails
            error_reason = result.error or "unknown"
            problem = await self._fallback.generate(
                anchor=anchor,
                target_difficulty=target_diff,
                reason=error_reason,
            )
            mode = "FALLBACK"

        # Step 5: Build recommendation reason
        problem.why_recommended = self._build_why_recommended(problem, anchor)

        # Step 6: Save to history for dedup and feedback
        try:
            from app.modules.recommendation.history_repo import RecommendationHistoryRepo
            repo = RecommendationHistoryRepo()
            await repo.save(
                student_id=student_id,
                problem=problem,
                anchor={
                    "type": anchor.anchor_type.value,
                    "kps": [kp.kp_id for kp in anchor.target_kps],
                },
                mode=mode,
            )
        except Exception:
            logger.exception("Failed to save recommendation history")

        # Step 7: Build response
        elapsed_ms = int((time.time() - start_time) * 1000)

        return RecommendResponse(
            success=True,
            recommendation=problem,
            metadata={
                "generation_time_ms": elapsed_ms,
                "generation_mode": mode,
                "knowledge_anchor": {
                    "type": anchor.anchor_type.value,
                    "kps": [kp.kp_id for kp in anchor.target_kps],
                    "goal": anchor.generation_goal,
                },
                "target_difficulty": target_diff,
            },
            error=None,
        )

    async def _load_profile(self, student_id: str) -> StudentProfile:
        """Load student profile from Module 4, or fall back to mock.

        Args:
            student_id: Student identifier.

        Returns:
            StudentProfile with real or mock data.
        """
        # Try Module 4 ProfileManager first
        if self._profile_manager:
            try:
                profile = await self._profile_manager.get_profile(student_id)
                all_kps = await self._kb.get_random_kps(10)
                mastered_kps = [
                    r.problem_id for r in profile.intervention_history
                    if r.outcome == "SOLVED"
                ][:10]
                weak_kps = [
                    kp for kp in all_kps if kp not in mastered_kps
                ][:5]
                return StudentProfile(
                    student_id=student_id,
                    dimension_ratio=profile.dimension_ratio,
                    recent_problems=[],
                    weak_kps=weak_kps,
                    mastered_kps=mastered_kps,
                    recent_methods=[],
                )
            except Exception:
                logger.exception("Failed to load profile from Module 4, falling back to mock")

        # Fallback: random weak KPs for demo
        all_kps = await self._kb.get_random_kps(10)
        return StudentProfile(
            student_id=student_id,
            dimension_ratio=0.5,
            recent_problems=[],
            weak_kps=all_kps[:5],
            mastered_kps=[],
            recent_methods=[],
        )

    def _build_why_recommended(
        self,
        problem,
        anchor,
    ) -> str:
        """Build human-readable recommendation reason.
        
        Args:
            problem: The generated problem.
            anchor: The knowledge anchor used.
            
        Returns:
            Recommendation reason string.
        """
        kp_names = [kp.name for kp in anchor.target_kps[:2]]
        kp_str = "、".join(kp_names) if kp_names else "相关知识点"
        
        anchor_descriptions = {
            "SAME_KP": f"继续巩固 {kp_str}，强化基础",
            "VARIATION": f"练习 {kp_str} 的变式，拓宽思路",
            "BALANCED": f"综合练习 {kp_str}，查漏补缺",
        }
        
        base = anchor_descriptions.get(anchor.anchor_type.value, f"练习 {kp_str}")
        
        if problem.method_used:
            base += f"，运用【{problem.method_used}】"
        
        return base