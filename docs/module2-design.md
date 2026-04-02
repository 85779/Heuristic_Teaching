# Module 2: 断点分层递进干预系统设计文档

**版本**: v2  
**核心功能**: 基于五节点管道的渐进式 Scaffold 干预引擎  
**最后更新**: 2026-03-30

---

## 1. 架构图（Architecture Diagram）

### 1.1 整体管道流程

```
学生输入
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  节点 1: BreakpointLocator                                            │
│  输入: student_steps, solution_steps                                  │
│  输出: BreakpointLocation (position, type, gap_description)           │
│  逻辑: 纯规则计算，三级级联匹配（无 LLM）                               │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  节点 2a: DimensionRouter                                            │
│  输入: student_input, expected_step, breakpoint_type, problem_context │
│  输出: DimensionResult { dimension: R|M, confidence, reasoning }     │
│  逻辑: LLM 分类，temperature=0.3，max_tokens=512                      │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  节点 2b: SubTypeDecider                                             │
│  输入: dimension, student_input, expected_step, intervention_memory, │
│        frontend_signal, current_level, problem_context                │
│  输出: SubTypeResult { sub_type: R1-R4|M1-M5, reasoning,             │
│                        escalation_decision }                          │
│  逻辑: LLM 决策，temperature=0.3，max_tokens=1024                      │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  节点 4: HintGeneratorV2                                             │
│  输入: level, problem_context, student_input, expected_step,          │
│        student_steps                                                  │
│  输出: { content: str, level: str, approach_used: str,                 │
│          original_intensity: float }                                 │
│  逻辑: LLM 生成，temperature=0.7，max_tokens=512                       │
│  约束: 永不直接给出完整答案                                            │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  节点 5: OutputGuardrail                                             │
│  输入: content, level                                                 │
│  输出: GuardrailResult { passed, reason, violations, revised_content } │
│  逻辑: 双层检查（Layer 1 规则 <1ms + Layer 2 LLM ~1s）                │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
提示内容 ──► 返回学生
```

### 1.2 ContextManager 侧向支撑

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ContextManager                                │
│                                                                      │
│   session_id ──► InterventionContext                                 │
│                      ├── session_id                                  │
│                      ├── student_id                                  │
│                      ├── dimension_result (from Node 2a)             │
│                      ├── current_level (R1-R4|M1-M5)                  │
│                      ├── intervention_memory (历史记录列表)            │
│                      ├── status (ACTIVE|COMPLETED|TERMINATED)        │
│                      └── ...                                         │
│                                                                      │
│   Fire-and-forget MongoDB persistence via asyncio.create_task()       │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.3 数据流摘要

| 阶段 | 输入 | 输出 | 关键决策 |
|------|------|------|----------|
| Locator | student_steps, solution_steps | BreakpointLocation | 断点位置 + 类型 |
| Router | breakpoint_type, student_input | {R, confidence} | 维度分类 |
| Decider | dimension, memory, current_level | {R1-R4/M1-M5, escalation} | 等级 + 升级策略 |
| Generator | level, problem_context | hint content | 提示生成 |
| Guardrail | hint content, level | {passed, violations} | 安全审查 |

---

## 2. 各节点设计详解（Component-by-Component Design）

### 2.1 节点 1: BreakpointLocator（断点定位）

**文件**: `locator/breaker.py`  
**设计原则**: 纯规则驱动，**不使用 LLM**，确保毫秒级响应

#### 2.1.1 三级级联匹配算法

```
┌─────────────────────────────────────────────────────────────────────┐
│                    三级语义匹配流程                                   │
│                                                                      │
│  Level 1: Jaccard 关键词重叠                                         │
│  ─────────────────────────────────────────────────────────────────  │
│  overlap > 0.80  ──► 匹配成功，继续比较下一步                          │
│  overlap < 0.30  ──► 进入 Level 2（低重叠 ≠ 错误，可能是缩写）         │
│  0.30 ≤ overlap ≤ 0.80 ──► 进入 Level 2                             │
│                                                                      │
│  Level 2: effective_sim 字符串相似度                                   │
│  ─────────────────────────────────────────────────────────────────  │
│  effective_sim > 0.80  ──► 匹配成功，继续                            │
│  effective_sim < 0.30  ──► 进入 Level 3                             │
│  0.30 ≤ effective_sim ≤ 0.80 ──► INCOMPLETE（继续扫描）             │
│                                                                      │
│  Level 3: WRONG_DIRECTION 判定                                        │
│  ─────────────────────────────────────────────────────────────────  │
│  keyword < 0.3 AND sim < 0.2  ──► WRONG_DIRECTION（双重低 = 偏离）   │
│  否则  ──► INCOMPLETE（继续扫描，查找真正的断点）                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### 2.1.2 effective_sim 的动态选择逻辑

```python
if kw_count >= 2:
    # 关键词丰富内容 → 信任关键词重叠度
    effective_sim = overlap
