# Module 6: RAG 知识库系统设计文档

**版本**: v1  
**核心功能**: 检索增强生成（RAG）知识库系统，为 Socrates tutoring 系统提供结构化数学知识检索能力  
**最后更新**: 2026-03-31

---

## 1. 架构概述与数据流

### 1.1 模块定位

Module 6 是 Socrates 系统中的检索增强生成（RAG）知识库模块，承担着为整个 tutoring 系统提供结构化数学知识检索能力的核心职责。在 Socrates 的整体架构中，Module 6 属于基础设施层，为 Module 2（干预提示生成器）、Module 3（题目推荐引擎）、Module 5（教学策略选择器）提供知识检索服务。

Module 6 与其他模块的关系是服务与被服务的关系。Module 6 不主动推送任何内容，而是响应其他模块的检索请求。这种设计确保了模块之间的松耦合，便于独立演进和测试。

### 1.2 整体架构

Module 6 采用标准的检索增强生成架构，由 ingestion pipeline 和 retrieval service 两大部分组成。数据流向从左侧的 PDF 文档开始，经过 extraction、chunking、embedding、storage 四个处理阶段，最终存储到 ChromaDB 向量数据库中。检索时，查询请求经过 embedding 过程后在向量数据库中进行相似性搜索，返回最匹配的知识片段。

