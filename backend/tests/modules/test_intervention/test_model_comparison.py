"""Module 2 v2 — Hint Generation Model Comparison Test

Compares hint quality and latency across three configurations:
    1. qwen-turbo      (baseline, fast)
    2. qwen3.5-plus   (no thinking, high quality)
    3. qwen3.5-plus   (thinking enabled, deep reasoning)

Tests R1 (弱提示) hint generation for the gcd-sequence proof problem.

Usage:
    cd backend
    export DASHSCOPE_API_KEY=your_key_here
    python tests/modules/test_intervention/test_model_comparison.py
"""
import asyncio
import json
import os
import sys
import time
import types

# ── Setup ──────────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# Stub motor
motor_stub = types.ModuleType("motor")
motor_asyncio_stub = types.ModuleType("motor.motor_asyncio")
motor_asyncio_stub.AsyncIOMotorClient = object
motor_asyncio_stub.AsyncIOMotorDatabase = object
sys.modules["motor"] = motor_stub
sys.modules["motor.motor_asyncio"] = motor_asyncio_stub

# ── Test scenario ──────────────────────────────────────────────────────────────
SCENARIO = {
    "problem": (
        "设 $a_0, a_1, \\ldots$ 是正整数序列，$(b_n)$ 是由 "
        "$b_n = \\gcd(a_n, a_{n+1})$ 定义的序列。"
        "证明：可以选择序列 $(a_n)$ 使得每个非零自然数恰好等于 "
        "$a_0, b_0, a_1, b_1, \\ldots$ 中的一项。"
    ),
    "student_id": "student_compare",
    "session_id": "session_compare",
    "student_steps": [
        {
            "step_id": "s1",
            "step_name": "理解问题",
            "content": "理解题目要求：构造序列使得每个正整数都出现在 a 或 b 中一次。",
        },
        {
            "step_id": "s2",
            "step_name": "设定初始值",
            "content": "设 a_0 = 1，令 a_1 = 2，则 b_0 = gcd(1, 2) = 1。",
        },
    ],
    "solution_steps": [
        {"step_id": "s1", "step_name": "理解问题",
         "content": "理解题目要求：构造序列使得每个正整数都出现在 a 或 b 中一次。"},
        {"step_id": "s2", "step_name": "设定初始值",
         "content": "设 a_0 = 1，令 a_1 = 2，则 b_0 = gcd(1, 2) = 1。"},
        {"step_id": "s3", "step_name": "归纳假设",
         "content": "假设已覆盖 1,...,n，构造 a_{n+1} = (n+1)×p，a_{n+2} = p，p 为新质数。"},
        {"step_id": "s4", "step_name": "验证覆盖",
         "content": "归纳验证每个正整数恰好出现一次。"},
        {"step_id": "s5", "step_name": "验证唯一性",
         "content": "质数不重复，正整数唯一出现。"},
    ],
}


# ── Service builder ────────────────────────────────────────────────────────────
def build_service(session_id_suffix: str, model: str, enable_thinking: bool = False):
    """Build an InterventionService with specific model and thinking config."""
    from app.modules.intervention.service import InterventionService
    from app.core.state.state_manager import StateManager

    os.environ["INTERVENTION_MODEL"] = model

    state_manager = StateManager()
    session_id = f"{SCENARIO['session_id']}_{session_id_suffix}"
    state_manager.create_session(session_id)
    state_manager.set_module_state(
        session_id,
        "solving",
        {
            "problem": SCENARIO["problem"],
            "solution_steps": SCENARIO["solution_steps"],
            "student_steps": SCENARIO["student_steps"],
            "student_work": "\n".join(s["content"] for s in SCENARIO["student_steps"]),
        },
    )

    class FakeContext:
        def __init__(self):
            self.state_manager = state_manager

    service = InterventionService(context=FakeContext(), enable_thinking=enable_thinking)

    from app.modules.intervention.context_manager import ContextManager
    ctx_mgr: ContextManager = service._context_manager
    ctx_mgr.get_or_create_context(
        session_id=session_id,
        student_id=SCENARIO["student_id"],
        problem_context=SCENARIO["problem"],
        student_input="",
        solution_steps=SCENARIO["solution_steps"],
        student_steps=SCENARIO["student_steps"],
    )
    return service, session_id


# ── Run one scenario ───────────────────────────────────────────────────────────
async def run_scenario(
    label: str,
    model: str,
    enable_thinking: bool,
) -> dict:
    """Run full intervention pipeline and return results."""
    service, session_id = build_service(label, model, enable_thinking)

    from app.modules.intervention.models import InterventionRequest

    request = InterventionRequest(
        session_id=session_id,
        student_id=SCENARIO["student_id"],
        student_input="学生不知道归纳构造怎么下手",
    )

    start = time.time()
    response = await service.create_intervention(request)
    elapsed = time.time() - start

    return {
        "label": label,
        "model": model,
        "thinking": "✅ 思考模式" if enable_thinking else "⚡ 非思考",
        "elapsed": elapsed,
        "success": response.success,
        "message": response.message,
        "breakpoint_type": response.breakpoint_location.get("breakpoint_type") if response.breakpoint_location else None,
        "breakpoint_gap": response.breakpoint_location.get("gap_description") if response.breakpoint_location else None,
        "dimension": response.intervention.metadata.get("dimension") if response.intervention else None,
        "level": response.intervention.metadata.get("prompt_level") if response.intervention else None,
        "content": response.intervention.content if response.intervention else None,
        "reasoning": response.intervention.metadata.get("reasoning") if response.intervention else None,
        "hint_direction": response.intervention.metadata.get("hint_direction") if response.intervention else None,
    }


