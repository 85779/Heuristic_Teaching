# 相关学术论文整理

> 本项目：高中数学智能教辅系统 — 双维度诊断（Resource/Metacognitive）+ 分层递进干预
> 目标期刊：CCF-B（ Computers & Education / 中文核心期刊）

---

## 一、核心参考文献（直接支撑本项目设计）

### 1.1 双维度诊断框架（Resource vs Metacognitive）

| 论文                                                                           | 作者                             | venue                               | 年份 | 核心贡献                                                                                                           | 对本项目的支撑                        |
| ------------------------------------------------------------------------------ | -------------------------------- | ----------------------------------- | ---- | ------------------------------------------------------------------------------------------------------------------ | ------------------------------------- |
| Do prior domain knowledge and motivation play different roles?                 | Zhang et al.                     | Contemporary Educational Psychology | 2022 | 实证研究证明 Domain Knowledge（资源型困难）与 Metacognitive Strategy（元认知型困难）是两个独立维度，需不同干预策略 | **直接支撑**本项目的 R/M 二元分流设计 |
| Improving students' help-seeking skills using metacognitive feedback in ITS    | Roll, Aleven, McLaren, Koedinger | Computers in Human Behavior         | 2011 | 元认知反馈能显著提升学生的 help-seeking 行为；区分"知道答案但不知道何时求助"vs"不知道怎么做"                       | 支撑 Metacognitive 维度的干预策略设计 |
| The Help Tutor: Does Metacognitive Feedback Improve Students' Help-Seeking?    | Roll et al.                      | AIED                                | 2006 | 元认知 tutoring 系统，提升学生主动求助能力                                                                         | M1-M5 元认知提示级别的理论基础        |
| The sub-dimensions of metacognition and their influence on modeling competency | —                                | Humanities and Social Sciences      | 2023 | 元认知的子维度分析（计划、监控、评估），可映射到 M1-M5 级别                                                        | 支撑 M 维度内部的分级设计             |
| Metacognition and Mathematical Modeling Skills                                 | —                                | PMC                                 | 2024 | 元认知在高中数学建模中的作用，证明 metacognitive 困难独立于 domain knowledge                                       | 数学学科的 R/M 二元诊断实证支撑       |

### 1.2 分层递进提示生成（Progressive Hint Scaffolding）

| 论文                                                                                     | 作者                              | venue                                | 年份 | 核心贡献                                                                                                                      | 对本项目的支撑                                 |
| ---------------------------------------------------------------------------------------- | --------------------------------- | ------------------------------------ | ---- | ----------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| Navigating the Landscape of Hint Generation Research: From the Past to the Future        | Jangra, Mozafari, Jatowt, Muresan | TACL / arXiv                         | 2025 | **最全面的提示生成综述**，覆盖100+篇论文，提出提示的解剖学框架（语用/语义/风格）；指出未来方向包括 LLM-based 生成和自适应递进 | **高优先级必读**；提示生成系统设计的理论基础   |
| Automatic Generation of Question Hints for Mathematics Problems using LLMs               | Tonga, Clement, Oudeyer           | NeurIPS Workshop (FM-EduAssess)      | 2024 | 用 GPT-4o/LLaMA-3 系统性评估数学提示生成质量；提出错误分类法（error taxonomy）；证明 LLM 能生成与专家相当的教学提示           | **直接相关**；高中数学提示生成的 baseline 方法 |
| Give me a hint: Can LLMs get a hint to solve math problems?                              | —                                 | arXiv                                | 2024 | 评估 LLM 接收渐进提示后的问题解决能力；证明 progressive hint 框架的有效性                                                     | 支撑 R1-R4 递进设计                            |
| Effect of intelligent tutoring system-delivered scaffolding                              | —                                 | ScienceDirect                        | 2026 | ITS 中 scaffolding 的有效性实证研究                                                                                           | 递进式干预有效性的证据                         |
| SMART: Student Modeling Approach for Responsive Tutoring                                 | Shute                             | User Modeling & Adaptive Interaction | 1995 | 响应式 tutoring 的早期框架，基于学生模型调整难度                                                                              | 响应式提示的理论基础                           |
| Staying in the Sweet Spot: Responsive Reasoning via Capability-Adaptive Hint Scaffolding | —                                 | arXiv                                | 2025 | 自适应 scaffolding 维持学生在"挑战-挫折"的最优区间                                                                            | 提示强度自动调节的理论                         |

