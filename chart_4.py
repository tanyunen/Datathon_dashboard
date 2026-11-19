import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from chart_palette import PALETTE, PARTY_COLORS


PARTY_LABELS = {"B": "Business", "C": "Consumer"}
COLORS = PARTY_COLORS


def main():
    parser = argparse.ArgumentParser(
        description="Generate Dashboard 4 charts from the competition CSV."
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

    sender_counts = {"B": 0, "C": 0}
    amount_values = {"B": [], "C": []}
    pair_counts = {}
    total_rows = 0

    for chunk in pd.read_csv(
        args.csv_path,
        usecols=["ORDERING_TYPE", "BENEFICIARY_TYPE", "USD_AMOUNT"],
        chunksize=args.chunksize,
        low_memory=True,
        encoding="utf-8",
    ):
        total_rows += len(chunk)
        sender = chunk["ORDERING_TYPE"].astype("string").str.strip()
        beneficiary = chunk["BENEFICIARY_TYPE"].astype("string").str.strip()
        amount = pd.to_numeric(chunk["USD_AMOUNT"], errors="coerce")

        for party, count in sender.value_counts().items():
            sender_counts[party] = sender_counts.get(party, 0) + int(count)
        pair_frame = pd.DataFrame({"sender": sender, "beneficiary": beneficiary})
        for pair, count in pair_frame.value_counts(dropna=False).items():
            sender_type, beneficiary_type = pair
            key = (str(sender_type), str(beneficiary_type))
            pair_counts[key] = pair_counts.get(key, 0) + int(count)

        for party in PARTY_LABELS:
            values = amount.loc[sender.eq(party).fillna(False) & amount.notna()]
            if not values.empty:
                amount_values[party].append(values.to_numpy(dtype="float64"))

    parties = ["B", "C"]
    counts = [sender_counts[party] for party in parties]
    medians = [
        float(np.median(np.concatenate(amount_values[party])))
        if amount_values[party]
        else 0.0
        for party in parties
    ]

    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Inter", "Arial", "DejaVu Sans"],
            "axes.edgecolor": "#cbd5e1",
            "axes.linewidth": 0.8,
        }
    )

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), facecolor="#f8fafc")
    for ax in axes:
        ax.set_facecolor("#ffffff")

    bars = axes[0].bar(
        [PARTY_LABELS[party] for party in parties],
        [count / 1_000_000 for count in counts],
        color=[COLORS[party] for party in parties],
        width=0.55,
    )
    axes[0].set_title("Transactions by sender type")
    axes[0].set_ylabel("Records (millions)")
    axes[0].bar_label(bars, labels=[f"{count / 1_000_000:.2f}M" for count in counts], padding=3)
    axes[0].set_ylim(0, max(counts) / 1_000_000 * 1.18)
    axes[0].spines[["top", "right"]].set_visible(False)

    bars = axes[1].bar(
        [PARTY_LABELS[party] for party in parties],
        medians,
        color=[COLORS[party] for party in parties],
        width=0.55,
    )
    axes[1].set_title("Median payment amount")
    axes[1].set_ylabel("Normalized amount (USD)")
    axes[1].bar_label(bars, labels=[f"${value:,.2f}" for value in medians], padding=3)
    axes[1].set_ylim(0, max(medians) * 1.18)
    axes[1].spines[["top", "right"]].set_visible(False)

    fig.suptitle("Sender type: volume and typical payment size", fontweight="bold")
    fig.tight_layout()
    fig.savefig(args.output_dir / "dashboard4_chart1_volume.png", dpi=240, bbox_inches="tight")
    plt.close(fig)

    pair_order = [("B", "C"), ("B", "B"), ("C", "C"), ("C", "B")]
    pair_labels = [f"{a} → {b}" for a, b in pair_order]
    values = [pair_counts.get(pair, 0) for pair in pair_order]
    shares = [value / total_rows * 100 for value in values] if total_rows else [0] * len(values)

    fig, ax = plt.subplots(figsize=(10, 4.5), facecolor="#f8fafc")
    bars = ax.bar(
        pair_labels,
        [value / 1_000_000 for value in values],
        color=[PALETTE[index] for index in range(len(pair_order))],
        width=0.58,
    )
    ax.set_facecolor("#ffffff")
    ax.set_title("Transactions by sender → beneficiary type")
    ax.set_ylabel("Records (millions)")
    ax.bar_label(
        bars,
        labels=[
            f"{value / 1_000_000:.2f}M\n{share:.2f}%"
            for value, share in zip(values, shares)
        ],
        padding=3,
    )
    ax.set_ylim(0, max(values) / 1_000_000 * 1.2)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(args.output_dir / "dashboard4_chart2_pairs.png", dpi=240, bbox_inches="tight")
    plt.close(fig)

    print(f"Scanned {total_rows:,} records.")
    for party, count, median in zip(parties, counts, medians):
        print(
            f"{PARTY_LABELS[party]} sender: {count:,} ({count / total_rows:.2%}); "
            f"median normalized amount ${median:,.2f}"
        )
    for (sender_type, beneficiary_type), value in zip(pair_order, values):
        print(
            f"{sender_type} -> {beneficiary_type}: {value:,} "
            f"({value / total_rows:.2%})"
        )
    print(f"Charts saved to {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
