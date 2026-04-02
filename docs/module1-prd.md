# Module 1 PRD: Organized Solution Mainline Generation
## 有序解题主线路生成模块

**文档版本**: v1.0  
**创建日期**: 2026-03-30  
**所属项目**: 高中数学 tutoring system  
**模块编号**: Module 1  
**状态**: 草稿

---

## 1. 模块概述 (Module Overview)

### 1.1 问题定位

当前高中数学教学中，AI 辅助解题系统普遍存在以下问题：
- 输出仅给出最终答案，缺乏解题过程的结构化展示
- 跳跃式推理，学生无法理解"为什么这样想"
- 模板化输出，使用"显然/易知"跳过关键推理步骤
- 无法为下游模块（Module 2: Breakpoint Analysis）提供可分析的解题脉络

Module 1 旨在生成**有序解题主线路**（Organized Solution Mainline），其核心价值在于：
> 不仅给出答案，更展示**数学思维的组织方式**，让学生看到"这题从哪看、怎么想、留下什么"。

### 1.2 输入定义

| 字段 | 类型 | 说明 |
|------|------|------|
| `problem_text` | string | 题目文本，支持 LaTeX 格式 |
| `problem_type` | enum | `calculation`, `proof`, `graph`, `combined` |
| `difficulty_level` | enum | `basic`, `intermediate`, `advanced` |
| `context_hints` | string[] | 可选，提供题目背景或相关知识点提示 |

**输入示例**：

```json
{
  "problem_text": "已知函数 f(x) = x^2 - 2ax + 3，当 x \in [1, 3] 时，f(x) \geq 0 恒成立，求实数 a 的取值范围。",
  "problem_type": "calculation",
  "difficulty_level": "intermediate",
  "context_hints": ["二次函数最值", "恒成立问题"]
}
```

### 1.3 输出定义

Module 1 输出**有序解题主线路**，包含：
- 完整解题步骤序列
- 每一步的显式推理链
- 关键洞察点（key_insight）
- 解题方法论总结（what this problem leaves behind）

### 1.4 与 Module 2 的关系

```
┌─────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Module 1  │ ───▶ │   Global         │ ───▶ │    Module 2     │
│   Input:    │      │   Solution       │      │    Input:       │
│   Problem   │      │   Mainline       │      │    Mainline +   │
│             │      │                  │      │    Student      │
│             │      │                  │      │    Response     │
└─────────────┘      └──────────────────┘      └─────────────────┘
                              │
                              ▼
                     Module 2 分析主线路，
                     识别学生断点
```

**接口约定**：
- Module 1 输出 JSON 格式的 `SolutionMainline`
- Module 2 消费 `SolutionMainline`，进行 breakpoint 分析
- 两者通过文件路径或消息队列传递，详见集成协议

---

## 2. 用户故事 (User Stories)

### 2.1 教师用户 (Teacher)

**角色**：高中数学教师，使用系统生成教学参考  
**场景**：备课时，需要生成高质量的解题思路，用于课堂讲解或制作教学材料

**用户故事**：

```
作为一名教师，
我希望系统生成包含完整推理过程的解题主线路，
以便我在课堂上展示"如何分析问题、如何组织思路"，
而不是直接给出答案让学生抄写。
```

**验收标准**：
- [ ] 系统输出的主线路包含至少 3 个可讲解的推理步骤
- [ ] 每个步骤都有"为什么这样做"的解释
- [ ] 输出可以直接用于课堂教学，无需教师二次加工

### 2.2 学生用户 (Student)

**角色**：高中生，使用系统辅助学习  
**场景**：解题时遇到困难，查看主线路学习解题思路

**用户故事**：

```
作为一名学生，
当我遇到不会的题目时，
我希望看到"这题从哪个角度切入、如何一步步想下去"，
而不是看到一堆公式不知道来龙去脉。
通过学习主线路，我能掌握这一类题目的思考方法。
```

**验收标准**：
- [ ] 主线路的"开头"（这题怎么看）帮助学生建立题目感知
- [ ] 主线路的"中间"（这题怎么想开）展示完整的思维展开
- [ ] 主线路的"结尾"（这题留下什么方法）提供可迁移的方法论

