# Module 4 API 接口文档

## 学生画像与认知建模系统

**版本**: 1.0.0
**最后更新**: 2026-03-30
**模块代号**: Socrates-Module-4-StudentProfile

---

## 1. 模块定位与概述 (Module Position)

**模块名称**: 学生画像与认知建模系统（Student Profile and Cognitive Modeling System）

**模块职能概述**: 学生画像与认知建模系统是 Socrates 智能导师系统的数据基石，负责维护每位学生的认知特征画像。系统核心指标 dimension_ratio（R型断点比例）反映了学生的认知薄弱点是知识缺口还是策略运用缺陷，为其他模块的个性化决策提供数据支撑。

**在整体架构中的位置**: Module 4 是整个系统的数据基石，被 Module 2（断点干预系统）、Module 3（智能推荐）、Module 5（教学策略）共同依赖。Module 2 在每次干预结束后将断点维度写入学生画像，Module 2/3/5 在决策前读取学生的维度偏向和趋势数据。

**核心设计理念**: 本模块遵循"数据驱动"和"冷启动友好"两大原则。数据驱动要求所有维度判断基于真实的干预历史数据，避免主观臆测。冷启动友好要求新学生（干预次数小于3次）使用默认均衡值，待数据积累后再计算真实比例。

**dimension_ratio 核心概念**:

```
dimension_ratio = R型断点次数 / 总断点次数
```

- **dimension_ratio = 0.7**: 学生偏重知识缺口，需要补充基础（RESOURCE型断点多）
- **dimension_ratio = 0.3**: 学生偏重元认知薄弱，需要训练策略运用（METACOGNITIVE型断点多）
- **dimension_ratio = 0.5**: 学生维度均衡

**技术选型理由**: 学生画像数据使用 MongoDB 存储，利用其文档型结构灵活存储干预历史数组和知识点掌握度映射。趋势计算采用简单线性回归，在保证准确性的同时满足实时性要求（P95 < 30ms）。

---

## 2. API 概述

### 2.1 基础信息

| 项目 | 说明 |
|------|------|
| **Base URL** | `/api/v1/profile` |
| **认证方式** | Bearer Token（JWT） |
| **内容类型** | `application/json` |
| **字符编码** | UTF-8 |

### 2.2 认证与授权

所有 API 请求必须在请求头中携带有效的 JWT Token：

```
Authorization: Bearer <token>
```

Token 验证策略：
- 验证 Token 签名有效性
- 检查 Token 过期时间
- 提取 `student_id` 或 `user_id` 字段用于权限校验

### 2.3 限流策略

| 限流维度 | 限制值 | 说明 |
|---------|--------|------|
| **每分钟请求数** | 1000 次/分钟 | 按 client_ip 统计 |
| **每学生每秒查询数** | 10 次/秒 | get_profile、get_routing_hint 等读接口 |
| **每学生每小时写入数** | 100 次/小时 | update_after_intervention 等写接口 |
| ** burst 突发配额** | 20 次 | 允许短期突发 |

限流响应头：

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

### 2.4 通用响应格式

**成功响应**:

```json
{
  "success": true,
  "data": { ... },
  "timestamp": "ISO8601 datetime"
}
```

