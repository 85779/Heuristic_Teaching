"""Prompt templates for hint generation."""

from typing import List


def build_hint_prompt(
    analysis: dict,       # BreakpointAnalysis as dict
    problem: str,
    level: str,           # "surface" | "middle" | "deep"
    intensity: float,
) -> str:
    """
    Build prompt for LLM to generate a hint.
    
    Level definitions:
    - surface (intensity < 0.4): Give directional hints only — don't give the actual solution
    - middle (0.4 <= intensity < 0.7): Give partial hints + example analogies
    - deep (intensity >= 0.7): Give complete example + step-by-step walkthrough
    
    IMPORTANT: 
    - NEVER give the complete solution directly
    - Focus on guiding the student to discover the next step
    - Use natural language, not formulas
    """
    analysis_str = _format_analysis(analysis)
    
    level_instruction = _get_level_instruction(level)
    
    return f"""你是一位高中数学辅导老师。你的任务是帮助学生跨越解题过程中的断点。

## 题目
{problem}

## 断点分析
{analysis_str}

## 提示级别
{level_instruction}

## 要求
1. 只提供 hints，不要直接给出完整解法
2. 引导学生自己发现下一步该怎么做
3. 使用自然语言，避免纯公式罗列
4. 根据提示级别调整 hint 的详细程度

## 输出格式
请返回 JSON 格式：
{{
  "content": "提示内容（自然语言）",
  "approach_used": "使用的解题思路或方法名称"
}}

请确保 content 中不包含完整答案，只包含引导性的提示。
"""


def _format_analysis(analysis: dict) -> str:
    """Format BreakpointAnalysis dict into readable string."""
    parts = []
    
    if analysis.get("required_knowledge"):
        parts.append(f"所需知识：{', '.join(analysis['required_knowledge'])}")
    
    if analysis.get("required_connection"):
        parts.append(f"关键联系：{analysis['required_connection']}")
    
    if analysis.get("possible_approaches"):
        parts.append(f"可能的思路：{', '.join(analysis['possible_approaches'])}")
    
    parts.append(f"难度等级：{analysis.get('difficulty_level', 0.5)}")
    
    return "\n".join(parts) if parts else "无详细分析信息"


def _get_level_instruction(level: str) -> str:
    """Get instruction text for the given hint level."""
    if level == "surface":
        return """【surface 级提示】（intensity < 0.4）
只给方向性提示，不给具体解法。
例如："想想题目中已知条件和所求目标之间的关系"
不要告诉学生具体该怎么做，而是引导他们思考方向。"""
    elif level == "middle":
        return """【middle 级提示】（0.4 <= intensity < 0.7）
给部分提示 + 类比示例。
可以告诉学生从哪个角度入手，并提供类似问题的参考。
例如："可以尝试先求出某个中间量，类似于之前学过的某某题型"
引导学生找到部分解法线索。"""
    else:  # deep
        return """【deep 级提示】（intensity >= 0.7）
给完整示例 + 步骤讲解。
可以给出类似题目的完整解题过程，逐步讲解关键步骤。
例如："来看一个完全一样的例子...第一步...第二步..."
但仍然不要直接给出原题的完整答案，而是通过示例让学生理解方法。"""
