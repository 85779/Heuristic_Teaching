# Module 6 API 接口文档

## RAG 知识库系统

**版本**: 1.0.0  
**最后更新**: 2026-03-31  
**模块代号**: Socrates-Module-6-KnowledgeBase

---

## 1. API 概述

### 1.1 模块定位

Module 6 是 Socrates 系统中的检索增强生成（RAG）知识库模块，为整个 tutoring 系统提供结构化数学知识检索能力。在 Socrates 整体架构中，Module 6 属于基础设施层，为 Module 2（干预提示生成器）、Module 3（题目推荐引擎）、Module 5（教学策略选择器）提供知识检索服务。

Module 6 与其他模块的关系是服务与被服务的关系。Module 6 不主动推送任何内容，而是响应其他模块的检索请求。这种设计确保了模块之间的松耦合，便于独立演进和测试。

### 1.2 基础信息

| 项目     | 说明                     |
| -------- | ------------------------ |
| 基础 URL | `/api/v1/knowledge-base` |
| 服务端口 | 8000                     |
| 协议     | HTTP REST                |
| 数据格式 | JSON                     |
| 字符编码 | UTF-8                    |

### 1.3 认证方式

Module 6 采用与系统其他模块一致的 Bearer Token 认证机制。

**请求头格式**:

```
Authorization: Bearer <token>
Content-Type: application/json
```

内部服务调用可使用服务间认证令牌，外部调用需使用用户级访问令牌。

### 1.4 限流策略

| 限流维度     | 限制值      | 说明                                    |
| ------------ | ----------- | --------------------------------------- |
| 检索请求     | 100 次/分钟 | POST /retrieve 和 POST /enrich-hint     |
| 导入请求     | 10 次/分钟  | POST /ingest 和 POST /ingest/batch      |
| 查询请求     | 200 次/分钟 | GET /collection/stats 和 GET /documents |
| 单次最大返回 | 20 条       | top_k 参数上限                          |
| 最大批量导入 | 50 个文档   | /ingest/batch 单次上限                  |

超过限流阈值时，返回 HTTP 状态码 `429 Too Many Requests`，响应体包含重试建议时间。

### 1.5 通用响应格式

所有 API 响应均采用统一封装格式。

**成功响应**:

```json
{
  "success": true,
  "data": { ... },
  "timestamp": "2026-03-31T10:00:00Z"
}
```

**错误响应**:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述信息",
    "details": { ... }
  },
  "timestamp": "2026-03-31T10:00:00Z"
}
```

### 1.6 服务依赖

| 依赖服务      | 用途                     | 健康检查 |
| ------------- | ------------------------ | -------- |
| ChromaDB      | 向量数据库，存储知识片段 | 必需     |
| DashScope API | 文本嵌入向量生成         | 必需     |
| MongoDB       | 文档元数据存储           | 可选     |

---

## 2. API Endpoints

### 2.1 POST /knowledge-base/retrieve

**功能描述**: 检索与查询语句语义相关的知识片段。这是 Module 6 最核心的检索接口，支持按文档类型、年级、难度等维度进行精确过滤。

**请求头**:

```
Content-Type: application/json
Authorization: Bearer <token>
```

**请求体 (Request)**:

```json
{
  "query": "string (必需, 检索查询字符串，长度 1-500 字符)",
  "top_k": "integer (可选, 返回结果数量，默认 3，最大 20)",
  "filter": {
    "type": "string (可选, 文档类型: knowledge_point | method | concept | example | strategy)",
    "grade": "string (可选, 年级筛选，默认 high_school)",
    "difficulty": "string (可选, 难度等级: easy | medium | hard)",
    "keywords": "array<string> (可选, 关键词列表，用于辅助过滤)"
  },
  "include_metadata": "boolean (可选, 是否返回完整元数据，默认 true)"
}
```

**请求体示例**:

```json
{
  "query": "数学归纳法的原理",
  "top_k": 3,
  "filter": {
    "type": "knowledge_point",
    "grade": "high_school"
  }
}
```

**响应体 (Response)**:

```json
{
  "success": true,
  "chunks": [
    {
      "id": "string (知识片段唯一标识，格式: {type}_{序号})",
      "content": "string (知识片段完整文本内容)",
      "metadata": {
        "type": "string (文档类型)",
        "name": "string (知识片段名称)",
        "keywords": ["string (关键词列表)"],
        "grade": "string (年级)",
        "difficulty": "string (难度等级)",
        "related_kp": ["string (相关知识点列表)"],
        "related_methods": ["string (相关方法列表)"],
        "similarity": "float (余弦相似度分数，0.0-1.0)"
      }
    }
  ],
  "total": "integer (返回的知识片段总数)",
  "query_time_ms": "integer (检索耗时毫秒)",
  "version": "string (知识库版本号)"
}
```

**响应示例**:

```json
{
  "success": true,
  "chunks": [
    {
      "id": "kp_001",
      "content": "数学归纳法是证明与正整数有关的命题的一种方法。其基本步骤包括：第一，验证当 n=1 时命题成立，称为基本步；第二，假设当 n=k 时命题成立，证明当 n=k+1 时命题也成立，称为归纳步。由基本步和归纳步即可得出对所有正整数 n，命题都成立的结论。",
      "metadata": {
        "type": "knowledge_point",
        "name": "数学归纳法",
        "keywords": ["归纳法", "正整数", "证明", "数列"],
        "grade": "high_school",
        "difficulty": "medium",
        "related_kp": ["递推关系", "数列通项公式"],
        "related_methods": ["直接证明法", "反证法"],
        "similarity": 0.923
      }
    },
    {
      "id": "kp_015",
      "content": "数列的递推关系是指数列中从某一项起，每一项与其前一项或前几项之间的数量关系。常见的递推关系包括一阶递推和高阶递推。",
      "metadata": {
        "type": "knowledge_point",
        "name": "数列递推关系",
        "keywords": ["数列", "递推", "通项公式"],
        "grade": "high_school",
        "difficulty": "medium",
        "related_kp": ["数学归纳法", "等差数列"],
        "related_methods": ["归纳法", "迭代法"],
        "similarity": 0.856
      }
    },
    {
      "id": "ex_003",
      "content": "【例题】已知数列 {a_n} 满足 a_1=2, a_{n+1}=2a_n+1，求其通项公式。\n\n【分析】观察递推关系 a_{n+1}=2a_n+1，可以尝试用迭代法推导，或者构造新数列转化为等比数列。\n\n【解答】令 b_n=a_n+1，则 b_{n+1}=a_{n+1}+1=2a_n+2=2(a_n+1)=2b_n，且 b_1=3，故 b_n=3·2^{n-1}，从而 a_n=3·2^{n-1}-1。",
      "metadata": {
        "type": "example",
        "name": "数列递推公式求通项",
        "keywords": ["数列", "递推", "通项公式"],
        "grade": "high_school",
        "difficulty": "medium",
        "related_kp": ["数列", "递推关系", "数学归纳法"],
        "related_methods": ["迭代法", "构造法"],
        "similarity": 0.789
      }
    }
  ],
  "total": 3,
  "query_time_ms": 45,
  "version": "1.0.0"
}
```

**HTTP 状态码**:

- `200 OK`: 检索成功
- `400 Bad Request`: 请求参数格式错误或验证失败
- `401 Unauthorized`: 认证失败
- `429 Too Many Requests`: 请求频率超限
- `500 Internal Server Error`: ChromaDB 或 DashScope 服务异常
- `503 Service Unavailable`: 依赖服务不可用

---

### 2.2 POST /knowledge-base/ingest

**功能描述**: 导入单个 PDF 文档到知识库。文档经过文本提取、语义分块、向量嵌入后存储到 ChromaDB。

**请求头**:

```
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

