# Module 4 PRD：学生画像与认知建模系统

> **版本**: v2.1  
> **更新日期**: 2026-04-02  
> **模块名称**: 学生画像与认知建模系统  
> **适用领域**: 高中数学辅导  
> **状态**: 未实现（需要从零开发）

---

## 1. 模块定位

### 1.1 一句话定位

**Module 4 = 学生数据的读写中枢。以 kp_id 为最小粒度，记录学生"做过什么题、卡在哪个知识点、需要什么提示"，供 Module 2 和 Module 3 决策使用。**

### 1.2 核心价值

```
没有 Module 4：
  Module 2 每次干预都是盲打，不知道学生是"知识不够"还是"方法不对"
  Module 3 每次推荐都是随机，不知道学生已经会了什么、还不会什么

有了 Module 4：
  Module 2 知道 dimension_ratio，知道该学生偏 R 还是偏 M
  Module 3 知道 weak_kp_ids，知道该学生哪几个知识点最薄弱
```

### 1.3 与其他模块的关系

```
┌─────────────────────────────────────────────────────────────────┐
│                        Socrates 系统                              │
│                                                                   │
│   Module 1: Cognitive Diagnosis Engine                            │
│        │  solution_steps 含 kp_ids 标注                           │
│        ▼                                                         │
│   Module 2: Progressive Scaffolding Intervention                  │
│        │  干预结束 → update_after_intervention()                   │
│        │  干预开始 → get_routing_hint()                           │
│        ▼                                                         │
│   Module 4: Student Profile ◄─────────────────────────────────┐  │
│   ┌──────────────────────────────────────────────────────┐     │  │
│   │  kp_mastery          ← kp_id 粒度的掌握度追踪        │     │  │
│   │  dimension_ratio     ← R/M 维度比例                   │     │  │
│   │  weak_kp_ids         ← 薄弱知识点                    │     │  │
│   │  weak_topics         ← 薄弱题型（扩展而来）           │     │  │
│   └──────────────────────────────────────────────────────┘     │  │
│        │                                                           │  │
│        ├──► Module 2: get_routing_hint()                        │  │
│        │      返回 dimension_ratio, recommended_dimension            │  │
│        │                                                            │  │
│        ├──► Module 3: get_topic_mastery()                        │  │
│        │      返回 weak_kp_ids, weak_topics                       │  │
│        │                                                            │  │
│        └──► Module 5: get_teaching_strategy()                     │  │
│               返回 dimension_ratio, topic_mastery                   │  │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. 核心概念

### 2.1 kp_id 粒度

每个知识点的唯一标识，格式为 `KP_{chapter}_{number}`：

```
KP_3_27   ← 第3章，第27个知识点
KP_2_04   ← 第2章，第4个知识点
```

**为什么用 kp_id 而不是章节名或题型名**：

| 粒度      | 例子             | 优点                 | 缺点                           |
| --------- | ---------------- | -------------------- | ------------------------------ |
| 章节      | "第3章 函数"     | 简单                 | 太粗，同一章有会的也有不会的   |
| 题型      | "二次函数单调性" | 中等                 | 题型边界模糊，同一题型方法不同 |
| **kp_id** | **KP_3_27**      | **精确到每个知识点** | **数据量大，需要足够多的标注** |

Module 4 选择 **kp_id 粒度**，因为这是追踪最精准的维度。

### 2.2 dimension_ratio（维度比例）

```
dimension_ratio = R型断点次数 / 总断点次数
```

含义：

| ratio 值 | 含义                | Module 2 策略               | Module 3 策略         |
| -------- | ------------------- | --------------------------- | --------------------- |
| 0.7-1.0  | R型为主（知识缺口） | 倾向 METACOGNITIVE 维度试试 | 多推荐策略类题（M型） |
| 0.3-0.0  | M型为主（方法薄弱） | 倾向 RESOURCE 维度试试      | 多推荐基础类题（R型） |
| 0.3-0.7  | 均衡                | 不特别倾向                  | 均衡推荐              |

### 2.3 KPMastery（知识点掌握度）

```
KPMastery = f(正确率, 提示依赖程度)

