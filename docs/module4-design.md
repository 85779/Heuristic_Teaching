# Module 4: 学生画像与认知建模系统设计文档

**版本**: v1
**核心功能**: 学生维度画像（dimension_ratio）计算、趋势分析、路由增强数据提供
**最后更新**: 2026-03-30

---

## 1. 架构概述与数据流

### 1.1 模块定位

Module 4 是整个 Socrates 系统的数据基石，负责维护每位学生的认知特征画像。其他模块（Module 2、Module 3、Module 5）依赖 Module 4 提供的学生特征数据来实现个性化服务。

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Socrates 系统架构                                  │
│                                                                              │
│    Module 1 (组织化解题)                                                       │
│           │                                                                  │
│           ▼                                                                  │
│    Module 2 (断点干预系统) ────────────────────────────────────────────────┐  │
│           │                                                                  │  │
│           │  每次干预结束写回                                                 │  │
│           │  intervention_history                                           │  │
│           ▼                                                                  ▼  │
│    Module 4 (学生画像)              Module 3 (智能推荐)         Module 5 (教学策略)  │
│    ┌─────────────────────┐                  │                    │            │
│    │ dimension_ratio    │ ◄────────────── │ 读取profile      │ 读取profile│
│    │ intervention_history│                  │                   │            │
│    │ topic_mastery       │ ──────────────► │                   │            │
│    └─────────────────────┘   被依赖为基石   └───────────────────┘            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 核心概念：dimension_ratio

**dimension_ratio** 是 Module 4 最核心的指标，定义如下：

```
dimension_ratio = R型断点次数 / 总断点次数
```

- **dimension_ratio = 0.7**：学生在所有断点中，70% 是 RESOURCE 型断点，说明该学生偏重知识缺口，需要补充基础
- **dimension_ratio = 0.3**：学生在所有断点中，70% 是 METACOGNITIVE 型断点，说明该学生偏重元认知薄弱，需要训练策略运用
- **dimension_ratio = 0.5**：R型与M型断点各占一半，学生维度均衡

### 1.3 数据流总图

```
Module 2 干预结束
     │
     ▼
create_intervention() 返回 InterventionResult
     │
     ▼
ProfileManager.update_after_intervention()
     │
     ├─► 追加到 intervention_history
     │
     ├─► 重新计算 dimension_ratio
     │
     ├─► 更新 total_interventions / total_solved / total_escalation
     │
     ├─► 更新 topic_mastery
     │
     └─► 保存到 MongoDB
              │
              ▼
routing_hint / profile_analytics 读取最新profile
              │
              ▼
输出到 Module 2（DimensionRouter / SubTypeDecider）
输出到 Module 3（推荐系统）
输出到 Module 5（教学策略）
```

### 1.4 与其他模块的关系

| 关系 | 说明 |
|------|------|
| **Module 2 → Module 4** | Module 2 每次干预结束（SOLVED / MAX_ESCALATION）后，调用 ProfileManager 将本次断点的维度类型写入学生的 intervention_history，并更新 dimension_ratio |
| **Module 4 → Module 2** | DimensionRouter 和 SubTypeDecider 在决策前，调用 routing_hint 获取学生的维度偏向、比例趋势、置信度等信息，注入到 prompt 中辅助决策 |
| **Module 4 → Module 3** | Module 3 推荐题目时，读取学生的 dimension_ratio、recent_problems、weak_dimensions，用于制定推荐策略 |
| **Module 4 → Module 5** | Module 5 选择教学策略时，读取学生的 dimension_ratio 和 topic_mastery，用于决定讲授/练习/讨论的配比 |

---

## 2. 核心数据模型

### 2.1 StudentProfile MongoDB Schema

```javascript
{
  "_id": ObjectId,
  "student_id": "string",                      // 学生唯一标识，主键
  "dimension_ratio": 0.65,                     // R型断点比例，0.0-1.0，默认0.5

  // 干预历史（最近50条，全量保存在别处，此处仅保留近期摘要）
  "intervention_history": [
    {
      "intervention_id": "int_20260330_001",   // 干预记录唯一ID
      "problem_id": "alg_seq_001",            // 对应的题目ID
      "dimension": "RESOURCE",                 // "RESOURCE" 或 "METACOGNITIVE"
      "level": "R2",                           // 断点级别，如 "R2", "M3"
      "outcome": "SOLVED",                    // "SOLVED", "MAX_ESCALATION", "ABANDONED"
      "intervention_count": 3,                // 本题干预次数
      "timestamp": ISODate("2026-03-30T10:00:00Z")
    },
    // ... 更多记录
  ],

  // 知识点掌握度（动态更新）
  "topic_mastery": {
    "数列": {
      "topic": "数列",
      "mastery_level": 0.75,                   // 掌握度 0.0-1.0
      "last_practiced": ISODate("2026-03-30T09:30:00Z"),
      "practice_count": 12
    },
    "函数": {
      "topic": "函数",
      "mastery_level": 0.45,
      "last_practiced": ISODate("2026-03-29T15:00:00Z"),
      "practice_count": 8
    }
  },

  // 元数据
  "created_at": ISODate("2026-03-30T10:00:00Z"),    // 首次创建时间
  "updated_at": ISODate("2026-03-30T15:30:00Z"),    // 最后更新时间
  "total_interventions": 42,                         // 累计干预次数
  "total_solved": 35,                               // 累计SOLVED次数
  "total_escalation": 7,                            // 累计MAX_ESCALATION次数

  // 趋势数据（由profile_analytics计算）
  "ratio_trend": "stable",                         // "rising", "falling", "stable"
  "trend_confidence": 0.75                         // 趋势置信度 0.0-1.0
}
```

