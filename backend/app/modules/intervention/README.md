# Module 2: 断点分层递进干预系统（v2）

## 概述

Module 2 的核心任务，是在学生处于断点、尚未继续生成下一推进步骤时，围绕该断点建立一个由**断点定位 → 双维度诊断 → 分层干预决策 → 提示生成**构成的递进支架系统。

**v2 重大更新**：从旧版三节点（Locator → Analyzer → Generator）升级为**五节点管道**，引入双维度诊断（Resource / Metacognitive）路由和 ContextManager 状态管理，支持多轮递进干预。

```
学生请求干预
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│  ① BreakpointLocator        纯逻辑 · 三级语义匹配            │
│     定位断点位置和类型                                        │
│                                                              │
│  ② DimensionRouter (2a)      判断维度：Resource 或 Metacognitive │
│                                                              │
│  ③ SubTypeDecider (2b)      确定子类型级别（R1-R4 / M1-M5）  │
│                                                              │
│  ④ HintGeneratorV2           生成维度+级别对应的提示（LLM）  │
│                                                              │
│  ⑤ OutputGuardrail           安全检查：防答案泄露            │
└──────────────────────────────────────────────────────────────┘
    │
    ▼
返回干预提示 / 自动升级 / 终止
```

## 核心概念：双维度诊断

所有干预决策都围绕两个维度展开：

| 维度              | 描述                               | 干预策略          |
| ----------------- | ---------------------------------- | ----------------- |
| **Resource**      | 学生缺乏知识或步骤（不知道怎么做） | 补充知识/方法     |
| **Metacognitive** | 学生有知识但未调用（知道但想不到） | 引导反思/策略激活 |

**为什么需要维度诊断？**

- 同一个断点（如"学生没有构造辅助量"），可能是 Resource 维度（完全不知道什么叫辅助量），
  也可能是 Metacognitive 维度（知道辅助量但想不到在这里用）
- 不同维度对应不同的提示策略，混用会导致提示无效甚至干扰学生

## 五节点管道详解

### 节点 1：BreakpointLocator（断点定位）

**职责**：比较学生步骤与参考解法步骤，定位断点位置。

**输入**：`student_steps`, `solution_steps`

**输出**：`BreakpointLocation`

**断点类型**：`MISSING_STEP` | `WRONG_DIRECTION` | `INCOMPLETE_STEP` | `STUCK` | `NO_BREAKPOINT`

**三级语义匹配**：

```
Step 1: 关键词 Jaccard 重叠
  overlap > 0.8  → 匹配，继续
  overlap < 0.3  → 进入 Step 2

Step 2: 字符串相似度
  effective_sim > 0.8  → 匹配，继续
  effective_sim < 0.3 → 进入 Step 3

Step 3: WRONG_DIRECTION 判断
  keyword < 0.3 AND string_sim < 0.2  → WRONG_DIRECTION
  否则 → INCOMPLETE（继续扫描）
```

**设计原则**：INCOMPLETE 不停止（继续扫描找到真正断点）；双重低才判 WRONG；纯逻辑无需 LLM。

### 节点 2a：DimensionRouter（维度路由）

**职责**：判断断点属于哪个维度（Resource / Metacognitive）。

**输入**：`student_input`, `expected_step`, `breakpoint_type`, `problem_context`

**输出**：`DimensionResult { dimension: DimensionEnum, confidence: float, reasoning: str }`

**判断逻辑**：

- `MISSING_STEP` → 强 Resource（学生不知道这一步）
- `WRONG_DIRECTION` → 强 Metacognitive（学生有知识但方向错了）
- `INCOMPLETE_STEP` → 偏向 Resource（学生能做但不完整）
- `STUCK` → 偏向 Resource（缺乏起始方向）

### 节点 2b：SubTypeDecider（子类型决策）

**职责**：在维度内部确定具体子类型（R1-R4 / M1-M5）。

**输入**：`dimension`, `student_input`, `expected_step`, `intervention_memory`, `frontend_signal`, `current_level`, `problem_context`

**输出**：`SubTypeResult { sub_type: PromptLevelEnum, reasoning: str, escalation_decision: EscalationDecision }`

**级别定义**：