else:
    # 稀疏内容（如短英文短语）→ 回退到字符串相似度
    effective_sim = self._string_similarity(text1, text2)
```

#### 2.1.3 INCOMPLETE 处理策略（关键设计）

**重要**: `INCOMPLETE` **不是最终答案**——系统**不停止在此层级**，而是继续扫描后续步骤，直到找到真正的断点。

```python
# Case 3: 中等相似度 (0.3–0.8) → INCOMPLETE（继续扫描）
# 学生思路正确但内容不完整，可能在后续步骤中找到真正断点
if len(student_content) < len(expected_content) * 0.4:
    continue  # 内容过短但方向对——继续
continue  # 实质内容但未完全匹配——继续扫描
```

#### 2.1.4 断点类型定义

| 类型 | 含义 | 典型场景 |
|------|------|----------|
| `MISSING_STEP` | 学生缺少该步骤 | 学生提交空白或只有导入语 |
| `WRONG_DIRECTION` | 方向偏离参考解法 | 双重低相似度（关键词<0.3 且 字符串<0.2）|
| `INCOMPLETE_STEP` | 该步骤内容不完整 | 有实质内容但未达到参考标准 |
| `STUCK` | 完全卡住 | 学生未提供任何步骤 |
| `NO_BREAKPOINT` | 无断点 | 学生与参考解法一致 |

#### 2.1.5 关键词提取规则（Jaccard）

```python
def _extract_keywords(self, text: str) -> set:
    """提取数学-aware 关键词"""
    # 1. LaTeX 命令: \alpha, \gcd, etc.
    tokens.update(re.findall(r'\\[a-zA-Z]+', text))
    # 2. 中文词汇（≥2字符）
    chinese = re.findall(r'[\u4e00-\u9fff]{2,}', text)
    tokens.update(chinese)
    # 3. 数学术语（单字符）
    math_terms = {"设", "令", "得", "为", "于", "在", "求", "证", ...}
    tokens.update(c for c in math_chars if c in math_terms)
    # 4. 变量名 (a-zA-Z)
    # 5. 数字
    # 6. 数学运算符
```

---

### 2.2 节点 2a: DimensionRouter（维度路由）

**文件**: `router/dimension_router.py`  
**职责**: 将断点分类为 **Resource** 或 **Metacognitive**

#### 2.2.1 输入输出

```python
async def route(
    student_input: str,
    expected_step: str,
    breakpoint_type: str,           # MISSING_STEP | WRONG_DIRECTION | INCOMPLETE_STEP | STUCK
    intervention_memory: Optional[List[InterventionRecord]] = None,
    problem_context: str = "",
) -> DimensionResult:
    # 输出:
    # DimensionResult {
    #     dimension: DimensionEnum.RESOURCE | DimensionEnum.METACOGNITIVE,
    #     confidence: float,
    #     reasoning: str
    # }