**错误响应**:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误信息描述",
    "details": { ... }
  },
  "timestamp": "ISO8601 datetime"
}
```

### 2.5 通用分页参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `limit` | integer | 20 | 返回数量上限，最大 100 |
| `offset` | integer | 0 | 分页偏移量 |

---

## 3. API Endpoints

### 3.1 POST /api/v1/profile

**功能描述**: 创建或更新学生画像（upsert）。如果学生不存在，则创建新画像并初始化默认值为；如果学生存在，则返回现有画像。此接口主要用于初始化学生画像，实际干预更新由 `/api/v1/profile/{student_id}/intervention` 接口完成。

**请求头**:

```
Content-Type: application/json
Authorization: Bearer <token>
```

**请求体 (Request)**:

```json
{
  "student_id": "string (必需, 学生唯一标识)"
}
```

**请求体示例**:

```json
{
  "student_id": "stu_20260330_001"
}
```

**响应体 (Response)**:

```json
{
  "student_id": "string (学生唯一标识)",
  "dimension_ratio": "float (当前 R 型断点比例, 0.0-1.0)",
  "total_interventions": "integer (累计干预次数)",
  "total_solved": "integer (累计 SOLVED 次数)",
  "total_escalation": "integer (累计 MAX_ESCALATION 次数)",
  "intervention_history_count": "integer (干预历史记录条数)",
  "topic_mastery_count": "integer (知识点掌握度条目数)",
  "created_at": "ISO8601 datetime (画像创建时间)",
  "updated_at": "ISO8601 datetime (最后更新时间)",
  "is_new": "boolean (是否为新创建画像)"
}
```

**HTTP 状态码**:

- `200 OK`: 操作成功（学生已存在，返回现有画像）
- `201 Created`: 新建画像成功
- `400 Bad Request`: 请求参数格式错误
- `401 Unauthorized`: Token 无效或已过期
- `429 Too Many Requests`: 请求频率超限
- `500 Internal Server Error`: 系统内部错误

**响应示例**:

```json
{
  "student_id": "stu_20260330_001",
  "dimension_ratio": 0.5,
  "total_interventions": 0,
  "total_solved": 0,
  "total_escalation": 0,
  "intervention_history_count": 0,
  "topic_mastery_count": 0,
  "created_at": "2026-03-30T10:00:00Z",
  "updated_at": "2026-03-30T10:00:00Z",
  "is_new": true
}
```

---

### 3.2 GET /api/v1/profile/{student_id}

**功能描述**: 获取指定学生的完整画像信息。包括 dimension_ratio、干预历史摘要、知识点掌握度、统计数据等。

**路径参数**:

- `student_id`: string (必需, 学生唯一标识)

**请求头**:

```
Authorization: Bearer <token>
```

**响应体 (Response)**:

```json
{
  "student_id": "string (学生唯一标识)",
  "dimension_ratio": "float (R 型断点比例, 0.0-1.0)",
  "intervention_history": [
    {
      "intervention_id": "string (干预记录唯一标识)",
      "problem_id": "string (题目 ID)",
      "dimension": "Dimension (RESOURCE | METACOGNITIVE)",
      "level": "string (断点级别, 如 R2, M3)",
      "outcome": "FinalStatus (SOLVED | MAX_ESCALATION | ABANDONED)",
      "intervention_count": "integer (本题干预次数)",
      "timestamp": "ISO8601 datetime (干预时间)"
    }
  ],
  "topic_mastery": {
    "<topic_name>": {
      "topic": "string (知识点名称)",
      "mastery_level": "float (掌握度, 0.0-1.0)",
      "last_practiced": "ISO8601 datetime (最近练习时间)",
      "practice_count": "integer (练习次数)"
    }
  },
  "created_at": "ISO8601 datetime",
  "updated_at": "ISO8601 datetime",
  "total_interventions": "integer",
  "total_solved": "integer",
  "total_escalation": "integer",
  "ratio_trend": "string (rising | falling | stable)",
  "trend_confidence": "float (0.0-1.0)"
}
```

**HTTP 状态码**:

- `200 OK`: 获取成功
- `401 Unauthorized`: Token 无效或已过期
- `404 Not Found`: 学生不存在
- `429 Too Many Requests`: 请求频率超限
- `500 Internal Server Error`: 系统内部错误

**响应示例**:

```json
{
  "student_id": "stu_20260330_001",
  "dimension_ratio": 0.65,
  "intervention_history": [
    {
      "intervention_id": "int_20260330_001",
      "problem_id": "alg_seq_001",
      "dimension": "RESOURCE",
      "level": "R2",
      "outcome": "SOLVED",
      "intervention_count": 2,
      "timestamp": "2026-03-30T10:00:00Z"
    },
    {
      "intervention_id": "int_20260330_002",
      "problem_id": "alg_seq_002",
      "dimension": "METACOGNITIVE",
      "level": "M2",
      "outcome": "SOLVED",
      "intervention_count": 1,
      "timestamp": "2026-03-30T10:15:00Z"
    }
  ],
  "topic_mastery": {
    "数列": {
      "topic": "数列",
      "mastery_level": 0.75,
      "last_practiced": "2026-03-30T10:15:00Z",
      "practice_count": 12
    },
    "函数": {
      "topic": "函数",
      "mastery_level": 0.45,
      "last_practiced": "2026-03-29T15:00:00Z",
      "practice_count": 8
    }
  },
  "created_at": "2026-03-30T10:00:00Z",
  "updated_at": "2026-03-30T10:15:00Z",
  "total_interventions": 42,
  "total_solved": 35,
  "total_escalation": 7,
  "ratio_trend": "stable",
  "trend_confidence": 0.75
}
```

---

### 3.3 PUT /api/v1/profile/{student_id}/dimension

**功能描述**: 更新学生的 dimension_ratio。此接口由 Module 2 在获取到维度判定结果后调用，用于记录本次干预的维度类型并更新画像。替代直接调用干预记录接口的轻量级操作。

**路径参数**:

- `student_id`: string (必需, 学生唯一标识)

**请求头**:

```
Content-Type: application/json
Authorization: Bearer <token>
```

**请求体 (Request)**:

```json
{
  "dimension": "Dimension (必需, RESOURCE | METACOGNITIVE)",
  "problem_id": "string (必需, 题目 ID)",
  "level": "string (必需, 断点级别, 如 R2, M3)",
  "outcome": "FinalStatus (必需, SOLVED | MAX_ESCALATION | ABANDONED)",
  "intervention_count": "integer (可选, 本题干预次数, 默认 1)",
  "topic": "string (可选, 知识点名称)"
}
```

**请求体示例**:

```json
{
  "dimension": "RESOURCE",
  "problem_id": "alg_seq_001",
  "level": "R2",
  "outcome": "SOLVED",
  "intervention_count": 2,
  "topic": "数列"
}
```

**响应体 (Response)**:

```json
{
  "student_id": "string",
  "dimension": "Dimension (本次记录的维度)",
  "dimension_ratio": "float (更新后的 R 型断点比例)",
  "total_interventions": "integer (更新后的累计干预次数)",
  "total_solved": "integer (更新后的累计 SOLVED 次数)",
  "total_escalation": "integer (更新后的累计 MAX_ESCALATION 次数)",
  "updated_at": "ISO8601 datetime"
}
```

**HTTP 状态码**:

- `200 OK`: 更新成功
- `400 Bad Request`: 请求参数格式错误
- `401 Unauthorized`: Token 无效或已过期
- `404 Not Found`: 学生不存在
- `422 Unprocessable Entity`: 业务逻辑校验失败（如 dimension 值无效）
- `429 Too Many Requests`: 请求频率超限
- `500 Internal Server Error`: 系统内部错误

**响应示例**:

```json
{
  "student_id": "stu_20260330_001",
  "dimension": "RESOURCE",
  "dimension_ratio": 0.65,
  "total_interventions": 43,
  "total_solved": 36,
  "total_escalation": 7,
  "updated_at": "2026-03-30T10:30:00Z"
}
```

---

### 3.4 POST /api/v1/profile/{student_id}/intervention

**功能描述**: 追加干预记录到学生的 intervention_history。此接口是 Module 2 更新画像的主要入口，在每次干预结束（SOLVED / MAX_ESCALATION / ABANDONED）后调用。系统会自动重新计算 dimension_ratio，并更新相关统计数据。

**路径参数**:

- `student_id`: string (必需, 学生唯一标识)

**请求头**:

```
Content-Type: application/json
Authorization: Bearer <token>
```

**请求体 (Request)**:

```json
{
  "problem_id": "string (必需, 题目 ID)",
  "dimension": "Dimension (必需, RESOURCE | METACOGNITIVE)",
  "level": "string (必需, 断点级别, 如 R1-R4 | M1-M5)",
  "outcome": "FinalStatus (必需, SOLVED | MAX_ESCALATION | ABANDONED)",
  "intervention_count": "integer (可选, 本题干预次数, 默认 1)",
  "topic": "string (可选, 知识点名称)"
}
```

**请求体示例**:

```json
{
  "problem_id": "alg_seq_001",
  "dimension": "RESOURCE",
  "level": "R2",
  "outcome": "SOLVED",
  "intervention_count": 2,
  "topic": "数列"
}
```

**响应体 (Response)**:

```json
{
  "student_id": "string",
  "intervention_id": "string (本次创建的干预记录 ID)",
  "dimension_ratio": "float (更新后的 R 型断点比例)",
  "previous_ratio": "float (更新前的 R 型断点比例)",
  "ratio_change": "float (变化量, 正值表示偏 R, 负值表示偏 M)",
  "total_interventions": "integer",
  "total_solved": "integer",
  "total_escalation": "integer",
  "topic_mastery_updated": "boolean (知识点掌握度是否更新)",
  "updated_at": "ISO8601 datetime"
}
```

**HTTP 状态码**:

- `201 Created`: 干预记录追加成功
- `400 Bad Request`: 请求参数格式错误
- `401 Unauthorized`: Token 无效或已过期
- `404 Not Found`: 学生不存在（系统会自动创建新画像）
- `422 Unprocessable Entity`: 业务逻辑校验失败
- `429 Too Many Requests`: 请求频率超限
- `500 Internal Server Error`: 系统内部错误

**响应示例**:

```json
{
  "student_id": "stu_20260330_001",
  "intervention_id": "int_20260330_043",
  "dimension_ratio": 0.65,
  "previous_ratio": 0.63,
  "ratio_change": 0.02,
  "total_interventions": 43,
  "total_solved": 36,
  "total_escalation": 7,
  "topic_mastery_updated": true,
  "updated_at": "2026-03-30T10:30:00Z"
}
```

---

### 3.5 GET /api/v1/profile/{student_id}/analytics/trend

**功能描述**: 获取学生维度比例趋势分析。包括当前 ratio、窗口内 ratio、线性拟合斜率、趋势判定和置信度。

**路径参数**:

- `student_id`: string (必需, 学生唯一标识)

**请求头**:

```
Authorization: Bearer <token>
```

**查询参数 (Query Parameters)**:

- `window`: integer (可选, 分析窗口大小, 默认 10, 最大 50)

**响应体 (Response)**:

```json
{
  "student_id": "string",
  "current_ratio": "float (当前 dimension_ratio)",
  "window_ratio": "float (窗口内 dimension_ratio)",
  "slope": "float (线性拟合斜率)",
  "trend": "string (rising | falling | stable)",
  "confidence": "float (置信度, 0.0-1.0)",
  "window_size": "integer (使用的窗口大小)",
  "sample_count": "integer (实际样本数量)",
  "computed_at": "ISO8601 datetime"
}
```

**HTTP 状态码**:

- `200 OK`: 获取成功
- `401 Unauthorized`: Token 无效或已过期
- `404 Not Found`: 学生不存在
- `429 Too Many Requests`: 请求频率超限
- `500 Internal Server Error`: 系统内部错误

**响应示例**:

```json
{
  "student_id": "stu_20260330_001",
  "current_ratio": 0.65,
  "window_ratio": 0.68,
  "slope": 0.05,
  "trend": "rising",
  "confidence": 0.80,
  "window_size": 10,
  "sample_count": 10,
  "computed_at": "2026-03-30T10:30:00Z"
}
```

**趋势判定规则**:

| slope 范围 | trend 标签 | 说明 |
|-----------|-----------|------|
| slope > 0.1 | `rising` | dimension_ratio 上升，学生偏 R 方向 |
| slope < -0.1 | `falling` | dimension_ratio 下降，学生偏 M 方向 |
| -0.1 ≤ slope ≤ 0.1 | `stable` | 维度比例相对稳定 |

---

### 3.6 GET /api/v1/profile/{student_id}/routing-hint

**功能描述**: 获取路由增强提示，供 Module 2 的 DimensionRouter 和 SubTypeDecider 在决策前调用。此接口返回学生的维度偏向、趋势信息、薄弱维度和建议，帮助 Module 2 生成更准确的路由决策。

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
  "is_new_student": "boolean (是否新学生, < 3 次干预)",
  "recent_dimension_bias": "string (R_dominant | M_dominant | balanced)",
  "dimension_ratio": "float (当前 dimension_ratio)",
  "ratio_trend": "string (rising | falling | stable)",
  "trend_confidence": "float (0.0-1.0)",
  "weak_dimensions": "array<string> (薄弱维度列表, 如 RESOURCE_R2, METACOGNITIVE_M3)",
  "recommended_dimension_hint": "string (建议优先使用的维度)",
  "recent_intervention_summary": "string (最近 3 次干预的文字摘要)",
  "confidence": "float (整体置信度, 0.0-1.0)"
}
```