# ── Main ────────────────────────────────────────────────────────────────────────
async def main():
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║     Module 2 v2 — Hint Generation Model Comparison                          ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝\n")

    configs = [
        ("qwen-turbo",        "qwen-turbo",      False, "🔹 qwen-turbo     (baseline)"),
        ("qwen35-no-think",  "qwen3.5-plus",   False, "🟢 qwen3.5-plus  (无思考)"),
        ("qwen35-think",     "qwen3.5-plus",   True,  "🔴 qwen3.5-plus  (深度思考)"),
    ]

    results = []

    for cfg_label, model, thinking, desc in configs:
        print(f"\n{'─'*80}")
        print(f"  {desc}")
        print(f"  模型: {model} | 思考: {thinking}")
        print(f"{'─'*80}")

        try:
            result = await run_scenario(cfg_label, model, thinking)
            results.append(result)

            print(f"  ⏱  耗时:    {result['elapsed']:.2f}s")
            print(f"  ✓  Success: {result['success']}")
            print(f"  💬 Message: {result['message']}")
            print(f"  📍 断点:    {result['breakpoint_type']} | {result['breakpoint_gap']}")
            print(f"  🧭 维度:    {result['dimension']} | 级别: {result['level']}")
            print(f"\n  💡 提示内容:")
            content_lines = result["content"].split("\n") if result["content"] else []
            for line in content_lines[:5]:
                print(f"     {line}")
            if len(content_lines) > 5:
                print(f"     ... ({len(content_lines) - 5} more lines)")
            print(f"\n  🧠 Reasoning:")
            reasoning_lines = (result["reasoning"] or "").split("\n")
            for line in reasoning_lines[:3]:
                print(f"     {line[:100]}")
            print(f"\n  🎯 Hint Direction:")
            print(f"     {result['hint_direction']}")

        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            results.append({
                "label": cfg_label,
                "model": model,
                "thinking": "✅ 思考模式" if thinking else "⚡ 非思考",
                "elapsed": 0,
                "success": False,
                "error": str(e),
            })

        # Rate limit between runs
        await asyncio.sleep(1)

    # ── Summary table ──────────────────────────────────────────────────────────
    print("\n\n" + "╔" + "═"*78 + "╗")
    print("║" + "  SUMMARY".center(78) + "║")
    print("╚" + "═"*78 + "╝")

    print(f"\n{'配置':<22} {'模型':<16} {'思考':<10} {'耗时':>8} {'断点类型':<16} {'维度':<14} {'级别':<6}")
    print("─" * 90)
    for r in results:
        if "error" in r:
            print(f"  {r['label']:<20} ERROR: {r['error'][:40]}")
            continue
        print(
            f"  {r['label']:<20} "
            f"{r['model']:<16} "
            f"{r['thinking']:<10} "
            f"{r['elapsed']:>7.2f}s "
            f"{str(r['breakpoint_type']):<16} "
            f"{str(r['dimension']):<14} "
            f"{str(r['level']):<6}"
        )

    # ── Comparison analysis ───────────────────────────────────────────────────
    print("\n\n" + "╔" + "═"*78 + "╗")
    print("║" + "  COMPARISON ANALYSIS".center(78) + "║")
    print("╚" + "═"*78 + "╝")

    valid = [r for r in results if r.get("success") and "error" not in r]
    if len(valid) >= 2:
        baseline = valid[0]
        print(f"\n  ▶ 以 {baseline['model']} ({baseline['thinking']}) 为基准\n")

        for r in valid[1:]:
            diff = r["elapsed"] - baseline["elapsed"]
            diff_pct = (diff / baseline["elapsed"]) * 100 if baseline["elapsed"] > 0 else 0
            print(f"  {r['model']} ({r['thinking']}) vs {baseline['model']} ({baseline['thinking']}):")
            print(f"    耗时差异: {'+' if diff > 0 else ''}{diff:.2f}s ({diff_pct:+.0f}%)")

            # Content comparison
            b_content = (baseline.get("content") or "").strip()
            r_content = (r.get("content") or "").strip()
            longer = len(r_content) - len(b_content)
            print(f"    提示长度: {len(b_content)} chars → {len(r_content)} chars ({'+' if longer > 0 else ''}{longer})")

            # Same dimension?
            same_dim = baseline.get("dimension") == r.get("dimension")
            same_level = baseline.get("level") == r.get("level")
            print(f"    维度一致: {'✅' if same_dim else '❌'} ({baseline.get('dimension')} vs {r.get('dimension')})")
            print(f"    级别一致: {'✅' if same_level else '❌'} ({baseline.get('level')} vs {r.get('level')})")

            # Reasoning length
            b_reasoning = len((baseline.get("reasoning") or "").strip())
            r_reasoning = len((r.get("reasoning") or "").strip())
            print(f"    Reasoning 长度: {b_reasoning} → {r_reasoning} chars")
            print()

        # Guardrail results
        print("  📋 Guardrail 检查结果:")
        for r in valid:
            status = "✅ 通过" if r.get("success") else "❌ 失败"
            print(f"    {r['model']} ({r['thinking']}): {status}")

    print(f"\n  总耗时: {sum(r.get('elapsed', 0) for r in results):.2f}s")
    print()


if __name__ == "__main__":
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("ERROR: DASHSCOPE_API_KEY not set")
        sys.exit(1)

    asyncio.run(main())
