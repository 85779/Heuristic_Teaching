# Module 2 框架 PRD 评审文档

> 基于用户提供的 PRD v2，分析框架完整性，列出未决问题，按优先级排序供讨论确认。

---

## 一、框架概览

```
┌─────────────────────────────────────────────────────────────┐
│                    Global State Object                      │
│  problem_context / student_history / intervention_memory     │
│  current_diagnosis / current_student_input                  │
└─────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
      ┌──────────┐     ┌────────────┐    ┌─────────────────┐
      │  Node 1  │────▶│   Node 2   │───▶│     Node 3      │
      │ Breakpoint│     │ Diagnostic │     │    Strategy     │
      │ Locator   │     │   Router   │     │   Controller    │
      └──────────┘     └────────────┘    └─────────────────┘
                                               │      │
                                               ▼      ▼
                                        ┌──────────┐ ┌──────────┐
                                        │  Node 4  │ │  Node 5  │
                                        │ Prompt   │ │  Output  │
                                        │Generator │ │ Guardrail│
                                        └──────────┘ └──────────┘
```

---

## 二、当前框架的实质进步（相比 v1）

| 方面 | v1 的问题 | v2 的改进 |
|------|----------|----------|
| 状态管理 | 缺失 | Global State Object 统一管理 |
| 干预策略 | 只有分类，无升级机制 | Strategy Controller 处理升级/降级 |
| 输出安全 | 无 | Node 5 Guardrail 拦截越界内容 |
| 模型分工 | 单一模型 | Node 2(重模型) vs Node4/5(轻模型) |

---

## 三、待确认的 10 个核心问题

### P0 — Node 2 分流 Prompt 设计（最优先）

**核心问题**：Node 2a 如何判断学生属于 Resource 还是 Metacognitive？

**两个维度的精确定义（来自计划.md）**：

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
```

**连接点：图式**
- Resource → 提供"有什么可走、为什么会出现"
- Metacognitive → 对已激活路径"如何判定、推进与修正"
- 两者在同一个"下一步"上形成前后衔接，不是平行关系

---

### P1 — 升级/切换规则（✅ 已确认）

**最终确认的升级/切换逻辑**：

```
同维度内升级：
  R1 → R2 → R3 → R4（R4为最高级，不可再升）
  M1 → M2 → M3 → M4 → M5（M5为最高级，不可再升）

M侧无法解决 → 切换到R侧：
  - 条件：M1-M5任意级别，student_response == "not_progressed"
  - 结果：切换到Resource维度，从R1重新开始判断
  - 含义：元认知层面给到极限仍不行，说明学生可能存在潜在的资源/知识缺口

R侧无法解决 → 终止AI干预：
  - 条件：R4，student_response == "not_progressed"
  - 结果：输出"不能直接给你答案，建议暂停尝试，或寻求老师帮助"
  - 含义：Resource给到最高级仍不行，说明学生可能不是真的在做题

⚠️ R侧不能切换到M侧：R侧到达最高级必须终止，不允许切换
```

---

### P2 — 学生反馈采集机制（✅ 已确认）

**双重信号控制**：

```
Node 1 自动判断（后端）：
  - accepted       → 学生推进了（断点消失/推进到新位置）
  - not_progressed → 学生没推进（断点位置没变）

前端信号（可选）：
  - END      → 直接结束干预
  - ESCALATE → 强制升级到更高一级提示
```

**前端交互**：
```
[我知道了]        → END
[给我更强提示]    → ESCALATE
```

**Node 2b 判断逻辑**：
```
1. frontend_signal == END → 直接终止
2. frontend_signal == ESCALATE → 强制升级（+1级）
3. frontend_signal == null + student_response == "accepted" → 结束，或继续
4. frontend_signal == null + student_response == "not_progressed" → 升级
   - R4最高级 → 终止
   - M5最高级 → 切换到R侧
