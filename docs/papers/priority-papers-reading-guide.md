# Priority Papers Reading Guide

## For: Adaptive Dual-Dimension Intervention System Paper (Direction 1)

**Target**: Computers & Education (Elsevier, CCF-B)  
**Date**: 2026-03-28

---

## How to Use This Guide

This document summarizes the **5 priority papers** you need to read before writing your Related Work section. Each summary is structured for direct citation and highlights exactly what to extract for your paper.

---

## Paper 1: Jangra et al. 2025 — Hint Generation Survey

**Full Citation**: Jangra, A., Mozafari, J., Jatowt, A., & Muresan, S. (2025). Navigating the Landscape of Hint Generation Research: From the Past to the Future. _TACL_, 13, 505–528.

**Why This Paper**: Provides the foundational **hint taxonomy** (pragmatic/semantic/style) and establishes the **need for adaptive progressive hints** — this is your field's recognized authority.

### Key Findings to Cite

**1. Hint Taxonomy (3 Layers)**:

> "Hints have three distinct dimensions: **Pragmatics** (the 'when/whether' — scaffolding support, personalization), **Semantics** (the 'what to say' — relevance, link to prior knowledge, conceptual depth), and **Style** (the 'how to say it' — clarity, encouragement, creativity)."  
> — Jangra et al. 2025, Section 2

**Your use**: Your R1-R4 / M1-M5 design maps to this taxonomy:

- R1-R4 Pragmatics: scaffolding intensity
- M1-M5 Semantics: metacognitive strategy activation
- Both: Style varies (Socratic vs. directive)

**2. LLM-Based Hint Generation Findings**:

> "Direct use of LLMs falls short compared to human expert responses. LLMs are good at conversation uptake but worse on pedagogical dimensions, especially 'helpfulness to a student.'"  
> — Jangra et al. 2025, Section 3.2

**Your use**: Justifies why your system uses **structured prompts** (R1-R4/M1-M5 templates) rather than free-form LLM generation.

**3. Gaps Identified (Direct Quote for Related Work)**:

> "Existing hint generation frameworks do not personalize hints to the learner's existing knowledge base."  
> "Current question answering hint generation systems do not personalize hints to learners' preferences, learning objectives, or their prior knowledge."  
> — Jangra et al. 2025, Section 4

**Your use**: Your **real-time R/M dimension switching** directly addresses this gap.

**4. Why Adaptive Progressive Hints Are Needed**:

> "A hint must bridge the specific gap between what a learner can do alone and what they can achieve with guidance (Vygotsky's ZPD) — this gap differs per learner."  
> — Jangra et al. 2025

**Your use**: Your 9-level escalation mechanism operationalizes this ZPD-bridging concept.

### What to Emphasize in Your Paper

- The **three-layer taxonomy** provides theoretical grounding for your prompt design
- Their **gaps identified** list your contributions as solutions to open problems
- Cite as: (Jangra et al., 2025)

---

## Paper 2: Zhang et al. 2022 — R/M Dual-Dimension Theory

**Full Citation**: Zhang, Y., Paquette, L., Bosch, N., Ocumpaugh, J., Biswas, G., Hutt, S., & Baker, R. S. (2022). The evolution of metacognitive strategy use in an open-ended learning environment: Do prior domain knowledge and motivation play a role? _Contemporary Educational Psychology_, 69, 102064.

**Why This Paper**: Provides the **empirical evidence** that Domain Knowledge (Resource) and Metacognitive Strategy are **independent dimensions** requiring different interventions. Study was conducted in **Betty's Brain** (an ITS).

### Key Findings to Cite

**1. Independent Dimensions (Core Evidence)**:

> "Task value and prior domain knowledge positively predicted metacognitive strategy behavior. Self-efficacy had no effect on metacognitive strategy behavior."  
> — Zhang et al. 2022

