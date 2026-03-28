"""Node 4: Hint Generator - R1-R4 / M1-M5 prompt level generation."""

import json
import os
from typing import Optional, List, Dict, Any

from app.infrastructure.llm.dashscope_client import DashScopeClient
from app.infrastructure.llm.base_client import Message

from ..models import (
    PromptLevelEnum,
    DimensionEnum,
    BreakpointLocation,
    SubTypeResult,
)


# =============================================================================
# Prompt Templates for R1-R4 (Resource Dimension)
# =============================================================================

R1_PROMPT = """你是一位高中数学辅导老师。学生在一个解题步骤上卡住了。

## 题目
{problem_context}

## 学生当前状态
学生已完成的步骤：
{student_steps}

## 参考解法的下一步
{expected_step}

## 学生说
"{student_input}"

## 你的任务
生成一条 R1 级提示。R1 的定义：
- 只给方向性提示，不给具体知识内容
- 不提及具体定理名称（如"余数定理"、"数学归纳法"等）
- 不给出第一步的具体形式
- 引导学生自己发现下一步应该做什么

## R1 提示原则
- 关注题目条件和目标之间的关系
- 提示学生回顾已知的类似题型
- 不直接告诉学生该怎么走，而是引导思考方向

## 输出格式
请返回 JSON 格式：
{{
  "hint_content": "提示内容（自然语言，50字以内）",
  "approach_hint": "简要说明使用的思路方向"
}}

请确保提示内容不包含具体定理名称或第一步的具体形式。"""

R2_PROMPT = """你是一位高中数学辅导老师。学生在一个解题步骤上卡住了。

## 题目
{problem_context}

## 学生当前状态
学生已完成的步骤：
{student_steps}

## 参考解法的下一步
{expected_step}

## 学生说
"{student_input}"

## 你的任务
生成一条 R2 级提示。R2 的定义：
- 可以提及具体的定理名称、知识概念（如"余数定理"、"数学归纳法"、"换元法"等）
- 仍然不给出第一步的具体形式
- 通过指明所需知识来引导学生

## R2 提示原则
- 明确指出学生需要什么知识
- 引导学生回忆相关定理或方法
- 不直接告诉学生怎么用，而是告诉学生用什么

## 输出格式
请返回 JSON 格式：
{{
  "hint_content": "提示内容（自然语言，80字以内）",
  "knowledge_hint": "指明的具体知识或定理"
}}

请确保提示内容包含具体的知识指引，但不给出第一步的具体形式。"""

R3_PROMPT = """你是一位高中数学辅导老师。学生在一个解题步骤上卡住了。

## 题目
{problem_context}

## 学生当前状态
学生已完成的步骤：
{student_steps}

## 参考解法的下一步
{expected_step}

## 学生说
"{student_input}"

## 你的任务
生成一条 R3 级提示。R3 的定义：
- 可以给出第一步的理论形式（如"先求一个中间量"）
- 不给出具体数值计算
- 学生能知道第一步该做什么形式，但不知道具体怎么算

## R3 提示原则
- 给出第一步的方向和形式
- 通过理论推导引导学生
- 不涉及具体数值计算

## 输出格式
请返回 JSON 格式：
{{
  "hint_content": "提示内容（自然语言，100字以内）",
  "first_step_form": "第一步的理论形式描述"
}}

请确保提示内容包含第一步的形式指引。"""

R4_PROMPT = """你是一位高中数学辅导老师。学生在一个解题步骤上卡住了。

## 题目
{problem_context}

## 学生当前状态
学生已完成的步骤：
{student_steps}

## 参考解法的下一步
{expected_step}

## 学生说
"{student_input}"

## 你的任务
生成一条 R4 级提示。R4 的定义：
- 给出真实的计算步骤
- 可以包含具体的数值计算（如"计算 gcd(24, 36) = 12"）
- 让学生能够直接按照提示进行计算

## R4 提示原则
- 给出完整可执行的步骤
- 包含具体计算过程
- 让学生能够立即推进

## 输出格式
请返回 JSON 格式：
{{
  "hint_content": "提示内容（自然语言，包含具体计算步骤）",
  "computation_step": "具体计算步骤"
}}

请确保提示内容包含真实的计算步骤。"""


