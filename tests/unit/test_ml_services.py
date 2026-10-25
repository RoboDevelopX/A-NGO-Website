"""The glue in app/services/ml.py: fallbacks, refitting and failure handling."""

from __future__ import annotations

from datetime import timedelta

from app.config import Settings
from app.db import utcnow
from app.models import Post
from app.services.ml import SpamFilter, TfidfRelatedPosts, build_spam_filter


class FakeClassifier:
    def __init__(self, score):
        self._score = score
        self.seen = []

    def score(self, text):
        self.seen.append(text)
        return self._score


class BrokenClassifier:
    def score(self, text):
        raise RuntimeError("model exploded")


def test_spam_filter_applies_threshold_and_scores_name_with_message():
    classifier = FakeClassifier(0.85)
    verdict = SpamFilter(classifier, threshold=0.8).check("Name", "Message")
    assert verdict.is_spam and verdict.score == 0.85
    assert classifier.seen == ["Name\nMessage"]
    assert not SpamFilter(FakeClassifier(0.79), threshold=0.8).check("a", "b").is_spam


def test_disabled_or_broken_filter_accepts_everything():
    off = SpamFilter(None, threshold=0.8)
    assert not off.enabled
    assert off.check("a", "b").is_spam is False and off.check("a", "b").score is None
    broken = SpamFilter(BrokenClassifier(), threshold=0.8).check("a", "b")
    assert broken.is_spam is False and broken.score is None


def test_build_spam_filter_respects_the_flag_and_a_missing_file(tmp_path):
    base = {"_env_file": None, "spam_model_path": tmp_path / "missing.joblib"}
    assert not build_spam_filter(Settings(**base, ml_spam_filter=True)).enabled
    assert not build_spam_filter(Settings(**base, ml_spam_filter=False)).enabled


def _post(slug, title, tags, body, days_ago=1):
    return Post(
        slug=slug,
        title=title,
        excerpt=title,
        body=body,
        tags=",".join(tags),
        author="Test",
        published_at=utcnow() - timedelta(days=days_ago),
    )


def test_tfidf_related_posts_refits_when_posts_change(db_session):
    reading = _post("reading", "Reading corners", ["literacy"], "Storybooks and reading aloud.")
    stories = _post("stories", "Storybooks for reading", ["literacy"], "Reading storybooks daily.")
    accounts = _post("accounts", "Annual accounts", ["donors"], "Audit fees and salaries.")
    db_session.add_all([reading, stories, accounts])
    db_session.commit()

    related = TfidfRelatedPosts(k=2)
    assert related(db_session, reading)[0].slug == "stories"
    first_signature = related._signature

    newer = _post("library", "Reading and storybooks", ["literacy"], "Reading corners, storybooks.")
    db_session.add(newer)
    db_session.commit()
    assert "library" in {p.slug for p in related(db_session, reading)}
    assert related._signature != first_signature


def test_tfidf_related_posts_ignores_unpublished_posts(db_session):
    live = _post("live", "Reading corners", ["literacy"], "Storybooks and reading aloud.")
    scheduled = _post("draft", "Reading corners", ["literacy"], "Storybooks.", days_ago=-5)
    db_session.add_all([live, scheduled])
    db_session.commit()
    # Only one published post: the model has nothing to compare, so we fall back to tags,
    # which also only consider published posts.
    assert TfidfRelatedPosts()(db_session, live) == []
