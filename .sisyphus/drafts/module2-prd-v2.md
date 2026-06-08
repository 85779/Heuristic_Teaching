# Module 2 断点分层递进干预系统 PRD v2

> 基于框架评审（module2-prd-review.md）整合所有确认内容，可用于论文写作和代码实现。

---

## 一、系统概述

### 1.1 核心目标

建立一个由"**断点定位—断点诊断—断点干预**"构成的递进支架系统。系统需在保持学生自主推进权的前提下，帮助其跨越当前断点，并重新接回 Module 1 生成的参考解主治线。

**系统不直接给出最终答案**，而是动态判断介入的维度与强度。

### 1.2 核心运转流程（四大步骤）

```
Step 1: 定位断点
  识别学生当前作答状态与参考解主治线下一关键步骤之间的局部间隙。

Step 2: 断点诊断
  - 解题侧分析：明确从当前步骤到下一步骤，对资源侧和元认知侧的要求。
  - 学生状态估计：判断学生当前的困难究竟出在"想不出/接不住"（资源侧）还是"不会选/不会守/不会换"（元认知侧）。

Step 3: 断点提示生成
  比较断点跨越要求与学生当前状态，确定干预维度（R或M）与强度等级，生成具体提示。

Step 4: 动态更新反馈
  根据学生接收提示后的新一轮作答表现，修正状态估计，决定是否维持、切换、升级或降级干预。
```

---

## 二、双维诊断框架

### 2.1 资源侧 vs 元认知侧

**两个维度的精确定义**：

```
Resource（资源侧）：
"下一步能不能出现"——学生是否形成了可用的候选路径。

核心问题：
- 学生是否形成了对下一步的候选？
- 这个候选依赖哪些知识/图式？
- 学生是否能识别触发这个图式的线索？

典型特征：
- 空白提交，完全不知道下一步怎么走
- 有思路，但依赖的知识/图式本身错误或缺失
- 方向完全错误（WRONG_DIRECTION）——没有形成正确的候选路径
- 断点类型为 MISSING_STEP、WRONG_DIRECTION 或 STUCK

Metacognitive（元认知侧）：
"当前路径怎么管"——候选图式已经出现，路径已经激活后，如何管理和推进。

核心问题：
- 候选路径是否仍然有效？
- 下一步该往哪推进？
- 什么情况下应该停止、回退或切换？

典型特征：
- 方向看起来对，但不知道下一步怎么展开
- 能看到目标，但看不清当前路径是否仍有效
- 局部卡住，不确定该继续坚持还是换路
- 断点类型为 INCOMPLETE_STEP
```

**连接点：图式**
- Resource → 提供"有什么可走、为什么会出现"
- Metacognitive → 对已激活路径"如何判定、推进与修正"
- 两者在同一个"下一步"上形成前后衔接，不是平行关系

### 2.2 断点类型 → 困难维度映射

| 断点类型 | 映射维度 | 原因 |
|----------|----------|------|
| MISSING_STEP | Resource | 没有形成候选路径 |
| WRONG_DIRECTION | Resource | 候选路径本身就是错的，没有形成正确的"可走之路" |
| INCOMPLETE_STEP | Metacognitive | 候选路径已出现，方向对但展开不完整 |
| STUCK | Resource | 完全不知道下一步怎么走 |

> ⚠️ WRONG_DIRECTION 不是 Metacognitive 问题——方向错说明没有形成正确的候选，是 Resource 问题。

---

## 三、干预策略库

### 3.1 资源侧策略（R1-R4）

| 等级 | 核心问题 | 显性程度 | 典型形式 |
|------|----------|----------|----------|
| **R1** | 触发线索 | 最低 | "先看看题目里哪种结构最显眼" |
| **R2** | 图式方向 | 低 | "这一步需要换元法"（只给方法类型，不展开） |
| **R3** | 知识/定理 | 中 | "换元法：设 t = x+1，把分母统一成 t²" |
| **R4** | 第一小步 | 高 | "第一步：设 t = x+1，整理得 t²-3t+2=0" |

**R2 → R3 边界**：R2 只给图式名/方法类型；R3 给出了具体定理的详细内容
**R3 → R4 边界**：R3 只给出定理/知识内容；R4 通过定理生成了真实的第一小步

**升级由 LLM 判断**。

### 3.2 元认知侧策略（M1-M5）

| 等级 | 核心问题 | 典型形式 |
|------|----------|----------|
| **M1** | 这条路的"前景"如何？还值得走吗？ | "再做两步会得到什么？" |
| **M2** | 这条路的"局部"卡住了，别放弃 | "这条路还在产生有效信息" |
| **M3** | 既然对，第一小步是什么？ | "先找最关键的落脚点" |
| **M4** | 这条路不行了，该停了 | "先停，不要继续堆步骤" |
| **M5** | 路换了，从哪起步？ | "哪个候选更可能生成果" |

**M1 vs M3 边界**：
- M1：帮助判断"该继续还是该停" → 不给具体下一步，而是问"前景是什么"
- M3：帮助确定"下一步往哪走" → 在路径内部给出推进方向

**M3 升级**：M3 失败后，LLM 判断给更详细的 M3+ 还是切换到 M4（只有断点切换时才切 M4）

---

## 四、升级/切换规则

### 4.1 同维度内升级

```
R1 → R2 → R3 → R4（R4为Resource最高级，不可再升）
M1 → M2 → M3 → M4 → M5（M5为Metacognitive最高级，不可再升）
```

### 4.2 M侧无法解决 → 切换到R侧

```
条件：M1-M5任意级别，student_response == "not_progressed"
结果：切换到Resource维度，从R1重新开始判断
含义：元认知层面给到极限仍不行，说明学生可能存在潜在的资源/知识缺口
```

### 4.3 R侧无法解决 → 终止AI干预

```
条件：R4，student_response == "not_progressed"
结果：输出"不能直接给你答案，建议暂停尝试，或寻求老师帮助"
含义：Resource给到最高级仍不行，说明学生可能不是真的在做题
```

### 4.4 M侧升级不完全线性

```
M1 失败 → M2 或 M3+（看学生是需要维持还是更具体）
M2 失败 → M3 或 M3+（看学生是需要推进还是更具体）
M3 失败 → M3+（更详细）或 M4（只有断点切换时才切M4）
M4 失败 → M5
M5 失败 → switch_to_resource
```

> ⚠️ R侧不能切换到M侧：R侧到达最高级必须终止，不允许切换

---

## 五、学生反馈采集机制

### 5.1 双重信号控制

```
Node 1 自动判断（后端）：
  - accepted       → 学生推进了（断点消失/推进到新位置）
  - not_progressed → 学生没推进（断点位置没变）

前端信号（可选）：
  - END      → 直接结束干预
  - ESCALATE → 强制升级到更高一级提示
```

### 5.2 前端交互

```
[我知道了]        → END
[给我更强提示]    → ESCALATE
```

### 5.3 Node 2b 判断逻辑

```
1. frontend_signal == END → 直接终止
2. frontend_signal == ESCALATE → 强制升级（+1级）
3. frontend_signal == null + student_response == "accepted" → 结束，或继续
4. frontend_signal == null + student_response == "not_progressed" → 升级
   - R4最高级 → 终止
   - M5最高级 → 切换到R侧
```

---

## 六、系统架构设计

### 6.1 整体数据流

