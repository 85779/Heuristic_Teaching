# Module 3 执行计划（知识库驱动版）

**版本**: v2
**创建日期**: 2026-04-07
**预估工期**: 3-4天
**依赖**: Module 1、Module 2（已完成）、Module 4（部分）

---

## 0. 前置准备

### 0.1 确认依赖

| 依赖项            | 状态        | 说明                                                                       |
| ----------------- | ----------- | -------------------------------------------------------------------------- |
| Module 6 知识本体 | ✅ 已就绪   | `knowledge_points_all.json`(175KP)、`methods.json`、`type_kp_mapping.json` |
| DashScope LLM     | ✅ 已就绪   | Module 1/2 已在用                                                          |
| MongoDB           | ✅ 已就绪   | Module 2 已在用                                                            |
| Module 4 学生画像 | ⚠️ 部分就绪 | 框架在，但profile读写接口需确认                                            |

### 0.2 目录创建

```bash
mkdir -p backend/app/modules/recommendation/profile
mkdir -p backend/app/modules/recommendation/retriever
mkdir -p backend/app/modules/recommendation/generator
mkdir -p backend/app/modules/recommendation/scorer
mkdir -p backend/app/modules/recommendation/output
mkdir -p backend/app/modules/recommendation/knowledge_base
mkdir -p backend/app/modules/recommendation/infrastructure/database/repositories
mkdir -p backend/tests/modules/test_recommendation
```

---

## Day 1：框架 + 数据层 ✅

### Task 1.1: 创建目录结构和 models.py ✅

**目标**: 建立 Module 3 骨架 + 定义所有数据模型

**文件**:

```
backend/app/modules/recommendation/
├── __init__.py
├── models.py            ← 数据模型
├── module.py            ← 模块入口（initialize/shutdown）
```

**models.py 需要定义的类型**:

```python
# ===== 输入类型 =====
class TriggerEvent(BaseModel):
    """推荐触发事件"""
    outcome: Literal["SOLVED", "MAX_ESCALATION", "ABANDONED", "MANUAL"]
    current_problem_kps: list[str]           # 当前题关联的KP
    current_method: Optional[str]             # 当前题使用的方法
    current_difficulty: int                  # 当前题难度
    session_id: str

class StudentProfile(BaseModel):
    """学生画像（从 Module 4 读取）"""
    student_id: str
    dimension_ratio: float                   # R型比例 0-1
    recent_problems: list[RecentProblem]     # 最近10题
    weak_kps: list[str]                     # 薄弱KP
    mastered_kps: list[str]                  # 已掌握KP
    recent_methods: list[str]                # 最近使用的方法

# ===== 锚点类型 =====
class AnchorType(str, Enum):
    SAME_KP = "SAME_KP"           # 同知识点练习
    VARIATION = "VARIATION"       # 变式题
    BALANCED = "BALANCED"         # 均衡

class KnowledgeAnchor(BaseModel):
    """知识锚点"""
    anchor_type: AnchorType
    target_kps: list[KnowledgePoint]     # 目标知识点
    target_method: Optional[Method]       # 推荐使用方法
    exclude_methods: list[str]            # 排除的方法
    exclude_similar: list[str]            # 排除的题目摘要
    generation_goal: str                  # 生成目标

# ===== 生成类型 =====
class GeneratedProblem(BaseModel):
    """生成的推荐题"""
    generated_id: str
    problem_text: str                     # 题目（LaTeX）
    answer: str                           # 答案
    solution_hint: str                    # 解题提示
    difficulty: int                       # 1-5
    related_kps: list[str]               # 关联KP
    method_used: str                      # 使用的方法
    why_recommended: str                  # 推荐理由
    generation_reasoning: str             # 生成推理

class ValidationResult(BaseModel):
    """校验结果"""
    passed: bool
    errors: list[str]

class GenerationResult(BaseModel):
    """生成结果"""
    success: bool
    problem: Optional[GeneratedProblem]
    error: Optional[str]

# ===== 输出类型 =====
class RecommendResponse(BaseModel):
    success: bool
    recommendation: Optional[GeneratedProblem]
    metadata: dict
    error: Optional[dict]
```

