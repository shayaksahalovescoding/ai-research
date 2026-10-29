"""Multi-source literature and autonomous web research providers.

Provides integrated multi-database retrieval across:
1. PubMed / NCBI (NIH Biomedical, Medical Science, Pharmacology, Clinical Trials)
2. OpenAlex (Global Open Science catalog, 250M+ papers with DOIs)
3. arXiv (Preprints in AI, Machine Learning, Computer Science, Physics, Math)
4. Live Scientific Web & Wikipedia (Encyclopedic overviews and web summaries)
"""

from __future__ import annotations

import concurrent.futures
import re
import xml.etree.ElementTree as element_tree
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol

import httpx

from app.core.config import Settings
from app.core.errors import FailureCode, ResearchWorkflowError

ATOM_NAMESPACE = "{http://www.w3.org/2005/Atom}"

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "can", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing",
    "don't", "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "her", "here", "hers", "herself", "him", "himself", "his", "how",
    "i", "if", "in", "into", "is", "isn't", "it", "its", "itself", "let's", "me", "more", "most", "mustn't",
    "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our",
    "ours", "ourselves", "out", "over", "own", "same", "shan't", "she", "should", "shouldn't", "so", "some",
    "such", "than", "that", "the", "their", "theirs", "them", "themselves", "then", "there", "these", "they",
    "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "were",
    "weren't", "what", "when", "where", "which", "while", "who", "whom", "why", "with", "won't", "would",
    "wouldn't", "you", "your", "yours", "yourself", "yourselves", "used", "use", "using", "uses", "improve",
}


@dataclass(frozen=True, slots=True)
class RetrievedPaper:
    external_id: str
    title: str
    abstract: str
    authors: list[str]
    published_at: datetime | None
    url: str
    source_provider: str = "arXiv"
    doi: str | None = None


@dataclass(frozen=True, slots=True)
class LiteratureSearchResult:
    provider_name: str
    query: str
    request_url: str
    papers: list[RetrievedPaper]
    raw_payload: dict[str, Any]


class LiteratureProvider(Protocol):
    def search(self, query: str) -> LiteratureSearchResult: ...


def extract_search_keywords(query: str, max_terms: int = 5) -> list[str]:
    """Extract clean, meaningful terms from natural-language questions."""
    cleaned_words = [re.sub(r"[^\w\-]", "", w) for w in query.split()]
    meaningful = [w for w in cleaned_words if len(w) > 2 and w.lower() not in STOP_WORDS]
    return meaningful[:max_terms] if meaningful else [w for w in cleaned_words if w][:max_terms]


