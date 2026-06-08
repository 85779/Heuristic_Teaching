#!/usr/bin/env python3
"""Manual E2E test for Module 3 - requires real DashScope API key.

Run with: python manual_e2e_test.py
Set DASHSCOPE_API_KEY environment variable before running.
"""

import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.modules.recommendation.knowledge_base.knowledge_api import KnowledgeBaseAPI
from app.modules.recommendation.retriever.knowledge_anchor_retriever import KnowledgeAnchorRetriever
from app.modules.recommendation.generator.problem_generator import ProblemGenerator
from app.modules.recommendation.generator.prompt_templates import ProblemPromptTemplates
from app.modules.recommendation.generator.problem_validator import ProblemValidator
from app.modules.recommendation.generator.fallback_generator import FallbackGenerator
from app.modules.recommendation.scorer.difficulty_scorer import DifficultyScorer
from app.modules.recommendation.models import StudentProfile, TriggerEvent, TriggerOutcome
from app.infrastructure.llm.dashscope_client import DashScopeClient


async def build_service():
    """Build the recommendation service with real components."""
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY not set")

    kb_api = KnowledgeBaseAPI(kb_dir="data/knowledge_ontology")
    llm_client = DashScopeClient(api_key=api_key, model="qwen-turbo")
    anchor_retriever = KnowledgeAnchorRetriever(kb_api=kb_api)
    prompt_templates = ProblemPromptTemplates()
    problem_validator = ProblemValidator()
    problem_generator = ProblemGenerator(
        llm_client=llm_client,
        prompt_templates=prompt_templates,
        validator=problem_validator,
        model="qwen-turbo",
    )
    fallback = FallbackGenerator()
    scorer = DifficultyScorer()

    return kb_api, anchor_retriever, problem_generator, fallback, scorer


async def test_r_type_scenario():
    """Test Case 1: R-type student (ratio > 0.65) → SAME_KP anchor."""
    print("\n" + "=" * 60)
    print("Test 1: R-type Student (dimension_ratio=0.75)")
    print("Expected: SAME_KP anchor")
    print("=" * 60)

    kb, retriever, generator, fallback, scorer = await build_service()

    profile = StudentProfile(
        student_id="test_r_student",
        dimension_ratio=0.75,
        recent_problems=[],
        weak_kps=[],
        mastered_kps=["KP_1_01"],
        recent_methods=[],
    )

    trigger = TriggerEvent(
        outcome=TriggerOutcome.SOLVED,
        current_problem_kps=["KP_3_13"],
        current_method="配方法",
        current_difficulty=2,
        session_id="s1",
    )

    anchor = await retriever.retrieve(
        profile=profile,
        current_kps=trigger.current_problem_kps,
        current_method=trigger.current_method,
    )

    print(f"Anchor type: {anchor.anchor_type}")
    print(f"Target KPs: {[kp.name for kp in anchor.target_kps]}")
    print(f"Goal: {anchor.generation_goal}")

    target_diff = scorer.calculate_target(trigger.current_difficulty, trigger.outcome)
    print(f"Target difficulty: {target_diff}")

    result = await generator.generate(anchor, target_diff, max_retries=2)

    if result.success:
        p = result.problem
        print(f"\n✅ Generated problem:")
        print(f"  Text: {p.problem_text[:80]}...")
        print(f"  Answer: {p.answer}")
        print(f"  Difficulty: {p.difficulty}")
        print(f"  Method: {p.method_used}")
        print(f"  Why: {p.why_recommended}")
    else:
        print(f"\n⚠️  Generation failed: {result.error}")
        fallback_p = fallback.generate(anchor, target_diff, reason=result.error or "")
        print(f"  Fallback problem: {fallback_p.problem_text[:80]}...")