### 2.3 Module 2 系统 (Module 2 Consumer)

**角色**：Module 2 (Breakpoint Analysis Module)  
**场景**：接收 Module 1 输出的主线路，与学生作答进行对比分析

**用户故事**：

```
作为 Module 2 的数据消费者，
我需要接收结构化的解题主线路，
其中包含：
  - 步骤序列及其关联的推理类型
  - 关键转折点（key_insight）
  - 涉及的数学知识点清单
以便与学生作答进行 breakpoint 对比分析。
```

**验收标准**：
- [ ] 主线路包含标准化的步骤序列，每步有唯一 ID
- [ ] 关键洞察点（key_insight）标记清晰
- [ ] 知识点清单（knowledge_points）完整覆盖

---

## 3. 功能需求 (Functional Requirements)

### 3.1 核心功能

| 功能 ID | 描述 | 优先级 |
|---------|------|--------|
| FR-1.1 | 接收题目输入，解析 LaTeX 格式 | P0 |
| FR-1.2 | 按照四思任务框架生成解题主线路 | P0 |
| FR-1.3 | 应用七项通用解题行动 | P0 |
| FR-1.4 | 输出结构化 JSON，包含步骤序列、推理链、关键洞察 | P0 |
| FR-1.5 | 生成"开头-中间-结尾"三段式主线路 | P0 |

### 3.2 四思任务合规性 (Four Thinking Tasks Compliance)

Module 1 必须按照以下框架组织解题思路：

| 思任务 | 名称 | 说明 | 在主线路中的体现 |
|--------|------|------|------------------|
| T1 | 问题定向 | 分析题目属于哪类问题，识别已知与未知 | 开头部分：题目定性 |
| T2 | 关系重构 | 建立数学对象间的联系，寻找等价的变换方式 | 中间部分：思路探索 |
| T3 | 形式化归 | 将问题转化为标准形式，执行形式化操作 | 中间部分：形式化处理 |
| T4 | 结果审查 | 验证答案合理性，检查边界情况 | 结尾部分：回顾验证 |

**合规性要求**：
- 主线路必须覆盖全部四个思任务
- 每个思任务至少对应一个步骤（step）
- T1（问题定向）和 T4（结果审查）不可省略

### 3.3 七项通用解题行动 (Seven Universal Problem-Solving Actions)

在生成主线路时，必须根据题目特征选择性地应用以下行动：

| 行动 ID | 名称 | 触发条件 | 示例 |
|---------|------|----------|------|
| A1 | 观察结构 | 题目有复杂表达式或嵌套结构时 | 观察二次函数配方后的结构特征 |
| A2 | 寻找联系 | 存在多个数学对象时 | 建立方程与几何意义的联系 |
| A3 | 化生为熟 | 遇到陌生形式时 | 将抽象函数问题转化为熟悉的具体情形 |
| A4 | 抓关键限制 | 存在约束条件时 | 从"恒成立"条件中提取关键不等式 |
| A5 | 适时分类 | 问题涉及多种情况时 | 分类讨论绝对值函数的不同区间 |
| A6 | 构造与替换 | 直接求解困难时 | 构造辅助函数或变量替换 |
| A7 | 特殊化边界化回验 | 需要验证或探索时 | 取特殊值验证答案合理性 |

**合规性要求**：
- 每条主线路必须至少应用 2 项行动
- 关键步骤必须标注对应的行动类型
- 避免单一行动重复使用（如全程只做"化生为熟"）

### 3.4 输出结构：三段式主线路

主线路必须按照"开头-中间-结尾"结构组织：

#### 3.4.1 开头：这题怎么看

**目的**：帮助读者建立题目感知，明确解题方向

**包含内容**：
- 题目类型定性（如：这是一道关于二次函数最值的恒成立问题）
- 关键条件的初步识别（如：注意到定义域是闭区间 [1, 3]）
- 解题方向的初步预判（如：考虑使用配方法求最值）

**格式要求**：
- 1-3 个自然段
- 避免直接使用"显然/易知"
- 重点是"为什么这样看"而非"题目说了什么"

#### 3.4.2 中间：这题怎么想开

