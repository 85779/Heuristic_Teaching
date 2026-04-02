# Module 3: 智能练习题推荐系统设计文档

**版本**: v1
**核心功能**: 基于学生维度画像的智能练习题推荐引擎
**最后更新**: 2026-03-30

---

## 1. 架构图与数据流（Architecture Diagram & Data Flow）

### 1.1 整体推荐管道流程

```
学生完成一道题（SOLVED / MAX_ESCALATION）
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 1: StudentProfileLoader（读取学生画像）                          │
│  输入: student_id                                                      │
│  输出: StudentProfile { dimension_ratio, recent_problems,              │
│                          weak_dimensions, current_difficulty }         │
│  数据来源: Module 4 的 MongoDB collections                             │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 2: CandidateRetrieval（候选题检索）                               │
│  输入: student_profile, current_problem_result                        │
│  输出: CandidateProblemSet（≤ 20 道候选题）                            │
│  逻辑: 硬过滤（同题/太近/难度跳级/前置知识缺失）                        │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 3: DimensionScorer（维度平衡打分）                               │
│  输入: candidate, student_profile, target_dimension                   │
│  输出: dim_score（0.0-1.0）                                           │
│  逻辑: 根据 dimension_ratio 偏离均衡的程度，动态调整 R/M 题目权重       │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 4: DifficultyScorer（难度递进打分）                              │
│  输入: candidate, target_difficulty                                   │
│  输出: diff_score（0.0-1.0）                                          │
│  逻辑: 目标难度 = min(current_difficulty + 1, 5)，偏差越大分数越低      │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 5: SpacedRepetitionScorer（间隔重复打分）                        │
│  输入: candidate, recent_problems                                      │
│  输出: recency_score（0.0-1.0）                                       │
│  逻辑: 同一知识点在最近 N 题中出现的次数越多，分数越低                  │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 6: QualityScorer（题目质量打分）                                 │
│  输入: candidate                                                      │
│  输出: quality_score（0.0-1.0，直接复用题库标注值）                     │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 7: RankingEngine（综合排序）                                     │
│  输入: 所有候选题的 4 项得分                                            │
│  输出: RankedProblemList（top-3）                                     │
│  逻辑: score = 0.4×dim + 0.3×diff + 0.2×recency + 0.1×quality         │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
推荐结果 ──► 学生端显示 + 写入推荐历史
```

### 1.2 与其他模块的交互关系

```
Module 1 (组织化解题)
         │
         ▼
Module 2 (断点干预系统)  ───────────────────────────────────┐
         │                                                          │
         ▼                                                          ▼
Module 3 (智能推荐系统)              Module 4 (学生画像)      Module 5 (教学策略)
    │                          （R/M维度画像存储）           （讲授/练习/讨论）
    │                                                              │
    └────── 触发推荐 ──► 推荐结果推送 ──► 学生端                  │
    │                                                              │
    └────── 更新推荐历史 ──► MongoDB                              │
```

### 1.3 数据流摘要

| 阶段 | 输入 | 输出 | 关键决策 |
|------|------|------|----------|
| ProfileLoader | student_id | StudentProfile | 维度比例 + 当前难度 |
| CandidateRetrieval | student_profile, trigger | 候选集（≤20） | 4 项硬过滤 |
| DimensionScorer | candidate, profile | dim_score | R/M 权重分配 |
| DifficultyScorer | candidate, target | diff_score | 难度偏差计算 |
| SpacedRepetitionScorer | candidate, recent | recency_score | 间隔新鲜度 |
| QualityScorer | candidate | quality_score | 直接复用 |
| RankingEngine | 4 项得分 | top-3 排名 | 加权求和 |

---

## 2. 核心算法设计（Core Algorithm Design）

### 2.1 维度平衡算法（Dimension Balancing）

**文件**: `scorer/dimension_scorer.py`
**职责**: 根据学生当前的 R/M 维度画像，动态调整推荐题的 R/M 比例

#### 2.1.1 维度比例计算

学生的 `dimension_ratio` 定义为 R 型断点占总断点的比例：

```
dimension_ratio = R 型断点总数 / 总断点数
```

- `dimension_ratio > 0.65`：学生偏 R 型（Resource 薄弱），应多推荐 M 型题
- `dimension_ratio < 0.35`：学生偏 M 型（Metacognitive 薄弱），应多推荐 R 型题
- `0.35 ≤ dimension_ratio ≤ 0.65`：维度均衡，维持平衡策略

#### 2.1.2 维度偏离度计算

```python
def calculate_dimension_focus_strength(dimension_ratio: float) -> float:
    """
    计算学生当前维度偏离均衡的程度
    
    参数:
        dimension_ratio: R 型断点比例（0.0-1.0）
    
    返回:
        focus_strength: 偏离度（0.0=完全均衡，1.0=完全偏向某一侧）
    
    算法:
        - 均衡点为 0.5
        - 偏离度 = |dimension_ratio - 0.5| × 2
        - 即：均衡时偏离度=0，一侧极化时偏离度=1
    """
    equilibrium = 0.5
    focus_strength = abs(dimension_ratio - equilibrium) * 2
    return focus_strength
```

#### 2.1.3 目标维度确定

