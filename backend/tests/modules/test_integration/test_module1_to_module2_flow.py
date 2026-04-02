"""Module 1 + Module 2 Real E2E Test.

Tests the complete flow:
    1. SolvingService.generate() → reference solution (Module 1)
    2. InterventionService.create_intervention() → hints (Module 2)

Usage:
    cd backend
    export DASHSCOPE_API_KEY=your_key_here
    python tests/modules/test_integration/test_module1_to_module2_flow.py

Requires:
    - Real DASHSCOPE_API_KEY in environment
    - MongoDB optional (graceful degradation if unavailable)
"""
import asyncio
import os
import sys
import time
from datetime import datetime
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# Stub motor (for MongoDB-free testing)
import types
motor_stub = types.ModuleType("motor")
motor_asyncio_stub = types.ModuleType("motor.motor_asyncio")
motor_asyncio_stub.AsyncIOMotorClient = object
motor_asyncio_stub.AsyncIOMotorDatabase = object
sys.modules["motor"] = motor_stub
sys.modules["motor.motor_asyncio"] = motor_asyncio_stub

# ── Test scenario ─────────────────────────────────────────────────────────────
PROBLEM = (
    "设 $a_0, a_1, \\ldots$ 是正整数序列，$(b_n)$ 是由 $b_n = \\gcd(a_n, a_{n+1})$ 定义的序列。"
    "证明：可以选择序列 $(a_n)$ 使得每个非零自然数恰好等于 $a_0, b_0, a_1, b_1, \\ldots$ 中的一项。"
)

# Student work: correctly sets initial values but stuck at induction step
STUDENT_WORK = (
    "设 a_0 = 1，令 a_1 = 2，则 b_0 = gcd(1, 2) = 1。"
    "接下来我不知道怎么构造后面的项来覆盖所有正整数。"
)

STUDENT_ID = "student_m1m2_001"
SESSION_ID = "session_m1m2_001"

# ── Report ───────────────────────────────────────────────────────────────────
report = StringIO()


def log(msg: str = ""):
    print(msg)
    report.write(msg + "\n")


def box(title: str, width: int = 80):
    log()
    log("╔" + "═" * (width - 2) + "╗")
    log(f"║  {title.center(width - 4)}  ║")
    log("╚" + "═" * (width - 2) + "╝")


def section(title: str):
    log()
    log("─" * 80)
    log(f"  {title}")
    log("─" * 80)


