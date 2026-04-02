# Module 3 PRD: Intelligent Problem Recommendation System

> **版本**: v1
> **创建日期**: 2026-03-30
> **模块名称**: 智能练习题推荐系统
> **适用领域**: 高中数学辅导

---

## 1. 模块概述（Module Overview）

### 1.1 问题定义

学生在一道题上完成干预（SOLVED 或 MAX_ESCALATION）后，系统需要推荐**下一道最合适的练习题**，以巩固学习效果并实现认知技能的螺旋上升。

当前高中数学 tutoring 系统面临三个推荐困境：

1. **同维度陷阱**：只推荐与当前题完全同类型的题（如一直做"求数列通项"），导致学生形成机械套路，缺乏灵活运用能力
2. **难度断层**：推荐题目难度跳跃过大（如刚做完基础题直接推荐竞赛题），学生无法完成，产生挫败感
3. **知识遗忘**：间隔太久才复习同类内容，知识点已遗忘，导致重复学习

Module 3 的核心任务是：**基于学生的 R/M 维度画像（来自 Module 2 的干预历史）和当前学习状态，智能推荐下一道练习题，实现维度平衡、难度递进和知识巩固三重目标。**

### 1.2 与其他模块的关系

```
Module 1 (组织化解题)
         │
         ▼
Module 2 (断点干预系统)  ───────────────────────────────────┐
         │                                                          │
         ▼                                                          ▼
Module 3 (智能推荐系统)              Module 4 (学生Profile)    Module 5 (教学策略)
         │                      （R/M维度画像存储）           （讲授/练习/讨论）
         │
         ▼
    推荐题列表 → 学生端显示
```

| 关系 | 说明 |
|------|------|
| **Module 2 → Module 3** | Module 2 每次干预结束（SOLVED / MAX_ESCALATION）后，触发 Module 3 推荐下一题。Module 2 提供：学生_id + 当前断点维度 + 干预历史摘要 |
| **Module 3 ↔ Module 4** | Module 3 读取学生的 dimension_ratio（来自 Module 4 的 profile），结合当前干预结果，更新推荐策略；同时 Module 2 的干预结果会更新到 Module 4 |
| **Module 3 → 学生端** | Module 3 输出 ranked problem list，推送到学生端显示 |

### 1.3 核心设计理念

**理念一：维度平衡（Dimension Balancing）**

如果学生最近 R 型断点多（知识缺口大），推荐题应侧重**同类知识点的再练习**（巩固基础）；如果 M 型断点多（元认知弱），推荐题应侧重**同类型题目的变式**（训练策略迁移）。

**理念二：难度递进（Difficulty Progression）**

难度分为 5 级（1-5）。推荐题难度 = min(当前完成题难度 + 1, 5)，确保每次都有适度挑战（i+1 原则）。

**理念三：间隔重复（Spaced Repetition）**

同一知识点的再次出现应间隔至少 3 道题，避免连续重复；同类题目之间应至少间隔 1 道异类题，防止套路固化。

---

## 2. 用户故事（User Stories）

### 场景一：学生刚完成一道代数题（SOLVED）

- **学生**：刚做完一道"求数列通项公式"题（Module 2 干预 2 次后解决）
- **Module 2 输出**：RESOURCE 维度，R2 级别，涉及"观察结构→寻找联系"动作
- **Module 3 读取**：该学生 dimension_ratio = 0.7（偏 R），最近 5 题中有 3 道代数题
- **Module 3 推荐**：下一题选择"数列求和"（同知识点，+1 难度），且不是最近做过的题

### 场景二：学生达到 MAX_ESCALATION（元认知困难）

- **学生**：在一道几何证明题上触发 MAX_ESCALATION（Module 2 输出 M5）
- **Module 2 判断**：学生的元认知策略使用能力不足
- **Module 3 推荐**：
  - 短期：推荐一道更简单的同类几何题（降低难度，调整信心）
  - 策略：标注该学生"元认知训练"标签，后续推荐侧重路径判定类题目（M1-M2 维度）

### 场景三：学生连续做了 3 道 R 型断点题

- **Module 4 Profile**：dimension_ratio = 0.8（严重偏 R）
- **Module 3 策略调整**：
  - 暂时减少 R 型题比例（改为 40% R + 60% M）
  - 主动推荐需要元认知策略的题目（路径判定、路径维持类）
  - 防止学生只会做机械计算、不会判断解题方向