**HTTP 状态码**:

- `200 OK`: 获取成功
- `401 Unauthorized`: Token 无效或已过期
- `404 Not Found`: 学生不存在（返回新学生默认提示）
- `429 Too Many Requests`: 请求频率超限
- `500 Internal Server Error`: 系统内部错误

**响应示例**:

```json
{
  "student_id": "stu_20260330_001",
  "is_new_student": false,
  "recent_dimension_bias": "R_dominant",
  "dimension_ratio": 0.72,
  "ratio_trend": "rising",
  "trend_confidence": 0.75,
  "weak_dimensions": ["RESOURCE_R2", "RESOURCE_R3"],
  "recommended_dimension_hint": "学生R型断点多，建议使用METACOGNITIVE维度尝试引导策略思考",
  "recent_intervention_summary": "最近3次：R2(SOLVED), R3(SOLVED), R2(MAX_ESCALATION)",
  "confidence": 0.82
}
```

**recent_dimension_bias 判定规则**:

| dimension_ratio 范围 | bias 标签 | 说明 |
|---------------------|---------|------|
| > 0.65 | `R_dominant` | 学生偏 R 型，知识缺口明显 |
| < 0.35 | `M_dominant` | 学生偏 M 型，元认知薄弱 |
| 0.35-0.65 | `balanced` | 维度相对均衡 |

---

### 3.7 GET /api/v1/profile/{student_id}/history

**功能描述**: 获取学生的干预历史记录，支持分页查询。

**路径参数**:

- `student_id`: string (必需, 学生唯一标识)

**请求头**:

```
Authorization: Bearer <token>
```

**查询参数 (Query Parameters)**:

- `limit`: integer (可选, 返回数量上限, 默认 20, 最大 50)
- `offset`: integer (可选, 分页偏移量, 默认 0)
- `dimension`: Dimension (可选, 按维度筛选: RESOURCE | METACOGNITIVE)
- `outcome`: FinalStatus (可选, 按结果筛选: SOLVED | MAX_ESCALATION | ABANDONED)
- `start_date`: ISO8601 date (可选, 筛选起始日期)
- `end_date`: ISO8601 date (可选, 筛选结束日期)

**响应体 (Response)**:

```json
{
  "student_id": "string",
  "history": [
    {
      "intervention_id": "string",
      "problem_id": "string",
      "dimension": "Dimension",
      "level": "string",
      "outcome": "FinalStatus",
      "intervention_count": "integer",
      "topic": "string | null",
      "timestamp": "ISO8601 datetime"
    }
  ],
  "total": "integer (符合条件的总数)",
  "limit": "integer",
  "offset": "integer",
  "has_more": "boolean (是否还有更多记录)"
}
```

**HTTP 状态码**:

- `200 OK`: 获取成功
- `401 Unauthorized`: Token 无效或已过期
- `404 Not Found`: 学生不存在
- `429 Too Many Requests`: 请求频率超限
- `500 Internal Server Error`: 系统内部错误

**响应示例**:

```json
{
  "student_id": "stu_20260330_001",
  "history": [
    {
      "intervention_id": "int_20260330_043",
      "problem_id": "alg_seq_001",
      "dimension": "RESOURCE",
      "level": "R2",
      "outcome": "SOLVED",
      "intervention_count": 2,
      "topic": "数列",
      "timestamp": "2026-03-30T10:30:00Z"
    },
    {
      "intervention_id": "int_20260330_042",
      "problem_id": "alg_seq_002",
      "dimension": "METACOGNITIVE",
      "level": "M2",
      "outcome": "SOLVED",
      "intervention_count": 1,
      "topic": "数列",
      "timestamp": "2026-03-30T10:15:00Z"
    }
  ],
  "total": 43,
  "limit": 20,
  "offset": 0,
  "has_more": true
}
```

---

### 3.8 GET /api/v1/profile/health

**功能描述**: 健康检查接口，返回学生画像系统各依赖服务的连接状态和整体可用性。

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
    }
  },
  "storage_metrics": {
    "total_students": "integer (学生总数)",
    "active_students_24h": "integer (24小时内活跃的学生数)",
    "total_interventions": "integer (总干预记录数)"
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
      "latency_ms": 5
    }
  },
  "storage_metrics": {
    "total_students": 1523,
    "active_students_24h": 342,
    "total_interventions": 48562
  },
  "performance_metrics": {
    "p50_latency_ms": 8.5,
    "p95_latency_ms": 22.3,
    "p99_latency_ms": 45.1,
    "requests_per_minute": 156.2,
    "error_rate": 0.001
  },
  "service_status": "operational",
  "uptime_seconds": 86400,
  "version": "1.0.0"
}
```

---

## 4. Data Models (数据模型)

### 4.1 TypeScript 类型定义

```typescript
// 认知维度枚举
type Dimension = 
  | "RESOURCE"      // 资源型：提供外部知识、工具、步骤指导
  | "METACOGNITIVE"; // 元认知型：引导自我监控、策略反思

// 最终状态枚举
type FinalStatus = 
  | "SOLVED"           // 问题已解决
  | "MAX_ESCALATION"   // 达到最大干预级别
  | "ABANDONED";       // 学生放弃

// 维度偏向枚举
type DimensionBias = 
  | "R_dominant"   // R 型主导
  | "M_dominant"   // M 型主导
  | "balanced";    // 均衡

// 趋势枚举
type TrendLabel = 
  | "rising"    // 上升
  | "falling"  // 下降
  | "stable";  // 稳定

// 干预记录
interface InterventionRecord {
  intervention_id: string;
  problem_id: string;
  dimension: Dimension;
  level: string;           // R1-R4 或 M1-M5
  outcome: FinalStatus;
  intervention_count: number;
  topic?: string;
  timestamp: string;      // ISO8601
}

// 知识点掌握度
interface TopicMastery {
  topic: string;
  mastery_level: number;   // 0.0 - 1.0
  last_practiced: string;  // ISO8601
  practice_count: number;
}

// 学生画像
interface StudentProfile {
  student_id: string;
  dimension_ratio: number;       // 0.0 - 1.0
  intervention_history: InterventionRecord[];
  topic_mastery: Record<string, TopicMastery>;
  created_at: string;
  updated_at: string;
  total_interventions: number;
  total_solved: number;
  total_escalation: number;
  ratio_trend: TrendLabel;
  trend_confidence: number;       // 0.0 - 1.0
}

// 趋势分析结果
interface TrendAnalysis {
  student_id: string;
  current_ratio: number;
  window_ratio: number;
  slope: number;
  trend: TrendLabel;
  confidence: number;
  window_size: number;
  sample_count: number;
  computed_at: string;
}

