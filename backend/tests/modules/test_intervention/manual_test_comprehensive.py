"""Comprehensive manual test for intervention module.

Tests the full intervention flow across all breakpoint types and intensities:
- BreakpointLocator: identify where student is stuck
- BreakpointAnalyzer: analyze what's needed to cross (LLM)
- HintGenerator: generate hints at surface/middle/deep levels (LLM)

Test Matrix:
  4 breakpoint types × 3 intensity levels = 12 scenarios (24 LLM calls total)

Usage:
    python tests/modules/test_intervention/manual_test_comprehensive.py

Requirements:
    export DASHSCOPE_API_KEY=your_key_here
"""
import asyncio
import os
import sys
import time
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# Stub motor for imports
sys.modules['motor'] = type(sys)('motor')
sys.modules['motor.motor_asyncio'] = type(sys)('motor_asyncio')
sys.modules['motor.motor_asyncio'].AsyncIOMotorClient = object
sys.modules['motor.motor_asyncio'].AsyncIOMotorDatabase = object


# =============================================================================
# Test scenarios: each defines problem, student_steps, solution_steps
# =============================================================================

SCENARIOS = [
    {
        "name": "MISSING_STEP",
        "description": "学生完成了前两步，但在第三步（关键构造步骤）之前停住了",
        "problem": (
            "设 $a_0, a_1, \\ldots$ 是正整数序列，$(b_n)$ 是由 $b_n = \\gcd(a_n, a_{n+1})$ 定义的序列。"
            "证明：可以选择序列 $(a_n)$ 使得每个非零自然数恰好等于 $a_0, b_0, a_1, b_1, \\ldots$ 中的一项。"
        ),
        "student_steps": [
            {
                "step_id": "s1",
                "step_name": "理解问题",
                "content": "理解题目要求：构造序列使得每个正整数都出现在 a 或 b 中一次。"
            },
            {
                "step_id": "s2",
                "step_name": "设定初始值",
                "content": "设 a_0 = 1。"
            },
        ],
        "solution_steps": [
            {
                "step_id": "s1",
                "step_name": "理解问题",
                "content": "理解题目要求：构造序列使得每个正整数都出现在 a 或 b 中一次。"
            },
            {
                "step_id": "s2",
                "step_name": "设定初始值",
                "content": "设 a_0 = 1，令 a_1 = 2，则 b_0 = gcd(1, 2) = 1。"
            },
            {
                "step_id": "s3",
                "step_name": "归纳构造",
                "content": "假设已覆盖 1,...,n，构造 a_{n+1} = (n+1)×p，a_{n+2} = p，其中 p 是新质数。"
            },
            {
                "step_id": "s4",
                "step_name": "验证覆盖",
                "content": "归纳验证每个正整数恰好出现一次。"
            },
        ],
    },
    {
        "name": "WRONG_DIRECTION",
        "description": "学生的步骤与参考解法方向不同，在第二步就偏离了正确路径",
        "problem": (
            "求函数 $f(x) = \\frac{x^2 - 1}{x - 1}$ 在 $x = 1$ 处的极限。"
        ),
        "student_steps": [
            {
                "step_id": "s1",
                "step_name": "代入法尝试",
                "content": "将 x = 1 代入得 f(1) = 0/0，是不定式。"
            },
            {
                "step_id": "s2",
                "step_name": "错误方法",
                "content": "因为 0/0 可以约去，所以极限是 0。"
            },
        ],
        "solution_steps": [
            {
                "step_id": "s1",
                "step_name": "识别不定式",
                "content": "代入 x=1 得 0/0，需要化简。"
            },
            {
                "step_id": "s2",
                "step_name": "因式分解",
                "content": "分子 x²-1 = (x-1)(x+1)，所以 f(x) = x+1 (x≠1)。"
            },
            {
                "step_id": "s3",
                "step_name": "求极限",
                "content": "lim_{x→1} f(x) = lim_{x→1} (x+1) = 2。"
            },
        ],
    },
    {
        "name": "INCOMPLETE_STEP",
        "description": "学生写了一个步骤但内容太短，没有完成该步骤的推理",
        "problem": (
            "证明：若函数 $f(x)$ 在 $[a,b]$ 上连续，则 $f(x)$ 在 $[a,b]$ 上有最大值和最小值。"
        ),
        "student_steps": [
            {
                "step_id": "s1",
                "step_name": "连续函数性质",
                "content": "连续函数在闭区间上有界。"
            },
            {
                "step_id": "s2",
                "step_name": "上确界",
                "content": "因为 f 有界，所以存在上确界。"
            },
        ],
        "solution_steps": [
            {
                "step_id": "s1",
                "step_name": "有界性",
                "content": "由连续函数的性质，f 在 [a,b] 上有界。"
            },
            {
                "step_id": "s2",
                "step_name": "上确界存在",
                "content": "有界集必有上确界和下确界，设 M = sup f([a,b])，m = inf f([a,b])。"
            },
            {
                "step_id": "s3",
                "step_name": "最大值点",
                "content": "由极值定理，f 在 [a,b] 上必能取得最大值 M 和最小值 m。"
            },
        ],
    },
    {
        "name": "STUCK",
        "description": "学生只写了起始，完全没有后续步骤，无法确定断点位置",
        "problem": (
            "设正项数列 ${a_n}$ 满足 $\\lim_{n \\to \\infty} a_n = 0$。"
            "判断级数 $\\sum_{n=1}^{\\infty} a_n$ 的敛散性，并说明理由。"
        ),
        "student_steps": [
            {
                "step_id": "s1",
                "step_name": "起始",
                "content": "已知 a_n → 0。"
            },
        ],
        "solution_steps": [
            {
                "step_id": "s1",
                "step_name": "分析条件",
                "content": "已知 a_n → 0，但仅此条件不足以判断级数敛散性。"
            },
            {
                "step_id": "s2",
                "step_name": "举反例",
                "content": "反例：a_n = 1/n → 0，但 Σ1/n 发散。"
            },
            {
                "step_id": "s3",
                "step_name": "另一个正例",
                "content": "正例：a_n = 1/n² → 0，Σ1/n² 收敛。"
            },
            {
                "step_id": "s4",
                "step_name": "结论",
                "content": "仅由 a_n → 0 无法判断 Σa_n 的敛散性，需要更多条件。"
            },
        ],
    },
]

