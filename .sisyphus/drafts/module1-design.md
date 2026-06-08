# 模块一设计文档

## 1. 模块定位

### 1.1 核心目标
**输入**：数学题目(LaTeX) + 学生已完成部分(LaTeX，可选)
**输出**：带有推进功能的组织化"参考解主治线"

### 1.2 核心价值
- 不是只给答案，而是展示**解题过程的组织**
- 帮助学生看懂：题目如何理解、已知与所求缺什么、为什么选这条路、问题如何转化推进

### 1.3 设计理念
```
学生输入
  ↓
题干 + 学生已完成部分
  ↓
┌─────────────────────────────┐
│         评估层              │
│  检查学生解答是否正确        │
└──────────────┬──────────────┘
               │
    ┌──────────┴──────────┐
    ↓                      ↓
正确分支                    错误分支
补完主线                    返回错误提示
    ↓                      ↓
┌─────────────────────────────┐
│         生成层              │
│  输出参考解主治线           │
└──────────────┬──────────────┘
               ↓
         流向模块二
```

---

## 2. 数据模型

### 2.1 输入/输出模型

```python
class SolvingRequest(BaseModel):
    problem: str                    # LaTeX 题干
    student_work: Optional[str]    # LaTeX 学生已完成部分
    model: str = "qwen-turbo"      # 使用的模型
    temperature: float = 0.7      # 温度参数

class SolvingResponse(BaseModel):
    success: bool                  # 是否成功
    evaluation: EvaluationResult   # 评估结果
    solution: Optional[ReferenceSolution]  # 完整解法(评估通过时)
    error_feedback: Optional[ErrorFeedback]  # 错误提示(评估未通过时)
```

### 2.2 评估模型

```python
class EvaluationResult(BaseModel):
    is_correct: bool               # 学生解答是否正确
    confidence: float             # 评估置信度 [0, 1]
    issues: List[Issue]           # 发现的问题列表
    can_continue: bool              # 是否可以继续生成
    breakpoint_step: Optional[int]  # 断点步骤号

class Issue(BaseModel):
    step: Optional[int]           # 涉及的步骤号
    location: str                 # 问题位置描述
    description: str                # 问题描述
    severity: str                  # error / warning / hint
```

### 2.3 参考解法模型

```python
class ReferenceSolution(BaseModel):
    problem: str                    # 原始题目
    generated_at: datetime         # 生成时间
    
    # 四步框架
    orientation: Orientation       # 问题定向
    reconstruction: Reconstruction  # 关系重构
    formalization: Formalization   # 形式化归
    verification: Verification     # 结果审查
    
    steps: List[SolutionStep]       # 关键步骤
    actions: List[ProblemAction]    # 核心解题动作
    teaching_summary: str          # 教学总结
    
    # 元信息
    student_work_included: bool     # 是否包含学生工作
    breakpoint: Optional[int]       # 从第几步继续

class Orientation(BaseModel):
    target: str                    # 目标/已知/所求
    core_info: List[str]           # 核心信息
    difficulty: str                # 真正困难点
    observation: str                # 关键观察点
```

---

## 3. API设计

### 3.1 端点

```
POST /solving/reference
```

### 3.2 请求格式

```json
{
  "problem": "求函数 $f(x) = x^2 - 4x + 3$ 的导数",
  "student_work": "解：$f'(x) = \\lim_{h \\to 0} \\frac{f(x+h) - f(x)}{h}$",
  "model": "qwen-turbo",
  "temperature": 0.7
}
```

### 3.3 响应格式

```json
{
  "success": true,
  "evaluation": {
    "is_correct": true,
    "confidence": 0.95,
    "issues": [],
    "can_continue": true,
    "breakpoint_step": null
  },
  "solution": {
    "problem": "求函数...",
    "generated_at": "2026-03-23T06:37:12",
    "orientation": {...},
    "reconstruction": {...},
    "formalization": {...},
    "verification": {...},
    "steps": [...],
    "actions": [...],
    "teaching_summary": "...",
    "student_work_included": false,
    "breakpoint": null
  },
  "error_feedback": null
}
```

---

## 4. 核心流程

