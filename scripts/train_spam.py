"""Train the spam classifier on data/spam_dataset.csv and save it.

Usage: python -m scripts.train_spam [--threshold 0.8]

1. Evaluate on held-out *templates* and print the metrics.
2. Refit on all data and save data/spam_model.joblib (+ .json with the metrics).
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from app.config import get_settings
from app.ml.spam import evaluate, save_model, train
from app.ml.spam_data import Sample

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
    print("Held-out evaluation (unseen templates; synthetic data, so treat as optimistic):")
    print(f"  train={result.n_train} test={result.n_test} threshold={result.threshold}")
    print(f"  precision={result.precision} recall={result.recall} f1={result.f1}")
    print(f"  roc_auc={result.roc_auc}")
    print(f"  confusion: tn={tn} fp={fp} fn={fn} tp={tp}")
    print(f"  held-out templates: {', '.join(result.test_templates)}")
    print("  threshold  precision  recall")
    for t, p, r in result.threshold_table:
        marker = "  <- in use" if t == result.threshold else ""
        print(f"  {t:>9}  {p:>9}  {r:>6}{marker}")

    model = train(samples)
    save_model(model, args.out, result)
    print(f"Saved model to {args.out}")


if __name__ == "__main__":
    main()