### 2.2 字段说明表

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `student_id` | string | 学生唯一标识符 | `"student_001"` |
| `dimension_ratio` | float | R型断点比例，0.0-1.0 | `0.65` |
| `intervention_history` | InterventionRecord[] | 最近50次干预记录 | 详见 2.3 |
| `topic_mastery` | dict | 知识点掌握度映射 | `{"数列": TopicMastery(...)}` |
| `created_at` | datetime | 画像创建时间 | `2026-03-30T10:00:00Z` |
| `updated_at` | datetime | 最后更新时间 | `2026-03-30T15:30:00Z` |
| `total_interventions` | int | 累计干预次数 | `42` |
| `total_solved` | int | 累计解决次数 | `35` |
| `total_escalation` | int | 累计达到最大干预次数 | `7` |
| `ratio_trend` | string | 维度比例趋势 | `"stable"` |
| `trend_confidence` | float | 趋势置信度 | `0.75` |

### 2.3 InterventionRecord 子文档结构

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `intervention_id` | string | 干预ID | `"int_20260330_001"` |
| `problem_id` | string | 题目ID | `"alg_seq_001"` |
| `dimension` | string | 断点维度 | `"RESOURCE"` |
| `level` | string | 断点级别 | `"R2"` |
| `outcome` | string | 干预结果 | `"SOLVED"` |
| `intervention_count` | int | 本题干预次数 | `3` |
| `timestamp` | datetime | 干预时间 | `2026-03-30T10:00:00Z` |

### 2.4 MongoDB 索引设计

为保证查询性能，需在 students collection 上建立以下索引：

| 索引字段 | 索引类型 | 用途 |
|---------|---------|------|
| `student_id` | unique | 主键查询 |
| `dimension_ratio` | ascending | 按维度比例筛选学生 |
| `updated_at` | descending | 按更新时间排序，查最近活跃学生 |
| `intervention_history.timestamp` | descending | 按时间范围查询干预历史 |

---

## 3. 核心算法设计

### 3.1 compute_dimension_ratio

**功能**：根据干预历史计算 dimension_ratio

**算法**：

```
输入：intervention_history (list of InterventionRecord)
输出：dimension_ratio (float, 0.0-1.0)

算法步骤：
1. 如果 intervention_history 为空：
   返回 0.5（默认均衡值）

2. 如果干预次数 < 3（冷启动期）：
   返回 0.5（不计算，使用默认）

3. 计算 R 型断点次数：
   R_count = count(record for record in intervention_history if record.dimension == "RESOURCE")

4. 计算总断点次数：
   total = len(intervention_history)

5. 计算比例：
   dimension_ratio = R_count / total

6. 返回 dimension_ratio
```

**伪代码**：

```python
def compute_dimension_ratio(intervention_history: list[InterventionRecord]) -> float:
    """
    计算 R/(R+M) 比例
    
    冷启动策略：干预次数 < 3 时返回默认 0.5
    """
    if not intervention_history:
        return 0.5
    
    if len(intervention_history) < 3:
        # 冷启动期，不计算真实比例
        return 0.5
    
    r_count = sum(1 for r in intervention_history if r.dimension == "RESOURCE")
    total = len(intervention_history)
    
    ratio = r_count / total if total > 0 else 0.5
    
    return ratio
```

### 3.2 compute_ratio_trend

**功能**：计算 dimension_ratio 的时间序列趋势

**算法**：

```
输入：
  - intervention_history: 最近 window 条干预记录
  - window: 窗口大小，默认 10

输出：
{
    "current_ratio": float,     # 当前 dimension_ratio
    "window_ratio": float,      # 窗口内 dimension_ratio
    "slope": float,             # 线性拟合斜率（正=上升=偏R方向）
    "trend": str,               # "rising" / "falling" / "stable"
    "confidence": float          # 置信度 0.0-1.0
}

算法步骤：
1. 获取最近 window 条记录（按 timestamp 降序）
2. 将 dimension 标记转换为数值（R=1, M=0）
3. 使用简单线性回归计算斜率
4. 根据斜率判断趋势：
   - slope > 0.1：rising（dimension_ratio 上升，学生偏 R 方向）
   - slope < -0.1：falling（dimension_ratio 下降，学生偏 M 方向）
   - otherwise：stable
5. 计算置信度（基于样本量和方差）
6. 返回趋势分析结果
```

**伪代码**：

```python
async def compute_ratio_trend(
    self,
    student_id: str,
    window: int = 10
) -> dict:
    """
    计算最近 window 次干预的 dimension_ratio 趋势
    
    采用简单线性回归计算斜率
    """
    profile = await self.get_profile(student_id)
    
    if not profile or len(profile.intervention_history) < 3:
        return {
            "current_ratio": 0.5,
            "window_ratio": 0.5,
            "slope": 0.0,
            "trend": "stable",
            "confidence": 0.0
        }
    
    # 取最近 window 条记录
    history = profile.intervention_history[-window:] if len(profile.intervention_history) >= window else profile.intervention_history
    
    # 将 dimension 转换为数值（R=1, M=0）
    values = [1 if r.dimension == "RESOURCE" else 0 for r in history]
    
    # 简单线性回归计算斜率
    n = len(values)
    if n < 2:
        slope = 0.0
    else:
        # x: 时间索引 [0, 1, 2, ...]
        # y: dimension 值 [0, 1, 0, ...]
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        
        numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0.0
    
    # 当前 ratio
    current_ratio = profile.dimension_ratio
    
    # 窗口内 ratio
    window_ratio = sum(values) / n if n > 0 else 0.5
    
    # 判断趋势
    if slope > 0.1:
        trend = "rising"
    elif slope < -0.1:
        trend = "falling"
    else:
        trend = "stable"
    
    # 置信度：基于样本量
    confidence = min(n / 10.0, 1.0)  # 样本量达到 10 时置信度为 1.0
    
    return {
        "current_ratio": current_ratio,
        "window_ratio": window_ratio,
        "slope": slope,
        "trend": trend,
        "confidence": confidence
    }
```