```python
def determine_target_dimension(
    dimension_ratio: float,
    current_dimension: str
) -> str:
    """
    确定下一道题的目标维度
    
    策略:
        - 严重偏 R（> 0.80）：目标维度 = METACOGNITIVE（补充元认知）
        - 偏 R（> 0.65）：维持 current_dimension（继续强化同类）
        - 均衡（0.35-0.65）：目标维度 = current_dimension（维持当前节奏）
        - 偏 M（< 0.35）：目标维度 = current_dimension（继续强化同类）
        - 严重偏 M（< 0.20）：目标维度 = RESOURCE（补充资源型）
    """
    if dimension_ratio > 0.80:
        return "METACOGNITIVE"
    elif dimension_ratio > 0.65:
        return current_dimension
    elif dimension_ratio < 0.20:
        return "RESOURCE"
    elif dimension_ratio < 0.35:
        return current_dimension
    else:
        return current_dimension
```

#### 2.1.4 维度分数计算

```python
def dimension_balance_score(
    problem_primary_dimension: str,
    target_dimension: str,
    dimension_focus_strength: float
) -> float:
    """
    计算维度匹配分数
    
    参数:
        problem_primary_dimension: 题目主维度（R 或 M）
        target_dimension: 目标维度（R 或 M）
        dimension_focus_strength: 维度偏离度（0.0-1.0）
    
    返回:
        dim_score: 维度匹配分数（0.0-1.0）
    
    算法:
        - 匹配（题目维度 = 目标维度）：
          dim_score = 0.8 + 0.2 × dimension_focus_strength
          说明：偏离度越高，越需要同维度强化
        - 不匹配（题目维度 ≠ 目标维度）：
          dim_score = 0.4 + 0.2 × (1 - dimension_focus_strength)
          说明：偏离度越高，越不鼓励跨维度（维持当前节奏）
    """
    if problem_primary_dimension == target_dimension:
        # 匹配：高分，偏离度越高分数越高
        dim_score = 0.8 + 0.2 * dimension_focus_strength
    else:
        # 不匹配：低分，偏离度越高分数越低
        dim_score = 0.4 + 0.2 * (1 - dimension_focus_strength)
    
    return dim_score
```

---

### 2.2 难度递进算法（Difficulty Progression）

**文件**: `scorer/difficulty_scorer.py`
**职责**: 确保推荐题难度适度递增，实现 i+1 挑战原则

#### 2.2.1 目标难度计算

```python
def calculate_target_difficulty(current_difficulty: int) -> int:
    """
    计算推荐题的目标难度
    
    参数:
        current_difficulty: 学生刚完成题目的难度（1-5）
    
    返回:
        target_difficulty: 推荐题的目标难度
    
    算法:
        - 目标难度 = min(current_difficulty + 1, 5)
        - 确保每次推荐都有适度挑战，但不跳跃过大
    """
    target = current_difficulty + 1
    return min(target, 5)
```

#### 2.2.2 难度分数计算

```python
def difficulty_score(
    problem_difficulty: int,
    target_difficulty: int
) -> float:
    """
    计算难度匹配分数
    
    参数:
        problem_difficulty: 候选题的难度（1-5）
        target_difficulty: 目标难度（1-5）
    
    返回:
        diff_score: 难度匹配分数（0.0-1.0）
    
    算法:
        diff_score = 1 - |target_difficulty - problem_difficulty| / 5
    
    示例:
        - 完全匹配（|差|=0）：diff_score = 1.0
        - 差 1 级：diff_score = 0.8
        - 差 2 级：diff_score = 0.6
        - 差 3 级：diff_score = 0.4
        - 差 4 级：diff_score = 0.2
    """
    diff = abs(target_difficulty - problem_difficulty)
    diff_score = 1 - (diff / 5)
    return diff_score
```

#### 2.2.3 边界处理

```python
def adjust_target_difficulty_for_escalation(
    current_difficulty: int,
    outcome: str
) -> int:
    """
    根据干预结果调整目标难度
    
    参数:
        current_difficulty: 当前完成题难度
        outcome: 干预结果（SOLVED / MAX_ESCALATION / ABANDONED）
    
    返回:
        adjusted_target_difficulty: 调整后的目标难度
    
    策略:
        - SOLVED：正常递进 +1
        - MAX_ESCALATION：降 1-2 级（学生遇到瓶颈，需要降难度建立信心）
        - ABANDONED：降 1 级（学生主动放弃，可能难度过高）
    """
    if outcome == "MAX_ESCALATION":
        # 降到比当前更难1级，而非再+1
        return max(current_difficulty - 1, 1)
    elif outcome == "ABANDONED":
        return max(current_difficulty, 1)
    else:
        return min(current_difficulty + 1, 5)
```

---

### 2.3 间隔重复算法（Spaced Repetition）

**文件**: `scorer/spaced_repetition_scorer.py`
**职责**: 避免推荐过于集中于同一知识点，防止套路固化

#### 2.3.1 新鲜度分数计算