**目的**：展示完整的思维展开过程，每一步都有推理

**包含内容**：
- 步骤序列：每个步骤包含编号、行动类型、推理说明
- 关键洞察（key_insight）：在适当位置标记
- 从一个步骤到下一个步骤的过渡说明

**格式要求**：
- 每个步骤必须有"这一步为什么这样做"的解释
- 不得跳过关键推理步骤
- 关键洞察用 `key_insight` 字段明确标记

#### 3.4.3 结尾：这题留下什么方法

**目的**：提供可迁移的方法论，总结本题涉及的思想

**包含内容**：
- 本题涉及的核心方法（如：配方法求最值）
- 这类问题的通用解法思路
- 类似的题目变式或延伸方向
- 易错点提醒（如：忽略定义域边界）

**格式要求**：
- 2-4 个要点
- 侧重"方法"而非"答案"
- 学生可据此解决同类问题

### 3.5 语言风格要求

| 要求 | 说明 | 反面案例 |
|------|------|----------|
| 自然流畅 | 使用自然的数学语言，非机器模板 | "Step 1: 观察结构"（生硬标题） |
| 清晰准确 | 术语使用准确，表述无歧义 | "易知..."（跳过推理） |
| 严谨有据 | 每一步都有依据，不凭空跳步 | "显然成立"（无解释） |
| 解释"为什么" | 重点说明思维动机 | 只说"做变换"，不说"为什么要变换" |

**禁止用语**：
- 显然、易知、不难发现、显然成立
- 直接可得、由此可得（无中间推理时）
- 通过观察可得（无具体观察内容时）

### 3.6 禁止事项 (Prohibitions)

| 禁止项 | 说明 | 替代方案 |
|--------|------|----------|
| 禁止纯公式流 | 不能只有公式和计算，必须有推理说明 | 每步公式配"为什么这样变形" |
| 禁止空洞模板 | 不能套用"审题→分析→解答"框架不填内容 | 具体描述本题的独特分析过程 |
| 禁止跳步 | 不能省略关键推理步骤 | 分解为更细的子步骤 |
| 禁止纯答案输出 | 不能只给出答案而无过程 | 完整的步骤序列 |

---

## 4. 非功能需求 (Non-Functional Requirements)

### 4.1 性能要求

| 指标 | 要求 | 说明 |
|------|------|------|
| 响应延迟 | < 5 秒 | 对于典型高中数学问题（含 3-5 步推理） |
| 最大处理时间 | < 15 秒 | 对于复杂证明题（含 8+ 步推理） |
| 并发能力 | 支持 10+ 并发请求 | 课堂教学场景 |

### 4.2 质量要求

| 指标 | 要求 | 评估方法 |
|------|------|----------|
| 推理可见性 | 每个步骤都有推理说明，无跳步 | 人工审核 + 规则检查 |
| 四思任务覆盖 | 100% 覆盖 | 输出结构字段校验 |
| 七项行动应用 | 至少应用 2 项 | 输出 action_ids 字段校验 |
| 方法论完整性 | 结尾包含可迁移方法 | 人工审核 |

### 4.3 安全要求

| 要求 | 说明 |
|------|------|
| 无答案泄露 | 主线路是"教你怎么想"，不是"替你解题" |
| 内容安全 | 输出内容符合教育场景，无不当言论 |
| 隐私保护 | 不记录学生个人信息 |

---

## 5. 提示词模板 (Prompt Template)

### 5.1 系统提示词 (System Prompt)

```
你是一位资深高中数学教师，擅长生成教学质量的解题思路。

你的任务是根据给定的数学问题，生成一条**有序解题主线路**。

## 核心原则
1. **不仅给答案，更要展示思维过程**
2. **每一步都要解释"为什么这样做"**
3. **绝对不要使用"显然、易知"等跳过推理的词汇**

## 四思任务框架（必须遵循）
1. **问题定向**：分析题目类型，明确已知与未知
2. **关系重构**：建立数学对象间的联系
3. **形式化归**：执行形式化操作
4. **结果审查**：验证答案合理性

## 七项通用解题行动（根据题目选择应用）
1. 观察结构
2. 寻找联系
3. 化生为熟
4. 抓关键限制
5. 适时分类
6. 构造与替换
7. 特殊化边界化回验

## 输出格式要求
必须按照以下结构组织：

### 这题怎么看
（开头：题目定性、关键条件识别、解题方向预判）

### 这题怎么想开
（中间：步骤序列，每步包含编号、行动类型、推理说明、关键洞察）

### 这题留下什么方法
（结尾：本章方法总结、可迁移思路、类似题目变式）

## 语言风格
- 使用自然的数学语言
- 重点解释"为什么"而非"是什么"
- 推理过程清晰，无跳步

现在开始生成解题主线路。
```

