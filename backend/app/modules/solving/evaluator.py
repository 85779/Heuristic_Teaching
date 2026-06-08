"""Evaluator - Evaluates student work correctness using LLM chain verification."""

import json
import logging
import re
from typing import Optional
from .models import (
    EvaluationResult,
    Issue,
    ErrorFeedback,
    DetailLevel,
)

logger = logging.getLogger(__name__)

# Step 1: Generate correct answer (no student context)
REFERENCE_PROMPT = """你是高中数学老师。请解出这道题的正确答案。

## 题目
{problem}

## 要求
直接给出完整的解题过程和最终答案。不需要解释概念，只要算式和结果。"""

# Step 2: Compare student work against reference answer
COMPARE_PROMPT = """你是高中数学老师。对比学生的答案和标准答案，判断学生是否做对了。

## 题目
{problem}

## 标准答案（已验证正确）
{reference}

## 学生作答
{student_work}

## 判断规则（严格执行）
1. **先看最终答案**：学生的最终答案与标准答案是否等价？
   - 数值：容许 ±0.01 误差
   - 表达式：代数等价即算对（如 x+2 和 2+x）
   - 集合/区间：元素完全一致即算对
2. **如果最终答案对** → is_correct=true。即使中间步骤不标准或跳跃，只要最终结果对就算对。
3. **如果最终答案错** → is_correct=false。找出第一步出错的位置。
4. **立体几何/向量**：如果学生通过坐标法得到正确答案，即使方法不是最简也算对。

## 输出格式（严格JSON）
{{
  "is_correct": true/false,
  "confidence": 0.0-1.0,
  "can_continue": true/false,
  "error_type": "无/概念错误/计算错误/遗漏错误/逻辑错误",
  "breakpoint_step": null 或 步骤编号,
  "issues": [
    {{
      "step": 步骤编号,
      "description": "问题描述",
      "severity": "error/warning/info",
      "location": "位置"
    }}
  ]
}}"""


class Evaluator:
    """Evaluator for assessing student solution correctness.

    Uses chain verification: first generates the correct answer,
    then compares the student's work against it step-by-step.
    Falls back to rule-based heuristics when LLM is unavailable.
    """

    def __init__(self, llm_client=None):
        self._llm_client = llm_client

    async def evaluate_student_work(
        self,
        problem: str,
        student_work: str,
        detail_level: DetailLevel = DetailLevel.SIMPLE,
    ) -> EvaluationResult:
        if not student_work or not student_work.strip():
            return EvaluationResult(
                is_correct=False,
                confidence=0.0,
                issues=[Issue(description="学生尚未开始作答", severity="info", location="")],
                can_continue=True,
                breakpoint_step=None,
            )

        if self._llm_client:
            try:
                return await self._evaluate_with_llm(problem, student_work)
            except Exception:
                logger.exception("LLM evaluation failed, falling back to rules")
        return self._evaluate_with_rules(problem, student_work)

    def _evaluate_with_rules(
        self, problem: str, student_work: str,
    ) -> EvaluationResult:
        has_math = bool(re.search(r"\$|\\frac|\\sum|\\int|\\lim", student_work))
        has_structure = student_work.count("\n") >= 1
        if has_math and has_structure:
            return EvaluationResult(
                is_correct=True, confidence=0.3,
                issues=[Issue(description="规则评估无法确定正确性，需LLM复核", severity="info", location="")],
                can_continue=True, breakpoint_step=None,
            )
        return EvaluationResult(
            is_correct=True, confidence=0.1,
            issues=[Issue(description="内容过短，无法评估", severity="warning", location="")],
            can_continue=True, breakpoint_step=None,
        )

    async def _evaluate_with_llm(
        self, problem: str, student_work: str,
    ) -> EvaluationResult:
        """Chain verification: generate correct answer, then compare."""
        from app.infrastructure.llm.base_client import Message

        # Step 1: Generate correct answer
        ref_prompt = REFERENCE_PROMPT.format(problem=problem)
        ref_response = await self._llm_client.chat(
            messages=[
                Message(role="system", content="你是高中数学老师。只输出解题过程和答案。"),
                Message(role="user", content=ref_prompt),
            ],
            temperature=0.1,
            max_tokens=512,
        )

        # Step 2: Compare student work against reference
        compare_prompt = COMPARE_PROMPT.format(
            problem=problem,
            reference=ref_response,
            student_work=student_work,
        )
        compare_response = await self._llm_client.chat(
            messages=[
                Message(role="system", content="你是高中数学老师。严格对比学生答案和标准答案，找出所有差异。"),
                Message(role="user", content=compare_prompt),
            ],
            temperature=0.1,
            max_tokens=512,
            response_format={"type": "json_object"},
        )

        data = self._parse_json(compare_response)
        return self._build_result(data)

    def _parse_json(self, text: str) -> dict:
        t = text.strip()
        t = re.sub(r"^```(?:json)?\s*", "", t)
        t = re.sub(r"\s*```$", "", t)
        try:
            return json.loads(t)
        except json.JSONDecodeError:
            return {}

    def _build_result(self, data: dict) -> EvaluationResult:
        issues = []
        for iss in data.get("issues", []):
            issues.append(Issue(
                step=iss.get("step"),
                description=iss.get("description", ""),
                severity=iss.get("severity", "info"),
                location=iss.get("location", ""),
            ))
        confidence = data.get("confidence", 0.5)
        if not isinstance(confidence, (int, float)):
            confidence = 0.5
        confidence = max(0.0, min(float(confidence), 1.0))
        return EvaluationResult(
            is_correct=data.get("is_correct", False),
            confidence=confidence,
            issues=issues,
            can_continue=data.get("can_continue", True),
            breakpoint_step=data.get("breakpoint_step"),
        )

    def create_error_feedback(
        self, evaluation: EvaluationResult, detail_level: DetailLevel = DetailLevel.SIMPLE,
    ) -> ErrorFeedback:
        if evaluation.is_correct:
            return ErrorFeedback(summary="解答正确", issues=[], suggestion="")
        parts, suggestions = [], []
        for issue in evaluation.issues:
            prefix = f"第{issue.step}步: " if issue.step else ""
            parts.append(f"{prefix}{issue.description}")
            if issue.severity == "error":
                suggestions.append(f"检查{issue.location}" if issue.location else "请重新检查该步骤")
        return ErrorFeedback(
            summary="; ".join(parts) if parts else "发现解题错误",
            issues=evaluation.issues,
            suggestion="; ".join(suggestions) if suggestions else "请重新审视解题思路",
        )

    def determine_breakpoint(self, student_work: str) -> Optional[int]:
        step_patterns = [
            r"第([一二三四五六七八九十\d]+)\s*步", r"步骤\s*(\d+)", r"step\s*(\d+)", r"(?:^|\n)\s*(\d+)[.、]\s",
        ]
        last_step = 0
        for pattern in step_patterns:
            for match in re.findall(pattern, student_work, re.IGNORECASE):
                try:
                    num_map = {"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9,"十":10}
                    step = num_map.get(match, int(match))
                    last_step = max(last_step, step)
                except (ValueError, KeyError):
                    pass
        return last_step if last_step > 0 else None
