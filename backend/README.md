# Math Tutor Backend

高中数学教辅系统后端，基于 FastAPI + MongoDB 构建。

## 项目结构

```
backend/
├── app/
│   ├── api/               # API 路由层
│   ├── core/              # 核心框架（context, events, orchestrator, registry, state）
│   ├── infrastructure/    # 基础设施层
│   │   ├── database/      # MongoDB 连接管理
│   │   └── llm/           # LLM 客户端（DashScope）
│   ├── modules/           # 业务模块
│   │   ├── solving/        # Module 1: 组织化解主治线生成
│   │   ├── intervention/   # Module 2: 错误干预
│   │   ├── recommendation/ # Module 3: 学习推荐
│   │   ├── student_model/  # Module 4: 学生画像
│   │   └── teaching/       # Module 5: 教学策略
│   ├── shared/             # 共享工具
│   ├── config.py           # 配置管理
│   └── main.py            # 应用入口
├── tests/                 # 测试套件
│   ├── modules/           # 模块测试
│   │   ├── test_solving/  # Solving 模块测试
│   │   └── test_intervention/ # Intervention 模块测试
│   ├── core/              # 核心框架测试
│   └── integration/       # 集成测试
├── prompts/               # 提示词工程
└── pyproject.toml
```

## 模块概览

| 模块     | 名称               | 状态      |
| -------- | ------------------ | --------- |
| Module 1 | 组织化解主治线生成 | ✅ 已实现 |
| Module 2 | 错误干预           | ✅ 已实现 |
| Module 3 | 学习推荐           | 🔨 开发中 |
| Module 4 | 学生画像           | 🔨 开发中 |
| Module 5 | 教学策略           | 🔨 开发中 |

## 快速开始

```bash
# 安装依赖
cd backend
pip install -e ".[dev]"

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 DASHSCOPE_API_KEY

# 运行开发服务器
uvicorn app.main:app --reload

# 运行测试
python -m pytest tests/ -v --ignore=tests/e2e
```

## Module 1: Solving（解题模块）

### 核心能力

接收 LaTeX 题目（可选学生已作答内容），评估学生解答正确性，返回结构化的参考解法或错误反馈。

### API 接口

**`POST /solving/reference`**

```bash
curl -X POST http://localhost:8000/solving/reference \
  -H "Content-Type: application/json" \
  -d '{
    "problem": "设 $a_0, a_1, \\ldots$ 是正整数序列...",
    "student_work": null,
    "model": "qwen-turbo",
    "temperature": 0.7
  }'
```

**请求体**

| 字段              | 类型    | 必填 | 说明                        |
| ----------------- | ------- | ---- | --------------------------- |
| `problem`         | `str`   | ✅   | LaTeX 题干                  |
| `student_work`    | `str`   | ❌   | LaTeX 学生已作答内容        |
| `model`           | `str`   | ❌   | 模型名，默认 `qwen-turbo`   |
| `temperature`     | `float` | ❌   | 温度，默认 `0.7`            |
| `max_tokens`      | `int`   | ❌   | 最大生成长度，默认 `8192`   |
| `enable_thinking` | `bool`  | ❌   | 深度思考（qwen3.5-plus 等） |

**响应体**

| 字段             | 类型     | 说明                         |
| ---------------- | -------- | ---------------------------- |
| `success`        | `bool`   | 是否成功                     |
| `evaluation`     | `object` | 评估结果                     |
| `solution`       | `object` | 参考解法（success=True 时）  |
| `error_feedback` | `object` | 错误反馈（success=False 时） |

### 模型参数配置

| 模型           | temperature | max_tokens | enable_thinking |
| -------------- | ----------- | ---------- | --------------- |
| `qwen-turbo`   | 0.7         | 2048       | False           |
| `qwen3.5-plus` | 0.7         | 8192       | True            |

### LLM 输出格式

LLM 输出为**自然语言三段式**：

```
这题怎么看：
关键观察点、真正突破口、整体路径。

这题怎么想：
第一步：...（关键判断和转折点）
第二步：...
第三步：...

这题留下什么方法：
总结核心思维动作，点出最关键的一步。
```

### 详细文档

- [Module 1 详细文档](app/modules/solving/README.md)
- [Module 1 测试说明](tests/modules/test_solving/README.md)

## Module 2: Intervention（断点分层递进干预系统）

### 核心能力

基于 Module 1 生成的参考解法，定位学生断点，通过双维度诊断（Resource / Metacognitive）选择干预策略，生成递进式提示，引导学生自主跨越断点。

### 核心概念：双维度诊断

干预决策围绕两个维度展开：