**交付物**: `backend/app/modules/recommendation/models.py`

---

### Task 1.2: 实现 KnowledgeBaseAPI ✅

**目标**: 封装知识本体读取，复用 `data/knowledge_ontology/` 下的 JSON 文件

**文件**: `backend/app/modules/recommendation/knowledge_base/knowledge_api.py`

**实现要点**:

```python
class KnowledgeBaseAPI:
    def __init__(self, kb_dir: str = "data/knowledge_ontology"):
        self._kps: dict[str, dict] = {}
        self._methods: dict[str, dict] = {}
        self._type_mappings: dict[str, dict] = {}
        self._load_all(kb_dir)  # 启动时加载所有JSON到内存

    async def get_kp(self, kp_id: str) -> Optional[dict]:
        return self._kps.get(kp_id)

    async def get_kps(self, kp_ids: list[str]) -> list[dict]:
        return [self._kps[kid] for kid in kp_ids if kid in self._kps]

    async def get_prerequisites(self, kp_id: str) -> list[str]:
        """获取前置KP列表"""
        kp = self._kps.get(kp_id, {})
        return kp.get("prerequisites", [])

    async def get_weak_kps(self, mastered_kps: list[str], count: int = 5) -> list[str]:
        """
        获取薄弱KP：已关联但掌握度低的KP
        策略：随机从知识本体中选count个（后续由Module 4提供真实薄弱KP）
        """
        all_kps = [k for k in self._kps.keys() if k not in mastered_kps]
        import random
        return random.sample(all_kps, min(count, len(all_kps)))

    async def get_same_type_kps(
        self,
        kp_id: str,
        exclude_methods: list[str] = None
    ) -> list[dict]:
        """获取同题型KP"""
        kp = self._kps.get(kp_id, {})
        related_types = kp.get("related_types", [])

        same_type = [
            k for k in self._kps.values()
            if any(t in k.get("related_types", []) for t in related_types)
        ]

        if exclude_methods:
            same_type = [
                k for k in same_type
                if k.get("method") not in exclude_methods
            ]

        return same_type

    async def get_random_kps(self, count: int) -> list[str]:
        """随机KP（用于冷启动）"""
        import random
        return random.sample(list(self._kps.keys()), min(count, len(self._kps)))
```

**注意**: 知识本体中的 `methods.json` 没有方法ID到KP的直接映射——需要通过 `type_kp_mapping.json` 建立关联。确认数据结构后再写代码。

**交付物**: `backend/app/modules/recommendation/knowledge_base/knowledge_api.py`

---

## Day 2：核心生成逻辑 ✅

### Task 2.1: 实现 KnowledgeAnchorRetriever ✅

**目标**: 根据学生维度画像，从知识本体检索生成锚点

**文件**: `backend/app/modules/recommendation/retriever/knowledge_anchor_retriever.py`

**实现要点**:

```python
class KnowledgeAnchorRetriever:
    def __init__(self, kb_api: KnowledgeBaseAPI):
        self._kb = kb_api

    async def retrieve(
        self,
        profile: StudentProfile,
        current_kps: list[str],
        current_method: str
    ) -> KnowledgeAnchor:
        ratio = profile.dimension_ratio

        if ratio > 0.65:
            # R型薄弱 → 同KP + 前置KP
            return await self._anchor_same_kp(profile, current_kps)
        elif ratio < 0.35:
            # M型薄弱 → 同题型不同方法
            return await self._anchor_variation(profile, current_kps)
        else:
            # 均衡 → 随机薄弱KP
            return await self._anchor_balanced(profile)

    async def _anchor_same_kp(self, profile, current_kps) -> KnowledgeAnchor:
        """获取同知识点锚点（前置KP补强）"""
        # 1. 获取前置KP
        prereqs = []
        for kp_id in current_kps:
            prereqs.extend(await self._kb.get_prerequisites(kp_id))

        # 2. 过滤已掌握的
        weak_prereqs = [k for k in prereqs if k not in profile.mastered_kps]

        # 3. 最多取3个
        kp_ids = (weak_prereqs or current_kps)[:3]
        kps = await self._kb.get_kps(kp_ids)

        return KnowledgeAnchor(
            anchor_type=AnchorType.SAME_KP,
            target_kps=kps,
            target_method=None,
            exclude_methods=[],
            exclude_similar=[],  # TODO: 从MongoDB获取历史生成题
            generation_goal="巩固前置知识点"
        )

    async def _anchor_variation(self, profile, current_kps) -> KnowledgeAnchor:
        """获取变式锚点（同题型不同方法）"""
        if not current_kps:
            return await self._anchor_balanced(profile)

        same_type = await self._kb.get_same_type_kps(
            current_kps[0],
            exclude_methods=profile.recent_methods
        )

        if same_type:
            target_kp = same_type[0]
            kps = [target_kp]
            # 找这个KP对应的方法
            method_name = target_kp.get("method", "")
        else:
            return await self._anchor_balanced(profile)

        return KnowledgeAnchor(
            anchor_type=AnchorType.VARIATION,
            target_kps=kps,
            target_method={"name": method_name} if method_name else None,
            exclude_methods=profile.recent_methods,
            exclude_similar=[],
            generation_goal=f"使用{method_name}的变式练习"
        )

    async def _anchor_balanced(self, profile) -> KnowledgeAnchor:
        """均衡锚点：随机薄弱KP"""
        if profile.weak_kps:
            kp_ids = profile.weak_kps[:2]
        else:
            kp_ids = await self._kb.get_random_kps(2)

        kps = await self._kb.get_kps(kp_ids)

        return KnowledgeAnchor(
            anchor_type=AnchorType.BALANCED,
            target_kps=kps,
            target_method=None,
            exclude_methods=[],
            exclude_similar=[],
            generation_goal="薄弱知识点巩固练习"
        )
```

**交付物**: `backend/app/modules/recommendation/retriever/knowledge_anchor_retriever.py`

---

### Task 2.2: 实现 PromptTemplates ✅

**目标**: 构建 LLM 生成 Prompt

**文件**: `backend/app/modules/recommendation/generator/prompt_templates.py`

**实现要点**:

```python
class ProblemPromptTemplates:
    def build_generation_prompt(
        self,
        anchor: KnowledgeAnchor,
        target_difficulty: int,
        seed: int = 0
    ) -> str:
        # 拼接知识点上下文
        kp_context = self._format_kps(anchor.target_kps)

        # 拼接方法上下文
        method_context = ""
        if anchor.target_method:
            method_context = f"""
## 推荐方法
- 方法名：{anchor.target_method['name']}
- 方法描述：{anchor.target_method['description']}
"""

        # 排除相似题
        exclude_context = ""
        if anchor.exclude_similar:
            exclude_context = f"""
## 排除相似题
以下题目已在近期出现，避免生成过于相似的题：
{chr(10).join(f'- {s}' for s in anchor.exclude_similar[:3])}
"""

        prompt = f"""
# 高中数学练习题生成任务

## 知识点锚点
{kp_context}

{method_context}
## 目标难度
{target_difficulty}（1=基础计算，3=标准练习，5=竞赛难度）

## 题目生成要求
1. 围绕上述知识点生成，难度控制在 {target_difficulty} 级
2. 题目条件充分、表述清晰、有唯一答案
3. 使用 LaTeX 格式书写数学表达式（用 $...$ 或 \\(...\\)）
4. 生成后自行评估难度并填入 difficulty_rating

{exclude_context}

## 输出格式（严格JSON，不要有其他内容）
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

    def _format_kps(self, kps: list[dict]) -> str:
        parts = []
        for i, kp in enumerate(kps[:3], 1):
            part = f"### 知识点 {i}：{kp['name']}"
            if kp.get("content"):
                part += f"\n内容：{kp['content']}"
            if kp.get("formula"):
                part += f"\n公式：{kp['formula']}"
            if kp.get("examples"):
                part += f"\n例题参考：{kp['examples'][0]}"
            parts.append(part)
        return "\n\n".join(parts)
```