**请求体 (Form Data)**:
| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| file | file | 是 | PDF 文件，最大 10MB |
| type | string | 是 | 文档类型: knowledge_point / method / concept / example / strategy |
| name | string | 是 | 文档名称，1-100 字符 |
| difficulty | string | 否 | 难度等级: easy / medium / hard |
| keywords | string | 否 | 关键词列表，逗号分隔 |
| grade | string | 否 | 年级，默认 high_school |

**请求体示例**:

```
file: [PDF 文件内容]
type: knowledge_point
name: 数学归纳法
difficulty: medium
keywords: 归纳法,正整数,证明,数列
grade: high_school
```

**响应体 (Response)**:

```json
{
  "success": true,
  "document_id": "string (文档唯一标识)",
  "chunks_created": "integer (创建的知识片段数量)",
  "content_hash": "string (文档内容 SHA256 哈希值，用于幂等性验证)",
  "processing_time_ms": "integer (处理耗时毫秒)",
  "version": "string (知识库版本号)"
}
```

**响应示例**:

```json
{
  "success": true,
  "document_id": "kp_001",
  "chunks_created": 5,
  "content_hash": "a1b2c3d4e5f6...",
  "processing_time_ms": 2340,
  "version": "1.0.0"
}
```

**HTTP 状态码**:

- `201 Created`: 文档导入成功
- `400 Bad Request`: 参数格式错误或文件类型不支持
- `401 Unauthorized`: 认证失败
- `409 Conflict`: 文档内容哈希已存在，执行更新而非创建
- `413 Payload Too Large`: 文件大小超过限制
- `415 Unsupported Media Type`: 不支持的文件类型
- `429 Too Many Requests`: 请求频率超限
- `500 Internal Server Error`: 处理失败

**幂等性说明**: 如果导入的文档内容哈希值与知识库中已有文档相同，系统执行更新操作，保留原文档 ID 并更新内容和向量，而非重复创建。

---

### 2.3 POST /knowledge-base/ingest/batch

**功能描述**: 批量导入多个文档到知识库。适用于初始化知识库或定期批量更新场景。

**请求头**:

```
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

**请求体 (Form Data)**:
| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| files | file[] | 是 | PDF 文件列表，最多 50 个，总大小不超过 100MB |
| type | string | 是 | 文档类型，适用于所有文件 |
| difficulty | string | 否 | 默认难度等级 |
| grade | string | 否 | 默认年级，默认 high_school |

**响应体 (Response)**:

```json
{
  "success": true,
  "total_files": "integer (提交的文件总数)",
  "succeeded": "integer (成功导入的数量)",
  "failed": "integer (导入失败的数量)",
  "results": [
    {
      "file_name": "string (文件名)",
      "document_id": "string (文档唯一标识，失败时为 null)",
      "status": "string (success | failed | skipped)",
      "chunks_created": "integer (创建的知识片段数量)",
      "error": "string (失败原因，success 时为 null)"
    }
  ],
  "processing_time_ms": "integer (总处理耗时毫秒)",
  "version": "string (知识库版本号)"
}
```

**响应示例**:

```json
{
  "success": true,
  "total_files": 3,
  "succeeded": 2,
  "failed": 1,
  "results": [
    {
      "file_name": "数学归纳法.pdf",
      "document_id": "kp_001",
      "status": "success",
      "chunks_created": 5,
      "error": null
    },
    {
      "file_name": "递推关系.pdf",
      "document_id": "kp_002",
      "status": "success",
      "chunks_created": 4,
      "error": null
    },
    {
      "file_name": "损坏文件.pdf",
      "document_id": null,
      "status": "failed",
      "chunks_created": 0,
      "error": "PDF 解析失败：文件损坏或加密"
    }
  ],
  "processing_time_ms": 15670,
  "version": "1.0.0"
}
```

**HTTP 状态码**:

- `200 OK`: 批量处理完成（部分成功也算完成）
- `400 Bad Request`: 参数格式错误
- `401 Unauthorized`: 认证失败
- `413 Payload Too Large`: 总文件大小超过限制
- `429 Too Many Requests`: 请求频率超限
- `500 Internal Server Error`: 批量处理异常

---

### 2.4 DELETE /knowledge-base/collection

**功能描述**: 清空知识库 collection 中的所有文档。此操作不可逆，通常仅用于知识库重建或完全刷新场景。

**请求头**:

```
Authorization: Bearer <token>
```

**请求体 (Request)**:

```json
{
  "confirm": "boolean (必需, 必须设为 true 确认删除)",
  "reason": "string (可选, 删除原因说明)"
}
```

**请求体示例**:

```json
{
  "confirm": true,
  "reason": "知识库版本升级，需要重新导入"
}
```

**响应体 (Response)**:

```json
{
  "success": true,
  "deleted_count": "integer (删除的文档数量)",
  "deleted_chunks": "integer (删除的知识片段数量)",
  "collection_name": "string (被清空的 collection 名称)",
  "operation_id": "string (操作唯一标识，用于审计)",
  "executed_at": "ISO8601 datetime"
}
```

**响应示例**:

```json
{
  "success": true,
  "deleted_count": 45,
  "deleted_chunks": 312,
  "collection_name": "math_knowledge",
  "operation_id": "del_20260331_abc123",
  "executed_at": "2026-03-31T10:00:00Z"
}
```

**HTTP 状态码**:

- `200 OK`: 删除成功
- `400 Bad Request`: confirm 参数未设为 true
- `401 Unauthorized`: 认证失败
- `403 Forbidden`: 无权限执行此操作
- `500 Internal Server Error`: 删除操作失败

**安全说明**: 此接口需要管理员权限。建议在生产环境中仅允许运维人员调用，并记录完整的审计日志。

---

### 2.5 GET /knowledge-base/collection/stats

**功能描述**: 获取知识库的统计信息，包括文档总数、分类型统计、存储空间使用等。

**请求头**:

```
Authorization: Bearer <token>
```

**响应体 (Response)**:

```json
{
  "success": true,
  "stats": {
    "collection_name": "string (collection 名称)",
    "total_documents": "integer (文档总数)",
    "total_chunks": "integer (知识片段总数)",
    "by_type": {
      "knowledge_point": "integer (知识点类型文档数)",
      "method": "integer (方法类型文档数)",
      "concept": "integer (概念类型文档数)",
      "example": "integer (例题类型文档数)",
      "strategy": "integer (策略类型文档数)"
    },
    "by_difficulty": {
      "easy": "integer (简单难度文档数)",
      "medium": "integer (中等难度文档数)",
      "hard": "integer (困难难度文档数)"
    },
    "storage": {
      "persist_directory": "string (持久化目录路径)",
      "estimated_size_mb": "float (估算存储大小 MB)",
      "embedding_dimension": "integer (向量维度)"
    },
    "version": "string (知识库版本)",
    "last_updated": "ISO8601 datetime (最后更新时间)"
  }
}
```

**响应示例**:

```json
{
  "success": true,
  "stats": {
    "collection_name": "math_knowledge",
    "total_documents": 45,
    "total_chunks": 312,
    "by_type": {
      "knowledge_point": 20,
      "method": 8,
      "concept": 5,
      "example": 10,
      "strategy": 2
    },
    "by_difficulty": {
      "easy": 12,
      "medium": 25,
      "hard": 8
    },
    "storage": {
      "persist_directory": "./data/chromadb",
      "estimated_size_mb": 128.5,
      "embedding_dimension": 1024
    },
    "version": "1.0.0",
    "last_updated": "2026-03-30T23:00:00Z"
  }
}
```

**HTTP 状态码**:

- `200 OK`: 获取成功
- `401 Unauthorized`: 认证失败
- `500 Internal Server Error`: 服务异常

---

### 2.6 GET /knowledge-base/health

**功能描述**: 健康检查接口，返回知识库系统各依赖服务的连接状态和整体可用性。

**请求头**:

```
Authorization: Bearer <token> (可选)
```

**响应体 (Response)**:

```json
{
  "success": true,
  "status": "string (整体状态: healthy | degraded | unhealthy)",
  "timestamp": "ISO8601 datetime",
  "services": {
    "chromadb": {
      "connected": "boolean (是否已连接)",
      "collection_exists": "boolean (collection 是否存在)",
      "latency_ms": "integer (最近一次请求延迟)",
      "error": "string (可选, 连接错误信息)"
    },
    "dashscope": {
      "available": "boolean (服务是否可用)",
      "model": "string (当前使用的 embedding 模型)",
      "latency_ms": "integer (最近一次请求延迟)",
      "error": "string (可选, 错误信息)"
    },
    "mongodb": {
      "connected": "boolean (是否已连接)",
      "latency_ms": "integer (可选, 最近一次请求延迟)",
      "error": "string (可选, 连接错误信息)"
    }
  },
  "performance_metrics": {
    "avg_retrieval_latency_ms": "float (平均检索延迟)",
    "p50_latency_ms": "float",
    "p95_latency_ms": "float",
    "requests_per_minute": "float",
    "error_rate": "float (错误率)"
  },
  "uptime_seconds": "integer (服务启动以来的秒数)",
  "version": "string (模块版本号)"
}
```

**响应示例**:

```json
{
  "success": true,
  "status": "healthy",
  "timestamp": "2026-03-31T10:00:00Z",
  "services": {
    "chromadb": {
      "connected": true,
      "collection_exists": true,
      "latency_ms": 12
    },
    "dashscope": {
      "available": true,
      "model": "text-embedding-v1",
      "latency_ms": 85
    },
    "mongodb": {
      "connected": true,
      "latency_ms": 8
    }
  },
  "performance_metrics": {
    "avg_retrieval_latency_ms": 45.2,
    "p50_latency_ms": 38.0,
    "p95_latency_ms": 120.5,
    "requests_per_minute": 25.3,
    "error_rate": 0.001
  },
  "uptime_seconds": 86400,
  "version": "1.0.0"
}
```

**HTTP 状态码**:

- `200 OK`: 健康检查完成（即使部分服务不健康也返回 200）
- `503 Service Unavailable`: 所有核心服务均不可用

---

### 2.7 POST /knowledge-base/enrich-hint

**功能描述**: Module 2 专用接口，将知识检索与提示增强一体化处理。此接口接收提示模板和学生输入，返回注入知识内容后的增强提示。

**使用场景**: 当 Module 2 在学生解题遇到困难时需要生成实时干预提示，此接口将检索与增强两个步骤合二为一，减少网络开销并确保提示与检索结果的上下文连贯性。

**请求头**:

```
Content-Type: application/json
Authorization: Bearer <token>
```

**请求体 (Request)**:

```json
{
  "hint_template": "string (必需, 提示模板，包含占位符 {knowledge} 和 {student_state})",
  "student_input": "string (必需, 学生当前输入或问题描述)",
  "expected_step": "string (可选, 期望的下一步骤描述)",
  "problem_kp": "array<string> (可选, 题目涉及的知识点列表)",
  "breakpoint_type": "string (可选, 断点类型: MISSING_STEP | WRONG_DIRECTION | INCOMPLETE_STEP | STUCK)",
  "difficulty": "string (可选, 题目难度: easy | medium | hard)",
  "top_k": "integer (可选, 检索的知识片段数量，默认 3，最大 5)"
}
```

**请求体示例**:

```json
{
  "hint_template": "【相关知识点】\n{knowledge}\n\n【学生当前】\n{student_state}\n\n【提示】\n请参考上述知识点，思考如何解决当前问题。",
  "student_input": "学生说：归纳构造怎么想",
  "expected_step": "构造归纳假设",
  "problem_kp": ["数学归纳法", "数列"],
  "breakpoint_type": "MISSING_STEP",
  "difficulty": "medium",
  "top_k": 3
}
```

**响应体 (Response)**:

```json
{
  "success": true,
  "enriched_hint": "string (注入知识后的完整提示文本)",
  "chunks_used": "integer (实际使用的知识片段数量)",
  "chunks": [
    {
      "id": "string",
      "content": "string (知识片段内容摘要)",
      "type": "string (文档类型)",
      "name": "string (知识片段名称)",
      "similarity": "float (相似度分数)"
    }
  ],
  "retrieval_time_ms": "integer (检索阶段耗时毫秒)",
  "total_time_ms": "integer (端到端总耗时毫秒)",
  "version": "string (知识库版本号)"
}
```

**响应示例**:

```json
{
  "success": true,
  "enriched_hint": "【相关知识点】\n数学归纳法：证明与正整数有关的命题的一种方法。基本步验证 n=1 时成立，归纳步假设 n=k 时成立并证明 n=k+1 时也成立。\n\n数列递推关系：数列中从某一项起，每一项与其前一项或前几项之间的数量关系。\n\n【学生当前】\n学生在构造归纳假设时遇到困难，不清楚如何从 n=k 的假设推导到 n=k+1。\n\n【提示】\n请参考上述知识点，思考如何解决当前问题。",
  "chunks_used": 3,
  "chunks": [
    {
      "id": "kp_001",
      "content": "数学归纳法是证明与正整数有关的命题的一种方法...",
      "type": "knowledge_point",
      "name": "数学归纳法",
      "similarity": 0.923
    },
    {
      "id": "kp_015",
      "content": "数列的递推关系是指数列中从某一项起...",
      "type": "knowledge_point",
      "name": "数列递推关系",
      "similarity": 0.856
    },
    {
      "id": "ex_003",
      "content": "【例题】已知数列 {a_n} 满足 a_1=2...",
      "type": "example",
      "name": "数列递推公式求通项",
      "similarity": 0.789
    }
  ],
  "retrieval_time_ms": 120,
  "total_time_ms": 890,
  "version": "1.0.0"
}
```

**HTTP 状态码**:

- `200 OK`: 处理成功
- `400 Bad Request`: 请求参数格式错误
- `401 Unauthorized`: 认证失败
- `429 Too Many Requests`: 请求频率超限
- `500 Internal Server Error`: 检索或增强处理失败
- `503 Service Unavailable`: 依赖服务不可用

---

### 2.8 GET /knowledge-base/documents

**功能描述**: 列出知识库中的文档，支持分页和按类型筛选。

**请求头**:

```
Authorization: Bearer <token>
```

**查询参数 (Query Parameters)**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| type | string | 否 | 按文档类型筛选 |
| difficulty | string | 否 | 按难度筛选 |
| grade | string | 否 | 按年级筛选，默认 high_school |
| limit | integer | 否 | 返回数量，默认 20，最大 100 |
| offset | integer | 否 | 分页偏移量，默认 0 |
| search | string | 否 | 按名称或关键词搜索 |

**响应体 (Response)**:

```json
{
  "success": true,
  "documents": [
    {
      "document_id": "string (文档唯一标识)",
      "name": "string (文档名称)",
      "type": "string (文档类型)",
      "difficulty": "string (难度等级)",
      "grade": "string (年级)",
      "keywords": ["string (关键词列表)"],
      "chunks_count": "integer (包含的知识片段数量)",
      "content_hash": "string (内容哈希值)",
      "created_at": "ISO8601 datetime",
      "updated_at": "ISO8601 datetime"
    }
  ],
  "total": "integer (符合条件的文档总数)",
  "limit": "integer",
  "offset": "integer"
}
```

**响应示例**:

```json
{
  "success": true,
  "documents": [
    {
      "document_id": "kp_001",
      "name": "数学归纳法",
      "type": "knowledge_point",
      "difficulty": "medium",
      "grade": "high_school",
      "keywords": ["归纳法", "正整数", "证明", "数列"],
      "chunks_count": 5,
      "content_hash": "a1b2c3d4e5f6...",
      "created_at": "2026-03-15T08:00:00Z",
      "updated_at": "2026-03-15T08:00:00Z"
    },
    {
      "document_id": "kp_002",
      "name": "数列递推关系",
      "type": "knowledge_point",
      "difficulty": "medium",
      "grade": "high_school",
      "keywords": ["数列", "递推", "通项公式"],
      "chunks_count": 4,
      "content_hash": "b2c3d4e5f6g7...",
      "created_at": "2026-03-15T09:00:00Z",
      "updated_at": "2026-03-15T09:00:00Z"
    }
  ],
  "total": 45,
  "limit": 20,
  "offset": 0
}
```

**HTTP 状态码**:

- `200 OK`: 查询成功
- `400 Bad Request`: 查询参数格式错误
- `401 Unauthorized`: 认证失败
- `500 Internal Server Error`: 服务异常

---

## 3. 数据模型

### 3.1 TypeScript 类型定义

```typescript
// 文档类型枚举
type DocumentType =
  | "knowledge_point" // 知识点
  | "method" // 解题方法
  | "concept" // 数学概念
  | "example" // 典型例题
  | "strategy"; // 教学策略

