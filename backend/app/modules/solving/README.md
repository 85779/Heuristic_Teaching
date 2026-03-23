# Module 1: 组织化解主治线生成 (Organized Reference Solution Generation)

解题模块，接收 LaTeX 题目（可选学生已作答内容），评估学生解答正确性，返回结构化的参考解法或错误反馈。

## 模块结构

```
app/modules/solving/
├── models.py          # 数据模型（请求/响应/内部结构）
├── service.py         # 核心业务逻辑
├── parser.py          # LLM 输出解析器
├── evaluator.py       # 学生解答评估器
├── routes.py          # FastAPI 路由
├── module.py          # 模块初始化与注册
├── pipeline.py        # 流程编排（预留）
└── prompts/           # 提示词模板
    ├── director.py        # Prompt 编排器
    ├── builder.py         # Chain 式 Prompt 构建器
    ├── orientation.py     # 问题定向阶段（预留）
    ├── reconstruction.py # 关系重构阶段（预留）
    ├── transformation.py  # 形式化归阶段（预留）
    ├── verification.py    # 结果审查阶段（预留）
    └── templates/        # 提示词模板常量
        ├── system.py           # 角色设定 + 结尾引导语
        ├── thinking_tasks.py    # 四项思维任务
        ├── actions.py          # 七种解题动作
        ├── output_format.py    # 自然语言三段式输出要求
        ├── language_style.py   # 语言风格要求
        └── prohibitions.py      # 明确禁止
```

## 核心流程

```
请求 (SolvingRequest)
    │
    ▼
┌─────────────────────────┐
│   Evaluator.evaluate()  │  评估学生解答
│   - 无作答 → 直接生成    │
│   - 有作答 → 正确性判断  │
└────────────┬────────────┘
             │
    ┌────────┴────────┐
    ▼                 ▼
  正确               错误
    │                 │
    ▼                 ▼
┌─────────────────┐  ┌─────────────────┐
│ PromptDirector   │  │ ErrorFeedback   │
│ 构建解题 Prompt  │  │ 返回错误分析    │
└────────┬────────┘  └─────────────────┘
         │
         ▼
┌─────────────────┐
│  DashScope LLM  │  Text Mode（自然语言输出）
│  (qwen-turbo)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ SolutionParser  │
│ 解析自然语言输出 │
│ 提取步骤结构    │
└────────┬────────┘
         │
         ▼
    SolvingResponse
    (success + solution / error_feedback)
```

## API 接口

### `POST /solving/reference`

生成参考解法。

**请求体 (`SolvingRequest`)**

| 字段              | 类型    | 必填 | 说明                            |
| ----------------- | ------- | ---- | ------------------------------- |
| `problem`         | `str`   | ✅   | LaTeX 题干                      |
| `student_work`    | `str`   | ❌   | LaTeX 学生已作答内容            |
| `model`           | `str`   | ❌   | 模型名，默认 `qwen-turbo`       |
| `temperature`     | `float` | ❌   | 温度参数，默认 `0.7`            |
| `max_tokens`      | `int`   | ❌   | 最大生成长度，默认 `8192`       |
| `enable_thinking` | `bool`  | ❌   | 启用深度思考（qwen3.5-plus 等） |

**响应体 (`SolvingResponse`)**

| 字段             | 类型                | 说明                           |
| ---------------- | ------------------- | ------------------------------ |
| `success`        | `bool`              | 是否成功生成解法               |
| `evaluation`     | `EvaluationResult`  | 评估结果                       |
| `solution`       | `ReferenceSolution` | 参考解法（`success=True` 时）  |
| `error_feedback` | `ErrorFeedback`     | 错误反馈（`success=False` 时） |

**评估结果 (`EvaluationResult`)**

