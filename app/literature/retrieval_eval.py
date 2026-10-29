"""Information Retrieval Benchmark Suite for Scientific Literature & Vector Search.

Measures quantitative retrieval quality across:
- Recall@K (K = 5, 10, 20)
- MRR (Mean Reciprocal Rank)
- nDCG@10 (Normalized Discounted Cumulative Gain)

Compares:
1. Dense Vector Embeddings
2. BM25 Lexical Scoring
3. Hybrid Search (Dense + BM25 Fusion)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable

from app.literature.vector_store import SemanticVectorStore


@dataclass(frozen=True, slots=True)
class GroundTruthQuery:
    query_id: str
    query_text: str
    domain: str
    relevant_paper_ids: set[str]
    relevance_scores: dict[str, float]  # paper_id -> graded relevance (e.g. 1.0, 2.0, 3.0)


@dataclass(frozen=True, slots=True)
class IRBenchmarkReport:
    mode: str
    total_queries: int
    mean_recall_at_5: float
    mean_recall_at_10: float
    mean_recall_at_20: float
    mean_mrr: float
    mean_ndcg_at_10: float
    per_query_metrics: list[dict[str, Any]]


class RetrievalBenchmarkEvaluator:
    """Evaluates scientific semantic search across Dense, BM25, and Hybrid modalities."""

    def __init__(self, ground_truth_queries: list[GroundTruthQuery] | None = None) -> None:
        self.queries = ground_truth_queries or self._default_benchmark_queries()

    def evaluate_vector_store(
        self,
        vector_store: SemanticVectorStore,
        mode: str = "hybrid",
        top_k: int = 20,
    ) -> IRBenchmarkReport:
        search_fn: Callable[[str, int], list[dict[str, Any]]]
        if mode == "dense":
            search_fn = lambda q, lim: vector_store.search_dense(q, limit=lim)  # noqa: E731
        elif mode == "bm25":
            search_fn = lambda q, lim: vector_store.search_bm25(q, limit=lim)  # noqa: E731
        else:
            search_fn = lambda q, lim: vector_store.search_hybrid(q, limit=lim)  # noqa: E731

        per_query_metrics: list[dict[str, Any]] = []
        recalls_5: list[float] = []
        recalls_10: list[float] = []
        recalls_20: list[float] = []
        mrrs: list[float] = []
        ndcgs_10: list[float] = []

        for q in self.queries:
            results = search_fn(q.query_text, top_k)
            retrieved_ids = [str(r.get("paper_id", "")) for r in results]

            r5 = self._compute_recall(retrieved_ids[:5], q.relevant_paper_ids)
            r10 = self._compute_recall(retrieved_ids[:10], q.relevant_paper_ids)
            r20 = self._compute_recall(retrieved_ids[:20], q.relevant_paper_ids)
            mrr = self._compute_mrr(retrieved_ids, q.relevant_paper_ids)
            ndcg10 = self._compute_ndcg(retrieved_ids[:10], q.relevance_scores, k=10)

            recalls_5.append(r5)
            recalls_10.append(r10)
            recalls_20.append(r20)
            mrrs.append(mrr)
            ndcgs_10.append(ndcg10)

            per_query_metrics.append({
                "query_id": q.query_id,
                "query_text": q.query_text,
                "recall@5": round(r5, 4),
                "recall@10": round(r10, 4),
                "recall@20": round(r20, 4),
                "mrr": round(mrr, 4),
                "ndcg@10": round(ndcg10, 4),
            })

        n = len(self.queries) or 1
        return IRBenchmarkReport(
            mode=mode.upper(),
            total_queries=len(self.queries),
            mean_recall_at_5=round(sum(recalls_5) / n, 4),
            mean_recall_at_10=round(sum(recalls_10) / n, 4),
            mean_recall_at_20=round(sum(recalls_20) / n, 4),
            mean_mrr=round(sum(mrrs) / n, 4),
            mean_ndcg_at_10=round(sum(ndcgs_10) / n, 4),
            per_query_metrics=per_query_metrics,
        )

    def compare_modalities(self, vector_store: SemanticVectorStore) -> dict[str, IRBenchmarkReport]:
        """Runs comparative evaluation across Dense, BM25, and Hybrid modalities."""
        return {
            "dense": self.evaluate_vector_store(vector_store, mode="dense"),
            "bm25": self.evaluate_vector_store(vector_store, mode="bm25"),
            "hybrid": self.evaluate_vector_store(vector_store, mode="hybrid"),
        }

    @staticmethod
    def _compute_recall(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
        if not relevant_ids:
            return 1.0
        hits = sum(1 for pid in retrieved_ids if pid in relevant_ids)
        return min(1.0, hits / len(relevant_ids))

    @staticmethod
    def _compute_mrr(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
        for rank, pid in enumerate(retrieved_ids, start=1):
            if pid in relevant_ids:
                return 1.0 / rank
        return 0.0

    @staticmethod
    def _compute_ndcg(retrieved_ids: list[str], relevance_scores: dict[str, float], k: int = 10) -> float:
        dcg = 0.0
        for rank, pid in enumerate(retrieved_ids[:k], start=1):
            rel = relevance_scores.get(pid, 0.0)
            if rel > 0:
                dcg += (2.0**rel - 1.0) / math.log2(rank + 1.0)

        ideal_rels = sorted(relevance_scores.values(), reverse=True)[:k]
        idcg = 0.0
        for rank, rel in enumerate(ideal_rels, start=1):
            if rel > 0:
                idcg += (2.0**rel - 1.0) / math.log2(rank + 1.0)

        if idcg == 0.0:
            return 1.0 if dcg == 0.0 else 0.0
        return min(1.0, dcg / idcg)

    @staticmethod
    def _default_benchmark_queries() -> list[GroundTruthQuery]:
        return [
            GroundTruthQuery(
                query_id="Q-ML-01",
                query_text="curvature-adaptive momentum non-convex optimization loss landscape",
                domain="MACHINE_LEARNING",
                relevant_paper_ids={"arxiv:opt.01", "arxiv:opt.02"},
                relevance_scores={"arxiv:opt.01": 3.0, "arxiv:opt.02": 2.0},
            ),
            GroundTruthQuery(
                query_id="Q-RL-02",
                query_text="optimistic Q-ensemble estimation overestimation bias continuous control",
                domain="REINFORCEMENT_LEARNING",
                relevant_paper_ids={"arxiv:rl.01", "arxiv:rl.02"},
                relevance_scores={"arxiv:rl.01": 3.0, "arxiv:rl.02": 2.0},
            ),
            GroundTruthQuery(
                query_id="Q-REG-03",
                query_text="elastic net structured sparsity generalization out-of-distribution covariate shift",
                domain="GENERALIZATION",
                relevant_paper_ids={"arxiv:gen.01"},
                relevance_scores={"arxiv:gen.01": 3.0},
            ),
        ]
