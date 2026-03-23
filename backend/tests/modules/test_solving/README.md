# Solving Module Tests

解题模块的测试套件，验证 Module 1（组织化解主治线生成）的核心功能。

## 运行测试

```bash
# 运行所有 solving 模块测试（单元测试）
cd backend
python -m pytest tests/modules/test_solving/test_solving.py -v

# 运行完整测试套件（不含 e2e）
python -m pytest tests/ -v --ignore=tests/e2e

# 只跑单元测试类（不含集成）
python -m pytest tests/modules/test_solving/test_solving.py::TestSolvingModule -v

# 手动 E2E 测试（需要真实 API Key）
python tests/modules/test_solving/e2e_turbo_manual.py      # qwen-turbo 快速验证
python tests/modules/test_solving/e2e_qwen35_manual.py    # qwen3.5-plus 深度思考
```

## 测试结构

```
tests/modules/test_solving/
├── __init__.py
├── test_solving.py           # 测试套件（26 个测试）
├── test_case_1_correct_full.json  # Case 1 测试数据（无学生作答）
├── test_case_2_wrong.json          # Case 2 测试数据（错误解答）
├── test_case_3_partial.json        # Case 3 测试数据（部分正确）
├── e2e_turbo_manual.py         # E2E 测试（qwen-turbo，需手动运行）
├── e2e_qwen35_manual.py       # E2E 测试（qwen3.5-plus，需手动运行）
└── README.md
```

## 三个测试场景

### Case 1: 正确完整解答（无学生作答）

**输入：** 仅有 LaTeX 题目，无学生作答  
**期望：** 返回完整参考解法

```
题目：设 a_0, a_1, ... 是正整数序列，证明可以选择序列 (a_n) 使得每个非零自然数恰好等于 a_0, b_0, a_1, b_1, ... 中的一项。

期望返回：
- success: True
- evaluation.is_correct: True
- solution.steps: 教学步骤列表（s1, s2, s3...）
- solution.answer: 核心思维动作总结
```

### Case 2: 错误学生解答

**输入：** 题目 + 错误的学生解答  
**期望：** 评估失败，返回错误反馈

```
学生错误思路：假设所有 a_n 互质，则所有 b_n = 1，只能覆盖正整数 1。

期望返回：
- success: False
- evaluation.is_correct: False
- error_feedback: 具体错误分析和修正建议
```

### Case 3: 正确部分解答（继续生成）

**输入：** 题目 + 正确的部分解答  
**期望：** 评估通过，继续生成后续步骤

```
学生已完成：设 a_0 = 1，令 a_{n+1} = b_n × (n+2)，则 b_n = n+1。

期望返回：
- success: True
- evaluation.is_correct: True
- evaluation.can_continue: True
- evaluation.breakpoint_step: 1
```

## LLM 输出格式

LLM 输出为**自然语言三段式**，Parser 自动解析为结构化数据：

```
这题怎么看：
关键观察点、真正突破口、整体路径。不要一上来就写公式。

这题怎么想：
第一步：...（关键判断和转折点）
第二步：...
第三步：...
（对重要变形、分类、替换、构造要解释理由）

这题留下什么方法：
总结核心思维动作，点出最关键的一步，说明以后遇到类似题从哪想。
```

## 测试覆盖

| 测试类                          | 测试内容                                           |
| ------------------------------- | -------------------------------------------------- |
| `TestSolvingModule`             | 模型导入、Parser、Director、Evaluator、Prompt 模板 |
| `TestSolvingServiceIntegration` | 三个 Case 的输入输出验证                           |

## step_id 格式

步骤 ID 使用扁平格式：`s1`, `s2`, `s3` ...  
暂不分组，后续由专门模块处理分组逻辑。

## 依赖环境

```bash
# 安装依赖
pip install -e ".[dev]"

# 环境变量
cp .env.example .env
# 填入 DASHSCOPE_API_KEY
```

## 模型参数说明

| 参数              | 默认值       | 说明                                                 |
| ----------------- | ------------ | ---------------------------------------------------- |
| `model`           | `qwen-turbo` | 模型名，支持 `qwen-turbo`、`qwen3.5-plus` 等         |
| `temperature`     | `0.7`        | 温度参数                                             |
| `max_tokens`      | `8192`       | 最大生成长度                                         |
| `enable_thinking` | `False`      | 启用深度思考（`qwen3.5-plus` 等思考模型设为 `True`） |

### 思考模型推荐配置

| 模型           | temperature | max_tokens | enable_thinking |
| -------------- | ----------- | ---------- | --------------- |
| `qwen-turbo`   | 0.7         | 2048       | False           |
| `qwen3.5-plus` | 0.7         | 8192       | True            |
