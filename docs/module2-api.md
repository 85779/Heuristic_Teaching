# Module 2 API 接口文档

## 渐进式脚手架干预系统在断点处的应用

**版本**: 2.0.0  
**最后更新**: 2026-03-30  
**模块代号**: Socrates-Module-2-Intervention

---

## 1. 模块定位 (Module Position)

**模块名称**: Progressive Scaffolding Intervention System at Breakpoints（断点处渐进式脚手架干预系统）

**模块职能概述**: 渐进式脚手架干预系统是 Socrates 智能导师系统的核心推理引擎，负责在学生解题过程中识别认知断点、动态路由认知维度、判断干预子类型、生成个性化提示，并经过双层安全过滤后交付给学生。该系统采用五节点管道架构，融合规则引擎与大语言模型，在适当时机提供恰到好处的认知支持，既避免过度干预导致的依赖，又防止干预不足导致的放弃。

**在整体架构中的位置**: Module 2 位于学生解题流程的核心位置，承接 Module 1（问题理解与分解）的输出，向 Module 3（进度追踪与评估）提供干预结果数据，并与外部 LLM 服务、矢量数据库、MongoDB 持久化存储紧密交互。作为自适应学习引擎的决策中枢，该模块根据学生的实时行为流（student_steps）动态决定干预时机、强度和形式。

**核心设计理念**: 本模块遵循"最小必要干预"原则，通过五级渐进式脚手架（R1→R4 资源型，M1→M5 元认知型）匹配学生的当前认知状态。系统首先通过 BreakpointLocator 精确定位思维断点，再由 DimensionRouter 判断干预方向（资源型 vs 元认知型），SubTypeDecider 确定具体干预层级，HintGeneratorV2 生成符合学生认知水平的提示内容，最终由 OutputGuardrail 确保提示的安全性、准确性和适当性。

**技术选型理由**: BreakpointLocator 采用纯规则引擎以保证实时性和确定性，适合处理明确的解题步骤缺失或方向错误；DimensionRouter、SubTypeDecider 和 HintGeneratorV2 使用 LLM 以处理模糊的认知状态判断和自然语言生成；OutputGuardrail 采用规则+LLM 双层机制，确保 LLM 输出的安全可控。

---

## 2. API Endpoints

### 2.1 POST /api/v1/intervention/start

**功能描述**: 初始化一个新的干预会话，分析学生当前解题状态，定位第一个断点，并生成初始提示。

**请求头**:
```
Content-Type: application/json
Authorization: Bearer <token>
```

**请求体 (Request)**:
```json
{
  "student_id": "string (必需, 学生唯一标识)",
  "problem": "string (必需, 问题描述)",
  "student_steps": [
    {
      "step_id": "string (步骤唯一标识)",
      "content": "string (步骤内容)",
      "timestamp": "ISO8601 datetime (可选, 步骤时间戳)",
      "is_final": "boolean (可选, 是否为最终答案步骤)"
    }
  ],
  "mainline_solution": [
    {
      "step_id": "string (标准解法步骤标识)",
      "content": "string (标准解法步骤内容)",
      "expected_response": "string (可选, 期望的学生反应)"
    }
  ]
}
```

**请求体示例**:
```json
{
  "student_id": "stu_20260330_001",
  "problem": "求方程 2x + 5 = 13 的解",
  "student_steps": [
    {
      "step_id": "step_1",
      "content": "2x = 13 - 5",
      "timestamp": "2026-03-30T10:00:00Z"
    },
    {
      "step_id": "step_2", 
      "content": "x = 8 / 2",
      "timestamp": "2026-03-30T10:00:15Z",
      "is_final": false
    },
    {
      "step_id": "step_3",
      "content": "x = 4",
      "timestamp": "2026-03-30T10:00:20Z",
      "is_final": true
    }
  ],
  "mainline_solution": [
    {
      "step_id": "sol_1",
      "content": "2x + 5 = 13",
      "expected_response": "识别方程两边"
    },
    {
      "step_id": "sol_2", 
      "content": "2x = 13 - 5",
      "expected_response": "移项得 2x = 8"
    },
    {
      "step_id": "sol_3",
      "content": "x = 8 / 2",
      "expected_response": "两边除以 2"
    },
    {
      "step_id": "sol_4",
      "content": "x = 4",
      "expected_response": "得出最终答案"
    }
  ]
}
```

**响应体 (Response)**:
```json
{
  "session_id": "string (干预会话唯一标识)",
  "breakpoint_location": {
    "position": "integer (断点在 mainline_solution 中的索引位置, 0-based)",
    "breakpoint_type": "BreakpointType (断点类型枚举)",
    "breakpoint_reason": "string (可选, 断点判定理由)",
    "missing_knowledge": "string (可选, 缺失知识点描述)"
  },
  "dimension_result": {
    "dimension": "Dimension (RESOURCE | METACOGNITIVE)",
    "confidence": "float (0.0-1.0, 判定置信度)",
    "reasoning": "string (LLM 推理过程简述)",
    "alternative_dimension": "Dimension (可选, 备选维度及置信度)",
    "routing_evidence": {
      "student_behavior_patterns": ["string (匹配的行为模式列表)"],
      "cognitive_indicators": ["string (认知指标列表)"]
    }
  },
  "current_hint": {
    "sub_type": "SubType (提示子类型: R1-R4 | M1-M5)",
    "level": "integer (1-9, 对应 SubType 的数字部分)",
    "content": "string (提示内容)",
    "approach_used": "string (使用的提示策略: scaffolding | probing | direct_guidance | metacognitive_questioning)",
    "prompt_template_id": "string (可选, 使用的提示模板ID)",
    "estimated_cognitive_load": "string (低 | 中 | 高)"
  },
  "guardrail_passed": {
    "passed": "boolean (是否通过安全过滤)",
    "rule_check_result": {
      "safe_content": "boolean",
      "appropriate_level": "boolean",
      "no_solution_leak": "boolean"
    },
    "llm_review_result": {
      "approved": "boolean",
      "concerns": ["string (潜在问题列表)"],
      "suggestions": ["string (修改建议列表)"]
    }
  },
  "session_status": "SessionStatus (IN_PROGRESS)",
  "intervention_count": 0,
  "created_at": "ISO8601 datetime"
}
```

**HTTP 状态码**:
- `201 Created`: 干预会话创建成功
- `400 Bad Request`: 请求参数格式错误
- `422 Unprocessable Entity`: 业务逻辑校验失败（如 student_steps 为空）
- `500 Internal Server Error`: LLM API 错误或系统内部错误

**响应示例**:
```json
{
  "session_id": "int_20260330_abc123",
  "breakpoint_location": {
    "position": 1,
    "breakpoint_type": "MISSING_STEP",
    "breakpoint_reason": "学生在移项后未说明计算过程，直接给出 x = 8/2",
    "missing_knowledge": "一元一次方程移项法则与合并同类项"
  },
  "dimension_result": {
    "dimension": "RESOURCE",
    "confidence": 0.85,
    "reasoning": "学生表现出对解题步骤的线性执行能力，但在中间步骤缺少详细推导，表现为程序性知识碎片化",
    "alternative_dimension": {
      "dimension": "METACOGNITIVE",
      "confidence": 0.45
    },
    "routing_evidence": {
      "student_behavior_patterns": ["step_skipping", "incomplete_calculation"],
      "cognitive_indicators": ["procedural_knowledge_gap"]
    }
  },
  "current_hint": {
    "sub_type": "R2",
    "level": 2,
    "content": "在你写完 2x = 13 - 5 之后，下一步需要计算右边 13 - 5 等于多少。这个减法运算的结果会告诉我们 2x 的值。",
    "approach_used": "scaffolding",
    "prompt_template_id": "tpl_r2_scaffolding_001",
    "estimated_cognitive_load": "低"
  },
  "guardrail_passed": {
    "passed": true,
    "rule_check_result": {
      "safe_content": true,
      "appropriate_level": true,
      "no_solution_leak": true
    },
    "llm_review_result": {
      "approved": true,
      "concerns": [],
      "suggestions": []
    }
  },
  "session_status": "IN_PROGRESS",
  "intervention_count": 0,
  "created_at": "2026-03-30T10:00:25Z"
}
```

---

### 2.2 POST /api/v1/intervention/feedback

**功能描述**: 接收学生对当前提示的反馈信号，处理反馈并决定是否生成新提示或升级干预级别。

**请求头**:
```
Content-Type: application/json
Authorization: Bearer <token>
```

**请求体 (Request)**:
```json
{
  "session_id": "string (必需, 干预会话唯一标识)",
  "signal": "FrontendSignal (必需, PROGRESSED | NOT_PROGRESSED | DISMISSED)",
  "student_input": "string (可选, 学生最新输入内容，当 signal 为 NOT_PROGRESSED 时建议提供)"
}
```

**请求体示例**:
```json
{
  "session_id": "int_20260330_abc123",
  "signal": "PROGRESSED",
  "student_input": "好的，我计算了一下，13 减 5 等于 8，所以 2x = 8"
}
```

**响应体 (Response)**:
```json
{
  "new_hint": {
    "sub_type": "SubType (新提示子类型)",
    "level": "integer (1-9)",
    "content": "string (新提示内容)",
    "approach_used": "string (提示策略)",
    "escalation_from": "SubType (可选, 升级前的提示类型)",
    "escalation_reason": "string (可选, 升级原因)"
  },
  "guardrail_passed": {
    "passed": "boolean",
    "rule_check_result": { ... },
    "llm_review_result": { ... }
  },
  "session_status": "SessionStatus",
  "intervention_count": "integer (当前干预次数)",
  "escalation_path": {
    "path_taken": ["SubType (路径上经过的所有类型)"],
    "current_position": "integer (在路径中的当前位置)",
    "max_level_reached": "integer (达到的最高级别)"
  },
  "fallback_used": {
    "used": "boolean (是否触发降级策略)",
    "fallback_reason": "string (可选, 降级原因)",
    "fallback_sub_type": "SubType (可选, 降级到的类型)"
  },
  "dimension_switches": "integer (维度切换次数)"
}
```

**HTTP 状态码**:
- `200 OK`: 反馈处理成功
- `404 Not Found`: SESSION_NOT_FOUND (会话不存在)
- `422 Unprocessable Entity`: INVALID_SIGNAL (无效信号)
- `500 Internal Server Error`: 系统内部错误

**响应示例**:
```json
{
  "new_hint": {
    "sub_type": "R3",
    "level": 3,
    "content": "很好！你已经正确得出 2x = 8。现在我们需要两边同时除以 2 来求出 x 的值。思考一下：2 乘以什么数会等于 8？",
    "approach_used": "probing",
    "escalation_from": "R2",
    "escalation_reason": "学生在 R2 级别提示后成功 progress，表现出对基础步骤的理解，需要适度增加认知挑战"
  },
  "guardrail_passed": {
    "passed": true,
    "rule_check_result": {
      "safe_content": true,
      "appropriate_level": true,
      "no_solution_leak": true
    },
    "llm_review_result": {
      "approved": true,
      "concerns": [],
      "suggestions": []
    }
  },
  "session_status": "IN_PROGRESS",
  "intervention_count": 2,
  "escalation_path": {
    "path_taken": ["R2", "R3"],
    "current_position": 2,
    "max_level_reached": 3
  },
  "fallback_used": {
    "used": false
  },
  "dimension_switches": 0
}
```

