from app.evidence.extractor import AbstractEvidenceExtractor
from app.literature.providers import RetrievedPaper


def test_abstract_extraction_preserves_text_category() -> None:
    evidence = AbstractEvidenceExtractor().extract(
        RetrievedPaper(
            external_id="paper-1",
            title="Fixture",
            abstract="A sufficiently long first abstract sentence for a test. A second sentence is also long.",
            authors=[],
            published_at=None,
            url="https://example.invalid/paper-1",
        )
    )

    assert evidence
    assert all(item.evidence_kind == "EXTRACTED_ABSTRACT_TEXT" for item in evidence)
    assert all(item.confidence == 1.0 for item in evidence)

