# Module 1 设计文档：组织化解主治线生成

**版本**：v2.0  
**状态**：已完成实现  
**最后更新**：2026-03-30

---

## 1. 架构设计 (Architecture)

### 1.1 Module 1 在五模块管道中的位置

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              完整管道数据流                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐       │
│   │ Problem  │ ──── │ Module 1 │ ──── │ Module 2 │ ──── │Module 3/5│ ────► │
│   │ (LaTeX)  │      │  生成主线 │      │ 断点干预  │      │ 学习推荐  │       │
│   └──────────┘      └──────────┘      └──────────┘      └──────────┘       │
│        │                 │                 │                               │
│        ▼                 ▼                 ▼                               │
│   题目输入          SolutionMainline    BreakpointHints    ◄── Module 4   │
│                     (JSON结构化)          + 干预提示         学生画像      │
│                                              │                         │
│                                              ▼                         │
│                                       干预结果存储                           │
│                                       (SessionState)                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Module 1 的核心职责**：接收数学题目，生成一份**有教学价值的参考解法主线**（Teaching-Quality Reference Solution），作为 Module 2 进行断点分析的**全局基准**。

### 1.2 数据流详解

```
题目输入 (LaTeX/文本)
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  SolvingService.generate(request)                       │
│                                                         │
│  ① Evaluator.evaluate_student_work()                   │
│     - 无作答 → 标记为"直接生成"                         │
│     - 有作答 → 评估正确性                               │
│       ├─ 正确 → 进入 Prompt 构建                        │
│       └─ 错误 → 返回 ErrorFeedback，流程终止            │
│                                                         │
│  ② PromptDirector 构建 Prompt                           │
│     - 有学生作答 → build_continuation_prompt()          │
│     - 无学生作答 → build_full_solution_prompt()         │
│                                                         │
│  ③ DashScope LLM 调用                                    │
│     - Model: qwen-turbo / qwen3.5-plus                 │
│     - Temperature: 0.7 (可配置)                         │
│     - Output: 自然语言三段式                             │
│                                                         │
│  ④ SolutionParser 解析输出                              │
│     - 提取"这题怎么看"→ problem_understanding           │
│     - 提取"这题怎么想"→ solution_steps[]               │
│     - 提取"这题留下什么方法"→ method_summary           │
│                                                         │
│  ⑤ 存入 SessionState (若提供 session_id)               │
│     └─ Module 2 后续读取进行断点分析                     │
└─────────────────────────────────────────────────────────┘
         │
         ▼
  SolutionMainline (JSON)
  {
    "problem_understanding": "...",
    "solution_steps": [...],
    "method_summary": "...",
    "breakpoint_hints": [...]
  }
```

### 1.3 与 Module 2 的连接机制

Module 1 生成的主线解法通过 SessionState 传递给 Module 2：

```python
# Module 1: 生成后自动存储
state = {
    "problem": request.problem,
    "student_work": request.student_work or "",
    "student_steps": getattr(request, 'student_steps', []) or [],
    "solution_steps": [s.dict() for s in solution.steps],
}
self._context.state_manager.set_module_state(session_id, "solving", state)

# Module 2: 读取进行断点分析
solving_state = self._context.state_manager.get_module_state(session_id, "solving")
```

---

## 2. 组件设计 (Component Design)

### 2.1 LLM 客户端配置

| 参数 | 值 | 说明 |
|------|-----|------|
| **模型** | `qwen-turbo`（默认）/ `qwen3.5-plus` | 通过 `SOLVING_MODEL` 环境变量配置 |
| **temperature** | `0.7` | 平衡正确性与多样性 |
| **max_tokens** | `8192`（默认） | 最大生成长度 |
| **enable_thinking** | `False`（默认） | qwen3.5-plus 可开启深度思考 |
| **base_url** | `https://dashscope.aliyuncs.com/compatible-mode/v1` | DashScope OpenAI 兼容端点 |
| **timeout** | `120.0` 秒 | 请求超时时间 |
| **max_retries** | `3` | API 自动重试次数 |