### 1.3 断点检测与错误诊断

| 论文                                                                                 | 作者                                    | venue | 年份 | 核心贡献                                                                 | 对本项目的支撑                                 |
| ------------------------------------------------------------------------------------ | --------------------------------------- | ----- | ---- | ------------------------------------------------------------------------ | ---------------------------------------------- |
| Stepwise Verification and Remediation of Student Reasoning Errors with LLM Tutors    | Daheim, Macina, Kapur, Gurevych, Sachan | EMNLP | 2024 | LLM 检测学生推理第一步错误并生成针对性补救；减少幻觉；1,002 条标注推理链 | **直接相关**；BreakpointLocator 语义匹配的参考 |
| MathMistake Checker: Step-by-Step Math Problem Mistake Finding by Prompt-Guided LLMs | Zhang, Jiang et al.                     | arXiv | 2025 | LLM 做逐步数学错因检测；prompt-guided 方法                               | 断点定位（breaker.py）参考                     |
| MalruleLib: Large-Scale Executable Misconception Reasoning with Step Traces          | Stanford SCALE Initiative               | arXiv | 2026 | 大规模可执行 misconception 推理数据集 + step traces                      | 构建 misconception 库的参考                    |
| Buggy rule diagnosis for combined steps through final answer evaluation              | van der Hoek, Jeuring, Bos              | arXiv | 2025 | 诊断组合步骤中的错误规则                                                 | 多步推理错误诊断参考                           |
| Wheel-Spinning: Students Who Fail to Master a Skill                                  | —                                       | AIED  | 2013 | **Wheel-Spinning 概念定义**：学生反复失败但不进步                        | 本项目"升级到 R4 后仍失败"的理论基础           |
| Early Detection of Wheel-Spinning in ASSISTments                                     | Wang, Kai, Baker                        | AIED  | 2020 | 深度学习早期检测 Wheel-Spinning                                          | 升级决策（R4 MAX → 终止干预）的参考            |
| Towards Detecting Wheel-Spinning: Future Failure in Mastery Learning                 | Gong, Beck                              | AIED  | 2015 | 在 Wheel-Spinning 发生前预测                                             | 预防性干预的参考                               |
| Evaluating Task-Level Struggle Detection Methods in ITS for Programming              | Dannath, Deriyeva, Paaßen               | GI    | 2023 | 编程 ITS 中的任务级困难检测                                              | 检测方法论参考                                 |

### 1.4 知识追踪与认知诊断

| 论文                                                              | 作者                                                          | venue   | 年份 | 核心贡献                                                         | 对本项目的支撑              |
| ----------------------------------------------------------------- | ------------------------------------------------------------- | ------- | ---- | ---------------------------------------------------------------- | --------------------------- |
| Deep Knowledge Tracing                                            | Piech, Bassen, Huang, Ganguli, Sahami, Guibas, Sohl-Dickstein | NeurIPS | 2015 | **DKT 奠基之作**；LSTM 对学生知识状态建模；Khan Academy 数据验证 | Module 4 认知诊断的理论基础 |
| Neural Cognitive Diagnosis for Intelligent Education Systems      | Wang, Liu, Chen, Huang et al.                                 | AAAI    | 2020 | 神经网络认知诊断模型；直接估计学生掌握度                         | Neural CD 框架参考          |
| Interpretable Cognitive Diagnosis with Neural Network             | Wang et al.                                                   | arXiv   | 2019 | 可解释认知诊断                                                   | Module 4 可解释性参考       |
| EduLoop-Agent: Closed-Loop Diagnosis-Recommendation-Feedback      | Wang, Zheng, Zeng                                             | arXiv   | 2025 | **闭环系统**：认知诊断 → 推荐 → 反馈；整合 BECAT 和 LLM          | **最相关的闭环架构设计**    |
| A Closed-Loop Personalized Learning Agent                         | Wang, Zheng, Zeng                                             | arXiv   | 2025 | 同上；诊断-推荐-反馈完整闭环                                     | 同上                        |
| Survey of Knowledge Tracing: Models, Variants, and Applications   | Shen, Liu, Huang et al.                                       | arXiv   | 2024 | BKT/DKT 全面综述；taxonomy 和开源库（EduKTM）                    | Module 4 技术选型参考       |
| pyBKT: An Accessible Python Library of Bayesian Knowledge Tracing | Badrinath, Wang, Pardos                                       | EDM     | 2021 | BKT 的权威 Python 实现；C++ 核心                                 | Module 4 BKT 实现参考       |
| Deep Knowledge Tracing                                            | Piech et al.                                                  | NeurIPS | 2015 | LSTM-based 知识追踪                                              | Module 4 DKT 参考           |
| ConceptKT: A Benchmark for Concept-Level Deficiency Prediction    | —                                                             | arXiv   | 2026 | 概念级缺陷预测 benchmark                                         | Module 4 概念标签参考       |

