# Module 1 接口文档：Organized Solution Mainline Generation

## 概述

本文档描述高中数学 tutoring system（ tutoring 系统）中 Module 1 的接口规范。Module 1 是五模块 pipeline 的入口点，负责将原始数学问题文本转换为结构化的解题主线路（organized solution mainline）。

---

## 1. 模块定位（Module Position）

### 1.1 架构位置

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户输入                                  │
│                   原始数学问题文本 (LaTeX/纯文本)                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Module 1: Mainline Generator                 │
│              Organized Solution Mainline Generation              │
│  - 接收原始问题                                                  │
│  - 生成结构化解题步骤                                             │
│  - 输出解题主线路 (JSON)                                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Module 2: Breakpoint Locator                  │
│                  (读取 Module 1 输出的 mainline steps)             │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 输入输出定义

| 属性 | 说明 |
|------|------|
| **接收（输入）** | 原始数学问题文本，支持 LaTeX 格式或纯文本 |
| **输出（产出）** | 组织化解题主线路（JSON 结构） |
| **下游模块** | Module 2（Breakpoint Locator）读取 `solution_steps` 中的步骤，定位潜在断点 |

### 1.3 核心职责

Module 1 承担以下职责：

1. **问题理解**：对输入问题进行语义理解，输出"这题怎么看"
2. **步骤拆解**：将解题过程拆解为可执行的中介步骤（Intermediate Steps）
3. **方法总结**：提炼本题的核心思维动作和方法论，留下"这题留下什么方法"
4. **断点预判**（可选）：提供潜在困难点，辅助 Module 2 定位断点

---

## 2. API 接口（API Endpoint）

### 2.1 端点信息

| 属性 | 值 |
|------|---|
| **方法** | `POST` |
| **路径** | `/api/v1/mainline/generate` |
| **内容类型** | `application/json` |
| **认证** | Bearer Token（预留） |

### 2.2 请求（Request）

```json
{
  "problem": "求证：任意奇数的平方减1能被8整除",
  "options": {
    "temperature": 0.7,
    "max_tokens": 2048,
    "include_breakpoint_hints": true
  }
}
```

#### 请求字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `problem` | `string` | **是** | 数学问题文本，支持 LaTeX 格式，如 `x^2 + 2x + 1 = 0` 或中文描述 `"求 x 的值"` |
| `options` | `object` | 否 | 生成选项 |
| `options.temperature` | `number` | 否 | LLM 温度参数，取值范围 `[0.0, 1.0]`，默认 `0.7` |
| `options.max_tokens` | `integer` | 否 | 最大生成 token 数，默认 `2048` |
| `options.include_breakpoint_hints` | `boolean` | 否 | 是否包含断点提示，默认 `true` |

### 2.3 成功响应（200 OK）

```json
{
  "success": true,
  "data": {
    "problem_understanding": "这道题要证明任意奇数平方减1的整除性...",
    "solution_steps": [
      {
        "step_id": 1,
        "action": "观察结构",
        "description": "设任意奇数为 2k+1",
        "reasoning": "奇数的一般形式，便于代数运算",
        "key_insight": null
      },
      {
        "step_id": 2,
        "action": "化生为熟",
        "description": "(2k+1)² - 1 = 4k² + 4k = 4k(k+1)",
        "reasoning": "平方展开后消去常数项，构造出 k(k+1) 的形式",
        "key_insight": "关键：k和k+1是连续整数，必有一个是偶数，所以 k(k+1) 能被2整除"
      }
    ],
    "method_summary": "本题的核心思维动作是：先用代数形式化简，再利用奇偶性分析。关键突破口是构造 k(k+1)。",
    "breakpoint_hints": [
      {
        "position": 1,
        "breakpoint_type": "MISSING_STEP",
        "potential_difficulty": "学生可能不知道如何表示奇数",
        "suggested_dimension": "RESOURCE"
      }
    ]
  },
  "metadata": {
    "model": "qwen-turbo",
    "latency_ms": 1234,
    "tokens_used": 856
  }
}
```

