# Intervention Module Tests

干预模块的测试套件，验证 Module 2 v2（五节点双维度干预系统）的核心功能。

## 运行测试

```bash
# 运行所有干预模块测试（87 个）
cd backend
python -m pytest tests/modules/test_intervention/ -v

# 运行指定测试文件
python -m pytest tests/modules/test_intervention/test_locator.py -v
python -m pytest tests/modules/test_intervention/test_context_manager.py -v
python -m pytest tests/modules/test_intervention/test_router_node2a.py -v
python -m pytest tests/modules/test_intervention/test_decider_node2b.py -v
python -m pytest tests/modules/test_intervention/test_generator_node4.py -v
python -m pytest tests/modules/test_intervention/test_guardrail_node5.py -v
python -m pytest tests/modules/test_intervention/test_service_v2_flow.py -v

# 手动 E2E 测试（需要真实 API Key）
export DASHSCOPE_API_KEY=your_key_here
python tests/modules/test_intervention/manual_test.py
python tests/modules/test_intervention/manual_test_comprehensive.py
```

## 测试结构

```
tests/modules/test_intervention/
├── __init__.py
├── conftest.py                        # pytest fixtures 和基础设施 stubs
│
├── test_locator.py                    # 节点1测试：BreakpointLocator（6个）
├── test_context_manager.py             # ContextManager 测试（16个）
├── test_router_node2a.py              # 节点2a测试：DimensionRouter（6个）
├── test_decider_node2b.py            # 节点2b测试：SubTypeDecider（14个）
├── test_generator_node4.py            # 节点4测试：HintGeneratorV2（16个）
├── test_guardrail_node5.py           # 节点5测试：OutputGuardrail（12个）
├── test_service_v2_flow.py            # v2 service 完整流程（14个）
│
├── manual_test.py                    # 手动 E2E 测试（需 API Key）
└── README.md                          # 本文件
```

## 测试覆盖（87 个）

| 测试文件                  | 测试内容                       | 测试数 |
| ------------------------- | ------------------------------ | ------ |
| `test_locator.py`         | BreakpointLocator 三级语义匹配 | 6      |
| `test_context_manager.py` | ContextManager 状态管理        | 16     |
| `test_router_node2a.py`   | DimensionRouter 维度路由       | 6      |
| `test_decider_node2b.py`  | SubTypeDecider 子类型决策      | 14     |
| `test_generator_node4.py` | HintGeneratorV2 提示生成       | 16     |
| `test_guardrail_node5.py` | OutputGuardrail 安全检查       | 12     |
| `test_service_v2_flow.py` | v2 service 完整流程            | 14     |
| **合计**                  |                                | **87** |

## 测试详情

### test_locator.py — 节点1：断点定位

| 测试函数                             | 场景                       | 期望结果                |
| ------------------------------------ | -------------------------- | ----------------------- |
| `test_no_breakpoint_exact_match`     | 学生步骤与参考解法完全一致 | `NO_BREAKPOINT`         |
| `test_missing_step`                  | 学生缺少某一步骤           | `MISSING_STEP`          |
| `test_wrong_direction`               | 学生步骤内容偏离参考解法   | `WRONG_DIRECTION`       |
| `test_empty_student_steps`           | 学生未提供任何步骤         | `MISSING_STEP` at pos 0 |
| `test_student_beyond_solution`       | 学生步骤超过参考解法       | `NO_BREAKPOINT`         |
| `test_multiple_correct_then_missing` | 学生完成前N步后缺失第N+1步 | `MISSING_STEP`          |

### test_context_manager.py — 状态管理

| 测试类                   | 测试内容                                  | 测试数 |
| ------------------------ | ----------------------------------------- | ------ |
| `TestInitContext`        | 初始化上下文                              | 3      |
| `TestEscalation`         | 升级逻辑（R1→R2, M1→M2 等）               | 4      |
| `TestInterventionMemory` | 干预历史记录                              | 4      |
| `TestFrontendSignals`    | 前端信号处理（PROGRESSED/NOT_PROGRESSED） | 5      |

### test_router_node2a.py — 节点2a：维度路由

| 测试函数                             | 场景                 | 期望结果           |
| ------------------------------------ | -------------------- | ------------------ |
| `test_missing_step_resource`         | MISSING_STEP 断点    | RESOURCE 维度      |
| `test_wrong_direction_metacognitive` | WRONG_DIRECTION 断点 | METACOGNITIVE 维度 |
| `test_incomplete_step_resource`      | INCOMPLETE_STEP 断点 | RESOURCE 维度      |
| `test_stuck_dimension`               | STUCK 断点           | RESOURCE 维度      |
| `test_confidence_scores`             | 置信度评分合理性     | 0.0-1.0 之间       |
| `test_reasoning_provided`            | reasoning 字段非空   | 有推理说明         |