```python
# backend/app/modules/solving/service.py
class ReferenceSolutionService:
    def _get_llm_client(self) -> DashScopeClient:
        if self._llm_client is None:
            api_key = os.getenv("DASHSCOPE_API_KEY")
            model = os.getenv("SOLVING_MODEL", "qwen-turbo")
            self._llm_client = DashScopeClient(api_key=api_key, model=model)
        return self._llm_client
```

### 2.2 Prompt 构建

Prompt 由 `PromptDirector` 组装，包含以下组件：

| 组件 | 文件 | 内容 |
|------|------|------|
| 系统角色 | `templates/system.py` | 高中数学教辅老师角色定义 |
| 四项思维任务 | `templates/thinking_tasks.py` | 问题定向、关系重构、形式化归、结果审查 |
| 七种解题动作 | `templates/actions.py` | 观察结构、寻找联系、化生为熟等 |
| 输出格式 | `templates/output_format.py` | 三段式：怎么看/怎么想/留下什么 |
| 语言风格 | `templates/language_style.py` | 自然、清楚、严谨的教学语言 |
| 禁止事项 | `templates/prohibitions.py` | 明确禁止的行为 |

```python
# backend/app/modules/solving/prompts/director.py
class PromptDirector:
    def build_base_prompt(self) -> str:
        parts = [
            SYSTEM_PROMPT,
            THINKING_TASKS_PROMPT,
            ACTIONS_PROMPT,
            OUTPUT_FORMAT_PROMPT,
            LANGUAGE_STYLE_PROMPT,
            PROHIBITIONS_PROMPT,
        ]
        return "\n".join(parts)
```

### 2.3 输出解析

`SolutionParser` 负责将 LLM 的自然语言输出解析为结构化的 `ReferenceSolution`：

```python
# backend/app/modules/solving/parser.py
class SolutionParser:
    def parse(self, llm_output: str, problem: str) -> ReferenceSolution:
        sections = self._split_sections(llm_output)  # 三段式切分
        steps = self._parse_steps(sections)          # 提取步骤
        answer = self._extract_answer(sections)      # 提取答案/总结

        return ReferenceSolution(
            problem=problem,
            answer=answer,
            generated_at=datetime.now(timezone.utc),
            steps=steps,
        )
```

**解析策略**：
- 正则匹配"这题怎么看"、"这题怎么想"、"这题留下什么方法"三个section
- 对"这题怎么想"部分，识别多级步骤格式（"第一步"、"1."等）
- 若无明显步骤格式，将段落作为fallback步骤

### 2.4 重试逻辑

| 错误类型 | 处理策略 |
|---------|---------|
| **API 错误**（网络、超时） | DashScopeClient 内置 3 次自动重试 |
| **LLM 输出格式错误**（无法解析三段式） | 解析器返回空 steps，service 层记录 error 但不重试 |
| **解析失败**（结构不完整） | 当前版本：返回部分数据，不触发重试 |
| **Temperature 过低导致重复** | 在 `SolvingRequest` 中可调整 temperature |

**未来优化方向**：
- 实现解析失败时的结构化 JSON 重试（`response_format={"type": "json_object"}`）
- 增加最大重试次数配置

---

## 3. 提示词工程 (Prompt Engineering)

### 3.1 System Prompt 结构

```markdown
你是一名高中数学教辅老师。你的任务不是只给出答案，也不是只展示演算过程，
而是示范一种清楚、严谨、可迁移的数学解题思考。

请始终以"解题过程的组织"为核心来讲解，而不是以固定模板、技巧堆砌或教材章节分类为核心。
你的目标是帮助学生看懂：
  - 题目一开始该如何理解
  - 已知与所求之间缺什么
  - 为什么选择这条路径
  - 问题是如何被转化并推进的
  - 最后又如何确认结论成立

现在开始，对我接下来提供的数学题，按上述要求进行讲解。
```

### 3.2 四项思维任务