```
┌─────────────────────────────────────────────────────────────────────┐
│                         整体架构图                                   │
│                                                                      │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐       │
│  │  PDF 文档     │ ───► │ 文本提取      │ ───► │ 结构化Chunking│      │
│  │  (原始知识)   │      │ (pdfplumber) │      │ (自适应切分)  │       │
│  └──────────────┘      └──────────────┘      └──────────────┘       │
│                                                        │              │
│                                                        ▼              │
│                                              ┌──────────────┐        │
│                                              │ 向量嵌入      │        │
│                                              │ (DashScope)   │        │
│                                              └──────────────┘        │
│                                                        │              │
│                                                        ▼              │
│                                              ┌──────────────┐        │
│                                              │ ChromaDB     │        │
│                                              │ 持久化存储    │        │
│                                              └──────────────┘        │
└─────────────────────────────────────────────────────────────────────┘

                        ▲                              │
                        │                              ▼
                        │
┌─────────────────────────────────────────────────────────────────────┐
│                         检索流程                                      │
│                                                                      │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐       │
│  │ Module 2/3/5 │ ───► │ Query Embed  │ ───► │ ChromaDB    │       │
│  │ 检索请求      │      │ (DashScope)  │      │ 相似性搜索   │       │
│  └──────────────┘      └──────────────┘      └──────────────┘       │
│                                                        │              │
│                                                        ▼              │
│                                              ┌──────────────┐        │
│                                              │ 结果后处理    │        │
│                                              │ (排序/去重)   │        │
│                                              └──────────────┘        │
│                                                        │              │
│                                                        ▼              │
│                                              ┌──────────────┐        │
│                                              │ 返回知识片段   │       │
│                                              │ List[Chunk]  │        │
│                                              └──────────────┘        │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.3 数据流设计原则

整个架构的设计遵循了数据与逻辑分离的原则。知识文档以向量形式存储在 ChromaDB 中，与业务逻辑完全解耦。当知识内容需要更新时，只需重新运行 ingestion pipeline 更新向量库，业务代码无需修改。

这种设计的优势体现在三个方面。第一，知识的独立性——知识内容存储在向量数据库中，与使用知识的业务模块相互独立，便于知识的单独维护和更新。第二，检索的灵活性——通过向量相似性检索而非关键词匹配，能够捕捉语义关联，提供更智能的检索结果。第三，扩展的便利性——当需要新增知识类型或调整检索策略时，只需修改知识库模块本身，不影响依赖其服务的其他模块。

---

## 2. 核心技术方案

### 2.1 ChromaDB 向量数据库集成

ChromaDB 是本模块选用的向量数据库，作为 Chroma 公司的开源产品，它提供了简洁的 API 和良好的 Python 原生支持。ChromaDB 支持本地持久化存储，数据完全保存在本地文件系统，不依赖外部数据库服务，这与 Socrates 系统轻量级部署的要求高度契合。

#### 2.1.1 为什么选择 ChromaDB

从部署复杂度来看，ChromaDB 支持本地持久化存储，不依赖外部服务。Socrates 系统的规模预计在初期不会很大，引入一个独立的向量数据库服务会增加部署和维护负担。ChromaDB 的嵌入即可运行特性降低了系统的整体复杂度。

从 API 友好性来看，ChromaDB 提供简洁的 Python SDK，接口设计直观易懂。对于快速实现 MVP 来说，ChromaDB 的低学习成本是一个重要优势。开发者可以在几个小时内完成从环境搭建到基本功能实现的完整流程。

从功能完整性来看，ChromaDB 虽然轻量，但提供了向量检索所需的核心功能：支持余弦相似度度量、支持元数据过滤、支持集合操作。对于 Socrates 系统的使用场景来说，ChromaDB 的功能是完备的。

#### 2.1.2 为什么不选择其他方案

Pinecone、Weaviate 等云端向量数据库服务提供了更强大的托管能力和弹性扩展性，但对于 Socrates 系统的初期规模来说过于重量级。这类服务的成本模型按存储空间和查询量计费，对于一个学校或教育机构来说是额外的支出。

FAISS 是 Facebook 开发的向量检索库，以性能著称，但它是一个库而非数据库。使用 FAISS 需要自行处理向量存储、索引管理、持久化等逻辑，增加了开发工作量。ChromaDB 在 FAISS 之上封装了这些功能，同时保持了良好的性能。

Milvus 是国产的成熟向量数据库，功能强大且支持分布式部署。但其面向大规模数据场景的设计使得部署和运维复杂度较高。对于 Socrates 系统预计的数据规模（不超过 10 万向量），Milvus 显得过于重型。

#### 2.1.3 ChromaDB 配置

ChromaDB 的初始化需要指定持久化目录和 collection 名称。本模块创建的 collection 名称为 "math_knowledge"，用于隔离不同类型的知识内容。

```python
# ChromaDB 配置参数
PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chromadb")
COLLECTION_NAME = "math_knowledge"
EMBEDDING_DIMENSION = 1024  # qwen-embeddings-v1 输出维度
```

### 2.2 DashScope Embedding 集成

DashScope 是阿里云提供的大模型服务平台，本模块使用其提供的 qwen-embeddings-v1 文本嵌入模型。该模型输出维度为 1024，在中文语义理解任务上表现优异，特别适合数学这类专业性强的领域。

#### 2.2.1 为什么选择 qwen-embeddings-v1

qwen-embeddings-v1 是阿里云通义千问系列提供的文本嵌入模型，在中文语义理解任务上经过了充分优化。高中数学知识库的特点是包含大量专业术语和公式符号，模型对中文的理解能力直接影响检索质量。

从中文能力来看，qwen-embeddings-v1 基于大规模中文语料训练，对中文语义的理解优于多数英文模型的翻译版本。在数学领域，模型能够正确理解归纳、递推、收敛等专业术语的语义。

从使用便利性来看，DashScope 提供 RESTful API 接口，通过 HTTP 请求即可调用。SDK 支持 Python 语言，与 Socrates 后端技术栈一致。相比需要本地部署的模型，DashScope API 方式无需占用服务器计算资源。

从成本角度来看，DashScope 的 embedding API 采用按调用量计费模式。Socrates 系统日均调用量预计不超过 1000 次，月度成本在可接受范围内。对于 MVP 阶段的验证性使用，DashScope 还提供免费额度。

#### 2.2.2 API 调用策略

Embedding API 调用采用批量模式以提高效率，单次批量处理的 chunk 数量不超过 32 条。API 调用采用异步模式以提高吞吐量，处理结果通过回调机制写入 ChromaDB。

```python
# DashScope 配置参数
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
EMBEDDING_MODEL = "text-embedding-v1"
EMBEDDING_BATCH_SIZE = 32
EMBEDDING_TIMEOUT = 30  # 秒
```

---

## 3. 核心算法设计

### 3.1 Ingestion Pipeline

Ingestion Pipeline 是将原始 PDF 文档转化为可检索向量数据的处理流水线。该流水线包含四个连续的阶段，每个阶段都有明确的输入输出规范。

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Ingestion Pipeline 流程                         │
│                                                                      │
│  阶段一：PDF 文本提取                                                 │
│  ─────────────────────────────────────────────────────────────────  │
│  输入：PDF 文件路径                                                   │
│  处理：使用 pdfplumber 提取原始文本内容                               │
│  输出：原始文本字符串 + 段落结构信息                                   │
│  挑战：LaTeX 公式处理、页眉页脚去除、OCR 识别（扫描版PDF）            │
│                                                                      │
│  阶段二：结构化 Chunking                                              │
│  ─────────────────────────────────────────────────────────────────  │
│  输入：原始文本 + 段落结构                                             │
│  处理：按语义边界切分为独立知识片段                                   │
│  输出：List[TextChunk]，每个 chunk 300-500 中文字符                  │
│  策略：章节边界 > 段落边界 > 句子边界（保底）                         │
│                                                                      │
│  阶段三：向量嵌入                                                     │
│  ─────────────────────────────────────────────────────────────────  │
│  输入：List[TextChunk]                                                │
│  处理：调用 DashScope qwen-embeddings-v1 生成 1024 维向量            │
│  输出：List[Embedding]，与输入一一对应                                 │
│  优化：批量处理，32条/批                                              │
│                                                                      │
│  阶段四：向量存储                                                     │
│  ─────────────────────────────────────────────────────────────────  │
│  输入：List[TextChunk] + List[Embedding] + metadata                  │
│  处理：写入 ChromaDB，支持幂等性（SHA256 去重）                        │
│  输出：存储确认                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

#### 3.1.1 PDF 文本提取

该阶段使用 PDF 解析库从 PDF 文件中提取原始文本内容。PDF 解析面临的主要挑战是数学公式的处理。高中数学文档中包含大量 LaTeX 格式的公式，解析库需要能够正确识别和提取这些公式文本。提取的文本应保持原有的段落结构和章节组织，因为后续的 chunking 阶段需要依赖这些结构信息。

对于扫描版 PDF，需要预先使用 OCR 工具进行文字识别。OCR 识别率直接影响后续处理的质量，因此需要选择支持数学符号识别的 OCR 引擎。

#### 3.1.2 结构化 Chunking

该阶段将提取的文本按语义边界切分为独立的知识片段。Chunking 策略直接影响检索质量，切分粒度太粗会导致检索结果包含过多无关内容，切分粒度太细则会丢失完整的语义信息。

本模块采用基于文档结构的自适应 chunking 策略。首先按章节标题进行一级切分，然后在章节内部按段落进行二级切分。每个 chunk 的目标长度控制在 300 到 500 个中文字符之间，这个长度既能保留完整的语义单元，又不会过于冗长。

对于包含多个知识点的长文档，系统会识别文档中的知识点标记（如定义、定理、例题等），以这些标记为边界进行切分，确保每个 chunk 对应一个独立的知识单元。

切分优先级设计如下：

- 最高优先级是章节标题边界。如果文档中包含明确的章节编号（如第一章、1.1）或标题样式（加粗、居中），系统会在这些位置进行切分。
- 中等优先级是段落边界。如果某个段落的长度超过预设的最大 chunk 长度（500 字符），系统会在段落内部继续按句子进行切分。
- 最低优先级是句子边界。当需要在段落内部进行切分时，系统以完整的句子为最小切分单元，避免出现句子被截断的情况。

#### 3.1.3 向量嵌入与存储

每个处理完成的 chunk 都会被发送到 DashScope embedding API 进行向量化。存储时，系统首先生成文档的 SHA256 哈希值作为唯一标识符。如果数据库中已存在相同哈希值的文档，系统执行更新操作而非重复创建。更新操作保留原有的 id，但更新 embedding 向量、文档内容和元数据。

### 3.2 Retrieval 算法

RAGService 是 Module 6 对外提供服务的核心类，封装了所有检索相关的业务逻辑。外部模块通过调用 RAGService 的 retrieve 方法来获取知识检索能力。

#### 3.2.1 检索流程

retrieve 方法接收三个参数：query（查询字符串）、top_k（返回结果数量，默认为 3）、filter（过滤条件，可选）。方法的返回类型为 List[Chunk]，每个 Chunk 包含文本内容、元数据和相关性分数。

检索流程分为五个步骤：

第一步，对输入的 query 文本调用 DashScope embedding API 生成查询向量。

第二步，在 ChromaDB 中执行向量相似性搜索，使用余弦相似度作为度量标准，返回 top_k 个最相似的文档。

第三步，如果提供了 filter 参数，系统会在向量搜索结果基础上进行元数据过滤。

第四步，系统对检索结果进行后处理，按照相似度分数从高到低排序，并添加检索来源标注。

第五步，返回处理后的 Chunk 列表给调用方。

#### 3.2.2 语义检索原理

检索过程利用了深度学习模型的语义理解能力。当用户输入如何使用数学归纳法证明数列问题时，系统首先将该文本转换为 1024 维的向量表示。这个向量编码了查询内容的语义信息，使得语义相似的内容在向量空间中具有相近的位置。

ChromaDB 在检索时计算查询向量与数据库中所有文档向量的余弦相似度，返回相似度最高的 top_k 个结果。这种检索方式不依赖关键词匹配，因此能够捕捉查询和文档之间的语义关联。

#### 3.2.3 结果后处理

检索结果在返回前会经过一系列后处理步骤。

首先是去重处理。如果多个检索结果的内容相似度超过 0.95，系统会合并这些结果，避免向调用方返回高度重复的内容。

其次是排序优化。向量数据库返回的结果已按相似度排序，但系统会根据文档类型进行微调。例如，当查询是什么是函数时，concept 类型文档的优先级会略微提高。

最后是来源标注。每个返回的 Chunk 都会附带其来源文档的信息，包括原始 PDF 文件名、在文档中的位置等，便于调用方进行溯源。

#### 3.2.4 过滤机制

filter 参数支持按以下维度进行精确过滤：

- type 字段支持按文档类型过滤，可选值为 knowledge_point、method、concept、example、strategy。
- grade 字段支持按年级过滤，如 high_school。
- difficulty 字段支持按难度过滤，可选值为 easy、medium、hard。
- keywords 字段支持按关键词模糊匹配。

过滤操作在向量检索之后执行，这种设计的好处是既能利用向量检索的语义相似性能力，又能通过元数据过滤确保结果的精确性。

### 3.3 Module 2 提示增强集成

Module 2 的核心职责是在学生解题遇到困难时生成实时的干预提示。干预提示的质量直接影响学生的学习效果。引入 Module 6 之后，Module 2 的提示生成流程增加了知识检索环节。

```
┌─────────────────────────────────────────────────────────────────────┐
│               Module 2 提示增强流程（RAG Integration）                │
│                                                                      │
│  ┌──────────────┐                                                   │
│  │ 原始提示生成   │                                                   │
│  │ base_prompt   │                                                   │
│  └──────────────┘                                                   │
│          │                                                          │
│          ▼                                                          │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ Step 1: 构造检索查询                                           │   │
│  │ ────────────────────────────────────────────────────────────  │   │
│  │ query = f"{breakpoint_type} {knowledge_point_name} 解题方法"  │   │
│  │ filter = {"type": "method", "difficulty": student_level}      │   │
│  └──────────────────────────────────────────────────────────────┘   │
│          │                                                          │
│          ▼                                                          │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ Step 2: 调用 RAGService.retrieve()                            │   │
│  │ ────────────────────────────────────────────────────────────  │   │
│  │ chunks = await rag_service.retrieve(                          │   │
│  │     query=query,                                              │   │
│  │     top_k=3,                                                  │   │
│  │     filter=filter                                            │   │
│  │ )                                                            │   │
│  └──────────────────────────────────────────────────────────────┘   │
│          │                                                          │
│          ▼                                                          │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ Step 3: 注入知识到提示                                         │   │
│  │ ────────────────────────────────────────────────────────────  │   │
│  │ enriched_prompt = rag_service.enrich_hint_prompt(             │   │
│  │     base_prompt=base_prompt,                                  │   │
│  │     chunks=chunks                                             │   │
│  │ )                                                            │   │
│  └──────────────────────────────────────────────────────────────┘   │
│          │                                                          │
│          ▼                                                          │
│  ┌──────────────┐                                                   │
│  │ LLM 生成提示  │                                                   │
│  └──────────────┘                                                   │
└─────────────────────────────────────────────────────────────────────┘
```

#### 3.3.1 提示增强示例

当 Module 2 监听到学生在一个涉及数列递推的 breakpoint 处卡顿时，它需要生成一条针对性的提示。

Module 2 原本的提示词模板可能是这样的：当前步骤涉及数列的递推关系，可以考虑使用数学归纳法来验证你的递推公式。

这条提示存在两个问题：第一，数学归纳法是泛泛而谈，没有给出具体的操作指导；第二，提示与学生当前的具体问题之间的关联不够紧密，学生可能不清楚如何将归纳法应用到当前的递推问题中。

引入 Module 6 之后，Module 2 首先构造检索查询。检索查询的内容包括当前断点类型（递推关系）、涉及的知识点名称（数列）、学生的难度评估。

检索查询示例为数列递推关系的证明方法，如何使用数学归纳法。

Module 6 收到检索请求后，返回最相关的知识片段。假设检索到三个结果：第一条是数学归纳法知识点文档，包含基本步和归纳步的具体步骤说明；第二条是数列归纳证明例题文档，包含一个完整的数列通项公式证明过程；第三条是递推与归纳的区别概念文档，解释了两种方法的适用场景差异。

Module 2 收到检索结果后，将这些知识片段注入到提示词模板中。生成的提示词变为：

```
当前你遇到的递推关系证明，可以尝试使用数学归纳法。
基本步骤是：先验证n=1时命题成立（基本步），
然后假设n=k时成立并证明n=k+1时也成立（归纳步）。
参考例题：{检索到的例题摘要}
注意区分递推方法（直接推导通项）和归纳方法（验证+假设）的适用场景。
```

这样的提示词不仅指出了方法名称，还提供了具体的操作步骤和参考案例，学生可以根据提示自行完成证明过程。

---

## 4. 模块结构

### 4.1 目录结构

Module 6 的代码组织遵循 Socrates 项目的模块化规范，所有相关代码集中在 `backend/app/modules/knowledge_base/` 目录下：

```
backend/app/modules/knowledge_base/
├── __init__.py                  # 模块导出，版本信息
├── service.py                   # RAGService — 核心服务类
├── models.py                    # 数据模型（KGDocument, KGQuery, KGResult等）
├── embedder.py                  # DashScopeEmbeddingClient — embedding生成
├── vector_store.py              # ChromaDBVectorStore — 向量存储+检索
├── ingestion.py                 # IngestionPipeline — PDF解析+chunking+批处理
├── prompts.py                   # RAG prompt 模板
└── routes.py                    # FastAPI 路由（管理接口）