// 难度等级枚举
type DifficultyLevel =
  | "easy" // 简单
  | "medium" // 中等
  | "hard"; // 困难

// 知识片段元数据
interface ChunkMetadata {
  type: DocumentType;
  name: string;
  keywords: string[];
  grade: string;
  difficulty: DifficultyLevel;
  related_kp?: string[];
  related_methods?: string[];
  similarity?: number;
}

// 知识片段
interface KnowledgeChunk {
  id: string;
  content: string;
  metadata: ChunkMetadata;
}

// 检索请求
interface RetrieveRequest {
  query: string;
  top_k?: number;
  filter?: {
    type?: DocumentType;
    grade?: string;
    difficulty?: DifficultyLevel;
    keywords?: string[];
  };
  include_metadata?: boolean;
}

// 检索响应
interface RetrieveResponse {
  success: boolean;
  chunks: KnowledgeChunk[];
  total: number;
  query_time_ms: number;
  version: string;
}

// 导入请求 (Form Data)
interface IngestRequest {
  file: File;
  type: DocumentType;
  name: string;
  difficulty?: DifficultyLevel;
  keywords?: string;
  grade?: string;
}

// 导入响应
interface IngestResponse {
  success: boolean;
  document_id: string;
  chunks_created: number;
  content_hash: string;
  processing_time_ms: number;
  version: string;
}

// 批量导入响应
interface BatchIngestResponse {
  success: boolean;
  total_files: number;
  succeeded: number;
  failed: number;
  results: Array<{
    file_name: string;
    document_id: string | null;
    status: "success" | "failed" | "skipped";
    chunks_created: number;
    error: string | null;
  }>;
  processing_time_ms: number;
  version: string;
}

// 增强提示请求
interface EnrichHintRequest {
  hint_template: string;
  student_input: string;
  expected_step?: string;
  problem_kp?: string[];
  breakpoint_type?: string;
  difficulty?: DifficultyLevel;
  top_k?: number;
}

// 增强提示响应
interface EnrichHintResponse {
  success: boolean;
  enriched_hint: string;
  chunks_used: number;
  chunks: Array<{
    id: string;
    content: string;
    type: DocumentType;
    name: string;
    similarity: number;
  }>;
  retrieval_time_ms: number;
  total_time_ms: number;
  version: string;
}

// 文档列表项
interface DocumentItem {
  document_id: string;
  name: string;
  type: DocumentType;
  difficulty: DifficultyLevel;
  grade: string;
  keywords: string[];
  chunks_count: number;
  content_hash: string;
  created_at: string;
  updated_at: string;
}

// 文档列表响应
interface DocumentListResponse {
  success: boolean;
  documents: DocumentItem[];
  total: number;
  limit: number;
  offset: number;
}

// 知识库统计
interface CollectionStats {
  collection_name: string;
  total_documents: number;
  total_chunks: number;
  by_type: Record<DocumentType, number>;
  by_difficulty: Record<DifficultyLevel, number>;
  storage: {
    persist_directory: string;
    estimated_size_mb: number;
    embedding_dimension: number;
  };
  version: string;
  last_updated: string;
}

// 健康状态
interface HealthStatus {
  status: "healthy" | "degraded" | "unhealthy";
  timestamp: string;
  services: {
    chromadb: {
      connected: boolean;
      collection_exists: boolean;
      latency_ms?: number;
      error?: string;
    };
    dashscope: {
      available: boolean;
      model: string;
      latency_ms?: number;
      error?: string;
    };
    mongodb?: {
      connected: boolean;
      latency_ms?: number;
      error?: string;
    };
  };
  performance_metrics: {
    avg_retrieval_latency_ms: number;
    p50_latency_ms: number;
    p95_latency_ms: number;
    requests_per_minute: number;
    error_rate: number;
  };
  uptime_seconds: number;
  version: string;
}
```

### 3.2 Pydantic 数据模型 (Python)

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    KNOWLEDGE_POINT = "knowledge_point"
    METHOD = "method"
    CONCEPT = "concept"
    EXAMPLE = "example"
    STRATEGY = "strategy"


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ChunkMetadata(BaseModel):
    type: DocumentType
    name: str
    keywords: List[str] = []
    grade: str = "high_school"
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    related_kp: List[str] = []
    related_methods: List[str] = []
    similarity: Optional[float] = None


class KnowledgeChunk(BaseModel):
    id: str
    content: str
    metadata: ChunkMetadata


class RetrieveFilter(BaseModel):
    type: Optional[DocumentType] = None
    grade: Optional[str] = "high_school"
    difficulty: Optional[DifficultyLevel] = None
    keywords: Optional[List[str]] = None


class RetrieveRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=3, ge=1, le=20)
    filter: Optional[RetrieveFilter] = None
    include_metadata: bool = True


class RetrieveResponse(BaseModel):
    success: bool
    chunks: List[KnowledgeChunk]
    total: int
    query_time_ms: int
    version: str


class IngestRequest(BaseModel):
    type: DocumentType
    name: str = Field(..., min_length=1, max_length=100)
    difficulty: Optional[DifficultyLevel] = None
    keywords: Optional[str] = None
    grade: str = "high_school"


class IngestResponse(BaseModel):
    success: bool
    document_id: str
    chunks_created: int
    content_hash: str
    processing_time_ms: int
    version: str


class BatchIngestResult(BaseModel):
    file_name: str
    document_id: Optional[str] = None
    status: Literal["success", "failed", "skipped"]
    chunks_created: int = 0
    error: Optional[str] = None


class BatchIngestResponse(BaseModel):
    success: bool
    total_files: int
    succeeded: int
    failed: int
    results: List[BatchIngestResult]
    processing_time_ms: int
    version: str


class DeleteCollectionRequest(BaseModel):
    confirm: bool
    reason: Optional[str] = None


class DeleteCollectionResponse(BaseModel):
    success: bool
    deleted_count: int
    deleted_chunks: int
    collection_name: str
    operation_id: str
    executed_at: datetime


class CollectionStats(BaseModel):
    collection_name: str
    total_documents: int
    total_chunks: int
    by_type: Dict[DocumentType, int]
    by_difficulty: Dict[DifficultyLevel, int]
    storage: Dict[str, Any]
    version: str
    last_updated: datetime


class DocumentItem(BaseModel):
    document_id: str
    name: str
    type: DocumentType
    difficulty: DifficultyLevel
    grade: str
    keywords: List[str]
    chunks_count: int
    content_hash: str
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    success: bool
    documents: List[DocumentItem]
    total: int
    limit: int
    offset: int


class EnrichHintRequest(BaseModel):
    hint_template: str
    student_input: str
    expected_step: Optional[str] = None
    problem_kp: Optional[List[str]] = None
    breakpoint_type: Optional[str] = None
    difficulty: Optional[DifficultyLevel] = None
    top_k: int = Field(default=3, ge=1, le=5)


class EnrichHintChunk(BaseModel):
    id: str
    content: str
    type: DocumentType
    name: str
    similarity: float


class EnrichHintResponse(BaseModel):
    success: bool
    enriched_hint: str
    chunks_used: int
    chunks: List[EnrichHintChunk]
    retrieval_time_ms: int
    total_time_ms: int
    version: str


class ServiceHealth(BaseModel):
    connected: bool
    latency_ms: Optional[int] = None
    error: Optional[str] = None


class DashScopeHealth(ServiceHealth):
    available: bool = True
    model: str = "text-embedding-v1"


class ChromaDBHealth(ServiceHealth):
    collection_exists: bool = False


class PerformanceMetrics(BaseModel):
    avg_retrieval_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    requests_per_minute: float
    error_rate: float


class HealthStatus(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    timestamp: datetime
    services: Dict[str, Any]
    performance_metrics: PerformanceMetrics
    uptime_seconds: int
    version: str
```

