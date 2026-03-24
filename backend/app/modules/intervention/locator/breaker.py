from typing import List
from app.modules.solving.models import TeachingStep
from .models import BreakpointLocation, BreakpointType


class BreakpointLocator:
    """Locates breakpoints by comparing student steps vs reference solution steps."""

    # Minimum content length to consider a step as "complete"
    MIN_COMPLETE_STEP_LENGTH = 5

    def locate(
        self,
        student_steps: List[TeachingStep],
        solution_steps: List[TeachingStep],
    ) -> BreakpointLocation:
        """
        Compare student steps to solution steps and locate the breakpoint.
        
        Logic:
        1. If student has more steps than solution, they're beyond the reference (NO_BREAKPOINT)
        2. Iterate through solution steps:
           - If student step i has different content than solution step i → WRONG_DIRECTION
           - If student is missing a step (no step i) → MISSING_STEP
           - If student step i is incomplete (too short) → INCOMPLETE_STEP
        3. If all student steps match first N solution steps but student has no more → MISSING_STEP (need next step)
        4. If student has exactly N steps matching first N solution steps with no gap → NO_BREAKPOINT
        5. If student gave no steps at all → STUCK (can't determine where)
        
        Returns:
            BreakpointLocation with details about the gap
        """
        # Edge case: student gave no steps at all
        if not student_steps:
            if not solution_steps:
                # No solution either - can't determine anything
                return BreakpointLocation(
                    breakpoint_position=0,
                    breakpoint_type=BreakpointType.STUCK,
                    expected_step_content="",
                    gap_description="学生未提供任何解题步骤，无法确定断点位置",
                    student_last_step=None,
                )
            # Student has no steps but solution has steps
            return BreakpointLocation(
                breakpoint_position=0,
                breakpoint_type=BreakpointType.MISSING_STEP,
                expected_step_content=solution_steps[0].content,
                gap_description="学生未开始解题，第一步缺失",
                student_last_step=None,
            )

        # Edge case: student has more steps than solution (beyond reference)
        if len(student_steps) > len(solution_steps):
            return BreakpointLocation(
                breakpoint_position=len(solution_steps),
                breakpoint_type=BreakpointType.NO_BREAKPOINT,
                expected_step_content="",
                gap_description="学生已超越参考解法步骤数",
                student_last_step=student_steps[-1].content,
            )

        # Compare steps one by one
        for i in range(len(solution_steps)):
            # Check if student has a step at position i
            if i >= len(student_steps):
                # Student is missing step i
                return BreakpointLocation(
                    breakpoint_position=i,
                    breakpoint_type=BreakpointType.MISSING_STEP,
                    expected_step_content=solution_steps[i].content,
                    gap_description=f"学生在第 {i + 1} 步缺失",
                    student_last_step=student_steps[i - 1].content if i > 0 else None,
                )

            student_content = student_steps[i].content.strip()
            expected_content = solution_steps[i].content.strip()

            # Check if content differs
            if student_content != expected_content:
                # Check if student's step is too short/incomplete
                if len(student_content) < self.MIN_COMPLETE_STEP_LENGTH:
                    return BreakpointLocation(
                        breakpoint_position=i,
                        breakpoint_type=BreakpointType.INCOMPLETE_STEP,
                        expected_step_content=expected_content,
                        gap_description=f"学生在第 {i + 1} 步的内容不完整",
                        student_last_step=student_content,
                    )
                # Content is different but substantial → wrong direction
                return BreakpointLocation(
                    breakpoint_position=i,
                    breakpoint_type=BreakpointType.WRONG_DIRECTION,
                    expected_step_content=expected_content,
                    gap_description=f"学生在第 {i + 1} 步的方向偏离了参考解法",
                    student_last_step=student_content,
                )

        # All compared steps match, but student may have fewer steps than solution
        if len(student_steps) < len(solution_steps):
            # Student matched first N steps but needs the next step
            next_position = len(student_steps)
            return BreakpointLocation(
                breakpoint_position=next_position,
                breakpoint_type=BreakpointType.MISSING_STEP,
                expected_step_content=solution_steps[next_position].content,
                gap_description=f"学生已正确完成前 {next_position} 步，第 {next_position + 1} 步缺失",
                student_last_step=student_steps[-1].content,
            )

        # Student has exactly the same number of steps and all match
        return BreakpointLocation(
            breakpoint_position=len(solution_steps),
            breakpoint_type=BreakpointType.NO_BREAKPOINT,
            expected_step_content="",
            gap_description="学生解题步骤与参考解法一致，无断点",
            student_last_step=student_steps[-1].content if student_steps else None,
        )