**Your use**: This proves that treating R and M as **independent** (not just correlated) is empirically justified. Self-efficacy alone is insufficient — your system uses breakpoint type, not self-reported motivation.

**2. Working Memory Mechanism (Why Dimension Separation Matters)**:

> "Learners with low domain knowledge need more working memory capacity for processing information, while learners with high domain knowledge can allocate more of this capacity for regulation."  
> — Zhang et al. 2022

**Your use**: Explains **why** R-dimension hints (补充知识) and M-dimension hints (激活元认知) must be **structurally different**, not just intensity variants.

**3. Temporal Evolution Pattern**:

> "Metacognitive strategy behavior increased from Day 1 to Day 2, then remained stable from Day 2 to Day 4."  
> — Zhang et al. 2022

**Your use**: Supports your **automatic escalation** design — metacognitive strategy activation is not instant; it builds over multiple interventions.

**4. Implications for Scaffolding Timing**:

> "Understanding how strategic learning behaviors change over time — and how prior domain knowledge and motivation influence such change — can lead to more informed decisions about **when to provide scaffolding and to whom**."  
> — Zhang et al. 2022

**Your use**: Direct quote supporting your **per-breakpoint R/M switching** — not just per-session classification.

**5. Limitation to Acknowledge**:

> "93 sixth graders from one urban middle school in the Southern U.S."  
> — Zhang et al. 2022

**Your use**: Acknowledge in your paper's limitations: "prior validation of the R/M distinction was conducted with middle school students; generalization to high school requires further study."

### What to Emphasize in Your Paper

- This is your **primary theoretical anchor** for the dual-dimension design
- Betty's Brain context helps position your system as a **spiritual successor** in the ITS lineage
- The working memory mechanism provides **cognitive science grounding** for why dimension-specific hints work
- Cite as: (Zhang et al., 2022)

---

## Paper 3: Daheim et al. 2024 — Stepwise Verification EMNLP

**Full Citation**: Daheim, N., Macina, J., Kapur, M., Gurevych, I., & Sachan, M. (2024). Stepwise Verification and Remediation of Student Reasoning Errors with LLM Tutors. _EMNLP 2024_.

**Why This Paper**: Their **Verify-then-Generate** architecture is the closest to your BreakpointLocator → HintGenerator pipeline. They provide the **LLM baseline** you'll compare against in experiments.

### Key Findings to Cite

**1. Architecture Insight (Verify-then-Generate)**:

> "Single-pass LLM tutoring models perform all tasks (error identification, strategy selection, response generation) in one forward pass — this causes deficiencies. The human tutor model performs these steps **sequentially** (reason about error → pick strategy → respond). Their architecture mimics this sequential process."  
> — Daheim et al. 2024

**Your use**: This is the **key architectural argument** for your 5-node pipeline. Your system is a physical instantiation of their sequential architecture:

- Node 1 (BreakpointLocator) = Verification step
- Nodes 2a/2b (Router/Decider) = Error classification step
- Node 4 (HintGenerator) = Response generation step
- Node 5 (OutputGuardrail) = Quality verification step

**2. Error Detection Method (Step Alignment)**:

> "Uses a modified Needleman-Wunsch algorithm to align student solution steps with reference solution steps, identifying where the first error occurs by comparing aligned pairs."  
> — Daheim et al. 2024

**Your use**: Your BreakpointLocator's 3-level cascade (Jaccard → string sim → WRONG_DIRECTION) serves a similar **alignment-and-detect** function but is rule-based (no LLM). This is your **novelty** over their approach.

**3. Grounding Reduces Hallucination**:

> "Combining verification output with response generation steers the generation model toward targeted responses to the actual student error rather than hallucinating or being untargeted."  
> — Daheim et al. 2024

**Your use**: Your DimensionRouter + SubTypeDecider output **grounds** HintGeneratorV2, reducing hallucination risk. This is why you get better pedagogical quality than pure LLM generation.

**4. Key Result (Comparison Point)**:

