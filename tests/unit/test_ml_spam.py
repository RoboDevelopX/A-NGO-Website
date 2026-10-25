"""Spam classifier: synthetic data, features, training, evaluation and persistence."""

from __future__ import annotations

import json

import numpy as np
import pytest

from app.ml.spam import (
    SpamClassifier,
    TextStatsTransformer,
    build_pipeline,
    evaluate,
    save_model,
    train,
)
from app.ml.spam_data import (
    HAM,
    HAM_TEMPLATES,
    HANDWRITTEN_HAM,
    HANDWRITTEN_SPAM,
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
    features = TextStatsTransformer().fit_transform(
        ["Visit http://x.com URGENT!!! $5, call +1 555 123 4567", "Our CSR team, 2027"]
    )
    names = TextStatsTransformer.feature_names
    assert features.shape == (2, len(names))
    row = dict(zip(names, features[0], strict=True))
    assert row["url_count"] >= 1
    assert row["exclamations"] == 3
    assert row["money_mentions"] == 1
    assert row["shouting_words"] == 1
    assert row["phone_numbers"] == 1
    # Acronyms and years are normal in genuine messages and must not look like spam signals.
    assert not features[1].any()
    assert np.isfinite(features).all()


def test_model_separates_clear_cases(model):
    classifier = SpamClassifier(model)
    assert classifier.score(GENUINE) < 0.2
    assert classifier.score(OBVIOUS_SPAM) > 0.9


def test_handwritten_sanity_messages(model):
    """Messages never used in training, including a false positive found by hand."""
    classifier = SpamClassifier(model)
    for name, message in HANDWRITTEN_HAM:
        assert classifier.score(classifier_text(name, message)) < 0.5, message
    for name, message in HANDWRITTEN_SPAM:
        assert classifier.score(classifier_text(name, message)) > 0.5, message


def test_pipeline_uses_text_stats_only_when_asked():
    default = dict(build_pipeline().named_steps["features"].transformer_list)
    assert set(default) == {"words", "chars"}
    with_stats = dict(build_pipeline(use_text_stats=True).named_steps["features"].transformer_list)
    assert set(with_stats) == {"words", "chars", "stats"}


def test_grouped_cross_validation_scores_every_sample_and_beats_a_floor(samples):
    result = evaluate(samples, threshold=0.65)
    (tn, fp), (fn, tp) = result.confusion
    assert tn + fp + fn + tp == result.n_samples == len(samples)  # every sample scored once
    assert result.n_folds == 4 and result.use_text_stats is False
    # Loose floors: the point is to catch a broken pipeline, not to chase a number.
    assert result.roc_auc > 0.9
    assert result.precision > 0.8
    assert all(0 < rate <= 1 for _, rate in result.hardest_templates)
    thresholds = [t for t, _, _ in result.threshold_table]
    assert thresholds == sorted(thresholds)
    recalls = [r for _, _, r in result.threshold_table]
    assert recalls == sorted(recalls, reverse=True)  # stricter cut-off, lower recall


def test_save_and_load_roundtrip(tmp_path, model, samples):
    path = tmp_path / "model.joblib"
    save_model(model, path, evaluate(samples))
    metadata = json.loads(path.with_suffix(".json").read_text())
    assert "synthetic" in metadata["data"]
    assert metadata["evaluation"]["threshold"] == 0.65

    loaded = SpamClassifier.load(path)
    assert loaded is not None
    assert loaded.score(GENUINE) == pytest.approx(SpamClassifier(model).score(GENUINE))


def test_missing_or_corrupt_model_disables_the_filter(tmp_path):
    assert SpamClassifier.load(tmp_path / "nope.joblib") is None
    corrupt = tmp_path / "corrupt.joblib"
    corrupt.write_bytes(b"not a model")
    assert SpamClassifier.load(corrupt) is None
