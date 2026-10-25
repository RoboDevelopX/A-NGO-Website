"""Related-posts recommender (TF-IDF + cosine similarity)."""

from __future__ import annotations

from app.ml.recommender import Document, RelatedPostsRecommender, document_text

DOCS = [
    Document(1, "Reading corners in village schools", ["literacy", "library"],
             "Children borrow storybooks from the library corner and read aloud every morning."),
    Document(2, "Why storybooks matter for early reading", ["literacy"],
             "Storybooks in the mother tongue help children start reading sooner."),
    Document(3, "Our annual accounts, explained", ["transparency", "donors"],
             "Where every rupee went: salaries, materials, audit fees and transport."),
    Document(4, "Library volunteers wanted", ["library", "volunteering"],
             "Help us sort and label storybooks for the library corners."),
]  # fmt: skip


def test_document_text_weights_title_and_tags_and_splits_hyphenated_tags():
    text = document_text(Document(9, "Title", ["girls-education"], "Body"))
    assert text.count("Title") == 2
    assert text.count("girls education") == 2
    assert text.endswith("Body")


def test_related_returns_most_similar_posts_first_and_never_the_post_itself():
    model = RelatedPostsRecommender().fit(DOCS)
    related = model.related(1, k=3)
    ids = [doc_id for doc_id, _ in related]
    assert 1 not in ids
    assert ids[0] in {2, 4}  # the other reading/library posts
    assert 3 not in ids  # the finance post shares no meaningful words
    scores = [score for _, score in related]
    assert scores == sorted(scores, reverse=True)
    assert all(0 < s <= 1 for s in scores)


def test_related_respects_k_and_min_score():
    model = RelatedPostsRecommender(min_score=0.0).fit(DOCS)
    assert len(model.related(1, k=1)) == 1
    strict = RelatedPostsRecommender(min_score=0.99).fit(DOCS)
    assert strict.related(1) == []


def test_unknown_id_and_tiny_corpora_return_nothing():
    model = RelatedPostsRecommender().fit(DOCS)
    assert model.related(999) == []
    assert RelatedPostsRecommender().fit(DOCS[:1]).related(1) == []
    assert RelatedPostsRecommender().fit([]).related(1) == []


def test_results_are_deterministic():
    a = RelatedPostsRecommender().fit(DOCS).related(4)
    b = RelatedPostsRecommender().fit(DOCS).related(4)
    assert a == b
