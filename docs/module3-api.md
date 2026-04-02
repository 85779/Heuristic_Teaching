# Module 3 API 接口文档

## 智能练习题推荐系统

**版本**: 1.0.0  
**最后更新**: 2026-03-30  
**模块代号**: Socrates-Module-3-Recommendation

---

## 1. 模块定位与概述 (Module Position)

**模块名称**: 智能练习题推荐系统（Intelligent Problem Recommendation System）

**模块职能概述**: 智能练习题推荐系统是 Socrates 智能导师系统的核心推荐引擎，负责在学生完成一道题目后，基于学生的维度画像（R型 Resource / M型 Metacognitive）、历史答题记录、知识点掌握度等维度，智能推荐下一道最适合的练习题。系统采用七节点推荐管道，包括学生画像加载、候选题检索、四项打分（维度匹配、难度递进、间隔重复、题目质量）、综合排序和多样性保护，确保推荐结果既符合学生的认知发展水平，又能促进维度平衡。

**在整体架构中的位置**: Module 3 位于学生解题流程的推荐环节，接收来自 Module 2（断点干预系统）的触发事件，从 Module 4（学生画像系统）读取学生维度数据和历史记录，向题库（MongoDB）查询候选题目，最终将推荐结果推送到学生端。Module 3 与 Module 2 协同完成"干预-推荐-练习"的完整学习闭环。

**核心设计理念**: 本模块遵循"适度挑战"和"维度平衡"两大原则。适度挑战要求推荐题目的难度略高于学生当前水平（i+1原则），确保学生能够在已有知识基础上获得适度认知挑战。维度平衡要求根据学生的R/M维度画像动态调整推荐比例，防止学生过度依赖某一解题策略类型，促进认知能力的全面发展。

**技术选型理由**: 推荐管道采用纯 Python 异步实现，确保推荐响应时间满足实时性要求（P50 < 20ms）。学生画像加载使用 MongoDB 聚合查询，候选题检索使用预建索引的维度+难度复合查询，四项打分采用 asyncio 并行计算，最大化系统吞吐量。推荐历史使用 MongoDB 存储，支持后续分析和模型优化。

---

## 2. API Endpoints

### 2.1 POST /api/v1/recommend

**功能描述**: 基于学生当前状态触发智能推荐流程，返回 top-3 推荐题目列表。此端点是 Module 3 的核心入口，通常由 Module 2 在学生完成一道题或达到最大干预级别后调用，也可以由学生端主动触发"再来一题"请求。

**请求头**:
```
Content-Type: application/json
Authorization: Bearer <token>
X-Request-ID: <optional-request-id>
```

**请求体 (Request)**:
```json
{
  "student_id": "string (必需, 学生唯一标识)",
  "session_id": "string (必需, 推荐触发所属的会话标识)",
  "trigger_event": "TriggerEvent (必需, 触发事件类型)",
  "current_problem": {
    "problem_id": "string (必需, 当前完成的题目 ID)",
    "difficulty": "integer (必需, 当前题目难度等级 1-5)",
    "primary_dimension": "Dimension (必需, 当前题目的主维度)",
    "topic": "array<string> (可选, 当前题目知识点标签)",
    "topic_tree": "string (可选, 当前题目知识点树路径)"
  },
  "outcome": "FinalStatus (必需, 干预结果: SOLVED | MAX_ESCALATION | ABANDONED)"
}
```

**触发事件 (TriggerEvent) 枚举值**:
- `SOLVED`: 学生成功解决问题，触发正常推荐流程
- `MAX_ESCALATION`: 学生达到最大干预级别，触发降难度推荐策略
- `ABANDONED`: 学生主动放弃题目，触发轻度降难度推荐策略
- `MANUAL`: 学生主动请求"再来一题"，触发标准推荐流程

**请求体示例**:
```json
{
  "student_id": "stu_20260330_001",
  "session_id": "int_20260330_abc123",
  "trigger_event": "SOLVED",
  "current_problem": {
    "problem_id": "alg_seq_001",
    "difficulty": 2,
    "primary_dimension": "RESOURCE",
    "topic": ["数列", "通项公式"],
    "topic_tree": "代数/数列/通项公式"
  },
  "outcome": "SOLVED"
}
```

**响应体 (Response)**:
```json
{
  "recommendation_id": "string (推荐会话唯一标识)",
  "session_id": "string (关联的干预会话 ID)",
  "student_id": "string (学生 ID)",
  "trigger_event": "TriggerEvent",
  "strategy_applied": {
    "label": "string (策略标签, 如 R_BALANCED / M_DOMINANT / REDUCE_DIFFICULTY)",
    "dimension_ratio_target": {
      "r": "float (目标 R 型比例, 0.0-1.0)",
      "m": "float (目标 M 型比例, 0.0-1.0)"
    },
    "difficulty_target": "integer (目标难度等级, 1-5)",
    "adjustment_reason": "string (策略调整原因)"
  },
  "student_state_snapshot": {
    "dimension_ratio": "float (当前 R/M 比例, 0.0-1.0)",
    "current_difficulty": "integer (当前难度)",
    "weak_dimensions": "array<Dimension> (薄弱维度列表)",
    "recent_problems_count": "integer (最近做题数量)"
  },
  "recommendations": [
    {
      "rank": "integer (排名, 1-3)",
      "problem": {
        "problem_id": "string",
        "problem_text": "string (题目文本摘要)",
        "difficulty": "integer (难度等级 1-5)",
        "primary_dimension": "Dimension",
        "topic": "array<string> (知识点标签)",
        "topic_tree": "string (知识点树路径)",
        "estimated_time_minutes": "integer (预计完成时间)",
        "quality_score": "float (题目质量分, 0.0-1.0)"
      },
      "final_score": "float (综合得分, 0.0-1.0)",
      "score_breakdown": {
        "dim_score": "float (维度匹配分, 0.0-1.0)",
        "diff_score": "float (难度匹配分, 0.0-1.0)",
        "recency_score": "float (间隔新鲜度分, 0.0-1.0)",
        "quality_score": "float (题目质量分, 0.0-1.0)"
      },
      "recommended_reason": "string (推荐理由说明)"
    }
  ],
  "insufficient_candidates": "boolean (候选题是否不足)",
  "warnings": "array<string> (警告信息列表)",
  "created_at": "ISO8601 datetime",
  "processing_time_ms": "integer (处理耗时毫秒)"
}
```

**HTTP 状态码**:
- `200 OK`: 推荐生成成功
- `400 Bad Request`: 请求参数格式错误
- `404 Not Found`: 学生不存在或当前题目 ID 无效
- `422 Unprocessable Entity`: 业务逻辑校验失败（如 trigger_event 与 outcome 不匹配）
- `500 Internal Server Error`: 题库查询失败或系统内部错误
- `504 Gateway Timeout`: 题库查询超时（超过 100ms）

**响应示例**:
```json
{
  "recommendation_id": "rec_20260330_def456",
  "session_id": "int_20260330_abc123",
  "student_id": "stu_20260330_001",
  "trigger_event": "SOLVED",
  "strategy_applied": {
    "label": "R_BALANCED",
    "dimension_ratio_target": {
      "r": 0.60,
      "m": 0.40
    },
    "difficulty_target": 3,
    "adjustment_reason": "dimension_ratio 处于均衡区间 (0.35-0.65)，维持当前节奏"
  },
  "student_state_snapshot": {
    "dimension_ratio": 0.55,
    "current_difficulty": 2,
    "weak_dimensions": [],
    "recent_problems_count": 8
  },
  "recommendations": [
    {
      "rank": 1,
      "problem": {
        "problem_id": "alg_seq_007",
        "problem_text": "已知数列 {a_n} 满足 a_1 = 3, a_{n+1} = 2a_n + 1，求其通项公式。",
        "difficulty": 3,
        "primary_dimension": "RESOURCE",
        "topic": ["数列", "通项公式"],
        "topic_tree": "代数/数列/通项公式",
        "estimated_time_minutes": 12,
        "quality_score": 0.85
      },
      "final_score": 0.82,
      "score_breakdown": {
        "dim_score": 0.88,
        "diff_score": 1.00,
        "recency_score": 0.60,
        "quality_score": 0.85
      },
      "recommended_reason": "维度匹配 (RESOURCE->RESOURCE)，难度递进 (+1)，间隔新鲜度良好"
    },
    {
      "rank": 2,
      "problem": {
        "problem_id": "alg_seq_012",
        "problem_text": "求数列 2, 4, 8, 16, ... 的通项公式并计算第 10 项。",
        "difficulty": 3,
        "primary_dimension": "METACOGNITIVE",
        "topic": ["数列", "等比数列"],
        "topic_tree": "代数/数列/等比数列",
        "estimated_time_minutes": 15,
        "quality_score": 0.78
      },
      "final_score": 0.76,
      "score_breakdown": {
        "dim_score": 0.72,
        "diff_score": 0.80,
        "recency_score": 1.00,
        "quality_score": 0.78
      },
      "recommended_reason": "维度平衡推荐 (引入 M 型)，新鲜知识点"
    },
    {
      "rank": 3,
      "problem": {
        "problem_id": "alg_seq_018",
        "problem_text": "已知数列前 n 项和 S_n = n^2 + n，求该数列的通项公式。",
        "difficulty": 3,
        "primary_dimension": "RESOURCE",
        "topic": ["数列", "前 n 项和"],
        "topic_tree": "代数/数列/前 n 项和",
        "estimated_time_minutes": 10,
        "quality_score": 0.82
      },
      "final_score": 0.71,
      "score_breakdown": {
        "dim_score": 0.88,
        "diff_score": 0.80,
        "recency_score": 0.40,
        "quality_score": 0.82
      },
      "recommended_reason": "维度匹配，难度适中，题目质量优良"
    }
  ],
  "insufficient_candidates": false,
  "warnings": [],
  "created_at": "2026-03-30T10:05:30Z",
  "processing_time_ms": 18
}
```

---

### 2.2 GET /api/v1/recommend/{session_id}

**功能描述**: 获取指定推荐会话的完整推荐结果和状态信息。

**路径参数**:
- `session_id`: string (必需, 推荐会话唯一标识)

**请求头**:
```
Authorization: Bearer <token>
```

