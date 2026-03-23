"""End-to-end test for solving module with qwen-turbo."""
import asyncio
import os
import sys
import json

test_dir = os.path.abspath(os.path.dirname(__file__))
backend_dir = os.path.abspath(os.path.join(test_dir, '..', '..', '..'))
sys.path.insert(0, backend_dir)
print(f"sys.path[0] = {backend_dir}")

# Load .env file
env_path = os.path.join(backend_dir, '.env')
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
    print("Test Case 1: Full Solution (qwen-turbo)")
    print("=" * 60)

    service = ReferenceSolutionService()
    request = SolvingRequest(
        problem=PROBLEM,
        student_work=None,
        model="qwen-turbo",
        temperature=0.7,
        max_tokens=2048,
        enable_thinking=False,
    )

    try:
        response = await service.generate(request)
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()
        await service.close()
        return None

    print(f"Success: {response.success}")
    print(f"Evaluation - is_correct: {response.evaluation.is_correct}")
    print(f"Evaluation - confidence: {response.evaluation.confidence}")

    if response.solution:
        print(f"\nAnswer: {response.solution.answer}")
        print(f"\nSteps ({len(response.solution.steps)}):")
        for step in response.solution.steps:
            print(f"  [{step.step_id}] {step.step_name}")
            print(f"    {step.content[:150]}...")

        # Write to file
        result = {
            "success": response.success,
            "answer": response.solution.answer,
            "steps": [
                {"step_id": s.step_id, "step_name": s.step_name, "content": s.content}
                for s in response.solution.steps
            ],
        }
        with open(os.path.join(test_dir, 'e2e_result.json'), 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print("\nResult written to e2e_result.json")
    elif response.error_feedback:
        print(f"\nError feedback: {response.error_feedback.summary}")
        print(f"Suggestion: {response.error_feedback.suggestion}")

    await service.close()
    return response


async def main():
    result = await test_full_solution()
    print("\n" + "=" * 60)
    print("Result:", "PASS" if result and result.success else "FAIL")


if __name__ == "__main__":
    asyncio.run(main())