**趋势判定规则**：

| slope 范围 | trend 标签 | 说明 |
|-----------|-----------|------|
| slope > 0.1 | `rising` | dimension_ratio 上升，学生偏 R 方向（R 型断点越来越多） |
| slope < -0.1 | `falling` | dimension_ratio 下降，学生偏 M 方向（R 型断点越来越少） |
| -0.1 ≤ slope ≤ 0.1 | `stable` | 维度比例相对稳定 |

### 3.3 generate_routing_hint

**功能**：生成路由增强提示，供 Module 2 路由决策使用

**算法**：

```
输入：student_id (str)
输出：RoutingHint 结构

RoutingHint = {
    "student_id": str,
    "is_new_student": bool,                    # 是否新学生（<3次干预）
    "recent_dimension_bias": str,              # "R_dominant" / "M_dominant" / "balanced"
    "dimension_ratio": float,                  # 当前 dimension_ratio
    "ratio_trend": str,                        # "rising" / "falling" / "stable"
    "trend_confidence": float,                 # 0.0-1.0
    "weak_dimensions": list[str],              # 薄弱维度列表
    "recommended_dimension_hint": str,         # 建议优先使用的维度
    "recent_intervention_summary": str,         # 最近3次干预的文字摘要
    "confidence": float                        # 整体置信度
}

算法步骤：
1. 获取学生 profile
2. 判断 is_new_student（干预次数 < 3）
3. 根据 dimension_ratio 计算 recent_dimension_bias
4. 调用 compute_ratio_trend 获取趋势
5. 分析 weak_dimensions（统计高频断点级别）
6. 生成 recommended_dimension_hint
7. 生成 recent_intervention_summary
8. 计算整体 confidence
9. 返回 RoutingHint
```

**伪代码**：

```python
async def generate_routing_hint(self, student_id: str) -> RoutingHint:
    """
    生成路由增强提示
    被 Module 2 的 DimensionRouter 和 SubTypeDecider 调用
    """
    profile = await self.get_profile(student_id)
    
    # 判断是否新学生
    is_new_student = not profile or profile.total_interventions < 3
    
    if is_new_student:
        return RoutingHint(
            student_id=student_id,
            is_new_student=True,
            recent_dimension_bias="balanced",
            dimension_ratio=0.5,
            ratio_trend="stable",
            trend_confidence=0.0,
            weak_dimensions=[],
            recommended_dimension_hint="新学生，无明显偏好，默认使用RESOURCE维度开始",
            recent_intervention_summary="新学生，尚无干预历史",
            confidence=0.0
        )
    
    # 计算 recent_dimension_bias
    ratio = profile.dimension_ratio
    if ratio > 0.65:
        bias = "R_dominant"
    elif ratio < 0.35:
        bias = "M_dominant"
    else:
        bias = "balanced"
    
    # 获取趋势
    trend_data = await self.compute_ratio_trend(student_id)
    
    # 分析薄弱维度
    weak_dims = self._analyze_weak_dimensions(profile.intervention_history)
    
    # 生成建议
    hint = self._generate_dimension_hint(bias, is_new_student)
    
    # 生成摘要
    summary = self._generate_intervention_summary(profile.intervention_history)
    
    # 计算置信度
    confidence = self._calculate_confidence(profile, trend_data)
    
    return RoutingHint(
        student_id=student_id,
        is_new_student=False,
        recent_dimension_bias=bias,
        dimension_ratio=ratio,
        ratio_trend=trend_data["trend"],
        trend_confidence=trend_data["confidence"],
        weak_dimensions=weak_dims,
        recommended_dimension_hint=hint,
        recent_intervention_summary=summary,
        confidence=confidence
    )
```

**recent_dimension_bias 判定规则**：

| dimension_ratio 范围 | bias 标签 | 说明 |
|---------------------|---------|------|
| > 0.65 | `R_dominant` | 学生偏 R 型，知识缺口明显 |
| < 0.35 | `M_dominant` | 学生偏 M 型，元认知薄弱 |
| 0.35-0.65 | `balanced` | 维度相对均衡 |

**recommended_dimension_hint 生成逻辑**：

```
如果 is_new_student == True：
    hint = "新学生，无明显偏好，默认使用RESOURCE维度开始"
否则如果 recent_dimension_bias == "R_dominant"：
    hint = "学生R型断点多，建议使用METACOGNITIVE维度尝试引导策略思考"
否则如果 recent_dimension_bias == "M_dominant"：
    hint = "学生M型断点多，建议使用RESOURCE维度补充知识基础"
否则：
    hint = "学生维度均衡，可根据题目特征灵活选择"
```

### 3.4 薄弱维度分析

