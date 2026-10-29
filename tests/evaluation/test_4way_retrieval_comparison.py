"""Tests for Comparative Retrieval Benchmark (Dense vs BM25 vs Hybrid)."""

from __future__ import annotations

from app.literature.pdf_reader import ExtractedSection
from app.literature.retrieval_eval import GroundTruthQuery, RetrievalBenchmarkEvaluator
from app.literature.vector_store import SemanticVectorStore


def test_4way_retrieval_comparison() -> None:
    store = SemanticVectorStore()

    sections_1 = [
        ExtractedSection(
            section_type="METHODOLOGY",
            heading="Curvature Adaptive Momentum Optimization",
            content="We study curvature-adaptive stochastic momentum on non-convex objective surfaces.",
            locator="pdf:opt1:sec1",
        )
    ]
    sections_2 = [
        ExtractedSection(
            section_type="METHODOLOGY",
            heading="Second-Order Diagonal Preconditioning",
            content="Conditioning stochastic gradients with diagonal bounds accelerates non-convex optimization.",
            locator="pdf:opt2:sec1",
        )
    ]
    sections_3 = [
        ExtractedSection(
            section_type="ABSTRACT",
            heading="Lipid Nanoparticles",
            content="Lipid nanoparticle formulations for targeted drug delivery across blood brain barrier.",
            locator="pdf:bio:sec1",
        )
    ]

    store.index_paper_sections("arxiv:opt.01", "Adaptive Momentum", "arXiv", 2024, 25, sections_1)
    store.index_paper_sections("arxiv:opt.02", "Diagonal Preconditioning", "arXiv", 2023, 15, sections_2)
    store.index_paper_sections("arxiv:bio.01", "Lipid Nanoparticles", "PubMed", 2022, 50, sections_3)

    queries = [
        GroundTruthQuery(
            query_id="Q-01",
            query_text="curvature adaptive momentum non-convex optimization",
            domain="OPTIMIZATION",
            relevant_paper_ids={"arxiv:opt.01", "arxiv:opt.02"},
            relevance_scores={"arxiv:opt.01": 3.0, "arxiv:opt.02": 2.0},
        )
    ]

    evaluator = RetrievalBenchmarkEvaluator(ground_truth_queries=queries)
    comparison = evaluator.compare_modalities(store)

    assert "dense" in comparison
    assert "bm25" in comparison
    assert "hybrid" in comparison

    assert comparison["dense"].mean_recall_at_5 > 0.0
    assert comparison["bm25"].mean_recall_at_5 > 0.0
    assert comparison["hybrid"].mean_recall_at_5 > 0.0
    assert comparison["hybrid"].mean_ndcg_at_10 > 0.0
