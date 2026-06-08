"""Node 4: Hint Generator - R1-R4 / M1-M5 prompt level generation."""

from __future__ import annotations

import json
import os
from typing import Optional, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.infrastructure.llm.dashscope_client import DashScopeClient
from app.infrastructure.llm.base_client import Message

from ..models import (
    PromptLevelEnum,
    DimensionEnum,
    BreakpointLocation,
    SubTypeResult,
)

HINT_SYSTEM = """你是高中数学辅导老师。学生解不出题，需要你的提示来引导他们自己思考。

核心原则：
- 不直接给答案，帮助学生自己发现
- 提示强度从低到高递进（R1→R4, M1→M5）
- R维度（知识资源型）：学生缺知识或步骤，需要补充知识或方法
- M维度（元认知型）：学生有知识但不会调用，需要激活策略思维

## R维度递进逻辑（知识缺口）
R1=方向引导（不问具体知识）→ R2=指明所需定理/知识 → R3=给出第一步形式 → R4=完整计算步骤

## M维度递进逻辑（策略调用）
M1=反思当前路径 → M2=指明思考方向 → M3=推荐具体策略 → M4=策略对比+框架 → M5=完整思路+类比"""


# =============================================================================
# R1-R4: Resource Dimension (知识资源型)
# =============================================================================

R1_PROMPT = """## 题目
{problem_context}

## 学生已完成
{student_steps}

{knowledge_context}

## 学生说
"{student_input}"

## 生成 R1 级提示（最低强度）
学生卡住了，但还不清楚是知识缺口还是思路问题。你的任务是：
1. 从题目条件中挑出一个关键信息，问学生"这个条件暗示了什么"
2. 或者让学生对比他已做的步骤和题目目标之间的差距
3. 绝对不提及任何定理名、方法名、公式形式

## 示例
题目：求 f(x)=x^3-3x 的极值
学生已完成：计算了 f'(x)=3x^2-3
R1 提示："你算出了导数，接下来导数能告诉你关于原函数的什么信息？"

## 输出 JSON
{{
  "hint_content": "引导性提示（40字以内，以问句结尾）",
  "approach_hint": "你期望学生自己发现的思路"
}}"""

R2_PROMPT = """## 题目
{problem_context}

## 学生已完成
{student_steps}

{knowledge_context}

## 学生说
"{student_input}"

## 生成 R2 级提示
学生需要知识指引。你的任务：
1. 明确指出学生需要用到哪个定理/知识（如"这里需要用到导数的符号判别法"）
2. 说明为什么这个知识适用于当前情况
3. 不写出具体的计算形式

## 示例
R2 提示："你已求出 f'(x)=3x^2-3，现在需要判断单调性。回忆一下：导数的正负号如何决定原函数的增减？"

## 输出 JSON
{{
  "hint_content": "知识指引提示（60字以内）",
  "knowledge_hint": "指明的具体知识名称"
}}"""

R3_PROMPT = """## 题目
{problem_context}

## 学生已完成
{student_steps}

## 下一步参考（仅供你理解方向，不要原样输出）
{expected_step}

{knowledge_context}

## 学生说
"{student_input}"

## 生成 R3 级提示
学生已知道需要什么知识但不知道怎么用。你的任务：
1. 给出第一步的理论形式（如"令f'(x)=0，解这个方程"）
2. 说明为什么要这样操作
3. 不代做具体数值计算——让学生自己算

## 示例
R3 提示："令f'(x)=0解出临界点。因为极值只可能出现在导数为零或不存在的点。现在解方程3x^2-3=0。"

## 输出 JSON
{{
  "hint_content": "包含第一步形式的提示（80字以内）",
  "first_step_form": "第一步的操作描述"
}}"""

R4_PROMPT = """## 题目
{problem_context}

## 学生已完成
{student_steps}

## 下一步参考（仅供你理解方向）
{expected_step}

{knowledge_context}

## 学生说
"{student_input}"

## 生成 R4 级提示（最高强度）
学生已穷尽低强度提示仍无法推进。你的任务：
1. 给出完整可执行的计算步骤
2. 包含具体的中间结果
3. 让学生能直接跟着做

## 输出 JSON
{{
  "hint_content": "完整计算步骤（自然语言，含具体数值）",
  "computation_step": "逐步计算过程"
}}"""


# =============================================================================
# M1-M5: Metacognitive Dimension (元认知型)
# =============================================================================

M1_PROMPT = """## 题目
{problem_context}

## 学生已完成
{student_steps}

{knowledge_context}

## 学生说
"{student_input}"

## 生成 M1 级提示（最低强度）
学生困惑，但可能不是不会做，而是不知道从哪入手。你的任务：
1. 让学生评估：已完成的步骤是否正确？是否朝着目标前进？
2. 让学生回想：以前遇到过类似的题目吗？那时怎么做的？
3. 不指明任何具体方法或知识

## 示例
题目：证明数列 {{a_n}} 单调递减
学生已完成：计算了 a_{{n+1}} - a_n = 1/(n+1) - 1/n
M1 提示："你得到了 a_{{n+1}} - a_n 的表达式。这个差值的符号是什么？如果它是负的，对证明单调性意味着什么？"

## 输出 JSON
{{
  "hint_content": "引导反思的提示（以问句为主，50字以内）",
  "question_to_student": "让学生自己回答的问题"
}}"""

