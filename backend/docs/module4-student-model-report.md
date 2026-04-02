# Module 4: 学生画像系统 — 技术架构报告

> 基于开源调研 + 项目现有能力分析
> 生成日期：2026-03-28

---

## 一、需求定位

Module 4（学生画像）的核心任务，是在 Module 1（解题）和 Module 2（干预）的交互数据之上，构建每个学生的**长期认知模型**，支撑 Module 3（推荐）和 Module 5（教学策略）。

Module 4 不是从零构建认知模型——Module 2 的五节点管道已经对每次干预做了双维度诊断（R/M），这是学生画像最核心的数据来源。

---

## 二、开源方案调研结论

### 2.1 主流技术路线对比

| 技术路线                 | 代表项目             | 数据需求             | 可解释性 | 实现难度 | 是否适合本项目        |
| ------------------------ | -------------------- | -------------------- | -------- | -------- | --------------------- |
| **BKT** (贝叶斯知识追踪) | pyBKT (249⭐)        | 低（几十条数据即可） | 高       | 低       | ⚠️ 需预设知识图谱     |
| **DKT** (深度知识追踪)   | mmkhajah/dkt (101⭐) | 高（需数千条序列）   | 低       | 中       | ❌ 高中数学题数据不足 |
| **DKVMN** (记忆网络)     | EduStudio 内置       | 高                   | 中       | 高       | ❌ 同上               |
| **Transformer-based KT** | DTransformer, SAKT   | 高                   | 中       | 高       | ❌ 同上               |
| **LLM-based**            | DeepTutor, EduAgent  | 中                   | 中       | 低       | ✅ 已有 qwen-turbo    |
| **Cognitive Diagnosis**  | NeuralCD 系列        | 中                   | 高       | 中       | ✅ 可借鉴             |

### 2.2 推荐参考项目

**① pyBKT** — 最佳可解释贝叶斯实现，NeurIPS 2015 原生 DKT 团队后续工作，249⭐，C++ 核心 + Python 绑定，EDM 2021 论文

**② EduStudio** (HFUT-LEC/EduStudio, 72⭐) — FCS 2025 论文，统一知识追踪框架，内置 DKT/DKVMN/SAKT 等 10+ 模型，开箱即用

**③ DTransformer** (yxonic/DTransformer, 44⭐) — WWW 2023，"Stable Knowledge Tracing with Diagnostic Transformer"，兼顾准确率和可解释性

**④ DeepTutor** (HKUDS/DeepTutor, 10,870⭐) — LLM-based 个性化学习助手，AI-Powered，自带推荐能力

**⑤ EduAgent** (EduAgent/EduAgent, 32⭐) — LLM 生成式学生模拟，适合研究场景

**⑥ ORCDF** (ECNU-ILOG/ORCDF) — KDD 2024，过平滑抵抗认知诊断，适合图结构知识建模

---

## 三、架构设计

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Module 4: 学生画像                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   事件输入层                                                 │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│   │ Module 1     │  │ Module 2     │  │ Module 3     │    │
│   │ Solving 事件  │  │ Intervention │  │ Recommendation│   │
│   │ (解题结果)    │  │ 事件 (R/M)   │  │ 反馈事件      │    │
│   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│          │                 │                  │            │
│          └────────────┬────┴──────────────────┘            │
│                       ▼                                     │
│   画像更新层                                                  │
│   ┌─────────────────────────────────────────────────────┐  │
│   │              StudentProfileService                   │  │
│   │   ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │  │
│   │   │ 概念 mastery │  │ 维度轨迹    │  │ 行为模式  │  │  │
│   │   │ 追踪器      │  │ 分析器      │  │ 分析器    │  │  │
│   │   └─────────────┘  └─────────────┘  └───────────┘  │  │
│   └─────────────────────────────────────────────────────┘  │
│                       │                                     │
│   数据存储层（MongoDB）                                      │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│   │ student_profiles│ │ concept_mastery│ │ learning_trajectories│ │
│   └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                             │
│   API 层                                                    │
│   GET  /students/{id}/profile    → 学生画像总览             │
│   GET  /students/{id}/mastery    → 概念掌握情况              │
│   GET  /students/{id}/dimension  → R/M 维度分析             │
│   POST /students/{id}/snapshot   → 手动触发快照             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 核心数据模型