| 维度              | 描述                               | 干预策略          |
| ----------------- | ---------------------------------- | ----------------- |
| **Resource**      | 学生缺乏知识或步骤（不知道怎么做） | 补充知识/方法     |
| **Metacognitive** | 学生有知识但未调用（知道但想不到） | 引导反思/策略激活 |

每个维度有多个递进级别（R1-R4 / M1-M5），当前级别未能帮助学生进步时，自动升级到下一级别。

### 五节点干预管道

```
学生请求干预
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│  ① BreakpointLocator（断点定位）                              │
│     纯逻辑计算，无需 LLM。三级语义匹配定位断点位置和类型        │
│                                                              │
│  ② DimensionRouter（维度路由 → Node 2a）                      │
│     判断断点属于 Resource 还是 Metacognitive 维度              │
│                                                              │
│  ③ SubTypeDecider（子类型决策 → Node 2b）                     │
│     在维度内部确定具体子类型（R1-R4 / M1-M5）和强度            │
│                                                              │
│  ④ HintGeneratorV2（提示生成）                                 │
│     基于子类型和强度生成提示，调用 LLM                         │
│                                                              │
│  ⑤ OutputGuardrail（输出守卫）                                │
│     检查提示是否包含答案、是否过于直接，必要时降级或替换       │
└──────────────────────────────────────────────────────────────┘
    │
    ▼
返回干预提示 / 升级 / 终止
```

### 提示递进级别

**Resource 维度（R）**

| 级别 | 强度范围 | 提示特点                         |
| ---- | -------- | -------------------------------- |
| R1   | 0.0-0.25 | 方向引导，不给任何具体内容       |
| R2   | 0.25-0.5 | 部分提示，揭示关键方向           |
| R3   | 0.5-0.75 | 接近完整的思路，关键步骤有提示   |
| R4   | 0.75-1.0 | 完整思路，但学生仍需自己完成计算 |

**Metacognitive 维度（M）**

| 级别 | 强度范围 | 提示特点                   |
| ---- | -------- | -------------------------- |
| M1   | 0.0-0.2  | 唤醒反思，不直接给解题方向 |
| M2   | 0.2-0.4  | 点出可能的策略方向         |
| M3   | 0.4-0.6  | 建议使用某种策略并说明原因 |
| M4   | 0.6-0.8  | 比较多种策略的优劣         |
| M5   | 0.8-1.0  | 引导学生比较并选择策略     |

### API 接口

**POST /interventions** — 创建干预

```bash
curl -X POST http://localhost:8000/interventions \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_001",
    "intensity": 0.5,
    "student_id": "student_001"
  }'
```

**POST /interventions/feedback** — 学生反馈（进步 / 未进步）

```bash
curl -X POST http://localhost:8000/interventions/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_001",
    "frontend_signal": "NOT_PROGRESSED",
    "student_input": "学生仍然卡在构造步骤"
  }'
```

**POST /interventions/end** — 结束干预

```bash
curl -X POST http://localhost:8000/interventions/end \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_001",
    "reason": "学生已掌握"
  }'
```

**POST /interventions/escalate** — 强制升级

```bash
curl -X POST http://localhost:8000/interventions/escalate \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_001",
    "reason": "学生要求更多帮助"
  }'
```

### 详细文档

- [Module 2 详细文档](app/modules/intervention/README.md)
- [Module 2 测试说明](tests/modules/test_intervention/README.md)

## 环境变量

| 变量                | 必填 | 说明                            |
| ------------------- | ---- | ------------------------------- |
| `DASHSCOPE_API_KEY` | ✅   | 阿里云 DashScope API Key        |
| `SOLVING_MODEL`     | ❌   | 解题默认模型，默认 `qwen-turbo` |
| `MONGODB_URI`       | ❌   | MongoDB 连接 URI                |

## 测试

```bash
# 单元测试
python -m pytest tests/modules/test_solving/test_solving.py -v
python -m pytest tests/modules/test_intervention/ -v

# 完整测试套件
python -m pytest tests/ -v --ignore=tests/e2e

# 带覆盖率
python -m pytest tests/ --cov=app --cov-report=term-missing
```

> **集成测试**：`tests/modules/test_integration/test_solving_intervention_connection.py`
> — 验证 Module 1 (Solving) → SessionState → Module 2 (Intervention) 的完整连接

## 技术栈

| 层级     | 技术                         |
| -------- | ---------------------------- |
| 框架     | FastAPI + Uvicorn            |
| 数据验证 | Pydantic v2                  |
| 数据库   | MongoDB + Motor（异步驱动）  |
| LLM      | DashScope（OpenAI 兼容接口） |
| 测试     | pytest + pytest-asyncio      |
| 代码质量 | ruff + black                 |
