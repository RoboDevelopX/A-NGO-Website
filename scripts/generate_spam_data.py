"""Write the synthetic spam dataset to data/spam_dataset.csv.

Usage: python -m scripts.generate_spam_data [--per-class 600] [--seed 42]
The data is SYNTHETIC: see app/ml/spam_data.py for what that means for the model.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from app.ml.spam_data import generate_dataset

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "spam_dataset.csv"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-class", type=int, default=600)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)

    samples = generate_dataset(args.per_class, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "label", "template_id"])
        for s in samples:
            writer.writerow([s.text, s.label, s.template_id])
    counts = Counter(s.label for s in samples)
    print(
        f"Wrote {len(samples)} synthetic samples ({counts[0]} ham, {counts[1]} spam) to {args.out}"
    )


if __name__ == "__main__":
    main()
