# Module 2 PRD: Progressive Scaffolding Intervention System at Breakpoints

> **版本**: v3.1（精简版 — KGContext 仅做查询，hint深度由级别决定）  
> **更新日期**: 2026-04-01  
> **模块名称**: 断点渐进式脚手架干预系统  
> **适用领域**: 高中数学辅导

---

## 1. 模块概述

### 1.1 问题定义

在高中数学辅导过程中，学生在解题时经常会在特定步骤（断点）卡住。Module 2 的核心任务是：**当学生处于断点时，以断点关联的知识点为上下文，提供维度感知的渐进式提示（Resource / Metacognitive），在不泄露答案的前提下引导解题。**

### 1.2 与其他模块的关系

```
Module 1 (Cognitive Diagnosis Engine)
         │
         │ solution_steps（含 kp_ids + method_id 标注）
         ▼
Module 2 (Progressive Scaffolding Intervention)  ◄── 当前模块
         │
    ┌────┴────────────┐
    ▼                 ▼
Module 6 (RAG)   Module 4 (Student Profile)
ChromaDB 查询       dimension_ratio / routing_hint
```

| 关系                    | 说明                                                                                                       |
| ----------------------- | ---------------------------------------------------------------------------------------------------------- |
| **Module 1 → Module 2** | 提供带标注的 `solution_steps`（每步有 `kp_ids` + `method_id`）；学生步骤 vs 参考步骤进入 BreakpointLocator |
| **Module 2 → Module 4** | 干预结束后，`update_after_intervention()` 写入本次断点的 `kp_ids`、维度、级别                              |
| **Module 4 → Module 2** | `get_routing_hint()` 向 Node 2a/2b 提供 `dimension_ratio`、薄弱维度等上下文                                |
| **Module 6 → Module 2** | ChromaDB 向量检索，根据断点 kp_ids 补充相关知识点 chunk                                                    |

### 1.3 核心设计原则

1. **知识点来源唯一**：断点关联的 `kp_ids` 来自 Module 1 的 solution_step 标注，不做二次推断
2. **KGContext 仅做查询**：Node 3 根据断点 kp_ids 查询知识点内容，不做任何方法推断
3. **Hint 深度由级别决定**：`R1-R4` / `M1-M5` 的深浅完全由 prompt 模板控制，与 KGContext 无关
4. **学生路径顺应**：`WRONG_DIRECTION` 断点时，按学生当前路径给提示，而非强制拉回 canonical

---

## 2. 完整管道流程

```
学生请求干预
    │
    ▼
┌──────────────────────────────────────────────────────────────────┐
│  Node 1: BreakpointLocator                                         │
│  输入: student_steps vs solution_steps（含 kp_ids 标注）          │
│  输出: breakpoint { position, type, expected_step,                │
│                    kp_ids, method_id }                            │
└──────────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────────────┐
│  Node 2a: DimensionRouter                                          │
│  输入: breakpoint + Module4 routing_hint                            │
│  输出: R（Resource）或 M（Metacognitive）                          │
└──────────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────────────┐
│  Node 2b: SubTypeDecider                                           │
│  输入: 维度 + breakpoint + Module4 routing_hint                    │
│  输出: R1-R4 或 M1-M5 级别 + escalation 决策                       │
└──────────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────────────┐
│  Node 3: KGQueryBuilder                                            │
│  输入: breakpoint.kp_ids + breakpoint.method_id                    │
│  行为: 查 knowledge_points_all.json + methods.json                 │
│  输出: KGPicks { kp_ids, method_ids }                             │
└──────────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────────────┐
│  Node 4: KGRetriever                                               │
│  输入: KGPicks                                                     │
│  行为:                                                             │
│    ① 从 knowledge_points_all.json 批量读 kp_id 内容               │
│    ② ChromaDB 向量检索 top_k 扩展（可选）                         │
│  输出: KGContext                                                   │
└──────────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────────────┐
│  Node 5: HintGeneratorV2                                           │
│  输入: R/M级别 + KGContext                                          │
│  行为: R1-R4 / M1-M5 级别 → 对应 prompt 模板 → 提示内容           │
│        hint 深度由级别决定，KGContext 仅作知识点引用依据          │
│  输出: hint content                                                │
└──────────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────────────┐
│  Node 6: OutputGuardrail                                            │
│  检查: 答案泄露 + 知识点引用验证                                   │
└──────────────────────────────────────────────────────────────────┘
    │
    ▼
返回 InterventionResponse
```

