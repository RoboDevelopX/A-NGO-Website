"""Volunteer-to-event matching rules."""

from __future__ import annotations

from datetime import datetime

import pytest

from app.ml.matching import (
    EventInfo,
    VolunteerProfile,
    availability_fit,
    jaccard,
    match_events,
)

VOCAB = frozenset({"teaching", "mentoring", "library", "digital", "events", "fundraising"})
SATURDAY_MORNING = datetime(2026, 11, 7, 10, 0)
WEDNESDAY_EVENING = datetime(2026, 11, 4, 18, 30)
WEDNESDAY_MORNING = datetime(2026, 11, 4, 9, 0)


def event(id, when, tags, online=False):
    return EventInfo(id, when, frozenset(tags), online)


def test_jaccard():
    assert jaccard(frozenset("ab"), frozenset("ab")) == 1.0
    assert jaccard(frozenset("ab"), frozenset("bc")) == pytest.approx(1 / 3)
    assert jaccard(frozenset(), frozenset("a")) == 0.0


@pytest.mark.parametrize(
    ("availability", "when", "online", "expected"),
    [
        ("weekends", SATURDAY_MORNING, False, 1.0),
        ("weekends", WEDNESDAY_EVENING, False, 0.0),
        ("weekday_evenings", WEDNESDAY_EVENING, False, 1.0),
        ("weekday_evenings", WEDNESDAY_MORNING, False, 0.0),
        ("weekday_daytime", WEDNESDAY_MORNING, False, 1.0),
        ("weekday_daytime", SATURDAY_MORNING, False, 0.0),
        ("remote", SATURDAY_MORNING, True, 1.0),
        ("remote", SATURDAY_MORNING, False, 0.0),
        ("flexible", WEDNESDAY_MORNING, False, 1.0),
        ("not-a-real-value", SATURDAY_MORNING, False, 0.0),
    ],
)
def test_availability_fit(availability, when, online, expected):
    assert availability_fit(availability, when, online) == expected


def test_ranks_by_interest_then_availability_and_explains_why():
    profile = VolunteerProfile(frozenset({"teaching", "library"}), "weekends")
    events = [
        event(1, WEDNESDAY_MORNING, {"teaching", "library", "rajasthan"}),  # perfect interests
        event(2, SATURDAY_MORNING, {"teaching", "events"}),  # partial interests + weekend
        event(3, SATURDAY_MORNING, {"fundraising"}),  # weekend but nothing in common
    ]
    matches = match_events(profile, events, VOCAB, labels={"teaching": "teaching and tutoring"})
    assert [m.event_id for m in matches] == [1, 2]
    assert matches[0].score == pytest.approx(0.7)  # "rajasthan" is outside the vocabulary
    assert matches[1].score == pytest.approx(0.7 / 3 + 0.3, abs=1e-4)  # scores are rounded
    assert matches[0].reasons == ("Matches your interest in library and teaching and tutoring",)
    assert matches[1].reasons[1] == "On a weekend, when you're free"


def test_ties_go_to_the_sooner_event_and_k_is_respected():
    profile = VolunteerProfile(frozenset({"mentoring"}), "flexible")
    events = [
        event(1, datetime(2026, 12, 1, 10), {"mentoring"}),
        event(2, datetime(2026, 11, 1, 10), {"mentoring"}),
        event(3, datetime(2026, 11, 15, 10), {"mentoring"}),
    ]
    assert [m.event_id for m in match_events(profile, events, VOCAB, k=2)] == [2, 3]


def test_no_interests_means_no_suggestions():
    profile = VolunteerProfile(frozenset(), "flexible")
    assert match_events(profile, [event(1, SATURDAY_MORNING, {"teaching"})], VOCAB) == []