```
┌─────────────────────────────────────────────────────────────┐
│                    ReferenceSolutionService.generate()       │
└──────────────────────────┬────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Evaluator.evaluate_student_work()                   │
│  - 如果无学生工作 → is_correct=True, can_continue=True       │
│  - 如果有学生工作 → LLM评估或规则评估                          │
└──────────────────────────┬────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ↓                         ↓
    ┌──────────────────┐      ┌──────────────────┐
    │ is_correct=True  │      │ is_correct=False │
    └────────┬─────────┘      └────────┬─────────┘
             │                           │
             ▼                           ▼
    ┌──────────────────┐      ┌──────────────────┐
    │ 构建提示词        │      │ 创建ErrorFeedback │
    │ PromptDirector    │      │ 返回错误提示      │
    └────────┬─────────┘      └──────────────────┘
             │
             ▼
    ┌──────────────────┐
    │ LLM.chat()       │
    │ DashScopeClient  │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ SolutionParser   │
    │ 解析为结构化模型  │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ 返回SolvingResponse│
    └──────────────────┘
```

---

## 5. 提示词设计

### 5.1 提示词来源
所有提示词内容来自 `计划.md` 的"角色设定"和"四步讲解框架"。

### 5.2 提示词组装

```
PromptDirector.build_base_prompt()
  ├── SYSTEM_PROMPT (角色设定)
  ├── THINKING_TASKS_PROMPT (四项思维任务)
  ├── ACTIONS_PROMPT (七种解题动作)
  ├── OUTPUT_FORMAT_PROMPT (输出要求)
  └── PROHIBITIONS_PROMPT (明确禁止)
```

### 5.3 提示词模板结构

```python
# prompts/templates/system.py
SYSTEM_PROMPT = """
# 角色设定
你是一名**高中数学教辅老师**。
你的任务不是只给出答案，而是示范一种**清楚、严谨、可迁移的数学解题思考**。
...
"""

# prompts/templates/thinking_tasks.py
THINKING_TASKS_PROMPT = """
# 一、讲解时必须完成的四项思维任务

## 1. 问题定向
先澄清这道题究竟要求什么，以及题目已经给了什么。

## 2. 关系重构
说明已知与目标之间还缺少什么，以及准备如何建立联系。

## 3. 形式化归
把问题转化为可推进、可判定、可完成的形式。

## 4. 结果审查
检验结论是否真实、完整并且与原问题一致。
...
"""

# prompts/templates/actions.py
ACTIONS_PROMPT = """
# 二、优先采用的普遍解题动作

## 1. 观察结构
## 2. 寻找联系
## 3. 化生为熟
## 4. 抓关键限制
## 5. 适时分类
## 6. 构造与替换
## 7. 特殊化、边界化与回验
"""

# prompts/templates/output_format.py
OUTPUT_FORMAT_PROMPT = """
# 三、输出要求

## 1. 开头先讲"这题怎么看"
## 2. 中间展开"这题怎么想开"
## 3. 结尾讲"这题留下什么方法"
"""

# prompts/templates/prohibitions.py
PROHIBITIONS_PROMPT = """
# 五、明确禁止
- 不要只给答案，不解释思路如何形成；
- 不要把讲解写成纯公式流水账；
- ...
"""
```

### 5.4 完整提示词示例

```python
def build_full_solution_prompt(self, problem: str) -> str:
    base = self.build_base_prompt()
    return f"""{base}

---
现在，请对以下题目进行完整讲解。

题目：
{problem}

请按照上述要求进行讲解。
"""
```

---

## 6. 组件关系

```
SolvingModule
    │
    ├── register_routes()
    │       │
    │       └── router.include_router(solving_routes.router)
    │
    └── initialize()
            │
            ▼
    ┌───────────────────────────────────────┐
    │        SolvingService (routes.py)       │
    │  POST /solving/reference              │
    └──────────────────┬────────────────────┘
                       │
                       ▼
    ┌───────────────────────────────────────┐
    │   ReferenceSolutionService (service.py) │
    │                                        │
    │  ┌─────────────┐  ┌──────────────┐    │
    │  │ Evaluator  │  │ PromptDirector│    │
    │  └──────┬──────┘  └──────┬───────┘    │
    │         │                │            │
    │         └────────┬───────┘            │
    │                  ▼                    │
    │         ┌──────────────┐              │
    │         │SolutionParser │              │
    │         └──────┬───────┘              │
    │                │                      │
    │                ▼                      │
    │         ┌──────────────┐              │
    │         │DashScopeClient│              │
    │         └──────────────┘              │
    └───────────────────────────────────────┘
```