**响应体 (Response)**:
```json
{
  "recommendation_id": "string",
  "session_id": "string",
  "student_id": "string",
  "trigger_event": "TriggerEvent",
  "strategy_applied": {
    "label": "string",
    "dimension_ratio_target": {
      "r": "float",
      "m": "float"
    },
    "difficulty_target": "integer",
    "adjustment_reason": "string"
  },
  "student_state_snapshot": {
    "dimension_ratio": "float",
    "current_difficulty": "integer",
    "weak_dimensions": "array<Dimension>",
    "recent_problems_count": "integer"
  },
  "recommendations": [
    {
      "rank": "integer",
      "problem": { ... },
      "final_score": "float",
      "score_breakdown": { ... },
      "recommended_reason": "string"
    }
  ],
  "feedback_received": {
    "accepted_problem_id": "string | null",
    "rejected_problem_ids": "array<string>",
    "feedback_at": "ISO8601 datetime | null"
  },
  "insufficient_candidates": "boolean",
  "warnings": "array<string>",
  "created_at": "ISO8601 datetime"
}
```

**HTTP 状态码**:
- `200 OK`: 获取成功
- `404 Not Found`: 推荐会话不存在
- `500 Internal Server Error`: 系统内部错误

**响应示例**:
```json
{
  "recommendation_id": "rec_20260330_def456",
  "session_id": "int_20260330_abc123",
  "student_id": "stu_20260330_001",
  "trigger_event": "SOLVED",
  "strategy_applied": {
    "label": "R_BALANCED",
    "dimension_ratio_target": {
      "r": 0.60,
      "m": 0.40
    },
    "difficulty_target": 3,
    "adjustment_reason": "dimension_ratio 处于均衡区间"
  },
  "student_state_snapshot": {
    "dimension_ratio": 0.55,
    "current_difficulty": 2,
    "weak_dimensions": [],
    "recent_problems_count": 8
  },
  "recommendations": [ ... ],
  "feedback_received": {
    "accepted_problem_id": "alg_seq_007",
    "rejected_problem_ids": [],
    "feedback_at": "2026-03-30T10:06:00Z"
  },
  "insufficient_candidates": false,
  "warnings": [],
  "created_at": "2026-03-30T10:05:30Z"
}
```

---

### 2.3 POST /api/v1/recommend/feedback

**功能描述**: 接收学生对推荐结果的反馈（接受或拒绝），用于优化后续推荐策略和更新推荐历史。

**请求头**:
```
Content-Type: application/json
Authorization: Bearer <token>
```

**请求体 (Request)**:
```json
{
  "recommendation_id": "string (必需, 推荐会话唯一标识)",
  "student_id": "string (必需, 学生唯一标识，用于验证)",
  "accepted_problem_id": "string (可选, 学生接受的题目 ID)",
  "rejected_problem_ids": "array<string> (可选, 学生拒绝的题目 ID 列表)",
  "skip_reason": "string (可选, 如果全部跳过，说明原因)"
}
```

**请求体示例**:
```json
{
  "recommendation_id": "rec_20260330_def456",
  "student_id": "stu_20260330_001",
  "accepted_problem_id": "alg_seq_007",
  "rejected_problem_ids": []
}
```

**响应体 (Response)**:
```json
{
  "feedback_recorded": "boolean (反馈是否成功记录)",
  "recommendation_id": "string",
  "accepted_problem_id": "string | null",
  "rejected_problem_ids": "array<string>",
  "recorded_at": "ISO8601 datetime",
  "acknowledged": "boolean (是否已确认收到反馈)"
}
```

**HTTP 状态码**:
- `200 OK`: 反馈记录成功
- `400 Bad Request`: 请求参数格式错误
- `404 Not Found`: 推荐会话不存在
- `422 Unprocessable Entity`: 业务逻辑校验失败（反馈对象不匹配）
- `500 Internal Server Error`: 系统内部错误

**响应示例**:
```json
{
  "feedback_recorded": true,
  "recommendation_id": "rec_20260330_def456",
  "accepted_problem_id": "alg_seq_007",
  "rejected_problem_ids": [],
  "recorded_at": "2026-03-30T10:06:00Z",
  "acknowledged": true
}
```

---

### 2.4 GET /api/v1/problem_bank

**功能描述**: 查询题库中的题目列表，支持按维度、难度、知识点等条件筛选。此端点用于后台管理和题目统计分析。

**请求头**:
```
Authorization: Bearer <token>
```

**查询参数 (Query Parameters)**:
- `dimension`: Dimension (可选, 筛选主维度: RESOURCE | METACOGNITIVE)
- `difficulty_min`: integer (可选, 最小难度等级, 1-5)
- `difficulty_max`: integer (可选, 最大难度等级, 1-5)
- `topic`: string (可选, 知识点标签，模糊匹配)
- `status`: string (可选, 题目状态: active | deprecated | hidden, 默认 active)
- `limit`: integer (可选, 返回数量上限, 默认 20, 最大 100)
- `offset`: integer (可选, 分页偏移量, 默认 0)

**响应体 (Response)**:
```json
{
  "problems": [
    {
      "problem_id": "string",
      "problem_text": "string (题目文本，前200字符)",
      "difficulty": "integer (难度等级 1-5)",
      "primary_dimension": "Dimension",
      "resource_weight": "float (资源型特征权重, 0.0-1.0)",
      "metacognitive_weight": "float (元认知型特征权重, 0.0-1.0)",
      "topic": "array<string> (知识点标签)",
      "topic_tree": "string (知识点树路径)",
      "prerequisite_topics": "array<string> (前置知识点)",
      "quality_score": "float (题目质量分, 0.0-1.0)",
      "estimated_time_minutes": "integer",
      "usage_count": "integer (被推荐次数)",
      "completion_rate": "float (完成率, 0.0-1.0)",
      "status": "string",
      "created_at": "ISO8601 datetime"
    }
  ],
  "total": "integer (符合条件的总数)",
  "limit": "integer",
  "offset": "integer"
}
```

**HTTP 状态码**:
- `200 OK`: 查询成功
- `400 Bad Request`: 查询参数格式错误
- `500 Internal Server Error`: 系统内部错误

**响应示例**:
```json
{
  "problems": [
    {
      "problem_id": "alg_seq_001",
      "problem_text": "已知数列 {a_n} 满足 a_1 = 2, a_{n+1} = 3a_n + 1，求其通项公式。",
      "difficulty": 2,
      "primary_dimension": "RESOURCE",
      "resource_weight": 0.75,
      "metacognitive_weight": 0.25,
      "topic": ["数列", "通项公式"],
      "topic_tree": "代数/数列/通项公式",
      "prerequisite_topics": ["代数基础"],
      "quality_score": 0.85,
      "estimated_time_minutes": 10,
      "usage_count": 42,
      "completion_rate": 0.78,
      "status": "active",
      "created_at": "2026-03-15T08:00:00Z"
    }
  ],
  "total": 156,
  "limit": 20,
  "offset": 0
}
```

---

### 2.5 GET /api/v1/recommendation/history/{student_id}

**功能描述**: 获取指定学生的推荐历史记录，支持分页查询。

**路径参数**:
- `student_id`: string (必需, 学生唯一标识)

**请求头**:
```
Authorization: Bearer <token>
```

**查询参数 (Query Parameters)**:
- `limit`: integer (可选, 返回数量上限, 默认 20, 最大 100)
- `offset`: integer (可选, 分页偏移量, 默认 0)
- `trigger_event`: TriggerEvent (可选, 按触发事件类型筛选)
- `start_date`: ISO8601 date (可选, 筛选起始日期)
- `end_date`: ISO8601 date (可选, 筛选结束日期)

**响应体 (Response)**:
```json
{
  "history": [
    {
      "recommendation_id": "string",
      "session_id": "string",
      "trigger_event": "TriggerEvent",
      "trigger_timestamp": "ISO8601 datetime",
      "outcome": "FinalStatus | null",
      "student_state": {
        "dimension_ratio": "float",
        "current_difficulty": "integer",
        "current_dimension": "Dimension",
        "recent_problems": [
          {
            "problem_id": "string",
            "topic": "array<string>",
            "topic_tree": "string",
            "difficulty": "integer",
            "primary_dimension": "Dimension",
            "solved_at": "ISO8601 datetime"
          }
        ]
      },
      "recommendations": [
        {
          "rank": "integer",
          "problem_id": "string",
          "final_score": "float",
          "score_breakdown": {
            "dim_score": "float",
            "diff_score": "float",
            "recency_score": "float",
            "quality_score": "float"
          },
          "recommended_at": "ISO8601 datetime"
        }
      ],
      "strategy_applied": {
        "label": "string",
        "dimension_ratio_target": {
          "r": "float",
          "m": "float"
        },
        "adjustment_reason": "string"
      },
      "student_feedback": {
        "accepted_problem_id": "string | null",
        "rejected_problem_ids": "array<string>",
        "feedback_at": "ISO8601 datetime | null"
      },
      "created_at": "ISO8601 datetime"
    }
  ],
  "total": "integer (符合条件的总数)",
  "limit": "integer",
  "offset": "integer"
}
```

**HTTP 状态码**:
- `200 OK`: 查询成功
- `404 Not Found`: 学生不存在
- `500 Internal Server Error`: 系统内部错误

**响应示例**:
```json
{
  "history": [
    {
      "recommendation_id": "rec_20260330_def456",
      "session_id": "int_20260330_abc123",
      "trigger_event": "SOLVED",
      "trigger_timestamp": "2026-03-30T10:05:30Z",
      "outcome": null,
      "student_state": {
        "dimension_ratio": 0.55,
        "current_difficulty": 2,
        "current_dimension": "RESOURCE",
        "recent_problems": [
          {
            "problem_id": "alg_seq_001",
            "topic": ["数列", "通项公式"],
            "topic_tree": "代数/数列/通项公式",
            "difficulty": 2,
            "primary_dimension": "RESOURCE",
            "solved_at": "2026-03-30T10:05:00Z"
          }
        ]
      },
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
          "recommended_at": "2026-03-30T10:05:30Z"
        }
      ],
      "strategy_applied": {
        "label": "R_BALANCED",
        "dimension_ratio_target": {
          "r": 0.60,
          "m": 0.40
        },
        "adjustment_reason": "dimension_ratio 处于均衡区间"
      },
      "student_feedback": {
        "accepted_problem_id": "alg_seq_007",
        "rejected_problem_ids": [],
        "feedback_at": "2026-03-30T10:06:00Z"
      },
      "created_at": "2026-03-30T10:05:30Z"
    }
  ],
  "total": 45,
  "limit": 20,
  "offset": 0
}
```