```python
def _analyze_weak_dimensions(self, intervention_history: list) -> list[str]:
    """
    分析干预历史，识别薄弱维度
    统计各维度级别的出现频率，返回高频项
    """
    if not intervention_history:
        return []
    
    # 统计各维度级别出现次数
    level_counts = {}
    for record in intervention_history[-20:]:  # 最近20条
        key = f"{record.dimension}_{record.level}"
        level_counts[key] = level_counts.get(key, 0) + 1
    
    # 按频率排序，取前2个
    sorted_levels = sorted(level_counts.items(), key=lambda x: x[1], reverse=True)
    
    # 只返回频率 > 1 的项
    weak = [level for level, count in sorted_levels if count > 1][:2]
    
    return weak
```

---

## 4. 模块结构

### 4.1 目录结构

```
backend/app/modules/student_model/
│
├── __init__.py                      # 模块导出
├── module.py                        # 模块入口（initialize/shutdown/router 注册）
├── routes.py                        # FastAPI 路由
│
├── models/                          # 数据模型
│   ├── __init__.py
│   ├── student_profile.py           # StudentProfile Schema
│   ├── intervention_record.py        # InterventionRecord Schema
│   ├── topic_mastery.py             # TopicMastery Schema
│   └── routing_hint.py              # RoutingHint Schema
│
├── repositories/                    # 数据访问层
│   ├── __init__.py
│   └── student_profile_repo.py      # MongoDB CRUD 操作
│
├── services/                        # 业务逻辑层
│   ├── __init__.py
│   ├── profile_manager.py           # 核心服务类（CRUD + update_after_intervention）
│   ├── profile_analytics.py         # 趋势分析（compute_ratio_trend）
│   └── routing_hint.py              # 路由增强（generate_routing_hint）
│
└── infrastructure/
    └── database/
        └── mongodb.py               # MongoDB 连接配置

backend/tests/modules/
└── test_student_model/
    ├── __init__.py
    ├── test_profile_manager.py      # CRUD 测试
    ├── test_profile_analytics.py    # 趋势分析测试
    └── test_routing_hint.py         # 路由提示测试

migrations/
└── 004_create_student_profiles.py    # MongoDB 迁移脚本
```

### 4.2 文件职责说明

| 文件路径 | 职责 |
|---------|------|
| `models/student_profile.py` | StudentProfile Pydantic 模型定义 |
| `models/intervention_record.py` | InterventionRecord 子文档模型 |
| `models/topic_mastery.py` | TopicMastery 子文档模型 |
| `models/routing_hint.py` | RoutingHint 输出模型 |
| `repositories/student_profile_repo.py` | MongoDB 持久化操作（upsert/find/update） |
| `services/profile_manager.py` | 画像管理器，对外提供统一接口 |
| `services/profile_analytics.py` | 趋势分析服务（compute_ratio_trend） |
| `services/routing_hint.py` | 路由增强服务（generate_routing_hint） |
| `module.py` | 模块初始化、服务注册 |
| `routes.py` | FastAPI 路由定义 |

---

## 5. MongoDB 数据模型

### 5.1 Collections 设计

| Collection 名称 | 用途 | 主键 |
|---------------|------|------|
| `students` | 学生完整画像 | `student_id` |
| `intervention_events` | 完整干预事件历史（归档） | `_id` |

### 5.2 students Collection Schema

```javascript
{
  "_id": ObjectId,
  "student_id": "string",                      // 唯一索引
  "dimension_ratio": float,                    // 默认 0.5
  "intervention_history": [...],                // 最近50条子文档
  "topic_mastery": {...},                       // 知识点掌握度映射
  "created_at": ISODate,
  "updated_at": ISODate,
  "total_interventions": int,
  "total_solved": int,
  "total_escalation": int,
  "ratio_trend": "rising" | "falling" | "stable",
  "trend_confidence": float
}
```

**索引**：

```javascript
// 主键查询
db.students.createIndex({ "student_id": 1 }, { unique: true })

// 按维度比例筛选
db.students.createIndex({ "dimension_ratio": 1 })

// 按更新时间排序
db.students.createIndex({ "updated_at": -1 })

// 干预历史时间索引
db.students.createIndex({ "intervention_history.timestamp": -1 })
```

### 5.3 intervention_events Collection（可选归档）

如果 intervention_history 超过 50 条限制，超出部分归档到此集合：

```javascript
{
  "_id": ObjectId,
  "student_id": "string",
  "intervention_id": "string",
  "problem_id": "string",
  "dimension": "RESOURCE" | "METACOGNITIVE",
  "level": "R1-R4" | "M1-M5",
  "outcome": "SOLVED" | "MAX_ESCALATION" | "ABANDONED",
  "intervention_count": int,
  "timestamp": ISODate,
  "archived_at": ISODate                       // 归档时间
}
```

**索引**：

```javascript
db.intervention_events.createIndex({ "student_id": 1, "timestamp": -1 })
db.intervention_events.createIndex({ "intervention_id": 1 }, { unique: true })
```

### 5.4 典型查询模式

```python
# 获取学生完整画像
await db.students.find_one({ "student_id": student_id })

# 获取最近活跃学生（分页）
cursor = db.students.find().sort("updated_at", -1).limit(20)

# 按 dimension_ratio 筛选学生
cursor = db.students.find({ "dimension_ratio": { "$gt": 0.65 } })

# 获取学生的最近干预历史
profile = await db.students.find_one({ "student_id": student_id })
recent_history = profile.get("intervention_history", [])[-10:]

# 统计各维度学生分布
pipeline = [
    { "$bucket": {
        "groupBy": "$dimension_ratio",
        "boundaries": [0, 0.35, 0.65, 1.0],
        "default": "other",
        "output": { "count": { "$sum": 1 } }
    }}
]
```

