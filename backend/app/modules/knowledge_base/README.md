# Module 6: Knowledge Base（RAG 知识库系统）

## 概述

基于 ChromaDB 的检索增强生成（RAG）系统，为 Socrates 教学系统提供结构化数学知识检索能力。

## 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| RAGService | `service.py` | 主服务（检索、摄入、统计） |
| ChromaDBVectorStore | `vector_store.py` | ChromaDB 向量存储封装 |
| DashScopeEmbeddingClient | `embedder.py` | DashScope 文本嵌入 |
| IngestionPipeline | `ingestion.py` | PDF 文档摄入流水线 |
| Chunker | `chunker.py` | 自适应文本切分 |
| OCR | `ocr.py` | PDF 文本提取 |

## 数据流

```
PDF 文档 → 文本提取 → Chunking → 向量嵌入 → ChromaDB 存储
                                              ↓
查询文本 → 向量嵌入 → 相似性搜索 → 返回知识片段
```

## API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/knowledge-base/retrieve` | POST | 语义检索 |
| `/knowledge-base/ingest` | POST | 文档摄入 |
| `/knowledge-base/ingest/batch` | POST | 批量摄入 |
| `/knowledge-base/collection/stats` | GET | 集合统计 |
| `/knowledge-base/health` | GET | 健康检查 |
| `/knowledge-base/document-types` | GET | 文档类型列表 |

## 依赖

- ChromaDB（向量数据库）
- DashScope Embedding API（`text-embedding-v3`）

## 测试

```bash
pytest backend/tests/modules/test_knowledge_base/ -v
```

## 设计文档

- [设计文档](../../../docs/module6-design.md)
- [PRD](../../../docs/module6-prd.md)