```

#### 2.2.2 启发式映射（LLM 参考）

| 断点类型 | 默认维度 | 置信度 | 理由 |
|----------|----------|--------|------|
| `MISSING_STEP` | **Resource** | 高 | 学生没有形成候选路径 |
| `WRONG_DIRECTION` | **Resource** | 高 | 候选路径本身就是错的 |
| `INCOMPLETE_STEP` | **Metacognitive** | 中 | 候选已出现，展开不完整 |
| `STUCK` | **Resource** | 高 | 完全不知道怎么做 |

#### 2.2.3 LLM 调用参数

| 参数 | 值 | 理由 |
|------|-----|------|
| model | qwen-turbo | 分类任务不需要最强模型 |
| temperature | 0.3 | 低温度保证稳定分类 |
| max_tokens | 512 | JSON 输出简短 |

#### 2.2.4 跨维度升级

当 Resource 侧达到 **R4** 仍无效时，系统支持切换到 **M3**（`SWITCH_TO_RESOURCE` action）。

---

### 2.3 节点 2b: SubTypeDecider（子类型决策）

**文件**: `decider/sub_type_decider.py`  
**职责**: 在维度内部确定具体级别（R1-R4 或 M1-M5）并决策升级策略

#### 2.3.1 Resource 维度（R1-R4）

| 等级 | 强度 | 定义 | 典型提示 |
|------|------|------|----------|
| **R1** | 最低 | 线索唤醒型 | "先看看题目里哪种结构最显眼" |
| **R2** | 中低 | 图式定向型 | "这一步需要的是一种'换元法'" |
| **R3** | 中高 | 资源显化型 | "换元法：设 t = x+1，把分母统一成 t²" |
| **R4** | 最高 | 半展开示范型 | "第一步：设 t = x+1，整理得 t²-3t+2=0" |

#### 2.3.2 Metacognitive 维度（M1-M5）

| 等级 | 强度 | 核心问题 | 典型提示 |
|------|------|----------|----------|
| **M1** | 最低 | 这条路的"前景"如何？ | "再做两步会得到什么？" |
| **M2** | 中低 | 别放弃这条路 | "这条路还在产生有效信息" |
| **M3** | 中 | 既然对，第一小步是什么？ | "先比较哪一步更能缩小问题空间" |
| **M4** | 中高 | 该停了 | "当前分支先停，不要继续堆步骤" |
| **M5** | 最高 | 路换了，从哪起步？ | "哪个候选更可能生成果？" |

#### 2.3.3 升级决策逻辑

```python
escalation_decision.action:
├── MAINTAIN        # 维持当前等级（学生有进步）
├── ESCALATE        # 升级到下一级（学生未进步）
├── SWITCH_TO_RESOURCE  # R侧失败，切换到 M侧 R1
└── MAX_LEVEL_REACHED  # 达到最高级，终止干预
```

**前端信号处理**:

| 信号 | 处理 |
|------|------|
| `PROGRESSED` | 维持当前等级 |
| `NOT_PROGRESSED` | 执行 escalation_decision |
| `DISMISSED` | 执行 escalation_decision |
| `ESCALATE` | 强制升级到下一级 |
| `END` | 终止干预 |

#### 2.3.4 LLM 调用参数

| 参数 | 值 | 理由 |
|------|-----|------|
| model | qwen-turbo | 决策任务不需要最强模型 |
| temperature | 0.3 | 低温度保证稳定决策 |
| max_tokens | 1024 | 决策输出较复杂 |

---

### 2.4 节点 4: HintGeneratorV2（提示生成）

**文件**: `generator/hints_v2.py`  
**职责**: 基于级别生成 Socratic 风格的提示

#### 2.4.1 核心约束

> **永不直接给出完整答案**  
> 提示的目的是**引导**学生自己发现，而不是**替代**学生完成推理。

#### 2.4.2 R 维度提示策略

```python
R1_PROMPT = """
- 只给方向性提示，不给具体知识内容
- 不提及具体定理名称（如"余数定理"、"数学归纳法"等）
- 不给出第一步的具体形式
- 引导学生自己发现下一步应该做什么
"""

R2_PROMPT = """
- 可以提及具体的定理名称、知识概念
- 仍然不给出第一步的具体形式
- 通过指明所需知识来引导学生
"""

R3_PROMPT = """
- 可以给出第一步的理论形式（如"先求一个中间量"）
- 不给出具体数值计算
- 学生能知道第一步该做什么形式，但不知道具体怎么算
"""

R4_PROMPT = """
- 给出真实的计算步骤
- 可以包含具体的数值计算
- 让学生能够直接按照提示进行计算
"""
```

#### 2.4.3 M 维度提示策略

```python
M1_PROMPT = """
- 帮助学生判断"应该继续还是停下来思考"
- 分析当前路径是否还有推进空间
- 引导学生评估自己的解题方向
- 问学生关于当前路径的问题
"""

M2_PROMPT = """
- 给出方向性指引
- 告诉学生应该往哪个方向思考
- 不涉及具体知识点或计算
"""

M3_PROMPT = """
- 给出更详细的方向指引
- 可以提示解题方法（如"考虑换元"、"考虑数学归纳法"）
- 帮助学生确定具体该怎么做
"""

M4_PROMPT = """
- 当 breakpoint 类型发生变化时触发
- 给出具体的解题步骤描述
- 可以包含多个可选路径
"""

