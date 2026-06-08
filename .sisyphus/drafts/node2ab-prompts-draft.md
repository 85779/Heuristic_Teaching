# Node 2a & Node 2b Prompt 设计文档 v2

> 两阶段分流架构：Node 2a 做 R/M 二元分流，Node 2b 决定具体等级 + 升级策略（LLM自主决定）

---

## 整体数据流

```
Node 1: BreakpointLocator
输出: {breakpoint_type, expected_step, gap_description}

         ↓

Node 2a: Dimension Router
输入: student_input, expected_step, breakpoint_type, intervention_memory
输出: {dimension, confidence, reasoning}

         ↓

Node 2b: Sub-type Decider + Escalation Manager
输入: dimension, student_input, expected_step, intervention_memory
      （intervention_memory = [{qa_history, prompt_level, prompt_content}, ...]）
输出: {sub_type, confidence, reasoning, hint_direction, escalation_decision}

escalation_decision: {
  "action": "maintain" | "escalate" | "switch_dimension",
  "from_level": "R1",
  "to_level": "R2",
  "reasoning": "..."
}

         ↓

Node 3: Strategy Controller（纯代码执行，不做决策）
根据 Node 2b 的 escalation_decision，执行对应的升级/降级/切换操作
```

---

## Node 2a: Dimension Router

### 职责
R/M 二元分流。只输出 dimension，不输出升级信号。

### 输入
| 字段 | 来源 | 说明 |
|------|------|------|
| `student_input` | Global State | 学生当前提交的步骤 |
| `expected_step` | Node 1 | 期望的下一步 |
| `breakpoint_type` | Node 1 | MISSING_STEP / WRONG_DIRECTION / INCOMPLETE_STEP / STUCK |
| `intervention_memory` | Global State | 历史记录（问答+层级+内容） |

### Prompt v2

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
每条记录包含：学生问答摘要、系统提示层级、提示内容。

如果为空，说明这是首次干预。

## 困难维度定义

**Resource（资源侧）**：
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

**Metacognitive（元认知侧）**：
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

**连接点：图式**
- Resource → 提供"有什么可走、为什么会出现"
- Metacognitive → 对已激活路径"如何判定、推进与修正"
- 两者在同一个"下一步"上形成前后衔接，不是平行关系

## 输出格式（JSON）

{
  "dimension": "Resource" | "Metacognitive",
  "confidence": 0.0-1.0,
  "reasoning": "判断理由，3-5句话"
}
```

---

## Node 2b: Sub-type Decider + Escalation Manager

### 职责
1. 根据 dimension，决定具体 sub_type（R1-R4 或 M1-M5）
2. 参考 intervention_memory，自主决定是否需要升级/降级/切换维度
3. 输出升级决策（escalation_decision）

### 升级策略（LLM自主决定，不是写死的规则）

LLM 可以根据 memory 中的信息自主决定：
- **维持 (maintain)**：当前等级有效，继续用
- **升级 (escalate)**：同维度内升级（R1→R2→R3→R4，或 M1→M2→...）
- **切换维度 (switch_dimension)**：从 Resource 切 Metacognitive，或反之

### 输入
| 字段 | 来源 | 说明 |
|------|------|------|
| `dimension` | Node 2a | Resource 或 Metacognitive |
| `student_input` | Global State | 学生当前提交的步骤 |
| `expected_step` | Node 1 | 期望的下一步 |
| `problem_context` | Global State | 题目上下文 |
| `intervention_memory` | Global State | 完整历史记录 |

`intervention_memory` 数据结构：
```python
{
    "turn": 1,
    "qa_history": {
        "student_q": "学生问：...",
        "system_a": "系统答：..."
    },
    "prompt_level": "R1" | "R2" | "R3" | "R4" | "M1" | "M2" | "M3" | "M4" | "M5",
    "prompt_content": "提示的具体内容...",
    "student_response": "accepted" | "rejected" | "still_stuck"
}
```

### Prompt v2（Dimension == Resource 时）

```
你是一位数学解题教育专家。

Node 2a 已判断学生困难为 **Resource（资源侧）**。
你的任务是：
1. 确定最合适的干预等级（R1-R4）
2. 参考历史干预记录，自主决定是否需要升级/降级/切换维度

## 当前状态

学生当前提交的步骤：
{student_current_input}

参考解法的期望步骤：
{expected_step_content}

历史干预记录：
{intervention_memory}
每条记录包含：
  - qa_history：学生问答摘要
  - prompt_level：系统提示层级（R1-R4）
  - prompt_content：提示的具体内容
  - student_response：学生反应（accepted / rejected / still_stuck）