#### 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | `boolean` | 请求是否成功 |
| `data` | `object` | 主线路数据 |
| `data.problem_understanding` | `string` | 问题理解，即"这题怎么看" |
| `data.solution_steps` | `array` | 解题步骤数组 |
| `data.method_summary` | `string` | 方法总结，即"这题留下什么方法" |
| `data.breakpoint_hints` | `array` | 断点提示数组（可选，当 `options.include_breakpoint_hints=true` 时存在） |
| `metadata` | `object` | 元信息 |
| `metadata.model` | `string` | 使用的 LLM 模型名称 |
| `metadata.latency_ms` | `integer` | 请求耗时（毫秒） |
| `metadata.tokens_used` | `integer` | 消耗的 token 数量 |

### 2.4 错误响应（500 Internal Server Error）

```json
{
  "success": false,
  "error": {
    "code": "LLM_PARSE_ERROR",
    "message": "模型输出无法解析为 JSON",
    "details": "原始输出：..."
  }
}
```

#### 错误响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | `boolean` | 固定为 `false` |
| `error` | `object` | 错误详情 |
| `error.code` | `string` | 错误码，见本文档第 5 节 |
| `error.message` | `string` | 错误信息的可读描述 |
| `error.details` | `string` | 详细信息（可选），如原始输出、堆栈等 |

---

## 3. 数据模型（Data Models）

### 3.1 TypeScript 类型定义

```typescript
// ========== 请求 ==========

/**
 * 生成主线路的请求选项
 */
interface GenerateMainlineOptions {
  /**
   * LLM 温度参数，控制随机性
   * @default 0.7
   */
  temperature?: number;

  /**
   * 最大生成 token 数
   * @default 2048
   */
  max_tokens?: number;

  /**
   * 是否包含断点提示（供 Module 2 使用）
   * @default true
   */
  include_breakpoint_hints?: boolean;
}

/**
 * 生成主线路的请求体
 */
interface GenerateMainlineRequest {
  /**
   * 数学问题文本，支持 LaTeX 或纯文本
   * @example "求证：任意奇数的平方减1能被8整除"
   * @example "已知 a^2 + b^2 = c^2，求证 ..."
   */
  problem: string;

  /**
   * 可选的生成选项
   */
  options?: GenerateMainlineOptions;
}

// ========== 响应 ==========

/**
 * 单个解题步骤
 */
interface SolutionStep {
  /**
   * 步骤编号，从 1 开始
   */
  step_id: number;

  /**
   * 思维动作类型
   * - 观察结构：识别问题的形式、结构特征
   * - 寻找联系：建立已知与未知的关联
   * - 化生为熟：将陌生问题转化为熟悉形式
   * - 抓关键限制：抓住问题的约束条件
   * - 适时分类：分类讨论
   * - 构造与替换：构造函数、换元等技巧
   * - 特殊化边界化回验：验证边界情况
   * - 结果审查：检查答案的合理性
   */
  action:
    | "观察结构"
    | "寻找联系"
    | "化生为熟"
    | "抓关键限制"
    | "适时分类"
    | "构造与替换"
    | "特殊化边界化回验"
    | "结果审查";

  /**
   * 这一步做了什么（尽量少公式，多描述）
   * @example "设任意奇数为 2k+1"
   */
  description: string;

  /**
   * 为什么要这样做（关键）
   * @example "奇数的一般形式，便于代数运算"
   */
  reasoning: string;

  /**
   * 如果是关键突破口，注明；否则为 null
   */
  key_insight: string | null;
}

/**
 * 断点提示（供 Module 2 使用）
 */
interface BreakpointHint {
  /**
   * 对应的 step_id
   */
  position: number;

  /**
   * 断点类型
   * - MISSING_STEP：缺少必要步骤
   * - WRONG_DIRECTION：解题方向错误
   * - INCOMPLETE_STEP：步骤不完整
   */
  breakpoint_type: "MISSING_STEP" | "WRONG_DIRECTION" | "INCOMPLETE_STEP";

  /**
   * 潜在困难描述
   * @example "学生可能不知道如何表示奇数"
   */
  potential_difficulty: string;

  /**
   * 建议的辅导维度
   * - RESOURCE：资源型辅助（提供背景知识、公式等）
   * - METACOGNITIVE：元认知型辅助（引导反思、监控解题过程）
   */
  suggested_dimension: "RESOURCE" | "METACOGNITIVE";
}

/**
 * 完整的解题主线路
 */
interface SolutionMainline {
  /**
   * 问题理解，即"这题怎么看"
   */
  problem_understanding: string;

  /**
   * 解题步骤数组（有序）
   */
  solution_steps: SolutionStep[];

  /**
   * 方法总结，即"这题留下什么方法"
   */
  method_summary: string;

  /**
   * 断点提示数组（可选）
   * 仅当请求中 `options.include_breakpoint_hints=true` 时存在
   */
  breakpoint_hints?: BreakpointHint[];
}

/**
 * API 成功响应
 */
interface GenerateMainlineResponse {
  success: true;
  data: SolutionMainline;
  metadata: {
    /**
     * 使用的 LLM 模型
     * @example "qwen-turbo"
     */
    model: string;

    /**
     * 请求耗时（毫秒）
     */
    latency_ms: number;

    /**
     * 消耗的 token 总数
     */
    tokens_used: number;
  };
}

/**
 * API 错误响应
 */
interface ErrorResponse {
  success: false;
  error: {
    /**
     * 错误码
     */
    code: string;

    /**
     * 错误信息
     */
    message: string;

    /**
     * 详细信息（可选）
     */
    details?: string;
  };
}
```