mastery_level = 正确率 × (1 - 提示惩罚)

  正确率 = correct_count / attempt_count
  提示惩罚 = min(avg_hint_level / 5.0, 0.5)
           = min((total_hint_count / attempt_count) / 5.0, 0.5)
```

**直观理解**：

| 学生 | attempt | correct | hints | mastery | 含义                         |
| ---- | ------- | ------- | ----- | ------- | ---------------------------- |
| 李四 | 2       | 1       | 5     | 0.25    | 对了50%，但用了很多提示 → 弱 |
| 王五 | 3       | 2       | 3     | 0.53    | 对了67%，提示用得少 → 较强   |

**提示级别量化**（用于计算 avg_hint_level）：

```
R1=1, R2=2, R3=3, R4=4
M1=1, M2=2, M3=3, M4=4, M5=5
```

### 2.4 weak_kp_ids 与 weak_topics

```
weak_kp_ids = mastery_level < 0.4 的 kp_id 列表

weak_topics = 通过 type_kp_mapping.json 扩展的薄弱题型
```

**扩展逻辑**：

```
weak_kp_ids = ["KP_3_27", "KP_3_32"]
        │
        ▼ type_kp_mapping.json
题型A "一元二次函数单调性" → 包含 KP_3_27 ✓
题型B "导数基础应用"         → 包含 KP_3_32 ✓
        │
        ▼
weak_topics = ["一元二次函数单调性", "导数基础应用"]
```

**用途**：Module 3 推荐时，不仅能说"KP_3_27 薄弱"，还能说"这个学生在一元二次函数单调性这块比较薄弱"，更有人情味。

---

## 3. 数据模型

### 3.1 MongoDB Schema：StudentProfile

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class KPMastery(BaseModel):
    """单个知识点的掌握度"""
    kp_id: str                           # "KP_3_27"
    mastery_level: float = Field(ge=0.0, le=1.0)
    last_attempt: Optional[datetime] = None
    attempt_count: int = 0               # 累计尝试次数
    correct_count: int = 0              # 累计正确次数
    total_hint_count: int = 0           # 累计提示级别之和
    avg_hint_level: float = 0.0         # total_hint_count / attempt_count


class InterventionRecord(BaseModel):
    """单次干预记录"""
    intervention_id: str
    session_id: str
    problem_id: str                      # 题目ID

    # 断点信息
    breakpoint_type: str                  # "MISSING_STEP" / "WRONG_DIRECTION"
    breakpoint_position: int             # 断点在解法中的位置

    # 干预决策
    dimension: str                        # "RESOURCE" / "METACOGNITIVE"
    level: str                           # "R2" / "M3" etc.

    # 知识点关联
    kp_ids: list[str]                   # 本次断点关联的 kp_id 列表
    methods_used: list[str]             # 本次提示使用的方法 ID

    # 结果
    outcome: str                        # "SOLVED" / "ESCALATED" / "TERMINATED"
    escalation_count: int = 0

    timestamp: datetime


class StudentProfile(BaseModel):
    """学生完整画像"""
    student_id: str

    # ── 维度画像 ──────────────────────────────
    dimension_ratio: float = Field(ge=0.0, le=1.0, default=0.5)
    # dimension_ratio = R型断点次数 / 总断点次数

    # ── 干预历史（最近100条）─────────────────
    intervention_history: list[InterventionRecord] = Field(default_factory=list)

    # ── 知识点掌握度（kp_id 粒度）【核心】───
    kp_mastery: dict[str, KPMastery] = Field(default_factory=dict)
    # key: kp_id (e.g., "KP_3_27"), value: KPMastery

    # ── 薄弱分析 ──────────────────────────────
    weak_kp_ids: list[str] = Field(default_factory=list)
    weak_topics: list[str] = Field(default_factory=list)

    # ── 统计 ──────────────────────────────────
    total_interventions: int = 0
    total_solved: int = 0
    total_escalation: int = 0

    # ── 元数据 ────────────────────────────────
    created_at: datetime
    updated_at: datetime
    last_active_at: datetime

    # ── 趋势 ──────────────────────────────────
    ratio_trend: Optional[str] = None   # "rising" / "falling" / "stable"
    trend_confidence: float = Field(ge=0.0, le=1.0, default=0.0)

    class Config:
        collection = "students"
```