| 维度 | 级别 | 强度范围 | 提示特点                     |
| ---- | ---- | -------- | ---------------------------- |
| R    | R1   | 0.0-0.25 | 方向引导，不给具体内容       |
| R    | R2   | 0.25-0.5 | 部分提示，揭示关键方向       |
| R    | R3   | 0.5-0.75 | 接近完整思路，关键步骤有提示 |
| R    | R4   | 0.75-1.0 | 完整思路，学生自己完成计算   |
| M    | M1   | 0.0-0.2  | 唤醒反思，不直接给解题方向   |
| M    | M2   | 0.2-0.4  | 点出可能的策略方向           |
| M    | M3   | 0.4-0.6  | 建议使用某种策略并说明原因   |
| M    | M4   | 0.6-0.8  | 比较多种策略的优劣           |
| M    | M5   | 0.8-1.0  | 引导学生比较并选择策略       |

**升级决策**：当 `frontend_signal = NOT_PROGRESSED` 或 `DISMISSED` 时，根据 `escalation_decision` 升级到下一级别。

### 节点 4：HintGeneratorV2（提示生成）

**职责**：根据子类型和强度生成提示。

**输入**：`level`, `problem_context`, `student_input`, `expected_step`, `student_steps`

**输出**：`GeneratedHint { content: str, level: str, approach_used: str, original_intensity: float }`

**原则**：永不直接给出完整答案，只引导学生自己发现。

### 节点 5：OutputGuardrail（输出守卫）

**职责**：检查提示是否安全。

**检查项**：

- 是否包含答案关键词（如"答案是"、"得证"等）
- 是否过于直接（等于替学生完成推理）
- 内容长度是否异常

**处理**：如果检查失败，用中性提示替换，并记录 `unsafe_content`。

## ContextManager（状态管理）

`ContextManager` 管理每个 session 的干预状态，支持内存+MongoDB 双写持久化：

```python
class InterventionContext:
    session_id: str
    student_id: str
    dimension_result: DimensionResult       # 维度诊断结果
    current_level: PromptLevelEnum         # 当前提示级别
    intervention_memory: List[InterventionRecord]  # 历史干预
    status: InterventionStatus
    student_input: str
```

关键操作：

- `apply_escalation()` — 根据 escalation_decision 升级
- `update_sub_type_result()` — 记录当前子类型决策
- `record_intervention()` — 记录已生成的干预，异步持久化到 MongoDB
- `handle_frontend_signal()` — 处理学生反馈信号（PROGRESSED / NOT_PROGRESSED / DISMISSED）

**MongoDB 持久化**：每次 `record_intervention()`、`apply_escalation()`、`handle_frontend_signal()` 后自动将 Context 同步到 MongoDB `intervention_contexts` 集合。`Intervention` 对象同步写入 `interventions` 集合。服务重启后可从 MongoDB 恢复 session 状态。

## 架构

```
app/modules/intervention/
├── __init__.py
├── module.py                 # 模块入口（initialize/shutdown/router注册）
├── routes.py                 # API 路由（7个端点）
├── service.py                # 总控服务（v2 五节点管道）
├── models.py                 # 数据模型
│
├── context_manager.py        # 状态管理（新增）
│
├── locator/                  # 节点1：断点定位（纯逻辑）
│   ├── __init__.py
│   ├── breaker.py            # BreakpointLocator
│   └── models.py             # BreakpointLocation, BreakpointType
│
├── router/                   # 节点2a：维度路由
│   ├── __init__.py
│   ├── dimension_router.py   # DimensionRouter
│   └── models.py             # DimensionResult, DimensionEnum
│
├── decider/                  # 节点2b：子类型决策
│   ├── __init__.py
│   ├── sub_type_decider.py   # SubTypeDecider
│   └── models.py             # SubTypeResult, PromptLevelEnum, EscalationDecision
│
├── generator/                # 节点4：提示生成
│   ├── __init__.py
│   ├── hints_v2.py           # HintGeneratorV2（R1-R4/M1-M5 模板）
│   └── prompts.py            # 提示词模板
│
└── guardrail/               # 节点5：输出守卫
    ├── __init__.py
    ├── guardrail.py          # OutputGuardrail
    └── models.py             # GuardrailResult
```

## API 接口

### POST /interventions

创建干预。