| 序号 | 任务 | 核心问题 |
|-----|------|---------|
| 一 | 问题定向 | 这道题要求什么？已知什么？困难在哪？ |
| 二 | 关系重构 | 已知与目标之间缺什么联系？如何建立？ |
| 三 | 形式化归 | 如何转化为可推进、可判定的形式？ |
| 四 | 结果审查 | 结论是否真实、完整、与原题一致？ |

### 3.3 七种解题动作

1. **观察结构** — 对称、重复，配对、定值、边界、趋势
2. **寻找联系** — 搭桥、中间量、等价表达
3. **化生为熟** — 改写、配凑、拆分、合并、代换、统一结构
4. **抓关键限制** — 符号、范围、端点、极端情形、等号条件
5. **适时分类** — 分类标准来自核心矛盾
6. **构造与替换** — 设中间量、等价关系、补结构
7. **特殊化与回验** — 特殊值、极端情形、边界情形检验

### 3.4 输出格式（三段式）

```
这题怎么看：
用一段自然的话说明关键观察点、真正突破口、整体路径。不要一上来就写公式。

这题怎么想：
第一步：...
第二步：...
第三步：...
突出关键判断和转折点，对重要变形、分类、替换、构造要解释理由。
对学生容易误判的地方主动提醒。

这题留下什么方法：
总结最核心的思维动作，点出最关键的一步。
说明以后遇到类似题，优先从哪里想、先检查什么、先抓什么关系。
```

### 3.5 语言风格要求

- 语言自然、清楚、严谨，像真正帮助学生建立思维框架的老师
- 重点解释"为什么这样想"，不是只陈列"做了什么"
- 不用"显然""易知""不难发现"等表达跳过关键思维
- 优先选择最自然、最稳定、最有迁移价值的路径，不炫技，不绕路

### 3.6 明确禁止

- ❌ 只给答案，不解释思路形成
- ❌ 纯公式流水账
- ❌ 机械套用空洞模板
- ❌ 按教材章节标签组织
- ❌ 只报方法名，不说明原因
- ❌ 跳过真正的转折点
- ❌ 把试探/例证当作未经说明的一般证明

### 3.7 Temperature 设置理由

| Temperature | 特点 | 适用场景 |
|------------|------|---------|
| **0.7**（推荐） | 平衡正确性与多样性 | 标准解题讲解 |
| 0.5 | 更确定性，变化少 | 简单题、重复生成 |
| 0.9 | 更多样化，可能有创意 | 开放性探究题 |

**选择 0.7 的理由**：
- 数学解题需要**正确性**（temperature太低可能陷入固定模式）
- 同时需要**多样性**（不同题目需要不同的切入角度）
- 0.7 是经过实践验证的平衡点，既保证推理正确，又能产生有教学价值的不同思路

---

## 4. 输出结构设计 (Output Schema)

### 4.1 目标输出 Schema（Module 1 → Module 2 接口）

```json
{
  "problem_understanding": "这题怎么看",
  "solution_steps": [
    {
      "step_id": 1,
      "action": "观察结构",
      "description": "步骤描述",
      "reasoning": "为什么这样做",
      "key_insight": "突破性洞见"
    }
  ],
  "method_summary": "方法总结",
  "breakpoint_hints": [
    {
      "step_id": 2,
      "potential_breakpoint": "可能在哪个点卡住",
      "dimension": "Resource",
      "suggested_hint_type": "R2"
    }
  ]
}
```

### 4.2 当前实现 Schema（ReferenceSolution）

```python
# backend/app/modules/solving/models.py

class TeachingStep(BaseModel):
    """教学步骤"""
    step_id: str = Field(..., description="步骤ID，如 s1, s2, s3")
    step_name: str = Field(..., description="步骤名称")
    content: str = Field(..., description="步骤内容")

class ReferenceSolution(BaseModel):
    """完整参考解法"""
    problem: str = Field(..., description="原始题目(LaTeX)")
    answer: Optional[str] = Field(None, description="答案")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="生成时间")
    steps: List[TeachingStep] = Field(default_factory=list, description="教学步骤列表")
```

### 4.3 Schema 对比与演进计划