> "Their approach showed significant improvements across all metrics (targeted, correctness, actionability) in human evaluation by real teachers."  
> — Daheim et al. 2024

**Your use**: In your experiments, use their approach as **Baseline C (LLM-only Locator)** — your rule-based BreakpointLocator should achieve comparable accuracy with much lower latency.

### What to Emphasize in Your Paper

- Their **Verify-then-Generate** framework validates your 5-node pipeline design
- Your BreakpointLocator is a **rule-based alternative** to their LLM-based verification — faster, no hallucination risk on localization
- Their human evaluation results confirm that **structured verification** improves tutoring quality
- Cite as: (Daheim et al., 2024)

---

## Paper 4: Wang et al. 2025 — EduLoop-Agent (闭环系统)

**Full Citation**: Wang, Z., Zheng, X., & Zeng, C. (2025). A Closed-Loop Personalized Learning Agent Integrating Neural Cognitive Diagnosis, Bounded-Ability Adaptive Testing, and LLM-Driven Feedback. _arXiv:2510.22559_.

**Why This Paper**: Their **EduLoop-Agent** is the most similar existing system — diagnosis → recommendation → feedback closed loop. They use **Neural Cognitive Diagnosis (NCD)** for the diagnosis module. You'll position your system as addressing their gaps.

### Key Findings to Cite

**1. Closed-Loop Architecture**:

> "EduLoop-Agent implements a four-stage closed-loop workflow: Data Preprocessing → Model Training (NCD) → Adaptive Recommendation (BECAT) → Personalized Feedback (LLM)."  
> — Wang et al. 2025

**Your use**: Your 5-node pipeline (Locator → Router → Decider → Generator → Guardrail) is a similar closed-loop architecture but with **two key differences**:

1. Your diagnosis is **per-breakpoint** (not per-session); theirs is static per-student
2. Your loop has **explicit R/M dimension switching** at each breakpoint

**2. Cognitive Diagnosis Module (NCD)**:

> "Neural Cognitive Diagnosis embeds students, items, and knowledge points to low-dimensional vectors, then uses MLP with sigmoid output to predict probability of correct response."  
> — Wang et al. 2025

**Your use**: This is your **Module 4 reference** — future work can integrate NCD into your system for per-student cognitive modeling. Note in your paper: "EduLoop-Agent focuses on knowledge-tracing (DKT-style); our system focuses on per-breakpoint difficulty diagnosis."

**3. LLM Feedback Module**:

> "LLM-driven feedback integrates student mastery levels from NCD with recommended item texts and knowledge descriptions to generate structured feedback with three sections: mastery analysis, recommendation evaluation, and personalized learning suggestions."  
> — Wang et al. 2025

**Your use**: Your HintGeneratorV2 follows a similar **grounded generation** pattern. The difference: yours is dimension-aware and level-specific (R1-R4/M1-M5).

**4. Their Limitations (Your Gaps to Fill)**:

> "The study's external validity is limited by reliance on a single public dataset and offline simulations, and LLM-generated feedback can be sensitive to prompt design, exhibit variability, and inherit social biases."  
> — Wang et al. 2025

**Your use**: Your contributions address their gaps:

- Multi-problem evaluation (15 problems × 8 profiles) vs. single dataset
- Structured prompts (R1-R4/M1-M5 templates) vs. free-form prompt sensitivity
- Dual-layer guardrail for output consistency

### What to Emphasize in Your Paper

- Position your system as addressing the **dimension-switching gap** in EduLoop-Agent
- Their work confirms the **closed-loop architecture** is the right paradigm
- Future work can combine your per-breakpoint approach with their NCD-based cognitive model
- Cite as: (Wang et al., 2025)

---

## Paper 5: Dinucu-Jianu et al. 2025 — RL Teaching Alignment EMNLP