scripts/
└── ingest_documents.py          # CLI 脚本，用于文档导入
```

### 4.2 文件职责划分

#### 4.2.1 `__init__.py`

模块入口文件，负责导出公共接口和版本信息：

```python
"""
Module 6: RAG 知识库系统
版本: 1.0.0
"""

from .service import RAGService
from .models import KGDocument, KGChunk, KGQuery, KGResult

__all__ = ["RAGService", "KGDocument", "KGChunk", "KGQuery", "KGResult"]
__version__ = "1.0.0"
```

#### 4.2.2 `models.py`

数据模型定义，包含所有在本模块中使用的数据结构：

- `KGDocument`：知识文档模型，包含原始文本、元数据、向量
- `KGChunk`：知识片段模型，对应 ChromaDB 中的一条记录
- `KGQuery`：检索查询模型
- `KGResult`：检索结果模型
- `DocumentType`：文档类型枚举

#### 4.2.3 `embedder.py`

DashScopeEmbeddingClient 类封装了与 DashScope embedding API 的交互逻辑：

```python
class DashScopeEmbeddingClient:
    def __init__(self, api_key: str, model: str = "text-embedding-v1")
    def embed(self, texts: List[str]) -> List[List[float]]
    async def aembed(self, texts: List[str]) -> List[List[float]]