**交付物**: `backend/app/modules/recommendation/generator/prompt_templates.py`

---

### Task 2.3: 实现 ProblemValidator ✅

**目标**: 校验 LLM 生成的题目质量

**文件**: `backend/app/modules/recommendation/generator/problem_validator.py`

```python
class ProblemValidator:
    FORBIDDEN = ["显然", "易知", "不难发现", "显然可知", "易得"]

    def validate(self, problem: dict) -> ValidationResult:
        errors = []

        if len(problem.get("problem_text", "")) < 10:
            errors.append("题目文本过短")

        if not problem.get("answer"):
            errors.append("答案为空")

        diff = problem.get("difficulty_rating")
        if not (isinstance(diff, int) and 1 <= diff <= 5):
            errors.append(f"难度值{diff}不在1-5范围")

        text = problem.get("problem_text", "") + problem.get("solution_hint", "")
        for phrase in self.FORBIDDEN:
            if phrase in text:
                errors.append(f"包含跳过词: {phrase}")

        return ValidationResult(passed=len(errors) == 0, errors=errors)
```

**交付物**: `backend/app/modules/recommendation/generator/problem_validator.py`

---

### Task 2.4: 实现 ProblemGenerator ✅

**目标**: 核心 LLM 生成逻辑

**文件**: `backend/app/modules/recommendation/generator/problem_generator.py`

```python
class ProblemGenerator:
    def __init__(
        self,
        llm_client: DashScopeClient,    # 复用 Module 1 的 client
        templates: ProblemPromptTemplates,
        validator: ProblemValidator
    ):
        self._llm = llm_client
        self._templates = templates
        self._validator = validator

    async def generate(
        self,
        anchor: KnowledgeAnchor,
        target_difficulty: int,
        max_retries: int = 2
    ) -> GenerationResult:
        for attempt in range(max_retries):
            # 构建Prompt
            prompt = self._templates.build_generation_prompt(
                anchor=anchor,
                target_difficulty=target_difficulty,
                seed=attempt
            )

            # 调用LLM（使用 qwen-turbo，响应格式 JSON）
            response = await self._llm.generate(
                prompt=prompt,
                model="qwen-turbo",
                temperature=0.8,
                max_tokens=1024,
                response_format={"type": "json_object"},
                timeout=5.0
            )

            # 解析
            try:
                data = json.loads(response.text)
            except json.JSONDecodeError:
                continue  # 重试

            # 校验
            validation = self._validator.validate(data)
            if validation.passed:
                return GenerationResult(
                    success=True,
                    problem=GeneratedProblem(
                        generated_id=f"gen_{uuid.uuid4().hex[:8]}",
                        **data
                    )
                )

        return GenerationResult(success=False, error="MAX_RETRIES_EXCEEDED")
```

**LLM Client 复用**: 参考 `backend/app/infrastructure/llm/dashscope_client.py`，Module 3 直接导入使用。

**交付物**: `backend/app/modules/recommendation/generator/problem_generator.py`

---

### Task 2.5: 实现 FallbackGenerator ✅

**目标**: LLM 生成失败时的降级策略

**文件**: `backend/app/modules/recommendation/generator/fallback_generator.py`

**实现要点**:

- 内置 5-10 道基础练习模板（不依赖 LLM）
- 模板覆盖主要方法：配方法、换元法、分组求和、待定系数法等
- 每个模板含：题目、答案、提示、难度、方法

```python
TEMPLATES = [
    {
        "problem_text": "用配方法化简：$x^2 + 6x + 5$",
        "answer": "$(x+3)^2 - 4$",
        "solution_hint": "将常数项移到一边，配方",
        "difficulty": 1,
        "method_used": "配方法"
    },
    {
        "problem_text": "求函数 $f(x) = \\frac{x-1}{x^2-x+1}$ 的值域",
        "answer": "$(-1, 1]$",
        "solution_hint": "令 t=x-1，换元后分析",
        "difficulty": 2,
        "method_used": "换元法"
    },
    # ... 更多模板
]
```