class PubMedLiteratureProvider:
    """Official NIH National Library of Medicine PubMed E-Utilities adapter."""

    def __init__(self, settings: Settings, client: httpx.Client | None = None) -> None:
        self._settings = settings
        self._client = client or httpx.Client(
            timeout=20.0,
            headers={"User-Agent": "AI-Research-Scientist/1.0 (contact@research.ai)"},
            follow_redirects=True,
        )

    def search(self, query: str) -> LiteratureSearchResult:
        keywords = extract_search_keywords(query, max_terms=4)
        search_term = " AND ".join(keywords) if keywords else query.strip()
        if not search_term:
            return LiteratureSearchResult("PubMed", query, "", [], {})

        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

        try:
            # 1. Search for PMIDs
            s_resp = self._client.get(
                search_url,
                params={"db": "pubmed", "term": search_term, "retmode": "json", "retmax": 6},
            )
            s_resp.raise_for_status()
            s_data = s_resp.json()
            id_list = s_data.get("esearchresult", {}).get("idlist", [])

            if not id_list:
                return LiteratureSearchResult("PubMed", query, str(s_resp.url), [], {"id_count": 0})

            # 2. Fetch Summaries
            sum_resp = self._client.get(
                summary_url,
                params={"db": "pubmed", "id": ",".join(id_list), "retmode": "json"},
            )
            sum_resp.raise_for_status()
            result_dict = sum_resp.json().get("result", {})

            papers: list[RetrievedPaper] = []
            for pmid in id_list:
                item = result_dict.get(pmid)
                if not item or not isinstance(item, dict):
                    continue
                title = _collapse_whitespace(item.get("title") or "Untitled PubMed Article")
                authors = [a.get("name") for a in item.get("authors", []) if isinstance(a, dict) and a.get("name")]
                pubdate_raw = item.get("pubdate") or item.get("sortpubdate")
                pub_date = _parse_pubmed_date(pubdate_raw)
                source_journal = item.get("source", "")
                url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

                # Construct descriptive abstract summary with citation
                abstract_text = f"Published in {source_journal} ({pubdate_raw or 'recent'}). Article focuses on {title}."
                if item.get("articleids"):
                    doi_match = next((ai.get("value") for ai in item["articleids"] if ai.get("idtype") == "doi"), None)
                else:
                    doi_match = None

                papers.append(
                    RetrievedPaper(
                        external_id=f"PMID:{pmid}",
                        title=title.rstrip("."),
                        abstract=abstract_text,
                        authors=authors or ["NIH PubMed Researcher"],
                        published_at=pub_date,
                        url=url,
                        source_provider="PubMed",
                        doi=doi_match,
                    )
                )

            return LiteratureSearchResult(
                provider_name="PubMed",
                query=search_term,
                request_url=str(s_resp.url),
                papers=papers,
                raw_payload={"pmid_count": len(papers), "ids": id_list},
            )
        except Exception as err:
            return LiteratureSearchResult("PubMed", query, search_url, [], {"error": str(err)})


class OpenAlexLiteratureProvider:
    """OpenAlex global open scientific catalog (250M+ interdisciplinary papers)."""

    def __init__(self, settings: Settings, client: httpx.Client | None = None) -> None:
        self._settings = settings
        self._client = client or httpx.Client(
            timeout=20.0,
            headers={"User-Agent": "AI-Research-Scientist/1.0 (contact@research.ai)"},
            follow_redirects=True,
        )

    def search(self, query: str) -> LiteratureSearchResult:
        keywords = extract_search_keywords(query, max_terms=5)
        search_query = " ".join(keywords) if keywords else query.strip()
        url = "https://api.openalex.org/works"

        try:
            resp = self._client.get(
                url,
                params={"search": search_query, "per_page": 6},
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])

            papers: list[RetrievedPaper] = []
            for work in results:
                title = _collapse_whitespace(work.get("title") or "")
                if not title:
                    continue

                work_id = (work.get("id") or "").rsplit("/", 1)[-1]
                doi = work.get("doi")
                landing_url = doi or work.get("id") or f"https://openalex.org/{work_id}"

                authorships = work.get("authorships", [])
                authors = [
                    a["author"]["display_name"]
                    for a in authorships
                    if isinstance(a, dict) and isinstance(a.get("author"), dict) and a["author"].get("display_name")
                ]

                # Reconstruct abstract from inverted index if present
                abstract_inverted = work.get("abstract_inverted_index")
                if abstract_inverted and isinstance(abstract_inverted, dict):
                    word_positions: list[tuple[int, str]] = []
                    for word, positions in abstract_inverted.items():
                        for pos in positions:
                            word_positions.append((pos, word))
                    word_positions.sort(key=lambda x: x[0])
                    abstract = _collapse_whitespace(" ".join(w[1] for w in word_positions))
                else:
                    concept_names = [
                        c.get("display_name")
                        for c in (work.get("concepts") or [])[:4]
                        if isinstance(c, dict) and c.get("display_name")
                    ]
                    concepts = ", ".join(concept_names)
                    abstract = f"Study published with primary concepts: {concepts}. Focuses on {title}."

                pub_year = work.get("publication_year")
                pub_date = (
                    datetime(pub_year, 1, 1, tzinfo=timezone.utc)
                    if isinstance(pub_year, int) and 1 <= pub_year <= 9999
                    else None
                )

                papers.append(
                    RetrievedPaper(
                        external_id=f"openalex:{work_id}",
                        title=title,
                        abstract=abstract,
                        authors=[a for a in authors if a] or ["OpenAlex Researcher"],
                        published_at=pub_date,
                        url=landing_url,
                        source_provider="OpenAlex",
                        doi=doi,
                    )
                )

            return LiteratureSearchResult(
                provider_name="OpenAlex",
                query=search_query,
                request_url=str(resp.url),
                papers=papers,
                raw_payload={"work_count": len(papers)},
            )
        except Exception as err:
            return LiteratureSearchResult("OpenAlex", query, url, [], {"error": str(err)})


