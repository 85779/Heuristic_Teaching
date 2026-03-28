"""Node 2a: Dimension Router - R/M 二元分流"""

import json
import os
from typing import Optional, List, Dict, Any

from app.infrastructure.llm.dashscope_client import DashScopeClient
from app.infrastructure.llm.base_client import Message

from ..models import (
    DimensionResult,
    DimensionEnum,
    InterventionRecord,
    BreakpointLocation,
)
from .prompts import DIMENSION_ROUTER_PROMPT, BREAKPOINT_TYPE_HINTS


class DimensionRouter:
    """Node 2a: 维度分流

    判断学生困难属于 Resource 还是 Metacognitive。
    """

    def __init__(self, llm_client: Optional[DashScopeClient] = None):
        """Initialize the dimension router.

        Args:
            llm_client: DashScope LLM client (optional, will create if None)
        """
        self._llm_client = llm_client

    def _get_llm_client(self) -> DashScopeClient:
        """Get or create LLM client."""
        if self._llm_client is None:
            api_key = os.getenv("DASHSCOPE_API_KEY")
            if not api_key:
                raise ValueError("DASHSCOPE_API_KEY not set")
            model = os.getenv("INTERVENTION_MODEL", "qwen-turbo")
            self._llm_client = DashScopeClient(api_key=api_key, model=model)
        return self._llm_client

    async def route(
        self,
        student_input: str,
        expected_step: str,
        breakpoint_type: str,
        intervention_memory: Optional[List[InterventionRecord]] = None,
        problem_context: str = "",
    ) -> DimensionResult:
        """判断学生困难属于 Resource 还是 Metacognitive。

        Args:
            student_input: 学生当前提交的步骤
            expected_step: 期望的下一步内容
            breakpoint_type: 断点类型 (MISSING_STEP / WRONG_DIRECTION / INCOMPLETE_STEP / STUCK)
            intervention_memory: 历史干预记录（可选，Node 2a通常不需要）
            problem_context: 题目上下文

        Returns:
            DimensionResult: 包含 dimension, confidence, reasoning
        """
        # 构建 memory summary（如果需要）
        memory_summary = ""
        if intervention_memory and len(intervention_memory) > 0:
            recent = intervention_memory[-3:]  # 最近3轮
            memory_summary = "\n历史干预记录（近3轮）：\n"
            for r in recent:
                student_response_val = r.student_response
                if hasattr(student_response_val, 'value'):
                    student_response_val = student_response_val.value
                memory_summary += f"- 第{r.turn}轮: {r.prompt_level}, 学生反馈: {student_response_val}\n"

        # 构建 prompt
        prompt = DIMENSION_ROUTER_PROMPT.format(
            problem_context=problem_context or "（无）",
            expected_step_content=expected_step or "（无）",
            student_current_input=student_input or "（空白）",
            breakpoint_type=breakpoint_type or "UNKNOWN",
        )

        # 添加断点类型提示
        prompt += BREAKPOINT_TYPE_HINTS

        if memory_summary:
            prompt += memory_summary

        # 调用 LLM
        llm_client = self._get_llm_client()
        response = await llm_client.chat(
            messages=[Message(role="user", content=prompt)],
            temperature=0.3,  # 低温度，更稳定的分类
            max_tokens=512,
        )

        # 解析 JSON 响应
        try:
            # 尝试提取 JSON
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            if response_clean.startswith("```"):
                response_clean = response_clean[3:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]

            data = json.loads(response_clean.strip())

            dimension_str = data.get("dimension", "Resource")
            if dimension_str == "Metacognitive":
                dimension = DimensionEnum.METACOGNITIVE
            else:
                dimension = DimensionEnum.RESOURCE

            confidence = float(data.get("confidence", 0.5))
            reasoning = data.get("reasoning", "")

            return DimensionResult(
                dimension=dimension,
                confidence=confidence,
                reasoning=reasoning,
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # 解析失败，默认返回 Resource
            return DimensionResult(
                dimension=DimensionEnum.RESOURCE,
                confidence=0.0,
                reasoning=f"LLM响应解析失败: {str(e)[:100]}",
            )

    async def close(self) -> None:
        """Close resources."""
        if self._llm_client is not None:
            await self._llm_client.close()
            self._llm_client = None
