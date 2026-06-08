# Module 3: Recommendation（智能练习题推荐系统）

## 概述

基于学生维度画像和知识本体，通过 LLM 实时生成个性化的下一道练习题。

## 核心流程

```
学生完成题目 → 读取画像 → 知识锚点检索 → LLM 生成 → 质量校验 → 返回推荐
```

## 组件

| 组件 | 文件 | 职责 |
|------|------|------|
| RecommendationService | `service.py` | 主编排服务 |
| KnowledgeBaseAPI | `knowledge_base/knowledge_api.py` | 知识本体查询 |
| KnowledgeAnchorRetriever | `retriever/knowledge_anchor_retriever.py` | 3 策略锚点检索 |
| ProblemGenerator | `generator/problem_generator.py` | LLM 题目生成 |
| ProblemValidator | `generator/problem_validator.py` | 生成质量校验 |
| FallbackGenerator | `generator/fallback_generator.py` | LLM 失败降级 |
| DifficultyScorer | `scorer/difficulty_scorer.py` | 目标难度计算 |

## 推荐策略

| dimension_ratio | 策略 | 行为 |
|-----------------|------|------|
| > 0.65 (R 型) | SAME_KP | 同知识点前置 KP 强化 |
| < 0.35 (M 型) | VARIATION | 同题型不同方法变式 |
| 0.35-0.65 | BALANCED | 随机薄弱 KP 练习 |

## API

- `POST /recommendations/recommend` — 触发推荐
- `GET /recommendations/health` — 健康检查

## 依赖

- Module 1 (solving)
- Module 4 (student_model, 当前使用 mock)
- Module 6 (知识本体 JSON 数据，非 RAG)

## 测试

```bash
pytest backend/tests/modules/test_recommendation/ -v
```

## 设计文档

- [设计文档](../../../docs/module3-design.md)
- [API 文档](../../../docs/module3-api.md)
- [执行计划](../../../docs/module3-execution-plan.md)
