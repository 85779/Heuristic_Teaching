# Module 2: 断点分层递进干预系统

## TL;DR

> **Goal**: 实现 Module 2 干预系统的核心功能 —— 断点定位 → 断点分析 → 提示生成
>
> **设计简化**：
> - `intensity` 作为外部输入参数（固定值），暂不做自动调整
> - 直接调用 SolvingService 获取 solution steps
> - 使用 qwen-turbo 进行 LLM 调用
>
> **核心流程**：
> ```
> 输入: student_steps + intensity + solution_steps
>   │
>   ▼
> BreakpointLocator (纯逻辑)
>   │
>   ▼
> BreakpointAnalyzer (LLM)
>   │
>   ▼
> HintGenerator (LLM)
>   │
>   ▼
> 输出: Intervention (提示内容)
> ```

## 现有文件状态

| 文件 | 状态 | 说明 |
|------|------|------|
| `models.py` | ✅ 可用 | `Intervention`, `InterventionRequest`, `InterventionResponse` |
| `routes.py` | ⚠️ 桩 | 4个路由未实现 |
| `service.py` | ⚠️ 桩 | 方法签名存在但 raise NotImplementedError |
| `module.py` | ⚠️ 接口 | 属性定义完成，方法未实现 |
| `pipeline.py` | ⚠️ 桩 | `InterventionPipeline` 未实现 |
| `prompts/` | ❌ 桩 | 5个提示模板全是空壳 |

---

## 架构

```
InterventionModule
    │
    ├── service.py (总控)
    │       │
    │       ├── locator/breaker.py    (断点定位 — 纯逻辑)
    │       │
    │       ├── analyzer/analyzer.py  (断点分析 — LLM)
    │       │
    │       └── generator/generator.py (提示生成 — LLM)
    │
    ├── routes.py                     (API 路由)
    │
    └── pipeline.py                   (Pipeline 接口实现)
```

### 数据流

```python
# service.generate() 流程
1. locator.locate(student_steps, solution_steps)
   → BreakpointLocation

2. analyzer.analyze(breakpoint_location, context)
   → BreakpointAnalysis

3. generator.generate(breakpoint_analysis, intensity)
   → Intervention
```

---

## 文件清单

```
app/modules/intervention/
├── module.py                          # 模块入口（实现 initialize/shutdown）
├── routes.py                         # API 路由（实现 4 个端点）
├── service.py                        # 总控服务（实现 generate）
│
├── locator/
│   ├── __init__.py
│   ├── breaker.py                    # BreakpointLocator
│   └── models.py                     # BreakpointLocation, BreakpointType
│
├── analyzer/
│   ├── __init__.py
│   ├── analyzer.py                   # BreakpointAnalyzer
│   ├── models.py                     # BreakpointAnalysis, RequiredKnowledge
│   └── prompts.py                    # 分析提示词模板
│
├── generator/
│   ├── __init__.py
│   ├── generator.py                  # HintGenerator
│   ├── models.py                     # GeneratedHint
│   └── prompts.py                    # 生成提示词模板
│
└── prompts/                          # 顶层提示词（保留，暂不用）
    ├── location.py
    ├── analysis.py
    ├── decision.py
    ├── intensity.py
    └── hint.py

tests/modules/test_intervention/
├── __init__.py
├── conftest.py
├── test_locator.py
├── test_analyzer.py
├── test_generator.py
└── test_service.py
```

---

## 任务分解

### T1. 实现 locator/breaker.py + models.py

**Status**: ✅ DONE — implemented, verified

- [x] T1. **Implement locator/breaker.py + models.py**

### T2. 实现 analyzer/analyzer.py + models.py + prompts.py

**Status**: ✅ DONE — implemented, verified

- [x] T2. **Implement analyzer/analyzer.py + models.py + prompts.py**

### T3. 实现 generator/generator.py + models.py + prompts.py

**Status**: ✅ DONE — implemented, verified

- [x] T3. **Implement generator/generator.py + models.py + prompts.py**

### T4. 实现 service.py（总控服务）

**Status**: ✅ DONE — implemented, verified

- [x] T4. **Implement InterventionService (service.py)**

### T5. 实现 module.py + routes.py

**Status**: ✅ DONE — implemented, verified

- [x] T5. **Implement InterventionModule and routes**

### T6. 实现 tests/modules/test_intervention/

**Status**: ✅ DONE — implemented, verified (13 tests passed)

- [x] T6. **Write unit tests (tests/modules/test_intervention/)**

### T7. 最终验证

**Status**: ✅ DONE

- [x] T7. **Final verification**

**QA Results:**
- `python -m pytest tests/modules/test_intervention/` → **13 passed**
- `python -m pytest tests/core/` → **122 passed**
- `python -c "from app.modules.intervention import InterventionModule"` → **import OK**
- No unexpected `NotImplementedError` in implementation files

