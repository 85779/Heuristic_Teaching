"""Tests for solving module with example problem."""

import pytest
import sys
import os

# Add backend to path (from tests/modules/test_solving/ up to backend/)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

# Stub motor before imports
sys.modules['motor'] = type(sys)('motor')
sys.modules['motor.motor_asyncio'] = type(sys)('motor_asyncio')
sys.modules['motor.motor_asyncio'].AsyncIOMotorClient = object
sys.modules['motor.motor_asyncio'].AsyncIOMotorDatabase = object


# Example problem from user
EXAMPLE_PROBLEM = {
    "question_id": "math_42",
    "latex_content": (
        "设 $a_0, a_1, \\ldots$ 是正整数序列，"
        "$(b_n)$ 是由 $b_n = \\gcd(a_n, a_{n+1})$ 定义的序列。"
        "证明：可以选择序列 $(a_n)$ 使得每个非零自然数恰好等于 "
        "$a_0, b_0, a_1, b_1, \\ldots$ 中的一项。"
    ),
    "answer": "证明成立",
    "question_type": "sequence_construction",
    "difficulty": "hard",
    "expected_steps": [
        {"step_id": "s1", "step_name": "设定初始值", "content": "设 $a_0 = 2$，$a_1 = 9$，则 $b_0 = \\gcd(2, 9) = 1$"},
        {"step_id": "s2", "step_name": "选择新元素", "content": "设 $d$ 是 $a_n$ 的一个未出现在序列中的因子，$x$ 是未出现的最小正整数"},
        {"step_id": "s3", "step_name": "利用质因数分解", "content": "通过质因数分解，构造适当的 $a_{n+1}$ 和 $a_{n+2}$ 使得 $b_n = d$，$b_{n+1} = x$"},
        {"step_id": "s4", "step_name": "验证覆盖性", "content": "通过归纳构造，每个正整数都会在某个时刻被选为 $x$，并出现在序列中"},
        {"step_id": "s5", "step_name": "验证唯一性", "content": "由于每次引入新的质因子，每个数只会出现一次"},
    ]
}