### 3.2 字段速查表

| 字段                   | 类型                 | 说明                        | 示例                            |
| ---------------------- | -------------------- | --------------------------- | ------------------------------- |
| `student_id`           | string               | 学生唯一标识                | `"s_001"`                       |
| `dimension_ratio`      | float                | R型断点比例                 | `0.72`                          |
| `intervention_history` | InterventionRecord[] | 最近100条                   | 见 3.3                          |
| `kp_mastery`           | dict                 | **kp_id → 掌握度**          | `{ "KP_3_27": KPMastery(...) }` |
| `weak_kp_ids`          | string[]             | 薄弱 kp_id（mastery < 0.4） | `["KP_3_27"]`                   |
| `weak_topics`          | string[]             | 薄弱题型（扩展）            | `["一元二次函数单调性"]`        |
| `total_interventions`  | int                  | 累计干预次数                | `42`                            |
| `total_solved`         | int                  | 累计 SOLVED                 | `35`                            |
| `ratio_trend`          | string               | 维度趋势                    | `"falling"`                     |

### 3.3 InterventionRecord 子文档

| 字段              | 类型     | 说明                            |
| ----------------- | -------- | ------------------------------- |
| `intervention_id` | string   | 干预唯一ID                      |
| `session_id`      | string   | 会话ID                          |
| `problem_id`      | string   | 题目ID                          |
| `breakpoint_type` | string   | 断点类型                        |
| `dimension`       | string   | RESOURCE / METACOGNITIVE        |
| `level`           | string   | R1-R4 / M1-M5                   |
| `kp_ids`          | string[] | 本次断点关联的 kp_id            |
| `methods_used`    | string[] | 本次使用的方法                  |
| `outcome`         | string   | SOLVED / ESCALATED / TERMINATED |
| `timestamp`       | datetime | 时间戳                          |

---

## 4. 核心功能

### 4.1 ProfileManager：对外接口

```python
class ProfileManager:
    """学生画像管理器——Module 4 对外的唯一入口"""

    # ── 基础读写 ──────────────────────────────

    async def get_profile(self, student_id: str) -> Optional[StudentProfile]:
        """获取学生画像，不存在返回 None"""

    async def upsert_profile(self, student_id: str) -> StudentProfile:
        """确保 profile 存在（新学生初始化 default 值）"""

    # ── 核心写入 ─────────────────────────────

    async def update_after_intervention(
        self,
        record: InterventionWriteBack,
    ) -> StudentProfile:
        """【最核心方法】每次 Module 2 干预结束调用"""

    # ── 核心读取 ─────────────────────────────

    async def get_routing_hint(self, student_id: str) -> RoutingHint:
        """Module 2 的 DimensionRouter / SubTypeDecider 调用"""

    async def get_topic_mastery(
        self,
        student_id: str,
        kp_ids: list[str],
    ) -> dict[str, float]:
        """Module 3 推荐时查询指定 kp_id 的 mastery"""

    async def get_weak_kp_ids(
        self,
        student_id: str,
        top_n: int = 10,
    ) -> list[str]:
        """获取薄弱 kp_id 列表"""
```

### 4.2 update_after_intervention（最核心方法）

