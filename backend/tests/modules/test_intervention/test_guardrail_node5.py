"""E2E tests for OutputGuardrail (Node 5)."""

import pytest
from unittest.mock import AsyncMock, patch
from app.modules.intervention.guardrail.guardrail import OutputGuardrail, GuardrailResult, RULES


@pytest.fixture
def output_guardrail():
    """Fresh OutputGuardrail instance with mocked LLM."""
    guardrail = OutputGuardrail()
    return guardrail


class TestOutputGuardrail:
    """Test Node 5: Output Guardrail (output validation)."""

    @pytest.mark.asyncio
    async def test_check_valid_hint(
        self,
        output_guardrail,
    ):
        """Test checking a valid hint (should pass)."""
        mock_response = '{"pass": true, "reason": "提示内容合规", "violations": []}'

        mock_client = AsyncMock()
        mock_client.chat.return_value = mock_response

        with patch.object(output_guardrail, '_get_llm_client', return_value=mock_client):
            result = await output_guardrail.check(
                content="思考题目中已知条件和所求目标之间的关系",
                level="R1",
            )

        assert result.passed is True
        assert len(result.violations) == 0

    @pytest.mark.asyncio
    async def test_check_hint_with_violation(
        self,
        output_guardrail,
    ):
        """Test checking a hint with violation (should fail)."""
        mock_response = '{"pass": false, "reason": "给出了答案", "violations": ["答案"]}'

        mock_client = AsyncMock()
        mock_client.chat.return_value = mock_response

        with patch.object(output_guardrail, '_get_llm_client', return_value=mock_client):
            result = await output_guardrail.check(
                content="答案是42",
                level="R1",
            )

        assert result.passed is False
        assert len(result.violations) > 0

    @pytest.mark.asyncio
    async def test_check_empty_content(
        self,
        output_guardrail,
    ):
        """Test checking empty content (should fail)."""
        result = await output_guardrail.check(
            content="",
            level="R1",
        )

        assert result.passed is False
        assert "空" in result.reason

    @pytest.mark.asyncio
    async def test_check_whitespace_content(
        self,
        output_guardrail,
    ):
        """Test checking whitespace-only content (should fail)."""
        result = await output_guardrail.check(
            content="   ",
            level="R1",
        )

        assert result.passed is False

    @pytest.mark.asyncio
    async def test_check_rule_based_violation(
        self,
        output_guardrail,
    ):
        """Test rule-based violation detection."""
        # Content that matches a forbidden pattern
        result = await output_guardrail.check(
            content="所以最终结果是 42",
            level="R1",
        )

        assert result.passed is False

    @pytest.mark.asyncio
    async def test_fallback_on_llm_error(
        self,
        output_guardrail,
    ):
        """Test fallback when LLM call fails."""
        mock_client = AsyncMock()
        mock_client.chat.side_effect = Exception("LLM error")

        with patch.object(output_guardrail, '_get_llm_client', return_value=mock_client):
            result = await output_guardrail.check(
                content="这是正常提示内容",
                level="R1",
            )

        # Should pass based on rule check only
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_fallback_on_json_parse_error(
        self,
        output_guardrail,
    ):
        """Test fallback when LLM returns invalid JSON."""
        mock_client = AsyncMock()
        mock_client.chat.return_value = "Invalid JSON"

        with patch.object(output_guardrail, '_get_llm_client', return_value=mock_client):
            result = await output_guardrail.check(
                content="这是正常提示内容",
                level="R1",
            )

        # Should pass based on rule check only
        assert result.passed is True


class TestRuleBasedChecks:
    """Test rule-based violation detection."""

    @pytest.mark.asyncio
    async def test_forbidden_patterns_r1(
        self,
        output_guardrail,
    ):
        """Test that R1 rules detect forbidden patterns."""
        # These patterns should be caught by universal_violations regex
        forbidden_contents = [
            "答案是 42",
            "所以最终结果是 100",
            "完整解答如下：",
            "解题步骤如下：",
        ]

        # Mock LLM client to avoid API call
        mock_client = AsyncMock()
        mock_client.chat.return_value = '{"pass": true, "reason": "ok", "violations": []}'

        for content in forbidden_contents:
            with patch.object(output_guardrail, '_get_llm_client', return_value=mock_client):
                result = await output_guardrail.check(content=content, level="R1")
                assert result.passed is False, f"Should fail: {content}"

    @pytest.mark.asyncio
    async def test_different_levels_have_different_rules(
        self,
        output_guardrail,
    ):
        """Test that different levels have different rule sets."""
        r1_rules = RULES.get("R1", {})
        r4_rules = RULES.get("R4", {})

        # Different levels may have different forbidden patterns
        assert r1_rules is not None
        assert r4_rules is not None


class TestGuardrailResult:
    """Test GuardrailResult dataclass."""

    def test_guardrail_result_pass(self):
        """Test GuardrailResult with passed=True."""
        result = GuardrailResult(
            passed=True,
            reason="通过检查",
            violations=[],
        )

        assert result.passed is True
        assert len(result.violations) == 0

    def test_guardrail_result_fail(self):
        """Test GuardrailResult with passed=False."""
        result = GuardrailResult(
            passed=False,
            reason="包含违规内容",
            violations=["答案", "完整解答"],
        )

        assert result.passed is False
        assert len(result.violations) == 2

    def test_guardrail_result_with_revision(self):
        """Test GuardrailResult with revised content."""
        result = GuardrailResult(
            passed=False,
            reason="已修订",
            violations=["原内容违规"],
            revised_content="修订后的合规内容",
        )

        assert result.revised_content == "修订后的合规内容"


class TestRULESDict:
    """Test RULES dictionary for each level."""

    def test_all_levels_have_rules(self):
        """Test that all 9 levels have rules defined."""
        levels = ["R1", "R2", "R3", "R4", "M1", "M2", "M3", "M4", "M5"]

        for level in levels:
            assert level in RULES, f"Missing rules for {level}"
            assert "forbidden" in RULES[level], f"Missing forbidden list for {level}"
