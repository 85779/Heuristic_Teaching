from dataclasses import dataclass
from enum import Enum
from typing import Optional


class BreakpointType(str, Enum):
    """Types of breakpoints."""
    MISSING_STEP = "missing_step"       # Student is missing a step
    WRONG_DIRECTION = "wrong_direction" # Student went off track
    INCOMPLETE_STEP = "incomplete_step" # Student started but didn't finish
    STUCK = "stuck"                     # Student is stuck with no clear next step
    NO_BREAKPOINT = "no_breakpoint"    # Student is on track


@dataclass
class BreakpointLocation:
    """Identifies where a student is stuck relative to the reference solution."""
    breakpoint_position: int              # 0-indexed: which solution step the student is stuck BEFORE
    breakpoint_type: BreakpointType
    expected_step_content: str           # Content of the next expected step
    gap_description: str                 # Human-readable description of the gap
    student_last_step: Optional[str]     # The student's last completed step (if any)
