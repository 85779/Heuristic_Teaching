# Module 3: 智能练习题推荐系统设计文档（知识库驱动版）

**版本**: v2
**核心功能**: 基于知识本体 + LLM 实时生成推荐题目
**最后更新**: 2026-04-07
**核心变化**: 移除题库检索管道，改为「知识检索 → LLM生成」管道

---

## 1. 架构变化对比

### 旧架构（有题库）

```
学生完成 → 读取profile → 题库检索候选题 → 4项打分 → 排序输出top-3
```

### 新架构（知识驱动）

```
学生完成 → 读取profile → 知识本体检索锚点 → LLM生成题目 → 校验 → 输出
```

**核心差异**：

| 对比项   | 旧架构                | 新架构                 |
| -------- | --------------------- | ---------------------- |
| 题目来源 | 预建题库（50-1000道） | 知识本体 + LLM实时生成 |
| 候选集   | 20道候选题            | 1-3个知识锚点          |
| 排序     | 4项打分排序           | 单一生成（不打分排序） |
| 难度标注 | 预标注                | LLM自评                |
| 去重     | problem_id去重        | exclude_similar参数    |
| 输出数量 | top-3                 | 1道（可扩展）          |

---

## 2. 整体数据流

```
学生完成一道题（SOLVED / MAX_ESCALATION）
    │
    ▼
┌────────────────────────────────────────────────────────────┐
│  Step 1: StudentProfileLoader                               │
│  读取: dimension_ratio, recent_problems, weak_kps           │
│  来源: Module 4 MongoDB                                     │
└────────────────────────────────────────────────────────────┘
    │
    ▼
┌────────────────────────────────────────────────────────────┐
│  Step 2: KnowledgeAnchorRetriever                          │
│  根据维度策略，从知识本体检索知识锚点                        │
│  输入: student_profile + current_problem                   │
│  输出: { anchor_type, kps[], methods[], exclude_similar }   │
└────────────────────────────────────────────────────────────┘
    │
    ▼
┌────────────────────────────────────────────────────────────┐
│  Step 3: ProblemGenerator                                   │
│  构建生成Prompt → 调用LLM → 解析JSON → 质量校验              │
│  输入: knowledge_anchor + target_difficulty                  │
│  输出: GeneratedProblem 或 GenerationError                   │
└────────────────────────────────────────────────────────────┘
    │
    ├─ 成功 ──► Step 4: 推荐理由构造 + 写入历史
    │
    └─ 失败 ──► FallbackGenerator: 降级生成
                 │
                 └─► 返回基础练习题或推荐复习
```

---

## 3. 核心组件设计

### 3.1 KnowledgeAnchorRetriever

**文件**: `retriever/knowledge_anchor_retriever.py`

根据学生画像确定生成锚点：

```python
@dataclass
class KnowledgeAnchor:
    """知识锚点：LLM生成题目的核心依据"""
    anchor_type: AnchorType  # SAME_KP / VARIATION / BALANCED
    target_kps: list[KnowledgePoint]  # 目标知识点（1-3个）
    target_method: Optional[Method]  # 推荐使用方法
    exclude_methods: list[str]  # 排除的方法（避免重复）
    exclude_similar: list[str]  # 排除的题目摘要
    generation_goal: str  # 生成目标描述


class KnowledgeAnchorRetriever:
    def __init__(self, knowledge_base: KnowledgeBaseAPI):
        self._kb = knowledge_base

    async def retrieve(
        self,
        student_profile: StudentProfile,
        current_problem: ProblemContext
    ) -> KnowledgeAnchor:
        """根据学生维度画像检索生成锚点"""
        ratio = student_profile.dimension_ratio

        if ratio > 0.65:
            return await self._retrieve_same_kp_anchor(student_profile, current_problem)
        elif ratio < 0.35:
            return await self._retrieve_variation_anchor(student_profile, current_problem)
        else:
            return await self._retrieve_balanced_anchor(student_profile)
```

### 3.2 ProblemGenerator

**文件**: `generator/problem_generator.py`

核心生成逻辑：