```python
async def update_after_intervention(
    self,
    record: InterventionWriteBack,
) -> StudentProfile:
    """
    每次 Module 2 干预结束调用，执行以下步骤：

    Step 1: 追加干预记录
      profile.intervention_history.append(record)
      超过 100 条则截断最旧的

    Step 2: 更新统计
      profile.total_interventions += 1
      if outcome == "SOLVED": total_solved += 1
      if outcome == "TERMINATED": total_escalation += 1

    Step 3: 重新计算 dimension_ratio
      r_count = sum(1 for r in history if r.dimension == "RESOURCE")
      profile.dimension_ratio = r_count / len(history)

    Step 4: 更新每个 kp_id 的 KPMastery
      for kp_id in record.kp_ids:
          _update_kp_mastery(profile, kp_id, record.level, record.outcome)

    Step 5: 重新计算 weak_kp_ids
      profile.weak_kp_ids = [
          kp_id for kp_id, m in profile.kp_mastery.items()
          if m.mastery_level < 0.4
      ]

    Step 6: 扩展 weak_topics
      profile.weak_topics = _expand_weak_topics(profile.weak_kp_ids)

    Step 7: 保存到 MongoDB
    """
```

**KPMastery 更新细节**：

```python
def _update_kp_mastery(
    profile: StudentProfile,
    kp_id: str,
    level: str,
    outcome: str,
) -> None:
    # 获取或创建 KPMastery
    if kp_id not in profile.kp_mastery:
        profile.kp_mastery[kp_id] = KPMastery(kp_id=kp_id)

    m = profile.kp_mastery[kp_id]

    # 更新计数
    m.attempt_count += 1
    m.last_attempt = datetime.utcnow()
    m.total_hint_count += _hint_level(level)

    if outcome == "SOLVED":
        m.correct_count += 1

    # 重新计算 mastery_level
    correct_rate = m.correct_count / m.attempt_count
    m.avg_hint_level = m.total_hint_count / m.attempt_count
    hint_penalty = min(m.avg_hint_level / 5.0, 0.5)

    m.mastery_level = correct_rate * (1 - hint_penalty)
    m.mastery_level = max(0.0, min(1.0, m.mastery_level))


def _hint_level(level: str) -> int:
    """R1=1, R2=2, ..., M5=5"""
    level_map = {
        "R1": 1, "R2": 2, "R3": 3, "R4": 4,
        "M1": 1, "M2": 2, "M3": 3, "M4": 4, "M5": 5,
    }
    return level_map.get(level, 0)
```

### 4.3 get_routing_hint（路由增强）

被 Module 2 的 Node 2a 和 Node 2b 调用，在干预决策前获取学生画像上下文。

```python
async def get_routing_hint(self, student_id: str) -> RoutingHint:
    profile = await self.get_profile(student_id)

    # 新学生（< 3 次干预）→ 默认值，置信度 0
    if not profile or profile.total_interventions < 3:
        return RoutingHint(
            student_id=student_id,
            is_new_student=True,
            dimension_ratio=0.5,
            recent_dimensions=[],
            weak_dimensions=[],
            weak_kp_ids=[],
            weak_topics=[],
            recommended_dimension="neutral",
            confidence=0.0,
        )

    # 计算 weak_dimensions（最近失败最多的维度级别）
    weak_dimensions = self._compute_weak_dimensions(
        profile.intervention_history
    )

    # 获取 weak_kp_ids
    weak_kp_ids = [
        kp_id for kp_id, m in profile.kp_mastery.items()
        if m.mastery_level < 0.4
    ][:10]  # 最多取 10 个

    # 推荐维度
    if profile.dimension_ratio > 0.65:
        recommended = "METACOGNITIVE"
    elif profile.dimension_ratio < 0.35:
        recommended = "RESOURCE"
    else:
        recommended = "neutral"

    return RoutingHint(
        student_id=student_id,
        is_new_student=False,
        dimension_ratio=profile.dimension_ratio,
        recent_dimensions=[
            r.dimension for r in profile.intervention_history[-10:]
        ],
        weak_dimensions=weak_dimensions,
        weak_kp_ids=weak_kp_ids,
        weak_topics=profile.weak_topics,
        recommended_dimension=recommended,
        confidence=min(profile.total_interventions / 20.0, 0.95),
    )
```

### 4.4 \_expand_weak_topics（薄弱题型扩展）