async def test_m_type_scenario():
    """Test Case 2: M-type student (ratio < 0.35) → VARIATION anchor."""
    print("\n" + "=" * 60)
    print("Test 2: M-type Student (dimension_ratio=0.20)")
    print("Expected: VARIATION anchor")
    print("=" * 60)

    kb, retriever, generator, fallback, scorer = await build_service()

    profile = StudentProfile(
        student_id="test_m_student",
        dimension_ratio=0.20,
        recent_problems=[],
        weak_kps=[],
        mastered_kps=["KP_1_01"],
        recent_methods=["配方法"],
    )

    trigger = TriggerEvent(
        outcome=TriggerOutcome.SOLVED,
        current_problem_kps=["KP_3_13"],
        current_method="配方法",
        current_difficulty=3,
        session_id="s2",
    )

    anchor = await retriever.retrieve(
        profile=profile,
        current_kps=trigger.current_problem_kps,
        current_method=trigger.current_method,
    )

    print(f"Anchor type: {anchor.anchor_type}")
    print(f"Target KPs: {[kp.name for kp in anchor.target_kps]}")
    print(f"Exclude methods: {anchor.exclude_methods}")

    target_diff = scorer.calculate_target(trigger.current_difficulty, trigger.outcome)
    result = await generator.generate(anchor, target_diff, max_retries=2)

    if result.success:
        p = result.problem
        print(f"\n✅ Generated problem:")
        print(f"  Text: {p.problem_text[:80]}...")
        print(f"  Method: {p.method_used}")
    else:
        print(f"\n⚠️  Generation failed: {result.error}")


async def test_escalation_scenario():
    """Test Case 3: MAX_ESCALATION → lower difficulty."""
    print("\n" + "=" * 60)
    print("Test 3: MAX_ESCALATION (difficulty 3 → should be 2)")
    print("Expected: Difficulty lowered")
    print("=" * 60)

    kb, retriever, generator, fallback, scorer = await build_service()

    profile = StudentProfile(
        student_id="test_escalate",
        dimension_ratio=0.5,
        recent_problems=[],
        weak_kps=["KP_2_01"],
        mastered_kps=[],
        recent_methods=[],
    )

    trigger = TriggerEvent(
        outcome=TriggerOutcome.MAX_ESCALATION,
        current_problem_kps=["KP_3_13"],
        current_method="配方法",
        current_difficulty=3,
        session_id="s3",
    )

    target_diff = scorer.calculate_target(trigger.current_difficulty, trigger.outcome)
    print(f"Current difficulty: {trigger.current_difficulty}")
    print(f"Target difficulty: {target_diff}")

    anchor = await retriever.retrieve(
        profile=profile,
        current_kps=trigger.current_problem_kps,
        current_method=trigger.current_method,
    )

    result = await generator.generate(anchor, target_diff, max_retries=2)

    if result.success:
        p = result.problem
        print(f"\n✅ Generated problem (difficulty={p.difficulty})")
        print(f"  Text: {p.problem_text[:80]}...")
    else:
        print(f"\n⚠️  Generation failed, using fallback")
        fb = fallback.generate(anchor, target_diff, reason="MAX_ESCALATION")
        print(f"  Fallback difficulty: {fb.difficulty}")


async def main():
    print("Module 3 E2E Manual Test")
    print("=" * 60)
    print(f"DashScope API Key: {'Set ✅' if os.environ.get('DASHSCOPE_API_KEY') else 'NOT SET ❌'}")
    print(f"Knowledge Base: data/knowledge_ontology")
    print("=" * 60)

    if not os.environ.get("DASHSCOPE_API_KEY"):
        print("\n⚠️  WARNING: DASHSCOPE_API_KEY not set. Set it with:")
        print("  Windows: set DASHSCOPE_API_KEY=your_key")
        print("  Linux/Mac: export DASHSCOPE_API_KEY=your_key")
        print("\nFalling back to fallback generator tests only.\n")
        return

    try:
        await test_r_type_scenario()
        await test_m_type_scenario()
        await test_escalation_scenario()
        print("\n" + "=" * 60)
        print("All E2E tests completed!")
    except Exception as e:
        print(f"\n❌ E2E test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())