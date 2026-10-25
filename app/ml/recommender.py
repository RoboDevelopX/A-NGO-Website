"""Related-posts recommender: TF-IDF + cosine similarity.

Why this method: with a few dozen posts there is no click data to learn from, so a
content-based method is the only honest option. TF-IDF is fast, needs no GPU or external
API, and its results are explainable (you can print the shared terms).

Limits: it matches *words*, not meaning ("girls' education" and "keeping daughters in
school" only match through shared terms), and it needs at least two posts. Sentence
embeddings would capture meaning better but add a heavy dependency; see the README.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel


@dataclass(frozen=True)
class Document:
    id: int
    title: str
    tags: Sequence[str]
    body: str


def document_text(doc: Document) -> str:
    """Text used for similarity. Title and tags are repeated to weight them more than body
    text: they are short, hand-written summaries of what the post is about."""
    tags = " ".join(t.replace("-", " ") for t in doc.tags)
    return " ".join([doc.title, doc.title, tags, tags, doc.body])


class RelatedPostsRecommender:
    def __init__(self, min_score: float = 0.05, max_features: int = 20_000) -> None:
        self.min_score = min_score
        self.max_features = max_features
        self._ids: list[int] = []
        self._index: dict[int, int] = {}
        self._similarity: np.ndarray | None = None

    def fit(self, docs: Sequence[Document]) -> RelatedPostsRecommender:
        self._ids = [d.id for d in docs]
        self._index = {doc_id: i for i, doc_id in enumerate(self._ids)}
        if len(docs) < 2:
            self._similarity = None
            return self
        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),  # bigrams catch phrases like "teacher fellowship"
            sublinear_tf=True,  # a word used 20 times isn't 20x more relevant
            max_features=self.max_features,
        )
        matrix = vectorizer.fit_transform([document_text(d) for d in docs])
        # Rows are L2-normalised by TfidfVectorizer, so the dot product *is* cosine
        # similarity. A full n x n matrix is fine for hundreds of posts; for many
        # thousands you'd switch to a nearest-neighbour index.
        self._similarity = linear_kernel(matrix)
        return self

    def related(self, doc_id: int, k: int = 3) -> list[tuple[int, float]]:
        """Up to ``k`` (id, score) pairs, most similar first, excluding the post itself."""
        if self._similarity is None or doc_id not in self._index:
            return []
        scores = self._similarity[self._index[doc_id]]
        order = np.argsort(-scores, kind="stable")
        results = []
        for i in order:
            if self._ids[i] == doc_id or scores[i] < self.min_score:
                continue
            results.append((self._ids[i], float(scores[i])))
            if len(results) == k:
                break
        return results
