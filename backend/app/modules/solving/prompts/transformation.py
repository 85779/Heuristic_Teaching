"""Transformation phase: choose strategies, develop solution approach."""

TRANSFORMATION_PROMPT = """## 题目
{problem}

## 定向阶段
{orientation}

## 重构阶段
{reconstruction}

## 你的任务
带领学生完成**变换阶段**：选择合适的解题策略，制定具体的解题步骤。

输出 JSON:
{{
  "strategies": ["策略1", "策略2"],
  "approach": "选定的解题思路（2-3句话说明为什么选这个策略）",
  "steps": ["具体步骤1", "步骤2", "步骤3"],
  "hint": "帮助学生自己找到解题策略的引导"
}}"""


class TransformationPrompt:
    """Build transformation phase prompts."""

    def get_prompt(
        self, problem: str, orientation: str = "", reconstruction: str = "", context: dict = None
    ) -> str:
        return TRANSFORMATION_PROMPT.format(
            problem=problem,
            orientation=orientation,
            reconstruction=reconstruction,
        )