```python
def spaced_repetition_score(
    problem_topic: str,
    recent_problems: list[dict],
    topic_tree: str
) -> float:
    """
    计算间隔重复分数（新鲜度分数）
    
    参数:
        problem_topic: 候选题的知识点标签（string[]）
        recent_problems: 最近 N 道题的 problem_id + topic 列表
        topic_tree: 候选题的知识点树路径（如"代数/数列/通项公式"）
    
    返回:
        recency_score: 新鲜度分数（0.0-1.0）
    
    算法:
        - 统计候选题知识点在 recent_problems 中最近 1/3/5 题的出现次数
        - 如果最近 1 题出现：recency_score = 0.3（太近，降低权重）
        - 如果最近 3 题出现：recency_score = 0.6
        - 如果最近 5 题出现：recency_score = 0.8
        - 如果均未出现：recency_score = 1.0（全新内容，高分）
    
    额外规则:
        - 同一 topic_tree 叶子节点视为同一知识点
        - 同一 topic 根节点（如"数列"）也视为重复
    """
    # 提取最近 1/3/5 题的 topic 列表
    recent_1 = set()
    recent_3 = set()
    recent_5 = set()
    
    for i, p in enumerate(recent_problems):
        topics = set(p.get("topics", []))
        # 提取 topic_tree 的叶子节点
        if "topic_tree" in p:
            leaf = p["topic_tree"].split("/")[-1]
            topics.add(leaf)
        
        if i < 1:
            recent_1.update(topics)
        if i < 3:
            recent_3.update(topics)
        if i < 5:
            recent_5.update(topics)
    
    # 检查候选题知识点是否在 recent 集合中
    candidate_topics = set(problem_topic)
    if topic_tree:
        candidate_topics.add(topic_tree.split("/")[-1])
    
    # 计算最小间隔
    min_distance = float('inf')
    for i, p in enumerate(recent_problems):
        p_topics = set(p.get("topics", []))
        if topic_tree and "topic_tree" in p:
            p_topics.add(p["topic_tree"].split("/")[-1])
        
        if candidate_topics & p_topics:  # 有交集
            min_distance = min(min_distance, i)
    
    # 根据最小距离计算分数
    if min_distance == 0:  # 最近 1 题
        recency_score = 0.3
    elif min_distance == 1 or min_distance == 2:  # 最近 3 题
        recency_score = 0.6
    elif min_distance == 3 or min_distance == 4:  # 最近 5 题
        recency_score = 0.8
    else:  # 未在最近 5 题中出现
        recency_score = 1.0
    
    return recency_score
```

#### 2.3.2 知识点间隔规则

```
同知识点再次出现应间隔至少 3 道题
同类题目（同一 topic_tree 叶子节点）之间应至少间隔 1 道异类题
```

---

### 2.4 综合排序算法（Final Ranking Formula）

**文件**: `engine/ranking_engine.py`
**职责**: 将三项得分加权求和，输出最终排名

#### 2.4.1 最终得分公式

```python
def calculate_final_score(
    dim_score: float,
    diff_score: float,
    recency_score: float,
    quality_score: float
) -> float:
    """
    计算综合得分
    
    公式:
        final_score = w1 × dim_score 
                    + w2 × diff_score 
                    + w3 × recency_score 
                    + w4 × quality_score
    
    权重配置:
        w1 = 0.4  (维度匹配权重) —— 最高权重，维度平衡是核心目标
        w2 = 0.3  (难度匹配权重) —— 次高权重，i+1 递进很重要
        w3 = 0.2  (间隔新鲜度权重) —— 中权重，防止知识遗忘
        w4 = 0.1  (题目质量权重) —— 低权重，仅作为微调因子
    
    参数:
        dim_score: 维度匹配分数（0.0-1.0）
        diff_score: 难度匹配分数（0.0-1.0）
        recency_score: 间隔新鲜度分数（0.0-1.0）
        quality_score: 题目质量分数（0.0-1.0）
    
    返回:
        final_score: 综合得分（0.0-1.0）
    """
    w1, w2, w3, w4 = 0.4, 0.3, 0.2, 0.1
    
    final_score = (
        w1 * dim_score +
        w2 * diff_score +
        w3 * recency_score +
        w4 * quality_score
    )
    
    return final_score
```

#### 2.4.2 排序与截断

```python
def rank_problems(candidates: list[CandidateProblem]) -> list[CandidateProblem]:
    """
    对候选题按综合得分降序排序，返回 top-3
    
    参数:
        candidates: 通过硬过滤的候选题列表
    
    返回:
        ranked: 排序后的 top-3 列表
    
    规则:
        - 按 final_score 降序排列
        - 取前 3 道题（不足 3 道时返回全部）
        - 同时确保 top-3 中至少有 1 道与最近 3 题不同 topic
          （多样性保护，如果 top-3 全部重复，则强制替换 1 道）
    """
    # 按综合得分降序排序
    ranked = sorted(candidates, key=lambda p: p.final_score, reverse=True)
    
    # 截取 top-3
    top_3 = ranked[:3]
    
    # 多样性保护：确保至少 1 道题与最近 3 题不同 topic
    recent_topics = set()
    for p in candidates[:3]:  # 使用原始顺序的前3题作为"最近"
        recent_topics.update(p.topic)
    
    diversity_count = sum(1 for p in top_3 if not (set(p.topic) & recent_topics))
    
    if diversity_count == 0 and len(candidates) > 3:
        # 全部重复，强制替换为非重复题
        for i, p in enumerate(ranked[3:], start=3):
            if set(p.topic) & recent_topics:
                continue
            top_3[2] = p  # 替换最后一道
            break
    
    return top_3
```

---

## 3. 候选题过滤规则（Candidate Filtering）

**文件**: `retriever/candidate_retriever.py`
**职责**: 在打分前过滤掉不符合硬约束的候选题

### 3.1 四项硬过滤规则

