# Module 3 PRD: 智能练习题推荐系统（知识库驱动版）

> **版本**: v2
> **创建日期**: 2026-03-30
> **更新日期**: 2026-04-07
> **核心变化**: 从「题库检索」改为「知识库 + LLM 实时生成」
> **模块名称**: 智能练习题推荐系统
> **适用领域**: 高中数学辅导

---

## 1. 模块概述（Module Overview）

### 1.1 问题定义

学生在一道题上完成干预（SOLVED 或 MAX_ESCALATION）后，系统需要推荐**下一道最合适的练习题**。

**原有方案的局限**：预建题库存在题量天花板（50/100/1000道），无法覆盖所有知识点变式，且题库维护成本高。

**新方案的核心思路**：不依赖预建题库，而是基于**知识本体**（175个知识点 + 20个方法 + 50种题型），在学生需要时由 LLM 实时生成匹配题目。

### 1.2 核心设计理念

**理念一：知识锚定（Knowledge Anchoring）**

推荐题不是从题库选出来的，而是从知识本体中**检索相关知识点**，再由 LLM 生成匹配的练习题。知识本体是锚，生成是手段。

**理念二：维度平衡（Dimension Balancing）**

- R 型薄弱（知识缺口）→ 生成**同知识点的基础练习题**
- M 型薄弱（元认知弱）→ 生成**同题型的变式题（不同方法）**

**理念三：难度自适应（Adaptive Difficulty）**

题目难度由 LLM 在生成时根据学生画像动态预估（1-5级），无需预标注。

---

## 2. 核心数据来源

### 2.1 知识本体（已就绪）

| 数据           | 规模         | 用途                      |
| -------------- | ------------ | ------------------------- |
| **知识点本体** | 175个KP      | 知识锚点 + 前置依赖       |
| **方法词典**   | ~20个方法    | 解题方法 + 适用KP         |
| **类型映射**   | ~50种题型    | 题型 → KP/方法 的映射关系 |
| **教材文本**   | 12章markdown | LLM 生成时的背景上下文    |

### 2.2 知识点数据结构

```typescript
interface KnowledgePoint {
  kp_id: string; // "KP_3_13"
  chapter: number; // 3
  chapter_name: string; // "第3章 指数函数与对数函数"
  name: string; // "配方法求最值"
  type: "knowledge" | "method";
  content: string; // 知识点内容
  formula: string | null; // 相关公式
  related_types: string[]; // 关联题型
  prerequisites: string[]; // 前置知识点 KP_ID 列表
}

interface Method {
  method_id: string; // "M_换元法"
  name: string; // "换元法"
  description: string; // 方法描述
  applicable_kps: string[]; // 适用知识点
  examples: string[]; // 典型例题（可作为生成参考）
}

interface TypeMapping {
  type: string; // "类型Ⅰ：二次函数最值"
  knowledge_points: string[];
  methods: string[]; // 解这类题的方法
  description: string;
}
```

---

## 3. 推荐流程（Functional Flow）

### 3.1 整体管道

```
学生完成一道题（SOLVED / MAX_ESCALATION）
        │
        ▼
┌──────────────────────────────────────────┐
│  Step 1: 读取学生画像（来自 Module 4）       │
│  → dimension_ratio                         │
│  → recent_problems（最近10题）            │
│  → weak_kps（薄弱知识点）                  │
│  → current_difficulty                      │
└──────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────┐
│  Step 2: 确定推荐目标（知识锚点）            │
│  → 检索相关知识点（从知识本体）              │
│  → 确定生成方向：                          │
│      R型薄弱 → 目标KP + 同KP变式           │
│      M型薄弱 → 同题型 + 不同方法           │
│      维度均衡 → 随机选一个薄弱KP            │
└──────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────┐
│  Step 3: LLM 生成题目                      │
│  → 构建生成 Prompt（知识 + 方法 + 要求）    │
│  → 调用 LLM（qwen-turbo）                 │
│  → LLM 自评难度（1-5）                   │
│  → 验证题目质量（格式/可解/无歧义）         │
└──────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────┐
│  Step 4: 推荐结果后处理                     │
│  → 构造推荐理由（why_recommended）         │
│  → 存储生成的题目（用于后续去重）           │
│  → 推送到学生端                           │
└──────────────────────────────────────────┘
        │
        ▼
推荐结果（1道题目 + 推荐理由）
```

### 3.2 Step 2 详解：知识锚点检索