```python
def _expand_weak_topics(self, weak_kp_ids: list[str]) -> list[str]:
    """
    通过 type_kp_mapping.json 将 weak_kp_ids 扩展为薄弱题型。

    规则：
      遍历所有题型映射
      若某题型涉及的 kp_ids 与 weak_kp_ids 有交集
      且 交集数量 / 该题型 kp_ids总数 >= 30%
      → 该题型标记为薄弱
    """
    if not weak_kp_ids:
        return []

    weak_set = set(weak_kp_ids)
    weak_topics = []

    for mapping in type_kp_mapping["mappings"]:
        topic_kps = set(mapping["knowledge_points"])
        intersection = weak_set & topic_kps

        # 该题型有 >= 30% 的 KP 都是薄弱
        if len(intersection) / len(topic_kps) >= 0.3:
            weak_topics.append(mapping["type"])

    return weak_topics
```

### 4.5 \_compute_weak_dimensions

```python
def _compute_weak_dimensions(
    self,
    history: list[InterventionRecord],
    window: int = 10,
) -> list[str]:
    """
    分析最近 window 次干预，统计失败最多的维度级别。

    "失败"定义：outcome == "ESCALATED" 或 "TERMINATED"

    返回: ["RESOURCE_R2", "METACOGNITIVE_M3"] 形式的列表
    """
    recent = history[-window:]
    failures: Counter = Counter()

    for record in recent:
        if record.outcome in ("ESCALATED", "TERMINATED"):
            failures[f"{record.dimension}_{record.level}"] += 1

    # 返回失败最多的前 3 个
    return [dim for dim, _ in failures.most_common(3)]
```

---

## 5. RoutingHint 数据结构

```python
class RoutingHint(BaseModel):
    """路由增强提示——Module 4 输出给 Module 2"""

    student_id: str
    is_new_student: bool               # < 3 次干预

    # 维度
    dimension_ratio: float              # 0.0-1.0
    recent_dimensions: list[str]         # 最近维度 ["RESOURCE", "METACOGNITIVE", ...]

    # 薄弱
    weak_dimensions: list[str]          # ["RESOURCE_R2", "METACOGNITIVE_M3"]
    weak_kp_ids: list[str]              # 薄弱 kp_id
    weak_topics: list[str]              # 薄弱题型

    # 建议
    recommended_dimension: str          # "RESOURCE" | "METACOGNITIVE" | "neutral"

    # 置信度
    confidence: float                   # 0.0-1.0，与干预次数正相关
```

**recommended_dimension 决策规则**：

```
dimension_ratio > 0.65:
  → METACOGNITIVE（学生偏 R 说明知识缺口多，试试换维度激活策略）

dimension_ratio < 0.35:
  → RESOURCE（学生偏 M 说明策略够了，试试补知识）

0.35 <= dimension_ratio <= 0.65:
  → neutral（两边差不多，不特别倾向）
```

**confidence 计算**：

```
confidence = min(total_interventions / 20.0, 0.95)

含义：
  干预 3 次以下 → confidence ≈ 0（数据太少，不可信）
  干预 10 次   → confidence = 0.5
  干预 20 次+ → confidence = 0.95（上界）
```

---

## 6. 数据流图

### 6.1 写入（Module 2 → Module 4）

```
学生解题
    │
    ▼
Module 2: 干预结束
    │
    ▼
InterventionWriteBack
  {
    student_id: "s_001",
    problem_id: "prob_001",
    breakpoint: {
      kp_ids: ["KP_3_27", "KP_3_32"],
      method_id: "M_换元法",
      type: "MISSING_STEP",
    },
    dimension: "RESOURCE",
    level: "R2",
    outcome: "ESCALATED",
  }
    │
    ▼
ProfileManager.update_after_intervention()
    │
    ├── 追加到 intervention_history
    │
    ├── total_interventions++
    │
    ├── dimension_ratio = R_count / total
    │
    ├── KPMastery["KP_3_27"] ← 更新
    │     attempt_count: 2
    │     correct_count: 0
    │     total_hint_count: 4
    │     mastery_level: 0.0 * (1 - 0.4) = 0.0
    │
    ├── KPMastery["KP_3_32"] ← 更新
    │     ...
    │
    ├── weak_kp_ids ← 重新计算
    │
    ├── weak_topics ← 扩展
    │
    └── MongoDB.save()
```

