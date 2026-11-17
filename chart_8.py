import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from chart_palette import ANOMALY_COLORS, SLATE


ANOMALY_LABELS = {
    "ROMANCE_SCAM": "Romance scam",
    "FAT_FINGER_MISTAKE": "Fat-finger mistake",
    "CEO_SCAM": "CEO scam",
    "DUPLICATE_PAYMENT": "Duplicate payment",
    "ACCOUNT_REPLACEMENT_SCAM": "Account replacement",
    "CUSTOMER_RECALL": "Customer recall",
}

COLORS = ANOMALY_COLORS


def main():
    parser = argparse.ArgumentParser(
        description="Build evidence-based anomaly charts from the competition CSV."
    )
    parser.add_argument("csv_path", type=Path, help="Path to the competition CSV file")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Directory for generated PNGs (default: this script's directory)",
    )
    parser.add_argument("--chunksize", type=int, default=500_000)
    args = parser.parse_args()

    if not args.csv_path.is_file():
        parser.error(f"CSV file not found: {args.csv_path}")
    if args.chunksize < 1:
        parser.error("--chunksize must be a positive integer")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    counts = {label: 0 for label in ANOMALY_LABELS}
    amount_values = {label: [] for label in ANOMALY_LABELS}
    other_amount_values = []
    total_rows = 0

    for chunk in pd.read_csv(
        args.csv_path,
        usecols=["ANOMALY_TYPE", "USD_AMOUNT"],
        dtype={"ANOMALY_TYPE": "string"},
        chunksize=args.chunksize,
        low_memory=True,
        encoding="utf-8",
    ):
        total_rows += len(chunk)
        anomaly = chunk["ANOMALY_TYPE"].astype("string").str.strip()
        amount = pd.to_numeric(chunk["USD_AMOUNT"], errors="coerce")

        for label in ANOMALY_LABELS:
            mask = anomaly.eq(label).fillna(False)
            counts[label] += int(mask.sum())
            valid_amounts = amount.loc[mask & amount.notna()]
            if not valid_amounts.empty:
                amount_values[label].append(valid_amounts.to_numpy(dtype="float64"))
        other_mask = ~anomaly.isin(ANOMALY_LABELS)
        other_amounts = amount.loc[other_mask & amount.notna()]
        if not other_amounts.empty:
            other_amount_values.append(other_amounts.to_numpy(dtype="float64"))

    labels = [label for label in ANOMALY_LABELS if counts[label] > 0]
    names = [ANOMALY_LABELS[label] for label in labels]
    color_list = [COLORS[label] for label in labels]
    frequencies = [counts[label] for label in labels]
    medians = [
        float(np.median(np.concatenate(amount_values[label])))
        if amount_values[label]
        else 0.0
        for label in labels
    ]
    other_median = (
        float(np.median(np.concatenate(other_amount_values)))
        if other_amount_values
        else 0.0
    )

    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Inter", "Arial", "DejaVu Sans"],
            "axes.titleweight": "bold",
        }
    )

    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=220)
    y = np.arange(len(labels))
    bars = ax.barh(y, frequencies, color=color_list, height=0.62)
    ax.set_yticks(y, names)
    ax.invert_yaxis()
    ax.set_xlabel("Labelled records (count)")
    ax.set_title("Observed anomaly-label frequency")
    ax.grid(axis="x", linestyle="--", alpha=0.35)
    ax.set_axisbelow(True)
    ax.bar_label(bars, labels=[f"{value:,}" for value in frequencies], padding=4)
    ax.spines[["top", "right", "left"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(args.output_dir / "dashboard8_chart1_anomalies.png", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=220)
    bars = ax.bar(names, medians, color=color_list, width=0.62)
    ax.axhline(
        other_median,
        color=SLATE,
        linestyle="--",
        linewidth=1.5,
        label=f"Baseline: records without these labels (${other_median:,.0f})",
    )
    ax.set_ylabel("Median normalized payment amount (USD)")
    ax.set_title("Anomaly-labelled medians vs unlabelled-record baseline")
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.set_axisbelow(True)
    ax.bar_label(bars, labels=[f"${value:,.0f}" for value in medians], padding=4)
    ax.tick_params(axis="x", rotation=18)
    ax.legend(frameon=False, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(args.output_dir / "dashboard8_chart2_exposure.png", bbox_inches="tight")
    plt.close(fig)

    print(f"Scanned {total_rows:,} records.")
    print("Amounts are normalized USD values, not measured losses or capital at risk.")
    print(
        "Baseline median for records without the six displayed anomaly labels: "
        f"${other_median:,.2f}"
    )
    print("Anomaly label | Count | Share of all records | Median USD amount")
    for label, count, median in zip(labels, frequencies, medians):
        share = count / total_rows * 100 if total_rows else 0
        print(f"{label} | {count:,} | {share:.4f}% | ${median:,.2f}")
    print(f"Charts saved to {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