---

## 6. 外部接口

### 6.1 Module 2 写入接口（Module 2 → Module 4）

Module 2 在每次干预结束时调用 `update_after_intervention` 写回画像数据。

```python
# Module 2 的 InterventionService
class InterventionService:
    def __init__(self, profile_manager: ProfileManager):
        self.profile_manager = profile_manager
    
    async def create_intervention(
        self,
        student_id: str,
        problem_id: str,
        dimension: str,              # "RESOURCE" 或 "METACOGNITIVE"
        level: str,                  # "R1-R4" 或 "M1-M5"
        outcome: str,                # "SOLVED", "MAX_ESCALATION", "ABANDONED"
        intervention_count: int,
        topic: Optional[str] = None
    ) -> InterventionResult:
        # ... 干预逻辑 ...
        
        # 干预结束后，更新学生画像
        result = InterventionResult(...)
        await self.profile_manager.update_after_intervention(student_id, result)
        
        return result
```

**调用时机**：
- 学生完成一道题（SOLVED）
- 学生达到最大干预强度（MAX_ESCALATION）
- 学生主动放弃（ABANDONED）

### 6.2 Module 2 读取接口（Module 4 → Module 2）

Module 2 的 DimensionRouter 和 SubTypeDecider 在决策前读取 routing_hint。

```python
# Module 2 的 DimensionRouter
class DimensionRouter:
    def __init__(self, profile_manager: ProfileManager):
        self.profile_manager = profile_manager
    
    async def decide_dimension(self, student_id: str, problem_id: str) -> str:
        # 获取路由增强提示
        hint = await self.profile_manager.get_routing_hint(student_id)
        
        # 将 hint 注入 prompt 上下文
        prompt_context = {
            "student_id": student_id,
            "dimension_bias": hint.recent_dimension_bias,
            "recommended_dimension": hint.recommended_dimension_hint,
            "confidence": hint.confidence
        }
        
        # 调用 LLM 决策
        return await self.llm_decide_dimension(prompt_context)
```

### 6.3 Module 3 读取接口（Module 4 → Module 3）

Module 3 在推荐题目时读取学生 profile 数据。

```python
# Module 3 的 RecommendationService
class RecommendationService:
    def __init__(self, profile_manager: ProfileManager):
        self.profile_manager = profile_manager
    
    async def recommend_next(self, student_id: str, current_problem_id: str):
        # 读取学生画像
        profile = await self.profile_manager.get_profile(student_id)
        
        if profile:
            dimension_ratio = profile.dimension_ratio
            recent_problems = [r.problem_id for r in profile.intervention_history[-10:]]
            topic_mastery = profile.topic_mastery
        else:
            # 新学生默认策略
            dimension_ratio = 0.5
            recent_problems = []
            topic_mastery = {}
        
        # 根据 profile 数据制定推荐策略
        strategy = self.compute_recommendation_strategy(
            dimension_ratio=dimension_ratio,
            recent_problems=recent_problems,
            topic_mastery=topic_mastery
        )
        
        return strategy
```

**读取数据**：
- `dimension_ratio`：用于决定 R 型/M 型题的推荐比例
- `recent_problems`（最近10题的 problem_id 列表）：用于过滤近期做过的题
- `topic_mastery`：用于前置知识过滤

### 6.4 Module 5 读取接口（Module 4 → Module 5）

Module 5 在选择教学策略时读取学生 profile。

```python
# Module 5 的 TeachingStrategySelector
class TeachingStrategySelector:
    def __init__(self, profile_manager: ProfileManager):
        self.profile_manager = profile_manager
    
    async def select_strategy(self, student_id: str, problem_id: str) -> TeachingStrategy:
        profile = await self.profile_manager.get_profile(student_id)
        
        if not profile:
            return TeachingStrategy(lecture_ratio=0.3, practice_ratio=0.5, discussion_ratio=0.2)
        
        # 基于 dimension_ratio 决定讲授/练习/讨论配比
        if profile.dimension_ratio > 0.65:
            # R型薄弱，增加讲授比例
            return TeachingStrategy(lecture_ratio=0.4, practice_ratio=0.4, discussion_ratio=0.2)
        elif profile.dimension_ratio < 0.35:
            # M型薄弱，增加讨论比例
            return TeachingStrategy(lecture_ratio=0.2, practice_ratio=0.4, discussion_ratio=0.4)
        else:
            # 均衡状态
            return TeachingStrategy(lecture_ratio=0.3, practice_ratio=0.5, discussion_ratio=0.2)
```

### 6.5 接口依赖矩阵

| 调用方 | 被调用方法 | 用途 |
|-------|----------|------|
| Module 2 | `update_after_intervention()` | 干预结束后写回画像 |
| Module 2 | `get_routing_hint()` | 路由决策增强 |
| Module 3 | `get_profile()` | 读取 dimension_ratio、recent_problems |
| Module 3 | `get_recent_problems()` | 过滤近期做过的题 |
| Module 5 | `get_profile()` | 读取 dimension_ratio、topic_mastery |

---

## 7. ProfileManager 服务编排

### 7.1 ProfileManager 类设计