---

### 2.3 POST /api/v1/intervention/end

**功能描述**: 结束指定的干预会话，生成会话总结报告。

**请求头**:
```
Content-Type: application/json
Authorization: Bearer <token>
```

**请求体 (Request)**:
```json
{
  "session_id": "string (必需, 干预会话唯一标识)",
  "final_status": "FinalStatus (必需, SOLVED | MAX_ESCALATION | ABANDONED)"
}
```

**请求体示例**:
```json
{
  "session_id": "int_20260330_abc123",
  "final_status": "SOLVED"
}
```

**响应体 (Response)**:
```json
{
  "session_summary": {
    "session_id": "string",
    "total_interventions": "integer (总干预次数)",
    "final_level": "SubType | null (最终到达的提示级别)",
    "dimension_switches": "integer (维度切换总次数)",
    "outcome": "FinalStatus (会话最终状态)",
    "resolution_time_seconds": "integer (从会话创建到结束的总秒数)",
    "student_id": "string",
    "problem_brief": "string (问题摘要，前100字符)",
    "breakpoint_types_encountered": ["BreakpointType (遇到的断点类型列表)"],
    "intervention_path": ["SubType (干预路径上的所有类型，按时间顺序)"],
    "escalation_events": [
      {
        "from_level": "SubType",
        "to_level": "SubType",
        "trigger_signal": "FrontendSignal",
        "timestamp": "ISO8601 datetime"
      }
    ],
    "guardrail_blocks": "integer (被安全门拦截的次数)",
    "dimension_distribution": {
      "RESOURCE": "integer (资源型提示使用次数)",
      "METACOGNITIVE": "integer (元认知型提示使用次数)"
    }
  },
  "session_status": "SessionStatus (应为 SOLVED | MAX_ESCALATION | ABANDONED)",
  "ended_at": "ISO8601 datetime"
}
```

**HTTP 状态码**:
- `200 OK`: 会话结束成功
- `404 Not Found`: SESSION_NOT_FOUND
- `400 Bad Request`: 会话已结束或 final_status 无效
- `500 Internal Server Error`: 系统内部错误

---

### 2.4 GET /api/v1/intervention/session/{session_id}

**功能描述**: 获取指定干预会话的完整上下文信息。

**路径参数**:
- `session_id`: string (必需, 干预会话唯一标识)

**请求头**:
```
Authorization: Bearer <token>
```

**响应体 (Response)**:
```json
{
  "session_id": "string",
  "student_id": "string",
  "problem": {
    "original": "string (原始问题描述)",
    "brief": "string (问题摘要)"
  },
  "mainline_solution": ["array (原始传入的标准解法)"],
  "student_steps": [
    {
      "step_id": "string",
      "content": "string",
      "timestamp": "ISO8601 datetime",
      "is_final": "boolean"
    }
  ],
  "dimension_result": {
    "dimension": "Dimension",
    "confidence": "float",
    "reasoning": "string"
  },
  "current_level": {
    "sub_type": "SubType",
    "level": "integer",
    "description": "string (级别描述)"
  },
  "intervention_memory": [
    {
      "intervention_id": "string (干预事件唯一标识)",
      "sequence": "integer (干预序号)",
      "breakpoint_location": {
        "position": "integer",
        "breakpoint_type": "BreakpointType"
      },
      "dimension": "Dimension",
      "level": "integer",
      "sub_type": "SubType",
      "hint_content": "string",
      "signal_received": "FrontendSignal",
      "student_input_at_signal": "string (可选)",
      "created_at": "ISO8601 datetime",
      "guardrail_passed": "boolean"
    }
  ],
  "escalation_path": {
    "path_taken": ["SubType"],
    "current_position": "integer",
    "max_level_reached": "integer"
  },
  "status": "SessionStatus",
  "created_at": "ISO8601 datetime",
  "updated_at": "ISO8601 datetime",
  "ended_at": "ISO8601 datetime | null"
}
```

**HTTP 状态码**:
- `200 OK`: 获取成功
- `404 Not Found`: SESSION_NOT_FOUND
- `500 Internal Server Error`: 系统内部错误

---

### 2.5 POST /api/v1/intervention/escalate

**功能描述**: 手动升级指定干预会话，通常在学生请求帮助、发生超时或其他异常情况时触发。

**请求头**:
```
Content-Type: application/json
Authorization: Bearer <token>
```

**请求体 (Request)**:
```json
{
  "session_id": "string (必需, 干预会话唯一标识)",
  "reason": "string (必需, 升级原因枚举值)",
  "student_input": "string (可选, 升级时的学生输入)",
  "escalation_type": "string (可选, force | gradual, 默认 gradual)"
}
```

**升级原因 (reason) 枚举值**:
- `student_requested`: 学生明确请求帮助
- `timeout`: 等待学生输入超时
- `repeated_errors`: 重复出现相同错误
- `confidence_drop`: 学生置信度下降
- `system_triggered`: 系统自动触发（如连续3次 NOT_PROGRESSED）
- `manual_override`: 人工介入

**响应体 (Response)**:
```json
{
  "escalation_result": {
    "success": "boolean (升级是否成功)",
    "new_hint": {
      "sub_type": "SubType",
      "level": "integer",
      "content": "string",
      "approach_used": "string"
    },
    "escalation_from": "SubType",
    "escalation_to": "SubType",
    "escalation_triggered_by": "string (升级触发原因)"
  },
  "guardrail_passed": {
    "passed": "boolean",
    "rule_check_result": { ... },
    "llm_review_result": { ... }
  },
  "session_status": "SessionStatus",
  "max_escalation_reached": {
    "reached": "boolean",
    "current_max": "SubType",
    "recommendation": "string (可选, 达到最大级别后的建议)"
  },
  "intervention_count": "integer"
}
```

**HTTP 状态码**:
- `200 OK`: 升级处理成功
- `404 Not Found`: SESSION_NOT_FOUND
- `409 Conflict`: 无法升级（如已达到最大级别且非 force 类型）
- `422 Unprocessable Entity`: 升级原因无效
- `500 Internal Server Error`: 系统内部错误

---

### 2.6 GET /api/v1/intervention/health

**功能描述**: 健康检查接口，返回干预系统各依赖服务的连接状态和整体可用性。

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
    "llm": {
      "available": "boolean",
      "provider": "string (e.g., openai | anthropic | azure)",
      "model_in_use": "string (当前使用的模型)",
      "latency_ms": "integer (可选, 最近一次请求延迟)",
      "error": "string (可选, 错误信息)"
    },
    "redis": {
      "connected": "boolean (可选, 如使用缓存)",
      "latency_ms": "integer (可选)"
    },
    "vector_db": {
      "connected": "boolean (可选)",
      "index_loaded": "boolean (可选)"
    }
  },
  "pipeline_nodes": {
    "breakpoint_locator": {
      "status": "string (operational | degraded | offline)",
      "rules_loaded": "integer (已加载的规则数量)"
    },
    "dimension_router": {
      "status": "string",
      "model_loaded": "boolean"
    },
    "sub_type_decider": {
      "status": "string",
      "model_loaded": "boolean"
    },
    "hint_generator": {
      "status": "string",
      "templates_loaded": "integer"
    },
    "output_guardrail": {
      "status": "string",
      "rule_engine_operational": "boolean",
      "llm_filter_operational": "boolean"
    }
  },
  "service_status": "string (operational | degraded | offline)",
  "uptime_seconds": "integer (服务启动以来的秒数)",
  "version": "string (模块版本号)"
}
```

**HTTP 状态码**:
- `200 OK`: 健康检查完成（即使部分服务不健康也返回200，具体状态在响应体中）
- `503 Service Unavailable`: 所有核心服务均不可用

**响应示例**:
```json
{
  "status": "degraded",
  "timestamp": "2026-03-30T10:05:00Z",
  "services": {
    "mongodb": {
      "connected": true,
      "latency_ms": 12
    },
    "llm": {
      "available": true,
      "provider": "anthropic",
      "model_in_use": "claude-3-sonnet-20240229",
      "latency_ms": 850
    },
    "redis": {
      "connected": false
    },
    "vector_db": {
      "connected": true,
      "index_loaded": true
    }
  },
  "pipeline_nodes": {
    "breakpoint_locator": {
      "status": "operational",
      "rules_loaded": 47
    },
    "dimension_router": {
      "status": "operational",
      "model_loaded": true
    },
    "sub_type_decider": {
      "status": "operational",
      "model_loaded": true
    },
    "hint_generator": {
      "status": "operational",
      "templates_loaded": 156
    },
    "output_guardrail": {
      "status": "operational",
      "rule_engine_operational": true,
      "llm_filter_operational": true
    }
  },
  "service_status": "degraded",
  "uptime_seconds": 86400,
  "version": "2.0.0"
}
```

---

## 3. Data Models (数据模型)

### 3.1 TypeScript 类型定义

```typescript
// 断点类型枚举
type BreakpointType = 
  | "MISSING_STEP"      // 缺失必要步骤
  | "WRONG_DIRECTION"   // 方向错误
  | "INCOMPLETE_STEP"   // 步骤不完整
  | "STUCK"             // 卡住无进展
  | "NO_BREAKPOINT";    // 无断点（正常解题）

// 认知维度枚举
type Dimension = 
  | "RESOURCE"      // 资源型：提供外部知识、工具、步骤指导
  | "METACOGNITIVE"; // 元认知型：引导自我监控、策略反思

// 提示子类型枚举（9级）
type SubType = 
  | "R1"  // 资源型 Level 1: 最基础的步骤提示
  | "R2"  // 资源型 Level 2: 增强的步骤指导
  | "R3"  // 资源型 Level 3: 接近直接指导
  | "R4"  // 资源型 Level 4: 几乎完整的答案
  | "M1"  // 元认知型 Level 1: 最低认知水平的元认知提示
  | "M2"  // 元认知型 Level 2: 增强的元认知引导
  | "M3"  // 元认知型 Level 3: 策略性元认知提示
  | "M4"  // 元认知型 Level 4: 深度自我反思引导
  | "M5";  // 元认知型 Level 5: 最高认知水平的元认知提示

// 前端信号枚举
type FrontendSignal = 
  | "PROGRESSED"       // 学生取得进展
  | "NOT_PROGRESSED"   // 学生未取得进展
  | "DISMISSED";       // 学生忽略/拒绝了提示

// 会话状态枚举
type SessionStatus = 
  | "IN_PROGRESS"      // 进行中
  | "SOLVED"           // 已解决
  | "MAX_ESCALATION"   // 达到最大升级
  | "ABANDONED";       // 已放弃