### test_decider_node2b.py — 节点2b：子类型决策

| 测试类                    | 测试内容             | 测试数 |
| ------------------------- | -------------------- | ------ |
| `TestResourceLevels`      | R1-R4 级别判断       | 4      |
| `TestMetacognitiveLevels` | M1-M5 级别判断       | 5      |
| `TestEscalationDecision`  | 升级/维持/终止决策   | 3      |
| `TestFrontendSignals`     | 前端信号对级别的影响 | 2      |

### test_generator_node4.py — 节点4：提示生成

| 测试类                 | 测试内容                    | 测试数 |
| ---------------------- | --------------------------- | ------ |
| `TestLevelMapping`     | 强度到 R1-R4/M1-M5 的映射   | 9      |
| `TestHintGeneration`   | 各级别提示内容生成          | 4      |
| `TestGuardrailTrigger` | 触发 OutputGuardrail 的生成 | 3      |

### test_guardrail_node5.py — 节点5：输出守卫

| 测试函数                        | 场景                    | 期望结果          |
| ------------------------------- | ----------------------- | ----------------- |
| `test_safe_content_passes`      | 安全内容通过            | passed=True       |
| `test_answer_keyword_blocked`   | 包含"答案是"被拦截      | passed=False      |
| `test_proof_keyword_blocked`    | 包含"得证"被拦截        | passed=False      |
| `test_partial_answer_blocked`   | 具体数值答案被拦截      | passed=False      |
| `test_deep_hints_more_lenient`  | deep 级别提示更宽松     | passed=True       |
| `test_fallback_content_safe`    | fallback 内容安全       | passed=True       |
| `test_multiple_answer_patterns` | 多种答案模式都能被拦截  | 全部 passed=False |
| `test_whitespace_robustness`    | 带空格的模式也能被检测  | 全部 passed=False |
| `test_chinese_punctuation`      | 中文标点变体检测        | 全部 passed=False |
| `test_unsafe_triggers_fallback` | 不安全内容触发 fallback | 使用 fallback     |
| `test_fallback_content_neutral` | fallback 内容中性安全   | 无答案关键词      |
| `test_level_affects_strictness` | 级别影响严格程度        | deep 最宽松       |

### test_service_v2_flow.py — v2 service 完整流程

| 测试类                     | 测试内容                              | 测试数 |
| -------------------------- | ------------------------------------- | ------ |
| `TestCreateIntervention`   | 创建干预流程                          | 3      |
| `TestProcessFeedback`      | 反馈处理（PROGRESSED/NOT_PROGRESSED） | 3      |
| `TestEndIntervention`      | 结束干预                              | 1      |
| `TestEscalateIntervention` | 升级干预                              | 2      |
| `TestHelperMethods`        | 辅助方法（\_location_to_dict 等）     | 5      |

## conftest.py Fixtures

> 注意：motor、Message、DashScopeClient 等已 stubbed，测试不依赖真实数据库或 LLM。

| Fixture              | 类型                | 说明                               |
| -------------------- | ------------------- | ---------------------------------- |
| `breakpoint_locator` | BreakpointLocator   | fresh 实例                         |
| `context_manager`    | ContextManager      | fresh 实例                         |
| `dimension_router`   | DimensionRouter     | fresh 实例                         |
| `sub_type_decider`   | SubTypeDecider      | fresh 实例                         |
| `hint_generator_v2`  | HintGeneratorV2     | fresh 实例                         |
| `output_guardrail`   | OutputGuardrail     | fresh 实例                         |
| `service_with_mocks` | InterventionService | 装配好的 service（带 mock 子模块） |

## Mock 说明

- LLM 调用全部 mock，不产生真实 API 请求
- 使用 `unittest.mock.AsyncMock` 模拟异步 LLM 响应
- motor (MongoDB driver)、DashScopeClient 已 stubbed，不依赖数据库或外部 API

## 扩展测试

如需添加新的测试场景：

```python
# test_locator.py
def test_your_scenario(breakpoint_locator):
    student = [TeachingStep(step_id="s1", step_name="Name", content="...")]
    solution = [...]
    result = breakpoint_locator.locate(student, solution)
    assert result.breakpoint_type == BreakpointType.MISSING_STEP

# test_decider_node2b.py
async def test_your_escalation(sub_type_decider):
    result = await sub_type_decider.decide(
        dimension=DimensionEnum.RESOURCE,
        student_input="学生仍然卡住",
        expected_step="构造辅助量",
        intervention_memory=[],
        frontend_signal=FrontendSignalEnum.NOT_PROGRESSED,
        current_level="R1",
        problem_context="...",
    )
    assert result.escalation_decision.action == EscalationAction.ESCALATE
    assert result.sub_type == "R2"
```