INTENSITY_LEVELS = [
    (0.2, "surface"),
    (0.5, "middle"),
    (0.8, "deep"),
]


async def run_scenario(scenario: dict, intensity: float, level: str):
    """Run one intervention scenario at one intensity level."""
    from app.modules.intervention.locator.breaker import BreakpointLocator
    from app.modules.intervention.analyzer.analyzer import BreakpointAnalyzer
    from app.modules.intervention.generator.generator import HintGenerator
    from app.modules.solving.models import TeachingStep

    locator = BreakpointLocator()
    student_steps_obj = [
        TeachingStep(step_id=s["step_id"], step_name=s["step_name"], content=s["content"])
        for s in scenario["student_steps"]
    ]
    solution_steps_obj = [
        TeachingStep(step_id=s["step_id"], step_name=s["step_name"], content=s["content"])
        for s in scenario["solution_steps"]
    ]

    # Step 1: Locate breakpoint
    location = locator.locate(student_steps_obj, solution_steps_obj)

    # Step 2: Analyze (LLM)
    analyzer = BreakpointAnalyzer()
    solution_step_contents = [s["content"] for s in scenario["solution_steps"]]
    analysis = await analyzer.analyze(
        breakpoint_location=location,
        problem=scenario["problem"],
        student_work="\n".join(s["content"] for s in scenario["student_steps"]),
        solution_steps=solution_step_contents,
    )

    # Step 3: Generate hints (LLM)
    generator = HintGenerator()
    hint = await generator.generate(
        analysis=analysis,
        problem=scenario["problem"],
        intensity=intensity,
    )

    return {
        "breakpoint_type": location.breakpoint_type.value,
        "breakpoint_position": location.breakpoint_position,
        "gap_description": location.gap_description,
        "analysis": {
            "required_knowledge": analysis.required_knowledge,
            "required_connection": analysis.required_connection,
            "possible_approaches": analysis.possible_approaches,
            "difficulty_level": analysis.difficulty_level,
        },
        "hint": {
            "level": hint.level,
            "approach_used": hint.approach_used,
            "content": hint.content,
        },
    }