```python
class ProblemGenerator:
    """LLM驱动的问题生成器"""

    def __init__(
        self,
        llm_client: DashScopeClient,
        prompt_templates: ProblemPromptTemplates,
        validator: ProblemValidator
    ):
        self._llm = llm_client
        self._templates = prompt_templates
        self._validator = validator

    async def generate(
        self,
        anchor: KnowledgeAnchor,
        target_difficulty: int,
        max_retries: int = 2
    ) -> GenerationResult:
        """
        生成一道练习题

        流程:
          1. 构建生成Prompt
          2. 调用LLM
          3. 解析JSON输出
          4. 质量校验
          5. 失败则重试
        """
        for attempt in range(max_retries):
            # 构建Prompt
            prompt = self._templates.build_generation_prompt(
                anchor=anchor,
                target_difficulty=target_difficulty,
                seed=attempt  # 不同seed产生不同变体
            )

            # 调用LLM
            response = await self._llm.generate(
                prompt=prompt,
                temperature=0.8,  # 需要一定创造性
                response_format={"type": "json_object"}
            )

            # 解析JSON
            try:
                data = json.loads(response.text)
                problem = GeneratedProblem(**data)
            except (json.JSONDecodeError, ValidationError):
                continue  # 重试

            # 质量校验
            validation = self._validator.validate(problem)
            if validation.passed:
                return GenerationResult(
                    success=True,
                    problem=problem,
                    generation_reasoning=response.reasoning
                )

        # 全部失败
        return GenerationResult(success=False, error="MAX_RETRIES_EXCEEDED")
```

### 3.3 Prompt构建

**文件**: `generator/prompt_templates.py`

```python
class ProblemPromptTemplates:
    """生成Prompt模板"""

    def build_generation_prompt(
        self,
        anchor: KnowledgeAnchor,
        target_difficulty: int,
        seed: int = 0
    ) -> str:
        """构建完整的生成Prompt"""

        # 拼接知识点信息
        kp_context = self._format_knowledge_points(anchor.target_kps)

        # 拼接方法信息
        method_context = self._format_method(anchor.target_method) if anchor.target_method else ""

        # 拼接排除信息
        exclude_context = self._format_exclude(anchor.exclude_similar) if anchor.exclude_similar else ""

        prompt = f"""
# 高中数学练习题生成任务

## 知识点锚点
{kp_context}

## 方法要求
{method_context}

## 目标难度
{target_difficulty}（1=基础计算，3=标准练习，5=竞赛难度）

## 题目生成要求
1. 围绕上述知识点生成，难度控制在 {target_difficulty} 级
2. 题目条件充分、表述清晰、有唯一答案
3. 使用 LaTeX 格式书写数学表达式
4. 生成后评估难度并填入 difficulty_rating 字段

{exclude_context}

## 输出格式（严格JSON）
{{
  "problem_text": "题目内容（LaTeX格式）",
  "answer": "标准答案",
  "solution_hint": "1-2句话解题提示",
  "difficulty_rating": {target_difficulty},
  "related_kps": ["KP_XXX", ...],
  "method_used": "使用方法名",
  "generation_reasoning": "生成思路（1句话）"
}}

现在开始生成。
"""
        return prompt
```

### 3.4 质量校验器

**文件**: `generator/problem_validator.py`

```python
@dataclass
class ValidationResult:
    passed: bool
    errors: list[str]


class ProblemValidator:
    """生成题目质量校验器"""

    FORBIDDEN_PHRASES = [
        "显然", "易知", "不难发现", "显然可知",
        "显然成立", "易得", "显然有"
    ]

    def validate(self, problem: GeneratedProblem) -> ValidationResult:
        errors = []

        # 非空检查
        if len(problem.problem_text) < 10:
            errors.append("题目文本过短")
        if not problem.answer:
            errors.append("答案为空")

        # 难度范围
        if not 1 <= problem.difficulty_rating <= 5:
            errors.append(f"难度值{problem.difficulty_rating}超出1-5范围")

        # 敏感词检查
        text = problem.problem_text + problem.solution_hint
        for phrase in self.FORBIDDEN_PHRASES:
            if phrase in text:
                errors.append(f"包含跳过词: {phrase}")

        # LaTeX格式检查（简单验证：含$或\\）
        if "$" not in text and "\\" not in text:
            errors.append("建议使用LaTeX格式书写数学表达式")

        return ValidationResult(passed=len(errors) == 0, errors=errors)
```

### 3.5 FallbackGenerator

**文件**: `generator/fallback_generator.py`

