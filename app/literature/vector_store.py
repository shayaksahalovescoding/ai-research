"""Local Semantic Vector Store with Subword Embeddings, BM25 Lexical Scoring & Hybrid Search.

Supports 4 distinct retrieval modalities:
1. Dense Vector Embeddings (Ollama or subword hashing)
2. Fallback Subword Hashing (Deterministic 64-dim projection)
3. BM25 Lexical Retrieval (Term frequency-inverse document frequency)
4. Hybrid Search (Reciprocal Rank Fusion of Dense + BM25)

Filters:
- Publication Year (year_min, year_max)
- Minimum Citation Count (min_citations)
- Journal / Source Provider (arXiv, PubMed, OpenAlex, etc.)
- Section Type (METHODOLOGY, RESULTS_TABLE, FIGURE_CAPTION, ABSTRACT, DISCUSSION)
"""

from __future__ import annotations

import collections
import hashlib
import math
import re
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.core.config import Settings
from app.literature.pdf_reader import ExtractedSection


@dataclass(slots=True)
class VectorChunk:
    chunk_id: str
    paper_id: str
    paper_title: str
    journal: str
    year: int
    citations: int
    section_type: str
    heading: str
    text: str
    locator: str
    vector: list[float] = field(default_factory=list)
    tokens: list[str] = field(default_factory=list)