```python
class ProfileManager:
    """
    学生画像管理器
    负责学生的 CRUD 操作和画像更新
    """
    
    def __init__(self, profile_repo: StudentProfileRepository):
        self.profile_repo = profile_repo
        self.analytics = ProfileAnalytics(profile_repo)
        self.hint_generator = RoutingHintGenerator(profile_repo)
    
    async def get_profile(self, student_id: str) -> Optional[StudentProfile]:
        """
        获取学生完整画像
        如果不存在，返回 None
        """
        return await self.profile_repo.find_by_student_id(student_id)
    
    async def upsert_profile(self, student_id: str) -> StudentProfile:
        """
        创建或更新学生画像
        新学生：初始化默认 dimension_ratio=0.5，created_at=当前时间
        老学生：直接返回现有 profile
        """
        existing = await self.profile_repo.find_by_student_id(student_id)
        if existing:
            return existing
        
        # 创建新画像
        new_profile = StudentProfile(
            student_id=student_id,
            dimension_ratio=0.5,
            intervention_history=[],
            topic_mastery={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            total_interventions=0,
            total_solved=0,
            total_escalation=0,
            ratio_trend="stable",
            trend_confidence=0.0
        )
        
        return await self.profile_repo.save(new_profile)
    
    async def update_after_intervention(
        self,
        student_id: str,
        intervention_result: InterventionResult
    ) -> StudentProfile:
        """
        【核心方法】每次 Module 2 干预结束后调用
        
        1. 追加本次干预到 intervention_history
        2. 重新计算 dimension_ratio
        3. 更新 topic_mastery（如果提供 topic 信息）
        4. 更新 updated_at
        """
        # Step 1: 确保 profile 存在
        profile = await self.upsert_profile(student_id)
        
        # Step 2: 构建本次干预记录
        record = InterventionRecord(
            intervention_id=intervention_result.intervention_id,
            problem_id=intervention_result.problem_id,
            dimension=intervention_result.dimension,
            level=intervention_result.level,
            outcome=intervention_result.outcome,
            intervention_count=intervention_result.intervention_count,
            timestamp=datetime.utcnow()
        )
        
        # Step 3: 追加到 history（保留最近50条）
        profile.intervention_history.append(record)
        if len(profile.intervention_history) > 50:
            profile.intervention_history = profile.intervention_history[-50:]
        
        # Step 4: 重新计算 dimension_ratio
        profile.dimension_ratio = self._compute_dimension_ratio(
            profile.intervention_history
        )
        
        # Step 5: 更新统计
        profile.total_interventions += 1
        if intervention_result.outcome == "SOLVED":
            profile.total_solved += 1
        elif intervention_result.outcome == "MAX_ESCALATION":
            profile.total_escalation += 1
        
        # Step 6: 更新 topic_mastery（如果提供）
        if intervention_result.topic:
            profile.topic_mastery[intervention_result.topic] = TopicMastery(
                topic=intervention_result.topic,
                mastery_level=self._compute_mastery(
                    profile, intervention_result.topic
                ),
                last_practiced=datetime.utcnow(),
                practice_count=profile.topic_mastery.get(
                    intervention_result.topic,
                    TopicMastery(topic=intervention_result.topic)
                ).practice_count + 1
            )
        
        # Step 7: 保存更新
        profile.updated_at = datetime.utcnow()
        await self.profile_repo.save(profile)
        
        return profile
    
    async def get_dimension_ratio(self, student_id: str) -> float:
        """
        快速获取 dimension_ratio
        新学生返回 0.5（均衡默认）
        """
        profile = await self.get_profile(student_id)
        if not profile:
            return 0.5
        return profile.dimension_ratio
    
    async def get_recent_problems(
        self, student_id: str, limit: int = 10
    ) -> list[str]:
        """
        获取学生最近 N 道题的 problem_id 列表
        用于 Module 3 的推荐过滤
        """
        profile = await self.get_profile(student_id)
        if not profile or not profile.intervention_history:
            return []
        
        recent = profile.intervention_history[-limit:]
        return [r.problem_id for r in recent]
    
    async def get_routing_hint(self, student_id: str) -> RoutingHint:
        """
        获取路由增强提示
        被 Module 2 调用
        """
        return await self.hint_generator.generate(student_id)
```

### 7.2 _compute_dimension_ratio 方法

```python
def _compute_dimension_ratio(
    self, intervention_history: list[InterventionRecord]
) -> float:
    """
    计算 R/(R+M) 比例
    
    冷启动策略：干预次数 < 3 时返回默认 0.5
    """
    if not intervention_history:
        return 0.5
    
    if len(intervention_history) < 3:
        return 0.5
    
    r_count = sum(
        1 for r in intervention_history if r.dimension == "RESOURCE"
    )
    total = len(intervention_history)
    
    ratio = r_count / total if total > 0 else 0.5
    
    return ratio
```

### 7.3 _compute_mastery 方法

```python
def _compute_mastery(
    self, profile: StudentProfile, topic: str
) -> float:
    """
    计算知识点掌握度
    基于最近练习结果和历史成功率
    """
    # 获取该 topic 的历史记录
    topic_records = [
        r for r in profile.intervention_history
        if r.problem_id.startswith(topic) or r.topic == topic
    ][-10:]  # 最近10条
    
    if not topic_records:
        return 0.5  # 默认中等掌握度
    
    # 计算成功率
    solved_count = sum(1 for r in topic_records if r.outcome == "SOLVED")
    success_rate = solved_count / len(topic_records)
    
    # 考虑历史基础
    existing_mastery = profile.topic_mastery.get(topic)
    if existing_mastery:
        # 指数平滑
        alpha = 0.3  # 新数据权重
        return alpha * success_rate + (1 - alpha) * existing_mastery.mastery_level
    
    return success_rate
```