```

**数据结构**：
```python
{
    "turn": int,
    "qa_history": {"student_q": str, "system_a": str},
    "prompt_level": str,
    "prompt_content": str,
    "student_response": "accepted" | "not_progressed",
    "frontend_signal": "END" | "ESCALATE" | null,
    "breakpoint_status": "resolved" | "persistent"
}
```

---

### P3 — 各等级显化边界量化（✅ 部分已确认）

**R侧边界（已确认）**：

| 等级 | 核心 | 显性程度 | 典型禁止内容 |
|------|------|----------|-------------|
| R1 | 触发线索 | 最低 | 不给方法名、公式、具体数值 |
| R2 | 图式方向 | 低 | 只给方法类型，不展开计算 |
| R3 | 知识/定理 | 中 | 给定理内容，但不生成真实小步 |
| R4 | 第一小步 | 高 | 给出真实第一小步，但不全程解法 |

**R2 → R3 边界（已确认）**：
- R2：只给图式名/方法类型（如"换元法"）
- R3：给出了具体某个定理的详细内容（如"换元法：设 t = x+1，把分母统一成 t²"）

**R3 → R4 边界（已确认）**：
- R3：只给出定理/知识内容
- R4：通过定理生成了真实的第一小步（如"第一步：设 t = x+1，整理得 t²-3t+2=0"）

**M侧边界（已确认）**：

| 等级 | 核心问题 | 典型形式 |
|------|----------|---------|
| M1 | 这条路的"前景"如何？还值得走吗？ | "再做两步会得到什么？" |
| M2 | 这条路的"局部"卡住了，别放弃 | "这条路还在产生有效信息" |
| M3 | 既然对，第一小步是什么？ | "先找最关键的落脚点" |
| M4 | 这条路不行了，该停了 | "先停，不要继续堆步骤" |
| M5 | 路换了，从哪起步？ | "哪个候选更可能生成果" |

**M侧升级逻辑（已确认）**：

M侧升级不完全是线性的，由 LLM 判断：
```
M1 失败 → M2 或 M3+（看需要维持还是更具体）
M2 失败 → M3 或 M3+（看需要推进还是更具体）
M3 失败 → M3+（更详细）或 M4（如果路径变了）
M4 失败 → M5
M5 失败 → switch_to_resource
```

**M3 → M4 的触发（已确认）**：
- M3 失败后，LLM 判断给更详细的 M3+ 还是切换到 M4
- M3+：学生方向对，但缺乏具体细节 → 继续 M3 但更详细
- 切换到 M4：只有当学生路径确实发生变化（断点切换）时才触发

---

### P4 — Module 1 → 2 接口（✅ 已确认）

**核心理解**：Module 1 只负责生成 solution_steps，Module 2 接管后续所有干预流程。

**接口设计**：

```
Module 1.generate() 
  → SessionState {
      problem_context,    # 题目上下文
      solution_steps,     # 参考解法步骤
    }
        ↓
Module 2 开始工作，从 SessionState 读取
        ↓
Module 2 独立运行干预循环，不依赖 Module 1 继续发送事件
```

**Module 2 内部事件/信号**：

| 信号 | 来源 | Module 2 响应 |
|------|------|--------------|
| `session_started` | Module 1 生成完毕 | 读取 SessionState，开始监控 |
| `student_step_submitted` | 学生提交步骤 | 判断是否需要干预 |
| `student_help_request` | 学生主动说"卡住了" | 进入完整干预流程 |
| `frontend_signal` | 前端按钮 | END / ESCALATE |

**Module 2 自主循环**：

```
学生提交步骤
       ↓
Node 1 定位断点（是否有断点？）
       ↓
有断点 → Node 2a → 2b → 3 → 4 → 5
       ↓
学生收到提示
       ↓
frontend_signal（END/ESCALATE）或 student_response（accepted/not_progressed）
       ↓
决定：结束 / 升级 / 维持 / 切换维度
       ↓
