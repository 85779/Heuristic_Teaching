"""Manual test script for intervention module.

Tests the full intervention flow:
1. BreakpointLocator - find where student is stuck
2. BreakpointAnalyzer - analyze what's needed to cross the breakpoint (LLM)
3. HintGenerator - generate hints at different intensity levels (LLM)

Usage:
    python tests/modules/test_intervention/manual_test.py
"""
import asyncio
import json
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# Stub motor for imports
import sys
sys.modules['motor'] = type(sys)('motor')
sys.modules['motor.motor_asyncio'] = type(sys)('motor_asyncio')
sys.modules['motor.motor_asyncio'].AsyncIOMotorClient = object
sys.modules['motor.motor_asyncio'].AsyncIOMotorDatabase = object


async def run_intervention_test():
    """Run the intervention flow with a real problem."""
    
    # Test problem
    problem = (
        "设 $a_0, a_1, \\ldots$ 是正整数序列，$(b_n)$ 是由 $b_n = \\gcd(a_n, a_{n+1})$ 定义的序列。"
        "证明：可以选择序列 $(a_n)$ 使得每个非零自然数恰好等于 $a_0, b_0, a_1, b_1, \\ldots$ 中的一项。"
    )
    
    # Student partial work (from Case 3)
    student_work = (
        "解：设 a_0 = 1。\n"
        "对于 n ≥ 0，令 a_{n+1} = b_n × (n+2)。\n"
        "则 b_n = gcd(a_n, a_{n+1}) = n+1。"
    )
    
    # Student steps (what they completed)
    student_steps = [
        {
            "step_id": "s1",
            "step_name": "学生已完成",
            "content": "设 a_0 = 1。对于 n ≥ 0，令 a_{n+1} = b_n × (n+2)。则 b_n = gcd(a_n, a_{n+1}) = n+1。"
        }
    ]
    
    # Reference solution steps (from Case 1)
    solution_steps = [
        {
            "step_id": "s1",
            "step_name": "理解问题",
            "content": "理解题目要求：我们需要构造一个正整数序列 a_0, a_1, ...，使得由 b_n = gcd(a_n, a_{n+1}) 定义的序列 b_n 满足：每个正整数都恰好出现在 a_0, b_0, a_1, b_1, ... 中一次。"
        },
        {
            "step_id": "s2",
            "step_name": "构造初始序列",
            "content": "设 a_0 = 1，则 b_0 = gcd(a_0, a_1)。为了方便后续构造，先让 a_0 = 1，a_1 = 2，则 b_0 = gcd(1, 2) = 1。"
        },
        {
            "step_id": "s3",
            "step_name": "归纳假设",
            "content": "假设我们已经构造了 a_0, a_1, ..., a_n 和 b_0, b_1, ..., b_{n-1}，并且已经覆盖了 1, 2, ..., n 这些正整数一次。"
        },
        {
            "step_id": "s4",
            "step_name": "构造新项",
            "content": "为了覆盖 n+1，我们选择 a_{n+1} = (n+1) * p，其中 p 是一个足够大的质数（从未使用过），使得 gcd(a_n, a_{n+1}) = n+1。具体构造时令 a_{n+2} = p，则 b_{n+1} = gcd(a_{n+1}, a_{n+2}) = gcd((n+1)*p, p) = p，而 b_n = n+1。"
        },
        {
            "step_id": "s5",
            "step_name": "验证覆盖性",
            "content": "通过归纳构造，每一步我们都引入一个新的质数 p，确保每个正整数都能在某个 b_k 中出现，同时新的 a_k 也被引入，覆盖了所有正整数。"
        },
        {
            "step_id": "s6",
            "step_name": "验证唯一性",
            "content": "由于每次引入的质数都是全新的，每个正整数只会在唯一的位置出现一次，不会重复。"
        }
    ]
    
    # Imports
    from app.modules.intervention.locator.breaker import BreakpointLocator
    from app.modules.intervention.analyzer.analyzer import BreakpointAnalyzer
    from app.modules.intervention.generator.generator import HintGenerator
    from app.modules.solving.models import TeachingStep
    
    print("=" * 80)
    print("INTERVENTION MODULE TEST")
    print("=" * 80)
    print()
    
    # ============================================================
    # STEP 1: BreakpointLocator
    # ============================================================
    print("=" * 80)
    print("STEP 1: BreakpointLocator")
    print("=" * 80)
    
    locator = BreakpointLocator()
    student_steps_obj = [
        TeachingStep(step_id=s["step_id"], step_name=s["step_name"], content=s["content"])
        for s in student_steps
    ]
    solution_steps_obj = [
        TeachingStep(step_id=s["step_id"], step_name=s["step_name"], content=s["content"])
        for s in solution_steps
    ]
    
    location = locator.locate(student_steps_obj, solution_steps_obj)
    
    print(f"Breakpoint Position: {location.breakpoint_position}")
    print(f"Breakpoint Type: {location.breakpoint_type.value}")
    print(f"Expected Step: {location.expected_step_content}")
    print(f"Gap Description: {location.gap_description}")
    print(f"Student Last Step: {location.student_last_step}")
    print()
    
    # ============================================================
    # STEP 2: BreakpointAnalyzer (LLM call)
    # ============================================================
    print("=" * 80)
    print("STEP 2: BreakpointAnalyzer (LLM)")
    print("=" * 80)
    
    analyzer = BreakpointAnalyzer()
    solution_step_contents = [s["content"] for s in solution_steps]
    
    print("Calling LLM for breakpoint analysis...")
    print("(This uses qwen-turbo and requires DASHSCOPE_API_KEY)")
    print()
    
    analysis = await analyzer.analyze(
        breakpoint_location=location,
        problem=problem,
        student_work=student_work,
        solution_steps=solution_step_contents,
    )
    
    print(f"Required Knowledge: {analysis.required_knowledge}")
    print(f"Required Connection: {analysis.required_connection}")
    print(f"Possible Approaches: {analysis.possible_approaches}")
    print(f"Difficulty Level: {analysis.difficulty_level}")
    print()
    
    # ============================================================
    # STEP 3: HintGenerator at different intensities
    # ============================================================
    generator = HintGenerator()
    
    for intensity in [0.3, 0.5, 0.8]:
        level = generator._determine_level(intensity)
        print("=" * 80)
        print(f"STEP 3: HintGenerator (intensity={intensity}, level={level})")
        print("=" * 80)
        
        print("Calling LLM for hint generation...")
        print()
        
        hint = await generator.generate(
            analysis=analysis,
            problem=problem,
            intensity=intensity,
        )
        
        print(f"Level: {hint.level}")
        print(f"Approach Used: {hint.approach_used}")
        print(f"Content:")
        print("-" * 40)
        print(hint.content)
        print("-" * 40)
        print()
    
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("ERROR: DASHSCOPE_API_KEY environment variable not set")
        print("Please set it and try again:")
        print("  export DASHSCOPE_API_KEY=your_key_here")
        sys.exit(1)
    
    asyncio.run(run_intervention_test())