---

## 二、系统架构参考

| 论文                                                                        | 作者                 | venue                         | 年份 | 核心贡献                                           | 对本项目的支撑                               |
| --------------------------------------------------------------------------- | -------------------- | ----------------------------- | ---- | -------------------------------------------------- | -------------------------------------------- |
| A systematically derived AI-based framework for student-centered learning   | —                    | ScienceDirect                 | 2025 | AI-based 学生中心学习框架                          | 系统设计方法论                               |
| A Dual-Fusion Cognitive Diagnosis Framework                                 | Liu et al.           | arXiv                         | 2023 | 融合多数据源的认知诊断                             | Module 4 多维度融合                          |
| MetaTutor: Leveraging Multichannel Data to Scaffold Self-Regulated Learning | Azevedo et al.       | Frontiers in Psychology       | 2022 | **最完整的元认知 ITS**；眼动等多通道数据；SRL 理论 | MetaTutor 的架构是本项目 Module 5 的重要参考 |
| Adaptive metacognitive prompting in young learners                          | —                    | ScienceDirect                 | 2025 | 适应性元认知提示                                   | Module 5 策略生成参考                        |
| EduStudio: towards a unified library for student cognitive modeling         | —                    | Frontiers of Computer Science | 2025 | 统一认知建模库（BKT/DKT/DINA 等10+模型）           | Module 4 工程实现参考                        |
| A General Multi-method Approach to Design-Loop Adaptivity in ITS            | Huang, Aleven et al. | AIED                          | 2020 | 多层次自适应框架（设计/交互/反馈）                 | 多层次干预架构参考                           |

---

## 三、提示生成与 LLM 相关

| 论文                                                                                   | 作者                                           | venue                     | 年份 | 核心贡献                                                                | 对本项目的支撑                                                |
| -------------------------------------------------------------------------------------- | ---------------------------------------------- | ------------------------- | ---- | ----------------------------------------------------------------------- | ------------------------------------------------------------- |
| From Problem-Solving to Teaching Problem-Solving: Aligning LLMs with Pedagogy using RL | Dinucu-Jianu, Macina, Daheim, Gurevych, Sachan | EMNLP                     | 2025 | **RL 对齐 LLM 到教学策略**；平衡教学指导与直接给答案；7B 模型媲美大模型 | **极高优先级**；HintGeneratorV2 的 pedagogical alignment 参考 |
| Progressive-Hint Prompting Improves Reasoning in Large Language Models                 | Zheng et al.                                   | ICML Workshop             | 2024 | LLM progressive hint prompting；用提示提升推理                          | HintGeneratorV2 的 prompt 策略参考                            |
| Give me a hint: Can LLMs get a hint to solve math problems?                            | —                                              | arXiv                     | 2024 | LLM 接收提示后解决数学问题                                              | 同上                                                          |
| Designing and Evaluating Hint Generation Systems for Science Education                 | Jangra, Muresan                                | Columbia                  | 2024 | 提示生成系统的设计与评估框架                                            | 评估方法论                                                    |
| Assessing large language models for math tutoring effectiveness                        | Goel, Ghanta                                   | J. Emerging Investigators | 2025 | LLM 数学 tutoring 效果评估                                              | 评估体系参考                                                  |
| Beyond Final Answers: Evaluating LLMs for Math Tutoring                                | Gupta et al.                                   | arXiv                     | 2025 | 多维 LLM tutoring 评估                                                  | 评估维度参考                                                  |
| Enhancing LLM-Based Feedback: Insights from ITS and Learning Sciences                  | Stamper, Xiao, Hou                             | arXiv                     | 2024 | Carnegie Mellon；ITS 原则指导 LLM 反馈设计                              | HintGeneratorV2 质量准则                                      |
| ChatGPT Scaffolding in Supporting Metacognition for Limit Concepts                     | Huda, Anwar et al.                             | JITE                      | 2025 | ChatGPT 元认知 scaffolding 在微积分教学中的应用                         | M 维度提示的实证参考                                          |