```

核心职责包括：API 密钥管理、批量请求处理、错误重试机制、超时控制。

#### 4.2.4 `vector_store.py`

ChromaDBVectorStore 类封装了向量存储和检索的逻辑：

```python
class ChromaDBVectorStore:
    def __init__(self, persist_dir: str, collection_name: str)
    def add_documents(self, documents: List[KGDocument]) -> None
    def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int,
        filter_metadata: dict = None
    ) -> List[Tuple[KGDocument, float]]
    def delete_collection(self) -> None
    def get_collection_stats(self) -> dict
```

核心职责包括：ChromaDB 连接管理、collection 操作、向量相似性搜索、元数据过滤。

#### 4.2.5 `ingestion.py`

IngestionPipeline 类封装了 PDF 文档导入的完整流程：

```python
class IngestionPipeline:
    def __init__(self, vector_store: ChromaDBVectorStore, embedder: DashScopeEmbeddingClient)
    async def ingest_file(self, file_path: str, metadata: dict) -> IngestionResult
    async def ingest_directory(self, dir_path: str, file_type: str = "knowledge_point") -> List[IngestionResult]
    def _extract_text(self, pdf_path: str) -> str
    def _chunk_text(self, text: str) -> List[str]
    def _generate_hash(self, content: str) -> str