M2_PROMPT = """## 题目
{problem_context}

## 学生已完成
{student_steps}

{knowledge_context}

## 学生说
"{student_input}"

## 生成 M2 级提示
学生明确了卡在哪里，但不知道往哪个方向走。你的任务：
1. 指出一个可行的思考方向（如"考虑从递推关系入手"）
2. 解释为什么这个方向可能有效
3. 不指定具体方法——让学生自己选

## 示例
M2 提示："你已经算出差值表达式，下一步需要判断它的符号。这里分母n(n+1)的符号是确定的，关键是分子的符号。"

## 输出 JSON
{{
  "hint_content": "方向性指引（60字以内）",
  "direction_hint": "建议的思考方向"
}}"""

M3_PROMPT = """## 题目
{problem_context}

## 学生已完成
{student_steps}

## 下一步参考（仅供你理解方向）
{expected_step}

{knowledge_context}

## 学生说
"{student_input}"

## 生成 M3 级提示
学生需要具体策略建议。你的任务：
1. 推荐一个具体的解题策略（如"尝试换元法"、"用数学归纳法"）
2. 解释为什么这个策略适合当前问题
3. 对比：如果不用这个策略会有什么困难

## 示例
M3 提示："你可以尝试作差法：计算a_{{n+1}}-a_n，判断符号。如果差值为负则递减。这种方法直接验证定义，比求极限更简单。"

## 输出 JSON
{{
  "hint_content": "策略推荐（80字以内）",
  "method_hint": "推荐的策略名称",
  "rationale": "推荐理由"
}}"""

M4_PROMPT = """## 题目
{problem_context}

## 学生已完成
{student_steps}

## 下一步参考（仅供你理解方向）
{expected_step}

{knowledge_context}

## 学生说
"{student_input}"

## 生成 M4 级提示
学生需要看到多种可能的路径。你的任务：
1. 给出 2-3 种可行的解题路径
2. 比较各路径的优劣（哪种更直接、哪种更严谨）
3. 让学生自己选择并解释理由

## 示例
M4 提示："证明数列递减有两种常见路径：(1)作差法：计算a_{{n+1}}-a_n判断符号，直观但计算可能复杂；(2)比值法：计算a_{{n+1}}/a_n与1比较，适合正项数列。你的数列是正项，两种都可行，你倾向于哪种？"

## 输出 JSON
{{
  "hint_content": "多路径对比提示",
  "step_framework": "整体解题框架",
  "alternative_paths": ["路径1描述", "路径2描述"]
}}"""

M5_PROMPT = """## 题目
{problem_context}

## 学生已完成
{student_steps}

## 下一步参考（仅供你理解方向）
{expected_step}

{knowledge_context}

## 学生说
"{student_input}"

## 生成 M5 级提示（最高强度，接近完整讲解）
学生已尝试所有低强度提示仍无效。你的任务：
1. 给出完整的解题思路——从这一步到最终答案的逻辑链
2. 类比：这道题和哪类标准题型相似？标准解法是什么？
3. 让学生理解思路后自己执行计算

## 输出 JSON
{{
  "hint_content": "完整解题思路（150字以内）",
  "full_approach": "从当前步骤到完成的完整逻辑链",
  "similar_example": "类似题型的标准解法参考"
}}"""


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
    knowledge_context: str = "",
) -> str:
    """Build the prompt for the given level."""
    template = LEVEL_PROMPTS.get(level, R1_PROMPT)
    formatted_steps = format_student_steps(student_steps)

    if knowledge_context and knowledge_context.strip():
        knowledge_section = f"\n## 相关知识点（来自知识库）\n{knowledge_context}\n"
    else:
        knowledge_section = ""

    return template.format(
        problem_context=problem_context or "（无）",
        student_steps=formatted_steps,
        expected_step=expected_step or "（无）",
        student_input=student_input or "（空白）",
        knowledge_context=knowledge_section,
    )


# =============================================================================
# Node 4 Generator Class
# =============================================================================

class HintGeneratorV2:
    """Node 4: Hint Generator for v2 intervention flow."""

    def __init__(self, llm_client: Optional["DashScopeClient"] = None):
        self._llm_client = llm_client

    def _get_llm_client(self) -> "DashScopeClient":
        if self._llm_client is None:
            from app.infrastructure.llm.dashscope_client import DashScopeClient
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
        knowledge_context: str = "",
    ) -> str:
        prompt = build_generator_prompt(
            level=level,
            problem_context=problem_context,
            student_input=student_input,
            expected_step=expected_step,
            student_steps=student_steps,
            knowledge_context=knowledge_context,
        )

        llm_client = self._get_llm_client()
        response = await llm_client.chat(
            messages=[
                Message(role="system", content=HINT_SYSTEM),
                Message(role="user", content=prompt),
            ],
            temperature=0.7,
            max_tokens=512,
            enable_thinking=enable_thinking,
        )

        # Parse JSON response
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
            return response

    async def close(self) -> None:
        if self._llm_client:
            await self._llm_client.close()
