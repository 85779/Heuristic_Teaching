"""Reconstruction phase: break down problem into components and relationships."""

RECONSTRUCTION_PROMPT = """## 题目
{problem}

## 定向阶段成果
{orientation}

## 你的任务
带领学生完成**重构阶段**：把题目拆解为可分析的组成部分，识别各组件之间的关系。

输出 JSON:
{{
  "components": ["组件1", "组件2"],
  "relationships": {{"组件1": "与组件2的关系描述"}},
  "breakdown": "结构化的问题拆解（2-3段）",
  "hint": "帮助学生自己拆解问题的引导"
}}"""


class ReconstructionPrompt:
    """Build reconstruction phase prompts."""

    def get_prompt(self, problem: str, orientation: str = "", context: dict = None) -> str:
        return RECONSTRUCTION_PROMPT.format(problem=problem, orientation=orientation)
