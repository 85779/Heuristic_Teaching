# Module 2: 断点分层递进干预系统

## 概述

Module 2 的核心任务，是在学生处于断点、尚未继续生成下一推进步骤时，围绕该断点建立一个由**断点定位 → 断点分析 → 分层干预决策 → 提示生成**构成的递进支架系统。

它的目标不是替代学生完成后续推理，而是在保持学生自主推进权的前提下，帮助其跨越当前断点，并重新接回 Module 1 所提供的整体解题目线。

```
Module 1 (Solving)                     Module 2 (Intervention)
┌──────────────────────┐              ┌──────────────────────┐
│ 生成带步骤的参考解法   │              │                       │
│                      │              │                       │
│ solution_steps       │ ──事件触发──▶│  接收断点             │
│  → SessionState      │              │                       │
└──────────────────────┘              │  POST /interventions   │
                                        │         │              │
                                        │         ▼              │
                                        │  BreakpointLocator     │
                                        │         │              │
                                        │         ▼              │
                                        │  BreakpointAnalyzer    │
                                        │         │              │
                                        │         ▼              │
                                        │  HintGenerator         │
                                        │         │              │
                                        │         ▼              │
                                        │  返回提示内容           │
                                        └──────────────────────┘
```

## 架构

```
app/modules/intervention/
├── __init__.py                     # 导出 InterventionModule
├── module.py                        # 模块入口（initialize/shutdown/router注册）
├── routes.py                        # API 路由（4个端点）
├── service.py                       # 总控服务
├── models.py                        # 数据模型
│
├── locator/                        # 子模块1：断点定位（纯逻辑）
│   ├── __init__.py
│   ├── breaker.py                   # BreakpointLocator
│   └── models.py                    # BreakpointLocation, BreakpointType
│
├── analyzer/                        # 子模块2：断点分析（LLM）
│   ├── __init__.py
│   ├── analyzer.py                  # BreakpointAnalyzer
│   ├── models.py                   # BreakpointAnalysis
│   └── prompts.py                   # 分析提示词模板
│
├── generator/                       # 子模块3：提示生成（LLM）
│   ├── __init__.py
│   ├── generator.py                 # HintGenerator
│   ├── models.py                   # GeneratedHint
│   └── prompts.py                  # 生成提示词模板
│
└── prompts/                        # 顶层提示词（保留，暂未使用）
    ├── __init__.py
    ├── hint.py
    ├── analysis.py
    ├── decision.py
    ├── intensity.py
    └── location.py
```

## 模块导出

```python
# app/modules/intervention/__init__.py
from app.modules.intervention.module import InterventionModule

__all__ = ["InterventionModule"]
```

## 模块初始化

### InterventionModule

```python
class InterventionModule(IModule):
    module_id: str = "intervention"
    module_name: str = "Intervention Module"
    version: str = "1.0.0"
    dependencies: list = ["solving"]       # 依赖 Module 1

    provides_events: list = [               # 发布的的事件
        "intervention.suggested",
        "intervention.delivered",
        "intervention.dismissed",
    ]

    subscribes_events: list = [             # 订阅的事件
        "solving.step_completed",
        "solving.error_detected",
        "solving.stuck_detected",
    ]
```

**initialize()**:

1. 创建 `InterventionService`
2. 订阅 `solving.*` 事件
3. 设置 routes 的 service 实例

**shutdown()**:

- 记录关闭日志

## 提示词设计

### 断点分析提示词 (analyzer/prompts.py)

引导 LLM 分析"跨越断点需要什么"，返回 JSON：

```json
{
  "required_knowledge": ["gcd的定义", "正整数序列的概念"],
  "required_connection": "需要建立的关键联系",
  "possible_approaches": ["路径1", "路径2"],
  "difficulty_level": 0.5
}
```

### 提示生成提示词 (generator/prompts.py)

根据 intensity 调整提示显性程度：

**surface (intensity < 0.4)**:

> 只给方向性提示，不给具体解法。
> 例如："想想题目中已知条件和所求目标之间的关系"

**middle (0.4 ≤ intensity < 0.7)**:

> 给部分提示 + 类比示例。
> 例如："可以尝试先求出某个中间量，类似于之前学过的某某题型"

**deep (intensity ≥ 0.7)**:

> 给完整示例 + 步骤讲解。
> 例如："来看一个完全一样的例子...第一步...第二步..."

## 核心流程

```
POST /interventions
    │
    ▼
┌─────────────────────────────────────────────┐
│  InterventionService.generate()                    │
│                                               │
│  输入:                                          │
│    - problem: 题目                             │
│    - student_work: 学生当前作答（可选）         │
│    - student_steps: 学生已完成的步骤            │
│    - solution_steps: Module1生成的参考解法步骤  │
│    - intensity: 干预强度 (0.0~1.0)             │
│    - session_id / student_id                    │
│                                               │
│  Step 1: BreakpointLocator.locate()            │
│    → 对比学生steps vs 参考解法steps            │
│    → 定位断点位置和类型                        │
│                                               │
│  Step 2: BreakpointAnalyzer.analyze()          │
│    → LLM分析跨越断点需要什么                   │
│    → 所需知识、关键联系、可选路径              │
│                                               │
│  Step 3: HintGenerator.generate()               │
│    → 根据断点分析 + intensity 生成提示          │
│    → intensity决定提示的显性程度                │
│                                               │
│  输出: Intervention (提示内容、层面、路径)     │
└─────────────────────────────────────────────┘
```

