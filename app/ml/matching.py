"""Volunteer-to-event matching.

Deliberately *not* a trained model. We have no history of which volunteers enjoyed which
events, so anything "learned" would be learned from nothing. A transparent scoring rule:

    score = 0.7 * interest_overlap + 0.3 * availability_fit

* interest_overlap: Jaccard similarity between the volunteer's interests and the event's
  tags, restricted to the shared interest vocabulary (so location tags like "rajasthan"
  don't dilute the score).
* availability_fit: 1 if the event happens when the volunteer said they're free, else 0.

Events must share at least one interest to be suggested at all, and every suggestion comes
with human-readable reasons. Once RSVP and attendance data exist, these hand-set weights
are exactly what a simple learned ranker would replace.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime

WEIGHT_INTERESTS = 0.7
WEIGHT_AVAILABILITY = 0.3
EVENING_STARTS_AT = 17  # 5 PM local time


@dataclass(frozen=True)
class VolunteerProfile:
    interests: frozenset[str]
    availability: str  # one of app.schemas.Availability values


@dataclass(frozen=True)
class EventInfo:
    id: int
    starts_at_local: datetime  # in the venue's time zone (IST)
    tags: frozenset[str]
    is_online: bool


@dataclass(frozen=True)
class Match:
    event_id: int
    score: float
    reasons: tuple[str, ...]


def jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def availability_fit(availability: str, starts_at_local: datetime, is_online: bool) -> float:
    is_weekend = starts_at_local.weekday() >= 5
    is_evening = starts_at_local.hour >= EVENING_STARTS_AT
    rules = {
        "flexible": True,
        "remote": is_online,
        "weekends": is_weekend,
        "weekday_evenings": not is_weekend and is_evening,
        "weekday_daytime": not is_weekend and not is_evening,
    }
    return 1.0 if rules.get(availability, False) else 0.0


_AVAILABILITY_REASONS = {
    "flexible": "Fits your flexible schedule",
    "remote": "Online, so you can join remotely",
    "weekends": "On a weekend, when you're free",
    "weekday_evenings": "On a weekday evening, when you're free",
    "weekday_daytime": "During the weekday daytime, when you're free",
}


def _join_words(words: list[str]) -> str:
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1]


def match_events(
    profile: VolunteerProfile,
    events: Iterable[EventInfo],
    vocabulary: frozenset[str],
    k: int = 3,
    labels: Mapping[str, str] | None = None,
) -> list[Match]:
    """Rank upcoming events for a volunteer.

    ``vocabulary`` is the set of interest keys; ``labels`` maps keys to readable names
    for the reasons ("teaching" -> "teaching and tutoring").
    """
    labels = labels or {}
    interests = profile.interests & vocabulary
    candidates: list[tuple[float, datetime, Match]] = []
    for event in events:
        event_interests = event.tags & vocabulary
        overlap = jaccard(interests, event_interests)
        if overlap == 0:
            continue  # nothing in common: never suggest it, however convenient the time
        fit = availability_fit(profile.availability, event.starts_at_local, event.is_online)
        score = round(WEIGHT_INTERESTS * overlap + WEIGHT_AVAILABILITY * fit, 4)
        shared = [labels.get(i, i) for i in sorted(interests & event_interests)]
        reasons = [f"Matches your interest in {_join_words(shared)}"]
        if fit:
            reasons.append(_AVAILABILITY_REASONS[profile.availability])
        candidates.append((score, event.starts_at_local, Match(event.id, score, tuple(reasons))))
    # Highest score first; ties go to the sooner event.
    candidates.sort(key=lambda c: (-c[0], c[1]))
    return [m for _, _, m in candidates[:k]]
