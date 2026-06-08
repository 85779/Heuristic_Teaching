# Module 3 API 接口文档

## 智能练习题推荐系统

**版本**: v2 (知识库驱动版)
**最后更新**: 2026-05-11
**模块代号**: Socrates-Module-3-Recommendation

> **架构变更说明**: v2 已从题库检索架构重构为知识本体 + LLM 实时生成架构。旧版 v1 API 文档已废弃（详见 git 历史）。
> 设计文档: [docs/module3-design.md](module3-design.md) | 执行计划: [docs/module3-execution-plan.md](module3-execution-plan.md)

---

## 1. 模块定位

Module 3 是智能练习题推荐系统，在学生完成一道题目后，基于学生维度画像 (R/M) 和知识本体，通过 LLM 实时生成适配的练习题。

**核心流程**:
```
学生完成 → 读取画像 → 知识锚点检索 → LLM 生成题目 → 校验 → 返回
```

**与旧版 (v1) 的核心差异**:

| 对比项   | v1 (旧)              | v2 (当前)              |
| -------- | -------------------- | ---------------------- |
| 题目来源 | 预建题库 (50-1000道) | 知识本体 + LLM 实时生成 |
| 候选集   | 20 道候选题          | 1-3 个知识锚点          |
| 排序     | 4 项打分排序         | 单一生成 (不打分排序)   |
| 输出数量 | top-3                | 1 道 (可扩展)           |

**依赖**: Module 1 (solving), Module 4 (student_model, 目前使用 mock), Module 6 (知识本体数据)

---

## 2. API Endpoints

### 2.1 POST /recommendations/recommend

触发智能推荐，返回一道生成的练习题。

**Request Body (RecommendRequest)**:

```json
{
  "student_id": "string (必需)",
  "trigger": {
    "outcome": "SOLVED | MAX_ESCALATION | ABANDONED | MANUAL",
    "current_problem_kps": ["KP_3_13"],
    "current_method": "配方法",
    "current_difficulty": 2,
    "session_id": "string"
  }
}
```

**Response Body (RecommendResponse)**:

```json
{
  "success": true,
  "recommendation": {
    "generated_id": "gen_a1b2c3d4",
    "problem_text": "已知函数 $f(x) = ...$",
    "answer": "$x = 3$",
    "solution_hint": "先配方，再...",
    "difficulty": 3,
    "related_kps": ["KP_3_13"],
    "method_used": "配方法",
    "why_recommended": "继续巩固 二次函数，强化基础，运用【配方法】",
    "generation_reasoning": "基于锚点 SAME_KP 生成"
  },
  "metadata": {
    "generation_time_ms": 1850,
    "generation_mode": "LLM_GENERATED",
    "knowledge_anchor": {
      "type": "SAME_KP",
      "kps": ["KP_3_13"],
      "goal": "巩固前置知识点"
    },
    "target_difficulty": 3
  },
  "error": null
}
```

**状态码**:
- `200 OK`: 推荐成功
- `500 Internal Server Error`: 生成失败
- `503 Service Unavailable`: 模块未初始化

---

### 2.2 GET /recommendations/health

健康检查。

**Response**:
```json
{
  "status": "ok",
  "module": "recommendation"
}
```

---

## 3. 核心数据模型

```python
class TriggerOutcome(str, Enum):
    SOLVED = "SOLVED"
    MAX_ESCALATION = "MAX_ESCALATION"
    ABANDONED = "ABANDONED"
    MANUAL = "MANUAL"

class AnchorType(str, Enum):
    SAME_KP = "SAME_KP"        # R型主导 → 同知识点强化
    VARIATION = "VARIATION"    # M型主导 → 变式题
    BALANCED = "BALANCED"      # 均衡 → 随机薄弱KP

class TriggerEvent(BaseModel):
    outcome: TriggerOutcome
    current_problem_kps: list[str]
    current_method: Optional[str]
    current_difficulty: int
    session_id: str

class StudentProfile(BaseModel):
    student_id: str
    dimension_ratio: float          # R型比例 0-1 (>0.65偏R, <0.35偏M)
    recent_problems: list[RecentProblem]
    weak_kps: list[str]
    mastered_kps: list[str]
    recent_methods: list[str]

class KnowledgeAnchor(BaseModel):
    anchor_type: AnchorType
    target_kps: list[KnowledgePoint]
    target_method: Optional[Method]
    exclude_methods: list[str]
    exclude_similar: list[str]
    generation_goal: str

class GeneratedProblem(BaseModel):
    generated_id: str
    problem_text: str               # LaTeX
    answer: str
    solution_hint: str
    difficulty: int                 # 1-5
    related_kps: list[str]
    method_used: str
    why_recommended: str
    generation_reasoning: str
```

---

## 4. 推荐策略

维度比例 (`dimension_ratio`) 决定知识锚点检索策略:

| ratio 范围 | 策略       | anchor_type | 行为                           |
| ---------- | ---------- | ----------- | ------------------------------ |
| > 0.65     | R 型主导   | SAME_KP     | 找未掌握的前置 KP，同知识点练习 |
| < 0.35     | M 型主导   | VARIATION   | 同题型不同方法的变式练习        |
| 0.35-0.65  | 均衡       | BALANCED    | 随机薄弱 KP 综合练习            |

目标难度由 `DifficultyScorer` 根据 `trigger.outcome` 调整:
- `SOLVED` / `MANUAL` → 难度 +1 (上限 5)
- `MAX_ESCALATION` → 难度 -1 (下限 1)
- `ABANDONED` → 难度维持

---

## 5. 模块结构

```
backend/app/modules/recommendation/
├── module.py              # IModule 入口
├── routes.py              # FastAPI 路由
├── service.py             # 主编排服务
├── models.py              # Pydantic 模型
├── knowledge_base/
│   └── knowledge_api.py   # 知识本体 API (加载 JSON)
├── retriever/
│   └── knowledge_anchor_retriever.py  # 锚点检索 (3 策略)
├── generator/
│   ├── problem_generator.py      # LLM 生成器
│   ├── prompt_templates.py       # Prompt 构建
│   ├── problem_validator.py      # 质量校验
│   └── fallback_generator.py     # 降级策略 (8 模板)
└── scorer/
    └── difficulty_scorer.py      # 目标难度计算
```

---

## 6. 集成方式

Module 2 在干预结束时触发 Module 3:

```python
# Module 2 → Module 3
POST /recommendations/recommend
{
    "student_id": "...",
    "trigger": {
        "outcome": "SOLVED",
        "current_problem_kps": [...],
        "current_method": "...",
        "current_difficulty": 2,
        "session_id": "..."
    }
}
```

Module 3 当前使用 mock 学生画像（`dimension_ratio=0.5`，随机薄弱 KP），后续接入 Module 4 获取真实画像数据。