```python
class StudentProfile(BaseModel):
    """学生画像主文档"""
    student_id: str
    session_ids: List[str]                    # 关联的 session

    # 画像基本信息
    total_sessions: int = 0
    total_problems_attempted: int = 0
    total_problems_solved: int = 0
    overall_accuracy: float = 0.0

    # 概念掌握情况 (knowledge concept → mastery level)
    # mastery: 0.0-1.0，1.0 表示完全掌握
    concept_mastery: Dict[str, float] = {}

    # 双维度轨迹（来自 Module 2 诊断）
    # Resource 维度问题数 vs Metacognitive 维度问题数
    dimension_counts: Dict[str, int] = {"resource": 0, "metacognitive": 0}

    # 维度比率（反映学生困难特征）
    # R/M_ratio > 1 表示知识型困难为主
    # R/M_ratio < 1 表示元认知型困难为主
    dimension_ratio: float = 1.0

    # 干预记录摘要
    total_interventions: int = 0
    escalation_count: int = 0                  # 升级次数
    max_level_reached: str = ""               # 最高到达级别

    # 学习轨迹（时序数据）
    learning_history: List[LearningSnapshot] = []

    # LLM 生成画像（可选，由 LLM 分析长期数据生成）
    llm_summary: Optional[str] = None
    cognitive_strengths: List[str] = []
    cognitive_gaps: List[str] = []

    updated_at: datetime
    created_at: datetime


class LearningSnapshot(BaseModel):
    """学习快照（每次 session 结束后更新）"""
    session_id: str
    timestamp: datetime

    # 题目级数据
    problem_id: str
    topic: str                                # 题目所属知识点
    correctness: bool

    # 干预数据（来自 Module 2）
    breakpoint_type: str                      # MISSING_STEP / WRONG_DIRECTION / ...
    dimension: str                           # RESOURCE / METACOGNITIVE
    prompt_level: str                        # R1-R4 / M1-M5
    intervention_count: int = 0
    escalated: bool = False

    # 行为数据
    response_time_seconds: Optional[float] = None
    hint_count: int = 0


class ConceptMasteryUpdate(BaseModel):
    """概念掌握更新事件"""
    student_id: str
    concept: str                              # 知识点标签
    delta: float                              # 掌握度变化 (+/-)
    source: str                               # "solving" | "intervention"
    evidence: str                             # LLM 生成的证据描述
```

---

## 四、技术实现路径

### 4.1 阶段一：事件驱动画像构建（推荐先做）

**目标**：接入现有事件系统，从 Module 1/2 的交互数据中自动构建学生画像。

**实现方式**：

1. 在 `StudentProfileService` 中注册事件监听器，订阅：
   - `solving.completed` — 题目解答完成事件
   - `intervention.hint_delivered` — 干预提示交付事件
   - `intervention.escalated` — 干预升级事件

2. 每次事件到达，更新 `StudentProfile` 文档：
   - 更新 `concept_mastery`（基于题目涉及的概念标签）
   - 更新 `dimension_counts`（基于 Module 2 的 R/M 诊断结果）
   - 追加 `learning_history` 快照

3. 概念标签来源：
   - Module 1 的 `TeachingStep` 中包含 step_name，可作为粗糙的概念标签
   - 可维护一个**知识点-步骤映射表**（手填 or LLM 自动生成）

**数据流**：

```
Module 1/2 触发事件
    → EventBus 广播
    → StudentProfileService 订阅
    → 更新 MongoDB student_profiles
    → 可选：推送到 Module 3 推荐系统
```

**优点**：不依赖额外模型，利用现有事件系统快速上线
**缺点**：概念粒度粗糙，缺乏深层推理

---

### 4.2 阶段二：轻量级认知诊断（BKT 可选扩展）

如果阶段一数据积累充分后，可以引入 **pyBKT** 做精细化概念掌握度推断：