### 6.2 读取（Module 4 → Module 2）

```
Module 2: 干预开始，请求 routing_hint
    │
    ▼
ProfileManager.get_routing_hint(student_id="s_001")
    │
    ├── MongoDB.load()
    │
    ├── total_interventions = 15 → confidence = 0.75
    │
    ├── dimension_ratio = 0.72 → recommended = "METACOGNITIVE"
    │
    ├── weak_kp_ids = ["KP_3_27", "KP_3_32"]
    │
    ├── weak_dimensions = ["RESOURCE_R2", "RESOURCE_R3"]
    │
    └── 返回 RoutingHint
           {
             dimension_ratio: 0.72,
             recommended_dimension: "METACOGNITIVE",
             weak_kp_ids: ["KP_3_27", "KP_3_32"],
             confidence: 0.75,
             ...
           }
    │
    ▼
Module 2 DimensionRouter:
  "你的 dimension_ratio = 0.72，说明你经常在知识层面卡住，
   我这次试试从策略角度给你提示。"
```

---

## 7. 典型场景

### 场景一：学生首次使用（冷启动）

```
新学生张三，第1次干预

Module 2 → update_after_intervention(...)
  → kp_mastery = {}（空的）
  → dimension_ratio = 0.5（默认）
  → weak_kp_ids = []

Module 2 → get_routing_hint()
  → is_new_student = True
  → confidence = 0.0
  → recommended_dimension = "neutral"
  → 画像没有参考价值，Module 2 自己做决定
```

### 场景二：知识薄弱检测

```
学生李四，dimension_ratio = 0.82

Module 4 → get_routing_hint()
  → recommended_dimension = "METACOGNITIVE"
  → weak_kp_ids = ["KP_2_04", "KP_2_05"]  ← 韦达定理、配方法薄弱

Module 2 → DimensionRouter
  → 收到 METACOGNITIVE 建议
  → WRONG_DIRECTION + recommended = METACOGNITIVE
  → 输出 METACOGNITIVE（而不是默认 RESOURCE）

Module 2 → HintGeneratorV2
  → M3 提示：
    "李四，你对韦达定理已经很熟了，
     但这道题换个角度想会更简单——"

Module 3 → get_topic_mastery()
  → 发现 KP_2_04 和 KP_2_05 薄弱
  → 推荐相关练习题，多为 R 型基础题
```

### 场景三：学生成长追踪

```
第1周：王五 dimension_ratio = 0.78，weak_kp_ids = ["KP_2_04", "KP_2_05"]
  → Module 3 推荐偏重 R 型基础练习

第3周：王五 dimension_ratio = 0.55，weak_kp_ids = ["KP_3_27"]
  → 知识缺口减少，开始出现 M 型挑战
  → Module 3 均衡推荐

第5周：王五 dimension_ratio = 0.38，weak_kp_ids = []
  → 知识够了，方法也灵活了
  → Module 3 推荐多为综合题、策略类
  → Module 4 ratio_trend = "falling"，confidence = 0.85
```

### 场景四：学生达到 TERMINATE

```
学生赵六，同一断点达到 M5 最高级别，仍未解决

Module 2 → update_after_intervention(outcome="TERMINATED")
  → total_escalation++
  → dimension_ratio 更新

Module 4 → 记录本次 TERMINATED 到 intervention_history
  → 标记 weak_dimensions 包含 "METACOGNITIVE_M5"

Module 2 → 触发 Module 3/5 介入
  → 建议观看知识点讲解视频
  → 或请求人工辅导
```

---

## 8. 与 Module 3 的接口

### 8.1 Module 3 读取接口