继续监控学生下一步...
```
学生行为              →  触发事件           →  Module 2 响应
─────────────────────────────────────────────────────────
学生主动说"下一题"    →  stuck_detected?   →  进入干预流程
学生提交步骤后停顿>60s →  stuck_detected?   →  提示是否需要帮助？
学生提交了错误步骤    →  error_detected    →  生成 M4（路径修正）提示
学生提交了空步骤      →  ???               →  需要判断是无思路还是误触
学生提交了完整但方向偏的 →  ???             →  需要判断是 WRONG 还是只是慢
```

---

### P5 — 技术选型（✅ 已确认）

**Qwen 模型（原型阶段）**：
```
所有 Node 全部使用 qwen-turbo
  → Node 2a、2b、4、5 都用 qwen-turbo
  → 后续可替换为更强的模型（qwen-plus / qwen-max）
```

**存储（原型阶段）**：
```
只用 MongoDB
  → SessionState 存 MongoDB
  → intervention_memory 存 MongoDB
  → 后续性能不够再加 Redis
```

---

## 四、框架新增内容建议（用户原始 PRD 未覆盖）

| 新增模块 | 目的 | 优先级 |
|----------|------|--------|
| **学生反馈采集层** | 定义和采集 accepted/rejected/still_stuck 信号 | P2 |
| **升级/降级规则引擎** | 将 Strategy Controller 的升级逻辑具体化 | P1 |
| **各等级显化边界量化** | R1-R4/M1-M5 的 Guardrail 规则表 | P3 |
| **断点类型 → 困难维度映射** | MISSING_STEP/WRONG_DIRECTION/INCOMPLETE → Resource/Metacognitive 的默认映射 | P0 |

---

## 五、断点类型与困难维度的映射（已确认）

| 断点类型 | 映射维度 | 原因 |
|----------|----------|------|
| MISSING_STEP | Resource | 没有形成候选路径 |
| WRONG_DIRECTION | Resource | 候选路径本身就是错的，没有形成正确的"可走之路" |
| INCOMPLETE_STEP | Metacognitive | 候选路径已出现，方向对但展开不完整 |
| STUCK | Resource | 完全不知道下一步怎么走 |

> ⚠️ WRONG_DIRECTION 不是 Metacognitive 问题——方向错说明没有形成正确的候选，是 Resource 问题。
> 这个映射是默认判断，Node 2a 有权根据学生具体输入调整。

---

## 六、Open Questions 汇总（按优先级）

| 优先级 | 问题 | 状态 |
|--------|------|------|
| **P0** | Node 2 分流 Prompt 怎么写？输入输出格式？ | ✅ 维度的精确定义已确认 |
| **P0** | 断点类型 → 困难维度的映射 | ✅ 已确认 |
| **P1** | 升级/切换规则 | ✅ 已确认 |
| **P2** | 学生反馈采集机制 | ✅ 已确认 |
| **P3** | 各等级显化边界量化 | ✅ R/M边界已确认；M3→M4边界已确认 |
| **P4** | Module 1 → 2 接口和事件响应机制 | ✅ 已确认 |
| **P5** | Qwen 模型选型 + 存储方案 | ✅ 已确认 |

---

## 七、已确认的设计决策（最终版）

### ✅ 升级/切换逻辑
- R侧：R1→R2→R3→R4，R4为最高级，不可再升，不可切换到M侧
- M侧：M1→M2→M3→M4→M5，M5为最高级
- M侧失败 → 切换到R侧，从R1重新判断
- R侧最高级失败 → 终止AI干预

### ✅ 两阶段分流
- Node 2a：R/M 二元分流（只输出dimension）
- Node 2b：具体等级决策 + 升级策略（LLM自主决定）
- Node 3：纯代码执行，不做决策

### ✅ memory 数据结构
```python
{
    "turn": int,
    "qa_history": {"student_q": str, "system_a": str},
    "prompt_level": str,
    "prompt_content": str,
    "student_response": "accepted" | "rejected" | "still_stuck"
}
```

---

## 八、下一步讨论计划

✅ 所有 Open Questions 已确认完毕