```

核心职责包括：PDF 文本提取、文本分块、向量生成、批量写入。

#### 4.2.6 `service.py`

RAGService 是 Module 6 对外提供服务的核心类：

```python
class RAGService:
    def __init__(self, vector_store: ChromaDBVectorStore, embedder: DashScopeEmbeddingClient)
    async def retrieve(
        self,
        query: str,
        top_k: int = 3,
        filter_metadata: dict = None
    ) -> List[KGChunk]
    async def enrich_hint_prompt(
        self,
        hint_template: str,
        knowledge_chunks: List[KGChunk]
    ) -> str
    def get_stats(self) -> dict
```

核心职责包括：检索流程编排、提示词增强、结果后处理。

#### 4.2.7 `prompts.py`

RAG 相关的 prompt 模板定义，包括提示增强模板和系统提示。

#### 4.2.8 `routes.py`

FastAPI 路由定义，提供管理接口：

```
POST /api/v1/kg/retrieve     # 检索接口
POST /api/v1/kg/ingest      # 导入接口
GET  /api/v1/kg/stats       # 统计信息
DELETE /api/v1/kg/collection # 删除 collection
```

#### 4.2.9 `scripts/ingest_documents.py`

命令行导入脚本，用于运维人员触发文档导入：

```bash
# 单文件导入
python -m scripts.ingest_documents --file /path/to/document.pdf --type knowledge_point

# 批量导入
python -m scripts.ingest_documents --dir /path/to/math_knowledge/ --type knowledge_point
```

---

## 5. ChromaDB 数据模型

### 5.1 Collection Schema

本模块在 ChromaDB 中创建名为 "math_knowledge" 的 collection。Collection 的 schema 设计需要平衡检索灵活性与存储效率。

| 字段名    | 类型        | 说明                                                                                         |
| --------- | ----------- | -------------------------------------------------------------------------------------------- |
| id        | string      | 文档唯一标识符，格式为 "{type}\_{序号}"，如 "kp_001"                                         |
| embedding | float[1024] | DashScope qwen-embeddings-v1 生成的文本向量                                                  |
| document  | string      | 文档原始文本内容，即知识片段的完整表述                                                       |
| metadata  | object      | 元数据对象，包含 type、name、keywords、grade、difficulty、related_kp、related_methods 等字段 |

### 5.2 Metadata 字段定义

```json
{
  "type": "knowledge_point | method | concept | example | strategy",
  "name": "知识片段的名称或标题",
  "keywords": ["关键词1", "关键词2", "关键词3"],
  "grade": "high_school",
  "difficulty": "easy | medium | hard",
  "related_kp": ["相关知识点1", "相关知识点2"],
  "related_methods": ["相关方法1", "相关方法2"]
}
```

### 5.3 文档类型定义

系统支持五种类型的知识文档，每种类型有其特定的使用场景和结构规范。

#### 5.3.1 knowledge_point 类型

knowledge_point 是知识库中最核心的文档类型，代表高中数学的独立知识点。每个知识点文档应包含该知识点的定义、核心性质、常见应用场景三个部分。定义部分给出知识点的严格数学定义；性质部分列出该知识点具有的重要性质和定理；应用部分说明该知识点在解题中的常见用法。

示例文档结构：

```
知识点名称：数学归纳法

定义：数学归纳法是证明与正整数n有关的命题的一种方法。

性质：
1. 基本步：证明当n=1时命题成立
2. 归纳步：假设当n=k时命题成立，证明当n=k+1时命题也成立
3. 结论：从而对所有正整数n，命题都成立

