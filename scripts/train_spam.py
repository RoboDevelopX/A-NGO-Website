"""Train the spam classifier on data/spam_dataset.csv and save it.

Usage: python -m scripts.train_spam [--threshold 0.8]

1. Grouped cross-validation (each template held out once); print the metrics.
2. Print the same metrics with the optional text-statistics features, for comparison.
3. Refit on all data, print hand-written sanity checks, and save
   data/spam_model.joblib (+ .json with the metrics).
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from app.config import get_settings
from app.ml.spam import SpamClassifier, evaluate, save_model, train
from app.ml.spam_data import HANDWRITTEN_HAM, HANDWRITTEN_SPAM, Sample, classifier_text

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "spam_dataset.csv"


def load_samples(path: Path) -> list[Sample]:
    with path.open(encoding="utf-8") as f:
        return [Sample(r["text"], int(r["label"]), r["template_id"]) for r in csv.DictReader(f)]


def main(argv: list[str] | None = None) -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA)
    parser.add_argument("--out", type=Path, default=settings.spam_model_path)
    parser.add_argument("--threshold", type=float, default=settings.spam_threshold)
    args = parser.parse_args(argv)

    if not args.data.exists():
        raise SystemExit(f"{args.data} not found. Run `python -m scripts.generate_spam_data`.")
    samples = load_samples(args.data)
    result = evaluate(samples, threshold=args.threshold)
    (tn, fp), (fn, tp) = result.confusion
    print(f"Grouped {result.n_folds}-fold cross-validation on {result.n_samples} synthetic samples")
    print("(every template scored by a model that never saw it; still optimistic):")
    print(f"  precision={result.precision} recall={result.recall} f1={result.f1}")
    print(f"  roc_auc={result.roc_auc}  confusion: tn={tn} fp={fp} fn={fn} tp={tp}")
    print("  threshold  precision  recall")
    for t, p, r in result.threshold_table:
        marker = "  <- in use" if t == result.threshold else ""
        print(f"  {t:>9}  {p:>9}  {r:>6}{marker}")
    hardest = ", ".join(f"{t} ({rate:.0%})" for t, rate in result.hardest_templates)
    print(f"  hardest unseen templates: {hardest or 'none'}")

    with_stats = evaluate(samples, threshold=args.threshold, use_text_stats=True)
    print("Comparison with the hand-made text statistics switched on:")
    print(
        f"  precision={with_stats.precision} recall={with_stats.recall} "
        f"roc_auc={with_stats.roc_auc}"
    )

    model = train(samples)
    classifier = SpamClassifier(model)
    print("Hand-written sanity checks (never trained on):")
    for label, examples in (("ham ", HANDWRITTEN_HAM), ("spam", HANDWRITTEN_SPAM)):
        for name, message in examples:
            score = classifier.score(classifier_text(name, message))
            print(f"  {label} {score:.3f}  {message[:70]}")
    save_model(model, args.out, result)
    print(f"Saved model to {args.out}")


if __name__ == "__main__":
    main()