## 子模块

### 1. BreakpointLocator（断点定位）

**职责**：比较学生步骤与参考解法步骤，定位断点位置。

**输入**：`student_steps`, `solution_steps`（均为 `List[TeachingStep]`）

**输出**：`BreakpointLocation`

**断点类型**：

| 类型              | 说明                           |
| ----------------- | ------------------------------ |
| `MISSING_STEP`    | 学生缺少某一步骤               |
| `WRONG_DIRECTION` | 学生在某一步的方向偏离参考解法 |
| `INCOMPLETE_STEP` | 学生某一步的内容不完整（太短） |
| `STUCK`           | 学生完全没有步骤，无法确定断点 |
| `NO_BREAKPOINT`   | 学生步骤与参考解法一致，无断点 |

**定位逻辑**：

- 逐个对比学生步骤与参考解法步骤
- 第一个差异点即为断点位置
- 纯逻辑计算，无需 LLM 调用

### 2. BreakpointAnalyzer（断点分析）

**职责**：分析跨越断点需要什么知识和能力。

**输入**：`BreakpointLocation`, `problem`, `student_work`, `solution_steps`

**输出**：`BreakpointAnalysis`

**LLM 分析内容**：

1. **required_knowledge**：跨越断点需要的知识点
2. **required_connection**：需要建立的关键联系
3. **possible_approaches**：可选的跨越路径
4. **difficulty_level**：难度等级（0.0~1.0）

**特点**：分析的是"跨越断点需要什么"，而非"学生为什么错"。

### 3. HintGenerator（提示生成）

**职责**：根据断点分析和强度生成提示。

**输入**：`BreakpointAnalysis`, `problem`, `intensity`

**输出**：`GeneratedHint`

**强度与层面**：

| intensity | level   | 提示特点                               |
| --------- | ------- | -------------------------------------- |
| < 0.4     | surface | 方向性提示，只给思考方向，不给具体解法 |
| 0.4 ~ 0.7 | middle  | 部分提示 + 类比示例                    |
| ≥ 0.7     | deep    | 完整示例 + 步骤讲解                    |

**原则**：永不直接给出完整答案，只引导学生自己发现。

## API 接口

### POST /interventions

创建干预。

**请求体**：

| 字段                | 类型 | 必填 | 说明                                                                         |
| ------------------- | ---- | ---- | ---------------------------------------------------------------------------- |
| `student_id`        | str  | ✅   | 学生ID                                                                       |
| `session_id`        | str  | ✅   | 会话ID                                                                       |
| `intervention_type` | str  | ❌   | 干预类型，默认 hint                                                          |
| `context`           | dict | ✅   | 上下文，包含 problem, student_work, student_steps, solution_steps, intensity |

**context 字段说明**：

```json
{
  "problem": "LaTeX 题目",
  "student_work": "学生当前作答（可选）",
  "student_steps": [
    { "step_id": "s1", "step_name": "步骤名", "content": "步骤内容" }
  ],
  "solution_steps": [
    { "step_id": "s1", "step_name": "步骤名", "content": "步骤内容" }
  ],
  "intensity": 0.5
}
```

**响应体**：

| 字段           | 类型         | 说明           |
| -------------- | ------------ | -------------- |
| `success`      | bool         | 是否成功       |
| `intervention` | Intervention | 生成的干预对象 |
| `message`      | str          | 状态消息       |

### GET /interventions/{intervention_id}

获取指定干预。

### POST /interventions/{intervention_id}/accept

标记干预为已接受。

### POST /interventions/{intervention_id}/dismiss

标记干预为已拒绝。

## 数据模型

### Intervention

```python
class Intervention(BaseModel):
    id: str                           # 唯一标识
    student_id: str                    # 学生ID
    session_id: str                    # 会话ID
    intervention_type: InterventionType # 干预类型
    status: InterventionStatus          # 状态
    content: str                       # 提示内容
    intensity: float                    # 强度 (0.0~1.0)
    metadata: dict                     # 元数据（包含断点信息、提示层面等）
    created_at: datetime                # 创建时间
    delivered_at: Optional[datetime]   # 送达时间
    outcome_at: Optional[datetime]     # 结果时间
```

### InterventionStatus

| 状态        | 说明           |
| ----------- | -------------- |
| `suggested` | 已生成，待送达 |
| `delivered` | 已送达学生     |
| `accepted`  | 学生接受       |
| `dismissed` | 学生拒绝       |
| `ignored`   | 学生忽略       |

### InterventionType