// 路由增强提示
interface RoutingHint {
  student_id: string;
  is_new_student: boolean;
  recent_dimension_bias: DimensionBias;
  dimension_ratio: number;
  ratio_trend: TrendLabel;
  trend_confidence: number;
  weak_dimensions: string[];
  recommended_dimension_hint: string;
  recent_intervention_summary: string;
  confidence: number;
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
  };
  storage_metrics: {
    total_students: number;
    active_students_24h: number;
    total_interventions: number;
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

### 4.2 Pydantic 数据模型 (Python)

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime
from enum import Enum


class Dimension(str, Enum):
    RESOURCE = "RESOURCE"
    METACOGNITIVE = "METACOGNITIVE"


class FinalStatus(str, Enum):
    SOLVED = "SOLVED"
    MAX_ESCALATION = "MAX_ESCALATION"
    ABANDONED = "ABANDONED"


class DimensionBias(str, Enum):
    R_DOMINANT = "R_dominant"
    M_DOMINANT = "M_dominant"
    BALANCED = "balanced"


class TrendLabel(str, Enum):
    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"


# ==================== Request Models ====================

class UpsertProfileRequest(BaseModel):
    student_id: str = Field(..., description="学生唯一标识")


class UpdateDimensionRequest(BaseModel):
    dimension: Dimension = Field(..., description="断点维度")
    problem_id: str = Field(..., description="题目 ID")
    level: str = Field(..., description="断点级别, 如 R2, M3")
    outcome: FinalStatus = Field(..., description="干预结果")
    intervention_count: int = Field(default=1, ge=1, description="本题干预次数")
    topic: Optional[str] = Field(None, description="知识点名称")


class AddInterventionRequest(BaseModel):
    problem_id: str = Field(..., description="题目 ID")
    dimension: Dimension = Field(..., description="断点维度")
    level: str = Field(..., description="断点级别, 如 R1-R4 | M1-M5")
    outcome: FinalStatus = Field(..., description="干预结果")
    intervention_count: int = Field(default=1, ge=1, description="本题干预次数")
    topic: Optional[str] = Field(None, description="知识点名称")


class HistoryQuery(BaseModel):
    limit: int = Field(default=20, ge=1, le=50)
    offset: int = Field(default=0, ge=0)
    dimension: Optional[Dimension] = None
    outcome: Optional[FinalStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class TrendQuery(BaseModel):
    window: int = Field(default=10, ge=3, le=50)


# ==================== Response Models ====================

class InterventionRecord(BaseModel):
    intervention_id: str
    problem_id: str
    dimension: Dimension
    level: str
    outcome: FinalStatus
    intervention_count: int
    topic: Optional[str] = None
    timestamp: datetime


class TopicMastery(BaseModel):
    topic: str
    mastery_level: float = Field(ge=0.0, le=1.0)
    last_practiced: datetime
    practice_count: int


class StudentProfile(BaseModel):
    student_id: str
    dimension_ratio: float = Field(ge=0.0, le=1.0)
    intervention_history: List[InterventionRecord] = []
    topic_mastery: Dict[str, TopicMastery] = {}
    created_at: datetime
    updated_at: datetime
    total_interventions: int = 0
    total_solved: int = 0
    total_escalation: int = 0
    ratio_trend: TrendLabel = TrendLabel.STABLE
    trend_confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class UpsertProfileResponse(BaseModel):
    student_id: str
    dimension_ratio: float
    total_interventions: int
    total_solved: int
    total_escalation: int
    intervention_history_count: int
    topic_mastery_count: int
    created_at: datetime
    updated_at: datetime
    is_new: bool


class GetProfileResponse(BaseModel):
    student_id: str
    dimension_ratio: float
    intervention_history: List[InterventionRecord]
    topic_mastery: Dict[str, TopicMastery]
    created_at: datetime
    updated_at: datetime
    total_interventions: int
    total_solved: int
    total_escalation: int
    ratio_trend: TrendLabel
    trend_confidence: float


class UpdateDimensionResponse(BaseModel):
    student_id: str
    dimension: Dimension
    dimension_ratio: float
    total_interventions: int
    total_solved: int
    total_escalation: int
    updated_at: datetime


class AddInterventionResponse(BaseModel):
    student_id: str
    intervention_id: str
    dimension_ratio: float
    previous_ratio: float
    ratio_change: float
    total_interventions: int
    total_solved: int
    total_escalation: int
    topic_mastery_updated: bool
    updated_at: datetime


class TrendAnalysis(BaseModel):
    student_id: str
    current_ratio: float
    window_ratio: float
    slope: float
    trend: TrendLabel
    confidence: float
    window_size: int
    sample_count: int
    computed_at: datetime


class RoutingHint(BaseModel):
    student_id: str
    is_new_student: bool
    recent_dimension_bias: DimensionBias
    dimension_ratio: float
    ratio_trend: TrendLabel
    trend_confidence: float
    weak_dimensions: List[str]
    recommended_dimension_hint: str
    recent_intervention_summary: str
    confidence: float


class HistoryItem(BaseModel):
    intervention_id: str
    problem_id: str
    dimension: Dimension
    level: str
    outcome: FinalStatus
    intervention_count: int
    topic: Optional[str]
    timestamp: datetime


class HistoryResponse(BaseModel):
    student_id: str
    history: List[HistoryItem]
    total: int
    limit: int
    offset: int
    has_more: bool


class StorageMetrics(BaseModel):
    total_students: int
    active_students_24h: int
    total_interventions: int


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
    storage_metrics: StorageMetrics
    performance_metrics: PerformanceMetrics
    service_status: Literal["operational", "degraded", "offline"]
    uptime_seconds: int
    version: str
```

---

## 5. Error Codes (错误码)

| 错误码 | HTTP 状态码 | 说明 | 处理建议 |
|--------|-------------|------|----------|
| `STUDENT_NOT_FOUND` | 404 | 学生不存在 | 调用 upsert 接口创建新画像，或检查 student_id 是否正确 |
| `INVALID_DIMENSION` | 422 | 维度值无效 | 确保 dimension 为 RESOURCE 或 METACOGNITIVE |
| `INVALID_OUTCOME` | 422 | 结果状态无效 | 确保 outcome 为 SOLVED、MAX_ESCALATION 或 ABANDONED |
| `INVALID_LEVEL` | 422 | 断点级别无效 | 确保 level 格式为 R1-R4 或 M1-M5 |
| `HISTORY_NOT_FOUND` | 404 | 干预历史不存在 | 学生尚无干预记录，属于正常情况 |
| `INVALID_DATE_RANGE` | 422 | 日期范围无效 | 确保 start_date <= end_date |
| `WINDOW_SIZE_INVALID` | 422 | 窗口大小无效 | 确保 window 在 3-50 之间 |
| `MONGODB_CONNECTION_ERROR` | 503 | MongoDB 连接失败 | 检查 MongoDB 服务状态，触发降级策略 |
| `RATE_LIMIT_EXCEEDED` | 429 | 请求频率超限 | 降低请求频率，等待限流重置 |
| `UNAUTHORIZED` | 401 | 认证失败 | 检查 Token 有效性，重新获取 Token |

---

## 6. Module Integration (模块集成说明)

### 6.1 模块依赖关系

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

### 6.2 Module 2 调用 Module 4

**写入接口（Module 2 → Module 4）**:

Module 2 在每次干预结束时调用干预记录接口更新画像：

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

**调用时机**:
- 学生完成一道题（SOLVED）
- 学生达到最大干预强度（MAX_ESCALATION）
- 学生主动放弃（ABANDONED）

**读取接口（Module 4 → Module 2）**:

Module 2 的 DimensionRouter 和 SubTypeDecider 在决策前读取路由提示：

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

### 6.3 Module 3 调用 Module 4

Module 3 在推荐题目时读取学生画像数据：

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

**读取数据**:
- `dimension_ratio`：用于决定 R 型/M 型题的推荐比例
- `recent_problems`（最近10题的 problem_id 列表）：用于过滤近期做过的题
- `topic_mastery`：用于前置知识过滤

### 6.4 Module 5 调用 Module 4

Module 5 在选择教学策略时读取学生画像：

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

## 7. MongoDB 文档示例

### 7.1 students Collection Schema

```javascript
{
  "_id": ObjectId("..."),
  "student_id": "stu_20260330_001",
  "dimension_ratio": 0.65,
  
  "intervention_history": [
    {
      "intervention_id": "int_20260330_001",
      "problem_id": "alg_seq_001",
      "dimension": "RESOURCE",
      "level": "R2",
      "outcome": "SOLVED",
      "intervention_count": 2,
      "timestamp": ISODate("2026-03-30T10:00:00Z")
    },
    {
      "intervention_id": "int_20260330_002",
      "problem_id": "alg_seq_002",
      "dimension": "METACOGNITIVE",
      "level": "M2",
      "outcome": "SOLVED",
      "intervention_count": 1,
      "timestamp": ISODate("2026-03-30T10:15:00Z")
    }
  ],
  
  "topic_mastery": {
    "数列": {
      "topic": "数列",
      "mastery_level": 0.75,
      "last_practiced": ISODate("2026-03-30T10:15:00Z"),
      "practice_count": 12
    },
    "函数": {
      "topic": "函数",
      "mastery_level": 0.45,
      "last_practiced": ISODate("2026-03-29T15:00:00Z"),
      "practice_count": 8
    }
  },
  
  "created_at": ISODate("2026-03-30T10:00:00Z"),
  "updated_at": ISODate("2026-03-30T10:15:00Z"),
  "total_interventions": 42,
  "total_solved": 35,
  "total_escalation": 7,
  "ratio_trend": "stable",
  "trend_confidence": 0.75
}
```

### 7.2 索引设计

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

### 7.3 典型查询示例

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

## 8. Internal Service Class (内部服务类)

### 8.1 ProfileManager 类定义

```python
from typing import Optional, Dict, Any, List
from datetime import datetime
from .models import (
    StudentProfile,
    InterventionRecord,
    InterventionResult,
    RoutingHint,
    TrendAnalysis,
    Dimension,
    FinalStatus,
    DimensionBias,
    TrendLabel,
)


class ProfileManager:
    """
    学生画像管理器
    
    负责学生的 CRUD 操作和画像更新，是 Module 4 的核心服务类。
    其他模块通过此类的公开方法与 Module 4 交互。
    
    Attributes:
        profile_repo: 学生画像 MongoDB 仓储实例
        analytics: 趋势分析服务实例
        hint_generator: 路由提示生成器实例
    """
    
    def __init__(self, profile_repo: StudentProfileRepository):
        """
        初始化画像管理器
        
        Args:
            profile_repo: MongoDB 仓储实例
        """
        self.profile_repo = profile_repo
        self.analytics = ProfileAnalytics(profile_repo)
        self.hint_generator = RoutingHintGenerator(profile_repo)
    
    # ==================== 读操作 ====================
    
    async def get_profile(self, student_id: str) -> Optional[StudentProfile]:
        """
        获取学生完整画像
        
        如果学生不存在，返回 None
        
        Args:
            student_id: 学生唯一标识
        
        Returns:
            StudentProfile 或 None
        """
        return await self.profile_repo.find_by_student_id(student_id)
    
    async def upsert_profile(self, student_id: str) -> StudentProfile:
        """
        创建或更新学生画像
        
        新学生：初始化默认 dimension_ratio=0.5，created_at=当前时间
        老学生：直接返回现有 profile
        
        Args:
            student_id: 学生唯一标识
        
        Returns:
            StudentProfile
        """
        existing = await self.profile_repo.find_by_student_id(student_id)
        if existing:
            return existing
        
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
            ratio_trend=TrendLabel.STABLE,
            trend_confidence=0.0
        )
        
        return await self.profile_repo.save(new_profile)
    
    async def get_dimension_ratio(self, student_id: str) -> float:
        """
        快速获取 dimension_ratio
        
        新学生返回 0.5（均衡默认）
        
        Args:
            student_id: 学生唯一标识
        
        Returns:
            float: dimension_ratio 值
        """
        profile = await self.get_profile(student_id)
        if not profile:
            return 0.5
        return profile.dimension_ratio
    
    async def get_recent_problems(
        self, student_id: str, limit: int = 10
    ) -> List[str]:
        """
        获取学生最近 N 道题的 problem_id 列表
        
        用于 Module 3 的推荐过滤
        
        Args:
            student_id: 学生唯一标识
            limit: 返回数量上限
        
        Returns:
            problem_id 列表
        """
        profile = await self.get_profile(student_id)
        if not profile or not profile.intervention_history:
            return []
        
        recent = profile.intervention_history[-limit:]
        return [r.problem_id for r in recent]
    
    async def get_intervention_history(
        self,
        student_id: str,
        limit: int = 20,
        offset: int = 0,
        dimension: Optional[Dimension] = None,
        outcome: Optional[FinalStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> tuple[List[InterventionRecord], int]:
        """
        获取干预历史
        
        Args:
            student_id: 学生唯一标识
            limit: 返回数量上限
            offset: 分页偏移量
            dimension: 按维度筛选
            outcome: 按结果筛选
            start_date: 起始日期
            end_date: 结束日期
        
        Returns:
            (历史记录列表, 总数)
        """
        return await self.profile_repo.find_history(
            student_id=student_id,
            limit=limit,
            offset=offset,
            dimension=dimension,
            outcome=outcome,
            start_date=start_date,
            end_date=end_date,
        )
    
    # ==================== 写操作 ====================
    
    async def update_after_intervention(
        self,
        student_id: str,
        intervention_result: InterventionResult,
    ) -> StudentProfile:
        """
        【核心方法】每次 Module 2 干预结束后调用
        
        执行以下更新：
        1. 追加本次干预到 intervention_history
        2. 重新计算 dimension_ratio
        3. 更新 topic_mastery（如果提供 topic 信息）
        4. 更新 total_interventions / total_solved / total_escalation
        5. 更新 updated_at
        
        Args:
            student_id: 学生唯一标识
            intervention_result: 干预结果对象
        
        Returns:
            更新后的 StudentProfile
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
        
        # Step 3: 追加到 history（保留最近 50 条）
        profile.intervention_history.append(record)
        if len(profile.intervention_history) > 50:
            profile.intervention_history = profile.intervention_history[-50:]
        
        # Step 4: 重新计算 dimension_ratio
        previous_ratio = profile.dimension_ratio
        profile.dimension_ratio = self._compute_dimension_ratio(
            profile.intervention_history
        )
        
        # Step 5: 更新统计
        profile.total_interventions += 1
        if intervention_result.outcome == FinalStatus.SOLVED:
            profile.total_solved += 1
        elif intervention_result.outcome == FinalStatus.MAX_ESCALATION:
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
    
    async def add_dimension_record(
        self,
        student_id: str,
        dimension: Dimension,
        problem_id: str,
        level: str,
        outcome: FinalStatus,
        intervention_count: int = 1,
        topic: Optional[str] = None,
    ) -> tuple[StudentProfile, str]:
        """
        轻量级维度记录追加
        
        用于 Module 2 在获取到维度判定结果后直接记录，
        无需构造完整的 InterventionResult 对象。
        
        Args:
            student_id: 学生唯一标识
            dimension: 维度类型
            problem_id: 题目 ID
            level: 断点级别
            outcome: 干预结果
            intervention_count: 本题干预次数
            topic: 知识点名称
        
        Returns:
            (更新后的 profile, 生成的干预记录 ID)
        """
        intervention_id = f"int_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        result = InterventionResult(
            intervention_id=intervention_id,
            problem_id=problem_id,
            dimension=dimension,
            level=level,
            outcome=outcome,
            intervention_count=intervention_count,
            topic=topic,
        )
        
        profile = await self.update_after_intervention(student_id, result)
        return profile, intervention_id
    
    # ==================== 分析操作 ====================
    
    async def get_routing_hint(self, student_id: str) -> RoutingHint:
        """
        获取路由增强提示
        
        被 Module 2 的 DimensionRouter 和 SubTypeDecider 调用
        
        Args:
            student_id: 学生唯一标识
        
        Returns:
            RoutingHint 路由增强提示
        """
        return await self.hint_generator.generate(student_id)
    
    async def get_trend_analysis(
        self, student_id: str, window: int = 10
    ) -> TrendAnalysis:
        """
        获取维度比例趋势分析
        
        Args:
            student_id: 学生唯一标识
            window: 分析窗口大小
        
        Returns:
            TrendAnalysis 趋势分析结果
        """
        return await self.analytics.compute_ratio_trend(student_id, window)
    
    # ==================== 内部方法 ====================
    
    def _compute_dimension_ratio(
        self, intervention_history: List[InterventionRecord]
    ) -> float:
        """
        计算 R/(R+M) 比例
        
        冷启动策略：干预次数 < 3 时返回默认 0.5
        
        Args:
            intervention_history: 干预历史记录
        
        Returns:
            float: dimension_ratio
        """
        if not intervention_history:
            return 0.5
        
        if len(intervention_history) < 3:
            return 0.5
        
        r_count = sum(
            1 for r in intervention_history if r.dimension == Dimension.RESOURCE
        )
        total = len(intervention_history)
        
        ratio = r_count / total if total > 0 else 0.5
        
        return ratio
    
    def _compute_mastery(
        self, profile: StudentProfile, topic: str
    ) -> float:
        """
        计算知识点掌握度
        
        基于最近练习结果和历史成功率，使用指数平滑
        
        Args:
            profile: 学生画像
            topic: 知识点名称
        
        Returns:
            float: 掌握度 0.0-1.0
        """
        topic_records = [
            r for r in profile.intervention_history
            if r.topic == topic
        ][-10:]
        
        if not topic_records:
            return 0.5
        
        solved_count = sum(1 for r in topic_records if r.outcome == FinalStatus.SOLVED)
        success_rate = solved_count / len(topic_records)
        
        existing_mastery = profile.topic_mastery.get(topic)
        if existing_mastery:
            alpha = 0.3
            return alpha * success_rate + (1 - alpha) * existing_mastery.mastery_level
        
        return success_rate
```

### 8.2 ProfileAnalytics 类定义

```python
from typing import List
from datetime import datetime
from .models import (
    StudentProfile,
    TrendAnalysis,
    TrendLabel,
    Dimension,
)


class ProfileAnalytics:
    """
    学生画像趋势分析服务
    
    负责计算 dimension_ratio 的时间序列趋势。
    """
    
    def __init__(self, profile_repo: StudentProfileRepository):
        self.profile_repo = profile_repo
    
    async def compute_ratio_trend(
        self,
        student_id: str,
        window: int = 10,
    ) -> TrendAnalysis:
        """
        计算最近 window 次干预的 dimension_ratio 趋势
        
        采用简单线性回归计算斜率：
        - slope > 0.1：rising
        - slope < -0.1：falling
        - otherwise：stable
        
        置信度基于样本量：样本量达到 10 时置信度为 1.0
        
        Args:
            student_id: 学生唯一标识
            window: 窗口大小
        
        Returns:
            TrendAnalysis 趋势分析结果
        """
        profile = await self.profile_repo.find_by_student_id(student_id)
        
        if not profile or len(profile.intervention_history) < 3:
            return TrendAnalysis(
                student_id=student_id,
                current_ratio=0.5,
                window_ratio=0.5,
                slope=0.0,
                trend=TrendLabel.STABLE,
                confidence=0.0,
                window_size=window,
                sample_count=0,
                computed_at=datetime.utcnow(),
            )
        
        history = (
            profile.intervention_history[-window:]
            if len(profile.intervention_history) >= window
            else profile.intervention_history
        )
        
        values = [1 if r.dimension == Dimension.RESOURCE else 0 for r in history]
        
        n = len(values)
        if n < 2:
            slope = 0.0
        else:
            x_mean = (n - 1) / 2
            y_mean = sum(values) / n
            
            numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
            denominator = sum((i - x_mean) ** 2 for i in range(n))
            
            slope = numerator / denominator if denominator != 0 else 0.0
        
        current_ratio = profile.dimension_ratio
        window_ratio = sum(values) / n if n > 0 else 0.5
        
        if slope > 0.1:
            trend = TrendLabel.RISING
        elif slope < -0.1:
            trend = TrendLabel.FALLING
        else:
            trend = TrendLabel.STABLE
        
        confidence = min(n / 10.0, 1.0)
        
        return TrendAnalysis(
            student_id=student_id,
            current_ratio=current_ratio,
            window_ratio=window_ratio,
            slope=slope,
            trend=trend,
            confidence=confidence,
            window_size=window,
            sample_count=n,
            computed_at=datetime.utcnow(),
        )
```

### 8.3 RoutingHintGenerator 类定义

```python
from typing import List
from datetime import datetime
from .models import (
    StudentProfile,
    RoutingHint,
    DimensionBias,
    TrendLabel,
    Dimension,
    FinalStatus,
)


class RoutingHintGenerator:
    """
    路由增强提示生成器
    
    负责生成供 Module 2 使用的路由增强提示。
    """
    
    def __init__(self, profile_repo: StudentProfileRepository):
        self.profile_repo = profile_repo
    
    async def generate(self, student_id: str) -> RoutingHint:
        """
        生成路由增强提示
        
        Args:
            student_id: 学生唯一标识
        
        Returns:
            RoutingHint 路由增强提示
        """
        profile = await self.profile_repo.find_by_student_id(student_id)
        
        is_new_student = not profile or profile.total_interventions < 3
        
        if is_new_student:
            return RoutingHint(
                student_id=student_id,
                is_new_student=True,
                recent_dimension_bias=DimensionBias.BALANCED,
                dimension_ratio=0.5,
                ratio_trend=TrendLabel.STABLE,
                trend_confidence=0.0,
                weak_dimensions=[],
                recommended_dimension_hint="新学生，无明显偏好，默认使用RESOURCE维度开始",
                recent_intervention_summary="新学生，尚无干预历史",
                confidence=0.0,
            )
        
        ratio = profile.dimension_ratio
        
        if ratio > 0.65:
            bias = DimensionBias.R_DOMINANT
        elif ratio < 0.35:
            bias = DimensionBias.M_DOMINANT
        else:
            bias = DimensionBias.BALANCED
        
        trend_data = await self._compute_simple_trend(profile)
        
        weak_dims = self._analyze_weak_dimensions(profile.intervention_history)
        
        hint = self._generate_dimension_hint(bias)
        
        summary = self._generate_intervention_summary(profile.intervention_history)
        
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
            confidence=confidence,
        )
    
    def _analyze_weak_dimensions(
        self, intervention_history: List[InterventionRecord]
    ) -> List[str]:
        """
        分析干预历史，识别薄弱维度
        
        统计各维度级别的出现频率，返回高频项
        """
        if not intervention_history:
            return []
        
        level_counts = {}
        for record in intervention_history[-20:]:
            key = f"{record.dimension.value}_{record.level}"
            level_counts[key] = level_counts.get(key, 0) + 1
        
        sorted_levels = sorted(level_counts.items(), key=lambda x: x[1], reverse=True)
        
        weak = [level for level, count in sorted_levels if count > 1][:2]
        
        return weak
    
    def _generate_dimension_hint(self, bias: DimensionBias) -> str:
        """生成维度建议"""
        if bias == DimensionBias.R_DOMINANT:
            return "学生R型断点多，建议使用METACOGNITIVE维度尝试引导策略思考"
        elif bias == DimensionBias.M_DOMINANT:
            return "学生M型断点多，建议使用RESOURCE维度补充知识基础"
        else:
            return "学生维度均衡，可根据题目特征灵活选择"
    
    def _generate_intervention_summary(
        self, intervention_history: List[InterventionRecord]
    ) -> str:
        """生成最近干预摘要"""
        recent = intervention_history[-3:]
        if not recent:
            return "尚无干预历史"
        
        parts = []
        for r in recent:
            outcome_str = r.outcome.value
            parts.append(f"{r.level}({outcome_str})")
        
        return f"最近{len(recent)}次：" + ", ".join(parts)
    
    async def _compute_simple_trend(self, profile: StudentProfile) -> dict:
        """计算简单趋势"""
        if len(profile.intervention_history) < 3:
            return {"trend": TrendLabel.STABLE, "confidence": 0.0}
        
        recent = profile.intervention_history[-10:]
        values = [1 if r.dimension == Dimension.RESOURCE else 0 for r in recent]
        
        n = len(values)
        if n < 2:
            return {"trend": TrendLabel.STABLE, "confidence": 0.0}
        
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        
        numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0.0
        
        if slope > 0.1:
            trend = TrendLabel.RISING
        elif slope < -0.1:
            trend = TrendLabel.FALLING
        else:
            trend = TrendLabel.STABLE
        
        confidence = min(n / 10.0, 1.0)
        
        return {"trend": trend, "confidence": confidence}
    
    def _calculate_confidence(
        self, profile: StudentProfile, trend_data: dict
    ) -> float:
        """计算整体置信度"""
        base_confidence = min(profile.total_interventions / 20.0, 1.0)
        trend_weight = 0.3
        return base_confidence * (1 - trend_weight) + trend_data["confidence"] * trend_weight
```

---

## 附录 A: 字段说明表

### StudentProfile 主文档字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `student_id` | string | 学生唯一标识符 | `"student_001"` |
| `dimension_ratio` | float | R型断点比例，0.0-1.0 | `0.65` |
| `intervention_history` | InterventionRecord[] | 最近50次干预记录 | 详见子文档结构 |
| `topic_mastery` | dict | 知识点掌握度映射 | `{"数列": TopicMastery(...)}` |
| `created_at` | datetime | 画像创建时间 | `2026-03-30T10:00:00Z` |
| `updated_at` | datetime | 最后更新时间 | `2026-03-30T15:30:00Z` |
| `total_interventions` | int | 累计干预次数 | `42` |
| `total_solved` | int | 累计解决次数 | `35` |
| `total_escalation` | int | 累计达到最大干预次数 | `7` |
| `ratio_trend` | string | 维度比例趋势 | `"stable"` |
| `trend_confidence` | float | 趋势置信度 | `0.75` |

### InterventionRecord 子文档结构

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `intervention_id` | string | 干预ID | `"int_20260330_001"` |
| `problem_id` | string | 题目ID | `"alg_seq_001"` |
| `dimension` | string | 断点维度 | `"RESOURCE"` |
| `level` | string | 断点级别 | `"R2"` |
| `outcome` | string | 干预结果 | `"SOLVED"` |
| `intervention_count` | int | 本题干预次数 | `3` |
| `topic` | string | 知识点名称 | `"数列"` |
| `timestamp` | datetime | 干预时间 | `2026-03-30T10:00:00Z` |

### TopicMastery 子文档结构

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `topic` | string | 知识点名称 | `"数列"` |
| `mastery_level` | float | 掌握度 0.0-1.0 | `0.75` |
| `last_practiced` | datetime | 最近练习时间 | `2026-03-30T09:30:00Z` |
| `practice_count` | int | 练习次数 | `12` |

---

## 附录 B: 冷启动默认配置

新学生（干预次数 < 3）使用以下默认配置：

| 字段 | 默认值 |
|------|-------|
| `dimension_ratio` | 0.5（均衡） |
| `recent_dimension_bias` | balanced |
| `ratio_trend` | stable |
| `trend_confidence` | 0.0 |
| `recommended_dimension_hint` | "新学生，无明显偏好，默认使用RESOURCE维度开始" |
| `is_new_student` | true |
| `confidence` | 0.0 |

---

## 附录 C: 错误处理流程

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

(End of file)