---

## 8. 错误处理与降级策略

### 8.1 错误场景处理

| 错误场景 | 处理方式 | 返回值 |
|---------|---------|--------|
| student_id 不存在 | 自动创建新 profile | 新建 profile，dimension_ratio=0.5 |
| MongoDB 查询失败 | 降级到内存缓存 | 返回缓存数据，标记 stale |
| intervention_history 为空 | 视为新学生处理 | is_new_student=True |
| dimension_ratio 计算异常（NaN） | 复位为 0.5 | 记录异常日志 |

### 8.2 降级策略实现

```python
class ProfileManager:
    def __init__(self, profile_repo: StudentProfileRepository):
        self.profile_repo = profile_repo
        self._memory_cache = {}  # 内存缓存，降级时使用
        self._cache_stale_flags = {}  # 标记缓存是否过期
    
    async def get_profile(self, student_id: str) -> Optional[StudentProfile]:
        try:
            profile = await self.profile_repo.find_by_student_id(student_id)
            
            if profile:
                # 更新内存缓存
                self._memory_cache[student_id] = profile
                self._cache_stale_flags[student_id] = False
            
            return profile
        
        except Exception as e:
            logger.warning(f"MongoDB query failed: {e}, falling back to memory cache")
            
            # 降级到内存缓存
            if student_id in self._memory_cache:
                self._cache_stale_flags[student_id] = True
                return self._memory_cache[student_id]
            
            # 缓存也没有，返回 None（上层会创建新 profile）
            return None
    
    async def update_after_intervention(
        self,
        student_id: str,
        intervention_result: InterventionResult
    ) -> StudentProfile:
        # 先尝试 MongoDB 更新
        try:
            profile = await self._update_mongodb(student_id, intervention_result)
            
            # 更新缓存
            self._memory_cache[student_id] = profile
            self._cache_stale_flags[student_id] = False
            
            return profile
        
        except Exception as e:
            logger.warning(f"MongoDB update failed: {e}, using memory-only mode")
            
            # 降级模式：仅更新内存
            profile = await self._update_memory(student_id, intervention_result)
            self._cache_stale_flags[student_id] = True
            
            # 异步尝试写回 MongoDB
            asyncio.create_task(self._sync_to_mongodb(student_id))
            
            return profile
    
    async def _sync_to_mongodb(self, student_id: str) -> None:
        """异步同步内存缓存到 MongoDB"""
        try:
            await self.profile_repo.save(self._memory_cache[student_id])
            self._cache_stale_flags[student_id] = False
        except Exception as e:
            logger.error(f"Failed to sync to MongoDB: {e}")
```

### 8.3 冷启动默认配置

新学生（干预次数 < 3）使用以下默认配置：

| 字段 | 默认值 |
|------|-------|
| `dimension_ratio` | 0.5（均衡） |
| `recent_dimension_bias` | balanced |
| `ratio_trend` | stable |
| `trend_confidence` | 0.0 |
| `recommended_dimension_hint` | "新学生，默认RESOURCE维度起步" |

### 8.4 异常处理

```python
async def update_after_intervention(...):
    try:
        # 正常的更新逻辑
        ...
    except ValueError as e:
        # dimension_ratio 计算异常（NaN）
        logger.error(f"dimension_ratio calculation error: {e}")
        profile.dimension_ratio = 0.5  # 复位
        return await self.profile_repo.save(profile)
    
    except Exception as e:
        # 其他异常，降级处理
        logger.error(f"Unexpected error in update_after_intervention: {e}")
        raise  # 重新抛出，由上层处理
```

---

## 9. 评估指标

### 9.1 数据质量指标

| 指标 | 定义 | 目标值 | 采集方式 |
|------|------|-------|---------|
| **profile 覆盖率** | 有画像的学生数 / 有过干预的学生数 | > 95% | MongoDB 统计 |
| **dimension_ratio 有效率** | dimension_ratio 非默认(0.5)的学生比例 | > 80%（随干预次数增加而提升） | MongoDB 统计 |
| **history 完整性** | 有 >= 3 条 intervention_history 的学生比例 | > 70% | MongoDB 统计 |
| **数据延迟** | 干预结束到 profile 更新的时间 | < 500ms | APM 埋点 |

### 9.2 分析准确性指标

| 指标 | 定义 | 目标值 | 采集方式 |
|------|------|-------|---------|
| **ratio_trend 准确率** | 趋势预测与后续实际表现的符合度 | > 65% | 回测分析 |
| **routing_hint 采纳率** | Module 2 实际采纳 routing_hint 建议的比例 | > 70% | 埋点日志 |
| **weak_dimensions 准确率** | 学生反馈薄弱的维度与系统判断的一致率 | > 60% | 学生反馈收集 |

### 9.3 系统性能指标

| 指标 | 目标值 | 告警阈值 |
|------|-------|---------|
| **get_profile 延迟** | < 20ms（P95） | > 50ms |
| **update_after_intervention 延迟** | < 50ms（P95） | > 100ms |
| **get_routing_hint 延迟** | < 30ms（P95） | > 80ms |
| **MongoDB 查询成功率** | > 99.9% | < 99.5% |

