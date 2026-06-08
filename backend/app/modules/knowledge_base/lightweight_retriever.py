"""Lightweight knowledge retriever using DashScope embeddings — no chromadb needed."""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class KnowledgeChunk:
    """Simple chunk compatible with KGChunk interface."""
    def __init__(self, content: str, metadata: dict = None):
        self.content = content
        self.metadata = metadata or {}


class LightweightRetriever:
    """In-memory embedding-based knowledge retrieval.

    Uses DashScope embeddings to build a searchable index of knowledge points,
    methods, and type descriptions. No external vector DB required.
    """

    def __init__(self, kb_api, llm_client):
        """Initialize with knowledge base and LLM client.

        Args:
            kb_api: KnowledgeBaseAPI with loaded KPs and methods.
            llm_client: DashScopeClient for computing embeddings.
        """
        self._kb = kb_api
        self._llm = llm_client
        self._documents: list[dict] = []
        self._embeddings: list[list[float]] = []
        self._built = False

    async def build_index(self) -> int:
        """Build the embedding index from knowledge base content.

        Returns number of documents indexed.
        """
        docs = []

        # Index knowledge points
        for kp_id, kp in self._kb._kps.items():
            text = f"{kp.get('name', '')}: {kp.get('content', '')}"
            if kp.get('formula'):
                text += f" 公式: {kp['formula']}"
            if text.strip():
                docs.append({
                    "id": kp_id,
                    "type": "knowledge_point",
                    "name": kp.get("name", ""),
                    "text": text[:500],
                })

        # Index methods
        for name, method in self._kb._methods.items():
            text = f"方法 {name}: {method.get('description', '')}"
            if text.strip():
                docs.append({
                    "id": f"method_{name}",
                    "type": "method",
                    "name": name,
                    "text": text[:500],
                })

        # Index type descriptions
        for t_name, mapping in self._kb._type_mappings.items():
            desc = mapping.get("description", "")
            if desc:
                docs.append({
                    "id": f"type_{t_name[:30]}",
                    "type": "problem_type",
                    "name": t_name,
                    "text": f"题型 {t_name}: {desc}"[:500],
                })

        if not docs:
            logger.warning("No documents to index")
            return 0

        # Batch embed all documents
        texts = [d["text"] for d in docs]
        batch_size = 10
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                embeddings = await self._llm.get_embeddings(batch)
                all_embeddings.extend(embeddings)
            except Exception:
                logger.exception(f"Embedding batch {i} failed, using zeros")
                all_embeddings.extend([[0.0] * 1024 for _ in batch])

        self._documents = docs
        self._embeddings = all_embeddings
        self._built = True

        logger.info(f"Indexed {len(docs)} documents ({len(self._kb._kps)} KPs, {len(self._kb._methods)} methods)")
        return len(docs)

    async def retrieve(
        self, query: str, top_k: int = 3,
    ) -> list[dict]:
        """Retrieve top-k relevant knowledge documents.

        Args:
            query: Search query.
            top_k: Number of results to return.

        Returns:
            List of dicts with 'name', 'type', 'text', 'score' keys.
        """
        if not self._built:
            await self.build_index()

        if not self._documents:
            return []

        # Embed query
        try:
            query_emb = await self._llm.get_embeddings([query])
            query_vec = query_emb[0]
        except Exception:
            logger.exception("Query embedding failed")
            return []

        # Compute cosine similarities
        scored = []
        for i, doc_vec in enumerate(self._embeddings):
            score = self._cosine(query_vec, doc_vec)
            scored.append((score, i))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, idx in scored[:top_k]:
            if score < 0.5:  # Relevance threshold
                continue
            doc = self._documents[idx]
            content = doc["text"][:200]
            metadata = {
                "type": doc["type"],
                "name": doc["name"],
                "score": round(score, 3),
            }
            results.append(KnowledgeChunk(content=content, metadata=metadata))

        return results

    def _cosine(self, a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(y * y for y in b) ** 0.5
        return dot / (na * nb) if na * nb > 0 else 0.0

    async def enrich_hint_prompt(
        self, problem_context: str, expected_step: str,
    ) -> str:
        """Build knowledge context string for hint generation."""
        query = f"{problem_context} {expected_step}"[:300]
        results = await self.retrieve(query, top_k=3)

        if not results:
            return ""

        parts = ["## 相关知识（来自知识库）"]
        for r in results:
            rtype = r.metadata.get("type", "")
            rname = r.metadata.get("name", "")
            parts.append(f"- [{rtype}] {rname}: {r.content[:100]}")
        return "\n".join(parts)