---

## 3. 功能需求（Functional Requirements）

### 3.1 核心推荐流程

```
输入：student_id + current_problem_result + intervention_summary
         │
         ▼
┌──────────────────────────────────────────┐
│ Step 1: 读取学生 Profile（来自 Module 4）   │
│         → dimension_ratio                  │
│         → recent_problems（最近10题）      │
│         → weak_dimensions（薄弱维度）        │
└──────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│ Step 2: 候选题检索（从题库）               │
│         → 过滤：同题/太近的题排除          │
│         → 保留：与目标维度匹配的题          │
│         → 候选集 ≤ 20 道                   │
└──────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│ Step 3: 维度平衡打分                       │
│         → 当前 R 型题多 → 提高 M 型题权重   │
│         → 当前 M 型题多 → 提高 R 型题权重   │
└──────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│ Step 4: 难度递进打分                        │
│         → 推荐难度 = min(current + 1, 5)  │
│         → 偏差越大分数越低                  │
└──────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│ Step 5: 综合排序                          │
│         → score = dim_score × 0.4         │
│              + diff_score × 0.3           │
│              + recency_score × 0.2         │
│              + quality_score × 0.1         │
│         → 取 top-3 输出                   │
└──────────────────────────────────────────┘
         │
         ▼
输出：Ranked Problem List (top-3)
```

### 3.2 题目元数据模型（ProblemMetadata）

每道题在题库中标注以下元数据：

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `problem_id` | string | 全局唯一 ID | `"alg_seq_001"` |
| `topic` | string[] | 知识点标签 | `["数列", "通项公式"]` |
| `topic_tree` | string | 知识点树（用于变式识别） | `"代数/数列/通项公式"` |
| `difficulty` | int (1-5) | 难度等级（人工标注） | `3` |
| `resource_weight` | float (0-1) | 资源型特征权重（0=纯元认知，1=纯知识） | `0.8` |
| `metacognitive_weight` | float (0-1) | 元认知型特征权重 | `0.2` |
| `primary_dimension` | enum | 主要维度（R/M） | `"RESOURCE"` |
| `problem_type` | string | 题目类型 | `"求解题" | "证明题" | "综合题"` |
| `related_problems` | string[] | 变式题 ID（同一知识点的不同问法） | `["alg_seq_002", "alg_seq_003"]` |
| `prerequisite_topics` | string[] | 前置知识点 | `["代数基础"]` |
| `estimated_time_minutes` | int | 预计完成时间（分钟） | `10` |
| `quality_score` | float (0-1) | 题目质量分（来源：人工标注或题目分析） | `0.9` |

### 3.3 推荐策略矩阵

根据学生的 `dimension_ratio` 和最近做题情况，动态调整推荐策略：

| 学生状态 | dimension_ratio | 推荐策略 | R 型题比例 | M 型题比例 |
|---------|----------------|---------|-----------|-----------|
| R 型薄弱（正常状态） | > 0.65 | 同知识点 + 难度递进 | 70% | 30% |
| R 型严重不足 | > 0.80 | 降难度补基础 | 85% | 15% |
| M 型薄弱 | < 0.35 | 策略迁移训练 | 30% | 70% |
| M 型严重不足 | < 0.20 | 强元认知训练 | 15% | 85% |
| 维度均衡 | 0.35-0.65 | 维持平衡 | 50% | 50% |
| 刚完成高难度题 | — | 降 1-2 级 | +10% 简单题 | — |

### 3.4 过滤规则（硬过滤，不进入候选集）

1. **同题过滤**：与 `recent_problems` 中任意一题的 `problem_id` 完全相同 → 排除
2. **太近过滤**：与最近 2 题属于同一 `topic_tree` 叶子节点 → 排除
3. **难度跳级过滤**：`|target_difficulty - problem.difficulty| > 2` → 排除（难度跳跃过大）
4. **前置知识缺失过滤**：学生未掌握 `prerequisite_topics` 中的任意知识点 → 排除（基于 Module 4 的知识点掌握度）

### 3.5 打分函数（Soft Scoring）

对通过过滤的候选题进行综合打分：