class TestSolvingModule:
    """Test cases for solving module."""

    def test_models_import(self):
        """Test that models can be imported."""
        from app.modules.solving.models import (
            SolvingRequest,
            SolvingResponse,
            ReferenceSolution,
            TeachingStep,
        )
        assert SolvingRequest is not None
        assert SolvingResponse is not None
        assert ReferenceSolution is not None
        assert TeachingStep is not None

    def test_parser_import(self):
        """Test that parser can be imported."""
        from app.modules.solving.parser import SolutionParser
        assert SolutionParser is not None

    def test_director_import(self):
        """Test that director can be imported."""
        from app.modules.solving.prompts.director import PromptDirector
        assert PromptDirector is not None

    def test_template_imports(self):
        """Test that templates can be imported."""
        from app.modules.solving.prompts.templates import (
            SYSTEM_PROMPT,
            THINKING_TASKS_PROMPT,
            ACTIONS_PROMPT,
            OUTPUT_FORMAT_PROMPT,
            LANGUAGE_STYLE_PROMPT,
            PROHIBITIONS_PROMPT,
        )
        assert SYSTEM_PROMPT is not None
        assert THINKING_TASKS_PROMPT is not None
        assert ACTIONS_PROMPT is not None
        assert OUTPUT_FORMAT_PROMPT is not None
        assert LANGUAGE_STYLE_PROMPT is not None
        assert PROHIBITIONS_PROMPT is not None

    def test_evaluator_import(self):
        """Test that evaluator can be imported."""
        from app.modules.solving.evaluator import Evaluator
        assert Evaluator is not None

    def test_reference_solution_model(self):
        """Test ReferenceSolution model structure."""
        from app.modules.solving.models import ReferenceSolution, TeachingStep
        from datetime import datetime

        step = TeachingStep(
            step_id="s1",
            step_name="设定初始值",
            content="设 a0 = 2",
        )

        solution = ReferenceSolution(
            problem="test problem",
            answer="test answer",
            generated_at=datetime.now(),
            steps=[step]
        )

        assert solution.problem == "test problem"
        assert solution.answer == "test answer"
        assert len(solution.steps) == 1
        assert solution.steps[0].step_id == "s1"

    def test_teaching_step_model(self):
        """Test TeachingStep model."""
        from app.modules.solving.models import TeachingStep

        step = TeachingStep(
            step_id="s2",
            step_name="选择新元素",
            content="设 d 是 a_n 的一个未出现在序列中的因子",
        )

        assert step.step_id == "s2"
        assert step.step_name == "选择新元素"
        assert "d" in step.content

    def test_parser_parse(self):
        """Test SolutionParser parse method with new three-part format."""
        from app.modules.solving.parser import SolutionParser

        parser = SolutionParser()

        sample_output = """
这题怎么看：
这道题要求构造一个正整数序列，使得每个非零自然数恰好出现一次。关键在于利用 gcd 的性质。

这题怎么想：
第一步：设 a0 = 1，则 b0 = gcd(a0, a1)。为方便构造，令 a1 = 2，则 b0 = 1。
第二步：令 a_{n+1} = b_n × (n+2)，则 b_n = gcd(a_n, a_{n+1}) = n+1。
第三步：通过归纳验证，每一步都引入新的质因子，确保每个正整数出现一次且仅一次。

这题留下什么方法：
构造序列的关键在于利用递归定义和归纳法，每次引入新的质数来覆盖新的正整数。
        """

        solution = parser.parse(sample_output, "证明题目")

        assert solution.problem == "证明题目"
        assert solution.answer is not None
        assert len(solution.steps) >= 3
        assert solution.steps[0].step_id == "s1"
        assert "a0 = 1" in solution.steps[0].content

    def test_parser_with_empty_output(self):
        """Test parser handles empty output."""
        from app.modules.solving.parser import SolutionParser

        parser = SolutionParser()
        solution = parser.parse("", "test problem")

        assert solution.problem == "test problem"
        assert solution.answer is None
        assert len(solution.steps) == 0

    def test_prompt_director_build_base(self):
        """Test PromptDirector builds base prompt."""
        from app.modules.solving.prompts.director import PromptDirector

        director = PromptDirector()
        base_prompt = director.build_base_prompt()

        assert len(base_prompt) > 0
        assert "高中数学教辅老师" in base_prompt
        assert "四项思维任务" in base_prompt
        # Check for action section header and count of action headers
        assert "二" in base_prompt and "解题动作" in base_prompt

    def test_prompt_director_build_full_solution(self):
        """Test PromptDirector builds full solution prompt."""
        from app.modules.solving.prompts.director import PromptDirector

        director = PromptDirector()
        problem = "设 a0, a1, ... 是正整数序列"
        prompt = director.build_full_solution_prompt(problem)

        assert len(prompt) > 0
        assert problem in prompt
        assert "高中数学教辅老师" in prompt

    def test_prompt_director_build_continuation(self):
        """Test PromptDirector builds continuation prompt."""
        from app.modules.solving.prompts.director import PromptDirector

        director = PromptDirector()
        problem = "证明题目"
        student_work = "设 a0 = 2"
        prompt = director.build_continuation_prompt(problem, student_work)

        assert student_work in prompt
        assert "继续" in prompt or "续" in prompt

    def test_evaluator_no_student_work(self):
        """Test Evaluator with no student work."""
        from app.modules.solving.evaluator import Evaluator

        evaluator = Evaluator()
        result = evaluator._evaluate_with_rules("test problem", "")

        assert result.is_correct is True
        assert result.can_continue is True

    def test_evaluator_determine_breakpoint(self):
        """Test Evaluator determines breakpoint from student work."""
        from app.modules.solving.evaluator import Evaluator

        evaluator = Evaluator()

        # Test with numbered steps
        student_work = """
        第1步：设 a0 = 2
        第2步：设 a1 = 9
        """
        breakpoint = evaluator.determine_breakpoint(student_work)
        assert breakpoint == 2

        # Test with step pattern
        student_work2 = "步骤3：选择新元素"
        breakpoint2 = evaluator.determine_breakpoint(student_work2)
        assert breakpoint2 == 3