# =============================================================================
# Prompt Templates for M1-M5 (Metacognitive Dimension)
# =============================================================================

M1_PROMPT = """你是一位高中数学辅导老师。学生遇到困难，表示不知道该怎么办。

## 题目
{problem_context}

## 学生当前状态
学生已完成的步骤：
{student_steps}

## 学生说
"{student_input}"

## 你的任务
生成一条 M1 级提示。M1 的定义：
- 帮助学生判断"应该继续还是停下来思考"
- 分析当前路径是否还有推进空间
- 引导学生评估自己的解题方向

## M1 提示原则
- 问学生关于当前路径的问题
- 引导学生思考是否应该坚持当前方向
- 不给出具体下一步

## 输出格式
请返回 JSON 格式：
{{
  "hint_content": "提示内容（引导学生思考当前路径是否正确）",
  "question_to_student": "给学生的问题"
}}

请确保提示内容是引导性的问题，而非答案。"""

M2_PROMPT = """你是一位高中数学辅导老师。学生在一个解题步骤上卡住了，但需要方向指引。

## 题目
{problem_context}

## 学生当前状态
学生已完成的步骤：
{student_steps}

## 参考解法的下一步
{expected_step}

## 学生说
"{student_input}"

## 你的任务
生成一条 M2 级提示。M2 的定义：
- 给出方向性指引
- 告诉学生应该往哪个方向思考
- 不涉及具体知识点或计算

## M2 提示原则
- 指明思考方向
- 不给具体方法或知识
- 帮助学生找到切入点

## 输出格式
请返回 JSON 格式：
{{
  "hint_content": "提示内容（方向性指引）",
  "direction_hint": "指向的方向"
}}

请确保提示内容给出方向，但不给出具体方法。"""

M3_PROMPT = """你是一位高中数学辅导老师。学生在一个解题步骤上卡住了。

## 题目
{problem_context}

## 学生当前状态
学生已完成的步骤：
{student_steps}

## 参考解法的下一步
{expected_step}

## 学生说
"{student_input}"

## 你的任务
生成一条 M3 级提示。M3 的定义：
- 给出更详细的方向指引
- 可以提示解题方法（如"考虑换元"、"考虑数学归纳法"）
- 帮助学生确定具体该怎么做

## M3 提示原则
- 指明具体方法
- 给出方法选择的理由
- 引导学生选择正确的解题方法

## 输出格式
请返回 JSON 格式：
{{
  "hint_content": "提示内容（包含方法指引）",
  "method_hint": "建议的解题方法"
}}

请确保提示内容包含方法指引。"""

M4_PROMPT = """你是一位高中数学辅导老师。学生需要更详细的帮助。

## 题目
{problem_context}

## 学生当前状态
学生已完成的步骤：
{student_steps}

## 参考解法的下一步
{expected_step}

## 学生说
"{student_input}"

## 你的任务
生成一条 M4 级提示。M4 的定义：
- 当 breakpoint 类型发生变化时触发
- 给出具体的解题步骤描述
- 可以包含多个可选路径

## M4 提示原则
- 给出具体的步骤框架
- 列出可选路径
- 帮助学生选择最适合的方法

## 输出格式
请返回 JSON 格式：
{{
  "hint_content": "提示内容（包含步骤框架）",
  "step_framework": "步骤框架描述",
  "alternative_paths": ["路径1", "路径2"]
}}

请确保提示内容包含步骤框架和可选路径。"""