应用场景：
- 证明数列通项公式
- 证明整除性命题
- 证明不等式
```

#### 5.3.2 method 类型

method 文档记录解题方法和技巧。相比知识点，方法文档更注重操作性，通常包含方法的使用步骤、适用条件、注意事项。方法文档的命名应简洁明确，如换元法、配方法、构造辅助函数等。

#### 5.3.3 concept 类型

concept 文档用于解释数学概念。与知识点的区别在于，概念更基础、更抽象，通常是定义其他知识点的前置知识。例如函数、变量、定义域等属于概念类型。

#### 5.3.4 example 类型

example 文档记录典型例题及其详细解答。每个例题文档应包含题目描述、思路分析、详细解答、关键点点评四个部分。例题文档的关键词应包含其考察的知识点标签，便于推荐系统进行匹配。

#### 5.3.5 strategy 类型

strategy 文档描述教学策略说明。这些文档不是面向学生的知识内容，而是面向系统如何进行教学指导的元信息。例如如何引导学生发现错误、探究式教学的实施步骤等。

### 5.4 元数据设计考量

元数据的设计需要考虑未来扩展的灵活性，同时保持与现有模块的数据格式兼容性。

keywords 字段采用数组格式，支持多个关键词的关联。这与 Module 3 的标签匹配逻辑兼容，推荐系统可以将学生的知识点薄弱项转换为关键词列表进行检索。

related_kp 和 related_methods 字段建立了知识点之间的关联网络。这个网络可以用于两个方面：一是支持 Module 3 的关联推荐，当学生在某个知识点上有薄弱时，可以推荐与该知识点相关的其他知识点进行巩固练习；二是支持 Module 6 自身的扩展检索，当用户检索某个知识点时，可以同时返回与之相关的其他知识点作为参考。

grade 字段统一使用 high_school 值，因为 Socrates 系统目前仅面向高中数学教学。设计为字符串类型是为了未来扩展到初中或大学数学时可以有明确的版本区分。

---

## 6. 外部接口

### 6.1 Module 2 接口规范

Module 2 是 MVP 阶段重点集成的模块。Module 2 通过调用 Module 6 的 RAGService 来获取知识检索能力。

#### 6.1.1 接口方法

```python
RAGService.retrieve(query: str, top_k: int = 3, filter: Optional[dict] = None) -> List[Chunk]
```

Module 2 在生成干预提示时，按以下流程调用该接口：

首先，Module 2 构造检索查询字符串。查询内容的来源包括当前断点类型（如递推关系）、涉及的知识点名称（从 breakpoint 元数据获取）、问题的难度等级。

其次，Module 2 指定 filter 参数。filter 应当包含当前知识点类型，如 {"type": "method"} 或 {"type": "example"}。Module 2 可以根据断点类型决定检索哪种类型的知识文档。

最后，Module 2 接收返回的 Chunk 列表。Module 2 的提示生成逻辑将 Chunk 的 text 字段内容插入到提示词模板中的指定位置。

#### 6.1.2 调用示例

```python
from module6.service import RAGService

rag_service = RAGService()

# Module 2 在需要生成提示时调用
query = f"{breakpoint_type} {knowledge_point_name} 解题方法"
filter = {"type": "method", "difficulty": student_difficulty}

chunks = rag_service.retrieve(query=query, top_k=3, filter=filter)

# Module 2 将检索结果注入到提示词模板
hint_prompt = build_hint_prompt(breakpoint, chunks)
```

#### 6.1.3 集成位置

Module 2 的集成点在 HintGeneratorV2 类中。当 HintGeneratorV2 需要生成提示时，它首先调用 RAGService 检索相关知识，然后将检索结果作为上下文传递给语言模型生成提示。

### 6.2 Module 3 接口规范

Module 3 在 Phase 2 中与 Module 6 进行集成。Module 3 调用 Module 6 的目的有二：一是获取知识点的关联关系，用于优化推荐策略；二是获取相关例题信息，用于丰富推荐内容。

#### 6.2.1 接口方法

Module 3 同样使用 RAGService.retrieve 方法。根据不同的使用场景，Module 3 有两种调用模式。

第一种是知识点关联查询。当 Module 3 需要获取某知识点的关联知识点列表时，调用 retrieve 方法并指定 type=knowledge_point，关键词为知识点名称。

```python
# Module 3 获取知识点的关联信息
chunks = rag_service.retrieve(
    query=f"知识点 {target_kp} 相关知识",
    top_k=5,
    filter={"type": "knowledge_point"}
)

# 从检索结果中提取 related_kp 字段
related_kps = []
for chunk in chunks:
    related_kps.extend(chunk.metadata.get("related_kp", []))
```

第二种是推荐题目关联查询。当 Module 3 准备推荐某道具体题目时，可以检索该题目的典型解法参考。

```python
# Module 3 获取题目的参考解法
chunks = rag_service.retrieve(
    query=f"题目 {problem_id} 解题方法",
    top_k=2,
    filter={"type": "example"}
)
```

### 6.3 Module 5 接口规范

Module 5 在 Phase 2 中与 Module 6 进行集成。Module 5 调用 Module 6 的目的是获取与当前教学内容相关的教学策略知识，用于丰富策略建议的专业性。

#### 6.3.1 接口方法

Module 5 使用 RAGService.retrieve 方法，检索与当前教学情境相关的 strategy 类型文档。

```python
# Module 5 获取教学策略建议
chunks = rag_service.retrieve(
    query=f"针对{learning_style}学习者讲授{topic}的教学策略",
    top_k=3,
    filter={"type": "strategy"}
)
```

### 6.4 接口通用约定

#### 6.4.1 服务发现机制

Module 6 作为 FastAPI 服务运行，通过 HTTP 接口对外提供检索能力。其他模块通过 HTTP 客户端调用 RAGService 的 RESTful 接口。

MVP 阶段采用直连模式，即 Module 2/3/5 在代码中直接实例化 RAGService 的本地代理对象，由代理对象负责 HTTP 通信。这种模式下，Module 6 的服务地址需要在调用方的环境变量中配置。

#### 6.4.2 版本兼容约定

Module 6 的接口遵循语义化版本规范。retrieve 方法的返回类型 Chunk 包含版本字段，标识该结果所依据的知识库版本。当知识库发生重大更新时，版本号递增。调用方可以通过检查版本号来判断是否需要重新处理检索结果。

---

## 7. 错误处理与降级策略

### 7.1 异常类型定义

Module 6 定义了以下自定义异常类型，用于区分不同类型的错误：

```python
class KGError(Exception):
    """知识库基础异常类"""
    pass

class ChromaDBConnectionError(KGError):
    """ChromaDB 连接失败"""
    pass

class EmbeddingServiceError(KGError):
    """Embedding 服务调用失败"""
    pass