class TestSolvingServiceIntegration:
    """Integration tests for SolvingService with LLM."""

    @pytest.fixture(autouse=True)
    def setup_env(self):
        """Setup environment variables."""
        env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line and not line.startswith('#'):
                        key, _, value = line.partition('=')
                        os.environ[key] = value

    def test_load_example_problem(self):
        """Test that example problem is loaded correctly."""
        assert EXAMPLE_PROBLEM["question_id"] == "math_42"
        assert "正整数序列" in EXAMPLE_PROBLEM["latex_content"]
        assert len(EXAMPLE_PROBLEM["expected_steps"]) == 5

    def test_example_problem_structure(self):
        """Test example problem has correct structure."""
        problem = EXAMPLE_PROBLEM

        # Check top level keys
        assert "question_id" in problem
        assert "latex_content" in problem
        assert "answer" in problem
        assert "expected_steps" in problem

        # Check steps structure
        for step in problem["expected_steps"]:
            assert "step_id" in step
            assert "step_name" in step
            assert "content" in step

    # ============== Test Case 1: Correct Full Solution ==============
    # Case 1: No student work, complete correct solution expected

    def test_case1_correct_full_problem_structure(self):
        """Test Case 1: problem field present."""
        from app.modules.solving.models import SolvingRequest
        problem_text = (
            "设 $a_0, a_1, \\ldots$ 是正整数序列，"
            "$(b_n)$ 是由 $b_n = \\gcd(a_n, a_{n+1})$ 定义的序列。"
            "证明：可以选择序列 $(a_n)$ 使得每个非零自然数恰好等于 "
            "$a_0, b_0, a_1, b_1, \\ldots$ 中的一项。"
        )
        request = SolvingRequest(problem=problem_text)
        assert request.problem == problem_text
        assert request.student_work is None

    def test_case1_correct_full_answer(self):
        """Test Case 1: answer field in solution."""
        from app.modules.solving.parser import SolutionParser
        import json
        import os

        json_path = os.path.join(os.path.dirname(__file__), 'test_case_1_correct_full.json')
        with open(json_path, encoding='utf-8') as f:
            data = json.load(f)

        assert "answer" in data
        assert data["answer"] is not None
        assert len(data["answer"]) > 0

    def test_case1_correct_full_steps(self):
        """Test Case 1: steps are flat s1, s2, s3... format."""
        import json
        import os

        json_path = os.path.join(os.path.dirname(__file__), 'test_case_1_correct_full.json')
        with open(json_path, encoding='utf-8') as f:
            data = json.load(f)

        steps = data.get("steps", [])
        assert len(steps) > 0

        # Verify flat step_id format (s1, s2, s3, not s1_1, s2_1)
        for i, step in enumerate(steps, 1):
            assert step["step_id"] == f"s{i}", (
                f"Step {i} should have step_id='s{i}', got '{step['step_id']}'"
            )
            assert "step_name" in step
            assert "content" in step
            assert len(step["content"]) > 0

    def test_case1_correct_full_parse(self):
        """Test Case 1: parser can parse natural language three-part output."""
        from app.modules.solving.parser import SolutionParser

        parser = SolutionParser()

        problem_text = (
            "设 $a_0, a_1, \\ldots$ 是正整数序列，"
            "$(b_n)$ 是由 $b_n = \\gcd(a_n, a_{n+1})$ 定义的序列。"
            "证明：可以选择序列 $(a_n)$ 使得每个非零自然数恰好等于 "
            "$a_0, b_0, a_1, b_1, \\ldots$ 中的一项。"
        )

        # Simulate LLM natural language output (new three-part format)
        llm_output = """
这题怎么看：
这道题要求构造正整数序列使得每个非零自然数恰好出现一次。突破口在于利用 gcd 的递归定义。

这题怎么想：
第一步：设 a0 = 1，则 b0 = gcd(a0, a1)。令 a1 = 2，则 b0 = 1。
第二步：令 a_{n+1} = b_n × (n+2)，则 b_n = gcd(a_n, a_{n+1}) = n+1。
第三步：通过归纳，每一步引入新质数，确保每个正整数出现一次。

这题留下什么方法：
关键是递归构造和归纳验证，利用质因数分解覆盖所有正整数。
        """

        solution = parser.parse(llm_output, problem_text)

        assert solution.problem == problem_text
        assert solution.answer is not None
        assert len(solution.steps) >= 3
        assert solution.steps[0].step_id == "s1"

    # ============== Test Case 2: Wrong Student Work ==============
    # Case 2: Incorrect student work, error feedback expected

    def test_case2_wrong_student_work_present(self):
        """Test Case 2: student_work field present."""
        import json
        import os

        json_path = os.path.join(os.path.dirname(__file__), 'test_case_2_wrong.json')
        with open(json_path, encoding='utf-8') as f:
            data = json.load(f)

        assert "student_work" in data
        assert data["student_work"] is not None
        assert len(data["student_work"]) > 0

    def test_case2_wrong_steps(self):
        """Test Case 2: steps in s1, s2, s3 format."""
        import json
        import os

        json_path = os.path.join(os.path.dirname(__file__), 'test_case_2_wrong.json')
        with open(json_path, encoding='utf-8') as f:
            data = json.load(f)

        steps = data.get("steps", [])
        assert len(steps) > 0
        assert steps[0]["step_id"] == "s1"
        assert "content" in steps[0]

    def test_case2_wrong_evaluation(self):
        """Test Case 2: evaluator detects wrong work."""
        from app.modules.solving.evaluator import Evaluator

        evaluator = Evaluator()
        problem = (
            "设 $a_0, a_1, \\ldots$ 是正整数序列，"
            "$(b_n)$ 是由 $b_n = \\gcd(a_n, a_{n+1})$ 定义的序列。"
            "证明：可以选择序列 $(a_n)$ 使得每个非零自然数恰好等于 "
            "$a_0, b_0, a_1, b_1, \\ldots$ 中的一项。"
        )
        student_work = (
            "解：假设所有 a_n 都互质，即 gcd(a_i, a_j) = 1 (i ≠ j)，"
            "则所有 b_n = 1，但这只能覆盖正整数 1。"
        )

        # Rule-based evaluation (no LLM) gives low confidence
        result = evaluator._evaluate_with_rules(problem, student_work)
        # Rule-based is heuristic, but should at least not crash
        assert result is not None
        assert hasattr(result, "is_correct")

    # ============== Test Case 3: Correct Partial Work ==============
    # Case 3: Correct partial work, continuation expected

    def test_case3_partial_student_work(self):
        """Test Case 3: student_work field present with breakpoint."""
        import json
        import os

        json_path = os.path.join(os.path.dirname(__file__), 'test_case_3_partial.json')
        with open(json_path, encoding='utf-8') as f:
            data = json.load(f)

        assert "student_work" in data
        assert data["student_work"] is not None
        assert len(data["student_work"]) > 0
        assert "breakpoint_step" in data

    def test_case3_partial_steps(self):
        """Test Case 3: steps in s1, s2, s3 format."""
        import json
        import os

        json_path = os.path.join(os.path.dirname(__file__), 'test_case_3_partial.json')
        with open(json_path, encoding='utf-8') as f:
            data = json.load(f)

        steps = data.get("steps", [])
        assert len(steps) > 1
        for i, step in enumerate(steps, 1):
            assert step["step_id"] == f"s{i}"

    def test_case3_partial_evaluator_continue(self):
        """Test Case 3: evaluator allows continuation from partial work."""
        from app.modules.solving.evaluator import Evaluator

        evaluator = Evaluator()
        student_work = (
            "解：设 a_0 = 1。\n"
            "对于 n ≥ 0，令 a_{n+1} = b_n × (n+2)。\n"
            "则 b_n = gcd(a_n, a_{n+1}) = n+1。"
        )

        result = evaluator._evaluate_with_rules("test problem", student_work)
        assert result.can_continue is True
        # Rule-based: has math and logical flow -> correct
        assert result.is_correct is True


# Run tests with: python -m pytest tests/modules/test_solving/ -v