// 最终状态枚举
type FinalStatus = 
  | "SOLVED"           // 问题已解决
  | "MAX_ESCALATION"   // 达到最大干预级别
  | "ABANDONED";       // 学生放弃

// 提示策略类型
type HintApproach = 
  | "scaffolding"           // 脚手架式：逐步搭建支持
  | "probing"              // 探测式：引导性提问
  | "direct_guidance"      // 直接指导：明确告知
  | "metacognitive_questioning"; // 元认知提问

// 学生解题步骤
interface StudentStep {
  step_id: string;
  content: string;
  timestamp?: string;       // ISO8601
  is_final?: boolean;
}

// 标准解法步骤
interface SolutionStep {
  step_id: string;
  content: string;
  expected_response?: string;
}

// 断点定位结果
interface BreakpointLocation {
  position: number;         // 0-based 索引
  breakpoint_type: BreakpointType;
  breakpoint_reason?: string;
  missing_knowledge?: string;
}

// 维度路由结果
interface DimensionResult {
  dimension: Dimension;
  confidence: number;       // 0.0 - 1.0
  reasoning: string;
  alternative_dimension?: {
    dimension: Dimension;
    confidence: number;
  };
  routing_evidence?: {
    student_behavior_patterns: string[];
    cognitive_indicators: string[];
  };
}

// 当前提示
interface CurrentHint {
  sub_type: SubType;
  level: number;            // 1-9
  content: string;
  approach_used: HintApproach;
  prompt_template_id?: string;
  estimated_cognitive_load?: "低" | "中" | "高";
}

// 安全门检查结果
interface GuardrailCheck {
  passed: boolean;
  rule_check_result: {
    safe_content: boolean;
    appropriate_level: boolean;
    no_solution_leak: boolean;
  };
  llm_review_result: {
    approved: boolean;
    concerns: string[];
    suggestions: string[];
  };
}

// 升级路径信息
interface EscalationPath {
  path_taken: SubType[];
  current_position: number;
  max_level_reached: number;
}

// 降级策略使用记录
interface FallbackUsed {
  used: boolean;
  fallback_reason?: string;
  fallback_sub_type?: SubType;
}

// 干预事件记录
interface InterventionEvent {
  intervention_id: string;
  sequence: number;
  breakpoint_location: BreakpointLocation;
  dimension: Dimension;
  level: number;
  sub_type: SubType;
  hint_content: string;
  signal_received?: FrontendSignal;
  student_input_at_signal?: string;
  created_at: string;
  guardrail_passed: boolean;
}

// 干预上下文（完整会话数据）
interface InterventionContext {
  session_id: string;
  student_id: string;
  problem: {
    original: string;
    brief: string;
  };
  mainline_solution: SolutionStep[];
  student_steps: StudentStep[];
  dimension_result: DimensionResult;
  current_level: {
    sub_type: SubType;
    level: number;
    description: string;
  };
  intervention_memory: InterventionEvent[];
  escalation_path: EscalationPath;
  status: SessionStatus;
  created_at: string;
  updated_at: string;
  ended_at?: string;
}

// 会话摘要
interface SessionSummary {
  session_id: string;
  total_interventions: number;
  final_level?: SubType;
  dimension_switches: number;
  outcome: FinalStatus;
  resolution_time_seconds: number;
  student_id: string;
  problem_brief: string;
  breakpoint_types_encountered: BreakpointType[];
  intervention_path: SubType[];
  escalation_events: Array<{
    from_level: SubType;
    to_level: SubType;
    trigger_signal: FrontendSignal;
    timestamp: string;
  }>;
  guardrail_blocks: number;
  dimension_distribution: {
    RESOURCE: number;
    METACOGNITIVE: number;
  };
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
    llm: {
      available: boolean;
      provider: string;
      model_in_use: string;
      latency_ms?: number;
      error?: string;
    };
    redis?: {
      connected: boolean;
      latency_ms?: number;
    };
    vector_db?: {
      connected: boolean;
      index_loaded: boolean;
    };
  };
  pipeline_nodes: {
    breakpoint_locator: {
      status: "operational" | "degraded" | "offline";
      rules_loaded: number;
    };
    dimension_router: {
      status: "operational" | "degraded" | "offline";
      model_loaded: boolean;
    };
    sub_type_decider: {
      status: "operational" | "degraded" | "offline";
      model_loaded: boolean;
    };
    hint_generator: {
      status: "operational" | "degraded" | "offline";
      templates_loaded: number;
    };
    output_guardrail: {
      status: "operational" | "degraded" | "offline";
      rule_engine_operational: boolean;
      llm_filter_operational: boolean;
    };
  };
  service_status: "operational" | "degraded" | "offline";
  uptime_seconds: number;
  version: string;
}
```

### 3.2 Pydantic 数据模型 (Python)

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum


class BreakpointType(str, Enum):
    MISSING_STEP = "MISSING_STEP"
    WRONG_DIRECTION = "WRONG_DIRECTION"
    INCOMPLETE_STEP = "INCOMPLETE_STEP"
    STUCK = "STUCK"
    NO_BREAKPOINT = "NO_BREAKPOINT"


class Dimension(str, Enum):
    RESOURCE = "RESOURCE"
    METACOGNITIVE = "METACOGNITIVE"


class SubType(str, Enum):
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"
    R4 = "R4"
    M1 = "M1"
    M2 = "M2"
    M3 = "M3"
    M4 = "M4"
    M5 = "M5"


class FrontendSignal(str, Enum):
    PROGRESSED = "PROGRESSED"
    NOT_PROGRESSED = "NOT_PROGRESSED"
    DISMISSED = "DISMISSED"


class SessionStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    SOLVED = "SOLVED"
    MAX_ESCALATION = "MAX_ESCALATION"
    ABANDONED = "ABANDONED"


class FinalStatus(str, Enum):
    SOLVED = "SOLVED"
    MAX_ESCALATION = "MAX_ESCALATION"
    ABANDONED = "ABANDONED"


class HintApproach(str, Enum):
    SCAFFOLDING = "scaffolding"
    PROBING = "probing"
    DIRECT_GUIDANCE = "direct_guidance"
    METACOGNITIVE_QUESTIONING = "metacognitive_questioning"


class StudentStep(BaseModel):
    step_id: str
    content: str
    timestamp: Optional[datetime] = None
    is_final: Optional[bool] = False


class SolutionStep(BaseModel):
    step_id: str
    content: str
    expected_response: Optional[str] = None


class BreakpointLocation(BaseModel):
    position: int = Field(description="0-based index in mainline_solution")
    breakpoint_type: BreakpointType
    breakpoint_reason: Optional[str] = None
    missing_knowledge: Optional[str] = None


class RoutingEvidence(BaseModel):
    student_behavior_patterns: List[str] = []
    cognitive_indicators: List[str] = []


class DimensionResult(BaseModel):
    dimension: Dimension
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    alternative_dimension: Optional[Dimension] = None
    routing_evidence: Optional[RoutingEvidence] = None


class CurrentHint(BaseModel):
    sub_type: SubType
    level: int = Field(ge=1, le=9)
    content: str
    approach_used: HintApproach
    prompt_template_id: Optional[str] = None
    estimated_cognitive_load: Optional[Literal["低", "中", "高"]] = "中"


class RuleCheckResult(BaseModel):
    safe_content: bool
    appropriate_level: bool
    no_solution_leak: bool


class LLMReviewResult(BaseModel):
    approved: bool
    concerns: List[str] = []
    suggestions: List[str] = []


class GuardrailCheck(BaseModel):
    passed: bool
    rule_check_result: RuleCheckResult
    llm_review_result: LLMReviewResult


class EscalationPath(BaseModel):
    path_taken: List[SubType] = []
    current_position: int = 0
    max_level_reached: int = 0


class FallbackUsed(BaseModel):
    used: bool = False
    fallback_reason: Optional[str] = None
    fallback_sub_type: Optional[SubType] = None


class InterventionEvent(BaseModel):
    intervention_id: str
    sequence: int
    breakpoint_location: BreakpointLocation
    dimension: Dimension
    level: int
    sub_type: SubType
    hint_content: str
    signal_received: Optional[FrontendSignal] = None
    student_input_at_signal: Optional[str] = None
    created_at: datetime
    guardrail_passed: bool


class InterventionContext(BaseModel):
    session_id: str
    student_id: str
    problem: dict  # {"original": str, "brief": str}
    mainline_solution: List[SolutionStep]
    student_steps: List[StudentStep]
    dimension_result: DimensionResult
    current_level: dict  # {"sub_type": SubType, "level": int, "description": str}
    intervention_memory: List[InterventionEvent] = []
    escalation_path: EscalationPath = Field(default_factory=EscalationPath)
    status: SessionStatus = SessionStatus.IN_PROGRESS
    created_at: datetime
    updated_at: datetime
    ended_at: Optional[datetime] = None


class SessionSummary(BaseModel):
    session_id: str
    total_interventions: int
    final_level: Optional[SubType] = None
    dimension_switches: int
    outcome: FinalStatus
    resolution_time_seconds: int
    student_id: str
    problem_brief: str
    breakpoint_types_encountered: List[BreakpointType] = []
    intervention_path: List[SubType] = []
    escalation_events: List[dict] = []
    guardrail_blocks: int = 0
    dimension_distribution: dict  # {"RESOURCE": int, "METACOGNITIVE": int}


class HealthStatus(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    timestamp: datetime
    services: dict
    pipeline_nodes: dict
    service_status: Literal["operational", "degraded", "offline"]
    uptime_seconds: int
    version: str


# Request Models
class StartInterventionRequest(BaseModel):
    student_id: str
    problem: str
    student_steps: List[StudentStep] = []
    mainline_solution: List[SolutionStep]


class FeedbackRequest(BaseModel):
    session_id: str
    signal: FrontendSignal
    student_input: Optional[str] = ""


class EndInterventionRequest(BaseModel):
    session_id: str
    final_status: FinalStatus


class EscalateRequest(BaseModel):
    session_id: str
    reason: str
    student_input: Optional[str] = ""
    escalation_type: Optional[Literal["force", "gradual"]] = "gradual"


# Response Models
class StartInterventionResponse(BaseModel):
    session_id: str
    breakpoint_location: BreakpointLocation
    dimension_result: DimensionResult
    current_hint: CurrentHint
    guardrail_passed: GuardrailCheck
    session_status: SessionStatus = SessionStatus.IN_PROGRESS
    intervention_count: int = 0
    created_at: datetime


class FeedbackResponse(BaseModel):
    new_hint: CurrentHint
    guardrail_passed: GuardrailCheck
    session_status: SessionStatus
    intervention_count: int
    escalation_path: Optional[EscalationPath] = None
    fallback_used: FallbackUsed = Field(default_factory=FallbackUsed)
    dimension_switches: int = 0


class EndInterventionResponse(BaseModel):
    session_summary: SessionSummary
    session_status: SessionStatus
    ended_at: datetime
```