```python
def apply_hard_filters(
    problem: ProblemMetadata,
    recent_problems: list[str],
    student_topic_mastery: dict[str, float],
    target_difficulty: int
) -> tuple[bool, str]:
    """
    应用硬过滤规则
    
    参数:
        problem: 候选题元数据
        recent_problems: 最近 10 道题的 problem_id 列表
        student_topic_mastery: 学生各知识点掌握度（来自 Module 4）
        target_difficulty: 目标难度
    
    返回:
        (passed: bool, reason: str): 是否通过过滤及原因
    
    过滤规则:
        1. 同题过滤：problem_id 在 recent_problems 中 → 排除
        2. 太近过滤：与最近 2 题属于同一 topic_tree 叶子节点 → 排除
        3. 难度跳级过滤：|target_difficulty - problem.difficulty| > 2 → 排除
        4. 前置知识缺失：prerequisite_topics 中有未掌握知识点 → 排除
    """
    
    # 规则 1：同题过滤
    if problem.problem_id in recent_problems:
        return False, "同题过滤：与最近做过的题相同"
    
    # 规则 2：太近过滤（检查最近 2 题）
    for recent in recent_problems[:2]:
        if recent.topic_tree and problem.topic_tree:
            recent_leaf = recent.topic_tree.split("/")[-1]
            problem_leaf = problem.topic_tree.split("/")[-1]
            if recent_leaf == problem_leaf:
                return False, "太近过滤：与最近 2 题同知识点"
    
    # 规则 3：难度跳级过滤
    if abs(target_difficulty - problem.difficulty) > 2:
        return False, f"难度跳级过滤：难度差{abs(target_difficulty - problem.difficulty)}过大"
    
    # 规则 4：前置知识缺失过滤
    for topic in problem.prerequisite_topics:
        mastery = student_topic_mastery.get(topic, 0.0)
        if mastery < 0.5:  # 掌握度低于 50% 视为未掌握
            return False, f"前置知识缺失：{topic} 掌握度不足"
    
    return True, "通过"
```

---

## 4. 模块结构与组件职责（Module Structure）

**目录**: `backend/app/modules/recommendation/`

```
backend/app/modules/recommendation/
│
├── __init__.py                      # 模块导出
├── module.py                        # 模块入口（initialize/shutdown/router 注册）
├── routes.py                        # FastAPI 路由
├── service.py                       # 主服务编排（RecommendationService）
├── models.py                        # Pydantic + dataclass 模型
│
├── profile/                         # Step 1：学生画像读取
│   ├── __init__.py
│   ├── loader.py                    # StudentProfileLoader（读取 Module 4 数据）
│   └── models.py                    # StudentProfile, DimensionRatio
│
├── retriever/                       # Step 2：候选题检索
│   ├── __init__.py
│   ├── candidate_retriever.py      # CandidateRetrieval（硬过滤引擎）
│   └── models.py                    # CandidateProblem
│
├── scorer/                          # Step 3-6：打分组件
│   ├── __init__.py
│   ├── dimension_scorer.py         # DimensionScorer（维度平衡）
│   ├── difficulty_scorer.py         # DifficultyScorer（难度递进）
│   ├── spaced_repetition_scorer.py  # SpacedRepetitionScorer（间隔重复）
│   ├── quality_scorer.py            # QualityScorer（题目质量）
│   └── models.py                    # ScoreBreakdown
│
├── engine/                          # Step 7：排序引擎
│   ├── __init__.py
│   ├── ranking_engine.py            # RankingEngine（综合排序）
│   └── strategy_selector.py         # StrategySelector（策略选择）
│
├── triggers/                       # 触发器
│   ├── __init__.py
│   ├── intervention_trigger.py      # 监听 Module 2 的 SOLVED/MAX_ESCALATION
│   └── student_trigger.py           # 监听学生主动请求
│
├── output/                          # 输出
│   ├── __init__.py
│   ├── recommender.py               # 推荐结果推送（到学生端）
│   └── notifier.py                  # 推送通知（可选）
│
└── infrastructure/
    └── database/
        └── repositories/
            ├── recommendation_repo.py   # MongoDB 推荐历史持久化
            └── problem_bank_repo.py     # MongoDB 题库访问
```

### 4.1 各组件职责

| 组件 | 文件 | 职责 |
|------|------|------|
| **StudentProfileLoader** | `profile/loader.py` | 从 Module 4 读取学生维度画像 |
| **CandidateRetrieval** | `retriever/candidate_retriever.py` | 从题库检索候选题，应用硬过滤 |
| **DimensionScorer** | `scorer/dimension_scorer.py` | 计算维度匹配分数 |
| **DifficultyScorer** | `scorer/difficulty_scorer.py` | 计算难度匹配分数 |
| **SpacedRepetitionScorer** | `scorer/spaced_repetition_scorer.py` | 计算间隔新鲜度分数 |
| **QualityScorer** | `scorer/quality_scorer.py` | 复用题库标注的质量分数 |
| **RankingEngine** | `engine/ranking_engine.py` | 加权求和，输出 top-3 |
| **StrategySelector** | `engine/strategy_selector.py` | 根据 dimension_ratio 选择推荐策略 |
| **InterventionTrigger** | `triggers/intervention_trigger.py` | 监听 Module 2 事件，触发推荐 |
| **RecommendationOutput** | `output/recommender.py` | 推送推荐结果到学生端 |

---

## 5. MongoDB 数据模型（Data Models）

**数据库**: `math_tutor`
**集合**: `student_recommendation_history`, `problem_bank`

### 5.1 `student_recommendation_history` 集合

存储学生的推荐历史，用于后续分析和 profile 更新。