**交付物**: `backend/app/modules/recommendation/generator/fallback_generator.py`

---

## Day 3：服务编排 + API ✅ (核心)

### Task 3.1: 实现 RecommendationService ✅

**目标**: 主编排服务，串联所有组件

**文件**: `backend/app/modules/recommendation/service.py`

```python
class RecommendationService:
    def __init__(
        self,
        kb_api: KnowledgeBaseAPI,
        anchor_retriever: KnowledgeAnchorRetriever,
        generator: ProblemGenerator,
        fallback: FallbackGenerator,
        difficulty_scorer: DifficultyScorer,
        repo: RecommendationRepository   # MongoDB
    ):
        self._kb = kb_api
        self._retriever = anchor_retriever
        self._generator = generator
        self._fallback = fallback
        self._scorer = difficulty_scorer
        self._repo = repo

    async def recommend(
        self,
        student_id: str,
        trigger: TriggerEvent
    ) -> RecommendResponse:
        start = time.time()

        # Step 1: 读取学生画像（mock，Module 4 未就绪时用默认）
        profile = await self._load_profile(student_id)

        # Step 2: 检索知识锚点
        anchor = await self._retriever.retrieve(
            profile=profile,
            current_kps=trigger.current_problem_kps,
            current_method=trigger.current_method
        )

        # Step 3: 计算目标难度
        target_diff = self._scorer.calculate_target(
            trigger.current_difficulty,
            trigger.outcome
        )

        # Step 4: 生成（主生成失败则降级）
        result = await self._generator.generate(anchor, target_diff, max_retries=2)

        if result.success:
            problem = result.problem
            mode = "LLM_GENERATED"
        else:
            problem = self._fallback.generate(anchor)
            mode = "FALLBACK"

        # Step 5: 构造推荐理由
        problem.why_recommended = self._build_why_recommended(
            problem, anchor
        )

        # Step 6: 写入历史
        await self._repo.save_recommendation(
            student_id=student_id,
            problem=problem,
            anchor=anchor,
            mode=mode
        )

        return RecommendResponse(
            success=True,
            recommendation=problem,
            metadata={
                "generation_time_ms": int((time.time() - start) * 1000),
                "generation_mode": mode,
                "knowledge_anchor": {
                    "type": anchor.anchor_type.value,
                    "kps": [kp.get("kp_id", "") for kp in anchor.target_kps]
                }
            }
        )

    async def _load_profile(self, student_id: str) -> StudentProfile:
        """读取学生画像，Module 4 未就绪时用默认"""
        # TODO: 后续接入 Module 4
        # 暂时返回默认画像
        all_kps = await self._kb.get_random_kps(10)
        return StudentProfile(
            student_id=student_id,
            dimension_ratio=0.5,
            recent_problems=[],
            weak_kps=all_kps[:5],
            mastered_kps=[],
            recent_methods=[]
        )
```

**交付物**: `backend/app/modules/recommendation/service.py`

---

### Task 3.2: 实现 DifficultyScorer ✅

**文件**: `backend/app/modules/recommendation/scorer/difficulty_scorer.py`

```python
class DifficultyScorer:
    def calculate_target(self, current: int, outcome: str) -> int:
        if outcome == "MAX_ESCALATION":
            return max(current - 1, 1)
        elif outcome == "ABANDONED":
            return max(current, 1)
        else:  # SOLVED / MANUAL
            return min(current + 1, 5)
```

**交付物**: `backend/app/modules/recommendation/scorer/difficulty_scorer.py`

---

### Task 3.3: 实现 API 路由 ✅

**实际路由**: `POST /recommendations/recommend`, `GET /recommendations/health`

**文件**: `backend/app/modules/recommendation/routes.py`

