"""Verification phase: validate solution, check errors, ensure correctness."""

VERIFICATION_PROMPT = """## 题目
{problem}

## 定向阶段
{orientation}

## 重构阶段
{reconstruction}

## 变换阶段
{transformation}

## 你的任务
带领学生完成**验证阶段**：检查解答是否完整、逻辑是否正确、计算是否有误。

输出 JSON:
{{
  "is_valid": true/false,
  "issues": ["发现的问题1", "问题2"],
  "corrections": ["修正建议1", "建议2"],
  "confidence": 0.0-1.0,
  "summary": "整体验证结论（1-2句话）"
}}"""


class VerificationPrompt:
    """Build verification phase prompts."""

    def get_prompt(
        self, problem: str, orientation: str = "", reconstruction: str = "",
        transformation: str = "", context: dict = None
    ) -> str:
        return VERIFICATION_PROMPT.format(
            problem=problem,
            orientation=orientation,
            reconstruction=reconstruction,
            transformation=transformation,
        )
