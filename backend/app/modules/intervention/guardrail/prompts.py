"""
Node 5: Output Guardrail Prompt

LLM-as-a-Judge 检查提示是否越界。
"""

# 各等级的边界规则
RULES = {
    "R1": {
        "name": "线索唤醒型",
        "forbidden": [
            "具体方法名称（如换元法、配方法）",
            "具体公式",
            "具体数值或变量赋值",
            "计算过程",
            "设 t =",
            "令 x =",
            "代入得",
        ],
        "allowed": [
            "方向性描述",
            "结构观察提示",
            "关系类比提示",
        ]
    },
    "R2": {
        "name": "图式定向型",
        "forbidden": [
            "完整计算过程",
            "最终答案",
            "具体数值结果",
            "设 t =",
            "令 x =",
        ],
        "allowed": [
            "方法名称（图式名）",
            "高阶方向（统一变量、观察结构）",
        ]
    },
    "R3": {
        "name": "资源显化型",
        "forbidden": [
            "完整解题步骤",
            "最终答案",
            "分步解答",
        ],
        "allowed": [
            "关键定理名称",
            "中间状态描述",
            "知识清单",
        ]
    },
    "R4": {
        "name": "半展开示范型",
        "forbidden": [
            "完整全程解法",
            "完整解题步骤",
        ],
        "allowed": [
            "第一小步的完整写法",
            "半成品结构",
            "关键中间台阶",
        ]
    },
    "M1": {
        "name": "路径判定支持型",
        "forbidden": [
            "直接告诉方向对不对",
            "替学生做判定",
        ],
        "allowed": [
            "引导学生观察方向",
            "问前景是什么",
        ]
    },
    "M2": {
        "name": "路径维持型",
        "forbidden": [
            "否定学生的放弃念头",
            "直接说方向对了",
        ],
        "allowed": [
            "帮助区分局部卡顿和整体失效",
            "鼓励维持当前路径",
        ]
    },
    "M3": {
        "name": "路径推进定向型",
        "forbidden": [
            "直接给出下一步的具体内容",
            "替学生决定推进顺序",
        ],
        "allowed": [
            "引导学生比较局部目标",
            "帮助确定落脚点",
        ]
    },
    "M4": {
        "name": "路径修正型",
        "forbidden": [
            "直接说学生错了",
            "替学生选择新路径",
        ],
        "allowed": [
            "帮助认识当前路径的局限",
            "引导回退",
        ]
    },
    "M5": {
        "name": "切换重建型",
        "forbidden": [
            "直接给出新路径",
            "替学生建立新起点",
        ],
        "allowed": [
            "帮助重新比较候选",
            "引导确定新推进中心",
        ]
    },
}

GUARDRAIL_PROMPT = """你是一位严格的教育内容审查员。

你的任务是检查给定的提示内容是否符合对应的等级规范。

## 提示内容
{content}

## 提示等级
{level}（{level_name}）

## 等级规范

**允许的内容**：
{allowed_desc}

**禁止的内容**：
{forbidden_desc}

## 审查标准

1. 如果提示包含任何"禁止的内容"，必须判定为不合格
2. 如果提示完全不包含任何有用信息，必须判定为不合格
3. 如果提示给出了"最终答案"或"完整解题步骤"，必须判定为不合格
4. 否则判定为合格

## 输出格式（JSON）

```json
{{
  "pass": true | false,
  "reason": "通过原因或违规原因",
  "violations": ["违规项1", "违规项2"]  // 如果违规
}}
```

只输出 JSON，不要有其他内容。
"""


def build_guardrail_prompt(content: str, level: str) -> str:
    """构建审查 prompt"""
    rule = RULES.get(level, RULES["R1"])

    allowed_desc = "、".join(rule["allowed"]) if rule["allowed"] else "无"
    forbidden_desc = "、".join(rule["forbidden"]) if rule["forbidden"] else "无"

    return GUARDRAIL_PROMPT.format(
        content=content,
        level=level,
        level_name=rule["name"],
        allowed_desc=allowed_desc,
        forbidden_desc=forbidden_desc,
    )
