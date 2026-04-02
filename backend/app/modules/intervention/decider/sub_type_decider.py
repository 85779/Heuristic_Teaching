"""Node 2b: Sub-type Decider - 等级决策 + 升级策略"""

from __future__ import annotations

import json
import os
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.infrastructure.llm.dashscope_client import DashScopeClient
from app.infrastructure.llm.base_client import Message

from ..models import (
    DimensionEnum,
    PromptLevelEnum,
    SubTypeResult,
    InterventionRecord,
    EscalationDecision,
    EscalationAction,
    FrontendSignalEnum,
)
from .prompts import (
    RESOURCE_DECIDER_PROMPT,
    METACOGNITIVE_DECIDER_PROMPT,
    RESOURCE_LEVELS,
    METACOGNITIVE_LEVELS,
    RESOURCE_NEXT_LEVEL,
    METACOGNITIVE_NEXT_LEVEL,
    RESOURCE_MAX_LEVEL,
    METACOGNITIVE_MAX_LEVEL,
)


class SubTypeDecider:
    """Node 2b: 等级决策

    决定具体干预等级（R1-R4 或 M1-M5）和升级策略。
    """

    def __init__(self, llm_client: Optional[DashScopeClient] = None):
        """Initialize the sub-type decider.

        Args:
            llm_client: DashScope LLM client (optional, will create if None)
        """
        self._llm_client = llm_client

    def _get_llm_client(self) -> "DashScopeClient":
        """Get or create LLM client."""
        if self._llm_client is None:
            from app.infrastructure.llm.dashscope_client import DashScopeClient
            api_key = os.getenv("DASHSCOPE_API_KEY")
            if not api_key:
                raise ValueError("DASHSCOPE_API_KEY not set")
            model = os.getenv("INTERVENTION_MODEL", "qwen-turbo")
            self._llm_client = DashScopeClient(api_key=api_key, model=model)
        return self._llm_client

    def _build_memory_summary(
        self,
        memory: List[InterventionRecord],
        max_turns: int = 3
    ) -> str:
        """构建干预记忆摘要"""
        if not memory:
            return "无历史干预记录"

        recent = memory[-max_turns:]
        summary = f"近{len(recent)}轮干预记录：\n"

        for r in recent:
            student_response_val = r.student_response
            if hasattr(student_response_val, 'value'):
                student_response_val = student_response_val.value
            summary += f"- 第{r.turn}轮 ({r.prompt_level}): 学生反馈={student_response_val}\n"

            # Handle qa_history as either dict or QaHistory object
            qa_history = r.qa_history
            if isinstance(qa_history, dict):
                student_q = qa_history.get("student_q", "")
            else:
                student_q = getattr(qa_history, "student_q", "")

            if student_q:
                q_preview = student_q[:30] + "..." if len(student_q) > 30 else student_q
                summary += f"  学生说: {q_preview}\n"

        # 如果有更早的记录
        if len(memory) > max_turns:
            old = memory[:-max_turns]
            old_levels = [r.prompt_level for r in old]
            old_responses = [r.student_response.value for r in old]
            summary += f"\n早期{len(old)}轮：尝试了 {', '.join(set(old_levels))}，"
            if all(r == "not_progressed" for r in old_responses):
                summary += "均未推进。"
            elif any(r == "accepted" for r in old_responses):
                summary += "有推进。"
            else:
                summary += "结果混杂。"

        return summary

    async def decide(
        self,
        dimension: DimensionEnum,
        student_input: str,
        expected_step: str,
        intervention_memory: Optional[List[InterventionRecord]] = None,
        frontend_signal: Optional[FrontendSignalEnum] = None,
        current_level: str = "",
        problem_context: str = "",
    ) -> SubTypeResult:
        """决定具体干预等级和升级策略。

        Args:
            dimension: 维度（Resource 或 Metacognitive）
            student_input: 学生当前输入
            expected_step: 期望的下一步
            intervention_memory: 历史干预记录
            frontend_signal: 前端信号（END / ESCALATE）
            current_level: 当前等级（如果是继续干预）
            problem_context: 题目上下文

        Returns:
            SubTypeResult: 包含 sub_type, confidence, reasoning, hint_direction, escalation_decision
        """
        # 构建 memory summary
        memory_summary = self._build_memory_summary(intervention_memory or [])

        # 选择 prompt
        if dimension == DimensionEnum.RESOURCE:
            prompt_template = RESOURCE_DECIDER_PROMPT
        else:
            prompt_template = METACOGNITIVE_DECIDER_PROMPT

        # 填充 prompt
        prompt = prompt_template.format(
            student_input=student_input or "（空白）",
            expected_step=expected_step or "（无）",
            memory_summary=memory_summary,
        )

        # 添加当前等级和前端信号（如果有）
        if current_level:
            prompt += f"\n\n当前等级: {current_level}"
        if frontend_signal:
            frontend_signal_val = frontend_signal
            if hasattr(frontend_signal_val, 'value'):
                frontend_signal_val = frontend_signal_val.value
            prompt += f"\n前端信号: {frontend_signal_val}"

        # 调用 LLM
        llm_client = self._get_llm_client()
        response = await llm_client.chat(
            messages=[Message(role="user", content=prompt)],
            temperature=0.3,
            max_tokens=1024,
        )

        # 解析 JSON 响应
        try:
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            if response_clean.startswith("```"):
                response_clean = response_clean[3:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]

            data = json.loads(response_clean.strip())

            # 解析 sub_type
            sub_type_str = data.get("sub_type", "R1")
            try:
                sub_type = PromptLevelEnum(sub_type_str)
            except ValueError:
                sub_type = PromptLevelEnum.R1

            confidence = float(data.get("confidence", 0.5))
            reasoning = data.get("reasoning", "")
            hint_direction = data.get("hint_direction", "")

            # 解析 escalation_decision
            esc_data = data.get("escalation_decision", {})
            try:
                action_str = esc_data.get("action", "maintain")
                action = EscalationAction(action_str)
            except ValueError:
                action = EscalationAction.MAINTAIN

            escalation_decision = EscalationDecision(
                action=action,
                from_level=esc_data.get("from_level", sub_type_str),
                to_level=esc_data.get("to_level"),
                reasoning=esc_data.get("reasoning", ""),
            )

            return SubTypeResult(
                sub_type=sub_type,
                confidence=confidence,
                reasoning=reasoning,
                hint_direction=hint_direction,
                escalation_decision=escalation_decision,
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # 解析失败，默认返回最低级
            if dimension == DimensionEnum.RESOURCE:
                default_level = PromptLevelEnum.R1
            else:
                default_level = PromptLevelEnum.M1

            return SubTypeResult(
                sub_type=default_level,
                confidence=0.0,
                reasoning=f"LLM响应解析失败: {str(e)[:100]}",
                hint_direction="",
                escalation_decision=EscalationDecision(
                    action=EscalationAction.MAINTAIN,
                    from_level=default_level.value,
                    to_level=None,
                    reasoning="解析失败，默认维持",
                ),
            )

    async def close(self) -> None:
        """Close resources."""
        if self._llm_client is not None:
            await self._llm_client.close()
            self._llm_client = None
