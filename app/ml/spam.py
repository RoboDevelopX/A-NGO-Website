"""Lightweight spam classifier for contact and volunteer submissions.

Model: logistic regression over three feature groups
  1. word 1-2 gram TF-IDF        ("guaranteed returns", "learning centre")
  2. character 3-5 gram TF-IDF   (robust to typos and obfuscation like "fr33", "c-a-s-i-n-o")
  3. a few hand-made text stats  (links, ALL CAPS, "!!!", currency symbols)

Why logistic regression: it trains in under a second on a laptop, its probabilities are
reasonably calibrated (we threshold them), and its weights can be inspected. This sits
*behind* the honeypot and rate limiter; it is a second layer, not the only defence.

The model only flags. Flagged submissions are still saved (hidden behind the admin's
"Spam" filter) so a false positive never silently loses a real volunteer, and we don't
send confirmation emails to them, so the form can't be used to spam third parties.
"""

from __future__ import annotations

import json
import logging
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import StandardScaler

from app.ml.spam_data import Sample

logger = logging.getLogger(__name__)

_URL_RE = re.compile(r"https?://|www\.|\b[\w-]+\.(?:com|xyz|top|click|biz|info|site|io)\b", re.I)
_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b")
_MONEY_RE = re.compile(r"[$₹€£]|\brs\.?\s?\d|\busd\b", re.I)


class TextStatsTransformer(BaseEstimator, TransformerMixin):
    """Turns raw text into a few numeric signals that TF-IDF can't express directly.

    Defined at module level (not inside a function) so joblib can pickle and reload it.
    """

    feature_names = (
        "url_count",
        "email_count",
        "caps_ratio",
        "exclamations",
        "digit_ratio",
        "money_mentions",
        "log_length",
    )

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        rows = []
        for text in X:
            letters = [c for c in text if c.isalpha()]
            rows.append(
                [
                    len(_URL_RE.findall(text)),
                    len(_EMAIL_RE.findall(text)),
                    sum(c.isupper() for c in letters) / max(1, len(letters)),
                    text.count("!"),
                    sum(c.isdigit() for c in text) / max(1, len(text)),
                    len(_MONEY_RE.findall(text)),
                    math.log1p(len(text)),
                ]
            )
        return np.asarray(rows, dtype=float)


def build_pipeline(seed: int = 42) -> Pipeline:
    features = FeatureUnion(
        [
            ("words", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=2)),
            (
                "chars",
                TfidfVectorizer(
                    analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True, min_df=2
                ),
            ),
            ("stats", Pipeline([("extract", TextStatsTransformer()), ("scale", StandardScaler())])),
        ]
    )
    classifier = LogisticRegression(
        C=2.0, class_weight="balanced", max_iter=2000, random_state=seed
    )
    return Pipeline([("features", features), ("clf", classifier)])


@dataclass(frozen=True)
class Evaluation:
    precision: float
    recall: float
    f1: float
    roc_auc: float
    confusion: list[list[int]]  # [[tn, fp], [fn, tp]]
    n_train: int
    n_test: int
    test_templates: list[str]
    threshold: float
    # (threshold, precision, recall) at a few cut-offs, to show the trade-off we chose.
    threshold_table: list[tuple[float, float, float]]

    def as_dict(self) -> dict:
        return dict(vars(self))


def evaluate(samples: Sequence[Sample], threshold: float = 0.8, seed: int = 42) -> Evaluation:
    """Hold out whole *templates* (not random rows) and report metrics on them.

    A random row split would put near-identical sentences from the same template in both
    train and test and report a meaninglessly perfect score.
    """
    texts = np.array([s.text for s in samples], dtype=object)
    labels = np.array([s.label for s in samples])
    groups = np.array([s.template_id for s in samples])
    splitter = StratifiedGroupKFold(n_splits=4, shuffle=True, random_state=seed)
    train_idx, test_idx = next(splitter.split(texts, labels, groups))

    model = build_pipeline(seed).fit(texts[train_idx], labels[train_idx])
    proba = model.predict_proba(texts[test_idx])[:, 1]
    predicted = (proba >= threshold).astype(int)
    y_true = labels[test_idx]
    table = []
    for t in (0.5, 0.65, 0.8, 0.9):
        p = (proba >= t).astype(int)
        table.append(
            (
                t,
                round(float(precision_score(y_true, p, zero_division=0)), 3),
                round(float(recall_score(y_true, p, zero_division=0)), 3),
            )
        )
    return Evaluation(
        precision=round(float(precision_score(y_true, predicted, zero_division=0)), 3),
        recall=round(float(recall_score(y_true, predicted, zero_division=0)), 3),
        f1=round(float(f1_score(y_true, predicted, zero_division=0)), 3),
        roc_auc=round(float(roc_auc_score(y_true, proba)), 3),
        confusion=confusion_matrix(y_true, predicted, labels=[0, 1]).tolist(),
        n_train=len(train_idx),
        n_test=len(test_idx),
        test_templates=sorted(set(groups[test_idx])),
        threshold=threshold,
        threshold_table=table,
    )


def train(samples: Sequence[Sample], seed: int = 42) -> Pipeline:
    """Fit on *all* samples. Call ``evaluate`` first to get honest held-out numbers."""
    texts = [s.text for s in samples]
    labels = [s.label for s in samples]
    return build_pipeline(seed).fit(texts, labels)


def save_model(model: Pipeline, path: Path, evaluation: Evaluation | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    metadata = {
        "trained_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "sklearn_version": sklearn.__version__,
        "data": "synthetic (app/ml/spam_data.py); not representative of real spam",
        "evaluation": evaluation.as_dict() if evaluation else None,
    }
    path.with_suffix(".json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


class SpamClassifier:
    def __init__(self, model: Pipeline) -> None:
        self.model = model

    @classmethod
    def load(cls, path: Path) -> SpamClassifier | None:
        """Load a trained model, or return None (spam filtering off) if it's unusable.

        Note: joblib files are pickles and can run code when loaded. We only ever load the
        file our own training script wrote, never one uploaded or downloaded at runtime.
        """
        if not path.exists():
            logger.warning("Spam model not found at %s; run `make train`. Filter disabled.", path)
            return None
        meta_path = path.with_suffix(".json")
        if meta_path.exists():
            trained_with = json.loads(meta_path.read_text(encoding="utf-8")).get("sklearn_version")
            if trained_with and trained_with != sklearn.__version__:
                logger.warning(
                    "Spam model was trained with scikit-learn %s but %s is installed; "
                    "retrain with `make train`.",
                    trained_with,
                    sklearn.__version__,
                )
        try:
            return cls(joblib.load(path))
        except Exception:
            logger.exception("Could not load spam model; filter disabled.")
            return None

    def score(self, text: str) -> float:
        """Probability (0 to 1) that ``text`` is spam."""
        return float(self.model.predict_proba([text])[0, 1])
