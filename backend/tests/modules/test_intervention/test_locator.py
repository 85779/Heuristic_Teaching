"""Tests for BreakpointLocator."""
import pytest
from app.modules.solving.models import TeachingStep
from app.modules.intervention.locator.models import BreakpointType


def test_no_breakpoint_exact_match(breakpoint_locator):
    """Student steps exactly match solution steps → NO_BREAKPOINT."""
    student = [
        TeachingStep(step_id="s1", step_name="Step 1", content="Do this"),
    ]
    solution = [
        TeachingStep(step_id="s1", step_name="Step 1", content="Do this"),
    ]
    result = breakpoint_locator.locate(student, solution)
    assert result.breakpoint_type == BreakpointType.NO_BREAKPOINT


def test_missing_step(breakpoint_locator):
    """Student is missing a step → MISSING_STEP."""
    student = [
        TeachingStep(step_id="s1", step_name="Step 1", content="Do this"),
    ]
    solution = [
        TeachingStep(step_id="s1", step_name="Step 1", content="Do this"),
        TeachingStep(step_id="s2", step_name="Step 2", content="Then do that"),
    ]
    result = breakpoint_locator.locate(student, solution)
    assert result.breakpoint_type == BreakpointType.MISSING_STEP
    assert result.breakpoint_position == 1
    assert "第 2 步缺失" in result.gap_description


def test_wrong_direction(breakpoint_locator):
    """Student step differs from solution → WRONG_DIRECTION."""
    student = [
        TeachingStep(step_id="s1", step_name="Step 1", content="Something completely different"),
    ]
    solution = [
        TeachingStep(step_id="s1", step_name="Step 1", content="Do this"),
    ]
    result = breakpoint_locator.locate(student, solution)
    assert result.breakpoint_type == BreakpointType.WRONG_DIRECTION
    assert result.breakpoint_position == 0


def test_empty_student_steps(breakpoint_locator):
    """Student gave no steps → MISSING_STEP at position 0."""
    student = []
    solution = [
        TeachingStep(step_id="s1", step_name="Step 1", content="Do this"),
    ]
    result = breakpoint_locator.locate(student, solution)
    assert result.breakpoint_type == BreakpointType.MISSING_STEP
    assert result.breakpoint_position == 0


def test_student_beyond_solution(breakpoint_locator):
    """Student has more steps than solution → NO_BREAKPOINT."""
    student = [
        TeachingStep(step_id="s1", step_name="Step 1", content="Do this"),
        TeachingStep(step_id="s2", step_name="Step 2", content="Then do that"),
    ]
    solution = [
        TeachingStep(step_id="s1", step_name="Step 1", content="Do this"),
    ]
    result = breakpoint_locator.locate(student, solution)
    assert result.breakpoint_type == BreakpointType.NO_BREAKPOINT


def test_multiple_correct_then_missing(breakpoint_locator):
    """Student completes first 2 steps correctly, missing step 3."""
    student = [
        TeachingStep(step_id="s1", step_name="Step 1", content="Step 1 content"),
        TeachingStep(step_id="s2", step_name="Step 2", content="Step 2 content"),
    ]
    solution = [
        TeachingStep(step_id="s1", step_name="Step 1", content="Step 1 content"),
        TeachingStep(step_id="s2", step_name="Step 2", content="Step 2 content"),
        TeachingStep(step_id="s3", step_name="Step 3", content="Step 3 content"),
    ]
    result = breakpoint_locator.locate(student, solution)
    assert result.breakpoint_type == BreakpointType.MISSING_STEP
    assert result.breakpoint_position == 2