```
┌─────────────────────────────────────────────────────────────┐
│                    Global State Object                      │
│  problem_context / student_history / intervention_memory     │
│  current_diagnosis / current_student_input                  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────┴─────────────────────────────┐
│                          Node 1                            │
│                    Breakpoint Locator                       │
│  输入: student_input, solution_steps                       │
│  输出: {breakpoint_type, expected_step, gap_description}  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────┴─────────────────────────────┐
│                          Node 2a                            │
│                   Dimension Router                          │
│  输入: student_input, expected_step, breakpoint_type,     │
│        intervention_memory                                  │
│  输出: {dimension: "Resource"|"Metacognitive",            │
│         confidence, reasoning}                             │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────┴─────────────────────────────┐
│                          Node 2b                            │
│              Sub-type Decider + Escalation Manager           │
│  输入: dimension, student_input, expected_step,            │
│        intervention_memory, frontend_signal                 │
│  输出: {sub_type, confidence, reasoning, hint_direction,    │
│         escalation_decision}                                │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────┴─────────────────────────────┐
│                          Node 3                            │
│                  Strategy Controller                         │
│  纯代码执行，根据 escalation_decision 操作 Global State     │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────┴─────────────────────────────┐
│                          Node 4                            │
│                   Prompt Generator                          │
│  输入: sub_type, hint_direction, problem_context          │
│  输出: 提示内容                                             │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────┴─────────────────────────────┐
│                          Node 5                            │
│                    Output Guardrail                         │
│  LLM-as-a-Judge，检查提示是否越界                          │
│  输出: {pass: bool, reason: str}                           │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Node 职责定义

| Node | 职责 | 决策权 |
|------|------|--------|
| Node 1 | 断点定位 | 无（纯逻辑计算） |
| Node 2a | R/M 二元分流 | 有（dimension判断） |
| Node 2b | 等级决策 + 升级策略 | 有（sub_type + escalation_decision） |
| Node 3 | 执行操作 | 无（纯代码执行） |
| Node 4 | 提示生成 | 无（根据sub_type模板生成） |
| Node 5 | 输出审查 | 有（pass/reject） |

---

## 七、数据结构与上下文管理

### 7.1 Module 2 内部数据结构

```python
@dataclass
class InterventionRecord:
    """干预记录"""
    turn: int                              # 第几轮干预
    qa_history: QaHistory                  # 学生问答
    prompt_level: str                      # R1-R4 / M1-M5
    prompt_content: str                    # 提示内容
    student_response: str                  # "accepted" | "not_progressed"
    frontend_signal: str                   # "END" | "ESCALATE" | null
    breakpoint_status: str                 # "resolved" | "persistent"


@dataclass
class QaHistory:
    """问答历史"""
    student_q: str                         # 学生的问题/行为
    system_a: str                          # 系统的提示内容


@dataclass
class Diagnosis:
    """当前诊断结果"""
    dimension: str                          # "Resource" | "Metacognitive"
    sub_type: str                          # R1-R4 / M1-M5
    confidence: float                      # 置信度 0.0-1.0
    reasoning: str                         # 判断理由
    escalation_decision: EscalationDecision


@dataclass
class EscalationDecision:
    """升级决策"""
    action: str                            # "maintain" | "escalate" | "switch_to_resource" | "max_level_reached"
    from_level: str                        # 当前等级
    to_level: Optional[str]                # 目标等级
    reasoning: str                         # 决策理由
    system_response: Optional[str]           # max_level_reached时的最终回复


@dataclass
class InterventionContext:
    """Node间传递的上下文"""
    session_id: str
    student_id: str
    problem_context: str                  # 题目原文
    student_input: str                   # 学生当前输入
    solution_steps: List[dict]            # 参考解法步骤
    student_steps: List[dict]            # 学生历史步骤
    breakpoint_location: BreakpointLocation # Node 1 输出
    dimension_result: DimensionResult       # Node 2a 输出
    sub_type_result: SubTypeResult        # Node 2b 输出
    intervention_memory: List[InterventionRecord]  # 历史干预记录
    current_level: str                   # 当前提示等级
    status: str                          # "active" | "completed" | "terminated"
```

### 7.2 上下文在Node间的流转

```
┌──────────────────────────────────────────────────────────────────┐
│                    InterventionContext                              │
│  session_id / student_id / problem_context / solution_steps       │
│  breakpoint_location / dimension_result / sub_type_result         │
│  intervention_memory / current_level / status                     │
└──────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
    ┌──────────┐       ┌──────────┐       ┌──────────┐
    │  Node 1  │──────▶│  Node 2a │──────▶│  Node 2b │
    │  Locator │       │  Router  │       │  Decider │
    └──────────┘       └──────────┘       └──────────┘
          │                   │                   │
          ▼                   │                   ▼
  设置 breakpoint_location    │           设置 escalation_decision
                              │                   │
                              └───────────────────┼───────────────────┘
                                                  ▼
                                            ┌──────────┐
                                            │  Node 3  │
                                            │ Controller│
                                            └──────────┘
                                                  │
                                    ┌─────────────┼─────────────┐
                                    ▼             ▼             ▼
                              ┌──────────┐ ┌──────────┐ ┌──────────┐
                              │  Node 4  │ │  Node 5  │ │ 存储     │
                              │ Generator│ │ Guardrail│ │ Context  │
                              └──────────┘ └──────────┘ └──────────┘
                                    │             │             │
                                    ▼             ▼             ▼
                              返回提示内容   越界检查    更新 intervention_memory
```

### 7.3 上下文更新规则

每个Node执行后，上下文必须按以下规则更新：

```python
class ContextManager:
    """上下文管理器 - 负责上下文的创建、更新、存储"""

    def __init__(self, state_manager: StateManager):
        self._state_manager = state_manager

    # ============================================================
    # 读取/创建上下文
    # ============================================================

    def get_or_create_context(
        self,
        session_id: str,
        student_id: str,
        student_input: str
    ) -> InterventionContext:
        """
        获取或创建干预上下文。
        首次干预时从 SessionState 读取 solving state。
        """
        # 1. 读取 Module 1 的 solving state
        solving_state = self._state_manager.get_module_state(session_id, "solving")

        # 2. 读取已有的 intervention state（如果存在）
        intervention_state = self._state_manager.get_module_state(session_id, "intervention")

        if intervention_state:
            # 恢复上下文
            return self._restore_from_state(intervention_state, solving_state)
        else:
            # 创建新上下文
            return InterventionContext(
                session_id=session_id,
                student_id=student_id,
                problem_context=solving_state["problem"],
                student_input=student_input,
                solution_steps=solving_state["solution_steps"],
                student_steps=solving_state.get("student_steps", []),
                breakpoint_location=None,
                dimension_result=None,
                sub_type_result=None,
                intervention_memory=[],
                current_level="",
                status="active"
            )

    # ============================================================
    # Node 1 执行后 - 更新断点位置
    # ============================================================

    def update_breakpoint_location(
        self,
        ctx: InterventionContext,
        location: BreakpointLocation
    ) -> InterventionContext:
        """Node 1 执行后调用"""
        ctx.breakpoint_location = location
        return ctx

    # ============================================================
    # Node 2a 执行后 - 更新维度结果
    # ============================================================

    def update_dimension_result(
        self,
        ctx: InterventionContext,
        result: DimensionResult
    ) -> InterventionContext:
        """Node 2a 执行后调用"""
        ctx.dimension_result = result
        return ctx

    # ============================================================
    # Node 2b 执行后 - 更新等级决策
    # ============================================================

    def update_sub_type_result(
        self,
        ctx: InterventionContext,
        result: SubTypeResult
    ) -> InterventionContext:
        """Node 2b 执行后调用"""
        ctx.sub_type_result = result
        ctx.current_level = result.sub_type
        return ctx

    # ============================================================
    # Node 3 执行后 - 更新状态
    # ============================================================

    def apply_escalation(
        self,
        ctx: InterventionContext,
        action: str,
        new_level: Optional[str] = None
    ) -> InterventionContext:
        """Node 3 根据 escalation_decision 执行操作"""
        if action == "maintain":
            # 维持当前等级
            pass
        elif action == "escalate":
            # 升级
            ctx.current_level = new_level
        elif action == "switch_to_resource":
            # 切换到 Resource 维度
            ctx.dimension_result.dimension = "Resource"
            ctx.current_level = "R1"
        elif action == "max_level_reached":
            # 终止
            ctx.status = "terminated"
        return ctx

    # ============================================================
    # Node 4+5 执行后 - 记录干预
    # ============================================================

    def record_intervention(
        self,
        ctx: InterventionContext,
        prompt_content: str,
        student_response: str,
        breakpoint_status: str
    ) -> InterventionContext:
        """记录一轮干预到 memory"""
        record = InterventionRecord(
            turn=len(ctx.intervention_memory) + 1,
            qa_history=QaHistory(
                student_q=ctx.student_input,
                system_a=prompt_content
            ),
            prompt_level=ctx.current_level,
            prompt_content=prompt_content,
            student_response=student_response,
            frontend_signal=None,  # 由前端传入
            breakpoint_status=breakpoint_status
        )
        ctx.intervention_memory.append(record)
        return ctx

    # ============================================================
    # 保存上下文到 SessionState
    # ============================================================

    def save_context(self, ctx: InterventionContext) -> None:
        """每轮干预后保存上下文到 SessionState"""
        state = {
            "problem_context": ctx.problem_context,
            "current_diagnosis": {
                "dimension": ctx.dimension_result.dimension if ctx.dimension_result else None,
                "sub_type": ctx.sub_type_result.sub_type if ctx.sub_type_result else None,
                "confidence": ctx.dimension_result.confidence if ctx.dimension_result else None,
            } if ctx.dimension_result else None,
            "current_level": ctx.current_level,
            "status": ctx.status,
            "intervention_memory": [
                {
                    "turn": r.turn,
                    "qa_history": {"student_q": r.qa_history.student_q, "system_a": r.qa_history.system_a},
                    "prompt_level": r.prompt_level,
                    "prompt_content": r.prompt_content,
                    "student_response": r.student_response,
                    "frontend_signal": r.frontend_signal,
                    "breakpoint_status": r.breakpoint_status
                }
                for r in ctx.intervention_memory
            ]
        }
        self._state_manager.set_module_state(
            ctx.session_id,
            "intervention",
            state
        )