---

## 3. 核心数据结构

### 3.1 Module 1 标注格式

Module 1 生成的参考解法，每个 `solution_step` 必须标注：

```json
{
  "step_id": "s3",
  "step_name": "用求根公式求 x",
  "content": "Δ = b² - 4ac = 9 - 8 = 1 > 0",
  "kp_ids": ["KP_2_04"],
  "method_id": "M_求根公式",
  "type": "computation"
}
```

| 字段        | 类型             | 说明                       |
| ----------- | ---------------- | -------------------------- |
| `kp_ids`    | `string[]`       | 该步骤关联的知识点 ID 列表 |
| `method_id` | `string \| null` | 该步骤使用的解题方法 ID    |

**标注规则**：

- 每个 `solution_step` 必须有 `kp_ids`（至少1个）
- `method_id` 可为空（纯知识型步骤），但不应为空字符串
- `kp_ids` 来自 `knowledge_points_all.json` 中的 `kp_id` 字段

### 3.2 BreakpointLocation

Node 1 输出：

```typescript
interface BreakpointLocation {
  position: number; // 断点在 solution_steps 中的索引（0-based）
  type: BreakpointType; // "MISSING_STEP" | "WRONG_DIRECTION" | "INCOMPLETE_STEP" | "STUCK" | "NO_BREAKPOINT"
  expected_step: string; // canonical 期望的下一步内容（原文）

  // 来自 solution_step 标注
  kp_ids: string[]; // 断点那一步的 kp_ids（Node 3 直接使用）
  method_id: string | null; // 断点那一步的 method_id

  student_last_step: string; // 学生最后一步的内容
  gap_description: string; // 差距描述
}
```

### 3.3 KGContext

Node 4 输出，传入 Node 5：

```typescript
interface KGContext {
  // 查出来的知识点（Node 3 直接从 kp_ids 查询，无推断）
  knowledge_points: {
    kp_id: string; // "KP_3_13"
    name: string; // "函数单调性的判断"
    type: "knowledge" | "method";
    content: string; // 知识内容
    formula: string | null; // 公式（如有）
    chapter: number;
  }[];

  // 相关解题方法
  methods: {
    method_id: string; // "M_换元法"
    name: string; // "换元法"
    description: string; // 方法描述
  }[];

  // ChromaDB 检索补充（如有）
  supplementary_chunks: {
    content: string;
    source: "chroma";
    distance: number;
  }[];

  // 元数据
  retrieval_confidence: number; // 0.0-1.0
  retrieval_source: "json_only" | "chroma_enhanced";
}
```

**KGContext 格式化示例**：

```
## 相关知识点

【知识点 1】KP_2_04 — 根据方程根的分布求参数（method）
  内容：根据一元二次方程在某区间上根的情况求参：若只说有根则参变分离；
        若规定根的个数则考虑判别式、对称轴、端点值
  公式：参变分离：对参数一侧求值域

【知识点 2】KP_2_02 — 一元二次不等式的解法（method）
  内容：先解对应方程，再根据二次项系数和判别式判断图象位置，写出解集
  公式：Δ>0时：ax²+bx+c>0解集为{x|x<x₁或x>x₂}

## 相关解题方法

【方法】M_求根公式
  描述：一元二次方程 ax²+bx+c=0 的根为 x = (-b±√Δ)/(2a)
```

### 3.4 InterventionResponse

```typescript
interface InterventionResponse {
  success: boolean;
  intervention: {
    id: string;
    content: string; // 提示内容
    dimension: "Resource" | "Metacognitive";
    level: "R1" | "R2" | "R3" | "R4" | "M1" | "M2" | "M3" | "M4" | "M5";
    kp_ids_used: string[]; // 本次提示使用的 kp_id
    method_id: string | null; // 本次提示使用的方法 ID
  } | null;
  breakpoint: {
    position: number;
    type: string;
    expected_step: string;
    kp_ids: string[];
  };
  student_profile_snapshot: {
    dimension_ratio: number;
    weak_dimensions: string[];
  };
}
```

---

## 4. 节点详解