```
score = w1 × dim_score + w2 × diff_score + w3 × recency_score + w4 × quality_score

其中：
  w1 = 0.4   (维度匹配权重)
  w2 = 0.3   (难度匹配权重)
  w3 = 0.2   (间隔新鲜度权重)
  w4 = 0.1   (题目质量权重)

维度分数 dim_score：
  if problem.primary_dimension == target_dimension:
      dim_score = 0.8 + 0.2 × dimension_focus_strength
  else:
      dim_score = 0.4 + 0.2 × (1 - dimension_focus_strength)
  （dimension_focus_strength: 学生当前维度偏离均衡的程度，0=完全均衡，1=完全偏向某一侧）

难度分数 diff_score：
  diff_score = 1 - |target_difficulty - problem.difficulty| / 5

新鲜度分数 recency_score：
  if problem.topic 与 recent_problems 中最近 1 题相同: recency_score = 0.3
  elif problem.topic 与 recent_problems 中最近 3 题相同: recency_score = 0.6
  elif problem.topic 与 recent_problems 中最近 5 题相同: recency_score = 0.8
  else: recency_score = 1.0

质量分数 quality_score：直接使用 problem.quality_score
```

### 3.6 边界情况处理

| 情况 | 处理策略 |
|------|---------|
| 题库候选不足 3 道 | 返回全部可用题（哪怕只有 1 道），并在响应中标注 `insufficient_candidates: true` |
| 题库完全为空 | 返回空列表，触发降级：推荐复习当前题目类似变式（`related_problems`） |
| 学生无历史记录（新学生） | 使用固定策略：50% R + 50% M，难度从 2 开始，topic 从高频知识点中选择 |
| 所有候选题都被过滤 | 返回 `MAX_ESCALATION` 标记，建议人工选题或推荐相关变式题 |
| dimension_ratio 异常（<0.05 或 >0.95） | 视为新学生处理，reset profile |

---

## 4. 输出格式（Output Schema）

### 4.1 核心响应结构

```typescript
interface RecommendResponse {
  success: boolean;
  data: {
    recommendations: RecommendedProblem[];  // top-3 ranked list
    strategy: RecommendationStrategy;        // 当前推荐策略标签
    insufficient_candidates?: boolean;        // 题库候选不足时为 true
  };
  metadata: {
    student_id: string;
    dimension_ratio: number;           // 当前学生的 R/M 比例
    current_difficulty: number;        // 当前完成题的难度
    target_difficulty: number;         // 推荐的基准难度
    generation_time_ms: number;        // 推荐生成耗时
  };
}

interface RecommendedProblem {
  problem_id: string;
  problem_text: string;               // 题目文本（LaTeX）
  topic: string[];
  difficulty: number;                 // 1-5
  primary_dimension: "RESOURCE" | "METACOGNITIVE";
  resource_weight: number;
  metacognitive_weight: number;
  why_recommended: string;             // 推荐理由（用于学生端展示）
  rank: number;                        // 排名 1-3
  score_breakdown?: {
    dim_score: number;
    diff_score: number;
    recency_score: number;
    quality_score: number;
  };
}

interface RecommendationStrategy {
  label: string;                       // 策略名称
  dimension_ratio_target: { r: number; m: number };
  description: string;               // 策略描述
  adjustment_reason: string;          // 为什么采用这个策略
}
```

### 4.2 典型响应示例

```json
{
  "success": true,
  "data": {
    "recommendations": [
      {
        "problem_id": "alg_seq_007",
        "problem_text": "已知数列 {a_n} 满足 a_1 = 2, a_{n+1} = 3a_n + 1，求其通项公式。",
        "topic": ["数列", "递推数列", "通项公式"],
        "difficulty": 3,
        "primary_dimension": "RESOURCE",
        "resource_weight": 0.75,
        "metacognitive_weight": 0.25,
        "why_recommended": "前一道题（alg_seq_001）为基础递推求通项，这道题需要构造等比数列的思路，属于同知识点递进，难度 +1",
        "rank": 1,
        "score_breakdown": {
          "dim_score": 0.88,
          "diff_score": 1.00,
          "recency_score": 0.60,
          "quality_score": 0.85
        }
      },
      {
        "problem_id": "alg_seq_012",
        "problem_text": "设数列 {a_n} 满足 a_1 = 1, a_2 = 4, a_{n+2} = 3a_{n+1} - 2a_n，求通项。",
        "topic": ["数列", "线性递推", "二阶递推"],
        "difficulty": 4,
        "primary_dimension": "RESOURCE",
        "resource_weight": 0.70,
        "metacognitive_weight": 0.30,
        "why_recommended": "二阶递推与一阶递推有相同的知识结构（构造+化归），但复杂度更高，适合挑战",
        "rank": 2,
        "score_breakdown": {
          "dim_score": 0.82,
          "diff_score": 0.80,
          "recency_score": 1.00,
          "quality_score": 0.90
        }
      }
    ],
    "strategy": {
      "label": "R型递进（同知识点+难度+1）",
      "dimension_ratio_target": { "r": 0.70, "m": 0.30 },
      "description": "学生 dimension_ratio=0.72（偏R），近3题均为R型，补充R型同知识点题同时引入M型元素",
      "adjustment_reason": "dimension_ratio偏高(>0.65)，需适度引入M型题防止套路化"
    }
  },
  "metadata": {
    "student_id": "student_001",
    "dimension_ratio": 0.72,
    "current_difficulty": 2,
    "target_difficulty": 3,
    "generation_time_ms": 23
  }
}
```