```

### 7.4 干预状态机

```
                    ┌─────────────────────────────────────┐
                    │                                     │
    start ─────────▶│            active                   │
                    │                                     │
                    │  ┌─────────────────────────────────┐│
                    │  │ Node 1 → 2a → 2b → 3 → 4 → 5  ││
                    │  │         每轮干预循环              ││
                    │  └─────────────────────────────────┘│
                    │                                     │
                    │  frontend_signal == END           │
                    │         or                         │
                    │  student_response == accepted      │
                    │         or                         │
                    │  max_level_reached                 │
                    │         or                         │
                    │  switch_to_resource (M侧失败)       │
                    │                                     │
                    └──────────────┬──────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────────────┐
                    │                                      │
                    │  completed / terminated              │
                    │                                      │
                    └──────────────────────────────────────┘
```

**状态转换规则**：

| 当前状态 | 触发条件 | 下一状态 | 说明 |
|----------|----------|----------|------|
| active | 首次创建 | active | 新干预会话 |
| active | 正常反馈 | active | 继续循环 |
| active | END / accepted | completed | 学生主动结束或推进成功 |
| active | max_level_reached | terminated | AI干预达到极限 |
| active | M侧切换 | active | 切换维度，重新诊断 |
| terminated | - | - | 终态，不可恢复 |
| completed | - | - | 终态，不可恢复 |

### 7.5 上下文持久化

```python
# SessionState 中的干预状态结构
{
    "session_id": "sess_001",
    "problem_context": "设 a_0, a_1, ...",
    "current_diagnosis": {
        "dimension": "Resource",
        "sub_type": "R2",
        "confidence": 0.85,
        "reasoning": "学生有零散思路，但没有形成完整的解题图式"
    },
    "current_level": "R2",
    "status": "active",          # active / completed / terminated
    "intervention_memory": [
        {
            "turn": 1,
            "qa_history": {
                "student_q": "我不知道下一步怎么走",
                "system_a": "先看看题目里哪种结构最显眼"
            },
            "prompt_level": "R1",
            "prompt_content": "先看看题目里哪种结构最显眼",
            "student_response": "not_progressed",
            "frontend_signal": None,
            "breakpoint_status": "persistent",
            "created_at": "2024-01-01T10:00:00Z"
        },
        {
            "turn": 2,
            "qa_history": {
                "student_q": "还是不太明白",
                "system_a": "这一步需要的是一种换元法"
            },
            "prompt_level": "R2",
            "prompt_content": "这一步需要的是一种换元法",
            "student_response": "not_progressed",
            "frontend_signal": None,
            "breakpoint_status": "persistent",
            "created_at": "2024-01-01T10:01:00Z"
        }
    ],
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:01:00Z"
}
```

### 7.6 上下文恢复

```python
def restore_from_session(
    self,
    session_id: str,
    intervention_id: str  # 可选，用于多轮干预中恢复特定轮次
) -> Optional[InterventionContext]:
    """
    从 SessionState 恢复干预上下文。
    用于：学生刷新页面后恢复干预状态。
    """
    intervention_state = self._state_manager.get_module_state(session_id, "intervention")
    solving_state = self._state_manager.get_module_state(session_id, "solving")

    if not intervention_state or not solving_state:
        return None

    # 恢复 InterventionRecord 列表
    memory = [
        InterventionRecord(
            turn=r["turn"],
            qa_history=QaHistory(student_q=r["qa_history"]["student_q"], system_a=r["qa_history"]["system_a"]),
            prompt_level=r["prompt_level"],
            prompt_content=r["prompt_content"],
            student_response=r["student_response"],
            frontend_signal=r.get("frontend_signal"),
            breakpoint_status=r["breakpoint_status"]
        )
        for r in intervention_state["intervention_memory"]
    ]

    ctx = InterventionContext(
        session_id=session_id,
        student_id=intervention_state.get("student_id", ""),
        problem_context=solving_state["problem"],
        student_input="",  # 恢复时为空，等待新输入
        solution_steps=solving_state["solution_steps"],
        student_steps=solving_state.get("student_steps", []),
        breakpoint_location=None,
        dimension_result=None,
        sub_type_result=None,
        intervention_memory=memory,
        current_level=intervention_state.get("current_level", ""),
        status=intervention_state.get("status", "active")
    )

    return ctx
```

---

## 七、上下文压缩策略

### 7.7 问题描述

随着干预轮次增加，`intervention_memory` 会持续增长，`solution_steps` 和 `student_steps` 可能很长。这会导致：

1. **LLM 调用超出 token 限制**
2. **响应延迟增加**
3. **成本上升**

### 7.8 压缩策略

#### 策略 1：Node 精简输入（核心策略）

**各 Node 只接收必要的精简信息，不传完整历史：**

```python
class ContextManager:
    MAX_MEMORY_TURNS = 5   # 保留最近5轮
    MAX_STEPS_WINDOW = 3    # 断点前后各3步

    def prepare_llm_context(self, ctx: InterventionContext, node: str) -> dict:
        """为不同Node准备精简的上下文"""
        
        if node == "2a":
            # Node 2a：最精简，只需要当前状态，不需要 memory
            return {
                "session_id": ctx.session_id,
                "problem_context": ctx.problem_context,
                "student_input": ctx.student_input,
                "expected_step": (
                    ctx.breakpoint_location.expected_step_content 
                    if ctx.breakpoint_location else ""
                ),
                "breakpoint_type": (
                    ctx.breakpoint_location.breakpoint_type 
                    if ctx.breakpoint_location else ""
                ),
                # intervention_memory 不传
            }
        
        elif node == "2b":
            # Node 2b：需要最近2轮记忆摘要
            return {
                "session_id": ctx.session_id,
                "problem_context": ctx.problem_context,
                "dimension": (
                    ctx.dimension_result.dimension 
                    if ctx.dimension_result else ""
                ),
                "student_input": ctx.student_input,
                "expected_step": (
                    ctx.breakpoint_location.expected_step_content 
                    if ctx.breakpoint_location else ""
                ),
                "recent_memory": self._summarize_recent_memory(
                    ctx.intervention_memory, n=2
                ),
            }
        
        elif node == "4":
            # Node 4：只需要等级和方向，不需要 memory
            return {
                "session_id": ctx.session_id,
                "problem_context": ctx.problem_context,
                "sub_type": ctx.current_level,
                "hint_direction": (
                    ctx.sub_type_result.hint_direction 
                    if ctx.sub_type_result else ""
                ),
                "truncated_steps": self._truncate_steps(ctx),
            }
        
        elif node == "5":
            # Node 5：只需要内容和等级
            return {
                "content": "",  # 待检查的内容
                "sub_type": ctx.current_level,
            }
```

#### 策略 2：干预记忆截断

```python
def _summarize_recent_memory(
    self, 
    memory: List[InterventionRecord], 
    n: int = 2
) -> List[dict]:
    """
    提取最近n轮记忆的摘要，用于 LLM 调用。
    超过 MAX_MEMORY_TURNS 时，旧轮次压缩为摘要。
    """
    if len(memory) == 0:
        return []
    
    if len(memory) <= self.MAX_MEMORY_TURNS:
        # 未超过限制，返回最近 n 轮
        recent = memory[-n:]
        return [
            {
                "turn": r.turn,
                "prompt_level": r.prompt_level,
                "student_response": r.student_response,
                "reasoning": r.qa_history.student_q[:50] + "..." if len(r.qa_history.student_q) > 50 else r.qa_history.student_q
            }
            for r in recent
        ]
    
    # 超过限制：最近 n 轮 + 旧轮次摘要
    recent = memory[-n:]
    old_turns = memory[:-n]
    old_summary = self._summarize_old_turns(old_turns)
    
    return [
        *[
            {
                "turn": r.turn,
                "prompt_level": r.prompt_level,
                "student_response": r.student_response,
            }
            for r in recent
        ],
        {"type": "summary", "content": old_summary}
    ]