---

## 4. 错误码

### 4.1 错误码定义

| 错误码                   | HTTP 状态码 | 说明             | 可能原因                                 |
| ------------------------ | ----------- | ---------------- | ---------------------------------------- |
| `INVALID_REQUEST`        | 400         | 请求参数格式错误 | 必填字段缺失、类型不匹配、超出范围       |
| `VALIDATION_ERROR`       | 400         | 数据验证失败     | 字段值不符合约束条件                     |
| `UNAUTHORIZED`           | 401         | 认证失败         | Token 无效、过期或缺失                   |
| `FORBIDDEN`              | 403         | 权限不足         | 需要管理员权限的操作                     |
| `NOT_FOUND`              | 404         | 资源不存在       | 文档 ID 或会话 ID 不存在                 |
| `CONFLICT`               | 409         | 资源冲突         | 文档内容哈希已存在                       |
| `PAYLOAD_TOO_LARGE`      | 413         | 请求体过大       | 文件大小超过 10MB 或批量总大小超过 100MB |
| `UNSUPPORTED_MEDIA_TYPE` | 415         | 不支持的文件类型 | 仅支持 PDF 文件                          |
| `RATE_LIMIT_EXCEEDED`    | 429         | 请求频率超限     | 超过每分钟允许的请求数                   |
| `INTERNAL_ERROR`         | 500         | 内部服务错误     | ChromaDB 或 DashScope 服务异常           |
| `SERVICE_UNAVAILABLE`    | 503         | 依赖服务不可用   | ChromaDB 连接失败或 DashScope API 不可用 |
| `TIMEOUT`                | 504         | 请求超时         | 检索或导入操作超过超时限制               |

### 4.2 错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述信息",
    "details": {
      "field": "具体字段名",
      "reason": "详细原因说明"
    }
  },
  "timestamp": "2026-03-31T10:00:00Z"
}
```

### 4.3 错误响应示例

**参数验证失败**:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "top_k 参数超出允许范围",
    "details": {
      "field": "top_k",
      "reason": "top_k 必须大于 0 且小于等于 20"
    }
  },
  "timestamp": "2026-03-31T10:00:00Z"
}
```

**认证失败**:

```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "访问令牌无效或已过期",
    "details": {
      "reason": "Token 已过期，请重新获取"
    }
  },
  "timestamp": "2026-03-31T10:00:00Z"
}
```

**限流**:

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "请求频率超出限制",
    "details": {
      "limit": "100 次/分钟",
      "retry_after_seconds": 30
    }
  },
  "timestamp": "2026-03-31T10:00:00Z"
}
```

**服务不可用**:

```json
{
  "success": false,
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "ChromaDB 服务暂时不可用",
    "details": {
      "service": "chromadb",
      "reason": "连接被拒绝，请检查服务状态"
    }
  },
  "timestamp": "2026-03-31T10:00:00Z"
}
```

---

## 5. Module 集成说明

### 5.1 Module 2 集成（干预提示生成器）

#### 集成架构

Module 2 通过调用 Module 6 的 `/knowledge-base/enrich-hint` 接口，在生成干预提示时动态检索相关知识并注入到提示模板中。

#### 调用流程

```
Module 2 干预流程
    │
    ├── 检测到学生解题断点
    │
    ├── 构造 enrich-hint 请求
    │   ├── hint_template: 当前提示模板
    │   ├── student_input: 学生当前输入
    │   ├── problem_kp: 题目涉及的知识点
    │   └── difficulty: 题目难度
    │
    ├── 调用 POST /api/v1/knowledge-base/enrich-hint
    │
    ├── 接收增强后的提示
    │   └── enriched_hint: 已注入知识的提示文本
    │
    └── 向学生展示增强提示
```

#### 调用示例

**Python 调用代码**:

```python
import httpx

async def generate_enriched_hint(
    hint_template: str,
    student_input: str,
    problem_kp: list[str],
    difficulty: str = "medium"
) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/knowledge-base/enrich-hint",
            json={
                "hint_template": hint_template,
                "student_input": student_input,
                "problem_kp": problem_kp,
                "difficulty": difficulty,
                "top_k": 3
            },
            headers={"Authorization": "Bearer <token>"},
            timeout=10.0
        )
        result = response.json()
        return result["enriched_hint"]
```

**使用场景示例**:

场景：学生在证明数列通项公式时遇到困难，使用数学归纳法但不清楚如何构造归纳假设。

Module 2 构造的请求：

```json
{
  "hint_template": "【相关知识点】\n{knowledge}\n\n【提示】\n{student_state}",
  "student_input": "学生问：归纳假设应该怎么构造？我知道要假设 n=k 时成立，但不知道怎么用到 n=k+1 上。",
  "problem_kp": ["数学归纳法", "数列递推关系", "数列通项公式"],
  "breakpoint_type": "MISSING_STEP",
  "difficulty": "medium",
  "top_k": 3
}
```

Module 6 返回的增强提示：

```
【相关知识点】

数学归纳法：证明与正整数有关的命题的一种方法。基本步骤包括：
1. 基本步：验证当 n=1 时命题成立
2. 归纳步：假设当 n=k 时命题成立，证明当 n=k+1 时命题也成立

数列递推关系：数列中每一项与其前一项或前几项之间的数量关系。

【提示】