```python
class RecommendationService:
    def __init__(self, profile_manager: ProfileManager):
        self.profile_manager = profile_manager

    async def recommend_next(
        self,
        student_id: str,
        current_problem_id: str,
    ) -> ProblemRecommendation:

        profile = await self.profile_manager.get_profile(student_id)

        if not profile:
            # 新学生：默认均衡策略
            return ProblemRecommendation(
                problem_types={"RESOURCE": 0.5, "METACOGNITIVE": 0.5},
                weak_kp_ids=[],
                reasoning="新学生，默认均衡推荐",
            )

        # 1. 过滤近期做过的题
        recent_problems = [
            r.problem_id for r in profile.intervention_history[-10:]
        ]

        # 2. 获取薄弱 kp_id
        weak_kp_ids = await self.profile_manager.get_weak_kp_ids(
            student_id, top_n=5
        )

        # 3. 决定 R/M 型题比例
        ratio = profile.dimension_ratio
        if ratio > 0.65:
            problem_types = {"RESOURCE": 0.3, "METACOGNITIVE": 0.7}
            reasoning = f"dimension_ratio={ratio:.2f}，偏R→多推M型题"
        elif ratio < 0.35:
            problem_types = {"RESOURCE": 0.7, "METACOGNITIVE": 0.3}
            reasoning = f"dimension_ratio={ratio:.2f}，偏M→多推R型题"
        else:
            problem_types = {"RESOURCE": 0.5, "METACOGNITIVE": 0.5}
            reasoning = f"dimension_ratio={ratio:.2f}，均衡推荐"

        # 4. 查询题库，筛选
        candidates = self.problem_bank.filter(
            exclude_problem_ids=recent_problems,
            target_kp_ids=weak_kp_ids,
            target_types=problem_types,
        )

        return ProblemRecommendation(
            problem_ids=[p.id for p in candidates],
            weak_kp_ids=weak_kp_ids,
            problem_types=problem_types,
            reasoning=reasoning,
        )
```

### 8.2 ProblemRecommendation 结构

```python
class ProblemRecommendation(BaseModel):
    problem_ids: list[str]              # 推荐题目 ID 列表
    weak_kp_ids: list[str]              # 推荐的薄弱 kp_id（用于展示）
    problem_types: dict[str, float]    # {"RESOURCE": 0.3, "METACOGNITIVE": 0.7}
    reasoning: str                       # 推荐理由（展示给老师/系统）
```

---

## 9. 目录结构

```
app/
├── modules/
│   └── student_model/                      # 【新建 Module 4】
│       ├── __init__.py
│       ├── models.py                       # Pydantic models
│       │                                      StudentProfile, KPMastery,
│       │                                      InterventionRecord
│       ├── schemas.py                      # API schemas
│       │                                      RoutingHint, ProblemRecommendation
│       │
│       ├── repository/
│       │   └── student_profile_repo.py    # MongoDB CRUD 操作
│       │
│       ├── services/
│       │   ├── profile_manager.py         # 【核心】ProfileManager
│       │   ├── mastery_analyzer.py       # KPMastery 更新 / weak 计算
│       │   └── topic_expander.py         # weak_topics 扩展
│       │
│       └── routes.py                      # API 端点（可选用）
│
├── infrastructure/
│   └── database/
│       └── mongodb.py                    # MongoDB 连接配置
```

---

## 10. MongoDB 索引

```python
# migration: 004_create_student_profiles

def upgrade(mongo_client):
    collection = mongo_client.socrates.students

    # 主键
    collection.create_index("student_id", unique=True)

    # 维度比例筛选（用于群体分析）
    collection.create_index([("dimension_ratio", ASCENDING)])

    # 活跃学生查询
    collection.create_index([("updated_at", DESCENDING)])

    # 薄弱 kp_id 倒排（查找有某薄弱 kp 的所有学生）
    collection.create_index([("weak_kp_ids", ASCENDING)])

    # kp_mastery 倒排（查找掌握某 kp 的所有学生）
    # 注：MongoDB 不支持 dict key 的索引，需要用 aggregation 或 separate collection
```