### 3.2 Python Pydantic 模型（参考实现）

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from enum import Enum


class SolutionAction(str, Enum):
    """思维动作类型"""
    OBSERVE_STRUCTURE = "观察结构"
    FIND_CONNECTIONS = "寻找联系"
    FAMILIARIZE = "化生为熟"
    GRAB_CONSTRAINTS = "抓关键限制"
    CLASSIFY = "适时分类"
    CONSTRUCT_REPLACE = "构造与替换"
    SPECIALIZE_CHECK = "特殊化边界化回验"
    REVIEW_RESULT = "结果审查"


class BreakpointType(str, Enum):
    """断点类型"""
    MISSING_STEP = "MISSING_STEP"
    WRONG_DIRECTION = "WRONG_DIRECTION"
    INCOMPLETE_STEP = "INCOMPLETE_STEP"


class SuggestedDimension(str, Enum):
    """建议辅导维度"""
    RESOURCE = "RESOURCE"
    METACOGNITIVE = "METACOGNITIVE"


class GenerateOptions(BaseModel):
    """生成选项"""
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(default=2048, ge=1)
    include_breakpoint_hints: bool = Field(default=True)


class GenerateMainlineRequest(BaseModel):
    """生成主线路请求"""
    problem: str = Field(..., description="数学问题文本，支持 LaTeX 或纯文本")
    options: Optional[GenerateOptions] = Field(default=None)


class SolutionStep(BaseModel):
    """单个解题步骤"""
    step_id: int = Field(..., ge=1, description="步骤编号，从 1 开始")
    action: SolutionAction = Field(..., description="思维动作类型")
    description: str = Field(..., description="这一步做了什么")
    reasoning: str = Field(..., description="为什么要这样做")
    key_insight: Optional[str] = Field(default=None, description="关键突破口")


class BreakpointHint(BaseModel):
    """断点提示"""
    position: int = Field(..., ge=1, description="对应的 step_id")
    breakpoint_type: BreakpointType = Field(..., description="断点类型")
    potential_difficulty: str = Field(..., description="潜在困难描述")
    suggested_dimension: SuggestedDimension = Field(..., description="建议辅导维度")


class SolutionMainline(BaseModel):
    """解题主线路"""
    problem_understanding: str = Field(..., description="问题理解：'这题怎么看'")
    solution_steps: List[SolutionStep] = Field(..., description="解题步骤数组")
    method_summary: str = Field(..., description="方法总结：'这题留下什么方法'")
    breakpoint_hints: Optional[List[BreakpointHint]] = Field(
        default=None,
        description="断点提示数组（可选）"
    )


class ResponseMetadata(BaseModel):
    """响应元信息"""
    model: str = Field(..., description="LLM 模型名称")
    latency_ms: int = Field(..., ge=0, description="请求耗时（毫秒）")
    tokens_used: int = Field(..., ge=0, description="消耗 token 数")


class GenerateMainlineResponse(BaseModel):
    """成功响应"""
    success: Literal[True] = Field(default=True)
    data: SolutionMainline
    metadata: ResponseMetadata


class ErrorDetail(BaseModel):
    """错误详情"""
    code: str = Field(..., description="错误码")
    message: str = Field(..., description="错误信息")
    details: Optional[str] = Field(default=None, description="详细信息")