### Node 1：BreakpointLocator

**职责**：对比学生步骤与参考解法，定位断点。

**输入**：

```python
student_steps: list[TeachingStep]
solution_steps: list[TeachingStep]  # 每个 step 有 kp_ids + method_id 标注
```

**输出**：`BreakpointLocation`

**断点类型**：

| 类型              | 定义                        | 典型场景           |
| ----------------- | --------------------------- | ------------------ |
| `MISSING_STEP`    | 学生缺少 canonical 的某一步 | 学生跳过了关键步骤 |
| `WRONG_DIRECTION` | 学生写了内容但方向不符      | 学生用了不同方法   |
| `INCOMPLETE_STEP` | 学生做了但不完整            | 算到一半停了       |
| `STUCK`           | 学生空白或极短              | 完全没有思路       |
| `NO_BREAKPOINT`   | 学生步骤与 canonical 一致   | 无需干预           |

**算法**：Jaccard + 字符串相似度，纯规则，无 LLM。

**关键**：输出中 `kp_ids` 和 `method_id` **直接取自对应位置的 `solution_step` 标注**，不做任何修改。

---

### Node 2a：DimensionRouter

**职责**：判断断点属于 Resource 还是 Metacognitive 维度。

**输入**：

```python
breakpoint: BreakpointLocation
student_work: str
Module4 routing_hint: RoutingHint  # 含 dimension_ratio, recommended_dimension
```

**判断规则**：

```
断点类型 = MISSING_STEP  → 强 RESOURCE（学生不知道这一步该做什么）
断点类型 = WRONG_DIRECTION → 强 METACOGNITIVE（学生有知识但方向偏了）
断点类型 = INCOMPLETE_STEP → 偏向 RESOURCE（能做但不完整）
断点类型 = STUCK            → 偏向 RESOURCE（缺乏起始方向）

Module4 routing_hint.recommended_dimension 可作为参考微调，但：
  - WRONG_DIRECTION 强制 METACOGNITIVE，不参考建议
  - 其他类型可参考建议调整
```

**Module 4 routing_hint 注入**：

```
## 学生画像上下文（来自 Module 4）
- dimension_ratio: {dimension_ratio}（R型断点占比，越高说明知识缺口越多）
- 推荐维度: {recommended_dimension}（参考值）
- 薄弱维度: {weak_dimensions}
```

---

### Node 2b：SubTypeDecider

**职责**：在维度内部确定具体级别（R1-R4 / M1-M5）。

**输入**：

```python
dimension: "RESOURCE" | "METACOGNITIVE"
breakpoint: BreakpointLocation
intervention_memory: list[InterventionRecord]  # 历史
frontend_signal: str | null
current_level: str | null
Module4 routing_hint: RoutingHint
```

**级别决策**：

| 维度 | 级别 | 触发条件                        |
| ---- | ---- | ------------------------------- |
| R    | R1   | 初次干预，MISSING_STEP          |
| R    | R2   | R1 失败，或 partial knowledge   |
| R    | R3   | R2 失败，或学生显示部分理解     |
| R    | R4   | R3 失败，或问题复杂需要完整步骤 |
| M    | M1   | 初次干预，WRONG_DIRECTION       |
| M    | M2   | M1 失败，尝试激活策略意识       |
| M    | M3   | M2 失败，给出具体方法建议       |
| M    | M4   | M3 失败，对比多种策略           |
| M    | M5   | M4 失败，引导选择策略           |

**Escalation 规则**：

```
NOT_PROGRESSED → 升级到下一级别
同一级别 NOT_PROGRESSED 两次 → 升级
R4 MAX → 跨维度切换到 M3
M5 MAX → TERMINATE（转 Module 3/4/5）
```

---

### Node 3：KGQueryBuilder【精简版 — 仅做查询】

**职责**：根据断点 kp_ids 查找知识点和方法。

**输入**：`BreakpointLocation`（含 `kp_ids` + `method_id`）

**处理逻辑**：

```
1. 直接取出 breakpoint.kp_ids（如 ["KP_2_04"]）
2. 直接取出 breakpoint.method_id（如 "M_求根公式"）
3. 查 knowledge_points_all.json，提取这些 kp_id 的完整内容
4. 查 methods.json，提取 method_id 对应的方法描述
5. 输出 KGPicks
```