## 干预等级定义

**R1 线索唤醒型**（强度最低）：
- 学生完全没有思路，不知道从哪下手
- 提示目标：只点触发线索，不提及具体方法名或公式
- 典型形式："先看看题目里哪种结构最显眼"

**R2 图式定向型**：
- 学生有零散思路，但没有形成完整的解题图式
- 提示目标：给出高阶图式路标，但不替学生展开计算
- 典型形式："这一步需要的是一种'把条件统一起来的图式'"

**R3 资源显化型**：
- 学生有解题方向，但关键知识或定理调用缺失
- 提示目标：直接补出关键知识、定理或典型出口状态，但不全程展示
- 典型形式："这里真正用到的是 A 定理和 B 关系"

**R4 半展开示范型**（强度最高）：
- 学生有方向但完全无法推进，资源断裂明显
- 提示目标：直接给出关键第一小步或半成品结构
- 典型形式："先把它改写成……这样就能看到后面怎么接上"

## 升级/切换决策指南（最终版）

### 规则一：同维度内升级
- R1 → R2 → R3 → R4（R4为Resource最高级，不可再升）
- M1 → M2 → M3 → M4 → M5（M5为Metacognitive最高级，不可再升）

### 规则二：R侧无法解决 → 终止AI干预
- 如果当前等级为R4，且student_response == "not_progressed"
- → 输出 "max_level_reached"
- → system_response: "不能直接给你答案，建议暂停尝试，或寻求老师帮助"
- → 终止干预流程

### 规则三：M侧无法解决 → 切换到R侧
- 如果当前等级为M1-M5（任意），且student_response == "not_progressed"
- 且已尝试过合理次数的M侧干预
- → 输出 "switch_to_resource"
- → 切换到Resource维度，从R1重新开始判断
- （M5本身也是这个逻辑：元认知层面给到了极限，仍然不行，说明可能是资源侧问题）

### 规则四：维持
- 如果student_response == "accepted" → 维持当前等级

## 输出格式（JSON）

{
  "sub_type": "R1" | "R2" | "R3" | "R4",
  "confidence": 0.0-1.0,
  "reasoning": "为什么选这个等级，2-3句话",
  "hint_direction": "生成提示时应遵循的方向，1-2句话",
  "escalation_decision": {
    "action": "maintain" | "escalate" | "switch_to_resource" | "max_level_reached",
    "from_level": "当前等级（如 R1）",
    "to_level": "目标等级（如 R2，维持时与from_level相同；switch时为新维度起始级）",
    "reasoning": "升级/维持/切换的理由，1-2句话",
    "system_response": "当 action == max_level_reached 时，填入对学生的最终回复"
  }
}
```

### Prompt v2（Dimension == Metacognitive 时）

```
你是一位数学解题教育专家。

Node 2a 已判断学生困难为 **Metacognitive（元认知侧）**。
你的任务是：
1. 确定最合适的干预等级（M1-M5）
2. 参考历史干预记录，自主决定是否需要升级

## 当前状态

学生当前提交的步骤：
{student_current_input}

参考解法的期望步骤：
{expected_step_content}

历史干预记录：
{intervention_memory}
每条记录包含：
  - qa_history：学生问答摘要
  - prompt_level：系统提示层级（M1-M5）
  - prompt_content：提示的具体内容
  - student_response：学生反应（accepted / rejected / still_stuck）

## 干预等级定义

**M1 路径判定支持型**：
- 核心问题：这条路的"前景"如何？还值得走吗？
- 训练目标：帮助学生学会自己判断方向是否有效
- 典型形式："再做两步会得到什么？"、"这一步有没有带来新的约束或新关系？"
- 注意：不直接说"对"或"错"，而是引导学生自己看"前景"

**M2 路径维持与稳住型**：
- 核心问题：这条路的"局部"卡住了，别放弃
- 训练目标：帮助区分"局部卡顿"和"整体失效"，维持有效路径
- 典型形式："这条路还在产生有效信息，先不要换"

**M3 路径推进定向型**：
- 核心问题：既然路对，第一小步是什么？
- 训练目标：帮助学生在正确方向内部确定推进顺序
- 典型形式："先比较：哪一步更能缩小问题空间？"、"先找最关键的落脚点"
- 注意：M3是在方向已经确认后，帮学生定向；M1是帮助判断方向是否有效

**M4 路径修正与切换型**：
- 当前路径已经明显失效，但学生仍在机械坚持
- 提示目标：引导停止低价值分支，回退并重新比较候选路径
- 典型形式："当前分支先停，不要继续堆步骤"