---

### 2.6 GET /api/v1/recommendation/strategy/{student_id}

**功能描述**: 获取指定学生的当前推荐策略状态和维度画像摘要。

**路径参数**:
- `student_id`: string (必需, 学生唯一标识)

**请求头**:
```
Authorization: Bearer <token>
```

**响应体 (Response)**:
```json
{
  "student_id": "string",
  "dimension_profile": {
    "dimension_ratio": "float (当前 R 型比例, 0.0-1.0)",
    "r_type_count": "integer (R 型断点总数)",
    "m_type_count": "integer (M 型断点总数)",
    "total_breakpoints": "integer (总断点数)",
    "profile_status": "string (active | new_student | anomalous)"
  },
  "current_strategy": {
    "label": "string (策略标签)",
    "r_ratio": "float (目标 R 型比例)",
    "m_ratio": "float (目标 M 型比例)",
    "difficulty_strategy": "string (+1 | -1 | maintain)",
    "description": "string (策略描述)"
  },
  "difficulty_profile": {
    "current_difficulty": "integer (当前难度等级)",
    "average_completed_difficulty": "float (平均完成难度)",
    "success_rate_by_difficulty": {
      "1": "float",
      "2": "float",
      "3": "float",
      "4": "float",
      "5": "float"
    }
  },
  "topic_mastery": {
    "mastered_topics": "array<string> (掌握度 > 0.8 的知识点)",
    "learning_topics": "array<string> (掌握度 0.5-0.8 的知识点)",
    "weak_topics": "array<string> (掌握度 < 0.5 的知识点)"
  },
  "recent_performance": {
    "recommendations_accepted": "integer (最近推荐被接受次数)",
    "recommendations_rejected": "integer (最近推荐被拒绝次数)",
    "acceptance_rate": "float (接受率)",
    "average_completion_time_minutes": "float"
  },
  "updated_at": "ISO8601 datetime"
}
```

**HTTP 状态码**:
- `200 OK`: 获取成功
- `404 Not Found`: 学生不存在
- `500 Internal Server Error`: 系统内部错误

**响应示例**:
```json
{
  "student_id": "stu_20260330_001",
  "dimension_profile": {
    "dimension_ratio": 0.55,
    "r_type_count": 11,
    "m_type_count": 9,
    "total_breakpoints": 20,
    "profile_status": "active"
  },
  "current_strategy": {
    "label": "NEUTRAL",
    "r_ratio": 0.50,
    "m_ratio": 0.50,
    "difficulty_strategy": "+1",
    "description": "维度均衡，维持当前节奏"
  },
  "difficulty_profile": {
    "current_difficulty": 3,
    "average_completed_difficulty": 2.4,
    "success_rate_by_difficulty": {
      "1": 0.95,
      "2": 0.88,
      "3": 0.72,
      "4": 0.45,
      "5": 0.20
    }
  },
  "topic_mastery": {
    "mastered_topics": ["代数基础", "一元一次方程"],
    "learning_topics": ["数列", "通项公式"],
    "weak_topics": ["不等式", "函数"]
  },
  "recent_performance": {
    "recommendations_accepted": 15,
    "recommendations_rejected": 5,
    "acceptance_rate": 0.75,
    "average_completion_time_minutes": 12.5
  },
  "updated_at": "2026-03-30T10:00:00Z"
}
```

---

### 2.7 GET /api/v1/recommendation/health

**功能描述**: 健康检查接口，返回推荐系统各依赖服务的连接状态和整体可用性。

**请求头**:
```
Authorization: Bearer <token> (可选)
```

**响应体 (Response)**:
```json
{
  "status": "string (overall_status: healthy | degraded | unhealthy)",
  "timestamp": "ISO8601 datetime",
  "services": {
    "mongodb": {
      "connected": "boolean",
      "latency_ms": "integer (可选, 最近一次请求延迟)",
      "error": "string (可选, 连接错误信息)"
    },
    "problem_bank": {
      "total_problems": "integer (题库总题量)",
      "active_problems": "integer (活跃题目数量)",
      "last_updated": "ISO8601 datetime"
    }
  },
  "pipeline_nodes": {
    "student_profile_loader": {
      "status": "string (operational | degraded | offline)"
    },
    "candidate_retriever": {
      "status": "string",
      "average_retrieval_time_ms": "float"
    },
    "dimension_scorer": {
      "status": "string"
    },
    "difficulty_scorer": {
      "status": "string"
    },
    "spaced_repetition_scorer": {
      "status": "string"
    },
    "quality_scorer": {
      "status": "string"
    },
    "ranking_engine": {
      "status": "string"
    }
  },
  "performance_metrics": {
    "p50_latency_ms": "float",
    "p95_latency_ms": "float",
    "p99_latency_ms": "float",
    "requests_per_minute": "float",
    "error_rate": "float"
  },
  "service_status": "string (operational | degraded | offline)",
  "uptime_seconds": "integer",
  "version": "string (模块版本号)"
}
```

**HTTP 状态码**:
- `200 OK`: 健康检查完成（即使部分服务不健康也返回 200，具体状态在响应体中）
- `503 Service Unavailable`: 所有核心服务均不可用

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2026-03-30T10:05:00Z",
  "services": {
    "mongodb": {
      "connected": true,
      "latency_ms": 8
    },
    "problem_bank": {
      "total_problems": 1523,
      "active_problems": 1480,
      "last_updated": "2026-03-29T23:00:00Z"
    }
  },
  "pipeline_nodes": {
    "student_profile_loader": {
      "status": "operational"
    },
    "candidate_retriever": {
      "status": "operational",
      "average_retrieval_time_ms": 4.2
    },
    "dimension_scorer": {
      "status": "operational"
    },
    "difficulty_scorer": {
      "status": "operational"
    },
    "spaced_repetition_scorer": {
      "status": "operational"
    },
    "quality_scorer": {
      "status": "operational"
    },
    "ranking_engine": {
      "status": "operational"
    }
  },
  "performance_metrics": {
    "p50_latency_ms": 15.3,
    "p95_latency_ms": 42.1,
    "p99_latency_ms": 78.5,
    "requests_per_minute": 120.5,
    "error_rate": 0.001
  },
  "service_status": "operational",
  "uptime_seconds": 86400,
  "version": "1.0.0"
}
```

---

## 3. Data Models (数据模型)

### 3.1 TypeScript 类型定义

```typescript
// 触发事件枚举
type TriggerEvent = 
  | "SOLVED"        // 学生成功解决问题
  | "MAX_ESCALATION" // 达到最大干预级别
  | "ABANDONED"     // 学生主动放弃
  | "MANUAL";       // 学生主动请求

// 认知维度枚举
type Dimension = 
  | "RESOURCE"      // 资源型：提供外部知识、工具、步骤指导
  | "METACOGNITIVE"; // 元认知型：引导自我监控、策略反思

// 最终状态枚举
type FinalStatus = 
  | "SOLVED"           // 问题已解决
  | "MAX_ESCALATION"   // 达到最大干预级别
  | "ABANDONED";       // 学生放弃

// 题目状态枚举
type ProblemStatus = 
  | "active"      // 活跃题目，可被推荐
  | "deprecated"  // 已废弃
  | "hidden";     // 隐藏题目

// 推荐策略标签
type StrategyLabel = 
  | "R_BALANCED"    // 轻度偏 R，维持平衡
  | "R_DOMINANT"    // 中度偏 R，同知识点强化
  | "R_SEVERE"      // 严重偏 R，降难度补元认知
  | "M_BALANCED"    // 轻度偏 M，维持平衡
  | "M_DOMINANT"    // 中度偏 M，同知识点强化
  | "M_SEVERE"      // 严重偏 M，降难度补资源型
  | "NEUTRAL"       // 维度均衡
  | "NEW_STUDENT"   // 冷启动
  | "REDUCE_DIFFICULTY"       // 降难度策略
  | "REDUCE_DIFFICULTY_MILD"; // 轻度降难度

// 难度策略类型
type DifficultyStrategy = "+1" | "-1" | "maintain";

// 学生画像快照
interface StudentStateSnapshot {
  dimension_ratio: number;       // 0.0 - 1.0
  current_difficulty: number;     // 1 - 5
  weak_dimensions: Dimension[];
  recent_problems_count: number;
}

// 维度画像
interface DimensionProfile {
  dimension_ratio: number;
  r_type_count: number;
  m_type_count: number;
  total_breakpoints: number;
  profile_status: "active" | "new_student" | "anomalous";
}

// 题目基本信息
interface ProblemInfo {
  problem_id: string;
  problem_text: string;
  difficulty: number;             // 1 - 5
  primary_dimension: Dimension;
  topic: string[];
  topic_tree: string;
  estimated_time_minutes: number;
  quality_score: number;          // 0.0 - 1.0
}

// 推荐项
interface RecommendedProblem {
  rank: number;
  problem: ProblemInfo;
  final_score: number;            // 0.0 - 1.0
  score_breakdown: ScoreBreakdown;
  recommended_reason: string;
}

// 得分明细
interface ScoreBreakdown {
  dim_score: number;              // 维度匹配分
  diff_score: number;             // 难度匹配分
  recency_score: number;          // 间隔新鲜度分
  quality_score: number;           // 题目质量分
}

// 策略配置
interface StrategyConfig {
  label: StrategyLabel;
  dimension_ratio_target: {
    r: number;
    m: number;
  };
  difficulty_target?: number;
  difficulty_strategy?: DifficultyStrategy;
  adjustment_reason: string;
}

// 学生反馈
interface StudentFeedback {
  accepted_problem_id: string | null;
  rejected_problem_ids: string[];
  feedback_at: string | null;
}