M5_PROMPT = """
- 最详细的提示级别
- 给出完整的解题思路
- 包含类似题目的参考
"""
```

#### 2.4.4 LLM 调用参数

| 参数 | 值 | 理由 |
|------|-----|------|
| model | qwen-turbo | 生成任务 |
| temperature | **0.7** | 较高温度增加多样性 |
| max_tokens | 512 | 提示应简洁 |

---

### 2.5 节点 5: OutputGuardrail（输出护栏）

**文件**: `guardrail/guardrail.py`  
**职责**: 确保提示内容安全，不泄露答案

#### 2.5.1 双层检查架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Layer 1: 规则检查（同步，<1ms）                   │
│                                                                      │
│  - 遍历 RULES[level]["forbidden"] 关键词                              │
│  - 正则匹配"答案[是为：：]"、"所以最终结果是?"等通用违规               │
│  - 命中任何一项 → 直接拒绝                                            │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 │ passed=True
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Layer 2: LLM Judge（异步，~1s）                     │
│                                                                      │
│  - 调用 LLM 判断提示是否违规                                          │
│  - temperature=0.1（极低温度，保证判断一致）                         │
│  - max_tokens=256                                                    │
│  - 违规 → 进入 Rewrite Protocol                                       │
└─────────────────────────────────────────────────────────────────────┘
```

#### 2.5.2 各等级边界规则

```python
RULES = {
    "R1": {
        "forbidden": ["具体方法名称", "具体公式", "具体数值", "设 t =", "令 x =", "代入得"],
        "allowed": ["方向性描述", "结构观察提示", "关系类比提示"]
    },
    "R4": {
        "forbidden": ["完整全程解法", "完整解题步骤"],
        "allowed": ["第一小步的完整写法", "半成品结构", "关键中间台阶"]
    },
    "M1": {
        "forbidden": ["直接告诉方向对不对", "替学生做判定"],
        "allowed": ["引导学生观察方向", "问前景是什么"]
    },
    # ... 其他等级
}
```

#### 2.5.3 Rewrite Protocol（重写协议）

```python
if not guardrail_result.passed:
    # Layer 2 失败 → 使用 Socratic framing 重写
    hint_content = self._socratic_rewrite(hint_content, level)
    
    # 再次检查
    guardrail_result = await self._guardrail.check(hint_content, level)
    
    # 仍然失败 → 使用 fallback
    if not guardrail_result.passed:
        hint_content = "继续思考这道题"
```

#### 2.5.4 Fallback 内容

```python
FALLBACK_HINTS = {
    "R1": "回顾一下题目中的已知条件，思考它们和所求目标之间有什么关系？",
    "R2": "思考一下解决这个问题可能需要用到哪些数学定理或方法。",
    "R3": "尝试从已知条件出发，先求出某个中间量。",
    "R4": f"参考步骤：{expected_step[:50]}...",
    "M1": "你觉得当前的解题方向是否正确？是否应该尝试其他方法？",
    "M5": "参考类似题目的解法，尝试套用相同的思路。",
}
```

---

## 3. 上下文管理器设计（ContextManager Design）

**文件**: `context_manager.py`

### 3.1 InterventionContext 数据结构

```python
@dataclass
class InterventionContext:
    session_id: str
    student_id: str
    problem_context: str
    student_input: str
    solution_steps: List[Dict[str, Any]]
    student_steps: List[Dict[str, Any]]
    breakpoint_location: Optional[BreakpointLocation] = None
    dimension_result: Optional[DimensionResult] = None      # from Node 2a
    sub_type_result: Optional[SubTypeResult] = None          # from Node 2b
    intervention_memory: List[InterventionRecord] = field(default_factory=list)
    current_level: str = ""                                   # R1-R4|M1-M5
    status: InterventionStatus = InterventionStatus.ACTIVE

    def is_active(self) -> bool: ...
    def is_terminated(self) -> bool: ...
    def is_completed(self) -> bool: ...
```

### 3.2 MongoDB Fire-and-forget 持久化

```python
def _schedule_persist(self, session_id: str) -> None:
    """调度异步持久化，不阻塞主管道"""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(self.persist_context(session_id))
    except RuntimeError:
        # 无运行中的事件循环 → 跳过（下次同步点再持久化）
        pass
```

### 3.3 Graceful Degradation（优雅降级）

```python
async def persist_context(self, session_id: str) -> None:
    try:
        await self._repo.upsert_context(session_id, self.save_context(session_id))
    except Exception as e:
        logger.warning(f"Failed to persist context: {e}")  # 仅记录，不抛出
        # 系统继续在内存中运行，不影响干预流程
```

### 3.4 Session 恢复

```python
def restore_from_session(
    self,
    session_id: str,
    student_id: str,
    problem_context: str,
    solution_steps: List[Dict[str, Any]],
    student_steps: List[Dict[str, Any]],
    **kwargs,  # current_level, intervention_memory, status
) -> InterventionContext:
    # 从 MongoDB 加载后重建 InterventionRecord 对象
    # 恢复干预历史和当前级别
```

