"""Lightweight spam classifier for contact and volunteer submissions.

Model: logistic regression over two TF-IDF feature groups
  1. word 1-2 grams        ("guaranteed returns", "learning centre")
  2. character 3-5 grams   (robust to typos and obfuscation like "fr33", "c-a-s-i-n-o", and
                            picks up link fragments such as "http" and ".xyz" by itself)

An optional third group of hand-made text statistics (links, SHOUTING, "!!!", phone
numbers, prices) is kept for comparison but switched off: on templates the model had not
seen, it made genuine messages with a LinkedIn link, a phone number or a price look like
spam. ``scripts/train_spam.py`` prints both variants so the choice can be re-checked.

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
# Words of 5+ letters in capitals ("URGENT", "CONGRATULATIONS"). Short acronyms such as
# CSR, NGO or NSS are normal in genuine messages, so they don't count.
_SHOUTING_RE = re.compile(r"\b[A-Z]{5,}\b")
# Phone-number-like runs: 8+ digits, allowing spaces, dashes and a leading "+".
_PHONE_RE = re.compile(r"\+?\d[\d\s-]{6,}\d")


class TextStatsTransformer(BaseEstimator, TransformerMixin):
    """Turns raw text into a few numeric signals that TF-IDF can't express directly.

    Defined at module level (not inside a function) so joblib can pickle and reload it.

    An earlier version also used message length, the share of capital letters and the share
    of digits. On the synthetic data they looked useful, but they flagged short genuine
    messages such as "Our company would like to discuss CSR in 2027." (a capitalised name,
    an acronym and a year) as spam. Each feature here has to describe *behaviour* (links,
    shouting, phone numbers, prices), not a side effect of how the templates were written.
    """

    feature_names = (
        "url_count",
        "email_count",
        "shouting_words",
        "exclamations",
        "phone_numbers",
        "money_mentions",
    )

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        rows = [
            [
                len(_URL_RE.findall(text)),
                len(_EMAIL_RE.findall(text)),
                len(_SHOUTING_RE.findall(text)),
                text.count("!"),
                len(_PHONE_RE.findall(text)),
                len(_MONEY_RE.findall(text)),
            ]
            for text in X
        ]
        return np.asarray(rows, dtype=float)


def build_pipeline(seed: int = 42, use_text_stats: bool = False) -> Pipeline:
    groups = [
        ("words", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=2)),
        (
            "chars",
            TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True, min_df=2),
        ),
    ]
    if use_text_stats:
        stats = Pipeline([("extract", TextStatsTransformer()), ("scale", StandardScaler())])
        groups.append(("stats", stats))
    # C=8 is fairly weak regularisation. TF-IDF values are small, and with a stronger
    # penalty every probability bunches up near 0.5, which makes thresholding meaningless.
    classifier = LogisticRegression(
        C=8.0, class_weight="balanced", max_iter=2000, random_state=seed
    )
    return Pipeline([("features", FeatureUnion(groups)), ("clf", classifier)])


THRESHOLDS_TO_REPORT = (0.5, 0.65, 0.8, 0.9)


@dataclass(frozen=True)
class Evaluation:
    precision: float
    recall: float
    f1: float
    roc_auc: float
    confusion: list[list[int]]  # [[tn, fp], [fn, tp]]
    n_samples: int
    n_folds: int
    threshold: float
    # (threshold, precision, recall) at a few cut-offs, to show the trade-off we chose.
    threshold_table: list[tuple[float, float, float]]
    # Templates the model gets wrong most often when it hasn't seen them: (id, error rate).
    hardest_templates: list[tuple[str, float]]
    use_text_stats: bool

    def as_dict(self) -> dict:
        return dict(vars(self))


def _rounded(value: float) -> float:
    return round(float(value), 3)


def evaluate(
    samples: Sequence[Sample],
    threshold: float = 0.65,
    seed: int = 42,
    n_folds: int = 4,
    use_text_stats: bool = False,
) -> Evaluation:
    """Grouped cross-validation: every *template* is held out exactly once.

    A random row split would put near-identical sentences from the same template in both
    train and test and report a meaninglessly perfect score. Here each sample is scored by
    a model that never saw any sentence from its template, and the metrics are computed
    over all of those out-of-fold scores together.
    """
    texts = np.array([s.text for s in samples], dtype=object)
    labels = np.array([s.label for s in samples])
    groups = np.array([s.template_id for s in samples])
    splitter = StratifiedGroupKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    proba = np.zeros(len(samples))
    for train_idx, test_idx in splitter.split(texts, labels, groups):
        model = build_pipeline(seed, use_text_stats).fit(texts[train_idx], labels[train_idx])
        proba[test_idx] = model.predict_proba(texts[test_idx])[:, 1]

    predicted = (proba >= threshold).astype(int)
    table = []
    for t in THRESHOLDS_TO_REPORT:
        p = (proba >= t).astype(int)
        table.append(
            (
                t,
                _rounded(precision_score(labels, p, zero_division=0)),
                _rounded(recall_score(labels, p, zero_division=0)),
            )
        )
    wrong = predicted != labels
    error_rates = [(t, _rounded(wrong[groups == t].mean())) for t in sorted(set(groups))]
    hardest = sorted((r for r in error_rates if r[1] > 0), key=lambda r: -r[1])[:5]
    return Evaluation(
        precision=_rounded(precision_score(labels, predicted, zero_division=0)),
        recall=_rounded(recall_score(labels, predicted, zero_division=0)),
        f1=_rounded(f1_score(labels, predicted, zero_division=0)),
        roc_auc=_rounded(roc_auc_score(labels, proba)),
        confusion=confusion_matrix(labels, predicted, labels=[0, 1]).tolist(),
        n_samples=len(samples),
        n_folds=n_folds,
        threshold=threshold,
        threshold_table=table,
        hardest_templates=hardest,
        use_text_stats=use_text_stats,
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