当主生成器失败时的降级策略：

```python
class FallbackGenerator:
    """降级生成器：主生成失败时使用"""

    # 内置基础练习模板（不依赖LLM）
    FALLBACK_TEMPLATES = {
        "配方法": {
            "problem_text": "用配方法化简：$x^2 + 6x + 5$",
            "answer": "$(x+3)^2 - 4$",
            "solution_hint": "将常数项移到一边，配方",
            "difficulty": 1,
            "method_used": "配方法"
        },
        "换元法": {
            "problem_text": "求函数 $f(x) = \\frac{x-1}{x^2-x+1}$ 的值域",
            "answer": "$(-1, 1]$",
            "solution_hint": "令 t=x-1，换元后转化为分式函数",
            "difficulty": 2,
            "method_used": "换元法"
        },
        # ... 更多模板
    }

    def generate(self, anchor: KnowledgeAnchor) -> GeneratedProblem:
        """
        降级生成策略：
          1. 如果 anchor.target_method 有对应模板 → 使用模板
          2. 否则 → 返回最基础的通用练习题
        """
        if anchor.target_method:
            template = self.FALLBACK_TEMPLATES.get(anchor.target_method.name)
            if template:
                return GeneratedProblem(
                    generated_id=f"fallback_{uuid.uuid4().hex[:6]}",
                    why_recommended="系统繁忙，这是同方法的巩固练习",
                    generation_reasoning="降级生成：使用内置模板",
                    **template
                )

        # 最基础的通用练习
        return GeneratedProblem(
            generated_id=f"fallback_{uuid.uuid4().hex[:6]}",
            problem_text="化简：$\\frac{x^2-4}{x-2}$",
            answer="$x+2$（$x \\neq 2$）",
            solution_hint="分子分解因式，约分",
            difficulty=1,
            related_kps=anchor.target_kps[0].kp_id if anchor.target_kps else "KP_UNKNOWN",
            method_used="因式分解",
            why_recommended="基础巩固练习",
            generation_reasoning="降级生成：通用基础题"
        )
```

---

## 4. 模块结构

**目录**: `backend/app/modules/recommendation/`

```
backend/app/modules/recommendation/
│
├── __init__.py
├── module.py
├── routes.py
├── service.py                # 主服务编排
├── models.py                 # Pydantic模型
│
├── retriever/               # Step 2: 知识锚点检索（已实现）
│   ├── __init__.py
│   ├── knowledge_anchor_retriever.py
│
├── generator/               # Step 3: LLM生成（已实现）
│   ├── __init__.py
│   ├── problem_generator.py
│   ├── prompt_templates.py
│   ├── problem_validator.py
│   └── fallback_generator.py
│
├── scorer/                  # 难度计算（已实现）
│   ├── __init__.py
│   └── difficulty_scorer.py
│
├── knowledge_base/          # 知识本体接口（已实现）
│   └── knowledge_api.py
│
├── profile/                  # TODO: 学生画像读取（待 Module 4 就绪）
│   └── loader.py
│
├── output/                  # TODO: 推荐结果推送
│   └── recommender.py
│
└── infrastructure/
    └── database/
        └── repositories/
            └── recommendation_repo.py   # TODO: MongoDB 推荐历史持久化
```

---

## 5. 数据流详解

### 5.1 Step 1: 学生画像读取

```python
async def _load_student_profile(self, student_id: str) -> StudentProfile:
    """从 Module 4 读取学生画像"""
    profile = await self._profile_repo.get_profile(student_id)

    if profile is None:
        # 新学生：使用默认策略
        return StudentProfile(
            student_id=student_id,
            dimension_ratio=0.5,
            recent_problems=[],
            weak_kps=self._kb.get_random_kps(5),  # 随机选5个KP
            current_difficulty=2
        )

    return profile
```

### 5.2 Step 2: 知识锚点检索

