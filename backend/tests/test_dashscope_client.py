"""Test DashScopeClient functionality."""
import asyncio
import os
import pytest
from app.infrastructure.llm.dashscope_client import DashScopeClient
from app.infrastructure.llm.base_client import Message


@pytest.mark.asyncio
async def test_health_check():
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        pytest.skip("DASHSCOPE_API_KEY not set")
    
    client = DashScopeClient(api_key=api_key, model="qwen-turbo")
    result = await client.health_check()
    assert result is True
    await client.close()


@pytest.mark.asyncio
async def test_simple_chat():
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        pytest.skip("DASHSCOPE_API_KEY not set")
    
    client = DashScopeClient(api_key=api_key, model="qwen-turbo")
    response = await client.chat(
        messages=[Message(role="user", content="1+1等于几？")],
        max_tokens=50
    )
    assert response and len(response) > 0
    await client.close()