**核心逻辑**：从知识本体中找到最适合当前学生的知识点，作为 LLM 生成题目的锚点。

```typescript
function retrieveKnowledgeAnchor(
  studentProfile: StudentProfile,
  currentProblem: ProblemContext,
): KnowledgeAnchor {
  const dimensionRatio = studentProfile.dimension_ratio;
  const currentKP = currentProblem.related_kps; // 当前题关联的知识点

  if (dimensionRatio > 0.65) {
    // R型薄弱：生成同知识点练习题
    // 优先选当前题关联的KP，或其前置KP
    const anchorKPs = [
      ...currentKP,
      ...getPrerequisites(currentKP), // 前置知识点
    ].filter((kp) => !studentProfile.mastered_kps.includes(kp));

    return {
      type: "SAME_KP_PRACTICE",
      kps: anchorKPs.slice(0, 3),
      generation_goal: "巩固基础，生成同知识点的不同问法练习题",
    };
  } else if (dimensionRatio < 0.35) {
    // M型薄弱：生成同题型变式题
    // 找同题型但不同方法的知识点
    const sameTypeKP = getSameTypeDifferentMethod(
      currentKP,
      studentProfile.recent_methods, // 学生最近用的方法
    );

    return {
      type: "VARIATION_WITH_DIFFERENT_METHOD",
      kps: sameTypeKP,
      exclude_methods: studentProfile.recent_methods,
      generation_goal: "策略迁移，生成同题型但需要换方法的变式题",
    };
  } else {
    // 维度均衡：随机选一个薄弱KP
    const randomWeakKP = randomChoice(studentProfile.weak_kps);

    return {
      type: "BALANCED",
      kps: [randomWeakKP],
      generation_goal: "维持平衡，选择一个薄弱知识点进行练习",
    };
  }
}
```

### 3.3 Step 3 详解：LLM 生成题目

**生成 Prompt 结构**：

```
## 任务
生成一道高中数学练习题。

## 知识点锚点
- 知识点名称：{kp.name}
- 知识点内容：{kp.content}
- 相关公式：{kp.formula}

## 方法要求
- 推荐方法：{method.name}
- 方法描述：{method.description}
- 典型例题参考：{method.examples[0]}

## 生成要求
1. 题目应围绕上述知识点，难度控制在 {target_difficulty} 级（1=基础，5=竞赛）
2. 优先使用指定方法（如指定了方法）
3. 题目表述清晰，条件充分，有唯一答案
4. 生成后自行评估难度：这道题属于1-5级的哪一级？
5. 不要生成与以下题目过于相似的题：{exclude_similar}

## 输出格式（严格按JSON）
{
  "problem_text": "题目内容（LaTeX格式）",
  "answer": "答案",
  "solution_hint": "解题思路提示（1-2句话）",
  "difficulty_rating": 3,
  "related_kps": ["KP_3_13", "KP_3_10"],
  "method_used": "换元法",
  "generation_reasoning": "为什么生成这道题（1句话）"
}
```

---

## 4. 推荐策略矩阵

### 4.1 维度策略

| 学生状态 | dimension_ratio | 推荐目标     | 生成方向                      |
| -------- | --------------- | ------------ | ----------------------------- |
| R 型薄弱 | > 0.65          | 同知识点巩固 | 生成同KP的不同变式练习        |
| R 型严重 | > 0.80          | 前置知识补强 | 生成前置KP的基础练习          |
| M 型薄弱 | < 0.35          | 策略迁移     | 生成同题型但换方法的变式      |
| M 型严重 | < 0.20          | 元认知训练   | 生成需要分析/判断的开放性问题 |
| 维度均衡 | 0.35-0.65       | 维持平衡     | 从薄弱KP中随机选择            |

### 4.2 难度策略

| 当前完成题难度 | SOLVED 目标难度 | MAX_ESCALATION 目标难度 |
| -------------- | --------------- | ----------------------- |
| 1              | 2               | 1                       |
| 2              | 3               | 1                       |
| 3              | 4               | 2                       |
| 4              | 5               | 3                       |
| 5              | 5（维持）       | 4                       |

### 4.3 去重策略

LLM 生成时，系统会传入「最近生成的题目摘要」作为 `exclude_similar`，避免生成重复题目。生成的题目在生成时即记录 `generated_problem_id` 到 MongoDB，后续生成时作为去重依据。

---

## 5. 输出格式（Output Schema）

### 5.1 核心响应