class ErrorResponse(BaseModel):
    """错误响应"""
    success: Literal[False] = Field(default=False)
    error: ErrorDetail
```

---

## 4. 内部服务类（Internal Service Class）

### 4.1 类接口设计

```python
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import asyncio


class LLMClient(ABC):
    """LLM 客户端抽象（支持切换不同 LLM provider）"""

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        发送聊天请求到 LLM

        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大 token 数

        Returns:
            LLM 原始输出文本
        """
        pass


class QwenTurboClient(LLMClient):
    """通义千问 Turbo 客户端实现"""

    def __init__(self, api_key: str, base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"):
        self.api_key = api_key
        self.base_url = base_url

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """调用通义千问 Turbo API"""
        import aiohttp
        import json

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "qwen-turbo",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    raise LLMAPIError(f"API 返回错误状态码: {resp.status}")
                result = await resp.json()
                return result["choices"][0]["message"]["content"]


class MainlineGenerator:
    """
    组织化解题主线路生成器

    负责：
    1. 接收原始问题文本
    2. 构建 prompt
    3. 调用 LLM
    4. 解析和验证响应
    """

    def __init__(
        self,
        llm_client: LLMClient,
        output_validator: Optional["OutputValidator"] = None,
    ):
        """
        初始化生成器

        Args:
            llm_client: LLM 客户端实例
            output_validator: 输出验证器（可选）
        """
        self.llm = llm_client
        self.validator = output_validator or OutputValidator()

    async def generate(
        self,
        problem: str,
        options: Optional[GenerateOptions] = None,
    ) -> SolutionMainline:
        """
        生成组织化解题主线路

        Args:
            problem: 数学问题文本
            options: 生成选项

        Returns:
            SolutionMainline: 结构化的解题主线路

        Raises:
            LLMAPIError: LLM API 调用失败
            LLMParseError: JSON 解析失败
            ValidationError: 输出不符合质量标准
            TimeoutError: LLM 响应超时
        """
        options = options or GenerateOptions()

        # Step 1: 构建 prompt
        prompt = self._build_prompt(problem, options)

        # Step 2: 调用 LLM
        raw_text = await self._call_llm(prompt, options)

        # Step 3: 解析响应
        mainline = self._parse_response(raw_text)

        # Step 4: 验证输出质量
        if not self._validate_output(mainline):
            raise ValidationError("输出不符合质量标准：四任务未完全覆盖")

        return mainline

    def _build_prompt(self, problem: str, options: GenerateOptions) -> str:
        """
        构建 LLM prompt

        构建策略：
        - System prompt 定义角色和输出格式
        - User prompt 包含问题文本和具体要求
        """
        system_prompt = """你是一位专业的高中数学教练，负责将解题过程分解为清晰的思维步骤。

你需要完成以下四个任务：
1. 问题理解：简洁描述"这题怎么看"，即问题的核心和入手点
2. 步骤拆解：将解题过程分解为 3-8 个思维步骤，每个步骤包含：
   - action: 思维动作类型（观察结构/寻找联系/化生为熟/抓关键限制/适时分类/构造与替换/特殊化边界化回验/结果审查）
   - description: 这一步做了什么（尽量少公式，多描述）
   - reasoning: 为什么要这样做（关键）
   - key_insight: 如果是关键突破口则注明，否则为 null
3. 方法总结：提炼"这题留下什么方法"，核心思维动作是什么
4. 断点预判（可选）：预判学生可能遇到的困难点

输出格式：严格 JSON，不要包含任何其他文字。"""

        breakpoint_hint_instruction = ""
        if options.include_breakpoint_hints:
            breakpoint_hint_instruction = """
5. 断点预判：为每个可能出问题的步骤提供：
   - position: step_id
   - breakpoint_type: MISSING_STEP | WRONG_DIRECTION | INCOMPLETE_STEP
   - potential_difficulty: 潜在困难描述
   - suggested_dimension: RESOURCE | METACOGNITIVE"""

        user_prompt = f"""问题：{problem}