---

## 四、开源工具与数据集

| 工具/数据集      | 地址                           | 说明                                    |
| ---------------- | ------------------------------ | --------------------------------------- |
| **pyBKT**        | github.com/CAHLR/pyBKT         | BKT 权威实现（EDM 2021）                |
| **EduStudio**    | github.com/HFUT-LEC/EduStudio  | 统一认知建模库（BKT/DKT/DINA，10+模型） |
| **DTransformer** | github.com/yxonic/DTransformer | Diagnostic Transformer KT（WWW 2023）   |
| **pyKT Toolkit** | pykt.org                       | Deep KT benchmark 框架                  |
| **EduKTM**       | —                              | Knowledge Tracing 模型集合              |
| **ASSISTments**  | assistments.org                | KT 标准数据集                           |
| **EdNet**        | —                              | 音乐教育 KT 数据集                      |
| **MalruleLib**   | Stanford SCALE                 | 可执行 misconception 推理数据集         |
| **DeepTutor**    | github.com/HKUDS/DeepTutor     | 多 Agent 个性化学习平台（10,870⭐）     |

---

## 五、按主题分类的关键论文

### 主题 A：R/M 二元诊断框架

1. **Zhang et al. 2022** — Domain Knowledge vs Metacognitive Strategy（核心理论）
2. **Roll et al. 2011** — Help-seeking metacognitive feedback（Metacognitive 干预）
3. **Azevedo et al. 2022** — MetaTutor SRL scaffolding（完整元认知 ITS）
4. **Wang et al. 2025** — EduLoop-Agent（诊断-推荐-反馈闭环）

### 主题 B：分层递进提示（R1-R4 / M1-M5）

1. **Jangra et al. 2024/2025** — Hint Generation 综述（必读）
2. **Tonga et al. 2024** — LLM 数学提示生成（NeurIPS，直接应用）
3. **Daheim et al. 2024** — Stepwise Verification（错误定位 → 提示）
4. **Dinucu-Jianu et al. 2025** — RL 教学对齐 EMNLP 2025（防止直接给答案）
5. **Zheng et al. 2024** — Progressive-Hint Prompting（LLM 递进推理）

### 主题 C：断点定位与错误检测

1. **Wang, Kai, Baker 2020** — Wheel-Spinning 早期检测（AIED）
2. **Daheim et al. 2024** — Stepwise Verification（第一步错误检测）
3. **Gong, Beck 2015** — Wheel-Spinning 预测
4. **Dannath et al. 2023** — 任务级困难检测
5. **Zhang et al. 2025** — MathMistake Checker（LLM 错因检测）

### 主题 D：认知诊断与知识追踪

1. **Piech et al. 2015** — Deep Knowledge Tracing（NeurIPS，奠基）
2. **Wang et al. 2020** — Neural Cognitive Diagnosis（AAAI，Neural CD）
3. **Badrinath et al. 2021** — pyBKT（EDM，权威实现）
4. **Shen et al. 2024** — Knowledge Tracing 综述（2024 最新）
5. **Wang et al. 2025** — EduLoop-Agent（闭环）

---

## 六、论文写作定位（本项目创新点可对标的工作）

### 创新点 1：双维度诊断（Resource vs Metacognitive）

**对标理论**：

- Zhang et al. (2022) — Domain knowledge vs Metacognitive 是两个独立维度
- Roll et al. (2011) — 元认知反馈有效性
- 本项目的创新：在线实时推断 R/M 维度，并据此选择不同提示模板

### 创新点 2：九级递进提示（R1-R4 / M1-M5）

**对标理论**：