def _summarize_old_turns(self, old_turns: List[InterventionRecord]) -> str:
    """
    将旧轮次压缩为摘要。
    """
    if not old_turns:
        return ""
    
    levels = [r.prompt_level for r in old_turns]
    responses = [r.student_response for r in old_turns]
    
    summary = f"早期{n}轮尝试了{', '.join(set(levels))}，"
    
    if all(r == "not_progressed" for r in responses):
        summary += "均未推进。"
    elif any(r == "accepted" for r in responses):
        summary += "有推进。"
    else:
        summary += "结果混杂。"
    
    return summary
```

#### 策略 3：Steps 截断

```python
def _truncate_steps(self, ctx: InterventionContext, window: int = 3) -> dict:
    """
    只传断点前后各 window 步，减少 token 消耗。
    """
    if not ctx.breakpoint_location:
        # 无断点位置，返回全部（但限制长度）
        return {
            "solution_steps": ctx.solution_steps[:10],  # 最多10步
            "student_steps": ctx.student_steps[:10],
            "note": "无断点位置，限制为前10步"
        }
    
    pos = ctx.breakpoint_location.breakpoint_position
    total = len(ctx.solution_steps)
    
    start = max(0, pos - window)
    end = min(total, pos + window + 1)
    
    truncated_steps = ctx.solution_steps[start:end]
    
    return {
        "solution_steps": truncated_steps,
        "student_steps": ctx.student_steps[start:end] if ctx.student_steps else [],
        "breakpoint_position": pos,
        "window_start": start,
        "window_end": end,
        "note": f"显示第{start+1}到第{end}步，共{end-start}步"
    }
```

### 7.9 Token 预算控制

```python
# 各 Node 的 token 预算（原型阶段）
TOKEN_BUDGETS = {
    "2a": {
        "input": 2000,    # 最多 2000 tokens
        "output": 256,     # 输出简短分类结果
    },
    "2b": {
        "input": 3000,    # 包含最近2轮记忆
        "output": 512,     # 输出等级+决策
    },
    "4": {
        "input": 2500,    # 包含截断后的 steps
        "output": 1024,   # 提示内容可以较长
    },
    "5": {
        "input": 1000,    # 只需要内容和规则
        "output": 256,    # Yes/No + 理由
    }
}

def estimate_tokens(text: str) -> int:
    """估算 token 数（简单估算）"""
    chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
    other_chars = len(text) - chinese_chars
    return int(chinese_chars * 1.5 + other_chars * 0.25)

def check_budget(node: str, context: dict) -> bool:
    """检查是否超过 token 预算"""
    text = json.dumps(context, ensure_ascii=False)
    tokens = estimate_tokens(text)
    budget = TOKEN_BUDGETS.get(node, {}).get("input", 2000)
    return tokens <= budget
```

### 7.10 截断后的上下文示例

```python
# Node 2a 收到的精简上下文（约 500 tokens）
{
    "session_id": "sess_001",
    "problem_context": "设 $a_0, a_1, \ldots$ 是正整数序列...",
    "student_input": "",  # 空白提交
    "expected_step": "构造策略：采用递归构造...",
    "breakpoint_type": "MISSING_STEP",
    # intervention_memory 不传
}

# Node 2b 收到的精简上下文（约 800 tokens）
{
    "session_id": "sess_001",
    "problem_context": "设 $a_0, a_1, \ldots$ 是正整数序列...",
    "dimension": "Resource",
    "student_input": "",
    "expected_step": "构造策略：采用递归构造...",
    "recent_memory": [
        {"turn": 1, "prompt_level": "R1", "student_response": "not_progressed"},
        {"turn": 2, "prompt_level": "R2", "student_response": "not_progressed"},
        {"type": "summary", "content": "早期2轮尝试了R1,R2，均未推进。"}
    ]
}

# Node 4 收到的精简上下文（约 600 tokens）
{
    "session_id": "sess_001",
    "problem_context": "设 $a_0, a_1, \ldots$ 是正整数序列...",
    "sub_type": "R3",
    "hint_direction": "给出换元法的具体操作",
    "truncated_steps": {
        "solution_steps": [
            {"step_id": "s2", "step_name": "构造策略", "content": "采用递归构造..."},  # pos=1
            {"step_id": "s3", "step_name": "归纳证明", "content": "用数学归纳法..."}    # pos=2
        ],
        "breakpoint_position": 1,
        "note": "显示第2到第4步，共3步"
    }
}
```
```

### 7.2 SessionState 存储（复用现有 StateManager）

**Module 1 → Module 2 数据流**：

```python
# Module 1 存储（已实现）
# app/modules/solving/service.py:118
context.state_manager.set_module_state(session_id, "solving", {
    "problem": request.problem,
    "student_work": request.student_work or "",
    "student_steps": [...],    # List[TeachingStep]
    "solution_steps": [...],  # List[TeachingStep] - Module 2 需要读取这个
})

# Module 2 读取（待实现）
state = context.state_manager.get_module_state(session_id, "solving")
problem_context = state["problem"]
solution_steps = state["solution_steps"]  # List[dict]
```

**Module 2 自身状态存储**：

```python
# Module 2 存储干预状态
context.state_manager.set_module_state(session_id, "intervention", {
    "current_diagnosis": {...},
    "intervention_memory": [...],
    "status": "active",  # active / completed / terminated
})
```

### 7.3 TeachingStep 数据结构（复用 Module 1 的定义）

```python
# 来自 app/modules/solving/models.py
class TeachingStep(BaseModel):
    step_id: str    # "s1", "s2", "s3"...
    step_name: str
    content: str

# SessionState 中存储的是 dict 列表
solution_steps = [
    {"step_id": "s1", "step_name": "理解问题", "content": "..."},
    {"step_id": "s2", "step_name": "构造", "content": "..."},
]
```

---

## 八、技术实现

### 8.1 复用的现有代码

#### LLM Client

**文件**: `app/infrastructure/llm/dashscope_client.py`

```python
from app.infrastructure.llm.dashscope_client import DashScopeClient
from app.infrastructure.llm.base_client import Message

# 使用方式（与 SolvingService 相同）
llm_client = DashScopeClient(api_key=api_key, model="qwen-turbo")
response = await llm_client.chat(
    messages=[Message(role="user", content=prompt)],
    temperature=0.7,
    max_tokens=8192,
)
```

**关键方法**:
- `chat(messages, temperature, max_tokens)` → `str`: 同步 chat 接口
- `chat_stream(messages, ...)` → `AsyncIterator[str]`: 流式接口
- `get_embeddings(texts)` → `List[List[float]]`: 语义匹配用

**环境变量**:
- `DASHSCOPE_API_KEY`: API密钥
- `INTERVENTION_MODEL`: 模型名（默认 `qwen-turbo`）

#### StateManager（SessionState）

**文件**: `app/core/state/state_manager.py`

```python
# 存储 solving state（Module 1 已实现）
context.state_manager.set_module_state(session_id, "solving", {
    "problem": request.problem,
    "solution_steps": [...],
    "student_steps": [...],
})

# 读取 solving state（Module 2 需要实现）
state = context.state_manager.get_module_state(session_id, "solving")
```

#### IModule 基类

**文件**: `app/core/interfaces/module.py`

```python
from app.core.interfaces.module import IModule

class InterventionModule(IModule):
    module_id: str = "intervention"
    module_name: str = "Intervention Module"
    version: str = "1.0.0"
    dependencies: list = ["solving"]  # 依赖 Module 1

    async def initialize(self, context: ModuleContext) -> None:
        self._context = context

    async def shutdown(self) -> None:
        pass
```

#### ModuleContext

**文件**: `app/core/context.py`

```python
@dataclass
class ModuleContext:
    registry: Any           # 模块注册表
    orchestrator: Any        # LLM编排器
    state_manager: Any       # StateManager - 存储/读取SessionState
    session_manager: Any      # SessionManager
    event_bus: Any          # 事件总线
    config: Any             # 配置
    repository: Any          # 数据访问
    logger: Logger          # 日志
```

