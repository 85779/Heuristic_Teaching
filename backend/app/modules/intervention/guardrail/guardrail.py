"""Node 5: Output Guardrail - 输出审查"""

from __future__ import annotations

import json
import os
import re
from typing import Optional, List, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from app.infrastructure.llm.dashscope_client import DashScopeClient
from app.infrastructure.llm.base_client import Message

from .prompts import RULES, build_guardrail_prompt


@dataclass
class GuardrailResult:
    """Guardrail 检查结果"""
    passed: bool
    reason: str
    violations: List[str]
    revised_content: Optional[str] = None


class OutputGuardrail:
    """Node 5: 输出审查

    LLM-as-a-Judge 检查提示是否越界。
    """

    def __init__(self, llm_client: Optional[DashScopeClient] = None):
        """Initialize the guardrail.

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

    async def check(self, content: str, level: str) -> GuardrailResult:
        """检查提示是否越界。

        Args:
            content: 待检查的提示内容
            level: 提示等级 (R1-R4 / M1-M5)

        Returns:
            GuardrailResult: 检查结果
        """
        if not content or not content.strip():
            return GuardrailResult(
                passed=False,
                reason="提示内容为空",
                violations=["empty_content"],
            )

        # 第一步：规则检查（快速）
        rule = RULES.get(level, RULES["R1"])
        violations = []

        for forbidden in rule.get("forbidden", []):
            if forbidden in content:
                violations.append(forbidden)

        # 检查是否有"最终答案"或"完整解题"等通用违规
        universal_violations = [
            (r"答案[是为：：]\s*", "给出了答案"),
            (r"所以最终结果是?\s*", "给出了最终结果"),
            (r"完整[的]?解答[如下：：]", "给出了完整解答"),
            (r"解题步骤[如下：：]", "给出了完整解题步骤"),
        ]

        for pattern, desc in universal_violations:
            if re.search(pattern, content):
                violations.append(desc)

        # 如果有违规项，直接返回
        if violations:
            return GuardrailResult(
                passed=False,
                reason=f"提示包含违规内容: {violations[0]}",
                violations=violations,
            )

        # 第二步：LLM 检查（更全面的判断）
        prompt = build_guardrail_prompt(content, level)

        llm_client = self._get_llm_client()
        try:
            response = await llm_client.chat(
                messages=[Message(role="user", content=prompt)],
                temperature=0.1,  # 低温度，更稳定的判断
                max_tokens=256,
            )

            # 解析 JSON 响应
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            if response_clean.startswith("```"):
                response_clean = response_clean[3:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]

            data = json.loads(response_clean.strip())

            pass_result = data.get("pass", True)
            reason = data.get("reason", "")
            llm_violations = data.get("violations", [])

            if not pass_result:
                all_violations = violations + llm_violations
                return GuardrailResult(
                    passed=False,
                    reason=reason or f"LLM判定违规: {all_violations[0] if all_violations else 'unknown'}",
                    violations=all_violations,
                )

            return GuardrailResult(
                passed=True,
                reason=reason or "通过检查",
                violations=[],
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # LLM 解析失败，但规则检查已通过，允许通过
            return GuardrailResult(
                passed=True,
                reason=f"LLM判定超时，使用规则检查通过: {str(e)[:50]}",
                violations=[],
            )

        except Exception as e:
            # 其他异常，使用规则检查结果
            if violations:
                return GuardrailResult(
                    passed=False,
                    reason=str(e)[:100],
                    violations=violations,
                )
            return GuardrailResult(
                passed=True,
                reason=f"检查异常: {str(e)[:50]}",
                violations=[],
            )

    async def close(self) -> None:
        """Close resources."""
        if self._llm_client is not None:
            await self._llm_client.close()
            self._llm_client = None
