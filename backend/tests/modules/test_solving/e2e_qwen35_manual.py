"""End-to-end test with qwen3.5-plus model."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

# Load .env file
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and '=' in line and not line.startswith('#'):
                key, _, value = line.partition('=')
                os.environ[key] = value

# Stub motor
sys.modules['motor'] = type(sys)('motor')
sys.modules['motor.motor_asyncio'] = type(sys)('motor_asyncio')
sys.modules['motor.motor_asyncio'].AsyncIOMotorClient = object
sys.modules['motor.motor_asyncio'].AsyncIOMotorDatabase = object

from app.modules.solving.models import SolvingRequest
from app.modules.solving.service import ReferenceSolutionService


PROBLEM = (
    "设 $a_0, a_1, \\ldots$ 是正整数序列，"
    "$(b_n)$ 是由 $b_n = \\gcd(a_n, a_{n+1})$ 定义的序列。"
    "证明：可以选择序列 $(a_n)$ 使得每个非零自然数恰好等于 "
    "$a_0, b_0, a_1, b_1, \\ldots$ 中的一项。"
)


async def test_full_solution():
    """Test Case 1: No student work, generate full solution."""
    print("=" * 60)
    print("Test Case 1: Full Solution (no student work)")
    print("=" * 60)

    os.environ["SOLVING_MODEL"] = "qwen3.5-plus"

    service = ReferenceSolutionService()
    request = SolvingRequest(
        problem=PROBLEM,
        student_work=None,
        model="qwen3.5-plus",
        temperature=0.7,
        max_tokens=8192,
        enable_thinking=True,
    )

    try:
        response = await service.generate(request)
    except Exception as e:
        print(f"\nException: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

    print(f"\nSuccess: {response.success}")
    print(f"Evaluation - is_correct: {response.evaluation.is_correct}")
    print(f"Evaluation - confidence: {response.evaluation.confidence}")

    if response.solution:
        print(f"\nAnswer: {response.solution.answer}")
        print(f"\nSteps ({len(response.solution.steps)}):")
        for step in response.solution.steps:
            print(f"  [{step.step_id}] {step.step_name}")
            print(f"    {step.content[:200]}...")
    elif response.error_feedback:
        print(f"\nError feedback: {response.error_feedback.summary}")
        print(f"Suggestion: {response.error_feedback.suggestion}")

    await service.close()
    return response


async def test_partial_work():
    """Test Case 3: Correct partial work, continue generation."""
    print("\n" + "=" * 60)
    print("Test Case 3: Partial Work (correct, continue)")
    print("=" * 60)

    os.environ["SOLVING_MODEL"] = "qwen3.5-plus"

    service = ReferenceSolutionService()
    student_work = (
        "解：设 a_0 = 1。\n"
        "对于 n ≥ 0，令 a_{n+1} = b_n × (n+2)。\n"
        "则 b_n = gcd(a_n, a_{n+1}) = n+1。"
    )

    request = SolvingRequest(
        problem=PROBLEM,
        student_work=student_work,
        model="qwen3.5-plus",
        temperature=0.7,
        max_tokens=8192,
        enable_thinking=True,
    )

    try:
        response = await service.generate(request)
    except Exception as e:
        print(f"\nException: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

    print(f"\nSuccess: {response.success}")
    print(f"Evaluation - is_correct: {response.evaluation.is_correct}")
    print(f"Evaluation - can_continue: {response.evaluation.can_continue}")
    print(f"Breakpoint step: {response.evaluation.breakpoint_step}")

    if response.solution:
        print(f"\nAnswer: {response.solution.answer}")
        print(f"\nSteps ({len(response.solution.steps)}):")
        for step in response.solution.steps:
            print(f"  [{step.step_id}] {step.step_name}")
            print(f"    {step.content[:200]}...")

    await service.close()
    return response


async def main():
    result1 = await test_full_solution()
    result2 = await test_partial_work()

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Case 1 (full solution): {'PASS' if result1.success else 'FAIL'}")
    print(f"Case 3 (partial work):   {'PASS' if result2.success else 'FAIL'}")


if __name__ == "__main__":
    asyncio.run(main())