```python
# 概念级别的贝叶斯追踪（每个概念独立 BKT）
from pybkt.models import Model

class ConceptBKTTracker:
    def __init__(self):
        self.models: Dict[str, "pybkt.models.Model"] = {}

    def update(self, concept: str, correct: bool) -> float:
        """更新概念掌握概率，返回新的 P(L)"""
        if concept not in self.models:
            self.models[concept] = Model()
            # 初始化参数
            self.models[concept].params = {
                "learn_rate": 0.1,
                "guess_rate": 0.2,
                "slip_rate": 0.1,
            }

        # BKT 更新
        mastery_prob = self.models[concept]. likelihood(correct)
        return mastery_prob
```

**何时用 BKT**：

- 某个概念有 50+ 次交互数据时，BKT 推断才稳定
- 高中数学场景下，核心概念（如"数列通项"、"三角函数化简"）重复出现率高，适合 BKT
- 不需要预设完整知识图谱，只需按题目定义零散概念标签

---

### 4.3 阶段三：LLM 生成式画像分析（最终形态）

当学生有 10+ 条 session 历史后，可以用 LLM 生成深度画像报告：

**Prompt 模板**：

```
你是一位高中数学教学专家。请分析以下学生学习历史，生成画像报告。

学生学习历史：
{格式化后的 learning_history}

Module 2 干预记录摘要：
- Resource 维度问题占比：{dimension_ratio}
- 最高到达提示级别：{max_level_reached}
- 升级次数：{escalation_count}

请生成：
1. 认知优势（学生擅长什么类型的题目/方法）
2. 认知薄弱点（经常在哪些地方卡住）
3. 学习行为特征（是否有反复看提示的习惯、是否主动反思）
4. 改进建议（针对薄弱点的练习方向）

输出格式：JSON
```

**输出结构**：

```json
{
  "cognitive_strengths": ["代数变形能力强", "愿意尝试多种方法"],
  "cognitive_gaps": ["几何构造思路单一", "归纳假设书写不规范"],
  "behavior_patterns": ["提示接受率高但转化率低", "喜欢跳步"],
  "recommendations": ["推荐多练习几何证明题", "建议使用 M3 以下级别提示"],
  "dimension_analysis": {
    "primary_difficulty": "metacognitive",
    "explanation": "学生知道方法但在关键时刻想不到调用"
  }
}
```

---

## 五、与 Module 2 的协同设计

Module 2 的五节点管道是学生画像最重要的数据来源：

### 5.1 数据复用

| Module 2 数据                            | 学生画像用途                                                                      |
| ---------------------------------------- | --------------------------------------------------------------------------------- |
| `breakpoint_type`                        | 判断学生困难类型分布（MISSING_STEP 多 → 知识缺口；WRONG_DIRECTION 多 → 策略缺失） |
| `dimension_result` (R/M)                 | 直接填入 `dimension_counts`，计算 `dimension_ratio`                               |
| `sub_type_result.sub_type` (R1-R4/M1-M5) | 追踪学生需要提示的"重度"程度                                                      |
| `escalation_decision`                    | 追踪升级次数，反映学习自主性                                                      |
| `intervention_memory`                    | 分析 Q&A 对话模式，判断学生是否有主动反思习惯                                     |

### 5.2 画像对 Module 2 的反馈

```
学生画像（Module 4）
    ↓
Module 2 可查询学生历史
    ↓
HintGeneratorV2 调整提示策略：
  - 认知优势学生 → 提示更抽象，给方向不给方法
  - 认知薄弱学生 → 提示更具体，增加示例
  ↓
Module 1 SolvingStrategy 选择：
  - Resource 主导学生 → 推荐更多知识讲解内容
  - Metacognitive 主导学生 → 推荐更多策略反思任务
```

---

## 六、MongoDB 集合设计

### 6.1 `student_profiles` 集合

```javascript
{
  _id: ObjectId,
  student_id: "student_001",          // 索引（唯一）
  session_ids: ["sess_001", "sess_002"],
  total_sessions: 12,
  concept_mastery: {
    "数列通项公式": 0.75,
    "数学归纳法": 0.45,
    "三角恒等变形": 0.82,
    "几何辅助线": 0.30
  },
  dimension_counts: { resource: 8, metacognitive: 15 },
  dimension_ratio: 0.53,               // metacognitive 主导
  total_interventions: 23,
  escalation_count: 5,
  max_level_reached: "R3",
  cognitive_strengths: ["代数运算规范", "愿意动手计算"],
  cognitive_gaps: ["几何直觉较弱", "容易在第一步卡住"],
  llm_summary: "学生代数能力强，几何和策略方面需要加强...",
  learning_history: [/* LearningSnapshot 数组 */],
  updated_at: ISODate("2026-03-28T12:00:00Z"),
  created_at: ISODate("2026-03-01T10:00:00Z")
}
```