### 5.2 用户提示词 (User Prompt)

```
## 题目
{problem_text}

## 题目类型
{problem_type}

## 难度等级
{difficulty_level}

## 背景提示（可选）
{context_hints}

请按照上述格式要求，生成这条题的解题主线路。
```

### 5.3 完整调用示例

```json
{
  "model": "gpt-4",
  "messages": [
    {"role": "system", "content": "<系统提示词内容>"},
    {"role": "user", "content": "## 题目\n已知函数 f(x) = x^2 - 2ax + 3，当 x \\in [1, 3] 时，f(x) \\geq 0 恒成立，求实数 a 的取值范围。\n\n## 题目类型\ncalculation\n\n## 难度等级\nintermediate\n\n## 背景提示\n二次函数最值、恒成立问题\n\n请按照上述格式要求，生成这条题的解题主线路。"}
  ],
  "temperature": 0.7,
  "max_tokens": 2000
}
```

---

## 6. 输出格式 (Output Schema)

### 6.1 JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SolutionMainline",
  "type": "object",
  "required": ["problem_id", "thinking_tasks", "steps", "key_insights", "methodology", "metadata"],
  "properties": {
    "problem_id": {
      "type": "string",
      "description": "题目唯一标识符（可由输入生成 MD5 或 UUID）"
    },
    "problem_text": {
      "type": "string",
      "description": "原始题目文本"
    },
    "thinking_tasks": {
      "type": "object",
      "description": "四思任务覆盖情况",
      "required": ["T1_问题定向", "T2_关系重构", "T3_形式化归", "T4_结果审查"],
      "properties": {
        "T1_问题定向": {
          "type": "object",
          "properties": {
            "covered": {"type": "boolean"},
            "description": {"type": "string"},
            "step_ids": {"type": "array", "items": {"type": "string"}}
          }
        },
        "T2_关系重构": {
          "type": "object",
          "properties": {
            "covered": {"type": "boolean"},
            "description": {"type": "string"},
            "step_ids": {"type": "array", "items": {"type": "string"}}
          }
        },
        "T3_形式化归": {
          "type": "object",
          "properties": {
            "covered": {"type": "boolean"},
            "description": {"type": "string"},
            "step_ids": {"type": "array", "items": {"type": "string"}}
          }
        },
        "T4_结果审查": {
          "type": "object",
          "properties": {
            "covered": {"type": "boolean"},
            "description": {"type": "string"},
            "step_ids": {"type": "array", "items": {"type": "string"}}
          }
        }
      }
    },
    "steps": {
      "type": "array",
      "description": "解题步骤序列",
      "items": {
        "type": "object",
        "required": ["step_id", "order", "action_type", "content", "reasoning"],
        "properties": {
          "step_id": {
            "type": "string",
            "description": "步骤唯一标识符，格式：step_1, step_2, ..."
          },
          "order": {
            "type": "integer",
            "description": "步骤顺序号（1-based）"
          },
          "action_type": {
            "type": "string",
            "enum": ["观察结构", "寻找联系", "化生为熟", "抓关键限制", "适时分类", "构造与替换", "特殊化边界化回验"],
            "description": "对应的解题行动"
          },
          "content": {
            "type": "string",
            "description": "步骤的具体内容（公式、计算、变换等）"
          },
          "reasoning": {
            "type": "string",
            "description": "这一步的推理说明：为什么这样做"
          },
          "key_insight": {
            "type": "boolean",
            "description": "是否为关键洞察点"
          },
          "knowledge_points": {
            "type": "array",
            "items": {"type": "string"},
            "description": "本步骤涉及的知识点"
          }
        }
      }
    },
    "key_insights": {
      "type": "array",
      "description": "关键洞察点列表",
      "items": {
        "type": "object",
        "properties": {
          "step_id": {"type": "string"},
          "insight": {"type": "string"},
          "why_important": {"type": "string"}
        }
      }
    },
    "methodology": {
      "type": "object",
      "description": "方法论总结",
      "properties": {
        "core_methods": {
          "type": "array",
          "items": {"type": "string"},
          "description": "本题涉及的核心方法"
        },
        "transferable_ideas": {
          "type": "array",
          "items": {"type": "string"},
          "description": "可迁移的思路"
        },
        "variations": {
          "type": "array",
          "items": {"type": "string"},
          "description": "类似题目变式"
        },
        "common_pitfalls": {
          "type": "array",
          "items": {"type": "string"},
          "description": "易错点提醒"
        }
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "problem_type": {"type": "string"},
        "difficulty_level": {"type": "string"},
        "generation_time_ms": {"type": "integer"},
        "model_version": {"type": "string"}
      }
    }
  }
}
```

### 6.2 输出示例

```json
{
  "problem_id": "md5_a1b2c3d4e5f6",
  "problem_text": "已知函数 f(x) = x^2 - 2ax + 3，当 x ∈ [1, 3] 时，f(x) ≥ 0 恒成立，求实数 a 的取值范围。",
  "thinking_tasks": {
    "T1_问题定向": {
      "covered": true,
      "description": "识别为二次函数最值问题，关键在于"恒成立"条件的转化",
      "step_ids": ["step_1"]
    },
    "T2_关系重构": {
      "covered": true,
      "description": "将恒成立条件转化为最值问题",
      "step_ids": ["step_2", "step_3"]
    },
    "T3_形式化归": {
      "covered": true,
      "description": "配方后求最值，建立不等式",
      "step_ids": ["step_4", "step_5", "step_6"]
    },
    "T4_结果审查": {
      "covered": true,
      "description": "验证边界情况，检查解的合理性",
      "step_ids": ["step_7"]
    }
  },
  "steps": [
    {
      "step_id": "step_1",
      "order": 1,
      "action_type": "观察结构",
      "content": "f(x) = x² - 2ax + 3 是开口向上的二次函数",
      "reasoning": "看到二次项系数为正，故图像开口向上。这意味着在闭区间上的最小值将决定"≥ 0 恒成立"的条件。",
      "key_insight": false,
      "knowledge_points": ["二次函数图像特征", "开口方向与最值位置"]
    },
    {
      "step_id": "step_2",
      "order": 2,
      "action_type": "抓关键限制",
      "content": "恒成立条件 f(x) ≥ 0 在 [1, 3] 上等价于 min{f(x) | x ∈ [1, 3]} ≥ 0",
      "reasoning": "对于开口向上的函数，要使整个区间上函数值非负，只需确保区间内的最小值不小于 0。这是处理"恒成立"问题的常用转化思路。",
      "key_insight": true,
      "knowledge_points": ["函数恒成立问题", "最值与不等式"]
    },
    {
      "step_id": "step_3",
      "order": 3,
      "action_type": "化生为熟",
      "content": "配方：f(x) = (x - a)² + 3 - a²",
      "reasoning": "将一般二次式化为顶点式，便于分析最值。配方是处理二次函数的常规操作。",
      "key_insight": false,
      "knowledge_points": ["配方法", "二次函数顶点式"]
    },
    {
      "step_id": "step_4",
      "order": 4,
      "action_type": "寻找联系",
      "content": "对称轴 x = a 与区间 [1, 3] 的位置关系",
      "reasoning": "二次函数的最小值位置取决于对称轴是否在区间内。需要分情况讨论：对称轴在区间内时最小值在顶点取得，在区间外时最小值在端点取得。",
      "key_insight": true,
      "knowledge_points": ["二次函数最值讨论", "对称轴位置"]
    },
    {
      "step_id": "step_5",
      "order": 5,
      "action_type": "适时分类",
      "content": "情况1：当 a ∈ [1, 3] 时，最小值为 f(a) = 3 - a² ≥ 0，得 a² ≤ 3",
      "reasoning": "对称轴在区间内时，顶点就是最小值点。",
      "key_insight": false,
      "knowledge_points": ["分类讨论"]
    },
    {
      "step_id": "step_6",
      "order": 6,
      "action_type": "适时分类",
      "content": "情况2：当 a < 1 时，最小值为 f(1) = 4 - 2a ≥ 0，得 a ≤ 2",
      "reasoning": "对称轴在区间左侧，x=1 更靠近对称轴，故 x=1 处取得最小值。",
      "key_insight": false,
      "knowledge_points": ["区间端点分析"]
    },
    {
      "step_id": "step_7",
      "order": 7,
      "action_type": "特殊化边界化回验",
      "content": "取 a = -1, 0, 1, √2, 2 验证",
      "reasoning": "选取边界值和特殊值检验解集的合理性。",
      "key_insight": false,
      "knowledge_points": ["特殊值验证"]
    }
  ],
  "key_insights": [
    {
      "step_id": "step_2",
      "insight": "恒成立 → 最小值 ≥ 0 的转化",
      "why_important": "这是处理"恒成立"问题的核心思路，将抽象条件转化为具体的最值计算"
    },
    {
      "step_id": "step_4",
      "insight": "对称轴与区间位置关系决定最值位置",
      "why_important": "这是二次函数最值问题的通法，避免盲目配方"
    }
  ],
  "methodology": {
    "core_methods": ["配方法", "分类讨论", "恒成立与最值的转化"],
    "transferable_ideas": ["遇到恒成立问题，优先考虑转化为最值问题", "二次函数最值先看对称轴与区间关系"],
    "variations": ["将"≥ 0"改为"≤ 0"", "改变定义域为开区间"],
    "common_pitfalls": ["忽略对称轴位置讨论", "配方计算错误"]
  },
  "metadata": {
    "problem_type": "calculation",
    "difficulty_level": "intermediate",
    "generation_time_ms": 2340,
    "model_version": "gpt-4"
  }
}
```

---

## 7. 边界情况 (Edge Cases)

### 7.1 多步证明题 vs 单一计算题

| 情况 | 处理策略 |
|------|----------|
| 多步证明题 | 适当增加 step 数量，确保每步推理可见；标注"证明关键点" |
| 单一计算题 | 仍需包含"为什么这样算"的解释，而非纯数值计算 |

**示例**：

```json
// 单一计算题（需要推理说明）
{
  "step_id": "step_3",
  "action_type": "化生为熟",
  "content": "计算：2 + 3 = 5",
  "reasoning": "直接相加：2个苹果加3个苹果等于5个苹果"
}
```

### 7.2 多条有效解题路径

| 处理策略 | 说明 |
|----------|------|
| 选择最优路径 | 基于题目特征选择最清晰、最具教学价值的路径 |
| 标注备选路径 | 在 `methodology.variations` 中说明其他可行路径 |
| 保持一致性 | 一旦选定路径，完整走通，不中途切换 |

**示例**：

```json
{
  "methodology": {
    "core_methods": ["配方法（主线路采用）", "求导法（备选路径）"],
    "variations": [
      "本题也可使用求导法求最值，但配方法更直接"
    ]
  }
}
```

### 7.3 学生答案包含错误的情况

**当前版本处理策略**：Deferred — 假设学生答案正确，Module 1 仅负责生成标准主线路。

**未来扩展计划**（Module 2 范畴）：
- Module 2 将接收学生作答，与 Module 1 主线路进行对比
- 识别学生作答中的错误类型（计算错误、思路错误、跳步等）
- Module 1 暂不涉及错误检测逻辑

### 7.4 特殊格式题目

| 题目类型 | 处理策略 |
|----------|----------|
| LaTeX 公式 | 解析为可读文本，保留数学结构 |
| 几何题（含图） | 文字描述图形特征，标注关键点 |
| 选择题 | 分析各选项正误原因，而非直接选答案 |
| 开放题 | 选择最具代表性的解法路径 |

---

## 8. 评估指标 (Metrics)

### 8.1 质量评估维度

| 维度 | 指标 | 目标值 | 评估方法 |
|------|------|--------|----------|
| 四思任务覆盖 | T1-T4 全部覆盖 | 100% | 检查 thinking_tasks 各字段 covered |
| 七项行动应用 | 至少应用 2 项 | ≥ 2 | 统计 steps[].action_type 去重数量 |
| 推理可见性 | 每步都有 reasoning | 100% | 检查 steps[].reasoning 非空 |
| 关键洞察标记 | key_insights 存在 | ≥ 1 | 检查 key_insights 数组长度 |
| 方法论完整性 | 结尾三部分齐全 | 100% | 检查 methodology 三字段 |

### 8.2 合规性检查清单

```
□ [ ] T1（问题定向）有对应步骤
□ [ ] T2（关系重构）有对应步骤
□ [ ] T3（形式化归）有对应步骤
□ [ ] T4（结果审查）有对应步骤
□ [ ] 至少 2 个不同的 action_type
□ [ ] 每步有非空 reasoning
□ [ ] 至少 1 个 key_insight = true
□ [ ] methodology.core_methods 非空
□ [ ] methodology.transferable_ideas 非空
□ [ ] 无"显然/易知"等禁用词汇
□ [ ] 无纯公式流（公式后有推理）
```

### 8.3 自动化评估脚本（伪代码）

```python
def evaluate_mainline(mainline: dict) -> dict:
    scores = {}
    
    # 四思任务覆盖
    scores["thinking_coverage"] = sum(
        1 for t in mainline["thinking_tasks"].values() 
        if t["covered"]
    ) / 4
    
    # 七项行动应用
    action_types = set(s["action_type"] for s in mainline["steps"])
    scores["action_diversity"] = len(action_types) / 7
    
    # 推理可见性
    scores["reasoning_visibility"] = sum(
        1 for s in mainline["steps"] 
        if s["reasoning"] and len(s["reasoning"]) > 10
    ) / len(mainline["steps"])
    
    # 关键洞察
    scores["key_insight_ratio"] = sum(
        1 for s in mainline["steps"] 
        if s.get("key_insight", False)
    ) / max(len(mainline["steps"]), 1)
    
    # 方法论完整性
    scores["methodology_completeness"] = (
        len(mainline["methodology"]["core_methods"]) > 0 and
        len(mainline["methodology"]["transferable_ideas"]) > 0
    )
    
    # 综合评分
    scores["overall"] = (
        scores["thinking_coverage"] * 0.3 +
        scores["action_diversity"] * 0.2 +
        scores["reasoning_visibility"] * 0.3 +
        scores["key_insight_ratio"] * 0.2
    )
    
    return scores