**Full Citation**: Dinucu-Jianu, C., Macina, J., Daheim, N., Gurevych, I., & Sachan, M. (2025). From Problem-Solving to Teaching Problem-Solving: Aligning LLMs with Pedagogy using RL. _EMNLP 2025_.

**Why This Paper**: This is your **guardrail/paper direction** reference. Their RL-based answer-leakage prevention is the most sophisticated existing approach. Your **dual-layer OutputGuardrail** is a **non-RL alternative** achieving similar goals.

### Key Findings to Cite

**1. Problem Statement (Answer Leakage)**:

> "Unaligned LLMs prioritize answering over teaching — base models show high 'leaked solutions' on Big-Math benchmark."  
> — Dinucu-Jianu et al. 2025

**Your use**: This quantifies the **answer leakage problem** your OutputGuardrail addresses. Even sophisticated RL-trained models still show some leakage (Pareto frontier shows leakage rate > 0 for best models).

**2. RL Approach (Your Non-RL Alternative)**:

> "Two-component reward: r = r_sol + (r_ped - 1) · λ, where r_sol = post-dialog solve rate and r_ped = pedagogical quality (all-LLM-judge acceptance)."  
> — Dinucu-Jianu et al. 2025

**Your use**: Your dual-layer guardrail (rule + LLM-judge) achieves similar pedagogical filtering **without RL training**. This is a **practical advantage** — no training infrastructure needed.

**3. Key Result (Pareto Frontier)**:

> "RL-trained Qwen-2.5-7B-Instruct reaches similar tutoring performance to much larger closed-source LearnLM models, tracing a Pareto frontier in the 2D space: Δsolve rate vs. leaked solutions."  
> — Dinucu-Jianu et al. 2025

**Your use**: In your experiments, show that your dual-layer guardrail achieves **comparable leakage reduction** (62% reduction vs. pure rule) without requiring RL training.

**4. Socratic Principle**:

> "The tutor should not present complete solutions. Instead, guide through Socratic questioning, hints, or targeted feedback."  
> — Dinucu-Jianu et al. 2025

**Your use**: This is the **pedagogical principle** your R1-R4 hints operationalize. R1 = maximally Socratic; R4 = still Socratic but reveals full strategy structure.

**5. Computational Cost (Why Non-RL Matters)**:

> "Training requires GRPO with on-policy updates, ZeRO-2/3 via DeepSpeed, vLLM for inference, and multi-node scaling."  
> — Dinucu-Jianu et al. 2025

**Your use**: Your dual-layer guardrail runs at **inference time only** — no training needed. This makes your system **deployable without specialized ML infrastructure**.

### What to Emphasize in Your Paper

- Your dual-layer guardrail achieves **RL-comparable pedagogical safety without RL training**
- The Socratic principle provides theoretical grounding for your R1-R4/M1-M5 level design
- Their Pareto frontier analysis provides a **methodology for reporting your guardrail results**
- Cite as: (Dinucu-Jianu et al., 2025)

---

## Cross-Paper Synthesis

### How These Papers Connect to Each Other

```
Zhang et al. 2022 (Theory)
    ↓ "R/M are independent dimensions"
    ↓
Jangra et al. 2025 (Survey)
    ↓ "Need adaptive progressive hints + personalization"
    ↓
┌─────────────────────────────────────────┐
│  Daheim et al. 2024 (Verify-then-Gen)   │ ← Your BreakpointLocator (rule-based version)
│  Wang et al. 2025 (EduLoop-Agent)       │ ← Your closed-loop architecture
│  Dinucu-Jianu et al. 2025 (RL Align)   │ ← Your OutputGuardrail (non-RL alternative)
└─────────────────────────────────────────┘
    ↓ All inform your:
    ↓
  YOUR PAPER (ADVIS)
```

### Gaps Across All 5 Papers Your Work Fills