---

## 11. 评估指标

| 指标                       | 定义                                           | 目标        | 采集         |
| -------------------------- | ---------------------------------------------- | ----------- | ------------ |
| **kp_mastery 覆盖率**      | 有 kp_mastery 记录的学生 / 有干预的学生        | > 80%       | MongoDB      |
| **weak_kp_ids 准确率**     | 学生自评薄弱与 system 判断一致的 kp 比例       | > 60%       | 学生反馈     |
| **routing_hint 采纳率**    | Module 2 采纳 recommended_dimension 建议的比例 | > 70%       | Node 2a 埋点 |
| **topic_mastery 收敛率**   | 薄弱 kp 经过 N 题后转不薄弱（>0.4）的比例      | > 50% @ 5题 | 追踪分析     |
| **dimension_ratio 稳定性** | 干预 10 次后 dimension_ratio 的标准差          | < 0.15      | MongoDB      |
| **get_routing_hint 延迟**  | P95                                            | < 30ms      | APM          |
| **update 延迟**            | P95                                            | < 50ms      | APM          |

---

## 12. 边界情况

| 场景                                    | 处理                                                       |
| --------------------------------------- | ---------------------------------------------------------- |
| 新学生（< 3 次干预）                    | `is_new_student=True`，dimension_ratio=0.5，confidence=0.0 |
| kp_id 不在 knowledge_points_all.json 中 | 跳过，不更新该 kp_id 的 mastery                            |
| intervention_history 为空               | 视为新学生                                                 |
| type_kp_mapping 中无匹配                | weak_topics = []                                           |
| dimension_ratio 计算 NaN                | 默认为 0.5                                                 |
| mastery_level 计算 NaN                  | 复位为 0.0                                                 |
| MongoDB 写入失败                        | 降级到内存缓存（LRU，max 100 profiles），恢复后异步 flush  |

---

## 13. 冷启动策略

新学生（total_interventions < 3）使用以下默认值：

| 字段                    | 默认值    | 原因     |
| ----------------------- | --------- | -------- |
| `dimension_ratio`       | 0.5       | 均衡假设 |
| `is_new_student`        | True      | 数据太少 |
| `confidence`            | 0.0       | 不可信   |
| `recommended_dimension` | "neutral" | 不误导   |
| `weak_kp_ids`           | []        | 无数据   |
| `ratio_trend`           | None      | 样本不足 |

---

## 14. 与旧版差异（v1 → v2）

| 变更项            | v1                                                  | v2                                                                |
| ----------------- | --------------------------------------------------- | ----------------------------------------------------------------- |
| **掌握度粒度**    | `topic_mastery`（dict，章节级，如 `{"函数": 0.6}`） | **`kp_mastery`**（dict，kp_id 粒度，如 `{"KP_3_27": KPMastery}`） |
| **更新方式**      | 干预结束写入 dimension_ratio                        | **每个 kp_id 同步更新 mastery**                                   |
| **薄弱分析**      | 只有一个 dimension_ratio 数                         | **weak_kp_ids 列表 + weak_topics 扩展**                           |
| **routing_hint**  | 基础维度建议                                        | **含 weak_kp_ids、weak_topics、confidence**                       |
| **Module 3 接口** | 无                                                  | **get_topic_mastery + weak_kp_ids 过滤**                          |
| **掌握度算法**    | 无                                                  | **correct_rate × (1 - hint_penalty)**                             |

---

## 15. 尚未实现清单

以下功能需要从零开发：

```
□ student_model/models.py        — Pydantic models
□ student_model/schemas.py      — API schemas
□ student_model/repository/     — MongoDB CRUD
□ student_model/services/profile_manager.py
□ student_model/services/mastery_analyzer.py
□ student_model/services/topic_expander.py
□ student_model/routes.py
□ MongoDB migration: 004_create_student_profiles
□ 集成测试
```

---

_本文档为 Module 4 v2.1 产品需求定义，供工程团队实现参考。_