```python
async def _retrieve_knowledge_anchor(
    self,
    profile: StudentProfile,
    current_problem: ProblemContext
) -> KnowledgeAnchor:
    """从知识本体检索生成锚点"""
    ratio = profile.dimension_ratio

    if ratio > 0.65:
        # R型薄弱 → 同知识点练习
        current_kps = current_problem.related_kps
        # 获取这些KP的前置知识点
        prerequisites = []
        for kp_id in current_kps:
            prereqs = await self._kb.get_prerequisites(kp_id)
            prerequisites.extend(prereqs)

        # 过滤已掌握的
        weak_prereqs = [k for k in prerequisites
                       if k not in profile.mastered_kps]

        target_kps = await self._kb.get_kps(weak_prereqs[:3])

        return KnowledgeAnchor(
            anchor_type=AnchorType.SAME_KP,
            target_kps=target_kps,
            target_method=None,
            exclude_methods=[],
            exclude_similar=current_problem.summary,
            generation_goal="巩固前置知识点"
        )

    elif ratio < 0.35:
        # M型薄弱 → 同题型变式
        same_type_kps = await self._kb.get_same_type_kps(
            current_problem.related_kps[0]
        )

        # 选择使用不同方法的KP
        different_method_kps = [
            kp for kp in same_type_kps
            if kp.related_method not in profile.recent_methods
        ]

        if different_method_kps:
            target_kp = different_method_kps[0]
            target_method = await self._kb.get_method(target_kp.primary_method)

            return KnowledgeAnchor(
                anchor_type=AnchorType.VARIATION,
                target_kps=[target_kp],
                target_method=target_method,
                exclude_methods=profile.recent_methods,
                exclude_similar=current_problem.summary,
                generation_goal=f"使用{target_method.name}的变式练习"
            )

    # 维度均衡 → 随机薄弱KP
    weak_kps = await self._kb.get_kps(profile.weak_kps[:2])

    return KnowledgeAnchor(
        anchor_type=AnchorType.BALANCED,
        target_kps=weak_kps,
        target_method=None,
        exclude_methods=[],
        exclude_similar=current_problem.summary,
        generation_goal="维持平衡的薄弱知识点练习"
    )
```

### 5.3 Step 3: LLM生成

```python
async def _generate_problem(
    self,
    anchor: KnowledgeAnchor,
    target_difficulty: int
) -> GenerationResult:
    """调用LLM生成题目"""

    # 构建Prompt
    prompt = self._templates.build_generation_prompt(
        anchor=anchor,
        target_difficulty=target_difficulty
    )

    # 调用LLM
    try:
        response = await self._llm_client.generate(
            prompt=prompt,
            model="qwen-turbo",
            temperature=0.8,
            max_tokens=1024,
            response_format={"type": "json_object"},
            timeout=5.0
        )

        # 解析
        data = json.loads(response.text)
        problem = GeneratedProblem(**data)

        # 校验
        validation = self._validator.validate(problem)
        if validation.passed:
            return GenerationResult(success=True, problem=problem)
        else:
            return GenerationResult(success=False, error=validation.errors[0])

    except asyncio.TimeoutError:
        return GenerationResult(success=False, error="LLM_TIMEOUT")
    except Exception as e:
        return GenerationResult(success=False, error=str(e))
```

### 5.4 主服务编排

```python
class RecommendationService:
    async def recommend(
        self,
        student_id: str,
        session_id: str,
        trigger: TriggerEvent
    ) -> RecommendResponse:
        start_time = time.time()

        # Step 1: 读取学生画像
        profile = await self._load_student_profile(student_id)

        # 获取当前题目上下文
        current_problem = await self._get_current_problem_context(session_id)

        # Step 2: 检索知识锚点
        anchor = await self._retrieve_knowledge_anchor(profile, current_problem)

        # Step 3: 计算目标难度
        target_difficulty = self._scorer.calculate_target(
            current_problem.difficulty,
            trigger.outcome
        )

        # Step 4: 生成题目（最多重试2次）
        result = await self._generate_problem(anchor, target_difficulty)

        # 失败则降级
        if not result.success:
            problem = self._fallback.generate(anchor)
            generation_mode = "FALLBACK"
        else:
            problem = result.problem
            generation_mode = "LLM_GENERATED"

        # Step 5: 构造推荐理由
        problem.why_recommended = self._build_why_recommended(
            problem, profile, anchor
        )

        # Step 6: 写入推荐历史
        await self._persist_recommendation(
            student_id=student_id,
            session_id=session_id,
            problem=problem,
            anchor=anchor,
            generation_mode=generation_mode
        )

        return RecommendResponse(
            success=True,
            recommendation=problem,
            metadata={
                "generation_time_ms": int((time.time() - start_time) * 1000),
                "knowledge_anchor": {
                    "type": anchor.anchor_type.value,
                    "kps": [kp.kp_id for kp in anchor.target_kps]
                }
            }
        )
```