---

## 4. Internal Service Class (内部服务类)

### 4.1 InterventionService 类定义

```python
from typing import Optional, Dict, Any, List
from datetime import datetime
from .models import (
    InterventionContext,
    InterventionResponse,
    FeedbackResponse,
    SessionSummary,
    HealthStatus,
    BreakpointType,
    Dimension,
    SubType,
    FrontendSignal,
    SessionStatus,
    FinalStatus,
)


class InterventionService:
    """
    渐进式脚手架干预服务核心类
    
    该服务封装了五节点干预管道的所有业务逻辑：
    1. BreakpointLocator: 规则引擎定位解题断点
    2. DimensionRouter: LLM 判断干预维度 (RESOURCE/METACOGNITIVE)
    3. SubTypeDecider: LLM 决定具体干预级别 (R1-R4/M1-M5)
    4. HintGeneratorV2: LLM 生成个性化提示内容
    5. OutputGuardrail: 规则+LLM 双层安全过滤
    
    Attributes:
        mongodb_client: MongoDB 客户端实例
        llm_provider: LLM 服务提供商 (OpenAI/Anthropic/Azure)
        redis_client: Redis 缓存客户端 (可选)
        vector_db: 矢量数据库客户端 (可选)
        config: 服务配置参数
    """
    
    def __init__(
        self,
        mongodb_client: Any,
        llm_provider: Any,
        redis_client: Optional[Any] = None,
        vector_db: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        初始化干预服务
        
        Args:
            mongodb_client: MongoDB 客户端实例，用于持久化存储
            llm_provider: LLM 服务提供商实例
            redis_client: Redis 客户端实例（可选，用于缓存）
            vector_db: 矢量数据库客户端（可选，用于相似问题检索）
            config: 配置字典，包含各管道节点的参数
        """
        self.mongodb = mongodb_client
        self.llm = llm_provider
        self.redis = redis_client
        self.vector_db = vector_db
        self.config = config or self._default_config()
        
        # 初始化五节点管道
        self._init_pipeline()
    
    def _default_config(self) -> Dict[str, Any]:
        """返回默认配置"""
        return {
            "breakpoint_locator": {
                "max_step_comparison_window": 3,
                "similarity_threshold": 0.6,
                "direction_check_enabled": True,
            },
            "dimension_router": {
                "model_name": "claude-3-sonnet-20240229",
                "temperature": 0.3,
                "max_tokens": 500,
                "confidence_threshold": 0.7,
            },
            "sub_type_decider": {
                "model_name": "claude-3-sonnet-20240229",
                "temperature": 0.2,
                "max_tokens": 300,
            },
            "hint_generator": {
                "model_name": "claude-3-sonnet-20240229",
                "temperature": 0.7,
                "max_tokens": 800,
                "use_template_fallback": True,
            },
            "output_guardrail": {
                "rule_check_enabled": True,
                "llm_review_enabled": True,
                "max_review_attempts": 3,
            },
            "escalation": {
                "max_interventions": 9,
                "max_same_level_attempts": 2,
                "dimension_switch_cooldown": 2,
            },
        }
    
    def _init_pipeline(self) -> None:
        """初始化五节点管道组件"""
        # BreakpointLocator: 纯规则引擎，无需 LLM
        self.breakpoint_locator = BreakpointLocator(
            config=self.config.get("breakpoint_locator", {})
        )
        
        # DimensionRouter: LLM 驱动的维度路由
        self.dimension_router = DimensionRouter(
            llm_provider=self.llm,
            config=self.config.get("dimension_router", {})
        )
        
        # SubTypeDecider: LLM 驱动的子类型决策
        self.sub_type_decider = SubTypeDecider(
            llm_provider=self.llm,
            config=self.config.get("sub_type_decider", {})
        )
        
        # HintGeneratorV2: LLM 驱动的提示生成器
        self.hint_generator = HintGeneratorV2(
            llm_provider=self.llm,
            config=self.config.get("hint_generator", {})
        )
        
        # OutputGuardrail: 规则+LLM 双层安全门
        self.output_guardrail = OutputGuardrail(
            llm_provider=self.llm,
            config=self.config.get("output_guardrail", {})
        )
    
    # ==================== Core Methods ====================
    
    async def create_intervention(
        self,
        student_id: str,
        problem: str,
        student_steps: List[Dict[str, Any]],
        mainline_solution: List[Dict[str, Any]],
    ) -> InterventionResponse:
        """
        创建新的干预会话
        
        执行完整的五节点管道流程：
        1. 解析和验证输入
        2. BreakpointLocator 定位断点
        3. DimensionRouter 判断维度
        4. SubTypeDecider 决定级别
        5. HintGeneratorV2 生成提示
        6. OutputGuardrail 安全过滤
        7. 存储会话上下文
        
        Args:
            student_id: 学生唯一标识
            problem: 问题描述文本
            student_steps: 学生已完成的解题步骤列表
            mainline_solution: 标准解法步骤列表
        
        Returns:
            InterventionResponse: 包含断点定位、维度路由、当前提示的完整响应
        
        Raises:
            ValueError: 输入参数验证失败
            LLMAPIError: LLM API 调用失败
            LLMParseError: LLM 响应解析失败
        """
        # Step 1: 输入验证与解析
        session_id = self._generate_session_id()
        parsed_student_steps = self._parse_student_steps(student_steps)
        parsed_solution = self._parse_solution_steps(mainline_solution)
        
        # Step 2: BreakpointLocator - 规则引擎定位断点（无 LLM）
        breakpoint_result = await self.breakpoint_locator.locate(
            student_steps=parsed_student_steps,
            mainline_solution=parsed_solution,
        )
        
        # 如果无断点，直接返回成功状态
        if breakpoint_result.breakpoint_type == BreakpointType.NO_BREAKPOINT:
            return InterventionResponse(
                session_id=session_id,
                breakpoint_location=breakpoint_result,
                dimension_result=None,
                current_hint=None,
                guardrail_passed=GuardrailCheck(passed=True),
                session_status=SessionStatus.SOLVED,
                intervention_count=0,
            )
        
        # Step 3: DimensionRouter - LLM 判断维度 (R/M 二分类)
        dimension_result = await self.dimension_router.route(
            problem=problem,
            student_steps=parsed_student_steps,
            breakpoint_location=breakpoint_result,
        )
        
        # Step 4: SubTypeDecider - LLM 决定具体级别 (9级分类)
        sub_type_result = await self.sub_type_decider.decide(
            problem=problem,
            student_steps=parsed_student_steps,
            breakpoint_location=breakpoint_result,
            dimension=dimension_result.dimension,
            confidence=dimension_result.confidence,
        )
        
        # Step 5: HintGeneratorV2 - LLM 生成提示内容
        hint_result = await self.hint_generator.generate(
            problem=problem,
            student_steps=parsed_student_steps,
            breakpoint_location=breakpoint_result,
            dimension=dimension_result.dimension,
            sub_type=sub_type_result.sub_type,
            level=sub_type_result.level,
        )
        
        # Step 6: OutputGuardrail - 双层安全过滤
        guardrail_result = await self.output_guardrail.check(
            content=hint_result.content,
            level=sub_type_result.level,
            dimension=dimension_result.dimension,
            breakpoint_type=breakpoint_result.breakpoint_type,
        )
        
        # 如果安全门未通过，触发降级策略
        if not guardrail_result.passed:
            hint_result, guardrail_result = await self._handle_guardrail_failure(
                original_hint=hint_result,
                breakpoint_location=breakpoint_result,
                dimension=dimension_result.dimension,
            )
        
        # Step 7: 构建响应并持久化会话
        response = InterventionResponse(
            session_id=session_id,
            breakpoint_location=breakpoint_result,
            dimension_result=dimension_result,
            current_hint=hint_result,
            guardrail_passed=guardrail_result,
            session_status=SessionStatus.IN_PROGRESS,
            intervention_count=1,
        )
        
        # 异步持久化会话上下文
        await self._persist_intervention_context(
            session_id=session_id,
            student_id=student_id,
            problem=problem,
            student_steps=parsed_student_steps,
            mainline_solution=parsed_solution,
            response=response,
        )
        
        return response
    
    async def process_feedback(
        self,
        session_id: str,
        signal: FrontendSignal,
        student_input: str = "",
    ) -> FeedbackResponse:
        """
        处理学生对提示的反馈
        
        根据反馈信号决定：
        - PROGRESSED: 升级到更高一级提示
        - NOT_PROGRESSED: 保持当前级别或降级重试
        - DISMISSED: 尝试不同维度的提示
        
        Args:
            session_id: 干预会话唯一标识
            signal: 前端反馈信号
            student_input: 学生最新输入内容
        
        Returns:
            FeedbackResponse: 包含新提示、升级路径、会话状态
        
        Raises:
            SessionNotFoundError: 会话不存在
            InvalidSignalError: 无效的反馈信号
        """
        # 获取当前会话上下文
        context = await self._get_intervention_context(session_id)
        
        if context is None:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        # 验证信号有效性
        if signal not in FrontendSignal:
            raise InvalidSignalError(f"Invalid signal: {signal}")
        
        # 记录当前状态用于对比
        current_level = context.current_level["sub_type"]
        current_dimension = context.dimension_result.dimension
        
        # 根据信号类型处理反馈
        if signal == FrontendSignal.PROGRESSED:
            new_hint, escalation_info = await self._handle_progressed(
                context=context,
                student_input=student_input,
            )
        elif signal == FrontendSignal.NOT_PROGRESSED:
            new_hint, escalation_info = await self._handle_not_progressed(
                context=context,
                student_input=student_input,
            )
        else:  # DISMISSED
            new_hint, escalation_info = await self._handle_dismissed(
                context=context,
                student_input=student_input,
            )
        
        # 安全门检查
        guardrail_result = await self.output_guardrail.check(
            content=new_hint.content,
            level=new_hint.level,
            dimension=new_hint.sub_type[0] == "R" and Dimension.RESOURCE or Dimension.METACOGNITIVE,
            breakpoint_type=context.intervention_memory[-1].breakpoint_location.breakpoint_type if context.intervention_memory else BreakpointType.MISSING_STEP,
        )
        
        # 计算维度切换次数
        dimension_switches = self._count_dimension_switches(
            context.escalation_path.path_taken + [new_hint.sub_type]
        )
        
        # 更新干预计数
        intervention_count = len(context.intervention_memory) + 1
        
        # 检查是否达到最大干预次数
        max_interventions = self.config["escalation"]["max_interventions"]
        if intervention_count >= max_interventions:
            return FeedbackResponse(
                new_hint=new_hint,
                guardrail_passed=guardrail_result,
                session_status=SessionStatus.MAX_ESCALATION,
                intervention_count=intervention_count,
                escalation_path=context.escalation_path,
                fallback_used=FallbackUsed(used=False),
                dimension_switches=dimension_switches,
            )
        
        # 构建响应
        response = FeedbackResponse(
            new_hint=new_hint,
            guardrail_passed=guardrail_result,
            session_status=SessionStatus.IN_PROGRESS,
            intervention_count=intervention_count,
            escalation_path=context.escalation_path,
            fallback_used=FallbackUsed(used=False),
            dimension_switches=dimension_switches,
        )
        
        # 持久化更新后的上下文
        await self._update_intervention_context(
            session_id=session_id,
            new_event={
                "intervention_id": self._generate_intervention_id(),
                "sequence": intervention_count,
                "breakpoint_location": context.intervention_memory[-1].breakpoint_location if context.intervention_memory else context.breakpoint_location,
                "dimension": context.dimension_result.dimension,
                "level": new_hint.level,
                "sub_type": new_hint.sub_type,
                "hint_content": new_hint.content,
                "signal_received": signal,
                "student_input_at_signal": student_input,
                "created_at": datetime.utcnow(),
                "guardrail_passed": guardrail_result.passed,
            },
        )
        
        return response
    
    async def end_intervention(
        self,
        session_id: str,
        final_status: FinalStatus,
    ) -> SessionSummary:
        """
        结束干预会话并生成总结报告
        
        Args:
            session_id: 干预会话唯一标识
            final_status: 最终会话状态 (SOLVED/MAX_ESCALATION/ABANDONED)
        
        Returns:
            SessionSummary: 包含完整会话统计的摘要对象
        
        Raises:
            SessionNotFoundError: 会话不存在
        """
        context = await self._get_intervention_context(session_id)
        
        if context is None:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        # 计算会话时长
        resolution_time = (datetime.utcnow() - context.created_at).total_seconds()
        
        # 收集断点类型
        breakpoint_types = [
            event.breakpoint_location.breakpoint_type 
            for event in context.intervention_memory
        ]
        
        # 收集干预路径
        intervention_path = [event.sub_type for event in context.intervention_memory]
        
        # 统计升级事件
        escalation_events = self._extract_escalation_events(context.intervention_memory)
        
        # 统计维度分布
        dimension_dist = {"RESOURCE": 0, "METACOGNITIVE": 0}
        for event in context.intervention_memory:
            dimension_dist[event.dimension.value] += 1
        
        # 统计安全门拦截次数
        guardrail_blocks = sum(
            1 for event in context.intervention_memory 
            if not event.guardrail_passed
        )
        
        # 计算维度切换次数
        dimension_switches = self._count_dimension_switches(intervention_path)
        
        # 构建摘要
        summary = SessionSummary(
            session_id=session_id,
            total_interventions=len(context.intervention_memory),
            final_level=intervention_path[-1] if intervention_path else None,
            dimension_switches=dimension_switches,
            outcome=final_status,
            resolution_time_seconds=int(resolution_time),
            student_id=context.student_id,
            problem_brief=context.problem.get("brief", context.problem.get("original", ""))[:100],
            breakpoint_types_encountered=breakpoint_types,
            intervention_path=intervention_path,
            escalation_events=escalation_events,
            guardrail_blocks=guardrail_blocks,
            dimension_distribution=dimension_dist,
        )
        
        # 更新会话状态为已结束
        await self._finalize_intervention_session(
            session_id=session_id,
            final_status=final_status,
            summary=summary,
        )
        
        return summary
    
    def get_session(self, session_id: str) -> InterventionContext:
        """
        获取干预会话的完整上下文
        
        Args:
            session_id: 干预会话唯一标识
        
        Returns:
            InterventionContext: 完整的会话上下文对象
        
        Raises:
            SessionNotFoundError: 会话不存在
        """
        # 尝试从缓存获取
        if self.redis:
            cached = self._get_cached_context(session_id)
            if cached:
                return cached
        
        # 从 MongoDB 获取
        context = self._fetch_intervention_context(session_id)
        
        if context is None:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        # 缓存结果
        if self.redis:
            self._cache_context(session_id, context)
        
        return context
    
    async def escalate(
        self,
        session_id: str,
        reason: str,
    ) -> FeedbackResponse:
        """
        手动升级干预会话
        
        Args:
            session_id: 干预会话唯一标识
            reason: 升级原因 (student_requested/timeout/repeated_errors/confidence_drop/system_triggered/manual_override)
        
        Returns:
            FeedbackResponse: 升级后的新提示和状态
        
        Raises:
            SessionNotFoundError: 会话不存在
            MaxEscalationError: 已达到最大升级级别
        """
        context = await self._get_intervention_context(session_id)
        
        if context is None:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        # 获取当前最高级别
        current_max = context.escalation_path.max_level_reached
        
        # 确定目标级别
        target_level = self._calculate_escalation_target(
            current_level=current_max,
            reason=reason,
        )
        
        # 检查是否已达到最大级别
        if target_level > 9:
            return FeedbackResponse(
                new_hint=context.intervention_memory[-1] if context.intervention_memory else None,
                guardrail_passed=GuardrailCheck(passed=True),
                session_status=SessionStatus.MAX_ESCALATION,
                intervention_count=len(context.intervention_memory),
                escalation_path=context.escalation_path,
                fallback_used=FallbackUsed(
                    used=True,
                    fallback_reason="Max escalation reached",
                    fallback_sub_type=context.escalation_path.path_taken[-1] if context.escalation_path.path_taken else None,
                ),
                dimension_switches=self._count_dimension_switches(context.escalation_path.path_taken),
            )
        
        # 生成升级后的提示
        new_hint = await self._generate_escalated_hint(
            context=context,
            target_level=target_level,
            reason=reason,
        )
        
        # 安全门检查
        guardrail_result = await self.output_guardrail.check(
            content=new_hint.content,
            level=new_hint.level,
            dimension=new_hint.sub_type[0] == "R" and Dimension.RESOURCE or Dimension.METACOGNITIVE,
            breakpoint_type=context.intervention_memory[-1].breakpoint_location.breakpoint_type if context.intervention_memory else BreakpointType.STUCK,
        )
        
        # 更新升级路径
        context.escalation_path.path_taken.append(new_hint.sub_type)
        context.escalation_path.current_position = len(context.escalation_path.path_taken) - 1
        context.escalation_path.max_level_reached = max(
            context.escalation_path.max_level_reached,
            new_hint.level,
        )
        
        # 构建响应
        response = FeedbackResponse(
            new_hint=new_hint,
            guardrail_passed=guardrail_result,
            session_status=SessionStatus.IN_PROGRESS,
            intervention_count=len(context.intervention_memory) + 1,
            escalation_path=context.escalation_path,
            fallback_used=FallbackUsed(used=False),
            dimension_switches=self._count_dimension_switches(context.escalation_path.path_taken),
        )
        
        # 持久化
        await self._update_intervention_context(
            session_id=session_id,
            new_event={
                "intervention_id": self._generate_intervention_id(),
                "sequence": len(context.intervention_memory) + 1,
                "breakpoint_location": context.intervention_memory[-1].breakpoint_location if context.intervention_memory else None,
                "dimension": new_hint.sub_type[0] == "R" and Dimension.RESOURCE or Dimension.METACOGNITIVE,
                "level": new_hint.level,
                "sub_type": new_hint.sub_type,
                "hint_content": new_hint.content,
                "signal_received": None,
                "student_input_at_signal": f"ESCALATION: {reason}",
                "created_at": datetime.utcnow(),
                "guardrail_passed": guardrail_result.passed,
            },
        )
        
        return response
    
    def health_check(self) -> HealthStatus:
        """
        执行健康检查，返回系统各组件状态
        
        Returns:
            HealthStatus: 包含所有依赖服务状态的健康检查对象
        """
        services_status = {}
        overall_health = "healthy"
        
        # MongoDB 连接检查
        mongodb_status = self._check_mongodb_health()
        services_status["mongodb"] = mongodb_status
        if not mongodb_status["connected"]:
            overall_health = "unhealthy"
        
        # LLM 可用性检查
        llm_status = self._check_llm_health()
        services_status["llm"] = llm_status
        if not llm_status["available"]:
            overall_health = "unhealthy"
        elif overall_health == "healthy" and llm_status.get("latency_ms", 0) > 2000:
            overall_health = "degraded"
        
        # Redis 连接检查（如果配置）
        if self.redis:
            redis_status = self._check_redis_health()
            services_status["redis"] = redis_status
            if not redis_status["connected"]:
                overall_health = "degraded"
        
        # VectorDB 连接检查（如果配置）
        if self.vector_db:
            vector_status = self._check_vector_db_health()
            services_status["vector_db"] = vector_status
        
        # 管道节点状态
        pipeline_status = {
            "breakpoint_locator": {
                "status": "operational",
                "rules_loaded": self.breakpoint_locator.get_rules_count(),
            },
            "dimension_router": {
                "status": "operational" if services_status["llm"]["available"] else "degraded",
                "model_loaded": self.dimension_router.is_model_loaded(),
            },
            "sub_type_decider": {
                "status": "operational" if services_status["llm"]["available"] else "degraded",
                "model_loaded": self.sub_type_decider.is_model_loaded(),
            },
            "hint_generator": {
                "status": "operational" if services_status["llm"]["available"] else "degraded",
                "templates_loaded": self.hint_generator.get_template_count(),
            },
            "output_guardrail": {
                "status": "operational",
                "rule_engine_operational": self.output_guardrail.is_rule_engine_operational(),
                "llm_filter_operational": self.output_guardrail.is_llm_filter_operational(),
            },
        }
        
        return HealthStatus(
            status=overall_health,
            timestamp=datetime.utcnow(),
            services=services_status,
            pipeline_nodes=pipeline_status,
            service_status=overall_health,
            uptime_seconds=self._get_uptime_seconds(),
            version=self.config.get("version", "2.0.0"),
        )
    
    # ==================== Helper Methods ====================
    
    def _generate_session_id(self) -> str:
        """生成唯一的会话 ID"""
        import uuid
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        unique_part = uuid.uuid4().hex[:8]
        return f"int_{timestamp}_{unique_part}"
    
    def _generate_intervention_id(self) -> str:
        """生成唯一的干预事件 ID"""
        import uuid
        return f"ievt_{uuid.uuid4().hex[:12]}"
    
    def _parse_student_steps(self, steps: List[Dict]) -> List[StudentStep]:
        """解析学生步骤数据"""
        return [StudentStep(**step) for step in steps]
    
    def _parse_solution_steps(self, steps: List[Dict]) -> List[SolutionStep]:
        """解析标准解法步骤数据"""
        return [SolutionStep(**step) for step in steps]
    
    async def _handle_guardrail_failure(
        self,
        original_hint: CurrentHint,
        breakpoint_location: BreakpointLocation,
        dimension: Dimension,
    ) -> tuple:
        """处理安全门未通过的情况，执行降级策略"""
        # 降级到更安全的提示模板
        fallback_level = max(1, original_hint.level - 2)
        fallback_sub_type = SubType(f"{dimension.value[0]}{fallback_level}")
        
        # 使用降级后的子类型重新生成提示
        fallback_hint = await self.hint_generator.generate_with_subtype(
            problem="",  # 需要从上下文获取
            sub_type=fallback_sub_type,
            breakpoint_type=breakpoint_location.breakpoint_type,
        )
        
        # 重新检查安全门
        guardrail_result = await self.output_guardrail.check(
            content=fallback_hint.content,
            level=fallback_hint.level,
            dimension=dimension,
            breakpoint_type=breakpoint_location.breakpoint_type,
        )
        
        return fallback_hint, guardrail_result
    
    async def _handle_progressed(
        self,
        context: InterventionContext,
        student_input: str,
    ) -> tuple:
        """处理 PROGRESSED 信号，升级提示级别"""
        current_sub_type = context.intervention_memory[-1].sub_type if context.intervention_memory else None
        
        # 计算下一个级别
        next_level = self._calculate_next_level(
            current_sub_type=current_sub_type,
            dimension=context.dimension_result.dimension,
            can_switch_dimension=False,
        )
        
        # 生成新提示
        new_hint = await self.hint_generator.generate_with_subtype(
            problem=context.problem["original"],
            sub_type=next_level,
            breakpoint_type=context.intervention_memory[-1].breakpoint_location.breakpoint_type if context.intervention_memory else BreakpointType.MISSING_STEP,
        )
        
        # 更新升级路径
        escalation_info = {
            "escalation_from": current_sub_type,
            "escalation_to": next_level,
        }
        context.escalation_path.path_taken.append(next_level)
        context.escalation_path.current_position = len(context.escalation_path.path_taken) - 1
        context.escalation_path.max_level_reached = max(
            context.escalation_path.max_level_reached,
            new_hint.level,
        )
        
        return new_hint, escalation_info
    
    async def _handle_not_progressed(
        self,
        context: InterventionContext,
        student_input: str,
    ) -> tuple:
        """处理 NOT_PROGRESSED 信号"""
        current_sub_type = context.intervention_memory[-1].sub_type if context.intervention_memory else None
        attempts_at_current_level = self._count_attempts_at_level(
            context.intervention_memory,
            current_sub_type,
        )
        
        # 如果当前级别尝试次数超过阈值，尝试升级
        max_same_level_attempts = self.config["escalation"]["max_same_level_attempts"]
        if attempts_at_current_level >= max_same_level_attempts:
            return await self._handle_progressed(context, student_input)
        
        # 否则保持当前级别，使用不同策略重新生成提示
        new_hint = await self.hint_generator.regenerate_with_strategy(
            problem=context.problem["original"],
            sub_type=current_sub_type,
            breakpoint_type=context.intervention_memory[-1].breakpoint_location.breakpoint_type if context.intervention_memory else BreakpointType.STUCK,
            student_input=student_input,
        )
        
        escalation_info = {"escalation_from": None, "escalation_to": None}
        return new_hint, escalation_info
    
    async def _handle_dismissed(
        self,
        context: InterventionContext,
        student_input: str,
    ) -> tuple:
        """处理 DISMISSED 信号，尝试切换维度"""
        current_dimension = context.dimension_result.dimension
        
        # 切换到另一个维度
        new_dimension = (
            Dimension.METACOGNITIVE 
            if current_dimension == Dimension.RESOURCE 
            else Dimension.RESOURCE
        )
        
        # 检查冷却期
        cooldown = self.config["escalation"]["dimension_switch_cooldown"]
        recent_switches = self._count_recent_dimension_switches(
            context.intervention_memory,
            cooldown,
        )
        
        if recent_switches > 0:
            # 冷却期内，不切换维度，而是使用更基础的提示
            fallback_sub_type = SubType(f"{current_dimension.value[0]}1")
            new_hint = await self.hint_generator.generate_with_subtype(
                problem=context.problem["original"],
                sub_type=fallback_sub_type,
                breakpoint_type=context.intervention_memory[-1].breakpoint_location.breakpoint_type if context.intervention_memory else BreakpointType.STUCK,
            )
        else:
            # 执行维度切换
            context.dimension_result.dimension = new_dimension
            new_hint = await self.hint_generator.generate_with_subtype(
                problem=context.problem["original"],
                sub_type=SubType(f"{new_dimension.value[0]}1"),
                breakpoint_type=context.intervention_memory[-1].breakpoint_location.breakpoint_type if context.intervention_memory else BreakpointType.STUCK,
            )
        
        escalation_info = {
            "escalation_from": current_dimension,
            "escalation_to": new_dimension,
            "dimension_switch": True,
        }
        context.escalation_path.path_taken.append(new_hint.sub_type)
        context.escalation_path.current_position = len(context.escalation_path.path_taken) - 1
        
        return new_hint, escalation_info
    
    def _calculate_next_level(
        self,
        current_sub_type: Optional[SubType],
        dimension: Dimension,
        can_switch_dimension: bool = False,
    ) -> SubType:
        """计算下一个提示级别"""
        if current_sub_type is None:
            return SubType(f"{dimension.value[0]}1")
        
        current_prefix = current_sub_type[0]
        current_num = int(current_sub_type[1])
        
        # 在同一维度内升级
        if current_num < 4:  # R1-R4 或 M1-M4
            next_num = current_num + 1
            return SubType(f"{current_prefix}{next_num}")
        
        # 达到当前维度最高级，考虑切换维度
        if can_switch_dimension:
            other_prefix = "M" if current_prefix == "R" else "R"
            return SubType(f"{other_prefix}1")
        
        # 不能切换，保持最高级
        return current_sub_type
    
    def _count_attempts_at_level(
        self,
        memory: List[InterventionEvent],
        sub_type: Optional[SubType],
    ) -> int:
        """统计在特定级别的尝试次数"""
        if sub_type is None:
            return 0
        return sum(1 for event in memory if event.sub_type == sub_type)
    
    def _count_dimension_switches(self, path: List[SubType]) -> int:
        """统计路径中的维度切换次数"""
        switches = 0
        prev_prefix = None
        for sub_type in path:
            prefix = sub_type[0]
            if prev_prefix and prefix != prev_prefix:
                switches += 1
            prev_prefix = prefix
        return switches
    
    def _count_recent_dimension_switches(
        self,
        memory: List[InterventionEvent],
        cooldown: int,
    ) -> int:
        """统计最近 N 次干预中的维度切换次数"""
        recent = memory[-cooldown:] if len(memory) > cooldown else memory
        return self._count_dimension_switches([e.sub_type for e in recent])
    
    def _calculate_escalation_target(
        self,
        current_level: int,
        reason: str,
    ) -> int:
        """计算升级的目标级别"""
        if reason in ("repeated_errors", "confidence_drop"):
            # 较严重的信号，大幅升级
            return min(9, current_level + 3)
        elif reason == "timeout":
            # 超时，中等升级
            return min(9, current_level + 2)
        else:
            # 默认小幅度升级
            return min(9, current_level + 1)
    
    def _extract_escalation_events(
        self,
        memory: List[InterventionEvent],
    ) -> List[Dict]:
        """从干预记忆中提取升级事件"""
        events = []
        for i in range(1, len(memory)):
            prev = memory[i - 1]
            curr = memory[i]
            if prev.sub_type != curr.sub_type:
                events.append({
                    "from_level": prev.sub_type,
                    "to_level": curr.sub_type,
                    "trigger_signal": curr.signal_received,
                    "timestamp": curr.created_at.isoformat(),
                })
        return events
    
    async def _persist_intervention_context(
        self,
        session_id: str,
        student_id: str,
        problem: str,
        student_steps: List[StudentStep],
        mainline_solution: List[SolutionStep],
        response: InterventionResponse,
    ) -> None:
        """持久化干预会话上下文到 MongoDB"""
        context = {
            "session_id": session_id,
            "student_id": student_id,
            "problem": {
                "original": problem,
                "brief": problem[:100] + "..." if len(problem) > 100 else problem,
            },
            "mainline_solution": [s.model_dump() for s in mainline_solution],
            "student_steps": [s.model_dump() for s in student_steps],
            "dimension_result": response.dimension_result.model_dump() if response.dimension_result else None,
            "current_level": {
                "sub_type": response.current_hint.sub_type if response.current_hint else None,
                "level": response.current_hint.level if response.current_hint else 0,
                "description": self._get_level_description(response.current_hint.sub_type) if response.current_hint else "",
            },
            "intervention_memory": [],
            "escalation_path": {
                "path_taken": [response.current_hint.sub_type] if response.current_hint else [],
                "current_position": 0,
                "max_level_reached": response.current_hint.level if response.current_hint else 0,
            },
            "status": response.session_status.value,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "ended_at": None,
        }
        
        await self.mongodb["intervention_contexts"].update_one(
            {"session_id": session_id},
            {"$set": context},
            upsert=True,
        )
    
    async def _update_intervention_context(
        self,
        session_id: str,
        new_event: Dict,
    ) -> None:
        """更新干预会话上下文，追加新的干预事件"""
        await self.mongodb["intervention_contexts"].update_one(
            {"session_id": session_id},
            {
                "$push": {"intervention_memory": new_event},
                "$set": {
                    "updated_at": datetime.utcnow(),
                    "current_level": {
                        "sub_type": new_event["sub_type"],
                        "level": new_event["level"],
                        "description": self._get_level_description(new_event["sub_type"]),
                    },
                },
            },
        )
        
        # 更新升级路径
        await self.mongodb["intervention_contexts"].update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "escalation_path.path_taken": new_event.get("path_taken", []),
                    "escalation_path.current_position": new_event.get("current_position", 0),
                    "escalation_path.max_level_reached": max(
                        new_event.get("max_level_reached", 0),
                        new_event.get("level", 0),
                    ),
                },
            },
        )
    
    async def _get_intervention_context(self, session_id: str) -> Optional[InterventionContext]:
        """从 MongoDB 获取干预会话上下文"""
        doc = await self.mongodb["intervention_contexts"].find_one(
            {"session_id": session_id}
        )
        if doc is None:
            return None
        
        # 移除 MongoDB _id 字段
        doc.pop("_id", None)
        return InterventionContext(**doc)
    
    async def _finalize_intervention_session(
        self,
        session_id: str,
        final_status: FinalStatus,
        summary: SessionSummary,
    ) -> None:
        """结束干预会话"""
        await self.mongodb["intervention_contexts"].update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "status": final_status.value,
                    "ended_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "session_summary": summary.model_dump(),
                },
            },
        )
    
    def _get_level_description(self, sub_type: SubType) -> str:
        """获取提示级别的描述"""
        descriptions = {
            "R1": "最低级别资源提示：提供最基本的步骤指引",
            "R2": "低级资源提示：增强的步骤指导",
            "R3": "中级资源提示：接近直接指导",
            "R4": "高级资源提示：几乎完整的答案",
            "M1": "最低级别元认知提示：基础自我监控引导",
            "M2": "低级元认知提示：增强的自我反思引导",
            "M3": "中级元认知提示：策略性自我反思",
            "M4": "高级元认知提示：深度自我反思引导",
            "M5": "最高级别元认知提示：最高认知水平的元认知引导",
        }
        return descriptions.get(sub_type, "")
    
    # ==================== Health Check Helpers ====================
    
    def _check_mongodb_health(self) -> Dict:
        """检查 MongoDB 连接状态"""
        import time
        try:
            start = time.time()
            self.mongodb.command("ping")
            latency = int((time.time() - start) * 1000)
            return {"connected": True, "latency_ms": latency}
        except Exception as e:
            return {"connected": False, "error": str(e)}
    
    def _check_llm_health(self) -> Dict:
        """检查 LLM 服务可用性"""
        import time
        try:
            start = time.time()
            # 简单测试调用
            self.llm.generate(prompt="test", max_tokens=1)
            latency = int((time.time() - start) * 1000)
            return {
                "available": True,
                "provider": self.llm.provider_name,
                "model_in_use": self.llm.model_name,
                "latency_ms": latency,
            }
        except Exception as e:
            return {"available": False, "error": str(e)}
    
    def _check_redis_health(self) -> Dict:
        """检查 Redis 连接状态"""
        import time
        try:
            start = time.time()
            self.redis.ping()
            latency = int((time.time() - start) * 1000)
            return {"connected": True, "latency_ms": latency}
        except Exception as e:
            return {"connected": False, "error": str(e)}
    
    def _check_vector_db_health(self) -> Dict:
        """检查矢量数据库连接状态"""
        try:
            return {
                "connected": self.vector_db.is_connected(),
                "index_loaded": self.vector_db.is_index_loaded(),
            }
        except Exception:
            return {"connected": False, "index_loaded": False}
    
    def _get_uptime_seconds(self) -> int:
        """获取服务运行时间（秒）"""
        if not hasattr(self, "_start_time"):
            self._start_time = datetime.utcnow()
        return int((datetime.utcnow() - self._start_time).total_seconds())
    
    # ==================== Cache Helpers ====================
    
    def _get_cached_context(self, session_id: str) -> Optional[InterventionContext]:
        """从缓存获取会话上下文"""
        try:
            cached = self.redis.get(f"intervention_context:{session_id}")
            if cached:
                return InterventionContext.parse_raw(cached)
        except Exception:
            pass
        return None
    
    def _cache_context(self, session_id: str, context: InterventionContext) -> None:
        """将会话上下文存入缓存"""
        try:
            self.redis.setex(
                f"intervention_context:{session_id}",
                3600,  # 1小时过期
                context.json(),
            )
        except Exception:
            pass
```