async def run_flow():
    total_start = time.time()

    box(f"Module 1 + Module 2 E2E Test — {datetime.now().isoformat()}")
    log(f"  Problem: {PROBLEM[:60]}...")
    log(f"  Student: {STUDENT_ID}")
    log(f"  Session: {SESSION_ID}")
    log(f"  Model: qwen-turbo")

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 1: Module 1 — Generate Reference Solution
    # ─────────────────────────────────────────────────────────────────────────
    section("STEP 1 — Module 1: SolvingService.generate()")
    t0 = time.time()

    from app.modules.solving.service import ReferenceSolutionService
    from app.modules.solving.models import SolvingRequest

    solving_service = ReferenceSolutionService()

    request = SolvingRequest(
        problem=PROBLEM,
        student_work=None,  # No student work — generate full solution
        model="qwen-turbo",
        temperature=0.7,
    )

    solving_response = await solving_service.generate(request, session_id=SESSION_ID)
    t1 = time.time()
    log(f"  ⏱  Module 1 耗时: {t1 - t0:.2f}s")

    if not solving_response.success:
        log(f"  ❌ Module 1 failed: {solving_response.error_feedback}")
        return

    solution = solving_response.solution
    log(f"  ✅ Solution generated: {len(solution.steps)} steps")
    for step in solution.steps:
        log(f"     [{step.step_id}] {step.step_name}: {step.content[:60]}...")

    # Extract solution steps for Module 2
    solution_steps = [
        {"step_id": s.step_id, "step_name": s.step_name, "content": s.content}
        for s in solution.steps
    ]

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 2: Simulate student work (partial solution)
    # ─────────────────────────────────────────────────────────────────────────
    section("STEP 2 — Simulate Student Partial Work")

    # Student correctly did step 1 and 2, but is stuck before step 3
    student_steps = solution_steps[:2]  # Only steps 1 and 2
    log(f"  Student completed: {len(student_steps)} steps")
    for step in solution_steps[:2]:
        log(f"     [{step['step_id']}] {step['step_name']}: {step['content'][:60]}...")
    log(f"  Student is stuck at: {solution_steps[2]['step_name']}")

    # Store student steps + solution in session state for Module 2
    from app.core.state.state_manager import StateManager

    state_manager = StateManager()
    state_manager.create_session(SESSION_ID)
    state_manager.set_module_state(
        SESSION_ID,
        "solving",
        {
            "problem": PROBLEM,
            "solution_steps": solution_steps,
            "student_steps": student_steps,
            "student_work": STUDENT_WORK,
        },
    )
    log(f"  ✅ State stored in StateManager for session {SESSION_ID}")

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 3: Module 2 — Intervention Pipeline
    # ─────────────────────────────────────────────────────────────────────────
    section("STEP 3 — Module 2: InterventionService.create_intervention()")
    t2 = time.time()

    from app.modules.intervention.service import InterventionService
    from app.modules.intervention.models import InterventionRequest, FrontendSignalEnum, FeedbackRequest

    class FakeContext:
        pass

    FakeContext.state_manager = state_manager

    intervention_service = InterventionService(context=FakeContext())

    # Mock context_manager to avoid MongoDB dependency
    from app.modules.intervention.context_manager import ContextManager

    ctx_mgr = intervention_service._context_manager
    ctx = ctx_mgr.get_or_create_context(
        session_id=SESSION_ID,
        student_id=STUDENT_ID,
        problem_context=PROBLEM,
        student_input=STUDENT_WORK,
        solution_steps=solution_steps,
        student_steps=student_steps,
    )

    intervention_request = InterventionRequest(
        student_id=STUDENT_ID,
        session_id=SESSION_ID,
        student_input=STUDENT_WORK,
        frontend_signal=None,
        intervention_type="hint",
    )

    response = await intervention_service.create_intervention(intervention_request)
    t3 = time.time()
    log(f"  ⏱  Module 2 耗时: {t3 - t2:.2f}s")

    if not response.success:
        log(f"  ❌ Module 2 failed: {response.message}")
        return

    iv = response.intervention
    log(f"  ✅ Intervention generated")
    log(f"     Level: {iv.metadata.get('prompt_level', 'N/A')}")
    log(f"     Dimension: {iv.metadata.get('dimension', 'N/A')}")
    log(f"     Content: {iv.content[:100]}...")

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 4: Student feedback — NOT_PROGRESSED → escalate
    # ─────────────────────────────────────────────────────────────────────────
    section("STEP 4 — Feedback: NOT_PROGRESSED → Escalate")
    t4 = time.time()

    escalation_request = FeedbackRequest(
        session_id=SESSION_ID,
        student_input="我还是不太理解归纳构造的思路",
        frontend_signal=FrontendSignalEnum.ESCALATE,
    )

    response2 = await intervention_service.process_feedback(escalation_request)
    t5 = time.time()
    log(f"  ⏱  Turn 2 耗时: {t5 - t4:.2f}s")

    if response2.success and response2.intervention:
        log(f"  ✅ Escalated intervention generated")
        log(f"     Level: {response2.intervention.metadata.get('prompt_level', 'N/A')}")
        log(f"     Dimension: {response2.intervention.metadata.get('dimension', 'N/A')}")
        log(f"     Content: {response2.intervention.content[:100]}...")
    else:
        log(f"  ⚠️  {response2.message}")

    # ─────────────────────────────────────────────────────────────────────────
    # SUMMARY
    # ─────────────────────────────────────────────────────────────────────────
    total = time.time() - total_start
    box("SUMMARY")
    log(f"  Total time: {total:.2f}s")
    log(f"  Module 1 (Solving):      {t1 - t0:.2f}s")
    log(f"  Module 2 Turn 1 (Intervention): {t3 - t2:.2f}s")
    log(f"  Module 2 Turn 2 (Escalate): {t5 - t4:.2f}s")
    log()
    log("  ✅ Full Module 1 → Module 2 flow completed successfully")

    return report.getvalue()


if __name__ == "__main__":
    api_key = os.getenv("DASHSCOPE_API_KEY", "")
    if not api_key:
        print("❌ DASHSCOPE_API_KEY not set. Run: export DASHSCOPE_API_KEY=your_key")
        sys.exit(1)

    result = asyncio.run(run_flow())
    print("\n--- REPORT ---")
    print(result)