### 8.2 技术栈

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| LLM | qwen-turbo | DashScopeClient（已实现，复用） |
| 会话状态 | StateManager | app/core/state/state_manager.py（已实现，复用） |
| 模块基类 | IModule | app/core/interfaces/module.py（已实现，复用） |
| API框架 | FastAPI | HTTP接口 |
| 编排 | 纯Python | Node逻辑直接调用，不引入LangGraph |

### 8.4 API 接口（复用现有 FastAPI 模式）

**参考**：`app/modules/intervention/routes.py`（现有实现）、`app/modules/solving/routes.py`

#### POST /interventions

创建干预会话。

```python
# Request（简化版 - 基于现有实现）
{
    "student_id": str,                    # 学生ID
    "session_id": str,                    # 从 SessionState 读取 solving state
    "student_input": str,                 # 学生当前输入
    "frontend_signal": Optional[str]       # "ESCALATE" | null（END用 POST /end）
}

# Response
{
    "success": bool,
    "intervention": {
        "id": str,                        # 干预记录ID
        "content": str,                   # 提示内容
        "level": str,                     # R1 / R2 / R3 / R4 / M1-M5
        "dimension": str,                 # "Resource" | "Metacognitive"
        "status": str,                   # "active" | "terminated" | "completed"
        "message": str,                  # 状态消息
        "breakpoint_location": {         # 断点位置信息
            "position": int,
            "type": str,                 # MISSING_STEP / WRONG_DIRECTION / INCOMPLETE_STEP
            "expected_step": str
        }
    }
}
```

#### GET /interventions/{intervention_id}

获取干预会话详情。

#### POST /interventions/{intervention_id}/end

前端触发 END 信号，直接结束干预。

```python
# Request
{"reason": "我知道了"}  # 可选
```

#### POST /interventions/{intervention_id}/escalate

前端触发 ESCALATE 信号，强制升级。

```python
# Request
{"reason": "还是不懂"}  # 可选
```

#### POST /interventions/{intervention_id}/feedback

处理学生反馈（内部使用，Node 1 自动判断）。

```python
# Request
{
    "student_input": str,                 # 学生提交的新内容
    "frontend_signal": Optional[str]       # "ESCALATE" | null
}

# Response（同 POST /interventions）
```

### 8.3 核心函数接口

**复用模式参考**：
- LLM 调用：`app/modules/solving/service.py:41-53`（lazy初始化）+ `service.py:100-105`（chat调用）
- 读取 SessionState：`app/modules/intervention/service.py:46`（get_module_state）
- 写入 SessionState：`app/modules/solving/service.py:118`（set_module_state）
- Prompt 构建：`app/modules/solving/prompts/director.py`（字符串模板组合）

```python
# ============================================================
# 核心服务类
# ============================================================

class InterventionService:
    """干预服务主类"""

    def __init__(self, context: Optional["ModuleContext"] = None):
        self._context = context
        self._llm_client: Optional[DashScopeClient] = None
        self._locator: Optional[BreakpointLocator] = None

    def _get_llm_client(self) -> DashScopeClient:
        """复用 solving/service.py 的 lazy 初始化模式"""
        if self._llm_client is None:
            api_key = os.getenv("DASHSCOPE_API_KEY")
            model = os.getenv("INTERVENTION_MODEL", "qwen-turbo")
            self._llm_client = DashScopeClient(api_key=api_key, model=model)
        return self._llm_client

    async def create_intervention(
        self,
        session_id: str,
        student_id: str,
        student_input: str,
        frontend_signal: Optional[str] = None
    ) -> Intervention:
        """
        创建干预会话。
        1. 从 SessionState 读取 solution_steps 和 problem_context
        2. 调用干预流程：Node 1 → 2a → 2b → 3 → 4 → 5
        3. 返回提示内容
        """
        # Step 1: 读取 SessionState
        state = self._context.state_manager.get_module_state(session_id, "solving")
        problem_context = state["problem"]
        solution_steps = state["solution_steps"]  # List[dict]

        # Step 2: Node 1 - 断点定位
        locator = BreakpointLocator()
        location = locator.locate(student_input, solution_steps)

        # Step 3: Node 2a - 维度分流
        router = DimensionRouter(self._get_llm_client())
        dimension_result = await router.route(
            student_input=student_input,
            expected_step=location.expected_step_content,
            breakpoint_type=location.breakpoint_type,
            intervention_memory=self._get_intervention_memory(session_id)
        )

        # Step 4: Node 2b - 等级决策
        decider = SubTypeDecider(self._get_llm_client())
        sub_type_result = await decider.decide(
            dimension=dimension_result.dimension,
            student_input=student_input,
            expected_step=location.expected_step_content,
            intervention_memory=self._get_intervention_memory(session_id),
            frontend_signal=frontend_signal
        )

        # Step 5: Node 4 - 提示生成
        generator = PromptGenerator(self._get_llm_client())
        content = await generator.generate(
            sub_type=sub_type_result.sub_type,
            hint_direction=sub_type_result.hint_direction,
            problem_context=problem_context,
            expected_step=location.expected_step_content
        )

        # Step 6: Node 5 - 输出审查
        guardrail = OutputGuardrail(self._get_llm_client())
        check_result = await guardrail.check(content, sub_type_result.sub_type)

        # 处理越界
        if not check_result.pass:
            content = check_result.revised_content

        # 存储干预状态
        self._save_intervention_state(session_id, {...})

        return Intervention(content=content, level=sub_type_result.sub_type, ...)

    def _get_intervention_memory(self, session_id: str) -> List[InterventionRecord]:
        """从 SessionState 读取干预记忆"""
        state = self._context.state_manager.get_module_state(session_id, "intervention")
        return state.get("intervention_memory", [])

    def _save_intervention_state(self, session_id: str, state: dict):
        """写入干预状态到 SessionState"""
        self._context.state_manager.set_module_state(session_id, "intervention", state)


# ============================================================
# Node 实现
# ============================================================

class BreakpointLocator:
    """Node 1: 断点定位（纯逻辑，无 LLM 调用）"""

    def locate(
        self,
        student_input: str,
        solution_steps: List[dict]  # List[TeachingStep as dict]
    ) -> BreakpointLocation:
        """
        比较学生输入与参考解法步骤，定位断点。
        使用三级语义匹配（breaker.py 已实现）。
        """
        # 复用现有 app/modules/intervention/locator/breaker.py
        pass


class DimensionRouter:
    """Node 2a: 维度分流（LLM 调用）"""

    def __init__(self, llm_client: DashScopeClient):
        self._llm_client = llm_client

    async def route(
        self,
        student_input: str,
        expected_step: str,
        breakpoint_type: str,
        intervention_memory: List[InterventionRecord]
    ) -> DimensionResult:
        """判断 Resource 或 Metacognitive"""
        # 复用 solving/service.py 的 LLM 调用模式
        prompt = self._build_prompt(student_input, expected_step, breakpoint_type, intervention_memory)
        response = await self._llm_client.chat(
            messages=[Message(role="user", content=prompt)],
            temperature=0.7,
            max_tokens=1024,
        )
        return self._parse_response(response)


class SubTypeDecider:
    """Node 2b: 等级决策 + 升级策略（LLM 调用）"""

    def __init__(self, llm_client: DashScopeClient):
        self._llm_client = llm_client

    async def decide(
        self,
        dimension: str,
        student_input: str,
        expected_step: str,
        intervention_memory: List[InterventionRecord],
        frontend_signal: Optional[str]
    ) -> SubTypeResult:
        """决定 R1-R4 或 M1-M5 + 升级策略"""
        pass


class PromptGenerator:
    """Node 4: 提示生成（LLM 调用）"""

    def __init__(self, llm_client: DashScopeClient):
        self._llm_client = llm_client

    async def generate(
        self,
        sub_type: str,
        hint_direction: str,
        problem_context: str,
        expected_step: str
    ) -> str:
        """根据等级生成提示内容"""
        pass


class OutputGuardrail:
    """Node 5: 输出审查（LLM 调用）"""

    def __init__(self, llm_client: DashScopeClient):
        self._llm_client = llm_client

    async def check(
        self,
        content: str,
        sub_type: str
    ) -> GuardrailResult:
        """LLM-as-a-Judge 检查提示是否越界"""
        pass
```

---

## 九、Module 1 → Module 2 接口

### 9.1 职责边界

```
Module 1（Solving）：
  → 只生成 solution_steps，存入 SessionState
  → 生成后工作结束

Module 2（Intervention）：
  → 从 SessionState 读取 solution_steps
  → 接管后续所有干预流程
  → 独立运行干预循环
```