**不做任何推断，不对比学生方法，不检测 mismatch。**

```python
def build_kpicks(breakpoint: BreakpointLocation) -> KGPicks:
    return KGPicks(
        kp_ids=breakpoint.kp_ids,
        method_ids=[breakpoint.method_id] if breakpoint.method_id else [],
    )
```

**输出**：

```typescript
interface KGPicks {
  kp_ids: string[]; // 直接来自 breakpoint，无处理
  method_ids: string[]; // 直接来自 breakpoint，无处理
}
```

---

### Node 4：KGRetriever

**职责**：将 KGPicks 转换为可注入 prompt 的 KGContext。

**处理流程**：

```
Step 1: 批量读取 knowledge_points_all.json 中 kp_ids 对应的条目
Step 2: 批量读取 methods.json 中 method_ids 对应的条目
Step 3（可选）: ChromaDB 向量检索扩展
        - 以 kp_ids 内容构建向量查询
        - 取 top_k=3 个最相似 chunk
        - 补充到 supplementary_chunks
Step 4: 格式化 KGContext
```

**ChromaDB 向量检索（可选增强）**：

```python
async def _chroma_expand(kpicks: KGPicks, top_k: int = 3) -> list[str]:
    """
    ChromaDB 扩展检索（Module 6 提供）
    以 kp 内容为 query，向量检索补充相关 chunk
    仅在 ChromaDB 可用时执行，失败则跳过
    """
    if self._chroma_client is None:
        return []

    try:
        query_texts = [get_kp_content(kp_id) for kp_id in kpicks.kp_ids]
        results = await self._chroma_client.query(
            query_texts=query_texts,
            n_results=top_k,
            where={"type": {"$in": ["knowledge", "method"]}}
        )
        return [r["document"] for r in results["documents"]]
    except Exception:
        return []
```

**KGContext 格式化**：

```python
def format_kg_context(kpicks: KGPicks, chroma_chunks: list[str]) -> KGContext:
    kps = [load_kp(kp_id) for kp_id in kpicks.kp_ids]
    methods = [load_method(mid) for mid in kpicks.method_ids]

    context_parts = []
    for kp in kps:
        context_parts.append(
            f"【知识点 {kp.kp_id}】{kp.name}（{kp.type}）\n"
            f"  内容：{kp.content}\n"
            f"  公式：{kp.formula or '无'}"
        )

    for method in methods:
        context_parts.append(
            f"【方法】{method.method_id}\n"
            f"  {method.description}"
        )

    return KGContext(
        knowledge_points=kps,
        methods=methods,
        supplementary_chunks=[{"content": c, "source": "chroma"} for c in chroma_chunks],
        retrieval_confidence=0.9 if chroma_chunks else 0.7,
        retrieval_source="chroma_enhanced" if chroma_chunks else "json_only",
    )
```

---

### Node 5：HintGeneratorV2

**职责**：根据 R/M 级别生成提示，知识点引用 KGContext。

**Hint 深度由级别决定，KGContext 仅作引用依据。**

#### Resource 维度（R1-R4）

| 级别 | 深度 | KGContext 引用方式      | 示例                                       |
| ---- | ---- | ----------------------- | ------------------------------------------ |
| R1   | 最浅 | 只引用知识点名称        | "这道题需要用到一元二次不等式的解法"       |
| R2   | 较浅 | 引用知识点内容摘要      | "一元二次不等式要先解对应方程，再判断符号" |
| R3   | 中等 | 引用公式+第一步形式     | "用判别式 Δ=b²-4ac，先算出 Δ 的值"         |
| R4   | 完整 | 引用公式+完整可执行步骤 | "Δ=9-8=1>0，x=(-3±1)/2，所以 x=-1 或 x=-2" |

#### Metacognitive 维度（M1-M5）

| 级别 | 深度 | KGContext 引用方式   | 示例                                       |
| ---- | ---- | -------------------- | ------------------------------------------ |
| M1   | 最浅 | 不引用，给反思性问题 | "你有没有想过这道题可能有几种不同的解法？" |
| M2   | 较浅 | 引用方法名称         | "有没有考虑过用求根公式来做？"             |
| M3   | 中等 | 引用方法+理由        | "用求根公式可以直接套公式，比配方法更直接" |
| M4   | 较深 | 引用多种方法对比     | "配方法 VS 求根公式，哪种更适合这里？"     |
| M5   | 最深 | 引用方法+完整对比    | "我们对比三种方法..."                      |

