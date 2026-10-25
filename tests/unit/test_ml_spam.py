"""Spam classifier: synthetic data, features, training, evaluation and persistence."""

from __future__ import annotations

import json

import numpy as np
import pytest

from app.ml.spam import SpamClassifier, TextStatsTransformer, evaluate, save_model, train
from app.ml.spam_data import (
    HAM,
    HAM_TEMPLATES,
    SPAM,
    SPAM_TEMPLATES,
    classifier_text,
    generate_dataset,
)

GENUINE = classifier_text(
    "Priya Sharma", "I teach maths at a school in Jaipur and would love to help on Saturdays."
)
OBVIOUS_SPAM = classifier_text(
    "SEO Expert",
    "Buy backlinks cheap!! 10,000 for just $5. Fast delivery. http://rank1-google.info",
)


@pytest.fixture(scope="module")
def samples():
    return generate_dataset(n_per_class=300, seed=7)


@pytest.fixture(scope="module")
def model(samples):
    return train(samples)


def test_dataset_is_balanced_deterministic_and_covers_every_template(samples):
    labels = [s.label for s in samples]
    assert labels.count(HAM) == labels.count(SPAM) == 300
    assert generate_dataset(50, seed=1) == generate_dataset(50, seed=1)
    assert generate_dataset(50, seed=1) != generate_dataset(50, seed=2)
    templates = {s.template_id for s in samples}
    assert set(HAM_TEMPLATES) | set(SPAM_TEMPLATES) == templates
    assert all("{" not in s.text for s in samples)  # every placeholder was filled


def test_classifier_text_is_name_then_message():
    assert classifier_text("A", "b") == "A\nb"


def test_text_stats_features():
    features = TextStatsTransformer().fit_transform(["Visit http://x.com NOW!!! $5", "hello there"])
    names = TextStatsTransformer.feature_names
    assert features.shape == (2, len(names))
    row = dict(zip(names, features[0], strict=True))
    assert row["url_count"] >= 1
    assert row["exclamations"] == 3
    assert row["money_mentions"] == 1
    assert row["caps_ratio"] > 0
    assert dict(zip(names, features[1], strict=True))["url_count"] == 0
    assert np.isfinite(features).all()


def test_model_separates_clear_cases(model):
    classifier = SpamClassifier(model)
    assert classifier.score(GENUINE) < 0.2
    assert classifier.score(OBVIOUS_SPAM) > 0.9


def test_evaluation_holds_out_whole_templates_and_beats_a_floor(samples):
    result = evaluate(samples, threshold=0.8)
    assert result.n_train + result.n_test == len(samples)
    assert result.test_templates  # some templates never seen in training
    # Loose floors: the point is to catch a broken pipeline, not to chase a number.
    assert result.roc_auc > 0.85
    assert result.precision > 0.75
    thresholds = [t for t, _, _ in result.threshold_table]
    assert thresholds == sorted(thresholds)
    recalls = [r for _, _, r in result.threshold_table]
    assert recalls == sorted(recalls, reverse=True)  # stricter cut-off, lower recall


def test_save_and_load_roundtrip(tmp_path, model, samples):
    path = tmp_path / "model.joblib"
    save_model(model, path, evaluate(samples))
    metadata = json.loads(path.with_suffix(".json").read_text())
    assert "synthetic" in metadata["data"]
    assert metadata["evaluation"]["threshold"] == 0.8

    loaded = SpamClassifier.load(path)
    assert loaded is not None
    assert loaded.score(GENUINE) == pytest.approx(SpamClassifier(model).score(GENUINE))


def test_missing_or_corrupt_model_disables_the_filter(tmp_path):
    assert SpamClassifier.load(tmp_path / "nope.joblib") is None
    corrupt = tmp_path / "corrupt.joblib"
    corrupt.write_bytes(b"not a model")
    assert SpamClassifier.load(corrupt) is None