| 字段              | 类型          | 说明                   |
| ----------------- | ------------- | ---------------------- |
| `is_correct`      | `bool`        | 学生解答是否正确       |
| `confidence`      | `float`       | 评估置信度             |
| `issues`          | `List[Issue]` | 发现的问题列表         |
| `can_continue`    | `bool`        | 是否可以继续生成       |
| `breakpoint_step` | `int`         | 断点步骤号（可继续时） |

**参考解法 (`ReferenceSolution`)**

| 字段           | 类型                 | 说明              |
| -------------- | -------------------- | ----------------- |
| `problem`      | `str`                | 原始题目（LaTeX） |
| `answer`       | `str`                | 答案              |
| `generated_at` | `datetime`           | 生成时间          |
| `steps`        | `List[TeachingStep]` | 教学步骤列表      |

**教学步骤 (`TeachingStep`)**

| 字段        | 类型  | 说明                              |
| ----------- | ----- | --------------------------------- |
| `step_id`   | `str` | 步骤 ID，格式 `s1`, `s2`, `s3`... |
| `step_name` | `str` | 步骤名称                          |
| `content`   | `str` | 步骤内容                          |

**错误反馈 (`ErrorFeedback`)**

| 字段         | 类型          | 说明     |
| ------------ | ------------- | -------- |
| `summary`    | `str`         | 总体反馈 |
| `issues`     | `List[Issue]` | 问题列表 |
| `suggestion` | `str`         | 修正建议 |

## 数据模型

### `SolvingRequest`

```python
class SolvingRequest(BaseModel):
    problem: str                     # LaTeX 题干
    student_work: Optional[str] = None  # LaTeX 学生已作答
    model: str = "qwen-turbo"       # 模型名
    temperature: float = 0.7         # 温度
    max_tokens: int = 8192           # 最大生成长度
    enable_thinking: bool = False      # 启用深度思考
```

### `SolvingResponse`

```python
class SolvingResponse(BaseModel):
    success: bool
    evaluation: EvaluationResult
    solution: Optional[ReferenceSolution]
    error_feedback: Optional[ErrorFeedback]
```

### `ReferenceSolution`

```python
class ReferenceSolution(BaseModel):
    problem: str
    answer: Optional[str]
    generated_at: datetime
    steps: List[TeachingStep]  # 扁平列表 s1, s2, s3...
```

### `TeachingStep`

```python
class TeachingStep(BaseModel):
    step_id: str    # s1, s2, s3...（暂不分组）
    step_name: str
    content: str
```

## 提示词设计

### 系统角色

```
你是高中数学教辅老师。任务是示范清楚、严谨、可迁移的数学解题思考。
目标是帮助学生看懂：题目如何入手 → 已知与所求缺什么 → 为什么选这条路 → 如何推进 → 如何确认结论。
结尾引导语："现在开始，对我接下来提供的数学题，按上述要求进行讲解。"
```

### 四项思维任务

| 序号 | 任务     | 核心问题                             |
| ---- | -------- | ------------------------------------ |
| 一   | 问题定向 | 这道题要求什么？已知什么？困难在哪？ |
| 二   | 关系重构 | 已知与目标之间缺什么联系？如何建立？ |
| 三   | 形式化归 | 如何转化为可推进、可判定的形式？     |
| 四   | 结果审查 | 结论是否真实、完整、与原题一致？     |

### 七种解题动作

1. **观察结构** — 对称、重复，配对、定值、边界、趋势
2. **寻找联系** — 搭桥、中间量、等价表达
3. **化生为熟** — 改写、配凑、拆分、合并、代换、统一结构
4. **抓关键限制** — 符号、范围、端点、极端情形、等号条件
5. **适时分类** — 分类标准来自核心矛盾
6. **构造与替换** — 设中间量、等价关系、补结构
7. **特殊化与回验** — 特殊值、极端情形、边界情形检验

### 输出格式（自然语言三段式）

LLM 输出为自然语言，不是 JSON：

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

### 语言风格要求