### 9.2 数据流

```
POST /solving/reference (Module 1)
    │
    ▼
ReferenceSolutionService.generate(request, session_id="sess_001")
    │
    ├─→ 存储到 SessionState:
    │     context.state_manager.set_module_state("sess_001", "solving", {
    │         "problem": ...,
    │         "student_work": ...,
    │         "student_steps": [...],
    │         "solution_steps": [...],  # Module 2 需要读取这个
    │     })
    │
    └─→ 返回 SolvingResponse

POST /interventions (Module 2)
    │
    ▼
InterventionService.create_intervention(session_id="sess_001", ...)
    │
    └─→ 读取 SessionState:
          context.state_manager.get_module_state("sess_001", "solving")
          → problem_context, solution_steps, student_steps
```

### 9.3 具体读取代码

```python
# Module 2 读取 Module 1 的数据
state = context.state_manager.get_module_state(session_id, "solving")

problem_context = state["problem"]                    # str
student_work = state.get("student_work", "")         # str
student_steps = state.get("student_steps", [])       # List[dict]
solution_steps = state.get("solution_steps", [])     # List[dict] - TeachingStep格式
```

**TeachingStep 格式**（来自 `app/modules/solving/models.py`）：
```python
{
    "step_id": "s1",           # 步骤ID
    "step_name": "理解问题",    # 步骤名称
    "content": "..."            # 步骤内容
}
```

---

## 十、Prompt 模板

### 10.1 Node 2a Prompt

```
你是一位数学解题教育专家。

你的任务是根据以下信息，判断学生当前的解题困难属于哪个维度。

## 输入信息

题目上下文：
{problem_context}

参考解法的期望步骤（学生应该做的下一步）：
{expected_step_content}

学生当前提交的步骤：
{student_current_input}

断点类型（来自断点定位模块）：
{breakpoint_type}
- MISSING_STEP：学生缺少这一步
- WRONG_DIRECTION：学生方向偏离参考解法
- INCOMPLETE_STEP：学生这一步不完整
- STUCK：学生完全卡住，无法继续

历史干预记录（近3轮）：
{intervention_memory_summary}

## 困难维度定义

**Resource（资源侧）**：
"下一步能不能出现"——学生是否形成了可用的候选路径。
- 空白提交，完全不知道下一步怎么走
- 有思路，但依赖的知识/图式本身错误或缺失
- 方向完全错误（WRONG_DIRECTION）——没有形成正确的候选路径

**Metacognitive（元认知侧）**：
"当前路径怎么管"——候选图式已经出现，路径已经激活后，如何管理和推进。
- 方向看起来对，但不知道下一步怎么展开
- 能看到目标，但看不清当前路径是否仍有效
- 局部卡住，不确定该继续坚持还是换路

## 输出格式（JSON）

{
  "dimension": "Resource" | "Metacognitive",
  "confidence": 0.0-1.0,
  "reasoning": "判断理由，3-5句话"
}
```

### 10.2 Node 2b Prompt（Resource 维度）

```
你是一位数学解题教育专家。

Node 2a 已判断学生困难为 **Resource（资源侧）**。
你的任务是：
1. 确定最合适的干预等级（R1-R4）
2. 参考历史干预记录，自主决定是否需要升级/降级/切换维度

## 干预等级定义

**R1 线索唤醒型**（强度最低）：
- 学生完全没有思路，不知道从哪下手
- 提示目标：只点触发线索，不提及具体方法名或公式
- 典型形式："先看看题目里哪种结构最显眼"

**R2 图式定向型**：
- 学生有零散思路，但没有形成完整的解题图式
- 提示目标：给出高阶图式路标，但不替学生展开计算
- 典型形式："这一步需要的是一种'换元法'"

**R3 资源显化型**：
- 学生有解题方向，但关键知识或定理调用缺失
- 提示目标：直接补出关键知识、定理或典型出口状态
- 典型形式："换元法：设 t = x+1，把分母统一成 t²"

**R4 半展开示范型**（强度最高）：
- 学生有方向但完全无法推进，资源断裂明显
- 提示目标：直接给出关键第一小步或半成品结构
- 典型形式："第一步：设 t = x+1，整理得 t²-3t+2=0"

## 升级/切换决策指南

- student_response == "still_stuck" → 考虑升级
- student_response == "accepted" → 考虑维持当前等级
- frontend_signal == "ESCALATE" → 强制升级
- frontend_signal == "END" → 终止
- 连续升级仍无效 → switch_to_resource（切到M侧）

## 输出格式（JSON）

{
  "sub_type": "R1" | "R2" | "R3" | "R4",
  "confidence": 0.0-1.0,
  "reasoning": "为什么选这个等级，2-3句话",
  "hint_direction": "生成提示时应遵循的方向，1-2句话",
  "escalation_decision": {
    "action": "maintain" | "escalate" | "switch_dimension",
    "from_level": "当前等级",
    "to_level": "目标等级",
    "reasoning": "升级/维持/切换的理由"
  }
}
```

### 10.3 Node 2b Prompt（Metacognitive 维度）

```
你是一位数学解题教育专家。

Node 2a 已判断学生困难为 **Metacognitive（元认知侧）**。
你的任务是：
1. 确定最合适的干预等级（M1-M5）
2. 参考历史干预记录，自主决定是否需要升级

## 干预等级定义

**M1 路径判定支持型**：
- 核心问题：这条路的"前景"如何？还值得走吗？
- 典型形式："再做两步会得到什么？"

**M2 路径维持与稳住型**：
- 核心问题：这条路的"局部"卡住了，别放弃
- 典型形式："这条路还在产生有效信息"

**M3 路径推进定向型**：
- 核心问题：既然对，第一小步是什么？
- 典型形式："先找最关键的落脚点"

**M4 路径修正与切换型**：
- 核心问题：这条路不行了，该停了
- 典型形式："先停，不要继续堆步骤"

**M5 路径切换后的重建型**：
- 核心问题：路换了，从哪起步？
- 典型形式："哪个候选更可能生成果"

## 升级指南

- M3失败后，LLM判断给更详细的M3+还是切换到M4
- M3+：学生方向对，但缺乏具体细节
- M4：只有当学生路径确实发生变化（断点切换）时才触发
- M5失败 → switch_to_resource

## 输出格式（JSON）

{
  "sub_type": "M1" | "M2" | "M3" | "M4" | "M5",
  "confidence": 0.0-1.0,
  "reasoning": "为什么选这个等级",
  "hint_direction": "生成提示时应遵循的方向",
  "escalation_decision": {
    "action": "maintain" | "escalate" | "switch_to_resource",
    "from_level": "当前等级",
    "to_level": "目标等级",
    "reasoning": "决策理由"
  }
}
```

---

## 十一、R1-R4 显化边界规则

### 11.1 Node 5 Guardrail 规则

```python
RULES = {
    "R1": {
        "forbidden": [
            "具体方法名称（如换元法、配方法）",
            "具体公式",
            "具体数值或变量赋值",
            "计算过程"
        ],
        "allowed": [
            "方向性描述",
            "结构观察提示",
            "关系类比提示"
        ]
    },
    "R2": {
        "forbidden": [
            "完整计算过程",
            "最终答案",
            "具体数值结果"
        ],
        "allowed": [
            "方法名称（图式名）",
            "高阶方向（统一变量、观察结构）",
            "但不展开这个方法具体怎么用"
        ]
    },
    "R3": {
        "forbidden": [
            "完整解题步骤",
            "最终答案"
        ],
        "allowed": [
            "关键定理名称",
            "中间状态描述",
            "知识清单"
        ]
    },
    "R4": {
        "forbidden": [
            "完整全程解法"
        ],
        "allowed": [
            "第一小步的完整写法",
            "半成品结构",
            "关键中间台阶"
        ]
    }
}
```

---

## 十二、部署说明

### 12.1 环境变量

```bash
# 必需
DASHSCOPE_API_KEY=           # 阿里云 DashScope API Key

# 可选
INTERVENTION_MODEL=          # 干预模型，默认 qwen-turbo（原型阶段）
MONGODB_URI=               # MongoDB URI（未来持久化用）
```

### 12.2 快速开始

```bash
cd backend

# 安装依赖
pip install -e ".[dev]"

# 运行服务
uvicorn app.main:app --reload
```

### 12.3 测试