| 字段（目标） | 当前字段 | 状态 | 说明 |
|------------|---------|------|------|
| `problem_understanding` | 无 | ❌ 需新增 | 从"这题怎么看"提取 |
| `solution_steps[].action` | 无 | ❌ 需新增 | LLM 输出中标注解题动作 |
| `solution_steps[].reasoning` | `content` | ⚠️ 部分覆盖 | 需在 prompt 中要求 |
| `solution_steps[].key_insight` | 无 | ❌ 需新增 | 识别关键突破点 |
| `method_summary` | `answer` | ⚠️ 部分覆盖 | 当前解析到"这题留下什么方法" |
| `breakpoint_hints` | 无 | ❌ 需新增 | 这是 Module 2 的输入，Module 1 只需提供原始素材 |

**演进说明**：
- 当前实现已能提取 `steps`、`problem_understanding`（通过解析"这题怎么看"）、`method_summary`（通过解析"这题留下什么方法"）
- `action`、`reasoning`、`key_insight` 需要在 **Prompt 中要求 LLM 输出结构化 JSON** 或在解析时进一步标注
- `breakpoint_hints` 属于 Module 2 的职责，Module 1 提供足够丰富的步骤信息供 Module 2 分析

---

## 5. 关键设计决策 (Key Design Decisions)

### 5.1 为什么用自然语言三段式而非纯 JSON？

| 方案 | 优点 | 缺点 |
|------|------|------|
| **自然语言三段式（当前）** | 教学自然流畅；人类可读性好；LLM 易于生成 | 解析需正则匹配；结构精度依赖 prompt |
| **纯 JSON（备选）** | 结构精确；易于程序处理 | JSON 结构限制表达；LLM 生成不自然；模板感强 |

**决策理由**：
1. **Module 1 的核心目标是教学**，而非数据交换
2. 数学解题讲解是**连贯的思维过程**，用自然段落表达更符合教学本质
3. Module 2 需要的是**步骤序列**，解析器可以将自然语言步骤转化为结构化数据
4. 未来如需更精确的结构，可要求 LLM 输出 **Markdown 内嵌 JSON** 或 **JSON in code block**

### 5.2 为什么是四任务 + 七动作框架？

**四任务** 来自学习科学研究：
- **问题定向**：激活相关先前知识，确定解题方向
- **关系重构**：建立已知与未知的联系
- **形式化归**：将问题转化为可操作的数学形式
- **结果审查**：验证解答正确性，培养元认知

**七动作** 是通用解题策略，不依赖具体数学分支：
- 覆盖了从"看"到"做"到"验"的完整解题周期
- 与四任务形成"目标-手段"对应关系

**设计依据**：
- 该框架被证明能有效组织数学思维教学
- 与 Module 2 的断点分析维度（Resource / Metacognitive）形成良好映射

### 5.3 Temperature 0.7 的理由

见 3.7 节。总结：**平衡正确性与多样性，避免套路化，同时保证数学推理的严谨性**。

### 5.4 错误处理策略

| 场景 | 当前策略 | 未来优化 |
|------|---------|---------|
| API 网络错误 | DashScopeClient 内置 3 次重试 | 增加指数退避 |
| API 业务错误（rate limit 等） | 抛出异常，由 service 层捕获 | 增加专用异常类型和重试逻辑 |
| LLM 输出格式异常 | 解析器返回空/部分 steps | 增加 JSON 模式重试 |
| 解析失败 | 返回部分数据，流程继续 | 增加解析质量评分 |

---

## 6. 代码结构 (Code Structure)

### 6.1 文件布局