### 3.5 升级/降级辅助函数

```python
def _next_resource_level(current: str) -> str:
    """R1 → R2 → R3 → R4 → R4"""
    return {"R1": "R2", "R2": "R3", "R3": "R4", "R4": "R4"}.get(current, "R1")

def _next_metacognitive_level(current: str) -> str:
    """M1 → M2 → M3 → M4 → M5 → M5"""
    return {"M1": "M2", "M2": "M3", "M3": "M4", "M4": "M5", "M5": "M5"}.get(current, "M1")
```

---

## 4. 服务编排（Service Orchestration）

**文件**: `service.py`

### 4.1 主管道: `create_intervention()`

```python
async def create_intervention(request: InterventionRequest) -> InterventionResponse:
    """
    完整五节点干预流程：

    1. 加载 SessionState solving state
    2. BreakpointLocator → 断点位置
    3. DimensionRouter → R/M 分类
    4. SubTypeDecider → 级别 + 升级决策
    5. HintGeneratorV2 → 提示内容
    6. OutputGuardrail → 安全审查
    7. 记录干预历史
    8. 应用升级决策
    9. 持久化到 MongoDB
    10. 返回提示给学生
    """
```

### 4.2 反馈处理: `process_feedback()`

```python
async def process_feedback(request: FeedbackRequest) -> InterventionResponse:
    """
    处理学生反馈：

    1. 加载 InterventionContext
    2. 检查前端信号（END/ESCALATE）
    3. 判断学生是否有进步（ACCEPTED vs NOT_PROGRESSED）
    4a. ACCEPTED → 重新运行 Locator 检查新断点
    4b. NOT_PROGRESSED → 运行 escalation decision
    5. 生成新提示
    6. 返回干预响应
    """
```

### 4.3 无进步处理: `_handle_no_progress()`

```python
async def _handle_no_progress(ctx, session_id, student_input) -> InterventionResponse:
    """
    学生未进步时的处理：

    1. 重新定位断点
    2. 重新运行 SubTypeDecider 获取 escalation_decision
    3. 应用升级（MAINTAIN | ESCALATE | SWITCH | TERMINATE）
    4. 生成新级别提示
    5. Guardrail 检查
    6. 持久化并返回
    """
```

### 4.4 跨维度切换: `apply_escalation()`

```python
def apply_escalation(session_id: str, decision: EscalationDecision) -> str:
    """
    应用升级决策：

    - MAINTAIN → 维持当前级别
    - ESCALATE → 同一维度内升级
    - SWITCH_TO_RESOURCE → 切换到 R 侧 R1
    - MAX_LEVEL_REACHED → 终止干预
    """
```

### 4.5 前端信号处理: `handle_frontend_signal()`

```python
def handle_frontend_signal(session_id: str, signal: FrontendSignalEnum) -> str:
    """
    处理前端信号：

    - END → 设置状态为 COMPLETED，返回 TERMINATED
    - ESCALATE → 强制升级到下一级，若已达最高级则 TERMINATE
    """
```

### 4.6 持久化: `_persist_intervention()`

```python
async def _persist_intervention(intervention: Intervention) -> None:
    """
    Fire-and-forget MongoDB 持久化：

    - 序列化 Intervention 对象
    - 调用 InterventionRepository.save_intervention()
    - 失败仅记录 warning，不阻塞流程
    """
```

---

## 5. 提示词模板（Prompt Templates）

### 5.1 DimensionRouter Prompt（维度路由）

```python
DIMENSION_ROUTER_PROMPT = """你是一位数学解题教育专家。

## 困难维度定义

**Resource（资源侧）**：
"下一步能不能出现"——学生是否形成了可用的候选路径。

典型特征：
- 空白提交，完全不知道下一步怎么走
- 有思路，但依赖的知识/图式本身错误或缺失
- 方向完全错误（WRONG_DIRECTION）——没有形成正确的候选路径

**Metacognitive（元认知侧）**：
"当前路径怎么管"——候选图式已经出现，路径已经激活后，如何管理和推进。

典型特征：
- 方向看起来对，但不知道下一步怎么展开
- 能看到目标，但看不清当前路径是否仍有效
- 局部卡住，不确定该继续坚持还是换路

## 输出格式（JSON）
{{
  "dimension": "Resource" | "Metacognitive",
  "confidence": 0.0-1.0,
  "reasoning": "判断理由，3-5句话"
}}
"""
```

### 5.2 SubTypeDecider Prompts（子类型决策）

**Resource 维度**:

