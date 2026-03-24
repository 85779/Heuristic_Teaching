from typing import List


def build_analysis_prompt(
    problem: str,
    student_work: str,
    solution_steps: List[str],
    breakpoint_location: str,  # gap description
    expected_step: str,       # expected next step content
) -> str:
    """
    Build prompt for LLM to analyze what is needed to cross a breakpoint.
    
    The analysis should answer:
    1. What knowledge/skills are required to understand this step?
    2. What connection or relationship needs to be established to proceed?
    3. What alternative approaches could cross this breakpoint?
    4. How difficult is this step (0.0-1.0)?
    
    IMPORTANT: Focus on what is NEEDED, not what the student did wrong.
    """
    solution_steps_text = "\n".join(
        f"步骤 {i+1}: {step}" for i, step in enumerate(solution_steps)
    )
    
    return f"""你是一个高中数学教学辅助专家。你的任务是分析学生跨越某个解题断点需要什么知识和能力。

请分析以下情况：

【题目】
{problem}

【学生已完成的工作】
{student_work if student_work else "(学生尚未开始作答)"}

【参考解法的步骤】
{solution_steps_text}

【学生当前的断点位置】
{breakpoint_location}

【期望的下一步】
{expected_step}

请分析学生要跨越这个断点需要什么。回答以下问题：
1. 学生需要掌握哪些知识点或技能才能理解并完成这一步？
2. 学生需要建立什么联系或关系才能顺利推进？
3. 有哪些替代路径可以帮助学生跨越这个断点？
4. 这一步的难度如何（0.0到1.0，0.0最简单，1.0最难）？

请以JSON格式返回你的分析：
{{
    "required_knowledge": ["知识点1", "知识点2", ...],
    "required_connection": "需要建立的关键联系或关系",
    "possible_approaches": ["路径1", "路径2", ...],
    "difficulty_level": 0.0到1.0之间的数字
}}

请确保：
- required_knowledge只列出知识点的名称，简洁明了
- required_connection描述学生需要理解或发现的核心关系
- possible_approaches列出2-3个不同的解题路径或策略
- difficulty_level是一个0.0到1.0之间的小数

请直接返回JSON，不要包含其他内容。
"""