---

## 5. Error Codes (错误代码)

### 5.1 错误码定义表

| 错误码 | HTTP 状态码 | 描述 | 可能原因 | 处理建议 |
|--------|-------------|------|----------|----------|
| `SESSION_NOT_FOUND` | 404 | 指定的干预会话不存在 | 会话 ID 错误、会话已过期、数据被清理 | 检查 session_id 是否正确，确认会话未超过保留期限 |
| `LLM_API_ERROR` | 500 | LLM API 调用失败 | 网络问题、API 限流、API Key 无效、模型服务不可用 | 检查网络连接、API Key 配置、查看 LLM 服务商状态页面 |
| `LLM_PARSE_ERROR` | 500 | LLM 响应解析失败 | LLM 返回格式不符合预期、响应被截断、内容被安全过滤 | 重试请求、检查提示模板、增加解析容错逻辑 |
| `GUARDRAIL_BLOCKED` | 200 | 提示内容被安全门拦截 | LLM 生成的提示包含不当内容、级别设置过高、可能泄露答案 | 自动降级到更基础的提示级别、记录拦截事件供人工审核 |
| `MAX_ESCALATION` | 200 | 已达到最大干预级别 | 学生持续未取得进展、问题难度超出系统能力范围 | 记录升级路径、触发人工介入流程、考虑问题降级或跳过 |
| `INVALID_SIGNAL` | 422 | 无效的反馈信号 | signal 参数值不在允许范围内 | 检查 signal 值是否为 PROGRESSED/NOT_PROGRESSED/DISMISSED |
| `INVALID_SESSION_STATE` | 409 | 会话状态不允许此操作 | 尝试结束已结束的会话、重复调用 start | 检查当前会话状态、确保操作符合状态转换规则 |
| `DIMENSION_SWITCH_COOLDOWN` | 409 | 维度切换冷却期未过 | 短时间内频繁切换维度 | 等待冷却期结束或提供低级别提示 |
| `MONGODB_CONNECTION_ERROR` | 503 | MongoDB 连接失败 | MongoDB 服务不可用、网络问题、认证失败 | 检查 MongoDB 服务状态、网络连接、认证配置 |
| `REDIS_CONNECTION_ERROR` | 503 | Redis 连接失败 | Redis 服务不可用、网络问题 | 检查 Redis 服务状态、考虑降级到无缓存模式 |
| `VECTOR_DB_ERROR` | 503 | 矢量数据库错误 | 连接失败、索引未加载、查询超时 | 检查矢量数据库服务状态、重载索引 |
| `BREAKPOINT_LOCATOR_ERROR` | 500 | 断点定位器执行失败 | 规则引擎错误、输入数据格式错误 | 检查 student_steps 和 mainline_solution 格式 |
| `HINT_GENERATION_TIMEOUT` | 504 | 提示生成超时 | LLM 响应过慢、网络延迟高 | 增加超时阈值、使用缓存的通用提示作为降级 |
| `CONTEXT_TOO_LONG` | 422 | 上下文长度超限 | 问题描述或解题步骤过长 | 截断或压缩输入内容、分段处理 |
| `UNAUTHORIZED` | 401 | 未授权访问 | 缺少或无效的认证 token | 检查 Authorization 请求头、刷新认证 token |
| `RATE_LIMIT_EXCEEDED` | 429 | 请求频率超限 | 短时间内请求过多 | 实施请求限流、使用指数退避重试 |

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
| `LLM_API_ERROR` | 是（最多3次，指数退避） | 使用缓存提示模板 | 是（连续失败时） |
| `LLM_PARSE_ERROR` | 是（最多2次） | 使用备用解析器 | 是 |
| `GUARDRAIL_BLOCKED` | 否 | 自动降级2级 | 记录但不告警 |
| `MONGODB_CONNECTION_ERROR` | 是（健康检查时） | 降级到只读缓存 | 是 |
| `REDIS_CONNECTION_ERROR` | 否 | 降级到无缓存模式 | 记录但不告警 |
| 其他错误 | 否 | 取决于具体错误 | 取决于严重程度 |

