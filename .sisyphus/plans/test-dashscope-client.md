# 测试 DashScopeClient

## TL;DR
> 测试阿里云百炼 DashScope LLM 客户端是否正常工作，验证 chat() 和 health_check() 方法。

## Context
DashScopeClient 已实现完整参数支持，但尚未测试。需要验证：
1. 配置项是否正确
2. API 调用是否正常
3. 返回结果是否符合预期

## Work Objectives

### Must Have
- [x] 更新 config.py 添加 DashScope 配置项
- [x] 创建测试脚本 tests/test_dashscope_client.py
- [x] 运行 health_check() 验证连接
- [x] 运行简单 chat() 调用验证功能

### Must NOT Have
- 不修改 DashScopeClient 源码（已实现完整）
- 不创建不必要的测试用例

## Execution Strategy

```
Step 1: 更新 config.py
  └── 添加 DASHSCOPE_API_KEY, DASHSCOPE_BASE_URL
  └── 添加 SOLVING_MODEL, INTERVENTION_MODEL

Step 2: 创建测试脚本
  └── tests/test_dashscope_client.py
  └── 测试 health_check()
  └── 测试简单 chat() 调用

Step 3: 执行测试
  └── 设置环境变量 DASHSCOPE_API_KEY
  └── 运行 pytest 或直接执行脚本
```

## Verification Strategy

**Agent-Executed QA (必须运行验证)**:
```bash
# 1. 设置环境变量
export DASHSCOPE_API_KEY="your-api-key"

# 2. 运行测试
cd D:\Socrates\backend
python -m pytest tests/test_dashscope_client.py -v

# 或直接运行
python -c "
import asyncio
from app.infrastructure.llm.dashscope_client import DashScopeClient
from app.infrastructure.llm.base_client import Message

async def test():
    client = DashScopeClient(api_key='${DASHSCOPE_API_KEY}', model='qwen-turbo')
    # health check
    result = await client.health_check()
    print(f'Health check: {result}')
    # simple chat
    response = await client.chat([Message(role='user', content='1+1等于几？')], max_tokens=50)
    print(f'Chat response: {response}')
    await client.close()

asyncio.run(test())
"
```

**Expected Result**:
- health_check() 返回 True
- chat() 返回有效文本响应

## Commit Strategy
- 暂不提交，等待测试通过后再决定

## Success Criteria
- [x] DashScope 配置项已添加
- [x] 测试脚本可执行
- [x] health_check() 返回 True
- [x] chat() 返回有效响应
