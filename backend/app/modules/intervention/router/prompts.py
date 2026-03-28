"""
Node 2a: Dimension Router Prompt

判断学生困难属于 Resource 还是 Metacognitive。
"""

DIMENSION_ROUTER_PROMPT = """你是一位数学解题教育专家。

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

## 连接点：图式
- Resource → 提供"有什么可走、为什么会出现"
- Metacognitive → 对已激活路径"如何判定、推进与修正"
- 两者在同一个"下一步"上形成前后衔接，不是平行关系

## 输出格式（JSON）

```json
{{
  "dimension": "Resource" | "Metacognitive",
  "confidence": 0.0-1.0,
  "reasoning": "判断理由，3-5句话"
}}
```

只输出 JSON，不要有其他内容。
"""

# 断点类型到维度的默认映射提示（LLM参考用）
BREAKPOINT_TYPE_HINTS = """
断点类型参考映射：
- MISSING_STEP → 通常是 Resource（没有形成候选路径）
- WRONG_DIRECTION → 通常是 Resource（候选路径本身就是错的）
- INCOMPLETE_STEP → 通常是 Metacognitive（候选已出现，展开不完整）
- STUCK → 通常是 Resource（完全不知道怎么做）
"""