---

## 6. MongoDB Collections (MongoDB 数据集合)

### 6.1 intervention_contexts 集合

**用途**: 存储每个干预会话的完整上下文数据，是系统的主要状态存储。

**文档结构**:
```json
{
  "_id": "ObjectId",
  "session_id": "string (索引, 唯一)",
  "student_id": "string (索引)",
  "problem": {
    "original": "string (原始问题描述)",
    "brief": "string (问题摘要, 前100字符)"
  },
  "mainline_solution": [
    {
      "step_id": "string",
      "content": "string",
      "expected_response": "string"
    }
  ],
  "student_steps": [
    {
      "step_id": "string",
      "content": "string",
      "timestamp": "ISODate",
      "is_final": "boolean"
    }
  ],
  "dimension_result": {
    "dimension": "RESOURCE | METACOGNITIVE",
    "confidence": "float",
    "reasoning": "string",
    "alternative_dimension": {
      "dimension": "Dimension",
      "confidence": "float"
    },
    "routing_evidence": {
      "student_behavior_patterns": ["string"],
      "cognitive_indicators": ["string"]
    }
  },
  "current_level": {
    "sub_type": "SubType",
    "level": "integer",
    "description": "string"
  },
  "intervention_memory": [
    {
      "intervention_id": "string",
      "sequence": "integer",
      "breakpoint_location": {
        "position": "integer",
        "breakpoint_type": "BreakpointType",
        "breakpoint_reason": "string",
        "missing_knowledge": "string"
      },
      "dimension": "Dimension",
      "level": "integer",
      "sub_type": "SubType",
      "hint_content": "string",
      "signal_received": "FrontendSignal",
      "student_input_at_signal": "string",
      "created_at": "ISODate",
      "guardrail_passed": "boolean"
    }
  ],
  "escalation_path": {
    "path_taken": ["SubType"],
    "current_position": "integer",
    "max_level_reached": "integer"
  },
  "status": "SessionStatus",
  "session_summary": {
    "total_interventions": "integer",
    "final_level": "SubType",
    "dimension_switches": "integer",
    "outcome": "FinalStatus",
    "resolution_time_seconds": "integer",
    "breakpoint_types_encountered": ["BreakpointType"],
    "intervention_path": ["SubType"],
    "guardrail_blocks": "integer",
    "dimension_distribution": {
      "RESOURCE": "integer",
      "METACOGNITIVE": "integer"
    }
  },
  "created_at": "ISODate",
  "updated_at": "ISODate",
  "ended_at": "ISODate | null"
}
```