**KGContext 注入格式（在 prompt 中）**：

```
## 相关知识点（来自知识本体）
{格式化后的 KGContext}

## 你的任务
生成一条 {level} 级提示...
```

**KGContext 对所有级别均注入**，但引用深度按级别梯度递增。

---

### Node 6：OutputGuardrail

**检查项**：

| 检查               | 方法                                        | 失败处理                           |
| ------------------ | ------------------------------------------- | ---------------------------------- |
| 答案关键词泄露     | 规则黑名单（同步，<1ms）                    | 降级到 M1                          |
| 提示过于直接       | LLM-judge（异步，~1s）                      | 替换为更抽象版本                   |
| **知识点引用缺失** | 检查提示是否引用了 KGContext 中的知识点名称 | 警告但不拦截（KGContext 可能为空） |
| ChromaDB 降级标记  | 检查 retrieval_source                       | 记录日志，不影响生成               |

---

## 5. 与 Module 4 的接口

### 5.1 Module 2 → Module 4：干预结束写回

```typescript
interface InterventionWriteBack {
  student_id: string;
  session_id: string;
  problem_id: string;

  // 断点信息
  breakpoint: {
    position: number;
    type: string; // "MISSING_STEP" / "WRONG_DIRECTION" etc.
    kp_ids: string[]; // 断点关联的 kp_ids
    method_id: string | null;
  };

  // 干预决策
  dimension: "RESOURCE" | "METACOGNITIVE";
  level: string; // "R2" / "M3" etc.
  kp_ids_used: string[]; // 本次提示实际使用的 kp_ids（Node 3 查出来的）

  // 结果
  outcome: "SOLVED" | "ESCALATED" | "TERMINATED";
  escalation_count: number;

  timestamp: string;
}
```

Module 4 用这些数据更新 `kp_mastery[kp_id]`。

### 5.2 Module 4 → Module 2：routing_hint

```typescript
interface RoutingHint {
  student_id: string;
  is_new_student: boolean; // < 3 次干预

  // 维度画像
  dimension_ratio: number; // 0.0-1.0
  recent_dimensions: string[]; // 最近10次维度

  // 薄弱分析
  weak_dimensions: string[]; // 如 ["RESOURCE_R2", "METACOGNITIVE_M3"]

  // 建议
  recommended_dimension: "RESOURCE" | "METACOGNITIVE" | "neutral";

  // 置信度
  confidence: number; // 0.0-1.0
}
```

Node 2a 和 Node 2b 读取 `routing_hint` 辅助决策。

---

## 6. 与 Module 6 (RAG) 的接口

Module 6 提供 ChromaDB 向量检索能力，供 Node 4 调用。

```python
class ChromaClient:
    """Module 6 提供"""

    async def query(
        self,
        query_texts: list[str],
        n_results: int = 3,
        where: dict | None = None,
    ) -> dict:
        """向量检索"""
        pass

    async def upsert(
        self,
        collection: str,
        documents: list[dict],
    ) -> None:
        """批量导入（Module 6 ingestion 时使用）"""
        pass
```

**ChromaDB Schema**（由 Module 6 ingestion 填充）：

| 字段               | 类型        | 示例                    |
| ------------------ | ----------- | ----------------------- |
| `id`               | string      | `kp_KP_2_04`            |
| `embedding`        | float[1536] | 向量                    |
| `document`         | string      | 知识点内容              |
| `metadata.kp_id`   | string      | `KP_2_04`               |
| `metadata.type`    | string      | `knowledge` \| `method` |
| `metadata.chapter` | int         | `2`                     |

---

## 7. 评估指标

| 指标                       | 定义                                          | 目标   | 采集            |
| -------------------------- | --------------------------------------------- | ------ | --------------- |
| **知识点引用率**           | 提示引用了 KGContext 中至少一个 kp 名称的比例 | > 90%  | Node 5 输出埋点 |
| **ChromaDB 降级率**        | ChromaDB 不可用导致仅用 JSON 的比例           | < 5%   | Node 4 日志     |
| **答案泄露率**             | OutputGuardrail 拦截的提示 / 总提示           | < 5%   | Node 6 统计     |
| **提示效率**               | 平均所需提示次数                              | < 3 次 | 会话分析        |
| **dimension_ratio 采纳率** | Node 2a 采纳 routing_hint 建议的比例          | > 70%  | Node 2a 埋点    |

