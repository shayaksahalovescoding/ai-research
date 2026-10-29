"""Unit tests for Information Retrieval Benchmark Suite (Recall@K, MRR, nDCG)."""

from __future__ import annotations

from app.literature.pdf_reader import ExtractedSection
from app.literature.retrieval_eval import GroundTruthQuery, RetrievalBenchmarkEvaluator
from app.literature.vector_store import SemanticVectorStore


def test_retrieval_benchmark_evaluator_metrics() -> None:
    store = SemanticVectorStore()

    # Index sample papers
    sections_opt_1 = [
        ExtractedSection(
            section_type="METHODOLOGY",
            heading="Curvature-Adaptive Momentum Optimization",
            content="We evaluate curvature-adaptive momentum on non-convex loss surfaces to reduce oscillation.",
            locator="pdf:opt1:sec1",
        )
    ]
    sections_opt_2 = [
        ExtractedSection(
            section_type="METHODOLOGY",
            heading="Second-Order Gradient Conditioning",
            content="Conditioning stochastic gradients with diagonal curvature bounds accelerates convergence.",
            locator="pdf:opt2:sec1",
        )
    ]
    sections_unrelated = [
        ExtractedSection(
            section_type="ABSTRACT",
            heading="General Overview",
            content="Synthesizing nanoparticles for drug delivery and cellular uptake kinetics.",
            locator="pdf:bio:sec1",
        )
    ]

    store.index_paper_sections("arxiv:opt.01", "Adaptive Momentum", "arXiv", 2024, 25, sections_opt_1)
    store.index_paper_sections("arxiv:opt.02", "Gradient Conditioning", "arXiv", 2023, 15, sections_opt_2)
    store.index_paper_sections("arxiv:bio.01", "Nanoparticle Overview", "PubMed", 2022, 50, sections_unrelated)

    queries = [
        GroundTruthQuery(
            query_id="Q-OPT-01",
            query_text="curvature adaptive momentum non-convex optimization",
            domain="OPTIMIZATION",
            relevant_paper_ids={"arxiv:opt.01", "arxiv:opt.02"},
            relevance_scores={"arxiv:opt.01": 3.0, "arxiv:opt.02": 2.0},
        )
    ]

    evaluator = RetrievalBenchmarkEvaluator(ground_truth_queries=queries)
    report = evaluator.evaluate_vector_store(store, top_k=5)

    assert report.total_queries == 1
    assert report.mean_recall_at_5 > 0.0
    assert report.mean_mrr > 0.0
    assert report.mean_ndcg_at_10 > 0.0

    q_metrics = report.per_query_metrics[0]
    assert q_metrics["query_id"] == "Q-OPT-01"
    assert q_metrics["recall@5"] == 1.0  # Both relevant papers retrieved in top 5
    assert q_metrics["mrr"] == 1.0  # Top result is relevant


def test_ndcg_calculation_edge_cases() -> None:
    # Test perfect ranking vs reversed ranking
    retrieved_perfect = ["p1", "p2", "p3"]
    scores = {"p1": 3.0, "p2": 2.0, "p3": 1.0}
    ndcg_perfect = RetrievalBenchmarkEvaluator._compute_ndcg(retrieved_perfect, scores, k=3)
    assert round(ndcg_perfect, 4) == 1.0

    retrieved_inverted = ["p3", "p2", "p1"]
    ndcg_inverted = RetrievalBenchmarkEvaluator._compute_ndcg(retrieved_inverted, scores, k=3)
    assert ndcg_inverted < 1.0
    assert ndcg_inverted > 0.0