学生在构造归纳假设时遇到困难。对于数列递推关系 a_{n+1}=2a_n+1，证明 n=k+1 时成立的关键是：
利用归纳假设中 n=k 时的等式关系，将 a_{n+1} 用 a_n 表示，再代入递推公式。
```

#### 降级策略

当 Module 6 服务不可用时，Module 2 应回退到不依赖知识检索的标准提示生成流程：

```python
async def generate_hint_with_fallback(
    hint_template: str,
    student_input: str,
    problem_kp: list[str]
) -> str:
    try:
        return await generate_enriched_hint(
            hint_template, student_input, problem_kp
        )
    except KGServiceError:
        # 降级：使用标准提示模板
        return build_standard_hint(hint_template, student_input)
```

### 5.2 Module 3 集成（题目推荐引擎）

#### 集成架构

Module 3 在 Phase 2 中与 Module 6 集成，使用检索能力获取知识点的关联关系，用于优化推荐策略和丰富推荐内容。

#### 调用场景

**场景一：获取知识点的关联信息**

当 Module 3 需要获取某知识点的关联知识点列表时，调用 `/knowledge-base/retrieve` 接口：

```python
async def get_related_knowledge(
    knowledge_point: str,
    top_k: int = 5
) -> list[dict]:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/knowledge-base/retrieve",
            json={
                "query": f"知识点 {knowledge_point} 相关知识",
                "top_k": top_k,
                "filter": {
                    "type": "knowledge_point"
                }
            },
            headers={"Authorization": "Bearer <token>"},
            timeout=5.0
        )
        result = response.json()
        return result["chunks"]
```

**场景二：获取相关例题信息**

当 Module 3 准备推荐某道具体题目的参考解法时：

```python
async def get_reference_examples(
    topic: str,
    difficulty: str
) -> list[dict]:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/knowledge-base/retrieve",
            json={
                "query": f"题目 {topic} 解题方法参考",
                "top_k": 2,
                "filter": {
                    "type": "example",
                    "difficulty": difficulty
                }
            },
            headers={"Authorization": "Bearer <token>"},
            timeout=5.0
        )
        result = response.json()
        return result["chunks"]
```

#### 集成点

Module 3 的集成点位于 `RecommendationService` 类的候选题检索阶段。在检索候选题之前，先调用 Module 6 获取相关的知识点和例题信息，用于后续的打分和排序。

### 5.3 Module 5 集成（教学策略选择器）

#### 集成架构

Module 5 在 Phase 2 中与 Module 6 集成，使用检索能力获取与当前教学内容相关的教学策略知识。

#### 调用场景

```python
async def get_teaching_strategies(
    topic: str,
    learning_style: str,
    top_k: int = 3
) -> list[dict]:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/knowledge-base/retrieve",
            json={
                "query": f"针对{learning_style}学习者讲授{topic}的教学策略",
                "top_k": top_k,
                "filter": {
                    "type": "strategy"
                }
            },
            headers={"Authorization": "Bearer <token>"},
            timeout=5.0
        )
        result = response.json()
        return result["chunks"]
```

---

## 6. ChromaDB 文档示例

### 6.1 Collection 配置

```python
# ChromaDB 配置
PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chromadb")
COLLECTION_NAME = "math_knowledge"
EMBEDDING_DIMENSION = 1024  # qwen-embeddings-v1 输出维度
```

### 6.2 文档结构示例

**知识点类型文档 (knowledge_point)**:

```json
{
  "id": "kp_001",
  "embedding": [0.123, -0.456, 0.789, ...],
  "document": "数学归纳法是证明与正整数有关的命题的一种方法。其基本步骤包括：第一，验证当 n=1 时命题成立，称为基本步；第二，假设当 n=k 时命题成立，证明当 n=k+1 时命题也成立，称为归纳步。由基本步和归纳步即可得出对所有正整数 n，命题都成立的结论。",
  "metadata": {
    "type": "knowledge_point",
    "name": "数学归纳法",
    "keywords": ["归纳法", "正整数", "证明", "数列"],
    "grade": "high_school",
    "difficulty": "medium",
    "related_kp": ["递推关系", "数列通项公式"],
    "related_methods": ["直接证明法", "反证法"]
  }
}
```

**方法类型文档 (method)**:

```json
{
  "id": "mt_001",
  "embedding": [0.234, -0.567, 0.890, ...],
  "document": "换元法是一种常用的代数变形技巧。其核心思想是将复杂的表达式中的某个部分用一个新变量替换，使问题简化。换元法的基本步骤是：1. 选择合适的代换表达式；2. 将原变量用新变量表示；3. 代入原式进行变形；4. 求解后回代。换元法常用于处理高次方程、分式方程、根式方程等。",
  "metadata": {
    "type": "method",
    "name": "换元法",
    "keywords": ["换元", "代换", "化简"],
    "grade": "high_school",
    "difficulty": "easy",
    "related_kp": ["代数变形", "方程求解"],
    "related_methods": ["配方法", "待定系数法"]
  }
}
```

**概念类型文档 (concept)**:

```json
{
  "id": "cn_001",
  "embedding": [0.345, -0.678, 0.901, ...],
  "document": "函数是数学中的基本概念，描述了两个变量之间的对应关系。设 A、B 为两个非空数集，如果对于 A 中的每一个元素 x，按照某种规则 f，在 B 中都有唯一确定的元素 y 与之对应，那么就称 f 为从 A 到 B 的函数，记作 y=f(x)，其中 x 称为自变量，y 称为因变量，A 称为定义域，f(A) 称为值域。",
  "metadata": {
    "type": "concept",
    "name": "函数定义",
    "keywords": ["函数", "自变量", "因变量", "定义域", "值域"],
    "grade": "high_school",
    "difficulty": "easy",
    "related_kp": ["函数图像", "函数性质"],
    "related_methods": ["解析法", "图像法", "列表法"]
  }
}
```

**例题类型文档 (example)**:

```json
{
  "id": "ex_001",
  "embedding": [0.456, -0.789, 0.012, ...],
  "document": "【例题】已知数列 {a_n} 满足 a_1=2, a_{n+1}=2a_n+1，求其通项公式。\n\n【分析】观察递推关系 a_{n+1}=2a_n+1，可以尝试用迭代法推导，或者构造新数列转化为等比数列。\n\n【解答】解法一（迭代法）：\n由 a_{n+1}=2a_n+1 得\na_n=2a_{n-1}+1=2(2a_{n-2}+1)+1=2^2 a_{n-2}+2+1\n依次类推可得 a_n=2^{n-1} a_1 + (2^{n-2}+2^{n-3}+...+2+1)\n=2^{n-1}·2 + (2^{n-1}-1)\n=3·2^{n-1} - 1\n\n解法二（构造法）：\n令 b_n=a_n+1，则 b_{n+1}=a_{n+1}+1=2a_n+2=2(a_n+1)=2b_n，且 b_1=3，\n故 b_n=3·2^{n-1}，从而 a_n=3·2^{n-1}-1。\n\n【点评】本题体现了处理递推关系的两种常用方法：迭代法和构造法。构造法的关键在于观察递推关系的形式，选择合适的辅助数列。",
  "metadata": {
    "type": "example",
    "name": "数列递推公式求通项",
    "keywords": ["数列", "递推", "通项公式", "迭代法", "构造法"],
    "grade": "high_school",
    "difficulty": "medium",
    "related_kp": ["数列", "递推关系", "数学归纳法"],
    "related_methods": ["迭代法", "构造法"]
  }
}
```

**策略类型文档 (strategy)**:

```json
{
  "id": "st_001",
  "embedding": [0.567, -0.890, 0.123, ...],
  "document": "【教学策略】引导学生发现错误的探究式教学步骤\n\n1. 呈现错误：展示学生在解题过程中常见的典型错误，不指出错误所在。\n2. 集体诊断：请学生独立思考后分组讨论，找出错误所在及其原因。\n3. 教师引导：教师通过追问引导学生认识到错误的本质，而不是直接告知。\n4. 总结归纳：师生共同总结该类错误的识别方法和避免技巧。\n5. 变式练习：提供相似的变式题，检验学生是否真正掌握。\n\n这种方法能够调动学生的主动性，加深对错误本质的理解，避免类似错误再次发生。",
  "metadata": {
    "type": "strategy",
    "name": "错误引导探究式教学",
    "keywords": ["错误分析", "探究式", "教学引导"],
    "grade": "high_school",
    "difficulty": "medium",
    "related_kp": ["解题策略", "错误分析"],
    "related_methods": ["苏格拉底式提问", "变式训练"]
  }
}
```

---

## 7. 内部服务类

### 7.1 RAGService 类定义

```python
from typing import Optional, Dict, Any, List
from datetime import datetime
from .models import (
    KnowledgeChunk,
    RetrieveRequest,
    RetrieveResponse,
    EnrichHintRequest,
    EnrichHintResponse,
    CollectionStats,
    DocumentItem,
    DocumentType,
    DifficultyLevel,
)