```
backend/app/modules/solving/
├── __init__.py              # 模块导出
├── module.py                # 模块初始化与注册
├── models.py                # 数据模型（Pydantic）
├── service.py               # 核心业务逻辑
├── parser.py                # LLM 输出解析器
├── evaluator.py             # 学生解答评估器
├── routes.py                # FastAPI 路由
├── pipeline.py              # 流程编排（预留）
└── prompts/                 # 提示词工程
    ├── __init__.py
    ├── director.py          # PromptDirector — 编排各模板
    ├── builder.py           # PromptBuilder — Chain 式构建
    ├── orientation.py       # 问题定向阶段（预留）
    ├── reconstruction.py    # 关系重构阶段（预留）
    ├── transformation.py    # 形式化归阶段（预留）
    ├── verification.py      # 结果审查阶段（预留）
    └── templates/           # 提示词模板常量
        ├── __init__.py
        ├── system.py        # 角色设定
        ├── thinking_tasks.py # 四项思维任务
        ├── actions.py       # 七种解题动作
        ├── output_format.py # 输出格式要求
        ├── language_style.py# 语言风格要求
        └── prohibitions.py  # 明确禁止
```

### 6.2 核心类：ReferenceSolutionService

```python
# backend/app/modules/solving/service.py

class ReferenceSolutionService:
    """生成参考解法的服务类。
    
    核心入口是 generate() 方法，协调评估、Prompt 构建、
    LLM 调用、解析整个流程。
    """

    def __init__(self, context: Optional["ModuleContext"] = None):
        self._context = context
        self._evaluator = Evaluator()
        self._parser = SolutionParser()
        self._director = PromptDirector()
        self._llm_client: Optional[DashScopeClient] = None

    def _get_llm_client(self) -> DashScopeClient:
        """获取或创建 LLM 客户端。"""
        ...

    async def generate(
        self,
        request: SolvingRequest,
        session_id: Optional[str] = None,
    ) -> SolvingResponse:
        """生成参考解法。
        
        Args:
            request: 解题请求（含题目和可选学生作答）
            session_id: 会话 ID（用于存储到 SessionState）
            
        Returns:
            SolvingResponse: 评估结果 + 解法（或错误反馈）
        """
        ...

    async def close(self) -> None:
        """关闭资源。"""
        ...
```

### 6.3 关键方法签名

```python
# 生成主线解法
async def generate_mainline(
    problem_text: str,
    student_work: Optional[str] = None,
    session_id: Optional[str] = None,
) -> SolutionMainline:
    """生成组织化解题主线。
    
    Args:
        problem_text: LaTeX 题目文本
        student_work: 学生已完成作答（可选）
        session_id: 会话 ID（用于 Module 2 连接）
        
    Returns:
        SolutionMainline: 结构化解法主线
    """
    request = SolvingRequest(
        problem=problem_text,
        student_work=student_work,
    )
    response = await self.generate(request, session_id)
    
    if not response.success:
        raise SolutionGenerationError(response.error_feedback)
    
    return SolutionMainline.from_reference_solution(response.solution)
```

### 6.4 数据模型

```python
# backend/app/modules/solving/models.py

class SolvingRequest(BaseModel):
    """解题请求"""
    problem: str                              # LaTeX 题干
    student_work: Optional[str] = None       # LaTeX 学生已完成部分
    model: str = "qwen-turbo"               # 使用的模型
    temperature: float = 0.7                  # 温度参数
    max_tokens: int = 8192                   # 最大生成长度
    enable_thinking: bool = False           # 启用深度思考


class SolvingResponse(BaseModel):
    """解题响应"""
    success: bool
    evaluation: "EvaluationResult"
    solution: Optional["ReferenceSolution"]
    error_feedback: Optional["ErrorFeedback"]


class ReferenceSolution(BaseModel):
    """参考解法"""
    problem: str
    answer: Optional[str]
    generated_at: datetime
    steps: List["TeachingStep"]


class TeachingStep(BaseModel):
    """教学步骤"""
    step_id: str     # s1, s2, s3...
    step_name: str
    content: str
```

### 6.5 依赖关系

```
┌─────────────────────────────────────────────┐
│         ReferenceSolutionService             │
│  ┌──────────┬──────────┬──────────┐         │
│  │Evaluator │ Parser   │ Director │         │
│  └────┬─────┴────┬─────┴────┬─────┘         │
│       │          │          │                │
│       ▼          ▼          ▼                │
│  ┌─────────┐ ┌─────────┐ ┌──────────┐       │
│  │ DashScope│ │自然语言  │ │Prompt    │       │
│  │ Client   │ │解析逻辑 │ │Templates │       │
│  └─────────┘ └─────────┘ └──────────┘       │
└─────────────────────────────────────────────┘
```