```python
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@router.post("/recommend", response_model=RecommendResponse)
async def trigger_recommendation(
    request: RecommendRequest,
    service=Depends(_get_service),
) -> RecommendResponse:
    """触发推荐（来自 Module 2 或学生端）"""
    return await service.recommend(
        student_id=request.student_id,
        trigger=request.trigger,
    )

@router.get("/health")
async def health_check() -> dict:
    """健康检查"""
    return {"status": "ok", "module": "recommendation"}
```

**Request Schema**:

```python
class TriggerRequest(BaseModel):
    student_id: str
    trigger: TriggerEvent
```

**交付物**: `backend/app/modules/recommendation/routes.py`

---

## Day 4：测试 + 验证 ✅

### Task 4.1: 单元测试 ✅

**文件**: `backend/tests/modules/test_recommendation/`

**测试用例**（最低通过标准）：

```python
# test_knowledge_api.py
class TestKnowledgeBaseAPI:
    async def test_load_kps(self):
        api = KnowledgeBaseAPI()
        kp = await api.get_kp("KP_1_01")
        assert kp is not None
        assert kp["name"] is not None

    async def test_get_prerequisites(self):
        api = KnowledgeBaseAPI()
        prereqs = await api.get_prerequisites("KP_3_13")
        assert isinstance(prereqs, list)

# test_anchor_retriever.py
class TestKnowledgeAnchorRetriever:
    async def test_same_kp_anchor_when_r_dominant(self):
        retriever = KnowledgeAnchorRetriever(self._kb_api)
        profile = StudentProfile(dimension_ratio=0.75, ...)
        anchor = await retriever.retrieve(profile, ["KP_3_13"], "配方法")
        assert anchor.anchor_type == AnchorType.SAME_KP

# test_generator.py
class TestProblemGenerator:
    async def test_generate_returns_valid_problem(self):
        generator = ProblemGenerator(self._llm, self._templates, self._validator)
        anchor = KnowledgeAnchor(...)
        result = await generator.generate(anchor, target_difficulty=2)
        assert result.success is True
        assert result.problem.problem_text is not None
        assert 1 <= result.problem.difficulty <= 5

# test_fallback.py
class TestFallbackGenerator:
    def test_fallback_returns_template(self):
        fallback = FallbackGenerator()
        problem = fallback.generate(self._anchor)
        assert problem is not None
        assert problem.problem_text is not None

# test_service.py
class TestRecommendationService:
    async def test_recommend_returns_problem(self):
        service = RecommendationService(...)
        result = await service.recommend(
            student_id="test_student",
            trigger=TriggerEvent(...)
        )
        assert result.success is True
        assert result.recommendation is not None
```

**执行**: `pytest backend/tests/modules/test_recommendation/ -v`

---

### Task 4.2: 手动 E2E 验证 ✅

**测试脚本**: `backend/tests/modules/test_recommendation/e2e_manual.py`

```python
async def test_e2e_with_real_llm():
    """手动E2E测试，需要真实 DashScope API key"""
    import os
    os.environ["DASHSCOPE_API_KEY"] = "your-key-here"

    service = build_recommendation_service()

    # Test Case 1: R型薄弱场景
    result = await service.recommend(
        student_id="test_r_student",
        trigger=TriggerEvent(
            outcome="SOLVED",
            current_problem_kps=["KP_3_13"],
            current_method="配方法",
            current_difficulty=2,
            session_id="s1"
        )
    )
    print(f"✅ R型推荐: {result.recommendation.problem_text[:50]}...")

    # Test Case 2: M型薄弱场景
    result = await service.recommend(
        student_id="test_m_student",
        trigger=TriggerEvent(
            outcome="SOLVED",
            current_problem_kps=["KP_3_13"],
            current_method="配方法",
            current_difficulty=2,
            session_id="s2"
        )
    )
    print(f"✅ M型推荐: {result.recommendation.problem_text[:50]}...")

    # Test Case 3: MAX_ESCALATION 降难度
    result = await service.recommend(
        student_id="test_escalate",
        trigger=TriggerEvent(
            outcome="MAX_ESCALATION",
            current_problem_kps=["KP_3_13"],
            current_method="配方法",
            current_difficulty=3,
            session_id="s3"
        )
    )
    print(f"✅ 降难度推荐: {result.recommendation.difficulty}")
```

