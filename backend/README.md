# Math Tutor Backend

高中数学教辅系统后端，基于 FastAPI + MongoDB 构建。

## 项目结构

```
backend/
├── app/
│   ├── api/               # API 路由层
│   ├── core/              # 核心框架（context, events, orchestrator, registry, state）
│   ├── infrastructure/     # 基础设施层
│   │   ├── database/      # MongoDB 连接管理
│   │   └── llm/           # LLM 客户端（DashScope）
│   ├── modules/           # 业务模块
│   │   ├── solving/        # Module 1: 组织化解主治线生成
│   │   ├── intervention/   # Module 2: 错误干预
│   │   ├── recommendation/  # Module 3: 学习推荐
│   │   ├── student_model/  # Module 4: 学生画像
│   │   └── teaching/       # Module 5: 教学策略
│   ├── shared/             # 共享工具
│   ├── config.py           # 配置管理
│   └── main.py            # 应用入口
├── tests/                 # 测试套件
│   ├── modules/           # 模块测试
│   │   └── test_solving/  # Solving 模块测试
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