```typescript
interface RecommendResponse {
  success: boolean;
  data: {
    recommendation: GeneratedProblem; // 生成的推荐题（1道）
    strategy: RecommendationStrategy; // 当前推荐策略
  };
  metadata: {
    student_id: string;
    dimension_ratio: number;
    target_difficulty: number;
    generation_time_ms: number;
    knowledge_anchor: {
      type: "SAME_KP_PRACTICE" | "VARIATION" | "BALANCED";
      kps: string[];
    };
  };
}

interface GeneratedProblem {
  generated_id: string; // 自动生成ID（UUID前8位）
  problem_text: string; // 题目文本（LaTeX）
  answer: string; // 答案
  solution_hint: string; // 解题思路提示
  difficulty: number; // 1-5（LLM自评）
  related_kps: string[]; // 关联知识点
  method_used: string; // 使用的方法
  why_recommended: string; // 推荐理由
  generation_reasoning: string; // LLM 生成推理过程
}

interface RecommendationStrategy {
  label: string; // "R型巩固（同知识点变式）"
  dimension_target: { r: number; m: number };
  generation_mode: "SAME_KP" | "VARIATION" | "BALANCED";
  description: string;
  adjustment_reason: string;
}
```

### 5.2 典型响应示例

```json
{
  "success": true,
  "data": {
    "recommendation": {
      "generated_id": "kp3_13_var_001",
      "problem_text": "已知函数 $f(x) = x^2 - 4x + 5$，求其在区间 $[1, 3]$ 上的最小值。",
      "answer": "最小值为 2，当 $x = 2$ 时取得。",
      "solution_hint": "将二次函数配方后，在给定区间内判断对称轴位置。",
      "difficulty": 2,
      "related_kps": ["KP_3_13", "KP_3_10"],
      "method_used": "配方法",
      "why_recommended": "前一道题涉及配方法求最值，这道题在同一知识点上变换条件，深化配方法的掌握",
      "generation_reasoning": "基于KP_3_13（配方法求最值），使用配方法，设置闭区间边界条件，难度2"
    },
    "strategy": {
      "label": "R型巩固（同知识点变式）",
      "dimension_target": { "r": 0.7, "m": 0.3 },
      "generation_mode": "SAME_KP",
      "description": "学生 dimension_ratio=0.72（偏R），继续生成同知识点练习巩固基础",
      "adjustment_reason": "R型断点较多，需要补充资源型练习"
    }
  },
  "metadata": {
    "student_id": "student_001",
    "dimension_ratio": 0.72,
    "target_difficulty": 3,
    "generation_time_ms": 1850,
    "knowledge_anchor": {
      "type": "SAME_KP_PRACTICE",
      "kps": ["KP_3_13", "KP_3_10"]
    }
  }
}
```

### 5.3 错误响应

```json
{
  "success": false,
  "error": {
    "code": "GENERATION_FAILED",
    "message": "LLM 生成失败，请重试",
    "details": {
      "reason": "API_TIMEOUT"
    }
  },
  "data": {
    "recommendation": null,
    "strategy": null
  }
}
```

---

## 6. 状态机与触发条件

### 6.1 触发时机

| 触发事件         | 来源     | 说明                               |
| ---------------- | -------- | ---------------------------------- |
| `SOLVED`         | Module 2 | 学生成功完成一道题，立即生成下一题 |
| `MAX_ESCALATION` | Module 2 | 降低难度生成（难度-1或-2）         |
| `ABANDONED`      | 学生端   | 生成基础练习题                     |
| 学生主动请求     | 学生端   | 学生点击"再来一题"                 |
| 定期复习         | 定时器   | 薄弱KP复习推送                     |

---

## 7. 与其他模块的接口

### 7.1 从 Module 4 读取

```python
# StudentProfileRepo (Module 4)
class StudentProfileRepo:
    async def get_profile(self, student_id: str) -> StudentProfile
    async def get_dimension_ratio(self, student_id: str) -> float
    async def get_recent_problems(self, student_id: str, limit: int = 10) -> list[dict]
    async def get_mastered_kps(self, student_id: str) -> list[str]     # 已掌握知识点
    async def get_weak_kps(self, student_id: str, limit: int = 5) -> list[str]  # 薄弱知识点
```

### 7.2 从知识本体检索