---

## 6. 与旧架构的组件对比

| 旧组件                        | 状态    | 新组件                          | 说明                     |
| ----------------------------- | ------- | ------------------------------- | ------------------------ |
| `candidate_retriever.py`      | ❌ 移除 | `knowledge_anchor_retriever.py` | 题库检索 → 知识检索      |
| `dimension_scorer.py`         | ❌ 移除 | —                               | 维度策略在检索阶段已体现 |
| `difficulty_scorer.py`        | ✅ 保留 | `difficulty_scorer.py`          | 仅保留target计算         |
| `spaced_repetition_scorer.py` | ❌ 移除 | `exclude_similar`参数           | 改为生成时排除           |
| `quality_scorer.py`           | ❌ 移除 | `problem_validator.py`          | 改为生成后校验           |
| `ranking_engine.py`           | ❌ 移除 | —                               | 不再需要排序             |
| `problem_bank_repo.py`        | ❌ 移除 | `knowledge_api.py`              | 题库访问 → 知识本体访问  |
| —                             | ✅ 新增 | `problem_generator.py`          | LLM生成器                |
| —                             | ✅ 新增 | `prompt_templates.py`           | Prompt工程               |
| —                             | ✅ 新增 | `fallback_generator.py`         | 降级策略                 |

---

## 7. MongoDB 数据模型

### 7.1 `generated_problems` 集合（新增）

存储已生成的推荐题（用于去重）：

```javascript
{
  "_id": ObjectId,
  "generated_id": "kp3_13_var_001",
  "problem_text": "已知函数...",
  "answer": "...",
  "difficulty": 2,
  "related_kps": ["KP_3_13"],
  "method_used": "配方法",
  "student_id": "student_001",   // 生成时的学生
  "anchor_type": "SAME_KP",
  "generated_at": ISODate,
  "usage_count": 0,  // 被推荐次数
  "status": "active"
}
```

**索引**:

```javascript
db.generated_problems.createIndex({ related_kps: 1 });
db.generated_problems.createIndex({ method_used: 1 });
db.generated_problems.createIndex({ student_id: 1, generated_at: -1 });
```

### 7.2 `student_recommendation_history` 集合（更新）

```javascript
{
  "_id": ObjectId,
  "student_id": "string",
  "session_id": "string",
  "trigger_event": "SOLVED" | "MAX_ESCALATION",

  "student_state": {
    "dimension_ratio": 0.72,
    "target_difficulty": 3,
    "weak_kps": ["KP_3_13"]
  },

  "generation": {
    "mode": "LLM_GENERATED" | "FALLBACK",
    "knowledge_anchor": {
      "type": "SAME_KP",
      "kps": ["KP_3_13", "KP_3_10"]
    },
    "generation_time_ms": 1850,
    "generation_reasoning": "..."
  },

  "recommendation": {
    "generated_id": "kp3_13_var_001",
    "problem_text": "...",
    "difficulty": 2,
    "method_used": "配方法",
    "why_recommended": "..."
  },

  "student_feedback": {
    "accepted": true,
    "completed": false,
    "feedback_at": ISODate
  },

  "created_at": ISODate
}
```

---

## 8. 错误处理架构

```python
class GenerationError(Enum):
    LLM_TIMEOUT = "LLM_TIMEOUT"
    PARSE_ERROR = "JSON_PARSE_ERROR"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    MAX_RETRIES_EXCEEDED = "MAX_RETRIES_EXCEEDED"


async def _generate_with_fallback(
    self,
    anchor: KnowledgeAnchor,
    target_difficulty: int
) -> GeneratedProblem:
    """
    带降级的生成流程

    策略:
      1. 主生成（2次重试）→ LLM生成
      2. 主生成失败 → FallbackGenerator → 内置模板题
      3. 完全无模板 → 返回最基础的通用练习题
    """
    result = await self._generate_problem(anchor, target_difficulty, max_retries=2)

    if result.success:
        return result.problem

    logger.warning(f"主生成失败，使用降级策略: {result.error}")
    return self._fallback.generate(anchor)
```