| 组件 | 依赖 | 说明 |
|------|------|------|
| `ReferenceSolutionService` | `Evaluator` | 评估学生作答正确性 |
| `ReferenceSolutionService` | `SolutionParser` | 解析 LLM 自然语言输出 |
| `ReferenceSolutionService` | `PromptDirector` | 构建解题提示词 |
| `ReferenceSolutionService` | `DashScopeClient` | LLM API 调用 |
| `PromptDirector` | 各 `*_PROMPT` 常量 | 模板组装 |

---

## 7. 测试策略 (Test Strategy)

### 7.1 测试分层

```
┌─────────────────────────────────────────────────────────────┐
│                    测试金字塔                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                        ┌─────────┐                          │
│                       │   E2E   │  ← 完整流程，端到端验证    │
│                       │  Tests  │    (人工抽检输出质量)      │
│                       └────┬────┘                          │
│                            │                               │
│                     ┌──────┴──────┐                        │
│                    │ Integration  │  ← Module1 + Module2   │
│                    │   Tests      │    连接测试              │
│                    └──────┬──────┘                        │
│                            │                               │
│              ┌─────────────┼─────────────┐                │
│              │             │             │                │
│        ┌─────┴─────┐ ┌─────┴─────┐ ┌─────┴─────┐          │
│       │ Unit Test │ │ Unit Test │ │ Unit Test │          │
│       │ (Parser)  │ │ (Director)│ │ (Evaluator)│          │
│       └───────────┘ └───────────┘ └───────────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 单元测试

#### 7.2.1 Prompt 解析测试

```python
# backend/tests/core/test_prompt_engine.py

class TestPromptDirector:
    def test_build_base_prompt_contains_all_components(self):
        director = PromptDirector()
        prompt = director.build_base_prompt()
        
        assert "高中数学教辅老师" in prompt
        assert "问题定向" in prompt
        assert "关系重构" in prompt
        assert "形式化归" in prompt
        assert "结果审查" in prompt
        assert "观察结构" in prompt
        assert "这题怎么看" in prompt
        assert "这题怎么想" in prompt
        assert "这题留下什么方法" in prompt

    def test_build_continuation_prompt_includes_student_work(self):
        director = PromptDirector()
        prompt = director.build_continuation_prompt(
            problem="题目",
            student_work="学生作答"
        )
        
        assert "题目" in prompt
        assert "学生作答" in prompt
        assert "继续" in prompt
```

#### 7.2.2 JSON Schema 验证测试

```python
# backend/tests/core/test_output_parser.py

class TestSolutionParser:
    def test_parse_three_section_format(self):
        parser = SolutionParser()
        llm_output = """这题怎么看：
这是一个关于数列的题目，关键在于观察递推关系。

这题怎么想：
第一步：写出递推公式
第二步：观察规律
第三步：得出通项

这题留下什么方法：
学会从递推关系推导通项公式。"""
        
        solution = parser.parse(llm_output, "原始题目")
        
        assert solution.problem == "原始题目"
        assert len(solution.steps) == 3
        assert solution.steps[0].step_id == "s1"
        assert solution.steps[0].step_name == "第一步"

    def test_parse_extracts_answer_from_conclusion(self):
        parser = SolutionParser()
        llm_output = """...
这题留下什么方法：
核心方法是配凑法，关键在于找到合适的辅助量。"""
        
        solution = parser.parse(llm_output, "题目")
        
        assert solution.answer is not None
        assert "配凑法" in solution.answer
```

### 7.3 集成测试

```python
# backend/tests/modules/test_integration/test_solving_intervention_connection.py