```python
RESOURCE_DECIDER_PROMPT = """...（见 decider/prompts.py）

## 干预等级定义

R1 线索唤醒型：
- 学生完全没有思路，不知道从哪下手
- 提示目标：只点触发线索，不提及具体方法名或公式
- 典型形式："先看看题目里哪种结构最显眼"

R2 图式定向型：
- 学生有零散思路，但没有形成完整的解题图式
- 提示目标：给出高阶图式路标，但不替学生展开计算
- 典型形式："这一步需要的是一种'换元法'"

R3 资源显化型：
- 学生有解题方向，但关键知识或定理调用缺失
- 提示目标：直接补出关键知识、定理或典型出口状态
- 典型形式："换元法：设 t = x+1，把分母统一成 t²"

R4 半展开示范型：
- 学生有方向但完全无法推进，资源断裂明显
- 提示目标：直接给出关键第一小步或半成品结构
"""
```

**Metacognitive 维度**:

```python
METACOGNITIVE_DECIDER_PROMPT = """...

## 干预等级定义

M1 路径判定支持型：
- 核心问题：这条路的"前景"如何？还值得走吗？
- 典型形式："再做两步会得到什么？"

M2 路径维持与稳住型：
- 核心问题：这条路的"局部"卡住了，别放弃
- 典型形式："这条路还在产生有效信息，先不要换"

M3 路径推进定向型：
- 核心问题：既然对，第一小步是什么？
- 典型形式："先比较：哪一步更能缩小问题空间？"

M4 路径修正与切换型：
- 核心问题：这条路不行了，该停了
- 典型形式："当前分支先停，不要继续堆步骤"

M5 路径切换后的重建型：
- 核心问题：路换了，从哪起步？
- 典型形式："哪个候选更可能生成果？"
"""
```

### 5.3 HintGeneratorV2 Prompts（提示生成）

**R1 vs R4 对比**:

| 维度 | R1 | R4 |
|------|----|----|
| 方向 | ✅ 给出思考方向 | ✅ 给出执行步骤 |
| 方法名 | ❌ 不提及 | ❌ 不提及具体方法 |
| 计算 | ❌ 不计算 | ✅ 给出具体计算 |
| 示例 | "先看看哪种结构最显眼" | "设 t = x+1，整理得 t²-3t+2=0" |

**M1 vs M5 对比**:

| 维度 | M1 | M5 |
|------|----|----|
| 问题类型 | 问学生关于路径前景 | 给完整思路 |
| 具体度 | 抽象问题 | 详细步骤 |
| 答案泄露风险 | 低 | 中 |

### 5.4 OutputGuardrail Layer 2 Prompt

```python
GUARDRAIL_PROMPT = """你是一位严格的教育内容审查员。

## 审查标准

1. 如果提示包含任何"禁止的内容"，必须判定为不合格
2. 如果提示完全不包含任何有用信息，必须判定为不合格
3. 如果提示给出了"最终答案"或"完整解题步骤"，必须判定为不合格
4. 否则判定为合格

## 输出格式（JSON）
{{
  "pass": true | false,
  "reason": "通过原因或违规原因",
  "violations": ["违规项1", "违规项2"]  // 如果违规
}}
"""
```

---

## 6. 错误处理架构（Error Handling Architecture）

### 6.1 LLM JSON 解析失败

```python
# DimensionRouter / SubTypeDecider / HintGeneratorV2
try:
    data = json.loads(response_clean)
except (json.JSONDecodeError, KeyError, ValueError) as e:
    # 默认回退值
    return DimensionResult(dimension=DimensionEnum.RESOURCE, confidence=0.0, ...)
    # SubTypeDecider: default_level = R1 (R侧) 或 M1 (M侧)
    # HintGeneratorV2: return raw response
```

### 6.2 MongoDB 不可用

```python
async def persist_context(self, session_id: str) -> None:
    try:
        await self._repo.upsert_context(...)
    except Exception as e:
        logger.warning(f"Failed to persist context: {e}")
        # 系统继续在内存中运行，不影响干预流程
        # 服务重启后 session 状态丢失（graceful degradation）
```

### 6.3 Guardrail Layer 1 触发

```python
# 直接拒绝，不调用 Layer 2
if violations:
    return GuardrailResult(passed=False, reason=f"提示包含违规内容: {violations[0]}", violations=violations)
```

### 6.4 Guardrail Layer 2 触发

```python
if not guardrail_result.passed:
    # 进入 Rewrite Protocol
    hint_content = self._socratic_rewrite(hint_content, level)
    
    # 再次检查
    guardrail_result = await self._guardrail.check(hint_content, level)
```