```javascript
{
  "_id": ObjectId,
  "student_id": "string",                    // 学生 ID（索引）
  "session_id": "string",                    // 推荐触发所属 session
  "trigger_event": "SOLVED" | "MAX_ESCALATION" | "ABANDONED" | "MANUAL",
  "trigger_timestamp": ISODate,              // 触发时间
  
  // 触发时的学生状态
  "student_state": {
    "dimension_ratio": 0.72,                 // 当时的 R/M 比例
    "current_difficulty": 2,                 // 刚完成题的难度
    "current_dimension": "RESOURCE",         // 刚完成题的主维度
    "recent_problems": [                     // 最近 10 题
      {
        "problem_id": "alg_seq_001",
        "topic": ["数列", "通项公式"],
        "topic_tree": "代数/数列/通项公式",
        "difficulty": 2,
        "primary_dimension": "RESOURCE",
        "solved_at": ISODate
      }
    ]
  },
  
  // 推荐结果
  "recommendations": [
    {
      "rank": 1,
      "problem_id": "alg_seq_007",
      "final_score": 0.82,
      "score_breakdown": {
        "dim_score": 0.88,
        "diff_score": 1.00,
        "recency_score": 0.60,
        "quality_score": 0.85
      },
      "recommended_at": ISODate
    },
    {
      "rank": 2,
      "problem_id": "alg_seq_012",
      "final_score": 0.76,
      "score_breakdown": {...},
      "recommended_at": ISODate
    }
  ],
  
  // 策略信息
  "strategy_applied": {
    "label": "R型递进（同知识点+难度+1）",
    "dimension_ratio_target": { "r": 0.70, "m": 0.30 },
    "adjustment_reason": "dimension_ratio偏高(>0.65)，需适度引入M型题防止套路化"
  },
  
  // 学生反馈（后续更新）
  "student_feedback": {
    "accepted_problem_id": "alg_seq_007",    // 学生接受的题
    "rejected_problem_ids": [],              // 学生拒绝的题
    "feedback_at": ISODate
  },
  
  "created_at": ISODate
}
```

**索引**:

```javascript
// 学生查询（最频繁）
db.student_recommendation_history.createIndex({ "student_id": 1, "created_at": -1 })

// Session 查询
db.student_recommendation_history.createIndex({ "session_id": 1 })

// 触发事件统计
db.student_recommendation_history.createIndex({ "trigger_event": 1, "created_at": -1 })
```

### 5.2 `problem_bank` 集合

题库，存储所有可推荐题目的元数据。

```javascript
{
  "_id": ObjectId,
  "problem_id": "alg_seq_001",               // 全局唯一 ID（索引）
  
  // 题目内容
  "problem_text": "已知数列 {a_n} 满足 a_1 = 2, a_{n+1} = 3a_n + 1，求其通项公式。",
  
  // 知识点标注
  "topic": ["数列", "通项公式"],             // 知识点标签
  "topic_tree": "代数/数列/通项公式",         // 知识点树路径
  "prerequisite_topics": ["代数基础"],        // 前置知识点
  
  // 难度与维度
  "difficulty": 2,                            // 难度等级（1-5，人工标注）
  "primary_dimension": "RESOURCE",           // 主维度（R/M）
  "resource_weight": 0.75,                   // 资源型特征权重（0-1）
  "metacognitive_weight": 0.25,              // 元认知型特征权重（0-1）
  
  // 题目类型
  "problem_type": "求解题",                   // 题目类型
  "related_problems": [                       // 变式题 ID
    "alg_seq_002",
    "alg_seq_003"
  ],
  
  // 质量与预计时间
  "quality_score": 0.85,                     // 题目质量分（0-1）
  "estimated_time_minutes": 10,             // 预计完成时间（分钟）
  
  // 统计字段
  "usage_count": 42,                         // 被推荐次数
  "completion_rate": 0.78,                   // 完成率
  "avg_difficulty_rating": 2.1,             // 学生评分平均难度
  
  // 状态
  "status": "active",                        // active | deprecated | hidden
  
  "created_at": ISODate,
  "updated_at": ISODate
}
```

**索引**:

```javascript
// problem_id 查询（最频繁）
db.problem_bank.createIndex({ "problem_id": 1 }, { unique: true })

// 维度 + 难度 组合查询
db.problem_bank.createIndex({ "primary_dimension": 1, "difficulty": 1 })

// 知识点查询
db.problem_bank.createIndex({ "topic": 1 })
db.problem_bank.createIndex({ "topic_tree": 1 })

// 质量筛选
db.problem_bank.createIndex({ "quality_score": -1 })

// 状态 + 使用次数
db.problem_bank.createIndex({ "status": 1, "usage_count": -1 })
```

### 5.3 典型查询模式

```python
# 获取学生最近推荐历史
await collection.find(
    {"student_id": student_id}
).sort("created_at", -1).limit(10)

# 获取题库中某维度的候选题
await collection.find({
    "primary_dimension": target_dimension,
    "difficulty": {"$gte": target_difficulty - 2, "$lte": target_difficulty + 2},
    "status": "active"
}).to_list(20)

# 按 topic_tree 查找变式题
await collection.find({
    "topic_tree": topic_tree,
    "problem_id": {"$ne": exclude_problem_id}
}).to_list(5)

# 统计某学生的维度比例
pipeline = [
    {"$match": {"student_id": student_id}},
    {"$unwind": "$student_state.recent_problems"},
    {"$group": {
        "_id": "$student_state.recent_problems.primary_dimension",
        "count": {"$sum": 1}
    }}
]
```

---

## 6. 外部接口（External Interfaces）

### 6.1 从 Module 4 读取学生画像

**文件**: `profile/loader.py`