```bash
# 干预模块单元测试
python -m pytest tests/modules/test_intervention/ -v

# 集成测试（Module 1 + Module 2）
python -m pytest tests/modules/test_integration/ -v

# 完整测试套件
python -m pytest tests/ -v --ignore=tests/e2e
```

### 12.4 目录结构

```
app/modules/intervention/
├── __init__.py
├── module.py                 # InterventionModule（IModule实现）
├── service.py               # InterventionService（主入口）
├── routes.py                # FastAPI 路由
├── models.py                # 数据模型
│
├── locator/                 # Node 1: 断点定位（纯逻辑）
│   ├── breaker.py           # BreakpointLocator（已实现）
│   └── models.py
│
├── router/                  # Node 2a: 维度分流（LLM）
│   ├── dimension_router.py
│   └── prompts.py           # Node 2a Prompt 模板
│
├── decider/                 # Node 2b: 等级决策（LLM）
│   ├── sub_type_decider.py
│   └── prompts.py           # Node 2b Prompt 模板
│
├── generator/               # Node 4: 提示生成（LLM，已实现部分）
│   ├── generator.py
│   └── prompts.py           # R1-R4 / M1-M5 提示模板
│
└── guardrail/             # Node 5: 输出审查（LLM）
    ├── guardrail.py
    └── prompts.py           # Guardrail Prompt 模板

tests/modules/test_intervention/
├── __init__.py
├── conftest.py              # pytest fixtures
├── test_locator.py          # Node 1 单元测试
├── test_router.py           # Node 2a 单元测试
├── test_decider.py          # Node 2b 单元测试
├── test_generator.py         # Node 4 单元测试
├── test_guardrail.py        # Node 5 单元测试
├── test_service.py          # IntegrationService 集成测试
├── test_e2e_locator.py     # Node 1 E2E（4种断点类型 × 3种难度）
├── test_e2e_router.py       # Node 2a E2E（R/M分类准确率）
├── test_e2e_decider.py      # Node 2b E2E（升级/切换决策）
├── test_e2e_guardrail.py    # Node 5 E2E（边界检查）
└── test_e2e_full_flow.py   # 完整流程 E2E（所有Node串联）
```

---

## 十三、E2E 测试设计

每个Node和完整流程都需要E2E测试覆盖。

### 13.1 测试数据

**测试题目库**（至少5道，覆盖不同数学主题）：

```python
TEST_PROBLEMS = [
    {
        "id": "prob_001",
        "topic": "数列递推",
        "problem": "设 $a_0, a_1, \ldots$ 是正整数序列，证明可以选择序列使得每个非零自然数恰好等于 $a_0, b_0, a_1, b_1, \ldots$ 中的一项。",
        "solution_steps": [
            {"step_id": "s1", "step_name": "理解问题", "content": "理解题目要求：每个非零自然数都能在序列中找到对应项。"},
            {"step_id": "s2", "step_name": "构造策略", "content": "采用递归构造：先确定a_0，再确定b_0，不断递归生成。"},
            {"step_id": "s3", "step_name": "归纳证明", "content": "用数学归纳法证明：假设前n项已构造完毕，构造第n+1项。"},
            {"step_id": "s4", "step_name": "验证完整性", "content": "验证所有非零自然数都能被覆盖。"}
        ]
    },
    {
        "id": "prob_002", 
        "topic": "函数方程",
        "problem": "求所有满足 $f(x+y) = f(x) + f(y) + 2xy$ 的函数 $f: \mathbb{R} \to \mathbb{R}$。",
        "solution_steps": [...]
    },
    # 至少5道题
]
```

**学生行为模拟数据**（每个题目4种断点类型）：

```python
# 每个题目的4种断点场景
BREAKPOINT_SCENARIOS = {
    "MISSING_STEP": {
        "student_input": "",  # 空白提交
        "expected_step": "s2",
        "dimension": "Resource"
    },
    "WRONG_DIRECTION": {
        "student_input": "用配方法试试...",  # 方向错误
        "expected_step": "s2",
        "dimension": "Resource"
    },
    "INCOMPLETE_STEP": {
        "student_input": "令 g(x) = f(x) - x^2，",  # 方向对但展开不完整
        "expected_step": "s2",
        "dimension": "Metacognitive"
    },
    "STUCK": {
        "student_input": "我不知道从哪里开始",  # 完全无思路
        "expected_step": "s1",
        "dimension": "Resource"
    }
}
```

### 13.2 Node 1 E2E（断点定位）

**测试目标**：验证三级语义匹配在不同断点类型上的准确率

```python
# tests/modules/test_intervention/test_e2e_locator.py

@pytest.mark.parametrize("problem", TEST_PROBLEMS)
@pytest.mark.parametrize("scenario", list(BREAKPOINT_SCENARIOS.values())
def test_locator_identifies_breakpoint_type(problem, scenario):
    """
    给定题目 + 学生输入，验证断点定位结果正确。
    
    期望：Node 1 输出与 scenario["expected_breakpoint_type"] 一致
    """
    locator = BreakpointLocator()
    result = locator.locate(
        student_input=scenario["student_input"],
        solution_steps=problem["solution_steps"]
    )
    
    assert result.breakpoint_type == scenario["expected_breakpoint_type"]

@pytest.mark.parametrize("problem", TEST_PROBLEMS)
@pytest.mark.parametrize("scenario", list(BREAKPOINT_SCENARIOS.values())
def test_locator_semantic_matching_accuracy(problem, scenario):
    """
    验证语义匹配的准确性：expected_step_content 提取正确。
    """
    locator = BreakpointLocator()
    result = locator.locate(
        student_input=scenario["student_input"],
        solution_steps=problem["solution_steps"]
    )
    
    assert result.expected_step_content is not None
    assert len(result.expected_step_content) > 0
```

**验收标准**：
- 准确率 ≥ 90%（4种断点类型 × 5道题 = 20个case，至少18个通过）
- 误判率（WRONG → MISSING）< 10%

### 13.3 Node 2a E2E（维度分流）

**测试目标**：验证 R/M 二元分类与专家标注一致率

```python
# tests/modules/test_intervention/test_e2e_router.py

@pytest.mark.parametrize("problem", TEST_PROBLEMS)
@pytest.mark.parametrize("scenario", list(BREAKPOINT_SCENARIOS.values())
async def test_router_dimension_classification(problem, scenario):
    """
    给定题目 + 学生输入 + 断点类型，验证维度分流正确。
    
    期望：Node 2a 输出与 scenario["dimension"] 一致
    """
    router = DimensionRouter(llm_client)
    
    result = await router.route(
        student_input=scenario["student_input"],
        expected_step=scenario["expected_step_content"],
        breakpoint_type=scenario["breakpoint_type"],
        intervention_memory=[]
    )
    
    assert result.dimension == scenario["dimension"]
    assert result.confidence >= 0.7
```

**验收标准**：
- Resource/Metacognitive 分类准确率 ≥ 85%
- 专家标注对照：邀请3位专家独立标注，计算Kappa一致性 ≥ 0.65

### 13.4 Node 2b E2E（等级决策 + 升级）

**测试目标**：验证等级选择和升级/切换决策符合规则

```python
# tests/modules/test_intervention/test_e2e_decider.py

async def test_decider_choices_r_for_resource_dimension():
    """Resource维度 → 应该选择R1-R4"""
    decider = SubTypeDecider(llm_client)
    
    result = await decider.decide(
        dimension="Resource",
        student_input="",
        expected_step="...",
        intervention_memory=[],
        frontend_signal=None
    )
    
    assert result.sub_type in ["R1", "R2", "R3", "R4"]

async def test_decider_choices_m_for_metacognitive_dimension():
    """Metacognitive维度 → 应该选择M1-M5"""
    decider = SubTypeDecider(llm_client)
    
    result = await decider.decide(
        dimension="Metacognitive", 
        student_input="方向对但不知道怎么展开",
        expected_step="...",
        intervention_memory=[],
        frontend_signal=None
    )
    
    assert result.sub_type in ["M1", "M2", "M3", "M4", "M5"]

async def test_frontend_escalate_triggers_upgrade():
    """前端 ESCALATE → 应该升级"""
    decider = SubTypeDecider(llm_client)
    
    result = await decider.decide(
        dimension="Resource",
        student_input="",
        expected_step="...",
        intervention_memory=[{
            "turn": 1,
            "prompt_level": "R1",
            "student_response": "not_progressed"
        }],
        frontend_signal="ESCALATE"
    )
    
    # 应该升级到 R2
    assert result.escalation_decision.action == "escalate"

async def test_r4_max_level_terminates():
    """R4 + still_stuck → 终止"""
    decider = SubTypeDecider(llm_client)
    
    result = await decider.decide(
        dimension="Resource",
        student_input="",
        expected_step="...",
        intervention_memory=[{
            "turn": 4,
            "prompt_level": "R4",
            "student_response": "not_progressed"
        }],
        frontend_signal=None
    )
    
    assert result.escalation_decision.action == "max_level_reached"
    assert "不能直接给你答案" in result.escalation_decision.system_response
```

