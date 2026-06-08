# 连接 Module 1 (Solving) 和 Module 2 (Intervention)

## TL;DR

> **Goal**: 让 Module 1 生成 solution_steps 后自动存入 SessionState，Module 2 从 SessionState 读取，无需调用方手动传递。
>
> **数据流**:
> ```
> POST /solving/reference → Module1.generate() → 存 SessionState
> POST /interventions     → Module2.generate() → 从 SessionState 读取
> ```

## 改动概览

### Module 1 (Solving)

| 文件 | 改动 |
|------|------|
| `service.py` | `generate()` 增加 `session_id` 参数，生成后存 SessionState |
| `routes.py` | 透传 `session_id` 参数 |

### Module 2 (Intervention)

| 文件 | 改动 |
|------|------|
| `service.py` | `generate()` 改为从 SessionState 读取数据 |
| `routes.py` | 简化请求体 |

## SessionState 数据结构

```
state_manager.set_module_state(session_id, "solving", {
    "problem": "...",
    "student_work": "...",
    "student_steps": [...],
    "solution_steps": [...],
})
```

## 任务分解

### T1. 修改 Module 1 service.py ✅

**文件**: `app/modules/solving/service.py`

**改动**:
1. `generate()` 方法签名增加 `session_id: Optional[str] = None` 参数
2. `generate()` 末尾，在返回 `SolvingResponse` 之前，增加存 SessionState 逻辑：

```python
if session_id and solution:
    state = {
        "problem": request.problem,
        "student_work": request.student_work or "",
        "student_steps": getattr(request, 'student_steps', []) or [],
        "solution_steps": [s.dict() for s in solution.steps],
    }
    self._context.state_manager.set_module_state(session_id, "solving", state)
```

3. 如果 `_context` 为 None（外部直接调用），跳过存状态（避免 NPE）

**Must NOT**: 不改现有返回结构，不改其他方法

---

### T2. 修改 Module 1 routes.py ✅

**文件**: `app/modules/solving/routes.py`

**改动**:
1. `get_reference_solution()` 增加 `session_id: Optional[str] = None` 参数（从请求体或header）
2. 透传给 `service.generate(request, session_id=session_id)`

**Must NOT**: 不改其他端点

---

### T3. 修改 Module 2 service.py ✅

**文件**: `app/modules/intervention/service.py`

**改动**:
1. `generate()` 方法签名改为：

```python
async def generate(
    self,
    session_id: str,                    # session_id 必填
    intensity: float = 0.5,              # intensity 可选
    student_work: Optional[str] = None,  # 可覆盖 SessionState
    student_id: Optional[str] = None,
) -> Intervention:
```

2. 方法内改为从 SessionState 读取：

```python
solving_state = self._context.state_manager.get_module_state(session_id, "solving")
if not solving_state:
    raise ValueError(f"No solving state found for session {session_id}")

problem = solving_state.get("problem", "")
student_steps = solving_state.get("student_steps", [])
solution_steps = solving_state.get("solution_steps", [])

# 如果传入了 student_work，覆盖默认值
if not student_work:
    student_work = solving_state.get("student_work", "")
```

**Must NOT**: 不改其他方法（deliver_intervention 等）

---

### T4. 修改 Module 2 routes.py ✅

**文件**: `app/modules/intervention/routes.py`

**改动**:
1. `create_intervention()` 请求体简化为：

```python
class InterventionRequest(BaseModel):
    session_id: str                     # 必填
    student_id: Optional[str] = None
    intensity: float = 0.5              # 可选，默认 0.5
    student_work: Optional[str] = None   # 可选，覆盖 SessionState
```

2. 调用改为：

```python
intervention = await service.generate(
    session_id=request.session_id,
    student_work=request.student_work,
    intensity=request.context.get("intensity", 0.5),
    student_id=request.student_id,
)
```

**Must NOT**: 不改 get_intervention / accept_intervention / dismiss_intervention 端点

---

### T5. 写集成测试 ✅

**文件**: `tests/modules/test_integration/test_solving_intervention_connection.py`

**测试场景**:

1. **完整流程**: 
   - 调用 solving 生成 solution_steps（存 SessionState）
   - 调用 intervention 读取 SessionState 生成提示

2. **SessionState 覆盖**:
   - solving 先生成 solution_steps
   - intervention 传入 student_work 覆盖

**Must NOT**: 不做真实 LLM 调用（mock）

---

## 并行化

- T1, T2 可并行（Module 1 的改动互不干扰）
- T3, T4 可并行（Module 2 的改动互不干扰）
- T5 依赖 T1-T4 完成

## 验收标准

- [x] `SolvingService.generate(request, session_id="xxx")` 后，SessionState 中有 solving 数据
- [x] `InterventionService.generate(session_id="xxx")` 能从 SessionState 读取 solving 数据
- [x] 不传 `session_id` 时，Module 1 不存状态（保持向后兼容）
- [x] 集成测试通过

## 提交记录

| 完成阶段 | Commit | Message |
|---------|--------|---------|
| T1-T4 + fix | `5cb794e` | `feat: connect Module 1 and Module 2 via SessionState` |

## Commit 策略

| 完成阶段 | Message | Files |
|---------|---------|-------|
| T1+T2 | `feat: solving module stores solution in SessionState` | `solving/service.py`, `solving/routes.py` |
| T3+T4 | `feat: intervention reads from SessionState` | `intervention/service.py`, `intervention/routes.py` |
| T5 | `test: add integration tests for solving-intervention connection` | `tests/modules/test_integration/` |