- Jangra et al. (2024) — 提示解剖学框架
- Tonga et al. (2024) — LLM 生成数学提示
- 本项目的创新：**自动升级机制**（学生未进步时自动升到下一级），结合 R/M 维度设计

### 创新点 3：五节点干预管道

**对标理论**：

- EduLoop-Agent (Wang et al. 2025) — 诊断-推荐-反馈闭环
- MetaTutor (Azevedo et al. 2022) — 多通道 SRL 支持
- 本项目的创新：**逻辑断点定位**（无需 LLM）+ **LLM 生成提示**的混合架构

### 创新点 4：Output Guardrail（防答案泄露）

**对标理论**：

- Dinucu-Jianu et al. (2025) — RL 对齐防止直接给答案
- Stamper et al. (2024) — ITS 原则指导 LLM 反馈
- 本项目的创新：规则 + LLM 双层 guardrail，R/M 维度级别差异化

---

## 七、目标期刊可投论文类型

### 方案 A：技术系统论文（侧重工程创新）

**适合投：**

- Computers & Education（Elsevier，CCF-B）
- British Journal of Educational Technology（SSCI）
- Journal of Educational Computing Research（SSCI）

**论文结构：**

1. 介绍 ITS 现有系统的不足（hint 质量、维度诊断缺失）
2. 提出双维度 + 九级提示框架
3. 五节点管道技术实现
4. 在线实验 / 模拟用户评估
5. 与现有系统（如 ASSISTments）对比

### 方案 B：理论框架论文（侧重框架创新）

**适合投：**

- Journal of Artificial Intelligence in Education（Springer，CCF-B）
- Educational Data Mining（CCF-C）
- 中国中文期刊（计算机教育/现代教育技术）

**论文结构：**

1. 文献综述：R/M 二元诊断的认知心理学基础
2. 理论框架：分层递进提示的教学设计原则
3. 计算模型：五节点管道
4. 实证验证：学生数据实验

### 方案 C：ACL/EMNLP 子会（侧重 NLP 技术）

**适合投：**

- ACL/Findings（CCF-A）
- EMNLP（CCF-B）
- AIED / EDM（教育数据挖掘CCF-C）

**论文结构：**

1. 问题：现有提示生成缺乏教学对齐和维度感知
2. 方法：R/M 感知提示生成 + Guardrail
3. 实验：自动评测 + 学生实验
4. 分析：维度与提示级别的交互效应

---

## 八、必读论文优先级排序

### 🔴 第一优先级（直接支撑本项目设计）

| 论文                                             | 为什么读                                 |
| ------------------------------------------------ | ---------------------------------------- |
| Jangra et al. 2024/2025 — Hint Generation 综述   | 建立提示生成领域的整体认知，指导系统设计 |
| Zhang et al. 2022 — Domain vs Metacognitive      | R/M 二元诊断的实证基础                   |
| Wang et al. 2025 — EduLoop-Agent                 | 诊断-干预-反馈闭环的完整系统参考         |
| Daheim et al. 2024 — Stepwise Verification       | 断点定位 + 错误检测的具体方法            |
| Dinucu-Jianu et al. 2025 — RL Teaching Alignment | 防止提示直接给答案的方法论               |

### 🟡 第二优先级（技术实现参考）

| 论文                                    | 章节参考                           |
| --------------------------------------- | ---------------------------------- |
| Tonga et al. 2024 — LLM Hint Generation | HintGeneratorV2 的 prompt 设计     |
| Piech et al. 2015 — DKT                 | Module 4 知识追踪的理论            |
| Wang et al. 2020 — Neural CD            | Module 4 认知诊断模型              |
| Wang, Kai, Baker 2020 — Wheel-Spinning  | 升级决策（R4 MAX → 终止）的参考    |
| Roll et al. 2011 — Help-seeking         | Metacognitive 维度干预的心理学基础 |

### 🟢 第三优先级（拓展视野）

| 论文                                           | 收获                           |
| ---------------------------------------------- | ------------------------------ |
| Azevedo et al. 2022 — MetaTutor                | 多通道 SRL 的完整 ITS 参考     |
| Zheng et al. 2024 — Progressive-Hint Prompting | LLM progressive reasoning 技巧 |
| Stamper et al. 2024 — ITS Principles for LLM   | ITS 教学原则用于 LLM feedback  |
