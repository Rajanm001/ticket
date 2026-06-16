from __future__ import annotations

from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from app.config import settings
from app.data_loader import load_faqs, load_tickets


@dataclass
class RetrievalItem:
    source_id: str
    source_type: str
    score: float
    snippet: str


class Retriever:
    """TF-IDF retrieval over resolved tickets and FAQ/policy entries.

    Why TF-IDF instead of neural embeddings:
      * Deterministic and auditable - the same query always returns the same
        sources, which matters for a grounded, low-hallucination assistant.
      * No model download, no GPU, no native crashes - runs in milliseconds on
        any laptop and stays well within the < 4s latency target.
      * For a small corpus (hundreds of tickets + FAQs) lexical similarity is a
        strong, transparent baseline. The interface below is embedding-ready, so
        a vector backend can be swapped in without changing any caller.
    """

    def __init__(self) -> None:
        tickets = load_tickets()
        faqs = load_faqs()

        self._corpus: list[RetrievalItem] = []
        documents: list[str] = []

        for t in tickets:
            # Ground on the historical body plus how it was actually resolved.
            text = f"{t.get('title', '')} {t.get('body', '')} {t.get('resolution', '')}".strip()
            if not text:
                continue
            self._corpus.append(
                RetrievalItem(
                    source_id=str(t.get("ticket_id", "")),
                    source_type="ticket",
                    score=0.0,
                    snippet=str(t.get("resolution") or t.get("body", ""))[:300],
                )
            )
            documents.append(text)

        for f in faqs:
            text = f"{f.get('title', '')} {f.get('content', '')}".strip()
            if not text:
                continue
            self._corpus.append(
                RetrievalItem(
                    source_id=str(f.get("id", "")),
                    source_type="faq",
                    score=0.0,
                    snippet=str(f.get("content", ""))[:300],
                )
            )
            documents.append(text)

        self._fitted = False
        if documents:
            self._vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
            self._matrix = self._vectorizer.fit_transform(documents)
            self._fitted = True

    def retrieve(self, query: str, top_k: int | None = None) -> list[RetrievalItem]:
        if not self._fitted or not query.strip():
            return []

        k = top_k or settings.retrieval_top_k
        q_vec = self._vectorizer.transform([query])
        sims = linear_kernel(q_vec, self._matrix).flatten()

        ranked = sims.argsort()[::-1][:k]
        results: list[RetrievalItem] = []
        for idx in ranked:
            score = float(sims[int(idx)])
            if score <= 0.0:
                continue
            base = self._corpus[int(idx)]
            results.append(
                RetrievalItem(
                    source_id=base.source_id,
                    source_type=base.source_type,
                    score=round(score, 4),
                    snippet=base.snippet,
                )
            )
        return results