class TestModule1Module2Connection:
    async def test_solving_stores_state_for_intervention(self):
        """验证 Module 1 生成后正确存储到 SessionState。"""
        service = ReferenceSolutionService(context=self.mock_context)
        request = SolvingRequest(
            problem="设 $a_0, a_1, \\ldots$ 是正整数序列...",
            student_work=None,
        )
        
        response = await service.generate(request, session_id="test_session")
        
        assert response.success is True
        assert response.solution is not None
        assert len(response.solution.steps) > 0
        
        # 验证状态存储
        solving_state = self.mock_context.state_manager.get_module_state(
            "test_session", "solving"
        )
        assert solving_state["problem"] == request.problem
        assert "solution_steps" in solving_state
```

### 7.4 "正确性"的定义与验证

**Module 1 的特殊性**：数学正确性无法完全自动验证。

| 验证维度 | 方法 | 说明 |
|---------|------|------|
| **结构完整性** | Schema 验证 | 检查所有必填字段存在，类型正确 |
| **格式合规性** | 正则匹配 | 检查"这题怎么看"等标记存在 |
| **步骤数量** | 启发式 | 步骤数在 1-10 之间为合理 |
| **内容非空** | 字符串长度 | 每个步骤 content 长度 > 10 |
| **数学正确性** | 人工抽检 | 随机抽样 5% 输出，由教师审核 |
| **教学价值** | 人工抽检 | 检查是否有"为什么这样想"的解释 |

### 7.5 端到端测试（手动）

```python
# backend/tests/modules/test_solving/e2e_qwen35_manual.py

async def test_e2e_with_real_api():
    """手动 E2E 测试，需要真实 API key。
    
    运行方式：
    python -m pytest tests/modules/test_solving/e2e_qwen35_manual.py -v -s
    """
    import os
    os.environ["DASHSCOPE_API_KEY"] = "your-key-here"
    
    service = ReferenceSolutionService()
    
    test_cases = [
        "设 a_0, a_1, ... 是正整数序列，证明可以选择序列 (a_n) 使得每个非零自然数恰好等于 a_0, b_0, a_1, b_1, ... 中的一项。",
        "求函数 f(x) = x^3 - 3x + 1 的极值。",
        "证明：任意平面三角形的内角和为 180 度。",
    ]
    
    for problem in test_cases:
        request = SolvingRequest(problem=problem, temperature=0.7)
        response = await service.generate(request)
        
        print(f"\n{'='*60}")
        print(f"题目: {problem}")
        print(f"成功: {response.success}")
        if response.solution:
            print(f"步骤数: {len(response.solution.steps)}")
            for step in response.solution.steps:
                print(f"  [{step.step_id}] {step.step_name}: {step.content[:100]}...")
```

---

## 8. 扩展说明与未来优化

### 8.1 当前限制

1. **Parser 依赖固定格式**：若 LLM 输出格式略有变化，解析可能失败
2. **无结构化 JSON 输出选项**：自然语言输出难以保证 100% 结构一致性
3. **Evaluator 依赖规则**：复杂学生作答的评估可能不准确

### 8.2 计划中的优化

| 优化项 | 优先级 | 说明 |
|-------|-------|------|
| JSON Mode 输出 | 高 | 要求 LLM 输出结构化 JSON，提高解析稳定性 |
| Parser 质量评分 | 中 | 对解析结果打分，低于阈值时触发重试 |
| 多步解题管道 | 中 | Orientation → Reconstruction → Transformation → Verification 分阶段调用 |
| LLM Evaluator | 低 | 用 LLM 评估学生作答，提高准确性 |

### 8.3 与 Module 2 的深度集成

Module 1 生成的 `solution_steps` 将作为 Module 2 `BreakpointLocator` 的输入：

```python
# Module 2 读取 Module 1 的输出
solving_state = state_manager.get_module_state(session_id, "solving")
solution_steps = solving_state["solution_steps"]

# BreakpointLocator 分析每个步骤的潜在断点
for step in solution_steps:
    breakpoint_score = locator.calculate_breakpoint_score(
        step=step,
        student_level=student_profile["level"],
    )
    if breakpoint_score > threshold:
        breakpoints.append(Breakpoint(step_id=step["step_id"], ...))