| 字段         | 类型  | 必填 | 说明                                         |
| ------------ | ----- | ---- | -------------------------------------------- |
| `session_id` | str   | ✅   | 会话ID（从 SessionState 读取 solving state） |
| `student_id` | str   | ❌   | 学生ID                                       |
| `intensity`  | float | ❌   | 初始干预强度，默认 0.5                       |

### POST /interventions/feedback

学生反馈。

| 字段              | 类型               | 必填 | 说明                       |
| ----------------- | ------------------ | ---- | -------------------------- |
| `session_id`      | str                | ✅   | 会话ID                     |
| `student_input`   | str                | ❌   | 学生当前输入               |
| `frontend_signal` | FrontendSignalEnum | ❌   | 进步/未进步/忽略/接受/拒绝 |

`frontend_signal` 可选值：

- `PROGRESSED` — 学生有进步，继续当前策略
- `NOT_PROGRESSED` — 学生未进步，升级干预
- `DISMISSED` — 学生忽略提示，升级干预
- `ACCEPTED` — 学生接受提示
- `REJECTED` — 学生拒绝提示

### POST /interventions/end

结束干预。

| 字段         | 类型 | 必填 | 说明     |
| ------------ | ---- | ---- | -------- |
| `session_id` | str  | ✅   | 会话ID   |
| `reason`     | str  | ❌   | 结束原因 |

### POST /interventions/escalate

强制升级。

| 字段         | 类型 | 必填 | 说明     |
| ------------ | ---- | ---- | -------- |
| `session_id` | str  | ✅   | 会话ID   |
| `reason`     | str  | ❌   | 升级原因 |

## 数据模型

### Intervention

```python
class Intervention(BaseModel):
    id: str
    student_id: str
    session_id: str
    intervention_type: InterventionType
    status: InterventionStatus
    content: str
    intensity: float
    metadata: dict  # 包含 breakpoint_type, dimension, prompt_level 等
    created_at: datetime
```

### DimensionResult

```python
class DimensionResult:
    dimension: DimensionEnum  # RESOURCE / METACOGNITIVE
    confidence: float
    reasoning: str
```

### SubTypeResult

```python
class SubTypeResult:
    sub_type: PromptLevelEnum  # R1-R4 / M1-M5
    reasoning: str
    escalation_decision: EscalationDecision
```

### EscalationDecision

```python
class EscalationDecision:
    action: EscalationAction  # ESCALATE / MAINTAIN / TERMINATE
    next_level: Optional[PromptLevelEnum]
    reason: str
```

## 使用示例

```python
from app.modules.intervention.service import InterventionService

service = InterventionService()

# 创建干预（session_id 必须）
response = await service.generate(
    session_id="sess_001",
    intensity=0.5,
    student_id="student_001",
)
print(response.intervention.content)

# 学生反馈：未进步 → 自动升级
response = await service.process_feedback(
    session_id="sess_001",
    frontend_signal=FrontendSignalEnum.NOT_PROGRESSED,
    student_input="学生仍然卡在构造步骤",
)

# 学生反馈：进步了 → 继续当前策略
response = await service.process_feedback(
    session_id="sess_001",
    frontend_signal=FrontendSignalEnum.PROGRESSED,
)
```

## 测试

```bash
# 运行干预模块测试（87 个测试）
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

详见 [`tests/modules/test_intervention/README.md`](../tests/modules/test_intervention/README.md)

## 环境变量

| 变量                 | 必填 | 说明                        |
| -------------------- | ---- | --------------------------- |
| `DASHSCOPE_API_KEY`  | ✅   | 阿里云 DashScope API Key    |
| `INTERVENTION_MODEL` | ❌   | 干预模型，默认 `qwen-turbo` |

## 与 Module 1 的关系

- Module 1 的 `SolvingService.generate(request, session_id="xxx")` 生成参考解法后，自动将 solving state 存入 SessionState
- Module 2 通过 `session_id` 从 SessionState 读取 solving state（problem、solution_steps、student_steps、student_work）
- 干预完成后，学生可继续 Module 1 的解题目线

## 后续扩展方向

1. **强度自动调节**：根据学生历史接受率动态调整 intensity
2. **多轮干预闭环**：学生接受/拒绝后自动生成下一轮提示
3. **✅ MongoDB 持久化**：将干预记录存入数据库用于分析（已实现）
4. **跨维度升级路径**：R4 仍失败后可切换到 Metacognitive 维度