```python
# KnowledgeBaseAPI (Module 6)
class KnowledgeBaseAPI:
    async def get_kp(self, kp_id: str) -> KnowledgePoint
    async def get_kps_by_chapter(self, chapter: int) -> list[KnowledgePoint]
    async def get_method(self, method_id: str) -> Method
    async def get_type_mapping(self, type_name: str) -> TypeMapping
    async def get_prerequisites(self, kp_id: str) -> list[str]  # 获取前置KP
    async def get_same_type_kps(self, kp_id: str) -> list[KnowledgePoint]  # 同题型KP
```

### 7.3 从 Module 2 接收触发

```python
class RecommendationTrigger:
    async def on_intervention_end(
        self,
        student_id: str,
        session_id: str,
        outcome: "SOLVED" | "MAX_ESCALATION" | "ABANDONED",
        current_problem_kps: list[str],
        current_method: str,
        final_level: str,
    ) -> RecommendResponse
```

---

## 8. 生成质量保障

### 8.1 LLM 自评 + 规则校验

生成后系统进行校验：

| 检查项   | 规则                         | 不通过处理 |
| -------- | ---------------------------- | ---------- |
| 题目非空 | `problem_text` 长度 > 10字符 | 重试生成   |
| 答案非空 | `answer` 长度 > 0            | 重试生成   |
| 难度合理 | `difficulty` 在 1-5 范围内   | 重试生成   |
| 无敏感词 | 不含"显然"、"易知"等跳过词   | 重试生成   |
| 可解性   | 答案格式正确（LaTeX或文字）  | 重试生成   |

### 8.2 重试策略

- 生成失败最多重试 2 次（不同 seed）
- 2 次均失败 → 返回降级结果：推荐复习当前题的类似练习
- 生成超时（>5s）→ 直接使用降级结果

---

## 9. 评估指标

### 9.1 生成效果指标

| 指标           | 定义                      | 目标  |
| -------------- | ------------------------- | ----- |
| **生成成功率** | 成功生成 / 总请求数       | > 95% |
| **生成延迟**   | LLM 调用耗时（P95）       | < 3s  |
| **学生接受率** | 学生点击推荐题 / 推荐次数 | > 60% |
| **完成率**     | 学生完成推荐题 / 接受次数 | > 70% |

### 9.2 系统性能

| 指标     | 目标  | 告警阈值 |
| -------- | ----- | -------- |
| P50 延迟 | < 2s  | > 3s     |
| P95 延迟 | < 4s  | > 6s     |
| 成功率   | > 95% | < 90%    |

---

## 10. 风险与备选

| 风险                   | 概率 | 影响 | 备选方案                          |
| ---------------------- | ---- | ---- | --------------------------------- |
| LLM 生成题目有数学错误 | 中   | 高   | LLM 自评 + 规则校验；人工审核通道 |
| 生成题目与之前过于相似 | 低   | 中   | 传入 exclude_similar；去重层      |
| LLM 生成超时/失败      | 低   | 中   | 2次重试；降级到推荐当前题类似练习 |
| 知识点覆盖不足         | 低   | 中   | 知识本体持续扩充                  |
| 难度评估不准确         | 中   | 中   | 学生完成后反馈校准难度分          |

---

## 附录 A：生成 Prompt 模板变量

| 变量                   | 来源       | 说明            |
| ---------------------- | ---------- | --------------- |
| `{kp.name}`            | 知识本体   | 知识点名称      |
| `{kp.content}`         | 知识本体   | 知识点内容      |
| `{kp.formula}`         | 知识本体   | 相关公式        |
| `{method.name}`        | 方法词典   | 推荐使用方法    |
| `{method.description}` | 方法词典   | 方法描述        |
| `{method.examples}`    | 方法词典   | 典型例题        |
| `{target_difficulty}`  | 学生画像   | 目标难度（1-5） |
| `{exclude_similar}`    | 已生成题目 | 排除的题目摘要  |
| `{chapter_context}`    | 教材文本   | 该章的背景知识  |

---

## 附录 B：错误码

| Code                  | HTTP Status | 说明                               |
| --------------------- | ----------- | ---------------------------------- |
| `SUCCESS`             | 200         | 生成成功                           |
| `GENERATION_FAILED`   | 500         | LLM 生成失败（2次重试后）          |
| `VALIDATION_FAILED`   | 200         | 生成格式校验失败（触发降级）       |
| `TIMEOUT`             | 504         | LLM 调用超时                       |
| `PROFILE_NOT_FOUND`   | 200         | 新学生，使用默认策略               |
| `KNOWLEDGE_NOT_FOUND` | 200         | 知识本体中未找到相关KP（触发降级） |