```python
class StudentProfileRepo:
    """Module 4 学生画像仓储接口"""
    
    async def get_profile(self, student_id: str) -> StudentProfile | None:
        """
        读取学生完整画像
        
        来源: Module 4 的 MongoDB collections
        
        返回:
            StudentProfile: 包含 dimension_ratio, recent_problems, weak_dimensions 等
            None: 学生不存在（新学生）
        """
    
    async def get_dimension_ratio(self, student_id: str) -> float:
        """
        读取当前的 R/M 比例（0.0-1.0）
        
        计算公式:
            dimension_ratio = R 型断点总数 / 总断点数
        
        边界情况:
            - 新学生（无历史）: 返回 0.5（均衡）
            - dimension_ratio 异常（<0.05 或 >0.95）: 返回 0.5
        """
    
    async def get_recent_problems(
        self, 
        student_id: str, 
        limit: int = 10
    ) -> list[dict]:
        """
        读取最近 N 道题的 problem_id 列表
        
        返回字段:
            - problem_id: 题目 ID
            - topic: 知识点标签
            - topic_tree: 知识点树路径
            - difficulty: 难度等级
            - primary_dimension: 主维度
            - solved_at: 完成时间
        """
    
    async def get_topic_mastery(
        self, 
        student_id: str
    ) -> dict[str, float]:
        """
        读取各知识点的掌握度（0.0-1.0）
        
        用于前置知识过滤：
            - 掌握度 < 0.5 的知识点对应的题不会被推荐
            - Module 4 未就绪时返回空字典（跳过前置知识过滤）
        """
```

### 6.2 从 Module 2 接收触发事件

**文件**: `triggers/intervention_trigger.py`

```python
class RecommendationTrigger:
    """Module 3 接收来自 Module 2 的触发"""
    
    async def on_intervention_end(
        self,
        student_id: str,
        session_id: str,
        problem_id: str,
        outcome: "SOLVED" | "MAX_ESCALATION" | "ABANDONED",
        final_dimension: "RESOURCE" | "METACOGNITIVE",
        final_level: str,                      # R1-R4 或 M1-M5
        intervention_count: int
    ) -> RecommendResponse:
        """
        Module 2 干预结束时调用，触发推荐流程
        
        调用时机:
            - Module 2 返回 SOLVED 时：正常推荐流程
            - Module 2 返回 MAX_ESCALATION 时：降级推荐策略
            - Module 2 返回 ABANDONED 时：降低难度推荐
        
        参数:
            student_id: 学生 ID
            session_id: Session ID
            problem_id: 刚完成/放弃的题目 ID
            outcome: 干预结果
            final_dimension: 断点的主维度（R/M）
            final_level: 断点的具体级别（R1-R4/M1-M5）
            intervention_count: 本次干预的提示次数
        
        返回:
            RecommendResponse: 推荐结果（top-3 ranked list）
        """
    
    def register_trigger(
        self,
        event: str,
        callback: callable
    ) -> None:
        """
        注册触发回调
        
        Module 2 在以下时机触发:
            - intervention_end (SOLVED / MAX_ESCALATION / ABANDONED)
            - 学生主动请求"再来一题"
        
        注册方式（Module 2 调用）:
            recommendation_trigger.register_trigger(
                event="intervention_end",
                callback=self.on_intervention_end
            )
        """
```

### 6.3 输出到学生端

**文件**: `output/recommender.py`

```python
class RecommendationOutput:
    """Module 3 输出到学生端"""
    
    async def push_to_student(
        self,
        student_id: str,
        recommendations: list[RecommendedProblem],
        channel: "app" | "web" | "notification"
    ) -> bool:
        """
        推送推荐结果到学生端
        
        参数:
            student_id: 学生 ID
            recommendations: 推荐的题目列表（top-3）
            channel: 推送渠道
                - app: 应用内推送
                - web: Web 端通知
                - notification: 系统通知
        
        返回:
            success: 是否推送成功
        """
    
    async def record_feedback(
        self,
        recommendation_history_id: str,
        student_id: str,
        accepted_problem_id: str | None,
        rejected_problem_ids: list[str]
    ) -> None:
        """
        记录学生对推荐结果的反馈
        
        用于:
            - 更新推荐历史（student_recommendation_history）
            - 优化后续推荐策略
            - 分析推荐效果指标
        """
```

### 6.4 服务间通信模式

Module 3 与 Module 2、Module 4 的通信采用**异步事件驱动**模式：

```
Module 2 干预结束
    │
    ├──► 触发事件: intervention_end
    │         │
    │         └──► Module 3 RecommendationTrigger.on_intervention_end()
    │                        │
    │                        ├──► StudentProfileLoader（读取 Module 4）
    │                        │
    │                        ├──► CandidateRetrieval（从题库检索）
    │                        │
    │                        ├──► ScoringPipeline（4 项打分）
    │                        │
    │                        ├──► RankingEngine（综合排序）
    │                        │
    │                        └──► RecommendationOutput（推送到学生端）
    │
    └──► 同时更新 Module 4 的学生画像（通过事件）:
              - 更新 recent_problems
              - 更新 dimension_ratio
              - 记录推荐历史
```

---

## 7. 推荐策略配置表（Recommendation Strategy Matrix）

### 7.1 策略映射表