// 推荐会话
interface RecommendationSession {
  recommendation_id: string;
  session_id: string;
  student_id: string;
  trigger_event: TriggerEvent;
  strategy_applied: StrategyConfig;
  student_state_snapshot: StudentStateSnapshot;
  recommendations: RecommendedProblem[];
  feedback_received: StudentFeedback;
  insufficient_candidates: boolean;
  warnings: string[];
  created_at: string;
}

// 知识点掌握度
interface TopicMastery {
  topic: string;
  mastery_score: number;          // 0.0 - 1.0
  questions_attempted: number;
  questions_correct: number;
  last_attempted_at: string;
}

// 推荐历史项
interface RecommendationHistoryItem {
  recommendation_id: string;
  session_id: string;
  trigger_event: TriggerEvent;
  trigger_timestamp: string;
  outcome: FinalStatus | null;
  student_state: {
    dimension_ratio: number;
    current_difficulty: number;
    current_dimension: Dimension;
    recent_problems: Array<{
      problem_id: string;
      topic: string[];
      topic_tree: string;
      difficulty: number;
      primary_dimension: Dimension;
      solved_at: string;
    }>;
  };
  recommendations: Array<{
    rank: number;
    problem_id: string;
    final_score: number;
    score_breakdown: ScoreBreakdown;
    recommended_at: string;
  }>;
  strategy_applied: StrategyConfig;
  student_feedback: StudentFeedback;
  created_at: string;
}

// 健康状态
interface HealthStatus {
  status: "healthy" | "degraded" | "unhealthy";
  timestamp: string;
  services: {
    mongodb: {
      connected: boolean;
      latency_ms?: number;
      error?: string;
    };
    problem_bank: {
      total_problems: number;
      active_problems: number;
      last_updated: string;
    };
  };
  pipeline_nodes: {
    student_profile_loader: { status: string };
    candidate_retriever: { 
      status: string;
      average_retrieval_time_ms?: number;
    };
    dimension_scorer: { status: string };
    difficulty_scorer: { status: string };
    spaced_repetition_scorer: { status: string };
    quality_scorer: { status: string };
    ranking_engine: { status: string };
  };
  performance_metrics: {
    p50_latency_ms: number;
    p95_latency_ms: number;
    p99_latency_ms: number;
    requests_per_minute: number;
    error_rate: number;
  };
  service_status: "operational" | "degraded" | "offline";
  uptime_seconds: number;
  version: string;
}
```

### 3.2 Pydantic 数据模型 (Python)

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime
from enum import Enum


class TriggerEvent(str, Enum):
    SOLVED = "SOLVED"
    MAX_ESCALATION = "MAX_ESCALATION"
    ABANDONED = "ABANDONED"
    MANUAL = "MANUAL"


class Dimension(str, Enum):
    RESOURCE = "RESOURCE"
    METACOGNITIVE = "METACOGNITIVE"


class FinalStatus(str, Enum):
    SOLVED = "SOLVED"
    MAX_ESCALATION = "MAX_ESCALATION"
    ABANDONED = "ABANDONED"


class ProblemStatus(str, Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    HIDDEN = "hidden"


class StrategyLabel(str, Enum):
    R_BALANCED = "R_BALANCED"
    R_DOMINANT = "R_DOMINANT"
    R_SEVERE = "R_SEVERE"
    M_BALANCED = "M_BALANCED"
    M_DOMINANT = "M_DOMINANT"
    M_SEVERE = "M_SEVERE"
    NEUTRAL = "NEUTRAL"
    NEW_STUDENT = "NEW_STUDENT"
    REDUCE_DIFFICULTY = "REDUCE_DIFFICULTY"
    REDUCE_DIFFICULTY_MILD = "REDUCE_DIFFICULTY_MILD"


class DifficultyStrategy(str, Enum):
    INCREASE = "+1"
    DECREASE = "-1"
    MAINTAIN = "maintain"


# ==================== Request Models ====================

class CurrentProblem(BaseModel):
    problem_id: str
    difficulty: int = Field(ge=1, le=5)
    primary_dimension: Dimension
    topic: List[str] = []
    topic_tree: Optional[str] = None


class RecommendRequest(BaseModel):
    student_id: str
    session_id: str
    trigger_event: TriggerEvent
    current_problem: CurrentProblem
    outcome: FinalStatus


class FeedbackRequest(BaseModel):
    recommendation_id: str
    student_id: str
    accepted_problem_id: Optional[str] = None
    rejected_problem_ids: List[str] = []
    skip_reason: Optional[str] = None


class ProblemBankQuery(BaseModel):
    dimension: Optional[Dimension] = None
    difficulty_min: Optional[int] = Field(default=None, ge=1, le=5)
    difficulty_max: Optional[int] = Field(default=None, ge=1, le=5)
    topic: Optional[str] = None
    status: Optional[ProblemStatus] = ProblemStatus.ACTIVE
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class RecommendationHistoryQuery(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    trigger_event: Optional[TriggerEvent] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


# ==================== Response Models ====================

class ScoreBreakdown(BaseModel):
    dim_score: float = Field(ge=0.0, le=1.0)
    diff_score: float = Field(ge=0.0, le=1.0)
    recency_score: float = Field(ge=0.0, le=1.0)
    quality_score: float = Field(ge=0.0, le=1.0)


class StrategyConfig(BaseModel):
    label: StrategyLabel
    dimension_ratio_target: Dict[str, float]
    difficulty_target: Optional[int] = None
    difficulty_strategy: Optional[DifficultyStrategy] = None
    adjustment_reason: str


class StudentStateSnapshot(BaseModel):
    dimension_ratio: float
    current_difficulty: int
    weak_dimensions: List[Dimension] = []
    recent_problems_count: int


class ProblemInfo(BaseModel):
    problem_id: str
    problem_text: str
    difficulty: int
    primary_dimension: Dimension
    topic: List[str] = []
    topic_tree: str
    estimated_time_minutes: int
    quality_score: float


class RecommendedProblem(BaseModel):
    rank: int
    problem: ProblemInfo
    final_score: float
    score_breakdown: ScoreBreakdown
    recommended_reason: str


class StudentFeedback(BaseModel):
    accepted_problem_id: Optional[str] = None
    rejected_problem_ids: List[str] = []
    feedback_at: Optional[datetime] = None


class RecommendResponse(BaseModel):
    recommendation_id: str
    session_id: str
    student_id: str
    trigger_event: TriggerEvent
    strategy_applied: StrategyConfig
    student_state_snapshot: StudentStateSnapshot
    recommendations: List[RecommendedProblem]
    insufficient_candidates: bool = False
    warnings: List[str] = []
    created_at: datetime
    processing_time_ms: int


class RecommendSessionResponse(BaseModel):
    recommendation_id: str
    session_id: str
    student_id: str
    trigger_event: TriggerEvent
    strategy_applied: StrategyConfig
    student_state_snapshot: StudentStateSnapshot
    recommendations: List[RecommendedProblem]
    feedback_received: StudentFeedback
    insufficient_candidates: bool = False
    warnings: List[str] = []
    created_at: datetime


class FeedbackResponse(BaseModel):
    feedback_recorded: bool
    recommendation_id: str
    accepted_problem_id: Optional[str] = None
    rejected_problem_ids: List[str] = []
    recorded_at: datetime
    acknowledged: bool = True


class ProblemBankItem(BaseModel):
    problem_id: str
    problem_text: str
    difficulty: int
    primary_dimension: Dimension
    resource_weight: float
    metacognitive_weight: float
    topic: List[str] = []
    topic_tree: str
    prerequisite_topics: List[str] = []
    quality_score: float
    estimated_time_minutes: int
    usage_count: int
    completion_rate: float
    status: ProblemStatus
    created_at: datetime


class ProblemBankResponse(BaseModel):
    problems: List[ProblemBankItem]
    total: int
    limit: int
    offset: int


class RecentProblem(BaseModel):
    problem_id: str
    topic: List[str]
    topic_tree: str
    difficulty: int
    primary_dimension: Dimension
    solved_at: datetime


class StudentStateHistory(BaseModel):
    dimension_ratio: float
    current_difficulty: int
    current_dimension: Dimension
    recent_problems: List[RecentProblem]


class RecommendationHistoryItem(BaseModel):
    recommendation_id: str
    session_id: str
    trigger_event: TriggerEvent
    trigger_timestamp: datetime
    outcome: Optional[FinalStatus] = None
    student_state: StudentStateHistory
    recommendations: List[Dict[str, Any]]
    strategy_applied: StrategyConfig
    student_feedback: StudentFeedback
    created_at: datetime


class RecommendationHistoryResponse(BaseModel):
    history: List[RecommendationHistoryItem]
    total: int
    limit: int
    offset: int


class DimensionProfile(BaseModel):
    dimension_ratio: float
    r_type_count: int
    m_type_count: int
    total_breakpoints: int
    profile_status: str


class CurrentStrategy(BaseModel):
    label: StrategyLabel
    r_ratio: float
    m_ratio: float
    difficulty_strategy: DifficultyStrategy
    description: str


class DifficultyProfile(BaseModel):
    current_difficulty: int
    average_completed_difficulty: float
    success_rate_by_difficulty: Dict[str, float]


class TopicMastery(BaseModel):
    mastered_topics: List[str] = []
    learning_topics: List[str] = []
    weak_topics: List[str] = []


class RecentPerformance(BaseModel):
    recommendations_accepted: int
    recommendations_rejected: int
    acceptance_rate: float
    average_completion_time_minutes: float


class StrategyResponse(BaseModel):
    student_id: str
    dimension_profile: DimensionProfile
    current_strategy: CurrentStrategy
    difficulty_profile: DifficultyProfile
    topic_mastery: TopicMastery
    recent_performance: RecentPerformance
    updated_at: datetime


class PipelineNodeStatus(BaseModel):
    status: str
    average_retrieval_time_ms: Optional[float] = None


class PerformanceMetrics(BaseModel):
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    requests_per_minute: float
    error_rate: float


class HealthStatus(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    timestamp: datetime
    services: Dict[str, Any]
    pipeline_nodes: Dict[str, PipelineNodeStatus]
    performance_metrics: PerformanceMetrics
    service_status: Literal["operational", "degraded", "offline"]
    uptime_seconds: int
    version: str
```

---

## 4. Internal Service Class (内部服务类)

