"""Glue between the ML helpers in app/ml and the web app.

Each feature is chosen once at startup from its config flag. When a flag is off (or the
spam model file is missing) the app uses a simple non-ML fallback, so no page ever
depends on a model being present.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.db import utcnow
from app.formatting import to_ist
from app.ml.matching import EventInfo, VolunteerProfile, match_events
from app.ml.recommender import Document, RelatedPostsRecommender
from app.ml.spam import SpamClassifier
from app.ml.spam_data import classifier_text
from app.models import Event, Post, Submission
from app.schemas import Interest
from app.services.content import posts_sharing_tags, upcoming_events

logger = logging.getLogger(__name__)

INTEREST_VOCABULARY = frozenset(i.value for i in Interest)
# Short nouns for the "Matches your interest in ..." reasons. The form labels ("Libraries
# and reading") already contain "and", which reads badly once several are joined.
INTEREST_READABLE = {
    Interest.TEACHING.value: "teaching",
    Interest.MENTORING.value: "mentoring",
    Interest.DIGITAL.value: "digital skills",
    Interest.LIBRARY.value: "libraries",
    Interest.EVENTS.value: "events",
    Interest.FUNDRAISING.value: "fundraising",
    Interest.CONTENT.value: "storytelling",
}


# --- (a) Related posts ----------------------------------------------------------


class TfidfRelatedPosts:
    """Callable used as ``app.state.related_posts``. Refits only when the set of
    published posts changes, so a page view normally costs one small query."""

    def __init__(self, k: int = 3) -> None:
        self.k = k
        self._signature: tuple | None = None
        self._model = RelatedPostsRecommender()
        self._lock = threading.Lock()

    def __call__(self, db: Session, post: Post) -> list[Post]:
        rows = db.execute(
            select(Post.id, Post.published_at).where(Post.published_at <= utcnow())
        ).all()
        signature = tuple(sorted((r.id, r.published_at) for r in rows))
        with self._lock:
            if signature != self._signature:
                posts = db.scalars(select(Post).where(Post.id.in_([r.id for r in rows]))).all()
                docs = [Document(p.id, p.title, p.tag_list, p.body) for p in posts]
                self._model.fit(docs)
                self._signature = signature
                logger.info("Related-posts model fitted on %d posts", len(docs))
            ranked = self._model.related(post.id, k=self.k)
        if not ranked:
            return posts_sharing_tags(db, post, self.k)
        by_id = {
            p.id: p for p in db.scalars(select(Post).where(Post.id.in_([i for i, _ in ranked])))
        }
        return [by_id[i] for i, _ in ranked if i in by_id]


# --- (b) Volunteer to event matching --------------------------------------------


@dataclass(frozen=True)
class EventSuggestion:
    event: Event
    score: float
    reasons: tuple[str, ...]


def suggest_events(db: Session, submission: Submission, k: int = 3) -> list[EventSuggestion]:
    events = upcoming_events(db)
    infos = [
        EventInfo(e.id, to_ist(e.starts_at), frozenset(e.tag_list), e.is_online) for e in events
    ]
    profile = VolunteerProfile(frozenset(submission.interest_list), submission.availability or "")
    matches = match_events(profile, infos, INTEREST_VOCABULARY, k=k, labels=INTEREST_READABLE)
    by_id = {e.id: e for e in events}
    return [EventSuggestion(by_id[m.event_id], m.score, m.reasons) for m in matches]


def admin_suggestions(db: Session, items: list[Submission]) -> dict[int, EventSuggestion]:
    """Best event for each volunteer row on the admin page."""
    out = {}
    for item in items:
        if item.kind == "volunteer" and not item.is_spam:
            best = suggest_events(db, item, k=1)
            if best:
                out[item.id] = best[0]
    return out


# --- (c) Spam scoring -----------------------------------------------------------


@dataclass(frozen=True)
class SpamVerdict:
    score: float | None  # None when the classifier is off
    is_spam: bool


class SpamFilter:
    def __init__(self, classifier: SpamClassifier | None, threshold: float) -> None:
        self.classifier = classifier
        self.threshold = threshold

    @property
    def enabled(self) -> bool:
        return self.classifier is not None

    def check(self, name: str, message: str) -> SpamVerdict:
        if self.classifier is None:
            return SpamVerdict(None, False)
        try:
            score = self.classifier.score(classifier_text(name, message))
        except Exception:
            # A broken model must never block a real person from contacting us.
            logger.exception("Spam scoring failed; accepting submission")
            return SpamVerdict(None, False)
        return SpamVerdict(round(score, 4), score >= self.threshold)


def build_spam_filter(settings: Settings) -> SpamFilter:
    classifier = SpamClassifier.load(settings.spam_model_path) if settings.ml_spam_filter else None
    return SpamFilter(classifier, settings.spam_threshold)