**What to do**:
- 创建 `BreakpointType` 枚举：`MISSING_STEP`, `WRONG_DIRECTION`, `INCOMPLETE_STEP`, `STUCK`
- 创建 `BreakpointLocation` dataclass：
  - `breakpoint_position: int` — 卡在第几步之后（0 = 第一步都没完成）
  - `breakpoint_type: BreakpointType`
  - `expected_step_content: str` — 期望的下一步内容
  - `gap_description: str` — 间隙描述
- 实现 `BreakpointLocator.locate()`：
  - 输入：`student_steps: List[TeachingStep]`, `solution_steps: List[TeachingStep]`
  - 逻辑：逐个对比学生steps和solution steps，找到第一个差异点
  - 输出：`BreakpointLocation`

**Must NOT do**:
- 不调用 LLM（纯逻辑）
- 不修改 `models.py`（主模型的 Intervention 等保持不变）

**Recommended Agent Profile**:
- **Category**: `unspecified-high`
  - Reason: 跨多个子目录创建新文件
- **Skills**: [`python-patterns`]

---

### T2. 实现 analyzer/analyzer.py + models.py + prompts.py

**What to do**:
- 创建 `BreakpointAnalysis` dataclass：
  - `required_knowledge: List[str]` — 跨越断点需要的知识/技能
  - `required_connection: str` — 需要建立什么联系
  - `possible_approaches: List[str]` — 可选的跨越路径
  - `difficulty_level: float` — 难度 0.0~1.0
- 实现 `BreakpointAnalyzer`：
  - `analyze(location: BreakpointLocation, problem: str, student_work: str, solution: str) -> BreakpointAnalysis`
  - 调用 LLM (qwen-turbo)，传入断点位置 + 题目上下文
  - 解析 LLM 输出为 `BreakpointAnalysis`
- 实现 `prompts.py`：
  - 提示词模板，引导 LLM 分析"跨越断点需要什么"

**Must NOT do**:
- 不直接给答案（分析的是"需要什么"而非"学生为什么错"）
- 不做强度决策（那是 generator 的事）

**Recommended Agent Profile**:
- **Category**: `unspecified-high`
  - Reason: 需要设计 LLM prompt 和解析逻辑
- **Skills**: [`python-patterns`]

---

### T3. 实现 generator/generator.py + models.py + prompts.py

**What to do**:
- 创建 `GeneratedHint` dataclass：
  - `content: str` — 提示内容文本
  - `level: str` — "surface" / "middle" / "deep"（由 intensity 决定）
  - `approach_used: str` — 使用的跨越路径
- 实现 `HintGenerator`：
  - `generate(analysis: BreakpointAnalysis, intensity: float) -> GeneratedHint`
  - 根据 `intensity` 决定提示层面：
    - intensity < 0.4 → surface（给方向性提示）
    - 0.4 ≤ intensity < 0.7 → middle（给部分提示 + 示例）
    - intensity ≥ 0.7 → deep（给完整示例）
  - 调用 LLM (qwen-turbo) 生成提示
  - 解析 LLM 输出为 `GeneratedHint`
- 实现 `prompts.py`：
  - 提示词模板，根据 intensity 调整提示的显性程度

**Must NOT do**:
- 不生成完整解法（只生成提示）
- intensity 不做自动调整（作为外部参数传入）

**Recommended Agent Profile**:
- **Category**: `unspecified-high`
  - Reason: 需要设计多层次的提示词模板
- **Skills**: [`python-patterns`]

---

### T4. 实现 service.py（总控服务）

**What to do**:
- 实现 `InterventionService.generate()`：
  - 输入：`problem: str`, `student_work: str`, `student_steps: List[dict]`, `intensity: float`
  - 流程：
    1. 调用 SolvingService 获取 solution steps（`context.get_module("solving")`）
    2. 调用 `BreakpointLocator.locate()` 定位断点
    3. 调用 `BreakpointAnalyzer.analyze()` 分析断点
    4. 调用 `HintGenerator.generate()` 生成提示
  - 输出：`Intervention` 对象
- 实现 `InterventionService.analyze_student_state()`（`service.py` 中已有签名）
  - 从 SessionState 获取学生当前 steps
  - 返回分析结果 dict
- 实现其他 `service.py` 中已有的方法签名（桩）
  - `determine_intervention_type()` — 返回 "hint"
  - `calculate_intensity()` — 返回传入的 intensity
  - `generate_intervention()` — 调用总控流程
  - `deliver_intervention()` — 记录 delivery timestamp
  - `record_intervention_outcome()` — 记录 outcome

**Must NOT do**:
- 不做强度自动调整（简化版）
- 不实现接受率追踪

**Recommended Agent Profile**:
- **Category**: `unspecified-high`
  - Reason: 跨多个子模块协调
- **Skills**: [`python-patterns`]

---

### T5. 实现 module.py + routes.py

**What to do**:
- 实现 `InterventionModule.initialize()`：
  - 初始化 `InterventionService`
  - 订阅 `solving.stuck_detected`, `solving.error_detected`, `solving.step_completed` 事件
  - 事件处理：触发 `generate()` 流程
