"""Orientation phase: understand problem space, identify key concepts."""

ORIENTATION_SYSTEM = """你是高中数学老师。引导学生理解题目，建立解题目标。"""

ORIENTATION_PROMPT = """## 题目
{problem}

## 你的任务
带领学生完成**定向阶段**：理解题目在问什么、考什么、突破口在哪里。

输出 JSON:
{{
  "understanding": "对题目的整体理解（2-3句话）",
  "key_concepts": ["关键概念1", "关键概念2"],
  "goals": ["要达成的目标1", "目标2"],
  "hint": "给学生的一个引导性问题（不直接给答案）"
}}"""


class OrientationPrompt:
    """Build orientation phase prompts."""

    def get_prompt(self, problem: str, context: dict = None) -> str:
        return ORIENTATION_PROMPT.format(problem=problem)