### 13.5 Node 4 E2E（提示生成 + 显化边界）

**测试目标**：验证生成的提示符合R1-R4/M1-M5的显化边界

```python
# tests/modules/test_intervention/test_e2e_generator.py

async def test_r1_hint_no_method_name():
    """R1提示：不应包含具体方法名"""
    generator = PromptGenerator(llm_client)
    
    content = await generator.generate(
        sub_type="R1",
        hint_direction="引导学生观察题目结构",
        problem_context="...",
        expected_step="..."
    )
    
    # R1不应出现方法名
    forbidden_words = ["换元法", "配方法", "因式分解", "求根公式"]
    for word in forbidden_words:
        assert word not in content

async def test_r2_hint_gives_method_not_calculation():
    """R2提示：给方法名，不给具体计算"""
    generator = PromptGenerator(llm_client)
    
    content = await generator.generate(
        sub_type="R2",
        hint_direction="提示使用换元法",
        problem_context="...",
        expected_step="..."
    )
    
    assert "换元" in content
    # 但不应有具体赋值
    assert "t =" not in content or "设" not in content

async def test_r3_hint_gives_knowledge_not_full_solution():
    """R3提示：给定理/知识，不给完整解法"""
    generator = PromptGenerator(llm_client)
    
    content = await generator.generate(
        sub_type="R3",
        hint_direction="给出换元法的具体操作",
        problem_context="...",
        expected_step="..."
    )
    
    # 应该有具体定理/方法描述
    assert "换元法" in content and ("设" in content or "令" in content)
    # 但不应有完整解题步骤
    assert content.count("\n") < 5  # 不超过5行

async def test_r4_hint_gives_first_step():
    """R4提示：给出第一小步"""
    generator = PromptGenerator(llm_client)
    
    content = await generator.generate(
        sub_type="R4",
        hint_direction="给出完整的第一小步",
        problem_context="...",
        expected_step="..."
    )
    
    # 应该有具体第一步
    assert "第一步" in content or "先" in content
```

### 13.6 Node 5 E2E（Guardrail边界检查）

**测试目标**：验证越界提示被正确拦截

```python
# tests/modules/test_intervention/test_e2e_guardrail.py

async def test_guardrail_blocks_r1_with_formula():
    """R1提示如果包含公式 → 应被拦截"""
    guardrail = OutputGuardrail(llm_client)
    
    bad_content = "这道题用换元法，具体是设 t = x+1，然后代入原式得到..."
    
    result = await guardrail.check(bad_content, sub_type="R1")
    
    assert result.pass == False
    assert "formula" in result.reason.lower()

async def test_guardrail_allows_valid_r1():
    """有效R1提示 → 应通过"""
    guardrail = OutputGuardrail(llm_client)
    
    valid_content = "先看看题目里有没有什么特殊结构，比如对称性或者重复出现的模式。"
    
    result = await guardrail.check(valid_content, sub_type="R1")
    
    assert result.pass == True

@pytest.mark.parametrize("level", ["R1", "R2", "R3", "R4"])
async def test_guardrail_handles_all_r_levels(level):
    """所有R等级都应该被检查"""
    guardrail = OutputGuardrail(llm_client)
    
    content = f"测试提示内容（level={level}）"
    result = await guardrail.check(content, sub_type=level)
    
    assert hasattr(result, "pass")
    assert hasattr(result, "reason")
```

### 13.7 完整流程 E2E

**测试目标**：验证 Module 1 → Module 2 完整流程

```python
# tests/modules/test_intervention/test_e2e_full_flow.py

async def test_full_flow_missing_step_to_r1_hint():
    """完整流程：空白提交 → R1提示"""
    # 1. Module 1 生成 solution_steps
    solving_response = await solving_service.generate(
        SolvingRequest(problem=TEST_PROBLEMS[0]["problem"]),
        session_id="test_session"
    )
    assert solving_response.success
    
    # 2. Module 2 处理空白输入
    intervention = await intervention_service.create_intervention(
        session_id="test_session",
        student_id="student_001",
        student_input="",  # 空白
        frontend_signal=None
    )
    
    # 3. 验证输出
    assert intervention.level in ["R1", "R2", "R3", "R4"]
    assert intervention.dimension == "Resource"
    assert intervention.status == "active"

async def test_full_flow_upgrade_r1_to_r2():
    """完整流程：R1后仍然卡住 → 升级到R2"""
    # 1. 创建干预，获取R1提示
    intervention_1 = await intervention_service.create_intervention(...)
    
    # 2. 学生仍然卡住，反馈
    intervention_2 = await intervention_service.process_feedback(
        intervention_id=intervention_1.id,
        student_input="",  # 仍然空白
        frontend_signal=None
    )
    
    # 3. 验证升级
    assert intervention_2.level in ["R2", "R3", "R4"]
    assert intervention_2.intervention_memory[0].prompt_level == "R1"

async def test_full_flow_r4_terminates():
    """完整流程：R4后仍然卡住 → 终止"""
    # 连续4次反馈都是 not_progressed
    
    intervention = intervention_1
    for i in range(4):
        intervention = await intervention_service.process_feedback(
            intervention_id=intervention.id,
            student_input="仍然不对",
            frontend_signal=None
        )
    
    # 最后应该终止
    assert intervention.status == "terminated"
    assert "不能直接给你答案" in intervention.content

async def test_full_flow_m5_switches_to_r():
    """完整流程：M5失败 → 切换到R"""
    # ... 先触发到 M5 ...
    
    intervention = await intervention_service.process_feedback(
        intervention_id=intervention.id,
        student_input="我知道要换路但不知道怎么换",
        frontend_signal=None
    )
    
    # 应该切换到R侧
    assert intervention.dimension == "Resource"
    assert intervention.level in ["R1", "R2", "R3", "R4"]

async def test_full_flow_frontend_end():
    """完整流程：前端 END → 直接终止"""
    intervention = await intervention_service.create_intervention(...)
    
    ended = await intervention_service.end_intervention(
        intervention_id=intervention.id,
        reason="我知道了"
    )
    
    assert ended.status == "completed"
    assert "不能直接给你答案" not in ended.content

async def test_full_flow_frontend_escalate():
    """完整流程：前端 ESCALATE → 强制升级"""
    intervention = await intervention_service.create_intervention(...)
    
    escalated = await intervention_service.escalate_intervention(
        intervention_id=intervention.id,
        reason="还是不懂"
    )
    
    # 应该升级
    assert escalated.level != intervention.level
```

### 13.8 E2E 测试执行命令

```bash
# Node 1 E2E（断点定位）
pytest tests/modules/test_intervention/test_e2e_locator.py -v

# Node 2a E2E（维度分流）
pytest tests/modules/test_intervention/test_e2e_router.py -v

# Node 2b E2E（等级决策）
pytest tests/modules/test_intervention/test_e2e_decider.py -v

# Node 4 E2E（提示生成）
pytest tests/modules/test_intervention/test_e2e_generator.py -v

# Node 5 E2E（Guardrail）
pytest tests/modules/test_intervention/test_e2e_guardrail.py -v

# 完整流程 E2E
pytest tests/modules/test_intervention/test_e2e_full_flow.py -v

# 所有E2E测试
pytest tests/modules/test_intervention/test_e2e_*.py -v
```

### 13.9 E2E 测试验收标准

| 测试项 | 验收标准 |
|--------|----------|
| Node 1 E2E（断点定位） | 准确率 ≥ 90%（20个case） |
| Node 2a E2E（维度分流） | 分类准确率 ≥ 85%，专家Kappa ≥ 0.65 |
| Node 2b E2E（等级决策） | 升级/切换决策正确率 ≥ 90% |
| Node 4 E2E（提示生成） | 显化边界符合率 ≥ 90% |
| Node 5 E2E（Guardrail） | 越界拦截率 = 100%，有效提示通过率 ≥ 95% |
| 完整流程 E2E | 端到端成功率 ≥ 95% |