**索引设计**:
```javascript
// 主键索引
{ "session_id": 1 }  // unique: true

// 查询优化索引
{ "student_id": 1, "created_at": -1 }  // 按学生 ID 查询其所有会话
{ "status": 1, "created_at": -1 }  // 查询特定状态的所有会话
{ "ended_at": 1 }  // TTL 索引字段（如果使用 TTL）

// 聚合分析索引
{ "dimension_result.dimension": 1, "status": 1 }
{ "session_summary.outcome": 1, "session_summary.total_interventions": 1 }
```

**集合配置建议**:
- `validator`: 启用模式验证确保数据完整性
- `expireAfterSeconds`: 根据业务需求设置会话保留期限（建议 30-90 天）
- `collation`: `{ locale: "en", strength: 2 }` 用于不区分大小写的查询

---

### 6.2 interventions 集合

**用途**: 存储所有干预事件的扁平化记录，用于审计、分析和模型训练数据收集。

**文档结构**:
```json
{
  "_id": "ObjectId",
  "session_id": "string (索引)",
  "intervention_id": "string (唯一)",
  "student_id": "string (索引)",
  "problem_brief": "string (问题摘要)",
  "breakpoint_location": {
    "position": "integer",
    "breakpoint_type": "BreakpointType",
    "breakpoint_reason": "string"
  },
  "dimension": "Dimension",
  "level": "integer",
  "sub_type": "SubType",
  "hint_content": "string",
  "hint_approach": "HintApproach",
  "signal_received": "FrontendSignal | null",
  "student_input": "string",
  "guardrail_passed": "boolean",
  "guardrail_details": {
    "rule_check": {
      "safe_content": "boolean",
      "appropriate_level": "boolean",
      "no_solution_leak": "boolean"
    },
    "llm_review": {
      "approved": "boolean",
      "concerns": ["string"],
      "suggestions": ["string"]
    }
  },
  "llm_usage": {
    "dimension_router": {
      "tokens_used": "integer",
      "latency_ms": "integer"
    },
    "sub_type_decider": {
      "tokens_used": "integer",
      "latency_ms": "integer"
    },
    "hint_generator": {
      "tokens_used": "integer",
      "latency_ms": "integer"
    },
    "output_guardrail": {
      "tokens_used": "integer",
      "latency_ms": "integer"
    }
  },
  "created_at": "ISODate (索引)",
  "escalation_trigger": "string | null"
}
```