**索引**：

- `student_id`: unique index
- `updated_at`: TTL index（可选，保留一年）
- `dimension_ratio`: 多维索引（用于筛选特定画像特征的学生）

### 6.2 `student_sessions` 集合（可选，长期数据）

每个学生在每个 session 的详细记录，供 LLM 画像分析使用：

```javascript
{
  _id: ObjectId,
  student_id: "student_001",
  session_id: "sess_001",
  problems: [/* 每道题的详细信息 */],
  interventions: [/* 每次干预的详情 */],
  profile_snapshot: {/* 该 session 结束时的画像快照 */}
}
```

---

## 七、实施计划

### Phase 1：基础设施 + 事件接入（约 1 周）

**文件结构**：

```
app/modules/student_model/
├── __init__.py
├── models.py            # Pydantic 模型（StudentProfile, LearningSnapshot）
├── service.py           # StudentProfileService（事件监听 + MongoDB 读写）
├── event_handler.py     # 事件处理器（订阅 Module 1/2 事件）
├── api/
│   └── routes.py        # API 端点
└── prompts/
    └── profile_prompt.py # LLM 画像生成 prompt

tests/modules/test_student_model/
├── test_models.py
├── test_service.py
└── test_event_handler.py
```

**交付物**：

- `StudentProfile` MongoDB 文档 CRUD
- 事件监听器（接入 `solving.completed`、`intervention.hint_delivered`）
- API: `GET /students/{id}/profile`

### Phase 2：维度追踪 + 概念标签（约 1 周）

**交付物**：

- `dimension_ratio` 自动计算和更新
- 题目概念标签体系（可从 Module 1 TeachingStep 提取）
- `concept_mastery` 追踪（简单计数模型即可）
- API: `GET /students/{id}/mastery`、`GET /students/{id}/dimension`

### Phase 3：LLM 生成式画像（约 1 周）

**交付物**：

- 画像报告生成接口（基于 `learning_history` + `dimension_ratio`）
- `cognitive_strengths`、`cognitive_gaps` 自动标注
- API: `POST /students/{id}/generate-profile`（手动触发）

### Phase 4（可选）：BKT 精细化追踪

**前置条件**：某概念有 50+ 次交互数据
**交付物**：概念级 BKT 追踪，替代简单计数模型

---

## 八、技术选型总结

| 组件             | 选型                 | 理由                                                                |
| ---------------- | -------------------- | ------------------------------------------------------------------- |
| **认知诊断模型** | 事件驱动 + LLM 生成  | 高中数学题数据量有限，BKT/DKT 冷启动难；qwen-turbo 已部署，直接复用 |
| **长期记忆存储** | MongoDB              | 已有 Motor 基础设施，文档模型天然适配画像结构                       |
| **画像更新机制** | 事件驱动             | Module 1/2 已有 EventBus，不增加耦合                                |
| **概念标签**     | 从 TeachingStep 提取 | Module 1 的 TeachingStep.step_name 可直接作为概念标签，无需额外标注 |
| **概念掌握度**   | 简单计数 + 可选 BKT  | 数据少时用计数，数据充分后切换 BKT                                  |

**最小可行产品（MVP）**：Phase 1 + Phase 2，2 周可交付，之后 Module 3 推荐系统即可接入学生画像数据。

---

## 附录：参考项目链接

| 项目         | 地址                               | 用途                       |
| ------------ | ---------------------------------- | -------------------------- |
| pyBKT        | github.com/CAHLR/pyBKT             | BKT 参考实现               |
| EduStudio    | github.com/HFUT-LEC/EduStudio      | 多模型 KT 框架             |
| DTransformer | github.com/yxonic/DTransformer     | 可解释 Transformer KT      |
| DeepTutor    | github.com/HKUDS/DeepTutor         | LLM-based ITS 参考         |
| dialogue-kt  | github.com/umass-ml4ed/dialogue-kt | LLM + 知识追踪（LAK 2025） |