| 类型          | 说明         |
| ------------- | ------------ |
| `HINT`        | 提示（默认） |
| `EXPLANATION` | 解释         |
| `REDIRECT`    | 重定向       |
| `EXAMPLE`     | 示例         |
| `SCAFFOLD`    | 支架         |

### BreakpointLocation

```python
@dataclass
class BreakpointLocation:
    breakpoint_position: int           # 断点位置（0-indexed）
    breakpoint_type: BreakpointType    # 断点类型
    expected_step_content: str        # 期望的下一步内容
    gap_description: str               # 间隙描述
    student_last_step: Optional[str]   # 学生最后一步
```

### BreakpointAnalysis

```python
@dataclass
class BreakpointAnalysis:
    required_knowledge: List[str]     # 所需知识点
    required_connection: str            # 关键联系
    possible_approaches: List[str]    # 可选路径
    difficulty_level: float            # 难度 0.0~1.0
```

### GeneratedHint

```python
@dataclass
class GeneratedHint:
    content: str                       # 提示内容
    level: str                        # 层面 (surface/middle/deep)
    approach_used: str                 # 使用的解题思路
    original_intensity: float          # 原始强度值
```

## 使用示例

### 1. 通过 API 调用

```python
import requests

response = requests.post("http://localhost:8000/interventions", json={
    "student_id": "student_001",
    "session_id": "session_001",
    "intervention_type": "hint",
    "context": {
        "problem": "设 $a_0, a_1, \\ldots$ 是正整数序列...",
        "student_work": "解：设 a_0 = 1。",
        "student_steps": [
            {"step_id": "s1", "step_name": "理解问题", "content": "理解题目要求..."}
        ],
        "solution_steps": [
            {"step_id": "s1", "step_name": "理解问题", "content": "..."},
            {"step_id": "s2", "step_name": "构造", "content": "..."},
        ],
        "intensity": 0.5
    }
})

intervention = response.json()["intervention"]
print(intervention["content"])  # 打印提示内容
```

### 2. 直接调用 Service

```python
from app.modules.intervention.service import InterventionService

service = InterventionService()

intervention = await service.generate(
    problem="设 $a_0, a_1, \\ldots$ 是正整数序列...",
    student_work="解：设 a_0 = 1。",
    student_steps=[{"step_id": "s1", "step_name": "步骤", "content": "内容"}],
    solution_steps=[{"step_id": "s1", "step_name": "步骤", "content": "内容"}],
    intensity=0.5,
    session_id="sess_001",
    student_id="student_001",
)

print(intervention.content)
print(intervention.metadata["hint_level"])
```

## 测试

```bash
# 运行干预模块测试
cd backend
python -m pytest tests/modules/test_intervention/ -v

# 手动 E2E 测试（需要真实 API Key）
python tests/modules/test_intervention/manual_test.py
```

详见 [`tests/modules/test_intervention/README.md`](../tests/modules/test_intervention/README.md)

## Fixtures (conftest.py)

测试使用的 pytest fixtures：

```python
@pytest.fixture
def breakpoint_locator():
    """Fresh BreakpointLocator instance."""
    from app.modules.intervention.locator.breaker import BreakpointLocator
    return BreakpointLocator()

@pytest.fixture
def mock_breakpoint_analyzer():
    """Mock BreakpointAnalyzer with canned BreakpointAnalysis."""
    from unittest.mock import AsyncMock
    analyzer = AsyncMock()
    analyzer.analyze.return_value = BreakpointAnalysis(
        required_knowledge=["知识点A"],
        required_connection="联系",
        possible_approaches=["方法"],
        difficulty_level=0.6,
    )
    return analyzer

@pytest.fixture
def mock_hint_generator():
    """Mock HintGenerator with canned GeneratedHint."""
    from unittest.mock import AsyncMock
    gen = AsyncMock()
    gen.generate.return_value = GeneratedHint(
        content="提示内容",
        level="middle",
        approach_used="类比法",
        original_intensity=0.5,
    )
    return gen

@pytest.fixture
def intervention_service():
    """Fresh InterventionService with mocked sub-modules."""
    # Creates service with mocked BreakpointLocator, BreakpointAnalyzer, HintGenerator
    ...
```

## 环境变量

| 变量                 | 必填 | 说明                        |
| -------------------- | ---- | --------------------------- |
| `DASHSCOPE_API_KEY`  | ✅   | 阿里云 DashScope API Key    |
| `INTERVENTION_MODEL` | ❌   | 干预模型，默认 `qwen-turbo` |

## 与 Module 1 的关系

- Module 2 订阅 Module 1 发布的事件（`solving.stuck_detected`, `solving.error_detected`, `solving.step_completed`）
- Module 1 生成的 `solution_steps` 是 Module 2 定位断点的参考
- 学生步骤来自 SessionState 或 Module 1 的逐步反馈

## 后续扩展方向

1. **强度自动调节**：根据学生历史接受率动态调整 intensity
2. **语义级断点匹配**：用 embedding 相似度而非字符串匹配判断断点
3. **多轮干预闭环**：学生接受/拒绝后自动生成下一轮提示
4. **MongoDB 持久化**：将干预记录存入数据库用于分析