---

## 7. 配置项

```python
# config.py

# DashScope 配置
DASHSCOPE_API_KEY: Optional[str] = None
DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# 各模块使用的模型
SOLVING_MODEL: str = "qwen-turbo"         # 模块一：组织化解主治线
INTERVENTION_MODEL: str = "qwen-turbo"     # 模块二：断点干预
```

---

## 8. 当前状态

### 8.1 已实现

| 组件 | 文件 | 状态 |
|------|------|------|
| 数据模型 | `models.py` | ✅ 完成 |
| 提示词模板 | `prompts/templates/*.py` | ✅ 完成 |
| PromptDirector | `prompts/director.py` | ✅ 完成 |
| PromptBuilder | `prompts/builder.py` | ✅ 完成 |
| SolutionParser | `parser.py` | ✅ 完成（简化版） |
| Evaluator | `evaluator.py` | ✅ 完成 |
| ReferenceSolutionService | `service.py` | ✅ 完成 |
| API端点 | `routes.py` | ✅ 完成 |
| Module初始化 | `module.py` | ✅ 完成 |

### 8.2 已知限制

1. **Parser简化实现**: 当前parser对于非结构化LLM输出会产生空steps/actions
   - 建议：生产环境使用JSON模式

2. **评估使用规则**: 当前`Evaluator._evaluate_with_rules()`是简化实现
   - 建议：接入LLM进行更准确的评估

3. **EventBus未集成**: 当前不发布solving事件
   - 建议：模块二需要时接入

---

## 9. 后续优化建议

### 9.1 Parser优化
```
方案A: 使用JSON模式
- LLM输出格式化为JSON
- Parser直接解析JSON

方案B: 改进文本解析
- 使用更复杂的正则匹配
- 引入NLP处理
```

### 9.2 评估增强
```
方案A: LLM评估
- 调用LLM评估学生工作正确性
- 返回详细错误分析

方案B: 规则+LLM混合
- 简单情况用规则
- 复杂情况用LLM
```

### 9.3 流式输出
```
如果需要逐步展示解题过程：
- 使用 chat_stream() 替代 chat()
- SSE推送实现实时展示
```

---

## 10. 测试验证

### 10.1 端到端测试

```bash
# 测试请求
curl -X POST http://localhost:8000/api/v1/solving/reference \
  -H "Content-Type: application/json" \
  -d '{
    "problem": "求函数 $f(x) = x^2 - 4x + 3$ 的导数",
    "student_work": null,
    "temperature": 0.7
  }'

# 预期响应
{
  "success": true,
  "evaluation": {
    "is_correct": true,
    "confidence": 1.0,
    ...
  },
  "solution": {
    "orientation": {...},
    ...
  }
}
```

### 10.2 评估测试

```python
# 学生工作有误
evaluation = await evaluator.evaluate_student_work(
    problem="求 x^2 = 4 的解",
    student_work="x = 3"  # 错误
)
assert evaluation.is_correct == False
assert len(evaluation.issues) > 0
```

---

## 11. 文件清单

```
backend/app/modules/solving/
├── __init__.py
├── models.py                      # 数据模型
├── service.py                     # ReferenceSolutionService
├── parser.py                      # SolutionParser
├── evaluator.py                   # Evaluator
├── routes.py                      # API端点
├── module.py                      # Module接口
│
└── prompts/
    ├── __init__.py
    ├── director.py                # PromptDirector
    ├── builder.py                 # PromptBuilder
    └── templates/
        ├── __init__.py
        ├── system.py              # SYSTEM_PROMPT
        ├── thinking_tasks.py      # THINKING_TASKS_PROMPT
        ├── actions.py             # ACTIONS_PROMPT
        ├── output_format.py       # OUTPUT_FORMAT_PROMPT
        └── prohibitions.py        # PROHIBITIONS_PROMPT
```