### 4.1 RecommendationService 类定义

```python
from typing import Optional, Dict, Any, List
from datetime import datetime
from .models import (
    RecommendRequest,
    RecommendResponse,
    FeedbackRequest,
    FeedbackResponse,
    StrategyResponse,
    HealthStatus,
    TriggerEvent,
    Dimension,
    FinalStatus,
    StrategyLabel,
)


class RecommendationService:
    """
    智能练习题推荐服务核心类
    
    该服务封装了七节点推荐管道的所有业务逻辑：
    1. StudentProfileLoader: 从 Module 4 读取学生画像
    2. CandidateRetrieval: 从题库检索候选题，应用硬过滤
    3. DimensionScorer: 计算维度匹配分数
    4. DifficultyScorer: 计算难度匹配分数
    5. SpacedRepetitionScorer: 计算间隔新鲜度分数
    6. QualityScorer: 复用题目质量分数
    7. RankingEngine: 加权求和，综合排序
    
    Attributes:
        mongodb_client: MongoDB 客户端实例
        problem_bank_repo: 题库仓储实例
        recommendation_repo: 推荐历史仓储实例
        config: 服务配置参数
    """
    
    def __init__(
        self,
        mongodb_client: Any,
        problem_bank_repo: Any,
        recommendation_repo: Any,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        初始化推荐服务
        
        Args:
            mongodb_client: MongoDB 客户端实例
            problem_bank_repo: 题库仓储实例
            recommendation_repo: 推荐历史仓储实例
            config: 配置字典，包含各管道节点的参数
        """
        self.mongodb = mongodb_client
        self.problem_bank = problem_bank_repo
        self.recommendation_repo = recommendation_repo
        self.config = config or self._default_config()
        
        # 初始化七节点管道
        self._init_pipeline()
    
    def _default_config(self) -> Dict[str, Any]:
        """返回默认配置"""
        return {
            "profile_loader": {
                "cache_ttl_seconds": 300,
                "default_dimension_ratio": 0.5,
            },
            "candidate_retriever": {
                "max_candidates": 20,
                "hard_filter": {
                    "max_difficulty_gap": 2,
                    "min_topic_mastery": 0.5,
                    "min_topic_distance": 1,
                },
            },
            "scoring": {
                "weights": {
                    "dimension": 0.4,
                    "difficulty": 0.3,
                    "recency": 0.2,
                    "quality": 0.1,
                },
                "recency_windows": [1, 3, 5],
                "recency_scores": [0.3, 0.6, 0.8],
            },
            "ranking": {
                "top_n": 3,
                "diversity_protection": True,
            },
        }
    
    def _init_pipeline(self) -> None:
        """初始化七节点管道组件"""
        # Step 1: 学生画像加载器
        self.profile_loader = StudentProfileLoader(
            mongodb_client=self.mongodb,
            config=self.config.get("profile_loader", {}),
        )
        
        # Step 2: 候选题检索器
        self.candidate_retriever = CandidateRetrieval(
            problem_bank_repo=self.problem_bank,
            config=self.config.get("candidate_retriever", {}),
        )
        
        # Step 3-6: 打分器
        self.dimension_scorer = DimensionScorer(
            config=self.config.get("scoring", {}),
        )
        self.difficulty_scorer = DifficultyScorer(
            config=self.config.get("scoring", {}),
        )
        self.spaced_repetition_scorer = SpacedRepetitionScorer(
            config=self.config.get("scoring", {}),
        )
        self.quality_scorer = QualityScorer()
        
        # Step 7: 排序引擎
        self.ranking_engine = RankingEngine(
            config=self.config.get("ranking", {}),
        )
        
        # 策略选择器
        self.strategy_selector = StrategySelector(
            config=self.config,
        )
    
    # ==================== Core Methods ====================
    
    async def recommend(
        self,
        request: RecommendRequest,
    ) -> RecommendResponse:
        """
        执行完整的推荐流程
        
        执行七节点推荐管道：
        1. 加载学生画像（来自 Module 4）
        2. 选择推荐策略
        3. 检索候选题（硬过滤）
        4. 并行计算 4 项得分
        5. 综合排序（加权求和）
        6. 多样性保护（确保 top-3 足够分散）
        7. 生成推荐理由
        8. 写入推荐历史
        9. 返回推荐结果
        
        Args:
            request: RecommendRequest 推荐请求
        
        Returns:
            RecommendResponse: 包含 top-3 推荐结果和策略信息
        
        Raises:
            StudentNotFoundError: 学生不存在
            ProblemNotFoundError: 题目不存在
            InsufficientCandidatesError: 候选题不足
            RecommendationError: 推荐生成失败
        """
        start_time = datetime.utcnow()
        recommendation_id = self._generate_recommendation_id()
        
        # Step 1: 加载学生画像
        student_profile = await self.profile_loader.load(
            student_id=request.student_id,
        )
        
        # Step 2: 选择推荐策略
        strategy = self.strategy_selector.select(
            dimension_ratio=student_profile.dimension_ratio,
            outcome=request.outcome,
            current_dimension=request.current_problem.primary_dimension,
        )
        
        # Step 3: 检索候选题
        candidates = await self.candidate_retriever.retrieve(
            student_profile=student_profile,
            current_problem=request.current_problem,
            strategy=strategy,
        )
        
        # 检查候选题是否充足
        insufficient_candidates = len(candidates) < 3
        
        # 如果候选题不足，使用降级策略
        if insufficient_candidates and request.current_problem.problem_id:
            candidates = await self._fallback_recommendation(
                problem_id=request.current_problem.problem_id,
                candidates=candidates,
            )
        
        # Step 4-5: 并行计算得分并排序
        scored_candidates = await self._score_and_rank(
            candidates=candidates,
            student_profile=student_profile,
            strategy=strategy,
            current_problem=request.current_problem,
        )
        
        # Step 6: 构建推荐结果
        recommendations = self._build_recommendations(
            scored_candidates=scored_candidates,
            top_n=self.config["ranking"]["top_n"],
        )
        
        # Step 7: 生成学生状态快照
        student_state_snapshot = self._build_student_state_snapshot(
            student_profile=student_profile,
        )
        
        # Step 8: 写入推荐历史
        await self._persist_recommendation_history(
            recommendation_id=recommendation_id,
            request=request,
            recommendations=recommendations,
            strategy=strategy,
            student_state=student_state_snapshot,
        )
        
        # 计算处理耗时
        processing_time_ms = int(
            (datetime.utcnow() - start_time).total_seconds() * 1000
        )
        
        return RecommendResponse(
            recommendation_id=recommendation_id,
            session_id=request.session_id,
            student_id=request.student_id,
            trigger_event=request.trigger_event,
            strategy_applied=self._build_strategy_config(strategy),
            student_state_snapshot=student_state_snapshot,
            recommendations=recommendations,
            insufficient_candidates=insufficient_candidates,
            warnings=self._collect_warnings(candidates, strategy),
            created_at=start_time,
            processing_time_ms=processing_time_ms,
        )
    
    async def get_recommendation_session(
        self,
        session_id: str,
    ) -> RecommendSessionResponse:
        """
        获取指定推荐会话的完整信息
        
        Args:
            session_id: 推荐会话唯一标识
        
        Returns:
            RecommendSessionResponse: 推荐会话完整信息
        
        Raises:
            RecommendationNotFoundError: 推荐会话不存在
        """
        history = await self.recommendation_repo.get_by_session_id(
            session_id=session_id,
        )
        
        if history is None:
            raise RecommendationNotFoundError(
                f"Recommendation session {session_id} not found"
            )
        
        return self._build_session_response(history)
    
    async def record_feedback(
        self,
        request: FeedbackRequest,
    ) -> FeedbackResponse:
        """
        记录学生对推荐结果的反馈
        
        Args:
            request: FeedbackRequest 反馈请求
        
        Returns:
            FeedbackResponse: 反馈记录结果
        
        Raises:
            RecommendationNotFoundError: 推荐会话不存在
        """
        # 验证推荐会话存在
        history = await self.recommendation_repo.get_by_id(
            recommendation_id=request.recommendation_id,
        )
        
        if history is None:
            raise RecommendationNotFoundError(
                f"Recommendation {request.recommendation_id} not found"
            )
        
        # 更新反馈信息
        await self.recommendation_repo.update_feedback(
            recommendation_id=request.recommendation_id,
            accepted_problem_id=request.accepted_problem_id,
            rejected_problem_ids=request.rejected_problem_ids,
        )
        
        return FeedbackResponse(
            feedback_recorded=True,
            recommendation_id=request.recommendation_id,
            accepted_problem_id=request.accepted_problem_id,
            rejected_problem_ids=request.rejected_problem_ids,
            recorded_at=datetime.utcnow(),
            acknowledged=True,
        )
    
    async def get_recommendation_history(
        self,
        student_id: str,
        query: RecommendationHistoryQuery,
    ) -> RecommendationHistoryResponse:
        """
        获取学生的推荐历史
        
        Args:
            student_id: 学生唯一标识
            query: 查询参数
        
        Returns:
            RecommendationHistoryResponse: 推荐历史分页结果
        """
        history_list, total = await self.recommendation_repo.get_by_student(
            student_id=student_id,
            limit=query.limit,
            offset=query.offset,
            trigger_event=query.trigger_event,
            start_date=query.start_date,
            end_date=query.end_date,
        )
        
        return RecommendationHistoryResponse(
            history=[self._build_history_item(h) for h in history_list],
            total=total,
            limit=query.limit,
            offset=query.offset,
        )
    
    async def get_student_strategy(
        self,
        student_id: str,
    ) -> StrategyResponse:
        """
        获取学生的当前推荐策略状态
        
        Args:
            student_id: 学生唯一标识
        
        Returns:
            StrategyResponse: 策略状态信息
        
        Raises:
            StudentNotFoundError: 学生不存在
        """
        # 获取学生画像
        profile = await self.profile_loader.load(student_id=student_id)
        
        # 获取推荐历史
        _, total = await self.recommendation_repo.get_by_student(
            student_id=student_id,
            limit=1,
            offset=0,
        )
        
        # 计算策略
        current_strategy = self.strategy_selector.select(
            dimension_ratio=profile.dimension_ratio,
            outcome=None,
            current_dimension=None,
        )
        
        return StrategyResponse(
            student_id=student_id,
            dimension_profile=self._build_dimension_profile(profile),
            current_strategy=self._build_current_strategy(current_strategy),
            difficulty_profile=self._build_difficulty_profile(profile),
            topic_mastery=self._build_topic_mastery(profile),
            recent_performance=self._build_recent_performance(
                student_id=student_id
            ),
            updated_at=datetime.utcnow(),
        )
    
    def health_check(self) -> HealthStatus:
        """
        执行健康检查，返回系统各组件状态
        
        Returns:
            HealthStatus: 包含所有依赖服务状态的健康检查对象
        """
        # MongoDB 连接检查
        mongodb_status = self._check_mongodb_health()
        
        # 题库状态检查
        problem_bank_status = self._check_problem_bank_health()
        
        # 管道节点状态
        pipeline_status = {
            "student_profile_loader": {
                "status": "operational" if mongodb_status["connected"] else "degraded",
            },
            "candidate_retriever": {
                "status": "operational",
                "average_retrieval_time_ms": 4.2,
            },
            "dimension_scorer": {"status": "operational"},
            "difficulty_scorer": {"status": "operational"},
            "spaced_repetition_scorer": {"status": "operational"},
            "quality_scorer": {"status": "operational"},
            "ranking_engine": {"status": "operational"},
        }
        
        # 性能指标
        performance_metrics = self._get_performance_metrics()
        
        # 计算整体状态
        overall_status = "healthy"
        if not mongodb_status["connected"]:
            overall_status = "unhealthy"
        elif performance_metrics.get("error_rate", 0) > 0.01:
            overall_status = "degraded"
        
        return HealthStatus(
            status=overall_status,
            timestamp=datetime.utcnow(),
            services={
                "mongodb": mongodb_status,
                "problem_bank": problem_bank_status,
            },
            pipeline_nodes=pipeline_status,
            performance_metrics=performance_metrics,
            service_status=overall_status,
            uptime_seconds=self._get_uptime_seconds(),
            version=self.config.get("version", "1.0.0"),
        )
    
    # ==================== Helper Methods ====================
    
    def _generate_recommendation_id(self) -> str:
        """生成唯一的推荐 ID"""
        import uuid
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        unique_part = uuid.uuid4().hex[:8]
        return f"rec_{timestamp}_{unique_part}"
    
    async def _score_and_rank(
        self,
        candidates: List[CandidateProblem],
        student_profile: StudentProfile,
        strategy: RecommendationStrategy,
        current_problem: CurrentProblem,
    ) -> List[ScoredProblem]:
        """
        并行计算所有候选题的 4 项得分，然后综合排序
        
        使用 asyncio.gather 并行执行 4 个打分器
        """
        # 并行计算各项得分
        tasks = []
        for candidate in candidates:
            task = self._score_single(
                candidate=candidate,
                student_profile=student_profile,
                strategy=strategy,
                current_problem=current_problem,
            )
            tasks.append(task)
        
        scored = await asyncio.gather(*tasks)
        
        # 按综合得分降序排序
        ranked = sorted(
            scored,
            key=lambda p: p.final_score,
            reverse=True,
        )
        
        return ranked
    
    async def _score_single(
        self,
        candidate: CandidateProblem,
        student_profile: StudentProfile,
        strategy: RecommendationStrategy,
        current_problem: CurrentProblem,
    ) -> ScoredProblem:
        """
        对单个候选题计算 4 项得分和综合得分
        """
        # 计算各项得分
        dim_score = await self.dimension_scorer.score(
            problem=candidate,
            student_profile=student_profile,
            strategy=strategy,
        )
        
        diff_score = await self.difficulty_scorer.score(
            problem=candidate,
            target_difficulty=strategy.difficulty_target,
        )
        
        recency_score = await self.spaced_repetition_scorer.score(
            problem=candidate,
            recent_problems=student_profile.recent_problems,
        )
        
        quality_score = self.quality_scorer.score(candidate)
        
        # 计算综合得分
        weights = self.config["scoring"]["weights"]
        final_score = (
            weights["dimension"] * dim_score +
            weights["difficulty"] * diff_score +
            weights["recency"] * recency_score +
            weights["quality"] * quality_score
        )
        
        return ScoredProblem(
            candidate=candidate,
            final_score=final_score,
            score_breakdown=ScoreBreakdown(
                dim_score=dim_score,
                diff_score=diff_score,
                recency_score=recency_score,
                quality_score=quality_score,
            ),
        )
    
    async def _fallback_recommendation(
        self,
        problem_id: str,
        candidates: List[CandidateProblem],
    ) -> List[CandidateProblem]:
        """
        降级推荐策略：题库为空或所有候选都被过滤时的备选方案
        
        策略顺序：
        1. 获取当前题的 related_problems（变式题）
        2. 如果变式题存在，返回变式题列表
        3. 如果变式题也不存在，返回最基础的同知识点题
        4. 完全无题可推时，返回空列表
        """
        current_problem = await self.problem_bank.get(problem_id)
        
        if current_problem and current_problem.related_problems:
            related = await self.problem_bank.get_many(
                current_problem.related_problems
            )
            if related:
                return [self._to_candidate(p) for p in related]
        
        # 尝试返回同 topic 的基础题
        if current_problem and current_problem.topic:
            base_problems = await self.problem_bank.get_by_topic(
                topic=current_problem.topic[0],
                difficulty_range=(1, 2),
            )
            if base_problems:
                return [self._to_candidate(base_problems[0])]
        
        return candidates
    
    def _build_recommendations(
        self,
        scored_candidates: List[ScoredProblem],
        top_n: int,
    ) -> List[RecommendedProblem]:
        """构建推荐结果列表"""
        recommendations = []
        top_candidates = scored_candidates[:top_n]
        
        for i, scored in enumerate(top_candidates):
            candidate = scored.candidate
            recommendations.append(
                RecommendedProblem(
                    rank=i + 1,
                    problem=ProblemInfo(
                        problem_id=candidate.problem_id,
                        problem_text=candidate.problem_text[:200],
                        difficulty=candidate.difficulty,
                        primary_dimension=candidate.primary_dimension,
                        topic=candidate.topic,
                        topic_tree=candidate.topic_tree,
                        estimated_time_minutes=candidate.estimated_time_minutes,
                        quality_score=candidate.quality_score,
                    ),
                    final_score=scored.final_score,
                    score_breakdown=scored.score_breakdown,
                    recommended_reason=self._generate_recommendation_reason(
                        scored=scored,
                    ),
                )
            )
        
        return recommendations
    
    def _generate_recommendation_reason(
        self,
        scored: ScoredProblem,
    ) -> str:
        """生成推荐理由"""
        candidate = scored.candidate
        breakdown = scored.score_breakdown
        
        reasons = []
        
        # 维度匹配理由
        if breakdown.dim_score > 0.8:
            reasons.append(
                f"维度匹配 ({candidate.primary_dimension.value}->{candidate.primary_dimension.value})"
            )
        elif breakdown.dim_score > 0.6:
            reasons.append(
                f"维度平衡推荐 (引入 {candidate.primary_dimension.value} 型)"
            )
        
        # 难度匹配理由
        if breakdown.diff_score > 0.8:
            reasons.append("难度递进适中")
        elif breakdown.diff_score > 0.6:
            reasons.append("难度略有挑战")
        
        # 新鲜度理由
        if breakdown.recency_score > 0.8:
            reasons.append("新鲜知识点")
        elif breakdown.recency_score > 0.6:
            reasons.append("间隔适当")
        
        # 质量理由
        if breakdown.quality_score > 0.8:
            reasons.append("题目质量优良")
        
        return "，".join(reasons) if reasons else "综合得分最高"
    
    def _collect_warnings(
        self,
        candidates: List[CandidateProblem],
        strategy: RecommendationStrategy,
    ) -> List[str]:
        """收集警告信息"""
        warnings = []
        
        if len(candidates) < 3:
            warnings.append(
                f"候选题数量不足 ({len(candidates)} < 3)，可能影响推荐多样性"
            )
        
        if strategy.label in (StrategyLabel.R_SEVERE, StrategyLabel.M_SEVERE):
            warnings.append(
                f"学生维度严重偏离均衡，采用特殊策略 ({strategy.label})"
            )
        
        return warnings
    
    async def _persist_recommendation_history(
        self,
        recommendation_id: str,
        request: RecommendRequest,
        recommendations: List[RecommendedProblem],
        strategy: RecommendationStrategy,
        student_state: StudentStateSnapshot,
    ) -> None:
        """持久化推荐历史"""
        history_doc = {
            "recommendation_id": recommendation_id,
            "session_id": request.session_id,
            "student_id": request.student_id,
            "trigger_event": request.trigger_event.value,
            "trigger_timestamp": datetime.utcnow(),
            "outcome": request.outcome.value,
            "current_problem": {
                "problem_id": request.current_problem.problem_id,
                "difficulty": request.current_problem.difficulty,
                "primary_dimension": request.current_problem.primary_dimension.value,
                "topic": request.current_problem.topic,
                "topic_tree": request.current_problem.topic_tree,
            },
            "student_state": {
                "dimension_ratio": student_state.dimension_ratio,
                "current_difficulty": student_state.current_difficulty,
                "weak_dimensions": [d.value for d in student_state.weak_dimensions],
            },
            "recommendations": [
                {
                    "rank": r.rank,
                    "problem_id": r.problem.problem_id,
                    "final_score": r.final_score,
                    "score_breakdown": {
                        "dim_score": r.score_breakdown.dim_score,
                        "diff_score": r.score_breakdown.diff_score,
                        "recency_score": r.score_breakdown.recency_score,
                        "quality_score": r.score_breakdown.quality_score,
                    },
                    "recommended_at": datetime.utcnow(),
                }
                for r in recommendations
            ],
            "strategy_applied": {
                "label": strategy.label.value,
                "dimension_ratio_target": strategy.dimension_ratio_target,
                "adjustment_reason": strategy.adjustment_reason,
            },
            "student_feedback": {
                "accepted_problem_id": None,
                "rejected_problem_ids": [],
                "feedback_at": None,
            },
            "created_at": datetime.utcnow(),
        }
        
        await self.recommendation_repo.insert(history_doc)
```