---

## 9. 性能考量

### 9.1 延迟预算

| 步骤          | 目标耗时     | 最坏耗时     |
| ------------- | ------------ | ------------ |
| 学生画像读取  | < 50ms       | < 100ms      |
| 知识锚点检索  | < 30ms       | < 50ms       |
| LLM生成       | < 2000ms     | < 4000ms     |
| 校验 + 后处理 | < 20ms       | < 50ms       |
| **总计**      | **< 2100ms** | **< 4200ms** |

### 9.2 LLM调用优化

- 使用 `qwen-turbo` 而非 `qwen-plus`（更便宜、更快）
- `temperature=0.8`（足够创造性，避免过于保守）
- `response_format={"type": "json_object"}`（确保输出JSON，减少解析失败）
- `max_tokens=1024`（题目不需要太长）

---

## 10. 知识本体接口设计

**文件**: `knowledge_base/knowledge_api.py`

```python
class KnowledgeBaseAPI:
    """Module 6 知识本体接口（供 Module 3 调用）"""

    def __init__(self, kb_data_path: str):
        self._kps = self._load_knowledge_points(kb_data_path)
        self._methods = self._load_methods(kb_data_path)
        self._type_mappings = self._load_type_mappings(kb_data_path)

    async def get_kp(self, kp_id: str) -> Optional[KnowledgePoint]:
        """根据KP_ID获取知识点"""
        return self._kps.get(kp_id)

    async def get_kps(self, kp_ids: list[str]) -> list[KnowledgePoint]:
        """批量获取知识点"""
        return [self._kps[kid] for kid in kp_ids if kid in self._kps]

    async def get_prerequisites(self, kp_id: str) -> list[str]:
        """获取知识点的直接前置知识点"""
        kp = self._kps.get(kp_id)
        return kp.prerequisites if kp else []

    async def get_same_type_kps(
        self,
        kp_id: str,
        exclude_methods: list[str] = None
    ) -> list[KnowledgePoint]:
        """获取同题型的知识点（可按方法过滤）"""
        kp = self._kps.get(kp_id)
        if not kp:
            return []

        # 找所有关联同一题型的KP
        same_type = [
            k for k in self._kps.values()
            if kp.type in k.related_types
        ]

        # 过滤方法
        if exclude_methods:
            same_type = [
                k for k in same_type
                if k.related_method not in exclude_methods
            ]

        return same_type

    async def get_method(self, method_id: str) -> Optional[Method]:
        """获取方法详情"""
        return self._methods.get(method_id)

    async def get_random_kps(self, count: int) -> list[str]:
        """随机获取KP列表（用于冷启动）"""
        import random
        return random.sample(list(self._kps.keys()), min(count, len(self._kps)))
```

---

## 附录 A: 文件清单与实现状态

| 文件路径                                                      | 职责                   | 状态 |
| ------------------------------------------------------------- | ---------------------- | ---- |
| `service.py`                                                  | 主管道编排             | ✅ 已实现 |
| `models.py`                                                   | Pydantic模型           | ✅ 已实现 |
| `routes.py`                                                   | FastAPI路由            | ✅ 已实现 |
| `module.py`                                                   | 模块入口               | ✅ 已实现 |
| `profile/loader.py`                                           | 学生画像读取           | 📋 TODO (依赖 Module 4) |
| `retriever/knowledge_anchor_retriever.py`                     | 知识锚点检索           | ✅ 已实现 |
| `generator/problem_generator.py`                              | LLM生成                | ✅ 已实现 |
| `generator/prompt_templates.py`                               | Prompt构建             | ✅ 已实现 |
| `generator/problem_validator.py`                              | 质量校验               | ✅ 已实现 |
| `generator/fallback_generator.py`                             | 降级策略               | ✅ 已实现 |
| `scorer/difficulty_scorer.py`                                 | 难度计算               | ✅ 已实现 |
| `output/recommender.py`                                       | 推荐结果推送           | 📋 TODO |
| `knowledge_base/knowledge_api.py`                             | 知识本体接口           | ✅ 已实现 |
| `infrastructure/database/repositories/recommendation_repo.py` | 推荐历史持久化         | 📋 TODO |

**预估总行数**: ~1,800 行（比旧设计减少约700行，移除了题库检索+打分+排序）