class RetrievalTimeoutError(KGError):
    """检索超时"""
    pass

class DocumentNotFoundError(KGError):
    """文档不存在"""
    pass

class ValidationError(KGError):
    """参数验证失败"""
    pass
```

### 7.2 错误处理策略

#### 7.2.1 ChromaDB 连接失败

当 ChromaDB 连接失败时，系统抛出 ChromaDBConnectionError 异常。在 retrieval 流程中，这意味着无法执行向量检索。调用方应当捕获此异常并进行降级处理，例如回退到不依赖知识检索的标准提示生成流程。

```python
try:
    results = vector_store.similarity_search(query_embedding, top_k)
except ChromaDBConnectionError:
    logger.error("ChromaDB connection failed, returning empty results")
    return []
```

#### 7.2.2 Embedding 服务不可用

当 DashScope embedding API 调用失败时，系统抛出 EmbeddingServiceError 异常。模块实现了重试机制，最多重试 3 次，每次重试之间采用指数退避策略。

```python
async def embed_with_retry(self, texts: List[str], max_retries: int = 3) -> List[List[float]]:
    for attempt in range(max_retries):
        try:
            return await self.embedder.aembed(texts)
        except EmbeddingServiceError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt
            logger.warning(f"Embedding failed, retrying in {wait_time}s: {e}")
            await asyncio.sleep(wait_time)
```

#### 7.2.3 检索超时

retrieve 方法设置了默认 5 秒的超时时间。当检索操作超过超时时间时，系统抛出 RetrievalTimeoutError 异常。调用方应当将此作为降级触发的信号。

### 7.3 降级策略

#### 7.3.1 降级决策树

```
检索请求到达
    │
    ▼
ChromaDB 可用？
    │
   Yes │ No
    │   │
    ▼   └── 返回空结果列表 []
    │
    ▼
Embedding 服务可用？
    │
   Yes │ No
    │   │
    ▼   └── 返回空结果列表 []
    │
    ▼
执行向量检索
    │
    ▼
超时？
    │
   Yes │ No
    │   │
    ▼   └── 返回检索结果
返回空结果列表 []
```

#### 7.3.2 Module 2 降级流程

当 Module 2 无法获取 RAG 检索结果时，回退到不依赖知识检索的标准提示生成流程。这种设计确保了系统的鲁棒性，不会因为知识库的临时故障导致干预功能完全不可用。

```python
async def generate_with_fallback(
    self,
    breakpoint: BreakpointLocation,
    context: InterventionContext
) -> str:
    try:
        # 尝试 RAG 增强
        chunks = await self.rag_service.retrieve(
            query=f"{breakpoint.type} {breakpoint.knowledge_point}",
            top_k=3
        )
        if chunks:
            return await self.generate_enriched_hint(breakpoint, chunks)
    except KGError as e:
        logger.warning(f"RAG retrieval failed, falling back to standard prompt: {e}")

    # 降级：使用标准提示
    return await self.generate_standard_hint(breakpoint, context)
```

### 7.4 日志记录

所有错误和降级决策都应当被记录到日志中，便于运维人员监控和排查问题。日志应当包含以下信息：

- 错误类型和错误消息
- 发生的模块和函数
- 请求的相关参数（脱敏后）
- 是否触发了降级流程
- 当前知识库版本信息

---

## 8. 配置说明

### 8.1 环境变量配置

Module 6 的配置通过环境变量进行管理，所有配置项都有默认值：

```bash
# ChromaDB 配置
CHROMA_PERSIST_DIR=./data/chromadb
CHROMA_COLLECTION_NAME=math_knowledge

# DashScope 配置
DASHSCOPE_API_KEY=your_api_key_here
DASHSCOPE_EMBEDDING_MODEL=text-embedding-v1

# 服务配置
KG_SERVICE_HOST=0.0.0.0
KG_SERVICE_PORT=8000

# 超时配置
EMBEDDING_TIMEOUT=30
RETRIEVAL_TIMEOUT=5

# 重试配置
EMBEDDING_MAX_RETRIES=3
```

### 8.2 配置验证

模块启动时应当验证配置的有效性：

```python
def validate_config() -> None:
    """验证配置有效性"""
    if not os.getenv("DASHSCOPE_API_KEY"):
        raise ValueError("DASHSCOPE_API_KEY environment variable is required")

    persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./data/chromadb")
    if not os.path.exists(persist_dir):
        os.makedirs(persist_dir, exist_ok=True)
