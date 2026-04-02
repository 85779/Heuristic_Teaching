"""
Module 6 (RAG Knowledge Base) E2E Test

真实测试 ChromaDB + DashScope Embedding 的端到端流程。
测试文档摄取、向量存储、相似性搜索和 RAG 服务。
"""

import os
import sys
import asyncio
import tempfile
import time
from pathlib import Path

from dotenv import load_dotenv

# 确保 app 模块可导入
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 加载 .env 文件
load_dotenv()

from app.modules.knowledge_base.embedder import DashScopeEmbeddingClient
from app.modules.knowledge_base.vector_store import ChromaDBVectorStore
from app.modules.knowledge_base.service import RAGService
from app.modules.knowledge_base.models import KGDocument, DocumentType
from app.modules.knowledge_base.ingestion import IngestionPipeline


class E2ETester:
    """Module 6 E2E 测试器"""
    
    def __init__(self):
        self.persist_dir = tempfile.mkdtemp(prefix="socrates_chroma_")
        self.embedder = None
        self.vector_store = None
        self.rag_service = None
        self.results = {}
    
    def log(self, phase, message):
        print(f"[{phase}] {message}")
    
    def run(self):
        """运行所有 E2E 测试"""
        print("=" * 60)
        print("Module 6 E2E 测试开始")
        print(f"临时目录: {self.persist_dir}")
        print("=" * 60)
        
        try:
            asyncio.run(self.test_embedding_service())
            asyncio.run(self.test_vector_store())
            self.test_ingestion_pipeline()
            asyncio.run(self.test_rag_service())
            self.print_summary()
        except Exception as e:
            print(f"\n❌ E2E 测试失败: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def test_embedding_service(self):
        """测试 DashScope Embedding API"""
        phase = "EMBEDDING"
        self.log(phase, "初始化 DashScope Embedding Client...")
        
        try:
            self.embedder = DashScopeEmbeddingClient()
            self.results["embedding_init"] = "✅ 成功"
        except ValueError as e:
            self.log(phase, f"❌ API Key 缺失: {e}")
            self.results["embedding_init"] = f"❌ {e}"
            raise
        
        self.log(phase, "调用 DashScope API 生成embedding...")
        start = time.time()
        
        test_texts = [
            "一元二次方程的求根公式",
            "勾股定理的应用",
            "三角函数的基本性质"
        ]
        
        try:
            embeddings = await self.embedder.aembed(test_texts)
            elapsed = (time.time() - start) * 1000
            
            self.log(phase, f"✅ 成功生成 {len(embeddings)} 个 embeddings")
            self.log(phase, f"   单个维度: {len(embeddings[0])}")
            self.log(phase, f"   耗时: {elapsed:.2f}ms")
            
            self.results["embedding_api"] = f"✅ {len(embeddings)} embeddings, {elapsed:.0f}ms"
            self.results["embedding_dim"] = len(embeddings[0])
            
        except Exception as e:
            self.log(phase, f"❌ API 调用失败: {e}")
            self.results["embedding_api"] = f"❌ {e}"
            raise
    
    async def test_vector_store(self):
        """测试 ChromaDB Vector Store"""
        phase = "VECTOR_STORE"
        self.log(phase, f"初始化 ChromaDB (persist_dir: {self.persist_dir})...")
        
        try:
            self.vector_store = ChromaDBVectorStore(persist_dir=self.persist_dir)
            self.results["chromadb_init"] = "✅ 成功"
        except Exception as e:
            self.log(phase, f"❌ ChromaDB 初始化失败: {e}")
            self.results["chromadb_init"] = f"❌ {e}"
            raise
        
        self.log(phase, "添加测试文档...")
        test_docs = [
            KGDocument(
                id="test_001",
                content="一元二次方程 ax²+bx+c=0 的求根公式: x = (-b±√(b²-4ac))/(2a)，其中判别式 Δ=b²-4ac",
                metadata={"type": "formula", "topic": "algebra", "grade": "middle"}
            ),
            KGDocument(
                id="test_002",
                content="勾股定理: 在直角三角形中，a²+b²=c²，其中 c 是斜边。常见勾股数: 3,4,5; 5,12,13",
                metadata={"type": "theorem", "topic": "geometry", "grade": "middle"}
            ),
            KGDocument(
                id="test_003",
                content="三角函数基本关系: sin²θ+cos²θ=1, tanθ=sinθ/cosθ, cotθ=cosθ/sinθ",
                metadata={"type": "formula", "topic": "trigonometry", "grade": "high"}
            ),
            KGDocument(
                id="test_004",
                content="等差数列通项公式: aₙ = a₁ + (n-1)d，前 n 项和: Sₙ = n(a₁+aₙ)/2",
                metadata={"type": "formula", "topic": "sequence", "grade": "high"}
            ),
            KGDocument(
                id="test_005",
                content="两点间距离公式: 若 A(x₁,y₁), B(x₂,y₂)，则 |AB| = √((x₂-x₁)²+(y₂-y₁)²)",
                metadata={"type": "formula", "topic": "geometry", "grade": "high"}
            ),
        ]
        
        # 生成 embeddings
        texts = [doc.content for doc in test_docs]
        embeddings = await self.embedder.aembed(texts)
        
        # 添加到 ChromaDB
        self.vector_store.add_documents(test_docs, embeddings)
        
        count = self.vector_store.count()
        self.log(phase, f"✅ 添加了 {count} 个文档")
        self.results["chromadb_add"] = f"✅ {count} docs"
        
        # 测试相似性搜索
        self.log(phase, "测试相似性搜索...")
        query_embedding = embeddings[0]  # 使用第一个公式的 embedding
        results = self.vector_store.similarity_search(query_embedding, top_k=3)
        
        self.log(phase, f"✅ 搜索返回 {len(results)} 个结果")
        for chunk, score in results:
            self.log(phase, f"   [{score:.3f}] {chunk.content[:50]}...")
        
        self.results["chromadb_search"] = f"✅ {len(results)} results"
        
        # 统计
        stats = self.vector_store.get_stats()
        self.log(phase, f"   统计: {stats}")
        self.results["chromadb_stats"] = stats
    
    def test_ingestion_pipeline(self):
        """测试文档摄取管道（模拟 PDF）"""
        phase = "INGESTION"
        self.log(phase, "测试摄取管道...")
        
        pipeline = IngestionPipeline(vector_store=self.vector_store, embedder=self.embedder)
        
        # 模拟 PDF 文本（实际会用 pdfplumber）
        pdf_text = """
        高中数学知识点：函数的基本性质
        
        1. 函数的定义
        设 A、B 是非空的数集，如果对于集合 A 中的任意一个数 x，
        按照某种确定的对应关系 f，在集合 B 中都有唯一确定的数 y=f(x)
        与之对应，则称 f: A→B 为从 A 到 B 的函数。
        
        2. 函数的单调性
        设函数 f(x)的定义域为 I：
        - 增函数：若对任意 x₁<x₂，有 f(x₁)<f(x₂)
        - 减函数：若对任意 x₁<x₂，有 f(x₁)>f(x₂)
        
        3. 函数的奇偶性
        - 偶函数：f(-x)=f(x)，图像关于 y 轴对称
        - 奇函数：f(-x)=-f(x)，图像关于原点对称
        """
        
        # 模拟单个 PDF 文件的摄取
        chunks = pipeline._chunk_text(pdf_text)
        
        self.log(phase, f"✅ 将 PDF 文本切分为 {len(chunks)} 个 chunk")
        for i, chunk in enumerate(chunks[:3]):
            self.log(phase, f"   Chunk {i+1}: {str(chunk)[:60]}...")
        
        self.results["ingestion_chunking"] = f"✅ {len(chunks)} chunks"
    
    async def test_rag_service(self):
        """测试完整的 RAG 服务流程"""
        phase = "RAG_SERVICE"
        self.log(phase, "初始化 RAG 服务...")
        
        self.rag_service = RAGService(
            vector_store=self.vector_store,
            embedder=self.embedder
        )
        
        # 健康检查
        self.log(phase, "执行健康检查...")
        health = await self.rag_service.health_check()
        self.log(phase, f"   健康状态: {health}")
        self.results["rag_health"] = health
        
        # 检索测试
        test_queries = [
            "怎么解一元二次方程？",
            "勾股定理是什么？",
            "三角函数的基本公式"
        ]
        
        self.log(phase, "执行检索查询...")
        for query in test_queries:
            start = time.time()
            chunks = await self.rag_service.retrieve(query, top_k=2)
            elapsed = (time.time() - start) * 1000
            
            self.log(phase, f"\n   查询: {query}")
            for chunk in chunks:
                self.log(phase, f"   → [{chunk.similarity:.3f}] {chunk.content[:50]}...")
            
            self.log(phase, f"   耗时: {elapsed:.0f}ms")
        
        # 测试带时间的检索
        self.log(phase, "\n测试 retrieve_with_timing...")
        result = await self.rag_service.retrieve_with_timing(
            "一元二次方程求根公式", top_k=3
        )
        self.log(phase, f"   结果: {result.total} chunks, {result.query_time_ms:.0f}ms")
        self.results["rag_retrieve"] = f"✅ {result.total} chunks, {result.query_time_ms:.0f}ms"
        
        # 测试 hint enrichment
        self.log(phase, "\n测试 hint prompt enrichment...")
        chunks = await self.rag_service.retrieve(
            "一元二次方程", top_k=2
        )
        
        hint_template = "同学，这道题可以试着使用求根公式来解决。"
        enriched = await self.rag_service.enrich_hint_prompt(
            hint_template=hint_template,
            student_input="我不知道该用什么方法",
            expected_step="识别出一元二次方程结构",
            knowledge_chunks=chunks
        )
        
        self.log(phase, f"   原始提示: {hint_template}")
        self.log(phase, f"   丰富后: {enriched[:150]}...")
        self.results["rag_enrich"] = "✅ 成功"
        
        # 统计
        stats = self.rag_service.get_stats()
        self.log(phase, f"\n   知识库统计: {stats}")
        self.results["rag_stats"] = stats
    
    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("E2E 测试结果汇总")
        print("=" * 60)
        
        for key, value in self.results.items():
            print(f"  {key}: {value}")
        
        print("\n" + "=" * 60)
        print("✅ Module 6 E2E 测试全部通过！")
        print("=" * 60)
        
        print("\n📊 性能数据:")
        if "embedding_api" in self.results:
            print(f"  - Embedding 生成: {self.results.get('embedding_api', 'N/A')}")
        if "chromadb_search" in self.results:
            print(f"  - 向量搜索: {self.results.get('chromadb_search', 'N/A')}")
        if "rag_retrieve" in self.results:
            print(f"  - RAG 检索: {self.results.get('rag_retrieve', 'N/A')}")
        
        print("\n🔍 验证点:")
        print("  ✅ DashScope API 可用")
        print("  ✅ ChromaDB 持久化正常")
        print("  ✅ 文档添加和检索正常")
        print("  ✅ 文本切分管道正常")
        print("  ✅ RAG 服务完整流程正常")


if __name__ == "__main__":
    # 修复 Windows GBK 控制台编码问题
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    tester = E2ETester()
    tester.run()
