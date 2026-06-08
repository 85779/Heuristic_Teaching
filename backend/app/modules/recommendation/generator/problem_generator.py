"""Problem generator using LLM.

Generates math problems based on knowledge anchors using DashScope LLM.
"""

import json
import uuid
from typing import Optional, Any
from app.infrastructure.llm.base_client import Message
from app.modules.recommendation.models import (
    GeneratedProblem,
    GenerationResult,
    KnowledgeAnchor,
    ValidationResult,
)
from app.modules.recommendation.generator.prompt_templates import ProblemPromptTemplates  # noqa: E402
from app.modules.recommendation.generator.problem_validator import ProblemValidator  # noqa: E402


class ProblemGenerator:
    """LLM-based problem generator.
    
    Takes a KnowledgeAnchor and target difficulty, generates a problem
    via LLM, validates it, and returns a GeneratedProblem.
    """

    DEFAULT_MODEL = "qwen-turbo"

    def __init__(
        self,
        llm_client: Any,
        prompt_templates: Optional[ProblemPromptTemplates] = None,
        validator: Optional[ProblemValidator] = None,
        model: Optional[str] = None,
    ):
        """Initialize the generator.
        
        Args:
            llm_client: DashScopeClient or compatible LLM client.
            prompt_templates: Prompt template builder.
            validator: Problem validator.
            model: Model name for LLM calls.
        """
        self._llm = llm_client
        self._templates = prompt_templates or ProblemPromptTemplates()
        self._validator = validator or ProblemValidator()
        self._model = model or self.DEFAULT_MODEL

    async def generate(
        self,
        anchor: KnowledgeAnchor,
        target_difficulty: int = 3,
        max_retries: int = 2,
    ) -> GenerationResult:
        """Generate a problem based on knowledge anchor.
        
        Args:
            anchor: Knowledge anchor with target KPs and methods.
            target_difficulty: Target difficulty 1-5.
            max_retries: Maximum number of generation attempts.
            
        Returns:
            GenerationResult with GeneratedProblem or error.
        """
        if not anchor.target_kps:
            return GenerationResult(
                success=False,
                problem=None,
                error="锚点中没有目标知识点，无法生成题目",
            )

        for attempt in range(max_retries + 1):
            try:
                # Build prompt
                prompt = self._templates.build_generation_prompt(
                    anchor=anchor,
                    target_difficulty=target_difficulty,
                )

                # Call LLM via chat() method (DashScopeClient interface)
                raw_output = await self._llm.chat(
                    messages=[Message(role="user", content=prompt)],
                    model=self._model,
                    temperature=0.8,
                    max_tokens=1024,
                    response_format={"type": "json_object"},
                )
                raw_output = raw_output.strip()

                # Validate
                validation = self._validator.validate(raw_output)

                if validation.passed:
                    # Parse and build GeneratedProblem
                    json_str = self._validator._extract_json(raw_output)
                    data = json.loads(json_str)

                    problem = GeneratedProblem(
                        generated_id=f"gen_{uuid.uuid4().hex[:8]}",
                        problem_text=data["problem_text"],
                        answer=data["answer"],
                        solution_hint=data["solution_hint"],
                        difficulty=data.get("difficulty_rating", target_difficulty),
                        related_kps=data.get("related_kps", []),
                        method_used=data.get("method_used", ""),
                        why_recommended=data.get("why_recommended", anchor.generation_goal),
                        generation_reasoning=data.get("generation_reasoning", ""),
                    )
                    return GenerationResult(success=True, problem=problem, error=None)

                if attempt < max_retries:
                    # Retry with feedback
                    continue

                return GenerationResult(
                    success=False,
                    problem=None,
                    error=f"生成校验失败: {'; '.join(validation.errors)}",
                )

            except Exception as e:
                if attempt < max_retries:
                    continue
                return GenerationResult(
                    success=False,
                    problem=None,
                    error=f"生成过程异常: {str(e)}",
                )

        return GenerationResult(
            success=False,
            problem=None,
            error="达到最大重试次数仍未成功",
        )