---

## 5. Error Codes (错误代码)

### 5.1 错误码定义表

| 错误码 | HTTP 状态码 | 描述 | 可能原因 | 处理建议 |
|--------|-------------|------|----------|----------|
| `STUDENT_NOT_FOUND` | 404 | 指定的学生不存在 | 学生 ID 错误、新学生尚未建立画像 | 检查 student_id 是否正确，对于新学生系统会自动创建默认画像 |
| `PROBLEM_NOT_FOUND` | 404 | 指定的题目不存在 | 题目 ID 错误、题目已下架 | 检查 problem_id 是否正确，确认题目状态为 active |
| `RECOMMENDATION_NOT_FOUND` | 404 | 指定的推荐会话不存在 | 推荐 ID 错误、会话已过期 | 检查 recommendation_id 是否正确 |
| `INSUFFICIENT_CANDIDATES` | 200 | 题库候选题数量不足 | 题库规模小、硬过滤条件过严 | 返回可用候选题同时设置 insufficient_candidates=true |
| `EMPTY_BANK` | 200 | 题库为空或无可用题目 | 题库未初始化、题目全部下架 | 触发降级策略，返回 related_problems 或空列表 |
| `PROFILE_LOAD_FAILED` | 200 | 学生画像加载失败 | MongoDB 连接问题、数据损坏 | 使用默认策略（NEW_STUDENT），返回 warnings |
| `DIMENSION_RATIO_ANOMALY` | 200 | 维度比例数据异常 | 学生历史数据不足或比例极端 | 视为新学生处理，重置 dimension_ratio 为 0.5 |
| `MONGODB_CONNECTION_ERROR` | 503 | MongoDB 连接失败 | MongoDB 服务不可用、网络问题、认证失败 | 检查 MongoDB 服务状态、网络连接、认证配置 |
| `QUERY_TIMEOUT` | 504 | 数据库查询超时 | 查询复杂度高、数据库负载高 | 增加超时阈值、实施查询优化 |
| `INVALID_TRIGGER_EVENT` | 422 | 无效的触发事件类型 | trigger_event 参数值不在允许范围内 | 检查 trigger_event 是否为 SOLVED/MAX_ESCALATION/ABANDONED/MANUAL |
| `INVALID_DIMENSION` | 422 | 无效的认知维度 | dimension 参数值不是 RESOURCE 或 METACOGNITIVE | 检查 dimension 字段值 |
| `INVALID_DIFFICULTY` | 422 | 无效的难度等级 | difficulty 不在 1-5 范围内 | 检查 difficulty 值是否在 1-5 之间 |
| `INVALID_OUTCOME` | 422 | 无效的干预结果 | outcome 参数与 trigger_event 不匹配 | 检查 outcome 是否与干预结果一致 |
| `FEEDBACK_MISMATCH` | 422 | 反馈对象与推荐会话不匹配 | 反馈的 recommendation_id 与 student_id 不对应 | 验证 feedback 请求中的学生 ID 与推荐会话一致 |
| `RATE_LIMIT_EXCEEDED` | 429 | 请求频率超限 | 短时间内请求过多 | 实施请求限流、使用指数退避重试 |
| `UNAUTHORIZED` | 401 | 未授权访问 | 缺少或无效的认证 token | 检查 Authorization 请求头、刷新认证 token |
| `INTERNAL_ERROR` | 500 | 系统内部错误 | 未预期的异常情况 | 查看服务器日志，联系技术支持 |