---

## 执行顺序

```
Day 1（上午）    Task 1.1 → 目录结构 + models.py
Day 1（下午）    Task 1.2 → KnowledgeBaseAPI
                 └─ 需先确认 methods.json 数据结构

Day 2（全天）    Task 2.1 → KnowledgeAnchorRetriever
                 Task 2.2 → PromptTemplates
                 Task 2.3 → ProblemValidator
                 Task 2.4 → ProblemGenerator（核心）
                 Task 2.5 → FallbackGenerator

Day 3（上午）    Task 3.1 → RecommendationService
                 Task 3.2 → DifficultyScorer
Day 3（下午）    Task 3.3 → API 路由
                 └─ 同时在 main.py 中注册路由

Day 4（全天）    Task 4.1 → 单元测试（6个测试文件）
                 Task 4.2 → E2E 手动验证
```

---

## 验收标准

| 验收项   | 标准                                                       |
| -------- | ---------------------------------------------------------- |
| 单元测试 | `pytest` 全部 PASS                                         |
| E2E 生成 | 3个场景（SOLVED/MAX_ESCALATION/ABANDONED）全部返回有效题目 |
| 难度校验 | 生成题目的 `difficulty_rating` 在 1-5 范围内               |
| 推荐理由 | 每个推荐题都有 `why_recommended` 字段                      |
| API      | `POST /recommendations/recommend` 返回正确的 JSON 结构             |
| Build    | `pytest -v` + `uvicorn` 启动无报错                         |

---

## 剩余工作

以下组件在设计文档和目录规划中已预留，但尚未实现，约占模块完整度的 **30%**：

### 高优先级

| 编号 | 任务 | 对应文件 | 阻塞项 |
|------|------|----------|--------|
| R1 | **MongoDB 持久化** | `infrastructure/database/repositories/recommendation_repo.py` | 无 — 可参考 Module 2 的 `intervention_repo.py` |
| R2 | **Service 接入 repo** | `service.py` — 在 `__init__` 注入 `RecommendationRepository`，`recommend()` 末尾调用 `save` | 依赖 R1 |
| R3 | **Module 4 学生画像对接** | `profile/loader.py` — 替换 `service.py` 的 `_load_profile` mock | 依赖 Module 4 实现 |
| R4 | **Module 2 集成触发** | Module 2 `on_intervention_end` → `POST /recommendations/recommend` | 依赖 Module 2 改造 |

### 中优先级

| 编号 | 任务 | 对应文件 | 说明 |
|------|------|----------|------|
| R5 | **推荐结果推送** | `output/recommender.py` | 学生端实时通知 |
| R6 | **Service E2E 测试** | `test_service.py` | 用 mock 组件跑完整 `recommend()` 管道 |
| R7 | **exclude_similar 去重** | retriever + generator | 从 MongoDB 历史查询已生成题，避免重复 |

### 低优先级

| 编号 | 任务 | 说明 |
|------|------|------|
| R8 | **知识数据路径配置化** | `KnowledgeBaseAPI` 的 `kb_dir` 当前硬编码为相对路径，部署时应从 config 读取 |
| R9 | **冷启动策略优化** | 新学生画像全空时，锚点完全随机。可基于年级/教材版本预设初始 KP 集合 |

### 进度估计

| 阶段 | 内容 | 预估 |
|------|------|------|
| 阶段 1 (R1-R2) | MongoDB 持久化 | 0.5 天 |
| 阶段 2 (R3-R4) | Module 4 对接 + Module 2 集成 | 依赖 Module 4 开发进度 |
| 阶段 3 (R5-R7) | 推送 + 测试 + 去重 | 1 天 |
| 阶段 4 (R8-R9) | 配置化 + 冷启动 | 0.5 天 |