```

---

## 附录 A：完整 Prompt 示例

```
你是一名高中数学教辅老师。你的任务不是只给出答案，也不是只展示演算过程，
而是示范一种清楚、严谨、可迁移的数学解题思考。

请始终以"解题过程的组织"为核心来讲解，而不是以固定模板、技巧堆砌或教材章节分类为核心。
你的目标是帮助学生看懂：题目一开始该如何理解，已知与所求之间缺什么，
为什么选择这条路径，问题是如何被转化并推进的，最后又如何确认结论成立。

一、优先完成的四项思维任务

无论题目属于什么内容，先完成这四项思维任务，再动手解题：

（一）问题定向 — 这道题要求什么？已知什么？困难在哪？
（二）关系重构 — 已知与目标之间缺什么联系？如何建立？
（三）形式化归 — 如何转化为可推进、可判定的形式？
（四）结果审查 — 结论是否真实、完整、与原题一致？

二、优先采用的普遍解题动作

无论题目属于什么内容，都优先从以下通用动作中寻找切入点：

1. 观察结构 — 对称、重复，配对、定值、边界、趋势
2. 寻找联系 — 搭桥、中间量、等价表达
3. 化生为熟 — 改写、配凑、拆分、合并、代换、统一结构
4. 抓关键限制 — 符号、范围、端点、极端情形、等号条件
5. 适时分类 — 分类标准来自核心矛盾
6. 构造与替换 — 设中间量、等价关系、补结构
7. 特殊化与回验 — 特殊值、极端情形、边界情形检验

三、输出要求

开头先讲"这题怎么看"
用一段自然的话说明关键观察点、真正突破口、整体路径。不要一上来就写公式。

中间展开"这题怎么想"
推导时突出关键判断和转折点。不要只堆算式。
对重要变形、分类、替换、构造要解释理由。
对学生容易误判的地方主动提醒。

结尾讲"这题留下什么方法"
总结最核心的思维动作。点出最关键的一步。
说明以后遇到类似题，优先从哪里想、先检查什么、先抓什么关系。

四、语言风格要求

- 语言自然、清楚、严谨，像真正帮助学生建立思维框架的老师
- 重点解释"为什么这样想"，不是只陈列"做了什么"
- 不用"显然""易知""不难发现"等表达跳过关键思维
- 优先选择最自然、最稳定、最有迁移价值的路径，不炫技，不绕路

五、明确禁止

- 只给答案，不解释思路形成
- 纯公式流水账
- 机械套用空洞模板
- 按教材章节标签组织
- 只报方法名，不说明原因
- 跳过真正的转折点
- 把试探/例证当作未经说明的一般证明

---

现在开始，对以下题目进行完整讲解。

题目：
设 $a_0, a_1, \ldots$ 是正整数序列，证明可以选择序列 $(a_n)$ 使得每个非零自然数恰好等于 $a_0, b_0, a_1, b_1, \ldots$ 中的一项。

请按照上述要求进行讲解。
```

---

## 附录 B：相关文件索引

| 文件 | 说明 |
|------|------|
| `backend/app/modules/solving/service.py` | 核心服务实现 |
| `backend/app/modules/solving/models.py` | 数据模型定义 |
| `backend/app/modules/solving/parser.py` | LLM 输出解析器 |
| `backend/app/modules/solving/evaluator.py` | 学生解答评估器 |
| `backend/app/modules/solving/prompts/director.py` | Prompt 编排器 |
| `backend/app/modules/solving/prompts/templates/*.py` | 各提示词模板 |
| `backend/app/infrastructure/llm/dashscope_client.py` | LLM 客户端实现 |
| `backend/tests/modules/test_solving/test_solving.py` | 单元测试 |
| `backend/tests/modules/test_integration/test_solving_intervention_connection.py` | 集成测试 |

---

**文档版本历史**：

| 版本 | 日期 | 修改说明 |
|-----|------|---------|
| v1.0 | 2026-03-01 | 初始版本 |
| v2.0 | 2026-03-30 | 增加 Module 2 连接机制、输出 Schema 演进计划、测试策略 |