### 5.2 错误响应格式

所有错误响应遵循以下 JSON 格式：

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "人类可读的错误描述",
    "details": {
      "field": "具体出错的字段（如果有）",
      "reason": "详细错误原因"
    },
    "request_id": "string (请求追踪 ID)",
    "timestamp": "ISO8601 datetime"
  }
}
```

### 5.3 错误处理策略

| 错误类型 | 自动重试 | 降级策略 | 人工告警 |
|----------|----------|----------|----------|
| `MONGODB_CONNECTION_ERROR` | 是（健康检查时） | 降级到只读缓存或默认策略 | 是（连续失败时） |
| `QUERY_TIMEOUT` | 是（最多2次） | 返回部分结果或空列表 | 记录但不告警 |
| `PROFILE_LOAD_FAILED` | 否 | 使用 NEW_STUDENT 默认策略 | 是 |
| `INSUFFICIENT_CANDIDATES` | 否 | 启用 fallback_recommendation | 记录但不告警 |
| `RATE_LIMIT_EXCEEDED` | 否 | 返回 429 错误 | 记录但不告警 |
| 其他错误 | 否 | 取决于具体错误 | 取决于严重程度 |

---

## 6. MongoDB Collections (MongoDB 数据集合)

### 6.1 student_recommendation_history 集合

**用途**: 存储学生的推荐历史，用于后续分析、profile 更新和效果评估。

**文档结构**:
```json
{
  "_id": "ObjectId",
  "recommendation_id": "string (索引, 唯一)",
  "session_id": "string (索引)",
  "student_id": "string (索引)",
  "trigger_event": "TriggerEvent",
  "trigger_timestamp": "ISODate",
  "outcome": "FinalStatus",
  
  "current_problem": {
    "problem_id": "string",
    "difficulty": "integer",
    "primary_dimension": "Dimension",
    "topic": ["string"],
    "topic_tree": "string"
  },
  
  "student_state": {
    "dimension_ratio": "float",
    "current_difficulty": "integer",
    "weak_dimensions": ["Dimension"],
    "recent_problems": [
      {
        "problem_id": "string",
        "topic": ["string"],
        "topic_tree": "string",
        "difficulty": "integer",
        "primary_dimension": "Dimension",
        "solved_at": "ISODate"
      }
    ]
  },
  
  "recommendations": [
    {
      "rank": "integer",
      "problem_id": "string",
      "final_score": "float",
      "score_breakdown": {
        "dim_score": "float",
        "diff_score": "float",
        "recency_score": "float",
        "quality_score": "float"
      },
      "recommended_at": "ISODate"
    }
  ],
  
  "strategy_applied": {
    "label": "StrategyLabel",
    "dimension_ratio_target": {
      "r": "float",
      "m": "float"
    },
    "difficulty_target": "integer",
    "adjustment_reason": "string"
  },
  
  "student_feedback": {
    "accepted_problem_id": "string | null",
    "rejected_problem_ids": ["string"],
    "feedback_at": "ISODate | null"
  },
  
  "warnings": ["string"],
  "processing_time_ms": "integer",
  "created_at": "ISODate"
}
```

**索引设计**:
```javascript
// 主键索引
{ "recommendation_id": 1 }  // unique: true

// 查询优化索引
{ "student_id": 1, "created_at": -1 }  // 按学生 ID 查询推荐历史（最频繁）
{ "session_id": 1 }  // 按会话 ID 查询
{ "trigger_event": 1, "created_at": -1 }  // 按触发事件统计

// 分析聚合索引
{ "student_feedback.accepted_problem_id": 1, "created_at": -1 }
{ "strategy_applied.label": 1, "created_at": -1 }
```

**TTL 策略**:
- 该集合数据保留期建议设置为 180-365 天
- 使用 `created_at` 字段作为 TTL 索引

---

### 6.2 problem_bank 集合

**用途**: 题库集合，存储所有可推荐题目的完整元数据。

**文档结构**:
```json
{
  "_id": "ObjectId",
  "problem_id": "string (索引, 唯一)",
  
  "problem_text": "string",
  "answer": "string (标准答案或解答)",
  "explanation": "string (题目解析)",
  
  "topic": ["string (知识点标签)"],
  "topic_tree": "string (知识点树路径)",
  "prerequisite_topics": ["string (前置知识点)"],
  
  "difficulty": "integer (难度等级 1-5)",
  "primary_dimension": "Dimension",
  "resource_weight": "float (资源型特征权重 0.0-1.0)",
  "metacognitive_weight": "float (元认知型特征权重 0.0-1.0)",
  
  "problem_type": "string (题目类型: 求解题/证明题/选择題等)",
  "related_problems": ["string (变式题 ID 列表)"],
  
  "quality_score": "float (题目质量分 0.0-1.0)",
  "estimated_time_minutes": "integer",
  
  "usage_count": "integer (被推荐次数)",
  "completion_rate": "float (完成率 0.0-1.0)",
  "avg_difficulty_rating": "float (学生评分平均难度)",
  
  "status": "ProblemStatus",
  
  "metadata": {
    "source": "string (题目来源)",
    "author": "string",
    "version": "string"
  },
  
  "created_at": "ISODate",
  "updated_at": "ISODate"
}
```

**索引设计**:
```javascript
// 主键索引
{ "problem_id": 1 }  // unique: true

// 维度+难度组合查询（最频繁）
{ "primary_dimension": 1, "difficulty": 1, "status": 1 }

// 知识点查询
{ "topic": 1 }
{ "topic_tree": 1 }

// 质量筛选
{ "quality_score": -1 }

// 状态+使用次数
{ "status": 1, "usage_count": -1 }