class SemanticVectorStore:
    """In-memory multi-modal scientific literature store with dense, BM25, and hybrid search."""

    def __init__(self, settings: Settings | None = None, vector_dim: int = 64) -> None:
        self._settings = settings or Settings()
        self._vector_dim = vector_dim
        self._chunks: list[VectorChunk] = []
        self._doc_freqs: dict[str, int] = collections.defaultdict(int)
        self._avg_doc_len: float = 0.0

    def clear(self) -> None:
        self._chunks.clear()
        self._doc_freqs.clear()
        self._avg_doc_len = 0.0

    def count(self) -> int:
        return len(self._chunks)

    def embed_text(self, text: str) -> list[float]:
        """Generates a normalized semantic dense vector representation."""
        ollama_vec = self._try_ollama_embedding(text)
        if ollama_vec:
            return ollama_vec
        return self._generate_dense_semantic_vector(text)

    def _try_ollama_embedding(self, text: str) -> list[float] | None:
        urls_to_try = [
            self._settings.ollama_base_url,
            "http://127.0.0.1:11434",
            "http://localhost:11434",
            "http://host.docker.internal:11434",
        ]
        timeout = httpx.Timeout(4.0, connect=1.0)
        for base_url in list(dict.fromkeys(urls_to_try)):
            try:
                endpoint = f"{base_url.rstrip('/')}/api/embeddings"
                payload = {
                    "model": self._settings.ollama_model,
                    "prompt": text[:500],
                }
                with httpx.Client(timeout=timeout) as client:
                    resp = client.post(endpoint, json=payload)
                    if resp.is_success:
                        emb = resp.json().get("embedding")
                        if isinstance(emb, list) and len(emb) > 0:
                            norm = math.sqrt(sum(x * x for x in emb)) or 1.0
                            return [x / norm for x in emb]
            except Exception:
                continue
        return None

    def _generate_dense_semantic_vector(self, text: str) -> list[float]:
        """Generates a normalized multi-gram subword semantic vector."""
        vec = [0.0] * self._vector_dim
        words = re.findall(r"\b\w+\b", text.lower())
        if not words:
            return [1.0 / math.sqrt(self._vector_dim)] * self._vector_dim

        for word in words:
            w_hash = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = w_hash % self._vector_dim
            sign = 1.0 if (w_hash >> 8) & 1 else -1.0
            vec[idx] += sign * (1.0 + len(word) * 0.1)

            for n in (3, 4):
                if len(word) >= n:
                    for i in range(len(word) - n + 1):
                        ngram = word[i : i + n]
                        ng_hash = int(hashlib.sha256(ngram.encode("utf-8")).hexdigest(), 16)
                        ng_idx = ng_hash % self._vector_dim
                        ng_sign = 1.0 if (ng_hash >> 4) & 1 else -1.0
                        vec[ng_idx] += ng_sign * 0.5

        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0.0:
            return [x / norm for x in vec]
        return [0.0] * self._vector_dim

    def index_paper_sections(
        self,
        paper_id: str,
        paper_title: str,
        journal: str,
        year: int,
        citations: int,
        sections: list[ExtractedSection],
    ) -> None:
        """Embeds and indexes all sections of a paper for dense and lexical search."""
        for sec in sections:
            chunk_id = f"{paper_id}:{sec.locator}"
            if any(c.chunk_id == chunk_id for c in self._chunks):
                continue

            full_text = f"{sec.heading}\n{sec.content}"
            vector = self.embed_text(full_text)
            tokens = re.findall(r"\b\w+\b", full_text.lower())

            chunk = VectorChunk(
                chunk_id=chunk_id,
                paper_id=paper_id,
                paper_title=paper_title,
                journal=journal,
                year=year,
                citations=citations,
                section_type=sec.section_type,
                heading=sec.heading,
                text=sec.content,
                locator=sec.locator,
                vector=vector,
                tokens=tokens,
            )
            self._chunks.append(chunk)

            # Update document frequency stats for BM25
            unique_tokens = set(tokens)
            for t in unique_tokens:
                self._doc_freqs[t] += 1

        total_tokens = sum(len(c.tokens) for c in self._chunks)
        self._avg_doc_len = total_tokens / len(self._chunks) if self._chunks else 1.0

    def _matches_filters(
        self,
        chunk: VectorChunk,
        year_min: int | None = None,
        year_max: int | None = None,
        min_citations: int | None = None,
        journal: str | None = None,
        section_type: str | None = None,
    ) -> bool:
        if year_min is not None and chunk.year < year_min:
            return False
        if year_max is not None and chunk.year > year_max:
            return False
        if min_citations is not None and chunk.citations < min_citations:
            return False
        if journal and journal.lower() not in chunk.journal.lower():
            return False
        if section_type and section_type.upper() not in {"ALL", ""}:
            if chunk.section_type.upper() != section_type.upper():
                return False
        return True

    def search_dense(
        self,
        query: str,
        limit: int = 10,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """Pure dense vector similarity retrieval."""
        if not self._chunks or not query.strip():
            return []
        query_vec = self.embed_text(query)
        results: list[tuple[float, VectorChunk]] = []

        for chunk in self._chunks:
            if not self._matches_filters(chunk, **filters):
                continue
            dot = sum(q * c for q, c in zip(query_vec, chunk.vector, strict=False))
            sim = max(0.0, min(1.0, (dot + 1.0) / 2.0 if dot < 0 else dot))
            results.append((sim, chunk))

        results.sort(key=lambda x: x[0], reverse=True)
        return self._format_results(results[:limit])

    def search_bm25(
        self,
        query: str,
        k1: float = 1.5,
        b: float = 0.75,
        limit: int = 10,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """Pure BM25 lexical keyword retrieval."""
        if not self._chunks or not query.strip():
            return []
        query_tokens = re.findall(r"\b\w+\b", query.lower())
        if not query_tokens:
            return []

        n_docs = len(self._chunks)
        results: list[tuple[float, VectorChunk]] = []

        for chunk in self._chunks:
            if not self._matches_filters(chunk, **filters):
                continue
            doc_len = len(chunk.tokens) or 1
            chunk_token_counts = collections.Counter(chunk.tokens)
            bm25_score = 0.0

            for t in query_tokens:
                if t in chunk_token_counts:
                    tf = chunk_token_counts[t]
                    df = self._doc_freqs.get(t, 1)
                    idf = math.log(1.0 + (n_docs - df + 0.5) / (df + 0.5))
                    num = tf * (k1 + 1.0)
                    den = tf + k1 * (1.0 - b + b * (doc_len / self._avg_doc_len))
                    bm25_score += idf * (num / den)

            results.append((max(0.0, bm25_score), chunk))

        results.sort(key=lambda x: x[0], reverse=True)
        return self._format_results(results[:limit])

    def search_hybrid(
        self,
        query: str,
        limit: int = 10,
        dense_weight: float = 0.60,
        bm25_weight: float = 0.40,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """Reciprocal Rank Fusion & weighted score combination of Dense + BM25 search."""
        dense_results = self.search_dense(query, limit=limit * 2, **filters)
        bm25_results = self.search_bm25(query, limit=limit * 2, **filters)

        # Reciprocal Rank Fusion
        rrf_scores: dict[str, float] = collections.defaultdict(float)
        chunk_map: dict[str, dict[str, Any]] = {}

        for rank, r in enumerate(dense_results, start=1):
            cid = r["chunk_id"]
            rrf_scores[cid] += dense_weight * (1.0 / (60 + rank))
            chunk_map[cid] = r

        for rank, r in enumerate(bm25_results, start=1):
            cid = r["chunk_id"]
            rrf_scores[cid] += bm25_weight * (1.0 / (60 + rank))
            chunk_map[cid] = r

        sorted_cids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        final_results = [chunk_map[cid] for cid in sorted_cids[:limit]]
        return final_results

    def search(self, query: str, limit: int = 10, **filters: Any) -> list[dict[str, Any]]:
        """Default search endpoint utilizing Hybrid Search."""
        return self.search_hybrid(query, limit=limit, **filters)

    def _format_results(self, raw_results: list[tuple[float, VectorChunk]]) -> list[dict[str, Any]]:
        ranked: list[dict[str, Any]] = []
        for sim, chunk in raw_results:
            ranked.append({
                "chunk_id": chunk.chunk_id,
                "paper_id": chunk.paper_id,
                "paper_title": chunk.paper_title,
                "journal": chunk.journal,
                "year": chunk.year,
                "citations": chunk.citations,
                "section_type": chunk.section_type,
                "heading": chunk.heading,
                "text": chunk.text,
                "locator": chunk.locator,
                "similarity_score": round(sim, 4),
                "similarity_percentage": f"{sim * 100:.1f}%",
            })
        return ranked


# Global in-memory singleton vector store
global_vector_store = SemanticVectorStore()