- 语言自然、清楚、严谨，像真正帮助学生建立思维框架的老师
- 重点解释"为什么这样想"，不是只陈列"做了什么"
- 不用"显然""易知""不难发现"等表达跳过关键思维
- 优先选择最自然、最稳定、最有迁移价值的路径，不炫技，不绕路

### 明确禁止

- ❌ 只给答案，不解释思路形成
- ❌ 纯公式流水账
- ❌ 机械套用空洞模板
- ❌ 按教材章节标签组织
- ❌ 只报方法名，不说明原因
- ❌ 跳过真正的转折点
- ❌ 把试探/例证当作未经说明的一般证明

## 提示词模板组件

| 文件                | 内容                                             |
| ------------------- | ------------------------------------------------ |
| `system.py`         | 角色设定 + 结尾引导语                            |
| `thinking_tasks.py` | 四项思维任务（一、二、三、四）                   |
| `actions.py`        | 七种通用解题动作                                 |
| `output_format.py`  | 自然语言三段式输出要求（怎么看/怎么想/留下什么） |
| `language_style.py` | 语言风格要求                                     |
| `prohibitions.py`   | 明确禁止的行为                                   |
| `director.py`       | `PromptDirector` — 编排各模板组装完整 Prompt     |
| `builder.py`        | `PromptBuilder` — Chain 式 Prompt 构建器         |

## 各组件职责

| 组件           | 职责                                              |
| -------------- | ------------------------------------------------- |
| `service.py`   | 入口：协调评估、Prompt 构建、LLM 调用、解析       |
| `evaluator.py` | 评估学生解答正确性（规则 + LLM）                  |
| `parser.py`    | 解析 LLM JSON 输出为 `ReferenceSolution`          |
| `director.py`  | 组装各 Prompt 模板为完整提示词                    |
| `routes.py`    | 注册 FastAPI 路由，提供 `/solving/reference` 端点 |
| `module.py`    | 模块初始化、路由注册                              |

## 使用示例

```python
from app.modules.solving.models import SolvingRequest
from app.modules.solving.service import ReferenceSolutionService

service = ReferenceSolutionService()

# 无学生作答 → 直接生成完整解法
request = SolvingRequest(
    problem="设 $a_0, a_1, \\ldots$ 是正整数序列，证明可以选择序列 $(a_n)$ 使得每个非零自然数恰好等于 $a_0, b_0, a_1, b_1, \\ldots$ 中的一项。",
    student_work=None,
)

response = await service.generate(request)
# response.solution.steps → [TeachingStep(step_id="s1", ...), ...]

# 有学生作答 → 评估正确性或继续生成
request = SolvingRequest(
    problem="...",
    student_work="设 a_0 = 1，令 a_{n+1} = b_n × (n+2)。则 b_n = n+1。",
)
response = await service.generate(request)
# response.evaluation.is_correct → True/False
```

## 测试

```bash
# 运行 solving 模块测试
cd backend
python -m pytest tests/modules/test_solving/ -v

# 完整测试套件
python -m pytest tests/ -v --ignore=tests/e2e
```

详见 [`tests/modules/test_solving/README.md`](../tests/modules/test_solving/README.md)

## 环境变量

| 变量                | 必填 | 说明                        |
| ------------------- | ---- | --------------------------- |
| `DASHSCOPE_API_KEY` | ✅   | 阿里云 DashScope API Key    |
| `SOLVING_MODEL`     | ❌   | 解题模型，默认 `qwen-turbo` |

## 扩展说明

- **step_id 格式**：当前为扁平 `s1, s2, s3`...，分组逻辑由后续专门模块处理
- **Orientation/Reconstruction/Transformation/Verification 阶段**：`prompts/` 下四个阶段类均预留，LLM 多轮调用时启用
- **MongoDB**：当前 `mongodb.py` 为预留基础设施，session 持久化待实现
- **Evaluator**：当前默认基于规则的启发式评估，生产环境建议切换为 LLM 评估以提高准确率