### 6.5 双层均失败

```python
if not guardrail_result.passed:
    # 最终 fallback
    hint_content = FALLBACK_HINTS.get(level, "请仔细思考题目中的条件。")
```

### 6.6 错误处理流程图

```
LLM 调用
    │
    ▼
┌─────────────────┐
│ JSON 解析成功？  │
└─────────────────┘
    │
  Yes │ No
    │   │
    ▼   └──────────────► 默认回退值
解析字段缺失？          （RESOURCE/R1/生成本级提示）
    │
  Yes │ No
    │   │
    ▼   └──────────────► 使用返回值
检查通过？──────────────► Guardrail.check()
    │
  Yes │ No
    │   │
    ▼   └──────────────► Socratic rewrite → 再次检查
   通过                   │
    │                     │ 仍失败
    ▼                     ▼
  返回提示           Fallback 提示
```

---

## 7. MongoDB Schema

**数据库**: `math_tutor`  
**集合**: `intervention_contexts`, `interventions`

### 7.1 `intervention_contexts` 集合

```javascript
{
  "_id": ObjectId,
  "session_id": "string",          // 索引，查询键
  "student_id": "string",           // 索引
  "problem_context": "string",
  "current_level": "R1" | "R2" | "R3" | "R4" | "M1" | "M2" | "M3" | "M4" | "M5",
  "status": "active" | "completed" | "terminated",
  "intervention_memory": [
    {
      "turn": 1,
      "qa_history": {
        "student_q": "学生的问题/行为",
        "system_a": "系统生成的提示"
      },
      "prompt_level": "R2",
      "prompt_content": "发给 LLM 的完整 prompt",
      "student_response": "accepted" | "not_progressed",
      "frontend_signal": null | "END" | "ESCALATE",
      "breakpoint_status": "resolved" | "persistent",
      "created_at": ISODate
    },
    // ... more turns
  ],
  "breakpoint_location": null,      // 通常不持久化，仅内存使用
  "dimension_result": null,          // 仅内存使用
  "sub_type_result": null,          // 仅内存使用
  "updated_at": ISODate              // 索引，用于排序
}
```

**索引**:

```javascript
// 复合索引（查询最频繁）
db.intervention_contexts.createIndex({ "session_id": 1, "updated_at": -1 })

// 单字段索引
db.intervention_contexts.createIndex({ "student_id": 1 })
db.intervention_contexts.createIndex({ "updated_at": -1 })
```

### 7.2 `interventions` 集合

```javascript
{
  "_id": ObjectId,
  "id": "int_abc123",               // 唯一标识，upsert key
  "student_id": "string",
  "session_id": "string",
  "intervention_type": "hint" | "explanation" | "redirect" | "example" | "scaffold",
  "status": "suggested" | "delivered" | "accepted" | "dismissed" | "ignored",
  "content": "提示内容文本",
  "intensity": 0.5,                  // 0.0-1.0（v2 中固定 0.5）
  "metadata": {
    "breakpoint_location": "gap description",
    "breakpoint_type": "MISSING_STEP",
    "dimension": "Resource",
    "prompt_level": "R2",
    "reasoning": "决策理由",
    "escalation_action": "escalate",
    "new_level": "R3",
    "turn": 1,
    "mode": "initial" | "escalation" | "continue_after_progress"
  },
  "created_at": ISODate,
  "delivered_at": null | ISODate,
  "outcome_at": null | ISODate
}
```

**索引**:

```javascript
// Upsert 查询
db.interventions.createIndex({ "id": 1 }, { unique: true })

// Session 查询
db.interventions.createIndex({ "session_id": 1, "created_at": -1 })

// Student 查询
db.interventions.createIndex({ "student_id": 1 })
```

### 7.3 典型查询模式

```python
# 获取 session 最新 context
await collection.find_one({"session_id": session_id}, sort=[("updated_at", -1)])

# 获取 session 所有 interventions（按时间排序）
cursor = collection.find({"session_id": session_id}).sort("created_at", -1)

# 按 student_id 统计干预次数
await collection.count_documents({"student_id": student_id})

# 获取最近活跃 sessions
cursor = collection.find().sort("updated_at", -1).limit(100)
```

---

## 8. 代码结构（Code Structure）

