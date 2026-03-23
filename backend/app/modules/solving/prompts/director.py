"""Prompt Director - Orchestrates prompt template assembly."""

from typing import Optional, List
from .templates import (
    SYSTEM_PROMPT,
    THINKING_TASKS_PROMPT,
    ACTIONS_PROMPT,
    OUTPUT_FORMAT_PROMPT,
    LANGUAGE_STYLE_PROMPT,
    PROHIBITIONS_PROMPT,
)


class PromptDirector:
    """Director for assembling prompt templates.
    
    Orchestrates the assembly of base prompt templates from计划.md
    into a complete prompt for the solving module.
    """

    def __init__(self):
        """Initialize the prompt director."""
        pass

    def build_base_prompt(self) -> str:
        """Build the base prompt combining all templates.
        
        Combines:
        - System role definition
        - Four thinking tasks
        - Seven universal actions
        - Output format requirements
        - Prohibitions
        
        Returns:
            str: Complete base prompt
        """
        parts = [
            SYSTEM_PROMPT,
            "",
            THINKING_TASKS_PROMPT,
            "",
            ACTIONS_PROMPT,
            "",
            OUTPUT_FORMAT_PROMPT,
            "",
            LANGUAGE_STYLE_PROMPT,
            "",
            PROHIBITIONS_PROMPT,
        ]
        return "\n".join(parts)

    def build_evaluation_prompt(self, problem: str, student_work: str) -> str:
        """Build prompt for evaluating student work.
        
        Args:
            problem: The problem statement (LaTeX)
            student_work: Student's work so far (LaTeX)
            
        Returns:
            str: Evaluation prompt
        """
        return f"""请评估以下学生解答是否正确。

题目：
{problem}

学生已完成部分：
{student_work}

请判断：
1. 学生的解题思路是否正确？
2. 学生的计算是否正确？
3. 学生是否在正确的方向上推进？

请给出简短的评估结论。"""

    def build_continuation_prompt(self, problem: str, student_work: str) -> str:
        """Build prompt for continuing from student's work.
        
        Args:
            problem: The problem statement (LaTeX)
            student_work: Student's work so far (LaTeX)
            
        Returns:
            str: Continuation prompt
        """
        base = self.build_base_prompt()
        return f"""{base}

---
现在，请基于学生的已完成部分，继续生成解题过程。

题目：
{problem}

学生已完成部分：
{student_work}

请从学生的最后一步之后继续，按照上述要求生成完整讲解。
"""

    def build_full_solution_prompt(self, problem: str) -> str:
        """Build prompt for generating complete solution from scratch.
        
        Args:
            problem: The problem statement (LaTeX)
            
        Returns:
            str: Full solution prompt
        """
        base = self.build_base_prompt()
        return f"""{base}

---
现在，请对以下题目进行完整讲解。

题目：
{problem}

请按照上述要求进行讲解。
"""