M5_PROMPT = """你是一位高中数学辅导老师。学生需要最详细的帮助。

## 题目
{problem_context}

## 学生当前状态
学生已完成的步骤：
{student_steps}

## 参考解法的下一步
{expected_step}

## 学生说
"{student_input}"

## 你的任务
生成一条 M5 级提示。M5 的定义：
- 最详细的提示级别
- 给出完整的解题思路
- 包含类似题目的参考

## M5 提示原则
- 完整解题思路
- 类似题目参考
- 详细步骤讲解

## 输出格式
请返回 JSON 格式：
{{
  "hint_content": "提示内容（详细解题思路）",
  "full_approach": "完整解题思路",
  "similar_example": "类似题目参考"
}}

请确保提示内容是最高详细级别。"""


# =============================================================================
# Level to Prompt Mapping
# =============================================================================

LEVEL_PROMPTS = {
    PromptLevelEnum.R1: R1_PROMPT,
    PromptLevelEnum.R2: R2_PROMPT,
    PromptLevelEnum.R3: R3_PROMPT,
    PromptLevelEnum.R4: R4_PROMPT,
    PromptLevelEnum.M1: M1_PROMPT,
    PromptLevelEnum.M2: M2_PROMPT,
    PromptLevelEnum.M3: M3_PROMPT,
    PromptLevelEnum.M4: M4_PROMPT,
    PromptLevelEnum.M5: M5_PROMPT,
}


def format_student_steps(student_steps: List[Dict[str, Any]]) -> str:
    """Format student steps for prompt."""
    if not student_steps:
        return "（无）"
    lines = []
    for i, step in enumerate(student_steps, 1):
        content = step.get("content", "")
        step_name = step.get("step_name", f"步骤{i}")
        lines.append(f"{i}. [{step_name}] {content}")
    return "\n".join(lines)


def build_generator_prompt(
    level: PromptLevelEnum,
    problem_context: str,
    student_input: str,
    expected_step: str,
    student_steps: List[Dict[str, Any]],
) -> str:
    """Build the generator prompt for a given level.

    Args:
        level: Prompt level (R1-R4 / M1-M5)
        problem_context: Problem text
        student_input: Student's current input
        expected_step: Expected next step from reference solution
        student_steps: Student's completed steps

    Returns:
        Formatted prompt string
    """
    prompt_template = LEVEL_PROMPTS.get(level, R1_PROMPT)

    formatted_student_steps = format_student_steps(student_steps)

    return prompt_template.format(
        problem_context=problem_context or "（无）",
        student_steps=formatted_student_steps,
        expected_step=expected_step or "（无）",
        student_input=student_input or "（空白）",
    )


# =============================================================================
# Node 4 Generator Class
# =============================================================================

class HintGeneratorV2:
    """Node 4: Hint Generator for v2 intervention flow.

    Generates hints based on R1-R4 / M1-M5 prompt levels.
    """

    def __init__(self, llm_client: Optional[DashScopeClient] = None):
        """Initialize the generator.

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

    async def generate(
        self,
        level: PromptLevelEnum,
        problem_context: str,
        student_input: str,
        expected_step: str,
        student_steps: List[Dict[str, Any]],
        enable_thinking: bool = False,
    ) -> str:
        """Generate a hint for the given level.

        Args:
            level: Prompt level (R1-R4 / M1-M5)
            problem_context: Problem text
            student_input: Student's current input
            expected_step: Expected next step
            student_steps: Student's completed steps
            enable_thinking: Enable deep thinking mode (qwen3.5-plus only)

        Returns:
            Generated hint content string
        """
        prompt = build_generator_prompt(
            level=level,
            problem_context=problem_context,
            student_input=student_input,
            expected_step=expected_step,
            student_steps=student_steps,
        )

        llm_client = self._get_llm_client()
        response = await llm_client.chat(
            messages=[Message(role="user", content=prompt)],
            temperature=0.7,
            max_tokens=512,
            enable_thinking=enable_thinking,
        )

        # Try to parse JSON response
        try:
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            if response_clean.startswith("```"):
                response_clean = response_clean[3:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]

            data = json.loads(response_clean.strip())
            return data.get("hint_content", response)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Fallback: return raw response
            return response

    async def close(self) -> None:
        """Close resources."""
        if self._llm_client is not None:
            await self._llm_client.close()
            self._llm_client = None