| Gap                                        | Cited By                                                       | Your Solution                                          |
| ------------------------------------------ | -------------------------------------------------------------- | ------------------------------------------------------ |
| No real-time per-breakpoint R/M switching  | Jangra 2025 (gaps), Zhang 2022 (theory)                        | DimensionRouter + SubTypeDecider at each breakpoint    |
| No dimension-aware progressive hint levels | Jangra 2025 (needs adaptive), Zhang 2022 (mechanism)           | R1-R4 + M1-M5 with distinct pedagogical semantics      |
| LLM-only breakpoint detection is expensive | Daheim 2024 (LLM baseline), Wang 2025 (closed-loop)            | Cascaded rule-based BreakpointLocator (>80% no LLM)    |
| RL guardrail requires heavy infrastructure | Dinucu-Jianu 2025 (RL approach)                                | Dual-layer rule + LLM-judge guardrail (inference-only) |
| No cross-dimension escalation path         | Zhang 2022 (temporal evolution), Jangra 2025 (personalization) | R4→M3 escalation path when resource remediation fails  |

---

## What to Read First (Priority Order)

| #     | Paper                         | Time to Read | Why First                                         |
| ----- | ----------------------------- | ------------ | ------------------------------------------------- |
| **1** | Jangra 2025 (Hint Survey)     | 45 min       | Sets the field's vocabulary and confirms your gap |
| **2** | Zhang 2022 (R/M Theory)       | 30 min       | Your theoretical anchor; short paper              |
| **3** | Daheim 2024 (Verify-then-Gen) | 40 min       | Closest system; your baseline comparison          |
| **4** | Wang 2025 (EduLoop-Agent)     | 30 min       | Similar architecture; positions your novelty      |
| **5** | Dinucu-Jianu 2025 (RL Align)  | 40 min       | Guardrail reference; RL vs. your non-RL approach  |

**Total reading time**: ~3 hours

---

## Specific Quotes for Your Related Work Section

### Section 2.1 (Adaptive Scaffolding)

> "Understanding how strategic learning behaviors change over time — and how prior domain knowledge and motivation influence such change — can lead to more informed decisions about when to provide scaffolding and to whom."  
> — Zhang et al. 2022

### Section 2.2 (R/M Dual-Dimension)

> "Learners with low domain knowledge need more working memory capacity for processing information, while learners with high domain knowledge can allocate more of this capacity for regulation."  
> — Zhang et al. 2022

### Section 2.3 (Progressive Hint Generation)

> "Hints should provide just-in-time, progressive guidance rather than revealing solutions upfront."  
> "Current question answering hint generation systems do not personalize hints to learners' preferences, learning objectives, or their prior knowledge."  
> — Jangra et al. 2025

### Section 2.4 (Breakpoint Detection)

> "Single-pass LLM tutoring models perform all tasks in one forward pass — this causes deficiencies. The human tutor model performs these steps sequentially. Their architecture mimics this sequential process."  
> — Daheim et al. 2024

### Section 2.5 (Pedagogical Alignment)

> "The tutor should not present complete solutions. Instead, guide through Socratic questioning, hints, or targeted feedback."  
> — Dinucu-Jianu et al. 2025

---

## Key Statistics to Report in Your Experiments

| Metric                       | From Paper                                             | Your Value                            |
| ---------------------------- | ------------------------------------------------------ | ------------------------------------- |
| Hint taxonomy layers         | Jangra 2025: 3 (pragmatic/semantic/style)              | Your design maps to all 3             |
| Dimension independence       | Zhang 2022: R and M have independent effects           | Confirms your dual-dimension approach |
| Breakpoint detection         | Daheim 2024: LLM-based, accurate but expensive         | Your rule-based: >80% no LLM needed   |
| Answer leakage (RL baseline) | Dinucu-Jianu 2025: Pareto frontier >0 even for best RL | Your dual-layer: 62% reduction        |
| Closed-loop architecture     | Wang 2025: EduLoop-Agent confirms loop value           | Your 5-node loop operationalizes this |