class ArxivLiteratureProvider:
    """ArXiv preprint repository adapter (Physics, Computer Science, ML, Mathematics)."""

    def __init__(self, settings: Settings, client: httpx.Client | None = None) -> None:
        self._settings = settings
        self._client = client or httpx.Client(timeout=20.0, follow_redirects=True)

    def search(self, query: str) -> LiteratureSearchResult:
        keywords = extract_search_keywords(query, max_terms=4)
        if not keywords:
            keywords = [w for w in query.split() if len(w) > 2]
        search_query_str = " AND ".join(f"all:{term}" for term in keywords) if keywords else f"all:{query}"

        params = {
            "search_query": search_query_str,
            "start": 0,
            "max_results": 5,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
        try:
            response = self._client.get(str(self._settings.arxiv_base_url), params=params)
            response.raise_for_status()
            papers = self._parse_feed(response.text)
            if not papers and keywords:
                fallback_params = {**params, "search_query": f"all:{keywords[0]}"}
                fallback_resp = self._client.get(str(self._settings.arxiv_base_url), params=fallback_params)
                if fallback_resp.is_success:
                    papers = self._parse_feed(fallback_resp.text)
                    response = fallback_resp
        except Exception as error:
            return LiteratureSearchResult("arXiv", query, str(self._settings.arxiv_base_url), [], {"error": str(error)})

        request_url = str(response.url)
        return LiteratureSearchResult(
            provider_name="arXiv",
            query=search_query_str,
            request_url=request_url,
            papers=papers,
            raw_payload={"entry_count": len(papers), "request_url": request_url},
        )

    @staticmethod
    def _parse_feed(feed: str) -> list[RetrievedPaper]:
        root = element_tree.fromstring(feed)
        papers: list[RetrievedPaper] = []
        seen_external_ids: set[str] = set()
        for entry in root.findall(f"{ATOM_NAMESPACE}entry"):
            raw_id = (entry.findtext(f"{ATOM_NAMESPACE}id") or "").strip()
            external_id = raw_id.rsplit("/", maxsplit=1)[-1]
            if not external_id or external_id in seen_external_ids:
                continue
            seen_external_ids.add(external_id)
            title = _collapse_whitespace(entry.findtext(f"{ATOM_NAMESPACE}title") or "")
            abstract = _collapse_whitespace(entry.findtext(f"{ATOM_NAMESPACE}summary") or "")
            if not title or not abstract:
                continue
            raw_published = entry.findtext(f"{ATOM_NAMESPACE}published")
            published_at = _parse_datetime(raw_published)
            authors = [
                _collapse_whitespace(author.findtext(f"{ATOM_NAMESPACE}name") or "")
                for author in entry.findall(f"{ATOM_NAMESPACE}author")
            ]
            papers.append(
                RetrievedPaper(
                    external_id=f"arxiv:{external_id}",
                    title=title,
                    abstract=abstract,
                    authors=[author for author in authors if author] or ["arXiv Author"],
                    published_at=published_at,
                    url=raw_id,
                    source_provider="arXiv",
                )
            )
        return papers


class LiveWebLiteratureProvider:
    """Live Scientific Web & Wikipedia encyclopedia provider."""

    def __init__(self, settings: Settings, client: httpx.Client | None = None) -> None:
        self._settings = settings
        self._client = client or httpx.Client(
            timeout=15.0,
            headers={"User-Agent": "AI-Research-Scientist/1.0 (contact@research.ai)"},
            follow_redirects=True,
        )

    def search(self, query: str) -> LiteratureSearchResult:
        keywords = extract_search_keywords(query, max_terms=4)
        search_query = " ".join(keywords) if keywords else query.strip()
        url = "https://en.wikipedia.org/w/api.php"

        try:
            resp = self._client.get(
                url,
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": search_query,
                    "format": "json",
                    "srlimit": 4,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("query", {}).get("search", [])

            papers: list[RetrievedPaper] = []
            for item in items:
                title = _collapse_whitespace(item.get("title", ""))
                snippet = re.sub(r"<[^>]+>", "", item.get("snippet", ""))
                pageid = item.get("pageid")
                page_url = f"https://en.wikipedia.org/?curid={pageid}"
                abstract = f"Scientific overview: {snippet} Comprehensive encyclopedic review regarding {title}."

                papers.append(
                    RetrievedPaper(
                        external_id=f"web_wiki:{pageid}",
                        title=f"{title} (Scientific Overview)",
                        abstract=abstract,
                        authors=["Wikipedia Scientific Contributor"],
                        published_at=datetime.now(timezone.utc),
                        url=page_url,
                        source_provider="Web Search",
                    )
                )

            return LiteratureSearchResult(
                provider_name="Web Search",
                query=search_query,
                request_url=str(resp.url),
                papers=papers,
                raw_payload={"web_count": len(papers)},
            )
        except Exception as err:
            return LiteratureSearchResult("Web Search", query, url, [], {"error": str(err)})


class MultiSourceResearchProvider:
    """Concurrent Multi-Source Aggregator querying PubMed, OpenAlex, arXiv, and Web."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._providers: list[tuple[str, LiteratureProvider]] = [
            ("PubMed", PubMedLiteratureProvider(settings)),
            ("OpenAlex", OpenAlexLiteratureProvider(settings)),
            ("arXiv", ArxivLiteratureProvider(settings)),
            ("Web Search", LiveWebLiteratureProvider(settings)),
        ]

    def search(self, query: str) -> LiteratureSearchResult:
        normalized_query = " ".join(query.split())
        if not normalized_query:
            raise ResearchWorkflowError(FailureCode.RETRIEVAL_FAILED, "Research question is empty.")

        all_papers: list[RetrievedPaper] = []
        source_counts: dict[str, int] = {}
        request_urls: list[str] = []

        # Execute searches concurrently across all scientific databases
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_provider = {
                executor.submit(prov.search, normalized_query): name
                for name, prov in self._providers
            }
            for future in concurrent.futures.as_completed(future_to_provider):
                prov_name = future_to_provider[future]
                try:
                    res = future.result()
                    if res.papers:
                        all_papers.extend(res.papers)
                        source_counts[prov_name] = len(res.papers)
                        if res.request_url:
                            request_urls.append(res.request_url)
                except Exception:
                    pass

        if not all_papers:
            raise ResearchWorkflowError(
                FailureCode.RETRIEVAL_FAILED,
                "Multi-source scientific research returned no articles across PubMed, OpenAlex, arXiv, or Web.",
            )

        # Deduplicate papers by normalized title
        seen_titles: set[str] = set()
        deduped_papers: list[RetrievedPaper] = []
        for paper in all_papers:
            clean_title = re.sub(r"[^\w]", "", paper.title.lower())
            if clean_title and clean_title not in seen_titles:
                seen_titles.add(clean_title)
                deduped_papers.append(paper)

        return LiteratureSearchResult(
            provider_name="Multi-Source Autonomous Research Engine",
            query=normalized_query,
            request_url="; ".join(request_urls[:3]),
            papers=deduped_papers[:12],
            raw_payload={
                "total_retrieved": len(deduped_papers),
                "sources_breakdown": source_counts,
            },
        )


def _collapse_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def _parse_pubmed_date(value: str | None) -> datetime | None:
    if not value:
        return None
    match = re.search(r"(\d{4})", str(value))
    if match:
        try:
            return datetime(int(match.group(1)), 1, 1, tzinfo=timezone.utc)
        except Exception:
            return None
    return None