- 实现 `InterventionModule.shutdown()`
- 实现 `routes.py` 中的 4 个端点：
  - `POST /interventions` — 创建干预（调用 service.generate）
  - `GET /interventions/{id}` — 获取干预
  - `POST /interventions/{id}/accept` — 接受干预
  - `POST /interventions/{id}/dismiss` — 拒绝干预

**Must NOT do**:
- 不改变 `module_id`, `module_name`, `dependencies` 等属性（已定义）

**Recommended Agent Profile**:
- **Category**: `unspecified-high`
  - Reason: 事件订阅 + API 路由
- **Skills**: [`python-patterns`]

---

### T6. 实现 tests/modules/test_intervention/

**What to do**:
- 创建 `tests/modules/test_intervention/` 目录
- 创建 `conftest.py`：fixtures for InterventionService, mock LLM client
- 创建 `test_locator.py`：测试 BreakpointLocator
  - 完全匹配、无断点
  - 缺少数步
  - 方向错误
  - 完全未开始
- 创建 `test_analyzer.py`：测试 BreakpointAnalyzer（mock LLM）
- 创建 `test_generator.py`：测试 HintGenerator（mock LLM）
  - intensity < 0.4 → surface 提示
  - 0.4 ≤ intensity < 0.7 → middle 提示
  - intensity ≥ 0.7 → deep 提示
- 创建 `test_service.py`：测试总控流程（mock 子模块）

**Must NOT do**:
- 不做真实 LLM 调用（全部 mock）
- 不连 MongoDB（mock state manager）

**Recommended Agent Profile**:
- **Category**: `unspecified-high`
  - Reason: 测试 4 个组件
- **Skills**: [`python-testing`]

---

### T7. 最终验证

**What to do**:
- 运行 `python -m pytest tests/modules/test_intervention/ -v`
- 运行 `python -c "from app.modules.intervention import InterventionModule; print('import OK')"`
- 验证 service.generate() 流程端到端可跑通
- 检查无 `raise NotImplementedError` 在实现文件中

**Must NOT do**:
- 不做真实 API 调用

---

## 并行化策略

| Wave | Tasks | 可并行 |
|------|-------|--------|
| Wave 1 | T1 (locator) | ✅ 独立 |
| Wave 2 | T2 (analyzer), T3 (generator) | ✅ 可并行（互相独立） |
| Wave 3 | T4 (service), T5 (module+routes) | ⚠️ T4 → T5（T4 先完成） |
| Wave 4 | T6 (tests) | ⚠️ 依赖 T1-T5 完成 |
| Wave 5 | T7 (final) | 串行 |

**关键路径**：T1 → T2/T3 → T4 → T5 → T6 → T7

---

## 依赖关系

```
T1 (locator)
    │
    ├── T2 (analyzer) ──┐
    │                   │── T4 (service) ── T5 (module+routes) ── T6 (tests) ── T7
    └── T3 (generator) ──┘
```

---

## 验收标准

- [x] `BreakpointLocator.locate()` 能正确识别断点位置和类型
- [x] `BreakpointAnalyzer.analyze()` 返回跨越断点需要的知识和路径
- [x] `HintGenerator.generate()` 根据 intensity 生成不同层面的提示
- [x] `InterventionService.generate()` 端到端串联三个子模块
- [x] `InterventionModule` 正确订阅 solving 事件
- [x] 4 个 API 路由正常工作
- [x] 122+ tests pass（包括 intervention tests）— **13 intervention + 122 core = 135 total**
- [x] 无 `NotImplementedError` 在 `locator/`, `analyzer/`, `generator/`, `service.py` 中

---

## Final Verification Wave

> Since this plan is a single module implementation (not infrastructure), the Final Wave is simplified to 3 quick checks.

### F1. Import Check
```bash
python -c "from app.modules.intervention import InterventionModule; print('OK')"
```
**Result**: ✅ OK

### F2. Test Suite
```bash
python -m pytest tests/modules/test_intervention/ -v --tb=short
```
**Result**: ✅ 13 passed

### F3. Stub Audit
```bash
grep -r "raise NotImplementedError" app/modules/intervention/locator/ app/modules/intervention/analyzer/ app/modules/intervention/generator/ app/modules/intervention/service.py
```
**Result**: ✅ None found (remaining stubs only in unused pipeline.py and top-level prompts/)

---

## Commit 策略

| 完成阶段 | Message | Files |
|---------|---------|-------|
| T1 | `feat: implement BreakpointLocator` | `locator/breaker.py`, `locator/models.py` |
| T2 | `feat: implement BreakpointAnalyzer` | `analyzer/analyzer.py`, `analyzer/models.py`, `analyzer/prompts.py` |
| T3 | `feat: implement HintGenerator` | `generator/generator.py`, `generator/models.py`, `generator/prompts.py` |
| T4 | `feat: implement InterventionService` | `service.py` |
| T5 | `feat: implement InterventionModule and routes` | `module.py`, `routes.py` |
| T6 | `test: add intervention module tests` | `tests/modules/test_intervention/` |
| T7 | `chore: final verification` | — |