```

### 8.4 人工评估标准

| 等级 | 描述 | 评分标准 |
|------|------|----------|
| A (优秀) | 推理完整，方法论清晰，可直接用于教学 | 综合分 ≥ 0.9 |
| B (良好) | 有轻微跳步或表达不流畅，但整体可用 | 综合分 ≥ 0.75 |
| C (及格) | 存在跳步或缺少关键解释，需小幅修改 | 综合分 ≥ 0.6 |
| D (不及格) | 明显跳步、模板化严重或方法论缺失 | 综合分 < 0.6 |

---

## 9. 附录

### 9.1 术语表

| 术语 | 定义 |
|------|------|
| 有序解题主线路 | Module 1 的核心输出，包含完整推理过程的解题思路 |
| 四思任务 | 问题定向、关系重构、形式化归、结果审查 |
| 七项行动 | 观察结构、寻找联系、化生为熟、抓关键限制、适时分类、构造与替换、特殊化边界化回验 |
| key_insight | 关键洞察点，解题中的核心转折或突破口 |
| 恒成立问题 | 参数取值使得某条件在给定区间内始终成立的问题 |

### 9.2 参考资料

- 波利亚《怎样解题》
- 高中数学课程标准
- Module 2 PRD (for integration details)

### 9.3 修订历史

| 版本 | 日期 | 修改内容 | 作者 |
|------|------|----------|------|
| v1.0 | 2026-03-30 | 初始版本 | System Architect |