class RAGService:
    """
    检索增强生成知识库服务核心类

    该服务封装了知识库检索的所有业务逻辑：
    1. 向量检索：基于语义相似性的知识片段检索
    2. 文档导入：PDF 文档解析、分块、向量生成、存储
    3. 提示增强：将检索结果注入到提示模板中

    Attributes:
        vector_store: ChromaDBVectorStore 向量存储实例
        embedder: DashScopeEmbeddingClient 嵌入生成实例
        ingestion_pipeline: IngestionPipeline 文档导入流水线
        config: 服务配置参数
    """

    def __init__(
        self,
        vector_store: Any,
        embedder: Any,
        ingestion_pipeline: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        初始化 RAG 服务

        Args:
            vector_store: ChromaDB 向量存储实例
            embedder: DashScope embedding 客户端实例
            ingestion_pipeline: 文档导入流水线实例（可选）
            config: 配置字典，包含检索和导入的参数
        """
        self.vector_store = vector_store
        self.embedder = embedder
        self.ingestion_pipeline = ingestion_pipeline
        self.config = config or self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """返回默认配置"""
        return {
            "retrieval": {
                "default_top_k": 3,
                "max_top_k": 20,
                "similarity_threshold": 0.5,
                "timeout_seconds": 5,
            },
            "ingestion": {
                "chunk_size": 400,
                "chunk_overlap": 50,
                "batch_size": 32,
                "max_file_size_mb": 10,
            },
            "enrichment": {
                "max_chunks_in_prompt": 5,
                "default_template": "【相关知识点】\n{knowledge}\n\n【提示】\n请参考上述知识点。",
            },
        }

    # ==================== Core Methods ====================

    async def retrieve(
        self,
        query: str,
        top_k: int = 3,
        filter_metadata: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True,
    ) -> List[KnowledgeChunk]:
        """
        检索与查询语句语义相关的知识片段

        检索流程：
        1. 将 query 文本转换为向量嵌入
        2. 在 ChromaDB 中执行向量相似性搜索
        3. 如提供 filter_metadata，执行元数据过滤
        4. 对结果进行后处理（排序、去重）
        5. 返回知识片段列表

        Args:
            query: 检索查询字符串，长度 1-500 字符
            top_k: 返回结果数量，默认 3，最大 20
            filter_metadata: 可选的元数据过滤条件
            include_metadata: 是否返回完整元数据，默认 True

        Returns:
            List[KnowledgeChunk]: 知识片段列表，按相似度降序排列

        Raises:
            ValueError: query 为空或 top_k 超出范围
            EmbeddingServiceError: DashScope API 调用失败
            ChromaDBConnectionError: ChromaDB 连接失败
            RetrievalTimeoutError: 检索操作超时
        """
        pass

    async def enrich_hint(
        self,
        hint_template: str,
        student_input: str,
        expected_step: Optional[str] = None,
        problem_kp: Optional[List[str]] = None,
        breakpoint_type: Optional[str] = None,
        difficulty: Optional[str] = None,
        top_k: int = 3,
    ) -> EnrichHintResponse:
        """
        将知识检索与提示增强一体化处理

        此方法是 Module 2 专用的便捷接口，将检索与增强两个步骤合二为一。

        流程：
        1. 构造检索查询（结合 problem_kp 和 breakpoint_type）
        2. 调用 retrieve 方法获取相关知识片段
        3. 将知识片段内容格式化后注入到 hint_template
        4. 返回增强后的提示文本

        Args:
            hint_template: 提示模板，包含 {knowledge} 和 {student_state} 占位符
            student_input: 学生当前输入或问题描述
            expected_step: 期望的下一步骤描述
            problem_kp: 题目涉及的知识点列表
            breakpoint_type: 断点类型
            difficulty: 题目难度
            top_k: 检索的知识片段数量，默认 3

        Returns:
            EnrichHintResponse: 包含增强提示和检索元数据

        Raises:
            ValueError: 参数验证失败
            RAGServiceError: 检索或增强处理失败
        """
        pass

    async def ingest_document(
        self,
        file_path: str,
        document_type: DocumentType,
        name: str,
        difficulty: Optional[DifficultyLevel] = None,
        keywords: Optional[List[str]] = None,
        grade: str = "high_school",
    ) -> Dict[str, Any]:
        """
        导入单个 PDF 文档到知识库

        导入流程：
        1. 解析 PDF 文件提取文本内容
        2. 按语义边界切分为知识片段
        3. 生成内容哈希（用于幂等性检查）
        4. 调用 embedder 生成向量嵌入
        5. 写入 ChromaDB 向量存储

        Args:
            file_path: PDF 文件路径
            document_type: 文档类型
            name: 文档名称
            difficulty: 难度等级
            keywords: 关键词列表
            grade: 年级

        Returns:
            Dict包含 document_id, chunks_created, content_hash 等信息

        Raises:
            ValueError: 参数验证失败
            PDFParseError: PDF 解析失败
            EmbeddingServiceError: 嵌入生成失败
            StorageError: 向量存储失败
        """
        pass

    async def ingest_batch(
        self,
        file_paths: List[str],
        document_type: DocumentType,
        difficulty: Optional[DifficultyLevel] = None,
        grade: str = "high_school",
    ) -> Dict[str, Any]:
        """
        批量导入多个 PDF 文档到知识库

        Args:
            file_paths: PDF 文件路径列表，最多 50 个
            document_type: 文档类型
            difficulty: 默认难度等级
            grade: 默认年级

        Returns:
            Dict包含 total_files, succeeded, failed, results 等信息
        """
        pass

    def get_stats(self) -> CollectionStats:
        """
        获取知识库统计信息

        Returns:
            CollectionStats: 包含文档数、片段数、分类型统计、存储信息
        """
        pass

    def list_documents(
        self,
        document_type: Optional[DocumentType] = None,
        difficulty: Optional[DifficultyLevel] = None,
        grade: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
    ) -> List[DocumentItem]:
        """
        列出知识库中的文档

        Args:
            document_type: 按文档类型筛选
            difficulty: 按难度筛选
            grade: 按年级筛选
            limit: 返回数量，默认 20
            offset: 分页偏移量，默认 0
            search: 按名称或关键词搜索

        Returns:
            List[DocumentItem]: 文档列表
        """
        pass

    async def delete_collection(
        self,
        confirm: bool,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        清空知识库 collection

        Args:
            confirm: 必须设为 True 确认删除
            reason: 删除原因说明

        Returns:
            Dict包含 deleted_count, deleted_chunks, operation_id 等信息

        Raises:
            ValueError: confirm 未设为 True
            PermissionError: 无管理员权限
        """
        pass

    async def health_check(self) -> Dict[str, Any]:
        """
        执行健康检查

        检查各依赖服务的连接状态和可用性：
        - ChromaDB 连接和 collection 状态
        - DashScope API 可用性
        - MongoDB 连接状态（如果配置）

        Returns:
            Dict包含 status, services, performance_metrics 等信息
        """
        pass

    # ==================== Helper Methods ====================

    def _build_retrieval_query(
        self,
        problem_kp: Optional[List[str]] = None,
        breakpoint_type: Optional[str] = None,
    ) -> str:
        """
        构造检索查询字符串

        根据 problem_kp 和 breakpoint_type 构建优化的检索查询。

        Args:
            problem_kp: 知识点列表
            breakpoint_type: 断点类型

        Returns:
            str: 构造后的检索查询字符串
        """
        pass

    def _format_chunks_for_prompt(
        self,
        chunks: List[KnowledgeChunk],
    ) -> str:
        """
        将知识片段格式化为提示文本

        Args:
            chunks: 知识片段列表

        Returns:
            str: 格式化后的知识文本
        """
        pass

    def _parse_pdf_and_chunk(
        self,
        file_path: str,
    ) -> List[str]:
        """
        解析 PDF 文件并切分为知识片段

        Args:
            file_path: PDF 文件路径

        Returns:
            List[str]: 切分后的文本片段列表
        """
        pass
```

### 7.2 ChromaDBVectorStore 类定义

```python
class ChromaDBVectorStore:
    """
    ChromaDB 向量存储封装类

    封装了与 ChromaDB 的所有交互操作：
    - Collection 管理
    - 文档添加、删除、查询
    - 向量相似性搜索
    - 元数据过滤
    """

    def __init__(
        self,
        persist_dir: str,
        collection_name: str = "math_knowledge",
        embedding_dimension: int = 1024,
    ) -> None:
        """
        初始化 ChromaDB 向量存储

        Args:
            persist_dir: 持久化目录路径
            collection_name: Collection 名称
            embedding_dimension: 嵌入向量维度
        """
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.embedding_dimension = embedding_dimension
        self._client = None
        self._collection = None

    def _ensure_collection(self) -> None:
        """确保 collection 已创建"""
        pass

    def add_documents(
        self,
        documents: List[Dict[str, Any]],
    ) -> List[str]:
        """
        添加文档到向量存储

        Args:
            documents: 文档列表，每项包含 id, embedding, document, metadata

        Returns:
            List[str]: 添加的文档 ID 列表
        """
        pass

    def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        执行向量相似性搜索

        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            filter_metadata: 元数据过滤条件

        Returns:
            List[Dict]: 匹配的文档列表，每项包含文档内容和相似度分数
        """
        pass

    def get_by_ids(
        self,
        ids: List[str],
    ) -> List[Dict[str, Any]]:
        """
        根据 ID 列表获取文档

        Args:
            ids: 文档 ID 列表

        Returns:
            List[Dict]: 文档列表
        """
        pass

    def delete_by_ids(
        self,
        ids: List[str],
    ) -> None:
        """
        根据 ID 列表删除文档

        Args:
            ids: 文档 ID 列表
        """
        pass

    def delete_collection(self) -> None:
        """删除整个 collection"""
        pass

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        获取 collection 统计信息

        Returns:
            Dict包含 total_documents, by_type, storage_info 等
        """
        pass

    def exists(self) -> bool:
        """
        检查 collection 是否存在

        Returns:
            bool: collection 是否存在
        """
        pass
```

### 7.3 DashScopeEmbeddingClient 类定义

```python
class DashScopeEmbeddingClient:
    """
    DashScope 嵌入生成客户端

    封装了与 DashScope embedding API 的交互：
    - API 密钥管理
    - 批量请求处理
    - 错误重试机制
    - 超时控制
    """

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-v1",
        batch_size: int = 32,
        timeout: int = 30,
        max_retries: int = 3,
    ) -> None:
        """
        初始化 DashScope 嵌入客户端

        Args:
            api_key: DashScope API 密钥
            model: 嵌入模型名称
            batch_size: 批量处理的文档数量
            timeout: 单次请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self.api_key = api_key
        self.model = model
        self.batch_size = batch_size
        self.timeout = timeout
        self.max_retries = max_retries

    async def embed(
        self,
        texts: List[str],
    ) -> List[List[float]]:
        """
        生成文本嵌入向量

        Args:
            texts: 文本列表

        Returns:
            List[List[float]]: 嵌入向量列表，与输入文本一一对应

        Raises:
            EmbeddingServiceError: API 调用失败
        """
        pass

    async def embed_with_retry(
        self,
        texts: List[str],
    ) -> List[List[float]]:
        """
        带重试机制的嵌入生成

        采用指数退避策略，最多重试 max_retries 次。

        Args:
            texts: 文本列表

        Returns:
            List[List[float]]: 嵌入向量列表
        """
        pass

    async def aembed(
        self,
        texts: List[str],
    ) -> List[List[float]]:
        """
        异步版本的嵌入生成

        Args:
            texts: 文本列表

        Returns:
            List[List[float]]: 嵌入向量列表
        """
        pass
```

---

## 8. 附录

### 8.1 术语表

| 术语               | 说明                                         |
| ------------------ | -------------------------------------------- |
| RAG                | Retrieval-Augmented Generation，检索增强生成 |
| ChromaDB           | 开源向量数据库，用于存储和检索嵌入向量       |
| DashScope          | 阿里云大模型服务平台，提供文本嵌入能力       |
| qwen-embeddings-v1 | 通义千问文本嵌入模型，输出 1024 维向量       |
| Chunk              | 知识片段，向量数据库中的最小检索单元         |
| Collection         | ChromaDB 中的文档集合，类似于关系数据库的表  |
| Embedding          | 文本的向量表示，将文本转换为稠密向量         |
| Cosine Similarity  | 余弦相似度，用于衡量向量间的语义相似性       |

### 8.2 环境变量配置

| 变量名                      | 必需 | 默认值              | 说明                 |
| --------------------------- | ---- | ------------------- | -------------------- |
| `CHROMA_PERSIST_DIR`        | 否   | `./data/chromadb`   | ChromaDB 持久化目录  |
| `CHROMA_COLLECTION_NAME`    | 否   | `math_knowledge`    | Collection 名称      |
| `DASHSCOPE_API_KEY`         | 是   | -                   | DashScope API 密钥   |
| `DASHSCOPE_EMBEDDING_MODEL` | 否   | `text-embedding-v1` | 嵌入模型名称         |
| `KG_SERVICE_HOST`           | 否   | `0.0.0.0`           | 服务监听地址         |
| `KG_SERVICE_PORT`           | 否   | `8000`              | 服务监听端口         |
| `EMBEDDING_TIMEOUT`         | 否   | `30`                | 嵌入请求超时（秒）   |
| `RETRIEVAL_TIMEOUT`         | 否   | `5`                 | 检索请求超时（秒）   |
| `EMBEDDING_MAX_RETRIES`     | 否   | `3`                 | 嵌入请求最大重试次数 |

### 8.3 版本历史

| 版本  | 日期       | 更新内容                                       |
| ----- | ---------- | ---------------------------------------------- |
| 1.0.0 | 2026-03-31 | 初始版本，包含核心检索功能和 Module 2 集成接口 |