async def run_all_tests():
    """Run the full test matrix."""
    print("=" * 90)
    print("INTERVENTION MODULE — COMPREHENSIVE E2E TEST")
    print(f"Scenarios: {len(SCENARIOS)} | Intensities per scenario: {len(INTENSITY_LEVELS)}")
    print(f"Total runs: {len(SCENARIOS) * len(INTENSITY_LEVELS)} LLM call pairs (analyze + generate)")
    print("=" * 90)

    all_results = {}

    for scenario in SCENARIOS:
        scenario_name = scenario["name"]
        print(f"\n{'=' * 90}")
        print(f"SCENARIO: {scenario_name}")
        print(f"Description: {scenario['description']}")
        print("=" * 90)

        results_for_scenario = []

        for intensity, level in INTENSITY_LEVELS:
            print(f"\n  [{level.upper():>6}] intensity={intensity}")
            print("-" * 70)

            start = time.time()
            try:
                result = await run_scenario(scenario, intensity, level)
                elapsed = time.time() - start
                results_for_scenario.append(result)

                # Print results
                print(f"  Breakpoint: {result['breakpoint_type']} @ pos {result['breakpoint_position']}")
                print(f"  Gap: {result['gap_description']}")
                print(f"  Analysis:")
                print(f"    Knowledge: {result['analysis']['required_knowledge']}")
                print(f"    Connection: {result['analysis']['required_connection']}")
                print(f"    Approaches: {result['analysis']['possible_approaches']}")
                print(f"    Difficulty: {result['analysis']['difficulty_level']}")
                print(f"  Hint ({result['hint']['level']}, {elapsed:.1f}s):")
                print(f"    Approach: {result['hint']['approach_used']}")
                hint_lines = result['hint']['content'].strip().split("\n")
                for line in hint_lines[:6]:
                    print(f"      {line}")
                if len(hint_lines) > 6:
                    print(f"      ... ({len(hint_lines) - 6} more lines)")

            except Exception as e:
                elapsed = time.time() - start
                print(f"  ERROR after {elapsed:.1f}s: {e}")
                results_for_scenario.append({"error": str(e)})

            # Rate limiting between LLM calls
            await asyncio.sleep(0.5)

        all_results[scenario_name] = results_for_scenario

    # =====================================================================
    # Summary table
    # =====================================================================
    print("\n" + "=" * 90)
    print("SUMMARY")
    print("=" * 90)
    print()
    print(f"{'Scenario':<45} {'Surface':<20} {'Middle':<20} {'Deep':<20}")
    print("-" * 90)

    for scenario in SCENARIOS:
        name = scenario["name"]
        results = all_results[scenario["name"]]
        hint_levels = []
        for r in results:
            if "error" in r:
                hint_levels.append("ERROR")
            else:
                hint_levels.append(f"{r['hint']['level']}({r['breakpoint_type']})")

        print(f"{name:<45} {hint_levels[0]:<20} {hint_levels[1]:<20} {hint_levels[2]:<20}")

    print("\n" + "=" * 90)
    print("TEST COMPLETE")
    print("=" * 90)

    return all_results


if __name__ == "__main__":
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("ERROR: DASHSCOPE_API_KEY not set")
        print("  export DASHSCOPE_API_KEY=your_key_here")
        sys.exit(1)

    # Redirect stdout to avoid GBK encoding errors on Chinese output
    import io, codecs
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    asyncio.run(run_all_tests())