| 策略名称 | dimension_ratio 范围 | R 型% | M 型% | 难度策略 | 典型场景 |
|---------|---------------------|-------|-------|---------|---------|
| `R_BALANCED` | 0.55-0.65 | 60% | 40% | +1 | 轻度偏 R，维持平衡 |
| `R_DOMINANT` | 0.65-0.80 | 70% | 30% | +1（部分+2） | 中度偏 R，同知识点强化 |
| `R_SEVERE` | > 0.80 | 85% | 15% | -1（补基础） | 严重偏 R，降难度补元认知 |
| `M_BALANCED` | 0.35-0.45 | 40% | 60% | +1 | 轻度偏 M，维持平衡 |
| `M_DOMINANT` | 0.20-0.35 | 30% | 70% | +1（部分+2） | 中度偏 M，同知识点强化 |
| `M_SEVERE` | < 0.20 | 15% | 85% | -1（补策略） | 严重偏 M，降难度补资源型 |
| `NEUTRAL` | 0.45-0.55 | 50% | 50% | +1 | 维度均衡 |
| `NEW_STUDENT` | 无历史 | 50% | 50% | 从 2 开始 | 冷启动 |

### 7.2 策略选择算法

```python
def select_strategy(
    dimension_ratio: float | None,
    outcome: str | None
) -> RecommendationStrategy:
    """
    根据学生状态选择推荐策略
    
    参数:
        dimension_ratio: R 型断点比例（None 表示新学生）
        outcome: 干预结果（SOLVED / MAX_ESCALATION / ABANDONED）
    
    返回:
        RecommendationStrategy: 策略配置
    """
    # 新学生
    if dimension_ratio is None:
        return RecommendationStrategy(
            label="NEW_STUDENT",
            r_ratio=0.5,
            m_ratio=0.5,
            difficulty_start=2,
            description="冷启动：50/50 均衡策略"
        )
    
    # MAX_ESCALATION：强制降难度
    if outcome == "MAX_ESCALATION":
        return RecommendationStrategy(
            label="REDUCE_DIFFICULTY",
            r_ratio=0.5,
            m_ratio=0.5,
            difficulty_adjustment=-1,
            description="元认知困难，降难度建立信心"
        )
    
    # ABANDONED：轻度降难度
    if outcome == "ABANDONED":
        return RecommendationStrategy(
            label="REDUCE_DIFFICULTY_MILD",
            r_ratio=0.5,
            m_ratio=0.5,
            difficulty_adjustment=-1,
            description="学生主动放弃，轻度降难度"
        )
    
    # 正常推荐：基于 dimension_ratio 选择策略
    if dimension_ratio > 0.80:
        return RecommendationStrategy(label="R_SEVERE", r_ratio=0.85, m_ratio=0.15, ...)
    elif dimension_ratio > 0.65:
        return RecommendationStrategy(label="R_DOMINANT", r_ratio=0.70, m_ratio=0.30, ...)
    elif dimension_ratio < 0.20:
        return RecommendationStrategy(label="M_SEVERE", r_ratio=0.15, m_ratio=0.85, ...)
    elif dimension_ratio < 0.35:
        return RecommendationStrategy(label="M_DOMINANT", r_ratio=0.30, m_ratio=0.70, ...)
    else:
        return RecommendationStrategy(label="NEUTRAL", r_ratio=0.50, m_ratio=0.50, ...)
```

---

## 8. 服务编排（Service Orchestration）

**文件**: `service.py`

### 8.1 主管道: `recommend()`

```python
async def recommend(
    self,
    student_id: str,
    session_id: str,
    trigger_event: TriggerEvent
) -> RecommendResponse:
    """
    完整推荐流程：
    
    1. 加载学生画像（来自 Module 4）
    2. 选择推荐策略
    3. 检索候选题（硬过滤）
    4. 并行计算 4 项得分
    5. 综合排序（加权求和）
    6. 多样性保护（确保 top-3 足够分散）
    7. 生成推荐理由
    8. 写入推荐历史
    9. 推送到学生端
    
    参数:
        student_id: 学生 ID
        session_id: Session ID
        trigger_event: 触发事件（SOLVED / MAX_ESCALATION / ABANDONED / MANUAL）
    
    返回:
        RecommendResponse: 包含 top-3 推荐结果和策略信息
    """
```

### 8.2 并行打分流水线

```python
async def _score_candidates(
    self,
    candidates: list[CandidateProblem],
    student_profile: StudentProfile,
    strategy: RecommendationStrategy
) -> list[ScoredProblem]:
    """
    并行计算所有候选题的 4 项得分
    
    使用 asyncio.gather 并行执行 4 个打分器:
        - DimensionScorer.score()
        - DifficultyScorer.score()
        - SpacedRepetitionScorer.score()
        - QualityScorer.score()
    
    然后在主线程计算 final_score（加权求和）
    """
    tasks = []
    for candidate in candidates:
        task = self._score_single(candidate, student_profile, strategy)
        tasks.append(task)
    
    scored = await asyncio.gather(*tasks)
    return scored

async def _score_single(...) -> ScoredProblem:
    """对单个候选题计算 4 项得分和综合得分"""
```

---

## 9. 错误处理架构（Error Handling）

### 9.1 边界情况处理

| 情况 | 处理策略 | HTTP 响应码 |
|------|---------|------------|
| 题库候选不足 3 道 | 返回全部可用题，`insufficient_candidates: true` | 200 |
| 题库完全为空 | 返回空列表，触发降级到 related_problems | 200 |
| 学生无历史记录（新学生） | 使用固定策略（50/50，难度从 2 开始） | 200 |
| 所有候选题都被过滤 | 返回 `EMPTY_BANK`，建议人工选题 | 200 |
| dimension_ratio 异常 | 视为新学生处理，reset profile | 200 |
| Module 4 读取失败 | 跳过学生画像读取，使用默认策略 | 200（带警告） |
| MongoDB 查询失败 | 返回 `INTERNAL_ERROR` | 500 |
| 题库查询超时（>100ms） | 返回 `TIMEOUT` | 504 |