```

### 8.3 部署配置

在生产环境中，建议使用以下配置：

```bash
# 生产环境推荐配置
CHROMA_PERSIST_DIR=/var/lib/socrates/chromadb
EMBEDDING_TIMEOUT=60
RETRIEVAL_TIMEOUT=10
EMBEDDING_MAX_RETRIES=5
```

---

## 9. 评估指标

### 9.1 检索质量指标

#### 9.1.1 召回率

召回率衡量检索系统找到相关文档的能力。对于 RAG 知识库系统，召回率可以定义为对于一组预设的测试查询，人工标注的相关文档中有多少比例被系统返回。

测试集的构建需要领域专家参与。对于每个测试查询（如如何证明数列通项公式），专家标注出知识库中真正相关的文档。系统检索后计算有多少标注文档被命中。

MVP 阶段的召回率目标为大于 70%。这个目标意味着系统能够找到大部分相关知识，但仍可能遗漏一些边缘情况。

#### 9.1.2 精确率

精确率衡量检索系统返回结果的相关性。对于每个测试查询，计算返回的 top_k 文档中有多少是真正相关的。

精确率的评估同样需要人工标注。如果系统返回的前 3 个文档中有 2 个是相关的，则该查询的精确率为 66.7%。

MVP 阶段的精确率目标为大于 80%。这个目标意味着系统返回的结果大部分是有价值的，不会向调用方返回大量无关内容。

#### 9.1.3 平均检索延迟

平均检索延迟衡量系统的响应速度。延迟从接收查询请求开始计时，到返回结果为止。

对于实时性要求高的使用场景（如 Module 2 的干预提示生成），检索延迟会直接影响学生体验到的提示生成时间。MVP 阶段的平均延迟目标为小于 500 毫秒。

### 9.2 业务效果指标

#### 9.2.1 Module 2 提示质量评估

Module 2 生成的干预提示需要进行人工评估。评估维度包括提示的准确性（是否正确引用了相关知识点）、提示的有用性（学生是否能够根据提示找到解题方向）、提示的适度性（是否给出了足够的启发而不至于直接给出答案）。

人工评估采用 5 分制量表，由教学专家对一批 Module 2 生成的提示进行打分。MVP 阶段的目标是平均分达到 4.0 以上。

#### 9.2.2 Module 3 推荐效果评估

Module 3 推荐题目的准确性需要进行离线评估和在线评估。离线评估使用历史数据，计算推荐命中率（学生最终作答正确的比例）。在线评估通过 A/B 测试，对比启用 Module 6 增强前后的推荐效果差异。

MVP 阶段不强制要求在线评估指标，但需要建立离线评估的基线数据。

#### 9.2.3 Module 5 策略满意度

Module 5 生成的策略建议需要进行学生满意度调查。学生通过简短的反馈表单报告策略建议的有用程度。

MVP 阶段的目标是满意度评分达到 4.2 以上（5 分制）。

### 9.3 系统稳定性指标

#### 9.3.1 服务可用性

Module 6 作为服务提供方，需要保证一定的可用性。MVP 阶段的目标可用性为 99%（即每月最多 7 小时维护窗口期）。

#### 9.3.2 API 错误率

API 错误率定义为返回非正常响应的调用占比。错误包括 API 超时、ChromaDB 连接失败、embedding 服务不可用等。

MVP 阶段的目标错误率小于 1%。

---

## 附录 A: 文件清单

| 文件路径                      | 职责             | 核心类/函数                            |
| ----------------------------- | ---------------- | -------------------------------------- |
| `__init__.py`                 | 模块导出         | 版本信息                               |
| `models.py`                   | 数据模型         | KGDocument, KGChunk, KGQuery, KGResult |
| `embedder.py`                 | Embedding 客户端 | DashScopeEmbeddingClient               |
| `vector_store.py`             | 向量存储         | ChromaDBVectorStore                    |
| `ingestion.py`                | 导入流水线       | IngestionPipeline                      |
| `service.py`                  | 核心服务         | RAGService                             |
| `prompts.py`                  | Prompt 模板      | RAG_PROMPTS                            |
| `routes.py`                   | API 路由         | FastAPI routes                         |
| `scripts/ingest_documents.py` | CLI 导入工具     | main()                                 |

---

## 附录 B: 接口文档

### B.1 retrieve 接口规范

```
POST /api/v1/kg/retrieve
Content-Type: application/json

Request Body:
{
  "query": "string",        // 检索查询字符串
  "top_k": 3,                // 返回结果数量
  "filter": {                // 可选过滤条件
    "type": "knowledge_point | method | concept | example | strategy",
    "grade": "high_school",
    "difficulty": "easy | medium | hard"
  }
}

Response Body:
{
  "success": true,
  "data": [
    {
      "id": "kp_001",
      "text": "知识片段文本内容...",
      "metadata": {
        "type": "knowledge_point",
        "name": "数学归纳法",
        "keywords": ["归纳法", "正整数", "证明"],
        "grade": "high_school",
        "difficulty": "medium",
        "related_kp": ["递推", "数列"],
        "related_methods": ["直接证明", "反证法"]
      },
      "score": 0.95
    }
  ],
  "version": "1.0.0"
}
```

### B.2 ingest 接口规范

```
POST /api/v1/kg/ingest
Content-Type: multipart/form-data

Form Data:
{
  "file": PDF 文件,
  "type": "knowledge_point | method | concept | example | strategy",
  "name": "文档名称",
  "difficulty": "easy | medium | hard",
  "keywords": "关键词1,关键词2,关键词3"
}

Response Body:
{
  "success": true,
  "document_id": "kp_001",
  "chunks_created": 5
}
```

---

## 附录 C: 术语表

| 术语               | 说明                                         |
| ------------------ | -------------------------------------------- |
| RAG                | Retrieval-Augmented Generation，检索增强生成 |
| ChromaDB           | 开源向量数据库                               |
| DashScope          | 阿里云大模型服务平台                         |
| qwen-embeddings-v1 | 通义千问文本嵌入模型                         |
| Chunk              | 知识片段，向量数据库中的最小检索单元         |
| Ingestion          | 数据导入，知识入库的过程                     |
| Retrieval          | 检索，从知识库中查找相关内容                 |
| Embedding          | 嵌入，将文本转换为向量表示的过程             |

---

_文档结束_