**索引设计**:
```javascript
// 主键索引
{ "_id": 1 }

// 查询优化索引
{ "session_id": 1, "created_at": -1 }
{ "student_id": 1, "created_at": -1 }
{ "sub_type": 1, "created_at": -1 }
{ "dimension": 1, "created_at": -1 }
{ "signal_received": 1, "created_at": -1 }

// 分析聚合索引
{ "breakpoint_type": 1, "dimension": 1, "outcome": 1 }
{ "guardrail_passed": 1, "created_at": -1 }
```

**TTL 策略**:
- 该集合数据保留期可设置为 180-365 天（用于长期分析）
- 使用 `created_at` 字段作为 TTL 索引

---

### 6.3 辅助函数

```python
# MongoDB 集合初始化脚本
MONGODB_SETUP_SCRIPT = """
// 创建 intervention_contexts 集合
db.createCollection("intervention_contexts", {
   validator: {
      $jsonSchema: {
         bsonType: "object",
         required: ["session_id", "student_id", "status", "created_at", "updated_at"],
         properties: {
            session_id: { bsonType: "string" },
            student_id: { bsonType: "string" },
            problem: {
               bsonType: "object",
               required: ["original"],
               properties: {
                  original: { bsonType: "string" },
                  brief: { bsonType: "string" }
               }
            },
            status: {
               enum: ["IN_PROGRESS", "SOLVED", "MAX_ESCALATION", "ABANDONED"]
            },
            dimension_result: {
               bsonType: "object",
               properties: {
                  dimension: { enum: ["RESOURCE", "METACOGNITIVE"] },
                  confidence: { bsonType: "double" },
                  reasoning: { bsonType: "string" }
               }
            },
            intervention_memory: { bsonType: "array" },
            escalation_path: {
               bsonType: "object",
               properties: {
                  path_taken: { bsonType: "array" },
                  current_position: { bsonType: "int" },
                  max_level_reached: { bsonType: "int" }
               }
            }
         }
      }
   },
   validationLevel: "moderate",
   validationAction: "warn"
});

// 创建索引
db.intervention_contexts.createIndex({ "session_id": 1 }, { unique: true });
db.intervention_contexts.createIndex({ "student_id": 1, "created_at": -1 });
db.intervention_contexts.createIndex({ "status": 1, "created_at": -1 });

// 创建 interventions 集合
db.createCollection("interventions", {
   validator: {
      $jsonSchema: {
         bsonType: "object",
         required: ["session_id", "intervention_id", "student_id", "created_at"],
         properties: {
            session_id: { bsonType: "string" },
            intervention_id: { bsonType: "string" },
            student_id: { bsonType: "string" },
            sub_type: { 
               enum: ["R1", "R2", "R3", "R4", "M1", "M2", "M3", "M4", "M5"] 
            },
            dimension: { enum: ["RESOURCE", "METACOGNITIVE"] },
            breakpoint_type: {
               enum: ["MISSING_STEP", "WRONG_DIRECTION", "INCOMPLETE_STEP", "STUCK", "NO_BREAKPOINT"]
            },
            signal_received: {
               enum: ["PROGRESSED", "NOT_PROGRESSED", "DISMISSED", null]
            }
         }
      }
   }
});

// 创建索引
db.interventions.createIndex({ "session_id": 1, "created_at": -1 });
db.interventions.createIndex({ "student_id": 1, "created_at": -1 });
db.interventions.createIndex({ "sub_type": 1, "created_at": -1 });
db.interventions.createIndex({ "dimension": 1, "created_at": -1 });

// 设置 TTL（可选，365天后自动删除）
// db.interventions.createIndex({ "created_at": 1 }, { expireAfterSeconds: 31536000 });
"""
```

---

## 附录 A: 五节点管道详细说明

### A.1 BreakpointLocator (断点定位器)

**类型**: 纯规则引擎，无 LLM 依赖

**输入**:
- `student_steps`: 学生已完成的解题步骤
- `mainline_solution`: 标准解法步骤

**输出**: `BreakpointLocation` 对象

**规则集**:

```python
class BreakpointLocator:
    """
    断点定位规则引擎
    
    规则优先级（从高到低）:
    1. WRONG_DIRECTION: 检测到明显方向错误
    2. MISSING_STEP: 检测到必要步骤缺失
    3. INCOMPLETE_STEP: 检测到步骤不完整
    4. STUCK: 检测到学生长时间无进展
    5. NO_BREAKPOINT: 未检测到断点
    """
    
    RULES = [
        # 规则1: 方向错误检测
        {
            "name": "wrong_direction_detection",
            "priority": 1,
            "condition": lambda student, solution: _check_wrong_direction(student, solution),
            "breakpoint_type": BreakpointType.WRONG_DIRECTION,
        },
        # 规则2: 步骤缺失检测
        {
            "name": "missing_step_detection",
            "priority": 2,
            "condition": lambda student, solution: _check_missing_step(student, solution),
            "breakpoint_type": BreakpointType.MISSING_STEP,
        },
        # 规则3: 步骤不完整检测
        {
            "name": "incomplete_step_detection",
            "priority": 3,
            "condition": lambda student, solution: _check_incomplete_step(student, solution),
            "breakpoint_type": BreakpointType.INCOMPLETE_STEP,
        },
        # 规则4: 卡住检测（时间维度）
        {
            "name": "stuck_detection",
            "priority": 4,
            "condition": lambda student, solution: _check_stuck(student),
            "breakpoint_type": BreakpointType.STUCK,
        },
    ]
    
    def locate(self, student_steps, mainline_solution) -> BreakpointLocation:
        # 按优先级遍历规则
        # 返回第一个匹配的断点位置和类型
        # 如果无匹配，返回 NO_BREAKPOINT
```

**相似度计算**: 使用编辑距离 (Levenshtein Distance) 和语义嵌入结合的方法

---

### A.2 DimensionRouter (维度路由器)

**类型**: LLM 驱动的二分类器

**输入**:
- `problem`: 问题描述
- `student_steps`: 学生步骤
- `breakpoint_location`: 断点位置

**输出**: `DimensionResult` (RESOURCE 或 METACOGNITIVE + 置信度)

**Prompt 模板**:

```
你是一位专业的教育心理学专家，负责判断学生在解题过程中遇到困难时，
最适合的干预维度是资源型(RESOURCE)还是元认知型(METACOGNITIVE)。

问题背景: {problem}

学生当前步骤:
{student_steps_formatted}

检测到的断点:
- 位置: 第 {position} 步
- 类型: {breakpoint_type}
- 原因: {breakpoint_reason}

请分析学生当前状态，判断:
1. RESOURCE (资源型): 学生需要具体的知识、步骤指导、工具支持
   特征: 不知道下一步怎么做、缺乏必要知识、步骤执行困难
   
2. METACOGNITIVE (元认知型): 学生需要自我监控、策略反思、计划调整的引导
   特征: 知道怎么做但效率低、缺乏策略意识、自我评估能力不足

请以 JSON 格式返回:
{{
  "dimension": "RESOURCE" 或 "METACOGNITIVE",
  "confidence": 0.0-1.0 的置信度,
  "reasoning": "判断理由，100-200字",
  "alternative_dimension": {{
    "dimension": "备选维度",
    "confidence": 备选置信度
  }}
}}
```

---

### A.3 SubTypeDecider (子类型决策器)

**类型**: LLM 驱动的 9 级分类器

**输入**:
- `problem`: 问题描述
- `dimension`: 维度结果 (RESOURCE/METACOGNITIVE)
- `breakpoint_location`: 断点位置
- `confidence`: 维度判定置信度

**输出**: `SubType` (R1-R4 或 M1-M5)

**级别定义**:

| 维度 | 级别 | 描述 | 典型提示 |
|------|------|------|----------|
| R | R1 | 最基础指导 | "你可以试着..." |
| R | R2 | 增强指导 | "你需要先...然后..." |
| R | R3 | 接近直接 | "下一步应该是..." |
| R | R4 | 几乎完整 | 给出大部分答案 |
| M | M1 | 基础元认知 | "你对自己的解题过程满意吗？" |
| M | M2 | 增强元认知 | "你能描述一下你的解题思路吗？" |
| M | M3 | 策略元认知 | "有没有其他可能的解题路径？" |
| M | M4 | 深度元认知 | "如果换一种方法，你会怎么做？" |
| M | M5 | 最高元认知 | "你能反思一下整个解题过程吗？" |

---

### A.4 HintGeneratorV2 (提示生成器 V2)

**类型**: LLM 驱动的自然语言生成

**输入**:
- `problem`: 问题描述
- `sub_type`: 目标子类型
- `breakpoint_type`: 断点类型

**输出**: `CurrentHint` (包含 content、approach_used 等)

**策略选择**:
- `scaffolding`: 脚手架策略，适用于 R1-R2
- `probing`: 探测策略，适用于 R3、M2-M3
- `direct_guidance`: 直接指导，适用于 R4
- `metacognitive_questioning`: 元认知提问，适用于 M1、M4-M5

---

### A.5 OutputGuardrail (输出安全门)

**类型**: 规则引擎 + LLM 双层过滤

**第一层 - 规则检查**:
```python
RULE_CHECKS = [
    {"name": "safe_content", "check": lambda x: _check_no_profanity(x)},
    {"name": "appropriate_level", "check": lambda x, lvl: _check_level_appropriate(x, lvl)},
    {"name": "no_solution_leak", "check": lambda x, sol: _check_no_direct_answer(x, sol)},
]
```

**第二层 - LLM 审核**:
```
请审查以下提示内容是否适合直接交给学生:

提示内容: {hint_content}
当前级别: {sub_type}

检查标准:
1. 内容是否安全、无不当信息
2. 级别是否适当（不过于简单也不过于直接）
3. 是否泄露了问题的直接答案
4. 是否符合教育伦理

请以 JSON 格式返回:
{{
  "approved": true/false,
  "concerns": ["问题列表，如果有"],
  "suggestions": ["修改建议，如果有"]
}}
```

---

## 附录 B: 版本变更记录

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 2.0.0 | 2026-03-30 | 初始版本，定义完整五节点管道架构 |
| 1.0.0 | 2025-01-15 | 早期原型版本（仅包含单节点提示生成） |

---

*本文档由 Socrates 系统自动生成，如有问题请联系系统维护团队。*