---

## 8. 与旧版 v2 的差异

| 变更项           | v2                              | v3.1                               |
| ---------------- | ------------------------------- | ---------------------------------- |
| KGContext 构建   | Node 3 从 type_kp_mapping 推断  | **直接用断点 kp_ids 查询，无推断** |
| method inference | student_work 方法推断（已删除） | 无                                 |
| mismatch 检测    | dual_path 模式（已删除）        | 无                                 |
| KGContext 内容   | 推断后的 kp_ids                 | **断点原始 kp_ids**                |
| hint 深度        | 部分与 KGContext 挂钩           | **完全由 R/M 级别决定**            |
| ChromaDB         | 存在但未集成                    | **可选增强，通过 top_k 扩展**      |

---

## 9. 边界情况

| 场景                         | 处理                                                                     |
| ---------------------------- | ------------------------------------------------------------------------ |
| 断点 kp_ids 为空             | 取前一步的 kp_ids；若仍为空则 KGContext 为空，提示仍可生成（无知识引用） |
| method_id 为空               | KGContext.methods = []，提示仍可生成（只用知识点）                       |
| ChromaDB 不可用              | 降级到 json_only，Node 4 正常返回，Node 6 记录日志                       |
| KGContext 命中 0 个 kp       | KGContext.knowledge_points = []，Node 5 仍按级别生成提示（无引用）       |
| solution_step 无 kp_ids 标注 | Module 1 质量问题，应在开发阶段发现；运行时降级为 KGContext = {}         |

---

## 附录：数据流示例

**场景：学生做二次方程，WRONG_DIRECTION（用因式分解，canonical 是配方法）**

```
Module 1 输入:
  problem: "解方程 x²+3x+2=0"
  solution_steps: [
    s1: { content: "移项", kp_ids: ["KP_2_01"], method_id: null },
    s2: { content: "配方法...", kp_ids: ["KP_2_02"], method_id: "M_配方法" },  ← 断点
  ]
  student_steps: [
    "移项 x²+3x=-2",
    "用十字相乘 (x+1)(x+2)=0"  ← 对应不上 s2，WRONG_DIRECTION
  ]

────────────────────────────────────────────

Node 1: BreakpointLocator
  → type = WRONG_DIRECTION
  → expected_step = "配方法..."（s2 内容）
  → kp_ids = ["KP_2_02"]          ← 直接取 solution_step 标注
  → method_id = "M_配方法"

Node 2a: DimensionRouter
  → WRONG_DIRECTION → METACOGNITIVE
  → routing_hint.recommended_dimension = "METACOGNITIVE"（参考）

Node 2b: SubTypeDecider
  → dimension = METACOGNITIVE
  → 初次 → M1

Node 3: KGQueryBuilder
  → kp_ids = ["KP_2_02"]
  → method_ids = ["M_配方法"]
  → 无推断，无 mismatch 检测

Node 4: KGRetriever
  → 查 KP_2_02 内容（一元二次不等式解法 + 配方法公式）
  → 查 M_配方法 描述
  → ChromaDB 扩展（若有）

Node 5: HintGeneratorV2
  → level = M1
  → KGContext 注入：KP_2_02 + M_配方法
  → M1 提示（最浅，不直接说方法）：
    "你有自己的思路了！
    实际上这道题用配方法的标准步骤是：
    x²+3x+2 = x²+3x+(3/2)² - (3/2)² + 2 = (x+3/2)² - 1/4
    ...
    你愿意继续用十字相乘，还是看看配方法怎么走？"

Node 6: OutputGuardrail
  → 无答案关键词 ✓
  → 引用了 KP_2_02 知识点名称 ✓
  → 通过
```

---

_本文档为 Module 2 v3.1 产品需求定义，核心变化：KGContext 仅做断点 kp_ids 查询，hint 深度由 R/M 级别决定。如有疑问，请联系 Module 2 产品负责人。_
