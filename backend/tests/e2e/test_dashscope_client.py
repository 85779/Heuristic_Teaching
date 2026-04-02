"""Test DashScopeClient functionality (real API tests requiring DASHSCOPE_API_KEY).

These tests make actual API calls and are intentionally SKIPPED by default.
Run them explicitly with: pytest tests/e2e/ -v

They live in tests/e2e/ (no conftest.py) to avoid stub pollution.
"""
import os
import pytest


@pytest.mark.skip(reason="Requires DASHSCOPE_API_KEY — run manually: pytest tests/e2e/ -v")
class TestDashScopeClientRealAPI:
    """Real API integration tests for DashScopeClient."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test that DashScopeClient can reach the DashScope API."""
        import importlib.util

        # Bypass conftest sys.modules stubs by loading the module directly
        # from its actual filesystem path
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        real_path = os.path.join(
            backend_dir, "app", "infrastructure", "llm", "dashscope_client.py"
        )
        spec = importlib.util.spec_from_file_location(
            "dashscope_client_real", real_path
        )
        real_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(real_module)
        DashScopeClient = real_module.DashScopeClient

        api_key = os.getenv("DASHSCOPE_API_KEY", "")
        if not api_key:
            pytest.skip("DASHSCOPE_API_KEY not set")

        client = DashScopeClient(api_key=api_key, model="qwen-turbo")
        try:
            result = await client.health_check()
            assert result is True
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_simple_chat(self):
        """Test a simple chat interaction with DashScope."""
        import importlib.util

        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        real_path = os.path.join(
            backend_dir, "app", "infrastructure", "llm", "dashscope_client.py"
        )
        spec = importlib.util.spec_from_file_location(
            "dashscope_client_real", real_path
        )
        real_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(real_module)
        DashScopeClient = real_module.DashScopeClient
        Message = real_module.Message

        api_key = os.getenv("DASHSCOPE_API_KEY", "")
        if not api_key:
            pytest.skip("DASHSCOPE_API_KEY not set")

        client = DashScopeClient(api_key=api_key, model="qwen-turbo")
        try:
            response = await client.chat(
                messages=[Message(role="user", content="1+1等于几？")],
                max_tokens=50,
            )
            assert response and len(response) > 0
        finally:
            await client.close()