### 9.2 降级策略

```python
async def _fallback_recommendation(
    problem_id: str,
    student_profile: StudentProfile
) -> list[RecommendedProblem]:
    """
    题库为空或所有候选都被过滤时的降级策略
    
    策略:
        1. 获取当前题的 related_problems（变式题）
        2. 如果变式题存在，返回变式题列表
        3. 如果变式题也不存在，返回最基础的同知识点题
        4. 完全无题可推时，返回空列表并标注 ERROR
    """
    current_problem = await self._problem_bank.get(problem_id)
    
    if current_problem and current_problem.related_problems:
        # 返回变式题
        related = await self._problem_bank.get_many(
            current_problem.related_problems
        )
        if related:
            return [self._to_recommended(p) for p in related]
    
    # 尝试返回同 topic 的基础题
    base_problems = await self._problem_bank.get_by_topic(
        topic=current_problem.topic[0] if current_problem else None,
        difficulty_range=(1, 2)
    )
    if base_problems:
        return [self._to_recommended(base_problems[0])]
    
    return []  # 完全无法推荐
```

---

## 10. 评估指标（Evaluation Metrics）

### 10.1 推荐效果指标

| 指标 | 定义 | 目标 | 采集方式 |
|------|------|------|---------|
| **推荐接受率** | 学生点击推荐的题 / 总推荐次数 | > 60% | MongoDB feedback 数据 |
| **推荐完成率** | 学生完成推荐的题 / 接受的题 | > 70% | MongoDB feedback 数据 |
| **维度平衡度** | 学生的 dimension_ratio 标准差（跨 session） | < 0.15 | MongoDB profile 数据分析 |
| **难度匹配度** | 学生完成推荐题难度 vs. 推荐难度的偏差 | 平均偏差 < 0.5 级 | 埋点 |
| **多样性指数** | top-3 中不同 topic 数 / 3 | 平均 > 2.0 | 埋点 |

### 10.2 系统性能指标

| 指标 | 目标 | 告警阈值 |
|------|------|---------|
| P50 延迟 | < 20ms | > 50ms |
| P95 延迟 | < 100ms | > 200ms |
| 题库查询超时率 | < 0.1% | > 1% |

---

## 附录 A: 文件清单

| 文件路径 | 职责 |
|----------|------|
| `service.py` | 主管道编排（recommend 方法） |
| `models.py` | 数据模型（Pydantic + dataclass） |
| `routes.py` | FastAPI 路由 |
| `module.py` | 模块入口 |
| `profile/loader.py` | 学生画像读取 |
| `profile/models.py` | StudentProfile 等 |
| `retriever/candidate_retriever.py` | 候选题检索 + 硬过滤 |
| `retriever/models.py` | CandidateProblem 等 |
| `scorer/dimension_scorer.py` | 维度平衡打分 |
| `scorer/difficulty_scorer.py` | 难度递进打分 |
| `scorer/spaced_repetition_scorer.py` | 间隔重复打分 |
| `scorer/quality_scorer.py` | 题目质量打分 |
| `scorer/models.py` | ScoreBreakdown 等 |
| `engine/ranking_engine.py` | 综合排序 |
| `engine/strategy_selector.py` | 策略选择 |
| `triggers/intervention_trigger.py` | Module 2 事件监听 |
| `triggers/student_trigger.py` | 学生主动请求处理 |
| `output/recommender.py` | 推荐结果推送 |
| `output/notifier.py` | 推送通知 |
| `infrastructure/database/repositories/recommendation_repo.py` | 推荐历史持久化 |
| `infrastructure/database/repositories/problem_bank_repo.py` | 题库访问 |

**预估总行数**: ~2,500 行

---

## 附录 B: API 端点汇总

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/recommendations/{student_id}` | 获取学生推荐结果 |
| POST | `/recommendations/trigger` | 手动触发推荐（来自 Module 2） |
| POST | `/recommendations/feedback` | 学生反馈（接受/拒绝） |
| GET | `/recommendations/history/{student_id}` | 获取推荐历史 |
| GET | `/recommendations/strategy/{student_id}` | 获取当前推荐策略 |

---

## 附录 C: 推荐流程时序图

```
学生端              Module 3               Module 4              题库
  │                    │                      │                    │
  │  SOLVED 事件       │                      │                    │
  │───────────────────>│                      │                    │
  │                    │                      │                    │
  │                    │  get_profile()        │                    │
  │                    │─────────────────────>│                    │
  │                    │<─────────────────────│                    │
  │                    │                      │                    │
  │                    │  get_recent_problems()│                    │
  │                    │─────────────────────>│                    │
  │                    │<─────────────────────│                    │
  │                    │                      │                    │
  │                    │  查询候选题（难度过滤）│                    │
  │                    │────────────────────────────────────────>│
  │                    │<────────────────────────────────────────│
  │                    │                      │                    │
  │                    │  [并行打分]            │                    │
  │                    │    - dim_score        │                    │
  │                    │    - diff_score       │                    │
  │                    │    - recency_score    │                    │
  │                    │    - quality_score    │                    │
  │                    │                      │                    │
  │                    │  [排序 + 多样性保护]   │                    │
  │                    │                      │                    │
  │                    │  写入推荐历史          │                    │
  │                    │─────────────────────>│                    │
  │                    │                      │                    │
  │  返回 top-3        │                      │                    │
  │<───────────────────│                      │                    │
  │                    │                      │                    │
```