```
backend/app/modules/intervention/
│
├── __init__.py                      # 模块导出
├── module.py                        # 模块入口（initialize/shutdown/router 注册）
├── routes.py                        # FastAPI 路由（7个端点）
├── service.py                       # 主服务编排（InterventionService）
├── models.py                        # Pydantic + dataclass 模型
│
├── context_manager.py               # 状态管理 + MongoDB 持久化
│
├── locator/                         # 节点 1：断点定位（纯规则）
│   ├── __init__.py
│   ├── breaker.py                   # BreakpointLocator（三级级联匹配）
│   └── models.py                    # BreakpointLocation, BreakpointType, MatchResult
│
├── router/                          # 节点 2a：维度路由
│   ├── __init__.py
│   ├── dimension_router.py          # DimensionRouter（LLM R/M 分类）
│   ├── models.py                    # DimensionResult, DimensionEnum
│   └── prompts.py                   # DIMENSION_ROUTER_PROMPT
│
├── decider/                         # 节点 2b：子类型决策
│   ├── __init__.py
│   ├── sub_type_decider.py          # SubTypeDecider（LLM 级别决策）
│   ├── models.py                    # SubTypeResult, PromptLevelEnum, EscalationDecision
│   └── prompts.py                   # RESOURCE_DECIDER_PROMPT, METACOGNITIVE_DECIDER_PROMPT
│
├── generator/                       # 节点 4：提示生成
│   ├── __init__.py
│   ├── hints_v2.py                  # HintGeneratorV2（R1-R4/M1-M5 提示模板）
│   ├── models.py
│   └── prompts.py                   # 各等级提示词模板
│
├── guardrail/                       # 节点 5：输出护栏
│   ├── __init__.py
│   ├── guardrail.py                 # OutputGuardrail（双层检查）
│   ├── models.py                    # GuardrailResult
│   └── prompts.py                   # GUARDRAIL_PROMPT, RULES
│
├── prompts/                         # 共享提示词
│   ├── __init__.py
│   ├── hint.py
│   ├── intensity.py
│   ├── decision.py
│   ├── analysis.py
│   └── location.py
│
└── infrastructure/
    └── database/
        └── repositories/
            └── intervention_repo.py  # MongoDB 持久化层

backend/app/infrastructure/database/
├── mongodb.py                       # MongoDB 连接管理（Motor）
└── repositories/
    └── intervention_repo.py         # 干预持久化仓储
```

---

## 附录 A: 文件清单

| 文件路径 | 行数 | 职责 |
|----------|------|------|
| `service.py` | 1028 | 主管道编排 |
| `context_manager.py` | 656 | 状态管理与持久化 |
| `models.py` | 299 | 数据模型 |
| `locator/breaker.py` | 371 | 三级级联断点定位 |
| `router/dimension_router.py` | 136 | 维度路由 |
| `decider/sub_type_decider.py` | 226 | 子类型决策 |
| `generator/hints_v2.py` | 489 | 提示生成 |
| `guardrail/guardrail.py` | 159 | 双层护栏 |
| `infrastructure/database/repositories/intervention_repo.py` | 409 | MongoDB 持久化 |

**总计**: ~3,800 行

---

## 附录 B: API 端点汇总

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/interventions` | 创建新干预 |
| POST | `/interventions/feedback` | 处理学生反馈 |
| POST | `/interventions/end` | 结束干预 |
| POST | `/interventions/escalate` | 强制升级 |
| GET | `/interventions/{id}` | 获取干预详情 |
| GET | `/interventions/session/{session_id}` | 获取 session 所有干预 |
| GET | `/interventions/student/{student_id}` | 获取学生所有干预 |

---

## 附录 C: 升级路径图

```
                    ┌─────────────────────────────────────────────┐
                    │              干预开始                        │
                    └─────────────────────────────────────────────┘
                                         │
                    ┌───────────────────┴───────────────────┐
                    ▼                                       ▼
            ┌──────────────┐                         ┌──────────────┐
            │  RESOURCE 侧  │                         │ METACOGNITIVE侧 │
            └──────────────┘                         └──────────────┘
                    │                                       │
         R1 ──► R2 ──► R3 ──► R4                      M1 ──► M2 ──► M3 ──► M4 ──► M5
                    │                     ↖                     │
                    │                     │                     │
                    └───── R4 失败 ──────┘                     │
                              │                                 │
                              ▼                                 │
                    ┌──────────────────┐                       │
                    │   SWITCH_TO_R     │                       │
                    │   (切换到 R1)     │                       │
                    └──────────────────┘                       │
                              │                                 │
                              ▼                                 ▼
                    ┌─────────────────────────────────────────┐
                    │           达到最高级 → TERMINATE          │
                    └─────────────────────────────────────────┘
```