### 9.4 业务效果指标

| 指标 | 定义 | 目标值 | 采集方式 |
|------|------|-------|---------|
| **dimension_ratio 收敛率** | 干预10次后 dimension_ratio 进入 0.35-0.65 区间的学生比例 | > 50% | MongoDB 分析 |
| **学生留存率** | 有3次以上干预的学生比例 | > 60% | 用户系统数据 |
| **profile 驱动推荐接受率** | 学生接受带 routing_hint 推荐的题目 / 总推荐次数 | > 65% | Module 3 埋点 |

---

## 附录 A：RoutingHint 完整数据结构

```python
class RoutingHint(BaseModel):
    """路由增强提示结构"""
    student_id: str
    is_new_student: bool
    
    # 维度偏向
    recent_dimension_bias: str  # "R_dominant" | "M_dominant" | "balanced"
    dimension_ratio: float      # 0.0-1.0
    
    # 趋势
    ratio_trend: str           # "rising" | "falling" | "stable"
    trend_confidence: float     # 0.0-1.0
    
    # 薄弱维度
    weak_dimensions: list[str]  # 如 ["RESOURCE_R2", "METACOGNITIVE_M3"]
    
    # 建议
    recommended_dimension_hint: str
    
    # 最近干预摘要
    recent_intervention_summary: str  # "最近3次：R2, R3, M1（SOLVED）"
    
    # 整体置信度
    confidence: float           # 0.0-1.0
```

---

## 附录 B：错误处理流程

```
ProfileManager 调用
     │
     ▼
┌─────────────────────┐
│ MongoDB 可用？       │
└─────────────────────┘
     │
   Yes │ No
     │   │
     ▼   └──► 使用内存缓存
  执行 CRUD        │
     │             ▼
     │      ┌─────────────────┐
     │      │ 缓存有数据？    │
     │      └─────────────────┘
     │          │     │
     │        Yes   No
     │          │     │
     │          ▼     ▼
     │      返回缓存  返回 None
     │      标记 stale  （创建新profile）
     ▼
┌─────────────────────┐
│ 计算 dimension_ratio│
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│ 结果有效（非NaN）？  │
└─────────────────────┘
     │
   Yes │ No
     │   │
     ▼   └──► 复位为 0.5
  保存到 MongoDB      │
     │               ▼
     │         记录异常日志
     ▼
┌─────────────────────┐
│ 返回更新后的 Profile │
└─────────────────────┘
```

---

## 附录 C：模块依赖图

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           Socrates System                                │
│                                                                          │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                │
│  │  Module 1   │────►│  Module 2   │────►│  Module 3   │                │
│  │ 组织化解题   │     │ 断点干预    │     │ 智能推荐    │                │
│  └─────────────┘     └──────┬──────┘     └─────────────┘                │
│                             │                                            │
│                             │ update_after_intervention                  │
│                             ▼                                            │
│                      ┌─────────────────┐                                  │
│                      │   Module 4     │                                  │
│                      │  学生画像系统   │◄──────────────┐                  │
│                      │ dimension_ratio│              │                  │
│                      └────────┬────────┘              │                  │
│                               │                       │                  │
│                               │ get_routing_hint      │ get_profile     │
│                               ▼                       ▼                  │
│                      ┌─────────────────┐     ┌─────────────────┐         │
│                      │   Module 2     │     │  Module 3/5     │         │
│                      │  路由决策增强   │     │  读取画像数据   │         │
│                      └─────────────────┘     └─────────────────┘         │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

Module 4 是整个系统的数据基石，被 Module 2、3、5 共同依赖。
```

---

## 附录 D：MongoDB 迁移脚本

```python
"""004_create_student_profiles.py
为 students collection 创建必要索引
"""
from pymongo import MongoClient, ASCENDING, DESCENDING

def upgrade(mongo_client: MongoClient):
    db = mongo_client.socrates
    collection = db.students
    
    # 创建唯一索引
    collection.create_index("student_id", unique=True)
    
    # 创建维度比例索引（用于按 ratio 筛选学生）
    collection.create_index([("dimension_ratio", ASCENDING)])
    
    # 创建更新时间索引（用于查活跃学生）
    collection.create_index([("updated_at", DESCENDING)])
    
    # 创建干预历史时间索引（用于按时间范围查询）
    collection.create_index([("intervention_history.timestamp", DESCENDING)])

def downgrade(mongo_client: MongoClient):
    db = mongo_client.socrates
    collection = db.students
    collection.drop_index("student_id")
    collection.drop_index("dimension_ratio")
    collection.drop_index("updated_at")
    collection.drop_index("intervention_history.timestamp")
```

---

## 附录 E：文件清单

| 文件路径 | 职责 |
|---------|------|
| `models/student_profile.py` | 学生画像数据模型 |
| `models/intervention_record.py` | 干预记录子文档模型 |
| `models/topic_mastery.py` | 知识点掌握度模型 |
| `models/routing_hint.py` | 路由提示模型 |
| `repositories/student_profile_repo.py` | MongoDB 仓库 |
| `services/profile_manager.py` | 画像管理器 |
| `services/profile_analytics.py` | 趋势分析 |
| `services/routing_hint.py` | 路由增强 |
| `module.py` | 模块入口 |
| `routes.py` | FastAPI 路由 |
| `migrations/004_create_student_profiles.py` | MongoDB 迁移脚本 |

**预计代码量**: ~1,500 行

(End of file - total ~950 lines)