### 4.3 错误响应

```json
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_CANDIDATES",
    "message": "题库中满足条件的候选题不足3道",
    "details": {
      "candidate_count": 1,
      "filters_applied": ["difficulty_filter", "topic_filter"]
    }
  },
  "data": {
    "recommendations": [...],
    "strategy": {...}
  }
}
```

---

## 5. 状态机与触发条件（State Machine）

### 5.1 Module 3 触发时机

Module 3 在以下情况下被触发：

| 触发事件 | 来源 | 说明 |
|---------|------|------|
| `SOLVED` | Module 2 | 学生成功完成一道题，立即推荐下一题 |
| `MAX_ESCALATION` | Module 2 | 学生达到最大干预强度，特殊处理 |
| `ABANDONED` | 学生端 | 学生主动放弃，触发降级推荐 |
| 学生主动请求 | 学生端 | 学生点击"再来一题"按钮 |
| 定期推送 | 定时器 | 每 30 分钟无活动，推送复习题 |

### 5.2 推荐状态

```typescript
enum RecommendationStatus {
  READY = "READY",           // 正常推荐状态
  RERCOMMENDING = "RERCOMMENDING",  // 推荐生成中
  INSUFFICIENT = "INSUFFICIENT",    // 候选不足
  EMPTY = "EMPTY",           // 题库为空
  ERROR = "ERROR"             // 推荐失败
}
```

---

## 6. 非功能需求（Non-Functional Requirements）

| 指标 | 要求 | 说明 |
|------|------|------|
| **响应延迟** | < 100ms（P95） | 推荐计算（特别是题库过滤+排序）应在 100ms 内完成 |
| **题库规模** | 支持 ≥ 1000 道题 | 每道题标注完整元数据 |
| **推荐多样性** | top-3 中至少 1 道与最近 3 题不同 topic | 防止推荐过于集中 |
| **可解释性** | 每道推荐题附带 `why_recommended` 说明 | 帮助学生理解推荐意图 |
| **降级能力** | 题库为空时降级到 related_problems | 确保始终有内容可推荐 |
| **新学生冷启动** | 有默认策略（50/50，难度2） | 不依赖历史数据 |

---

## 7. 与 Module 2 / Module 4 的接口（Module Interface）

### 7.1 从 Module 4 读取

```python
# Module 4 Profile Repository
class StudentProfileRepo:
    def get_profile(self, student_id: str) -> StudentProfile | None:
        """读取学生完整画像"""

    def get_dimension_ratio(self, student_id: str) -> float:
        """读取当前的 R/M 比例（0.0-1.0）"""

    def get_recent_problems(self, student_id: str, limit: int = 10) -> list[str]:
        """读取最近 N 道题的 problem_id 列表"""

    def get_topic_mastery(self, student_id: str) -> dict[str, float]:
        """读取各知识点的掌握度（0.0-1.0），用于前置知识过滤"""
```

### 7.2 从 Module 2 接收触发

```python
# Module 3 接收来自 Module 2 的事件
class RecommendationTrigger:
    def on_intervention_end(
        self,
        student_id: str,
        problem_id: str,
        outcome: "SOLVED" | "MAX_ESCALATION" | "ABANDONED",
        final_dimension: "RESOURCE" | "METACOGNITIVE",
        final_level: str,
        intervention_count: int
    ) -> RecommendResponse:
        """Module 2 干预结束时调用，触发推荐"""
```

### 7.3 输出到学生端

