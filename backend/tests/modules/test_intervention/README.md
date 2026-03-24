# Intervention Module Tests

干预模块的测试套件，验证 Module 2（断点分层递进干预系统）的核心功能。

## 运行测试

```bash
# 运行所有干预模块测试
cd backend
python -m pytest tests/modules/test_intervention/ -v

# 运行指定测试文件
python -m pytest tests/modules/test_intervention/test_locator.py -v
python -m pytest tests/modules/test_intervention/test_generator.py -v
python -m pytest tests/modules/test_intervention/test_service.py -v

# 手动 E2E 测试（需要真实 API Key）
export DASHSCOPE_API_KEY=your_key_here
python tests/modules/test_intervention/manual_test.py
```

## 测试结构

```
tests/modules/test_intervention/
├── __init__.py                        # 模块标记
├── conftest.py                        # pytest fixtures 和基础设施 stubs
├── test_locator.py                    # BreakpointLocator 单元测试（6 个）
├── test_generator.py                  # HintGenerator 单元测试（4 个）
├── test_service.py                    # InterventionService 单元测试（3 个）
├── manual_test.py                    # 手动 E2E 测试（需 API Key）
├── manual_test_comprehensive.py        # 全面 E2E 测试（4 场景 × 3 强度，12 个 LLM 调用）
└── README.md                          # 本文件
```

## 测试覆盖

| 测试文件            | 测试内容                         | 测试数 |
| ------------------- | -------------------------------- | ------ |
| `test_locator.py`   | BreakpointLocator 三级语义匹配   | 6      |
| `test_generator.py` | HintGenerator 强度判断和生成逻辑 | 4      |
| `test_service.py`   | InterventionService 总控流程     | 3      |
| **合计**            |                                  | **13** |

> 集成测试见 `tests/modules/test_integration/test_solving_intervention_connection.py`（6 个）

## 测试详情

### test_locator.py

测试 BreakpointLocator 的三级语义匹配逻辑：

| 测试函数                             | 场景                       | 期望结果                |
| ------------------------------------ | -------------------------- | ----------------------- |
| `test_no_breakpoint_exact_match`     | 学生步骤与参考解法完全一致 | `NO_BREAKPOINT`         |
| `test_missing_step`                  | 学生缺少某一步骤           | `MISSING_STEP`          |
| `test_wrong_direction`               | 学生步骤内容偏离参考解法   | `WRONG_DIRECTION`       |
| `test_empty_student_steps`           | 学生未提供任何步骤         | `MISSING_STEP` at pos 0 |
| `test_student_beyond_solution`       | 学生步骤超过参考解法       | `NO_BREAKPOINT`         |
| `test_multiple_correct_then_missing` | 学生完成前N步后缺失第N+1步 | `MISSING_STEP`          |

**语义匹配 vs 字符串匹配**：新测试使用数学内容（如"设 a_0 = 1"）验证语义匹配正确区分 INCOMPLETE 和 WRONG_DIRECTION。

### test_generator.py

测试 HintGenerator 的强度判断和生成逻辑：

| 测试函数                                  | 场景                  | 期望结果                        |
| ----------------------------------------- | --------------------- | ------------------------------- |
| `test_determine_level_surface`            | intensity < 0.4       | 返回 "surface"                  |
| `test_determine_level_middle`             | 0.4 ≤ intensity < 0.7 | 返回 "middle"                   |
| `test_determine_level_deep`               | intensity ≥ 0.7       | 返回 "deep"                     |
| `test_generate_returns_correct_structure` | 生成提示返回正确结构  | `GeneratedHint` with all fields |

### test_service.py

测试 InterventionService 的总控流程和状态管理：

| 测试函数                             | 场景                      | 期望结果                           |
| ------------------------------------ | ------------------------- | ---------------------------------- |
| `test_generate_returns_intervention` | 总控流程返回 Intervention | `Intervention` with correct fields |
| `test_deliver_intervention`          | 送达干预更新状态          | status → `DELIVERED`               |
| `test_record_outcome_accepted`       | 记录干预结果              | status → `ACCEPTED`                |

## conftest.py Fixtures

> 注意：motor、Message 等已 stubbed，测试不依赖真实数据库或 LLM。

```python
@pytest.fixture
def breakpoint_locator():
    """Fresh BreakpointLocator instance."""
    from app.modules.intervention.locator.breaker import BreakpointLocator
    return BreakpointLocator()

@pytest.fixture
def mock_breakpoint_analyzer():
    """Mock BreakpointAnalyzer with canned analysis."""
    ...

@pytest.fixture
def mock_hint_generator():
    """Mock HintGenerator with canned hint."""
    ...

@pytest.fixture
def intervention_service():
    """Fresh InterventionService with mocked sub-modules."""
    ...
```

## 手动测试 (manual_test.py)

手动测试脚本，测试完整的干预流程：

### manual_test.py（基础场景）

测试单个场景：学生缺失关键构造步骤。

```
测试流程：
1. BreakpointLocator 定位断点
2. BreakpointAnalyzer 分析跨越需要什么（LLM）
3. HintGenerator 生成 3 种强度的提示（LLM）

输出：断点分析 + surface/middle/deep 三种提示
```

### manual_test_comprehensive.py（全面测试矩阵）

测试 4 场景 × 3 强度 = 12 个组合，验证所有断点类型的定位和提示生成。

```
场景：
1. MISSING_STEP — 学生缺少关键步骤
2. WRONG_DIRECTION — 学生思路偏离
3. INCOMPLETE_STEP — 学生步骤不完整
4. STUCK — 学生完全卡住无步骤

强度：surface (0.2) / middle (0.5) / deep (0.8)

输出：
- 各场景各强度的断点类型、LLM 分析结果、提示内容
- SUMMARY 汇总表
```

### 使用方法

```bash
# 设置 API Key
export DASHSCOPE_API_KEY=sk-xxxxxxxx

# 运行基础手动测试
python tests/modules/test_intervention/manual_test.py

# 运行全面 E2E 测试（4×3=12 场景）
python tests/modules/test_intervention/manual_test_comprehensive.py
```

## Mock 说明

- LLM 调用全部 mock，不产生真实 API 请求
- 使用 `unittest.mock.AsyncMock` 模拟异步 LLM 响应
- motor (MongoDB driver) 已 stubbed，不依赖数据库

## 扩展测试

如需添加新的测试场景：

```python
# test_locator.py
def test_your_scenario(breakpoint_locator):
    student = [TeachingStep(step_id="s1", step_name="Name", content="...")]
    solution = [...]
    result = breakpoint_locator.locate(student, solution)
    assert result.breakpoint_type == BreakpointType.MISSING_STEP
```