请严格按照以下 JSON 格式输出（必须包含所有字段）：
{{
  "problem_understanding": "问题理解...",
  "solution_steps": [
    {{
      "step_id": 1,
      "action": "思维动作类型",
      "description": "这一步做了什么",
      "reasoning": "为什么要这样做",
      "key_insight": "关键突破口或null"
    }}
  ],
  "method_summary": "方法总结..."{breakpoint_hint_instruction if options.include_breakpoint_hints else ""}
}}"""

        return f"System: {system_prompt}\n\nUser: {user_prompt}"

    async def _call_llm(self, prompt: str, options: GenerateOptions) -> str:
        """
        调用 LLM

        Args:
            prompt: 构建好的 prompt
            options: 生成选项

        Returns:
            LLM 原始输出文本

        Raises:
            LLMAPIError: API 调用失败
            TimeoutError: 响应超时（>30s）
        """
        import json

        messages = [{"role": "user", "content": prompt}]

        try:
            # 设置 30 秒超时
            raw_text = await asyncio.wait_for(
                self.llm.chat(
                    messages=messages,
                    temperature=options.temperature,
                    max_tokens=options.max_tokens,
                ),
                timeout=30.0,
            )
            return raw_text
        except asyncio.TimeoutError:
            raise TimeoutError("LLM 响应超时（>30s）")
        except Exception as e:
            # 最多重试 1 次
            try:
                raw_text = await asyncio.wait_for(
                    self.llm.chat(
                        messages=messages,
                        temperature=options.temperature,
                        max_tokens=options.max_tokens,
                    ),
                    timeout=30.0,
                )
                return raw_text
            except Exception:
                raise LLMAPIError(f"LLM API 调用失败: {str(e)}")

    def _parse_response(self, raw_text: str) -> SolutionMainline:
        """
        解析 LLM 输出为结构化数据

        Args:
            raw_text: LLM 原始输出

        Returns:
            SolutionMainline: 解析后的主线路

        Raises:
            LLMParseError: JSON 解析失败
        """
        import json
        import re

        # 尝试提取 JSON 部分（处理可能的 markdown 代码块）
        json_match = re.search(r"```json\s*(.*?)\s*```", raw_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试直接解析整个输出
            json_str = raw_text.strip()

        # 移除可能的 BOM 和多余空白
        json_str = json_str.strip().lstrip("\ufeff")

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise LLMParseError(
                f"JSON 解析失败: {str(e)}",
                raw_output=raw_text,
            )

        # 转换为 Pydantic 模型进行验证
        try:
            return SolutionMainline(**data)
        except Exception as e:
            raise LLMParseError(
                f"数据结构验证失败: {str(e)}",
                raw_output=raw_text,
            )

    def _validate_output(self, mainline: SolutionMainline) -> bool:
        """
        验证输出质量

        质量标准：
        1. 四任务覆盖：problem_understanding、solution_steps、method_summary 必须非空
        2. 步骤有效：至少 1 个步骤，step_id 连续
        3. action 有效：每个步骤的 action 必须是定义的动作类型之一

        Args:
            mainline: 待验证的主线路

        Returns:
            bool: 是否通过验证
        """
        # 1. 检查必填字段非空
        if not mainline.problem_understanding or not mainline.problem_understanding.strip():
            return False
        if not mainline.method_summary or not mainline.method_summary.strip():
            return False

        # 2. 检查步骤
        if not mainline.solution_steps or len(mainline.solution_steps) == 0:
            return False

        # 3. 检查 step_id 连续性
        step_ids = [step.step_id for step in mainline.solution_steps]
        if step_ids != list(range(1, len(step_ids) + 1)):
            return False

        # 4. 检查 action 有效性
        valid_actions = set(SolutionAction)
        for step in mainline.solution_steps:
            if step.action not in valid_actions:
                return False

        return True


class OutputValidator:
    """输出验证器"""

    def validate(self, mainline: SolutionMainline) -> Dict[str, Any]:
        """
        验证主线路并返回详细报告

        Returns:
            Dict 包含:
            - is_valid: bool
            - errors: List[str] 错误列表
            - warnings: List[str] 警告列表
        """
        errors = []
        warnings = []

        # 检查必填字段
        if not mainline.problem_understanding:
            errors.append("缺少 problem_understanding")

        if not mainline.solution_steps:
            errors.append("缺少 solution_steps")
        else:
            # 检查步骤完整性
            for step in mainline.solution_steps:
                if not step.description:
                    errors.append(f"step_id={step.step_id}: 缺少 description")
                if not step.reasoning:
                    errors.append(f"step_id={step.step_id}: 缺少 reasoning")

        if not mainline.method_summary:
            errors.append("缺少 method_summary")

        # 检查断点提示
        if mainline.breakpoint_hints:
            for hint in mainline.breakpoint_hints:
                if hint.position not in [s.step_id for s in mainline.solution_steps]:
                    warnings.append(f"断点 position={hint.position} 指向不存在的 step_id")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }


# ========== 异常定义 ==========

class MainlineGeneratorError(Exception):
    """主线路生成器异常基类"""
    pass


class LLMAPIError(MainlineGeneratorError):
    """LLM API 调用失败"""
    pass


class LLMParseError(MainlineGeneratorError):
    """JSON 解析失败"""
    def __init__(self, message: str, raw_output: str = ""):
        super().__init__(message)
        self.raw_output = raw_output


class ValidationError(MainlineGeneratorError):
    """输出验证失败"""
    pass
```

### 4.2 服务注册与依赖注入（FastAPI 示例）

```python
# app/modules/solving/__init__.py
from app.modules.solving.mainline_generator import (
    MainlineGenerator,
    QwenTurboClient,
    GenerateOptions,
    SolutionMainline,
)

__all__ = [
    "MainlineGenerator",
    "QwenTurboClient",
    "GenerateOptions",
    "SolutionMainline",
]
```

```python
# app/dependencies.py
from functools import lru_cache
from app.modules.solving.mainline_generator import (
    MainlineGenerator,
    QwenTurboClient,
    LLMClient,
)


@lru_cache()
def get_llm_client() -> LLMClient:
    """获取 LLM 客户端单例"""
    api_key = os.environ.get("DASHSCOPE_API_KEY", "")
    return QwenTurboClient(api_key=api_key)


@lru_cache()
def get_mainline_generator() -> MainlineGenerator:
    """获取主线路生成器单例"""
    return MainlineGenerator(llm_client=get_llm_client())
```

```python
# app/api/v1/mainline.py
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_mainline_generator
from app.modules.solving.mainline_generator import (
    MainlineGenerator,
    GenerateMainlineRequest,
    GenerateMainlineResponse,
    ErrorResponse,
    LLMAPIError,
    LLMParseError,
    ValidationError,
)

router = APIRouter(prefix="/api/v1/mainline", tags=["主线路生成"])


@router.post(
    "/generate",
    response_model=GenerateMainlineResponse,
    responses={
        500: {"model": ErrorResponse, "description": "服务器错误"},
    },
)
async def generate_mainline(
    request: GenerateMainlineRequest,
    generator: MainlineGenerator = Depends(get_mainline_generator),
):
    """
    生成组织化解题主线路

    接收原始数学问题，输出结构化的解题步骤和方法总结。
    """
    try:
        import time
        import os

        start_time = time.time()

        mainline = await generator.generate(
            problem=request.problem,
            options=request.options,
        )

        latency_ms = int((time.time() - start_time) * 1000)
        tokens_used = int(os.environ.get("LAST_TOKENS_USED", "0"))

        return GenerateMainlineResponse(
            success=True,
            data=mainline,
            metadata={
                "model": "qwen-turbo",
                "latency_ms": latency_ms,
                "tokens_used": tokens_used,
            },
        )

    except LLMAPIError as e:
        raise HTTPException(status_code=500, detail={
            "code": "LLM_API_ERROR",
            "message": "LLM API 调用失败",
            "details": str(e),
        })

    except LLMParseError as e:
        raise HTTPException(status_code=500, detail={
            "code": "LLM_PARSE_ERROR",
            "message": "模型输出无法解析为 JSON",
            "details": e.raw_output[:500] if e.raw_output else str(e),
        })

    except ValidationError as e:
        raise HTTPException(status_code=422, detail={
            "code": "VALIDATION_ERROR",
            "message": "输出不符合质量标准",
            "details": str(e),
        })

    except TimeoutError as e:
        raise HTTPException(status_code=504, detail={
            "code": "TIMEOUT",
            "message": "LLM 响应超时（>30s）",
            "details": str(e),
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "code": "INTERNAL_ERROR",
            "message": "内部错误",
            "details": str(e),
        })
```

---

## 5. 错误码（Error Codes）

### 5.1 错误码表

| 错误码 | HTTP 状态码 | 描述 | 恢复策略 |
|--------|-------------|------|----------|
| `LLM_API_ERROR` | 500 | LLM API 调用失败（网络错误、API 限流等） | 自动重试 1 次，若仍失败返回错误 |
| `LLM_PARSE_ERROR` | 500 | 模型输出无法解析为 JSON（格式错误、非 JSON 输出等） | 使用更严格的 prompt 重试 |
| `VALIDATION_ERROR` | 422 | 输出不符合质量标准（四任务未覆盖、步骤不完整等） | 记录日志，人工检查，可能需要调整 prompt |
| `TIMEOUT` | 504 | LLM 响应超时（>30s） | 返回缓存结果或降级回答 |
| `INVALID_REQUEST` | 400 | 请求参数无效（缺少必填字段、参数类型错误等） | 返回详细错误信息，指导客户端修正 |
| `INTERNAL_ERROR` | 500 | 内部未预期错误 | 记录日志，返回通用错误信息 |

### 5.2 错误响应示例

```json
// 400 INVALID_REQUEST
{
  "success": false,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "请求参数无效",
    "details": "problem 字段为必填"
  }
}

// 422 VALIDATION_ERROR
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "输出不符合质量标准",
    "details": "solution_steps 为空数组"
  }
}

// 504 TIMEOUT
{
  "success": false,
  "error": {
    "code": "TIMEOUT",
    "message": "LLM 响应超时（>30s）",
    "details": "模型处理时间过长，请稍后重试"
  }
}
```

---

## 6. 使用示例（Usage Examples）

### 6.1 Python 服务调用示例

```python
# app/services/tutoring_service.py
from app.modules.solving.mainline_generator import MainlineGenerator, GenerateOptions

class TutoringService:
    def __init__(self):
        self.generator = MainlineGenerator(llm_client=get_llm_client())

    async def solve_problem(self, problem_text: str) -> dict:
        """
        完整解题流程

        Args:
            problem_text: 原始问题文本

        Returns:
            包含主线路和下游断点信息的字典
        """
        # Step 1: Module 1 - 生成主线路
        mainline = await self.generator.generate(
            problem=problem_text,
            options=GenerateOptions(
                temperature=0.7,
                include_breakpoint_hints=True
            )
        )

        # 验证输出
        assert mainline.problem_understanding is not None
        assert len(mainline.solution_steps) > 0
        assert mainline.method_summary is not None

        # Step 2: 传递给 Module 2（Breakpoint Locator）
        # breakpoint_hints 由 Module 2 消费
        if mainline.breakpoint_hints:
            for hint in mainline.breakpoint_hints:
                print(f"断点预警 @ step {hint.position}: {hint.potential_difficulty}")

        return {
            "mainline": mainline.model_dump(),
            "first_action": mainline.solution_steps[0].action,
            "total_steps": len(mainline.solution_steps),
        }


# 使用示例
async def main():
    service = TutoringService()
    result = await service.solve_problem(
        "求证：任意奇数的平方减1能被8整除"
    )
    print(result["first_action"])  # "观察结构"
    print(result["total_steps"])    # 4


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### 6.2 端到端调用示例

```bash
# POST 请求示例
curl -X POST http://localhost:8000/api/v1/mainline/generate \
  -H "Content-Type: application/json" \
  -d '{
    "problem": "求证：任意奇数的平方减1能被8整除",
    "options": {
      "temperature": 0.7,
      "max_tokens": 2048,
      "include_breakpoint_hints": true
    }
  }'
```

### 6.3 测试用例

```python
# tests/modules/solving/test_mainline_generator.py
import pytest
from app.modules.solving.mainline_generator import (
    MainlineGenerator,
    GenerateOptions,
    SolutionMainline,
    LLMParseError,
)


class MockLLMClient:
    """模拟 LLM 客户端"""

    def __init__(self, response: str, should_fail: bool = False):
        self.response = response
        self.should_fail = should_fail

    async def chat(self, messages, temperature, max_tokens):
        if self.should_fail:
            raise Exception("模拟 API 失败")
        return self.response


@pytest.fixture
def generator():
    """测试用生成器"""
    mock_client = MockLLMClient(response="")
    return MainlineGenerator(llm_client=mock_client)


@pytest.mark.asyncio
async def test_generate_success(generator):
    """测试成功生成主线路"""
    mock_response = """
    {
      "problem_understanding": "这道题要证明整除性",
      "solution_steps": [
        {
          "step_id": 1,
          "action": "观察结构",
          "description": "设任意奇数为 2k+1",
          "reasoning": "奇数的一般形式",
          "key_insight": null
        },
        {
          "step_id": 2,
          "action": "化生为熟",
          "description": "(2k+1)² - 1 = 4k(k+1)",
          "reasoning": "构造连续整数乘积",
          "key_insight": "k和k+1必有一个是偶数"
        }
      ],
      "method_summary": "利用奇偶性分析",
      "breakpoint_hints": [
        {
          "position": 1,
          "breakpoint_type": "MISSING_STEP",
          "potential_difficulty": "学生可能不知道如何表示奇数",
          "suggested_dimension": "RESOURCE"
        }
      ]
    }
    """
    generator.llm = MockLLMClient(response=mock_response)

    mainline = await generator.generate(
        problem="求证：任意奇数的平方减1能被8整除"
    )

    assert isinstance(mainline, SolutionMainline)
    assert mainline.problem_understanding == "这道题要证明整除性"
    assert len(mainline.solution_steps) == 2
    assert mainline.solution_steps[0].action == "观察结构"
    assert mainline.solution_steps[0].key_insight is None
    assert mainline.solution_steps[1].key_insight is not None


@pytest.mark.asyncio
async def test_parse_error(generator):
    """测试 JSON 解析失败"""
    generator.llm = MockLLMClient(response="这不是 JSON")

    with pytest.raises(LLMParseError) as exc_info:
        await generator.generate(problem="测试问题")

    assert "JSON" in str(exc_info.value)


@pytest.mark.asyncio
async def test_validation_error_empty_steps(generator):
    """测试步骤为空时的验证失败"""
    mock_response = """
    {
      "problem_understanding": "测试",
      "solution_steps": [],
      "method_summary": "测试方法"
    }
    """
    generator.llm = MockLLMClient(response=mock_response)

    from app.modules.solving.mainline_generator import ValidationError
    with pytest.raises(ValidationError):
        await generator.generate(problem="测试问题")


@pytest.mark.asyncio
async def test_options_respected(generator):
    """测试选项参数被正确传递"""
    captured_args = {}

    class CapturingLLMClient(MockLLMClient):
        async def chat(self, messages, temperature, max_tokens):
            captured_args["temperature"] = temperature
            captured_args["max_tokens"] = max_tokens
            return await super().chat(messages, temperature, max_tokens)

    generator.llm = CapturingLLMClient(response='{"problem_understanding":"","solution_steps":[{"step_id":1,"action":"观察结构","description":"","reasoning":"","key_insight":null}],"method_summary":""}')

    options = GenerateOptions(temperature=0.9, max_tokens=1024)
    await generator.generate(problem="测试", options=options)

    assert captured_args["temperature"] == 0.9
    assert captured_args["max_tokens"] == 1024
```

---

## 7. 附录

### 7.1 思维动作类型定义

| 动作 | 适用场景 | 示例 |
|------|----------|------|
| 观察结构 | 问题形式分析 | "这是一个一元二次方程" |
| 寻找联系 | 建立已知与未知的关系 | "发现可以用配方法" |
| 化生为熟 | 陌生转熟悉 | "令 t = x+1，化简为熟悉形式" |
| 抓关键限制 | 抓住约束条件 | "注意到定义域要求 x > 0" |
| 适时分类 | 分类讨论 | "当 a > 0 和 a < 0 时分别讨论" |
| 构造与替换 | 技巧性变形 | "构造平方差公式" |
| 特殊化边界化回验 | 验证与检查 | "代入 x=0 检验" |
| 结果审查 | 最终检查 | "检查是否符合题意" |

### 7.2 LLM Prompt 模板（供参考）

```
System: 你是一位专业的高中数学教练...

User: 问题：{problem}

请严格按照以下 JSON 格式输出...
```

### 7.3 修订历史

| 版本 | 日期 | 修订内容 |
|------|------|----------|
| 1.0.0 | 2026-03-30 | 初始版本 |