**M5 路径切换后的重建型**：
- 学生已回退，但切换后不知道如何重建新的推进重心
- 提示目标：帮助确定新的可操作起点
- 典型形式："既然这条路已经放弃，现在哪个候选更可能先生成关键中间状态？"

## 升级/切换决策指南（最终版）

### 规则一：M侧升级不完全线性
M侧升级由LLM自主判断，不完全是M1→M2→M3→M4→M5的线性升级：
```
M1 失败 → M2 或 M3+（看学生是需要维持还是更具体）
M2 失败 → M3 或 M3+（看学生是需要推进还是更具体）
M3 失败 → M3+（更详细）或 M4（只有断点切换时才切M4）
M4 失败 → M5
M5 失败 → switch_to_resource
```

### 规则二：M3 → M4 的触发
- M3失败后，LLM判断给更详细的M3+还是切换到M4
- M3+：学生方向对，但缺乏具体细节
- M4：只有当学生路径确实发生变化（断点切换）时才触发

### 规则三：M侧无法解决 → 切换到R侧
- 如果M5仍失败
- → 输出 "switch_to_resource"
- → 切换到Resource维度，从R1重新开始判断

### 规则四：维持
- 如果student_response == "accepted" → 维持当前等级

## 输出格式（JSON）

{
  "sub_type": "M1" | "M2" | "M3" | "M4" | "M5",
  "confidence": 0.0-1.0,
  "reasoning": "为什么选这个等级，2-3句话",
  "hint_direction": "生成提示时应遵循的方向，1-2句话",
  "escalation_decision": {
    "action": "maintain" | "escalate" | "switch_to_resource",
    "from_level": "当前等级",
    "to_level": "目标等级（如 escalation 时为 R1；维持时与from_level相同）",
    "reasoning": "升级/维持/切换的理由，1-2句话"
  }
}
```

---

## Node 3: Strategy Controller（执行节点）

### 职责
纯代码执行。不做任何决策，只根据 Node 2b 的指令操作 Global State。

### 决策表

| Node 2b escalation_decision.action | Node 3 操作 |
|-----------------------------------|------------|
| `maintain` | 维持当前 prompt_level，更新 qa_history |
| `escalate` | 更新 prompt_level，生成新提示 |
| `switch_to_resource` | 切换到R维度，从R1重新开始判断 |
| `max_level_reached` | 终止干预流程，输出最终回复 |

---

## intervention_memory 数据结构（最终版）

```python
# Global State 中的干预记忆
intervention_memory: List[{
    "turn": int,                           # 第几轮干预
    "qa_history": {                        # 学生问答
        "student_q": "学生说了什么/做了什么",
        "system_a": "系统给了什么提示"
    },
    "prompt_level": str,                    # R1/R2/R3/R4/M1/M2/M3/M4/M5
    "prompt_content": str,                  # 提示的具体内容
    "student_response": "accepted" | "not_progressed",  # Node 1 自动判断
    "frontend_signal": "END" | "ESCALATE" | null,       # 前端触发（可选）
    "breakpoint_status": "resolved" | "persistent"
}]
```

### student_response 定义

| 值 | 定义 | 触发条件 |
|----|------|----------|
| `accepted` | 学生推进了 | Node 1 判定断点消失/推进到新位置 |
| `not_progressed` | 学生没推进 | Node 1 判定断点位置没变 |

### frontend_signal 定义

| 值 | 定义 | 触发条件 |
|----|------|----------|
| `END` | 直接结束干预 | 学生点击"我知道了" |
| `ESCALATE` | 强制升级 | 学生点击"给我更强提示" |
| `null` | 无前端信号 | 按 student_response 正常处理 |

---

## 讨论点（未确认，需进一步讨论）

| # | 问题 | 影响 |
|---|------|------|
| 1 | `student_response` 的采集 — 谁来判定"推进到下一阶段"（accepted）？是 Node 1 的 BreakpointLocator？还是前端行为埋点？ | 重要：影响整个反馈回路的起点 |
| 2 | `new_breakpoint` — 如果学生推进后出现了**新的断点**（不是同一个），这个信号 Node 2b 应该怎么处理？是否需要重新跑 Node 1 → 2a → 2b？ | 中等：当前设计里没有处理这个分支 |
| 3 | `switch_dimension` 的边界 — 什么时候从 Resource 切 Metacognitive？目前 Prompt 里给的是"连续2-3次升级同一维度仍无效"，这个标准够用吗？ | 中等：需要更多案例验证 |