```python
# Module 3 输出到学生端/前端
class RecommendationOutput:
    def push_to_student(
        self,
        student_id: str,
        recommendations: list[RecommendedProblem],
        channel: "app" | "web" | "notification"
    ) -> bool:
        """推送推荐结果到学生端"""
```

---

## 8. 评估指标（Evaluation Metrics）

### 8.1 推荐效果指标

| 指标 | 定义 | 目标 | 采集方式 |
|------|------|------|---------|
| **推荐接受率** | 学生点击推荐的题 / 总推荐次数 | > 60% | 埋点 |
| **推荐完成率** | 学生完成推荐的题 / 接受的题 | > 70% | 埋点 |
| **维度平衡度** | 学生的 dimension_ratio 标准差（跨 session） | < 0.15 | MongoDB profile 数据分析 |
| **难度匹配度** | 学生完成推荐题难度 vs. 推荐难度的偏差 | 平均偏差 < 0.5 级 | 埋点 |
| **多样性指数** | top-3 中不同 topic 数 / 3 | 平均 > 2.0 | 埋点 |

### 8.2 系统性能指标

| 指标 | 目标 | 告警阈值 |
|------|------|---------|
| P50 延迟 | < 20ms | > 50ms |
| P95 延迟 | < 100ms | > 200ms |
| 题库查询超时率 | < 0.1% | > 1% |

---

## 9. 题库建设计划（Problem Bank Roadmap）

Module 3 的效果直接依赖题库质量。建议分阶段建设：

| 阶段 | 题库规模 | 标注完成度 | 时间 |
|------|---------|-----------|------|
| Phase 1（当前） | 15 道题（用于测试） | difficulty + topic | 第 1-2 周 |
| Phase 2 | 100 道题 | difficulty + topic + dimension_weight | 第 3-6 周 |
| Phase 3 | 500 道题 | 全部字段 + 人工审核 | 第 7-12 周 |
| Phase 4 | 1000+ 道题 | 持续扩充 + 学生反馈校准 | 第 13 周后 |

---

## 10. 风险与备选（Risks & Alternatives）

| 风险 | 概率 | 影响 | 备选方案 |
|------|------|------|---------|
| 题库题量不足（< 50 道） | 中 | 高 | Phase 1 用 15 道题测试；降级到 related_problems；扩大题库 |
| dimension_ratio 计算不准 | 中 | 中 | 暂时固定为 0.5（均衡策略）；收集反馈后校准 |
| 推荐过于集中（多样性不足） | 低 | 中 | 强制 top-3 中至少 1 道来自不同 topic |
| 新学生无历史（冷启动） | 高 | 低 | 默认策略（50/50，难度2）；3 道后建立稳定 profile |
| 前置知识过滤依赖 Module 4 | 中 | 低 | Module 4 未就绪时，跳过该过滤规则 |

---

## 附录 A：推荐策略配置表

| 策略名称 | dimension_ratio 范围 | R 型% | M 型% | 难度策略 |
|---------|---------------------|-------|-------|---------|
| `R_BALANCED` | 0.55-0.65 | 60% | 40% | +1 |
| `R_DOMINANT` | 0.65-0.80 | 70% | 30% | +1（部分+2） |
| `R_SEVERE` | > 0.80 | 85% | 15% | -1（补基础） |
| `M_BALANCED` | 0.35-0.45 | 40% | 60% | +1 |
| `M_DOMINANT` | 0.20-0.35 | 30% | 70% | +1（部分+2） |
| `M_SEVERE` | < 0.20 | 15% | 85% | -1（补策略） |
| `NEUTRAL` | 0.45-0.55 | 50% | 50% | +1 |
| `NEW_STUDENT` | 无历史 | 50% | 50% | 从 2 开始 |

---

## 附录 B：错误码

| Code | HTTP Status | Description | 用户可见信息 |
|------|-------------|-------------|------------|
| `SUCCESS` | 200 | 推荐成功 | — |
| `INSUFFICIENT_CANDIDATES` | 200 | 候选不足（但仍返回结果） | "候选题不足，以下为最优推荐" |
| `EMPTY_BANK` | 200 | 题库为空 | "题库暂无内容，请稍后再试" |
| `PROFILE_NOT_FOUND` | 200 | 学生 profile 不存在（新学生） | 使用默认策略 |
| `INTERNAL_ERROR` | 500 | 内部错误（题库查询失败等） | "推荐服务暂时不可用" |
| `TIMEOUT` | 504 | 题库查询超时 | "推荐服务响应超时，请重试" |