// 文本搜索
{ "problem_text": "text", "topic": "text" }
```

---

### 6.3 集合初始化脚本

```python
# MongoDB 集合初始化脚本
MONGODB_SETUP_SCRIPT = """
// 创建 student_recommendation_history 集合
db.createCollection("student_recommendation_history", {
   validator: {
      $jsonSchema: {
         bsonType: "object",
         required: ["recommendation_id", "student_id", "session_id", "trigger_event", "created_at"],
         properties: {
            recommendation_id: { bsonType: "string" },
            student_id: { bsonType: "string" },
            session_id: { bsonType: "string" },
            trigger_event: { 
               enum: ["SOLVED", "MAX_ESCALATION", "ABANDONED", "MANUAL"] 
            },
            created_at: { bsonType: "date" }
         }
      }
   }
})

// 创建 problem_bank 集合
db.createCollection("problem_bank", {
   validator: {
      $jsonSchema: {
         bsonType: "object",
         required: ["problem_id", "problem_text", "difficulty", "primary_dimension", "status", "created_at"],
         properties: {
            problem_id: { bsonType: "string" },
            problem_text: { bsonType: "string" },
            difficulty: { 
               bsonType: "int", 
               minimum: 1, 
               maximum: 5 
            },
            primary_dimension: { 
               enum: ["RESOURCE", "METACOGNITIVE"] 
            },
            status: { 
               enum: ["active", "deprecated", "hidden"] 
            },
            created_at: { bsonType: "date" }
         }
      }
   }
})

// 创建推荐历史索引
db.student_recommendation_history.createIndex(
   { "recommendation_id": 1 }, 
   { unique: true }
)
db.student_recommendation_history.createIndex(
   { "student_id": 1, "created_at": -1 }
)
db.student_recommendation_history.createIndex(
   { "session_id": 1 }
)

// 创建题库索引
db.problem_bank.createIndex(
   { "problem_id": 1 }, 
   { unique: true }
)
db.problem_bank.createIndex(
   { "primary_dimension": 1, "difficulty": 1, "status": 1 }
)
db.problem_bank.createIndex(
   { "topic": 1 }
)
db.problem_bank.createIndex(
   { "status": 1, "quality_score": -1 }
)
"""
```

---

## 7. Integration with Module 2 and Module 4 (模块集成)

### 7.1 Module 2 -> Module 3 触发集成

Module 3 提供两种方式与 Module 2 集成：同步 REST API 调用和异步事件驱动。

#### 7.1.1 REST API 触发方式

Module 2 在干预会话结束时（SOLVED / MAX_ESCALATION / ABANDONED）调用 Module 3 的 `/api/v1/recommend` 端点：

**触发时机**:

| Module 2 会话结果 | Module 3 trigger_event | Module 3 策略调整 |
|-------------------|------------------------|------------------|
| SOLVED | SOLVED | 正常推荐，目标难度 +1 |
| MAX_ESCALATION | MAX_ESCALATION | 降难度推荐，目标难度 -1 |
| ABANDONED | ABANDONED | 轻度降难度，目标难度维持或 -1 |
| 学生主动请求"再来一题" | MANUAL | 标准推荐流程 |

**调用示例** (Module 2 服务端):
```python
# Module 2: 干预会话结束时调用 Module 3
async def on_intervention_end(
    session_id: str,
    student_id: str,
    problem_id: str,
    outcome: FinalStatus,
    final_dimension: Dimension,
):
    # 调用 Module 3 推荐 API
    recommend_response = await recommendation_client.post(
        "/api/v1/recommend",
        json={
            "student_id": student_id,
            "session_id": session_id,
            "trigger_event": outcome.value,  # SOLVED / MAX_ESCALATION / ABANDONED
            "current_problem": {
                "problem_id": problem_id,
                "difficulty": current_difficulty,
                "primary_dimension": final_dimension,
            },
            "outcome": outcome.value,
        }
    )
    
    # 推送推荐结果到学生端
    if recommend_response.status == 200:
        recommendations = recommend_response.json()["recommendations"]
        await push_to_student(student_id, recommendations)
```

#### 7.1.2 异步事件驱动方式

Module 3 提供事件注册机制，Module 2 可以注册回调函数：

**事件类型**:
- `intervention_end`: 干预会话结束事件
- `student_manual_request`: 学生主动请求"再来一题"

**注册方式**:
```python
# Module 3: 事件触发器
class RecommendationTrigger:
    def register_trigger(
        self,
        event: str,
        callback: callable
    ) -> None:
        """
        注册触发回调
        
        Module 2 可以注册以下事件:
        - intervention_end: 干预结束（SOLVED / MAX_ESCALATION / ABANDONED）
        - student_manual_request: 学生主动请求
        """
        self._triggers[event] = callback
    
    async def emit(
        self,
        event: str,
        payload: dict
    ) -> None:
        """触发事件"""
        if event in self._triggers:
            await self._triggers[event](payload)


# Module 2: 注册事件处理器
recommendation_trigger.register_trigger(
    event="intervention_end",
    callback=self.on_intervention_end
)
```

#### 7.1.3 Webhook 事件格式

当使用 Webhook 方式集成时，Module 3 向 Module 2 配置的端点发送 POST 请求：

**Webhook  Payload**:
```json
{
  "event": "recommendation_generated",
  "recommendation_id": "rec_20260330_def456",
  "session_id": "int_20260330_abc123",
  "student_id": "stu_20260330_001",
  "trigger_event": "SOLVED",
  "recommendations": [
    {
      "rank": 1,
      "problem_id": "alg_seq_007",
      "problem_text": "已知数列...",
      "final_score": 0.82
    }
  ],
  "timestamp": "2026-03-30T10:05:30Z"
}
```

---

### 7.2 Module 3 -> Module 4 数据集成

Module 3 需要从 Module 4 获取学生画像数据，包括维度比例、历史答题记录、知识点掌握度等。

#### 7.2.1 数据获取接口

**学生画像加载 (StudentProfileLoader)**:
```python
class StudentProfileLoader:
    async def load(self, student_id: str) -> StudentProfile:
        """
        加载完整学生画像
        
        从 Module 4 获取:
        - dimension_ratio: R/M 维度比例
        - recent_problems: 最近 N 道题
        - weak_dimensions: 薄弱维度
        - topic_mastery: 知识点掌握度
        """
    
    async def get_dimension_ratio(self, student_id: str) -> float:
        """
        获取当前 R/M 比例
        
        计算公式: dimension_ratio = R 型断点数 / 总断点数
        
        边界情况:
        - 新学生: 返回 0.5
        - 比例异常 (<0.05 或 >0.95): 返回 0.5
        """
    
    async def get_recent_problems(
        self,
        student_id: str,
        limit: int = 10
    ) -> List[dict]:
        """
        获取最近 N 道题
        
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
    ) -> Dict[str, float]:
        """
        获取各知识点掌握度 (0.0-1.0)
        
        用于前置知识过滤:
        - 掌握度 < 0.5 的知识点对应的题不会被推荐
        - Module 4 未就绪时返回空字典
        """
```

#### 7.2.2 数据更新接口

推荐结果生成后，Module 3 需要通知 Module 4 更新学生画像：

**事件格式**:
```json
{
  "event": "recommendation_accepted",
  "student_id": "stu_20260330_001",
  "recommendation_id": "rec_20260330_def456",
  "accepted_problem_id": "alg_seq_007",
  "timestamp": "2026-03-30T10:06:00Z"
}
```

**触发时机**:
- 学生接受推荐题目时（`POST /api/v1/recommend/feedback`）
- 推荐结果被接受后，更新 `recent_problems` 和 `dimension_ratio`

---

### 7.3 集成时序图

```
学生端                    Module 2                  Module 3                  Module 4                   题库
  │                          │                          │                          │                       │
  │  解题完成                │                          │                          │                       │
  │─────────────────────────>│                          │                          │                       │
  │                          │                          │                          │                       │
  │                          │  [干预结束事件]           │                          │                       │
  │                          │─────────────────────────>│                          │                       │
  │                          │                          │                          │                       │
  │                          │                          │  get_profile()           │                       │
  │                          │                          │─────────────────────────>│                       │
  │                          │                          │<─────────────────────────│                       │
  │                          │                          │                          │                       │
  │                          │                          │  get_recent_problems()   │                       │
  │                          │                          │─────────────────────────>│                       │
  │                          │                          │<─────────────────────────>│                       │
  │                          │                          │                          │                       │
  │                          │                          │  查询候选题（难度+维度过滤）│                       │
  │                          │                          │────────────────────────────────────────────>│
  │                          │                          │<────────────────────────────────────────────│
  │                          │                          │                          │                       │
  │                          │                          │  [并行打分]              │                       │
  │                          │                          │    - dim_score           │                       │
  │                          │                          │    - diff_score          │                       │
  │                          │                          │    - recency_score       │                       │
  │                          │                          │    - quality_score       │                       │
  │                          │                          │                          │                       │
  │                          │                          │  [排序 + 多样性保护]      │                       │
  │                          │                          │                          │                       │
  │                          │                          │  写入推荐历史             │                       │
  │                          │                          │─────────────────────────>│                       │
  │                          │                          │                          │                       │
  │  返回 top-3 推荐          │                          │                          │                       │
  │<─────────────────────────│                          │                          │                       │
  │                          │                          │                          │                       │
  │  [学生接受推荐]           │                          │                          │                       │
  │─────────────────────────>│                          │                          │                       │
  │                          │                          │                          │                       │
  │                          │  [反馈]                   │  [更新 recent_problems]   │                       │
  │                          │─────────────────────────>│─────────────────────────>│                       │
  │                          │                          │                          │                       │
```

---

## 8. Rate Limiting (接口限流)

### 8.1 限流策略

| 端点 | 限制 | 时间窗口 | 超出响应 |
|------|------|----------|----------|
| POST /api/v1/recommend | 60 请求 | 1 分钟 | 429 Too Many Requests |
| GET /api/v1/recommend/{session_id} | 120 请求 | 1 分钟 | 429 Too Many Requests |
| POST /api/v1/recommend/feedback | 60 请求 | 1 分钟 | 429 Too Many Requests |
| GET /api/v1/problem_bank | 30 请求 | 1 分钟 | 429 Too Many Requests |
| GET /api/v1/recommendation/history/{student_id} | 30 请求 | 1 分钟 | 429 Too Many Requests |
| GET /api/v1/recommendation/strategy/{student_id} | 30 请求 | 1 分钟 | 429 Too Many Requests |
| GET /api/v1/recommendation/health | 10 请求 | 1 分钟 | 429 Too Many Requests |

### 8.2 限流响应头

限流触发的响应包含以下 HTTP 头：

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1743322800
Retry-After: 45
```

---

## 9. Authentication (认证授权)

### 9.1 认证方式

所有 API 端点（除健康检查外）需要 Bearer Token 认证：

```
Authorization: Bearer <token>
```

### 9.2 Token 验证

- Token 在请求头中传递
- Token 验证由 API Gateway 处理
- 无效或过期的 Token 返回 401 Unauthorized

### 9.3 权限模型

| 角色 | 权限 |
|------|------|
| student | 访问自己的推荐结果和历史 |
| teacher | 访问所有学生的推荐统计 |
| admin | 访问所有端点，包括问题银行管理 |

---

(End of file)
