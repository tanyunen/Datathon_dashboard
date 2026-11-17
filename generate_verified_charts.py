import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from chart_palette import (
    CONTINUITY_COLORS,
    BLUE,
    FOREST,
    GREEN,
    SLATE,
    TYPE_COLORS,
)


REQUIRED_COLUMNS = [
    "CONTINUITY_QFLAG",
    "EPOCH_SECONDS",
    "PARTICIPANT_COUNT",
    "TOTAL_DURATION",
    "TRANSACTION_TYPE_CODE",
    "USD_AMOUNT",
]
TYPE_ORDER = ["Direct", "Indirect", "Covered"]
FLAG_ORDER = ["Y", "N"]
WEEKDAY_ORDER = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
def add_value_summaries(values, groups, sums, counts):
    frame = pd.DataFrame({"group": groups, "value": values}).dropna()
    grouped = frame.groupby("group", observed=True)["value"].agg(["sum", "count"])
    for key, row in grouped.iterrows():
        label = str(int(key)) if isinstance(key, (int, float, np.integer, np.floating)) else str(key)
        sums[label] += float(row["sum"])
        counts[label] += int(row["count"])


def plot_style():
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Inter", "Arial", "DejaVu Sans"],
            "axes.edgecolor": "#cbd5e1",
            "axes.linewidth": 0.8,
            "axes.titleweight": "bold",
        }
    )


def save_route_charts(output_dir, participant_counts, duration_sums, duration_counts):
    duration_participants = list(range(2, 15))
    means = [
        duration_sums[str(n)] / duration_counts[str(n)]
        if duration_counts[str(n)]
        else np.nan
        for n in duration_participants
    ]

    fig, ax = plt.subplots(figsize=(10, 4.7), facecolor="white")
    ax.plot(duration_participants, means, marker="o", color=FOREST, linewidth=2.5)
    if np.isfinite(means[0]):
        ax.axhline(
            means[0],
            color=SLATE,
            linestyle="--",
            linewidth=1.5,
            label=f"Baseline: 2 participants ({means[0]:.0f}s)",
        )
        ax.legend(frameon=False, loc="upper left")
    ax.set_title("Mean observed duration by participant count (2–14)")
    ax.set_xlabel("Participants in route")
    ax.set_ylabel("Mean TOTAL_DURATION (seconds)")
    ax.set_xticks(duration_participants)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.set_axisbelow(True)
    for x, y in zip(duration_participants, means):
        n = participant_counts.get(str(x), 0)
        if n < 10_000 and np.isfinite(y):
            ax.annotate(f"n={n:,}", (x, y), xytext=(0, 8), textcoords="offset points", ha="center", fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_dir / "dashboard_routing_styled.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    participants = sorted(int(value) for value in participant_counts)
    counts = [participant_counts[str(n)] for n in participants]
    fig, ax = plt.subplots(figsize=(10, 4.7), facecolor="white")
    bars = ax.bar(participants, counts, color=GREEN, width=0.72)
    ax.set_title("Record count by participant count (all observed groups)")
    ax.set_xlabel("Participants in route")
    ax.set_ylabel("Records (log scale)")
    ax.set_xticks(participants)
    ax.set_yscale("log")
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.set_axisbelow(True)
    for bar, count in zip(bars, counts):
        if count and count <= 100:
            ax.annotate(
                f"{count:,}",
                (bar.get_x() + bar.get_width() / 2, count),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                fontsize=7,
                rotation=90,
            )
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_dir / "dashboard_distribution_styled.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def save_type_charts(output_dir, type_counts, type_flags):
    labels = [value for value in TYPE_ORDER if type_counts.get(value, 0)]
    values = [type_counts[value] for value in labels]

    fig, ax = plt.subplots(figsize=(10, 4.7), facecolor="white")
    bars = ax.bar(labels, values, color=[TYPE_COLORS[label] for label in labels])
    ax.set_title("Payment records by transaction type")
    ax.set_ylabel("Records")
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.set_axisbelow(True)
    ax.bar_label(bars, labels=[f"{value:,}" for value in values], padding=3)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_dir / "dashboard2_chart1_transaction_types.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.7), facecolor="white")
    incomplete_shares = []
    for label in labels:
        counts = type_flags[label]
        total = sum(counts.values())
        incomplete_shares.append(counts.get("N", 0) / total * 100 if total else 0)
    x = np.arange(len(labels))
    bars = ax.bar(x, incomplete_shares, color=[TYPE_COLORS[label] for label in labels])
    sample_labels = [
        f"{label}\nn={sum(type_flags[label].values()):,}"
        for label in labels
    ]
    ax.set_xticks(x, sample_labels)
    ax.set_ylabel("Incomplete path (N) within type (%)")
    ax.set_title("Incomplete-path rate by type vs Direct baseline")
    ax.bar_label(bars, labels=[f"{value:.2f}%" for value in incomplete_shares], padding=3)
    if "Direct" in labels:
        baseline = incomplete_shares[labels.index("Direct")]
        ax.axhline(
            baseline,
            color=SLATE,
            linestyle="--",
            linewidth=1.5,
            label=f"Direct baseline ({baseline:.2f}%)",
        )
        ax.legend(frameon=False, loc="upper left")
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_dir / "dashboard2_chart2_continuity.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def save_route_observability_charts(
    output_dir, participant_counts, participant_flags, continuity_duration_sums, continuity_duration_counts
):
    participants = list(range(2, 23))
    incomplete_share = []
    sample_sizes = []
    for participant_count in participants:
        counts = participant_flags.get(str(participant_count), {})
        total = sum(counts.values())
        sample_sizes.append(total)
        incomplete_share.append(counts.get("N", 0) / total * 100 if total else np.nan)

    fig, ax = plt.subplots(figsize=(10, 4.7), facecolor="white")
    bars = ax.bar(participants, incomplete_share, color=GREEN, width=0.72)
    ax.set_title("Incomplete or discontinuous path share by participant count")
    ax.set_xlabel("Participants in route")
    ax.set_ylabel("CONTINUITY_QFLAG = N (%)")
    ax.set_xticks(participants)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.set_axisbelow(True)
    if incomplete_share and np.isfinite(incomplete_share[0]):
        ax.axhline(
            incomplete_share[0],
            color=SLATE,
            linestyle="--",
            linewidth=1.3,
            label=f"Baseline: 2 participants ({incomplete_share[0]:.2f}%)",
        )
        ax.legend(frameon=False, loc="upper left")
    for x, bar, n in zip(participants, bars, sample_sizes):
        if n <= 1_000 and n:
            ax.annotate(
                f"n={n:,}",
                (x, bar.get_height()),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                fontsize=7,
                rotation=90,
            )
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_dir / "dashboard3_chart1_corridors.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    flags = [flag for flag in FLAG_ORDER if continuity_duration_counts.get(flag, 0)]
    means = [
        continuity_duration_sums[flag] / continuity_duration_counts[flag]
        for flag in flags
    ]
    samples = [continuity_duration_counts[flag] for flag in flags]
    fig, ax = plt.subplots(figsize=(10, 4.7), facecolor="white")
    bars = ax.bar(
        ["Continuous path (Y)" if flag == "Y" else "Incomplete path (N)" for flag in flags],
        means,
        color=[CONTINUITY_COLORS[flag] for flag in flags],
    )
    ax.set_title("Mean observed duration by path-continuity flag")
    ax.set_ylabel("Mean TOTAL_DURATION (seconds)")
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.set_axisbelow(True)
    ax.bar_label(
        bars,
        labels=[f"{mean:,.0f}s\nn={sample:,}" for mean, sample in zip(means, samples)],
        padding=3,
    )
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_dir / "dashboard3_chart2_continuity_duration.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def save_temporal_chart(
    output_dir, hourly_counts, weekday_counts, hourly_amount_sums, hourly_amount_counts, hourly_duration_sums, hourly_duration_counts
):
    hours = list(range(24))
    weekdays = WEEKDAY_ORDER
    fig, axes = plt.subplots(2, 2, figsize=(13, 8), facecolor="white")

    axes[0, 0].bar(hours, [hourly_counts.get(hour, 0) for hour in hours], color=GREEN)
    average_hourly = sum(hourly_counts.values()) / 24
    axes[0, 0].axhline(
        average_hourly,
        color=SLATE,
        linestyle="--",
        linewidth=1.3,
        label=f"Uniform-hour baseline ({average_hourly:,.0f})",
    )
    axes[0, 0].legend(frameon=False, fontsize=8)
    axes[0, 0].set_title("Hourly records vs uniform-hour baseline")
    axes[0, 0].set_xlabel("Hour of day")
    axes[0, 0].set_ylabel("Records")

    axes[0, 1].bar(
        weekdays,
        [weekday_counts.get(day, 0) for day in weekdays],
        color=[GREEN] * 5 + [BLUE, BLUE],
    )
    average_daily = sum(weekday_counts.values()) / 7
    axes[0, 1].axhline(
        average_daily,
        color=SLATE,
        linestyle="--",
        linewidth=1.3,
        label=f"Uniform-day baseline ({average_daily:,.0f})",
    )
    axes[0, 1].legend(frameon=False, fontsize=8)
    axes[0, 1].set_title("Daily records vs uniform-day baseline")
    axes[0, 1].tick_params(axis="x", rotation=25)
    axes[0, 1].set_ylabel("Records")

    hourly_means = [
        hourly_amount_sums[str(hour)] / hourly_amount_counts[str(hour)]
        if hourly_amount_counts[str(hour)]
        else np.nan
        for hour in hours
    ]
    axes[1, 0].plot(hours, hourly_means, marker="o", color=GREEN)
    axes[1, 0].set_title("Mean normalized payment amount by hour")
    axes[1, 0].set_xlabel("Hour of day")
    axes[1, 0].set_ylabel("Mean USD amount")

    duration_means = [
        hourly_duration_sums[str(hour)] / hourly_duration_counts[str(hour)]
        if hourly_duration_counts[str(hour)]
        else np.nan
        for hour in hours
    ]
    axes[1, 1].plot(hours, duration_means, marker="o", color=BLUE)
    axes[1, 1].set_title("Mean observed duration by hour")
    axes[1, 1].set_xlabel("Hour of day")
    axes[1, 1].set_ylabel("Mean seconds")

    for ax in axes.flat:
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Temporal patterns in the synthetic payment dataset", fontweight="bold")
    fig.tight_layout()
    output_dir.joinpath("dashboard11").mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / "dashboard11" / "dashboard11_charts.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(
        description="Rebuild data-backed charts for Dashboards 1, 2, 3, and 11."
    )
    parser.add_argument("csv_path", type=Path, help="Path to the competition CSV file")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Project root for generated chart images",
    )
    parser.add_argument("--chunksize", type=int, default=500_000)
    parser.add_argument(
        "--timezone",
        default="Asia/Kuala_Lumpur",
        help="Timezone for Dashboard 11 (default: Asia/Kuala_Lumpur)",
    )
    args = parser.parse_args()

    if not args.csv_path.is_file():
        parser.error(f"CSV file not found: {args.csv_path}")
    if args.chunksize < 1:
        parser.error("--chunksize must be a positive integer")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    participant_counts = Counter()
    participant_flags = defaultdict(Counter)
    participant_duration_sums = Counter()
    participant_duration_counts = Counter()
    type_counts = Counter()
    type_flags = defaultdict(Counter)
    continuity_duration_sums = Counter()
    continuity_duration_counts = Counter()
    hourly_counts = Counter()
    weekday_counts = Counter()
    hourly_amount_sums = Counter()
    hourly_amount_counts = Counter()
    hourly_duration_sums = Counter()
    hourly_duration_counts = Counter()
    total_rows = 0

    for chunk in pd.read_csv(
        args.csv_path,
        usecols=REQUIRED_COLUMNS,
        dtype={
            "CONTINUITY_QFLAG": "string",
            "TRANSACTION_TYPE_CODE": "string",
        },
        chunksize=args.chunksize,
        low_memory=True,
        encoding="utf-8",
    ):
        total_rows += len(chunk)
        participant = pd.to_numeric(chunk["PARTICIPANT_COUNT"], errors="coerce")
        duration = pd.to_numeric(chunk["TOTAL_DURATION"], errors="coerce")
        amount = pd.to_numeric(chunk["USD_AMOUNT"], errors="coerce")
        continuity = chunk["CONTINUITY_QFLAG"].fillna("(missing)").astype(str).str.strip()
        transaction_type = chunk["TRANSACTION_TYPE_CODE"].fillna("(missing)").astype(str).str.strip()

        participant_labels = participant.dropna().astype(int).astype(str)
        participant_counts.update(participant_labels.value_counts().to_dict())
        participant_flag_frame = pd.DataFrame(
            {"participant": participant, "flag": continuity}
        ).dropna(subset=["participant"])
        for (number, flag), count in participant_flag_frame.value_counts().items():
            participant_flags[str(int(number))][flag] += int(count)

        duration_frame = pd.DataFrame(
            {"participant": participant, "duration": duration}
        ).dropna()
        grouped_duration = duration_frame.groupby("participant")["duration"].agg(["sum", "count"])
        for number, row in grouped_duration.iterrows():
            key = str(int(number))
            participant_duration_sums[key] += float(row["sum"])
            participant_duration_counts[key] += int(row["count"])

        type_counts.update(transaction_type.value_counts().to_dict())
        type_flag_frame = pd.DataFrame(
            {"type": transaction_type, "flag": continuity}
        )
        for (kind, flag), count in type_flag_frame.value_counts().items():
            type_flags[kind][flag] += int(count)

        continuity_duration = pd.DataFrame(
            {"flag": continuity, "duration": duration}
        ).dropna()
        for flag, row in continuity_duration.groupby("flag")["duration"].agg(["sum", "count"]).iterrows():
            continuity_duration_sums[str(flag)] += float(row["sum"])
            continuity_duration_counts[str(flag)] += int(row["count"])

        epoch = pd.to_numeric(chunk["EPOCH_SECONDS"], errors="coerce")
        utc = pd.to_datetime(epoch, unit="s", utc=True, errors="coerce")
        local = utc.dt.tz_convert(args.timezone)
        hour = local.dt.hour.astype("Int64")
        weekday = local.dt.day_name()
        hourly_counts.update(hour.dropna().astype(int).value_counts().to_dict())
        weekday_counts.update(weekday.dropna().value_counts().to_dict())
        add_value_summaries(amount, hour, hourly_amount_sums, hourly_amount_counts)
        add_value_summaries(duration, hour, hourly_duration_sums, hourly_duration_counts)

        if total_rows % (args.chunksize * 10) == 0:
            print(f"Processed {total_rows:,} records...", flush=True)

    plot_style()
    save_route_charts(
        args.output_dir,
        participant_counts,
        participant_duration_sums,
        participant_duration_counts,
    )
    save_type_charts(args.output_dir, type_counts, type_flags)
    save_route_observability_charts(
        args.output_dir,
        participant_counts,
        participant_flags,
        continuity_duration_sums,
        continuity_duration_counts,
    )
    save_temporal_chart(
        args.output_dir,
        hourly_counts,
        weekday_counts,
        hourly_amount_sums,
        hourly_amount_counts,
        hourly_duration_sums,
        hourly_duration_counts,
    )

    report = {
        "records": total_rows,
        "transaction_types": {
            kind: {
                "count": type_counts[kind],
                "continuous_y": type_flags[kind].get("Y", 0),
                "incomplete_n": type_flags[kind].get("N", 0),
                "incomplete_share_pct": round(
                    type_flags[kind].get("N", 0) / type_counts[kind] * 100, 4
                )
                if type_counts[kind]
                else 0,
            }
            for kind in TYPE_ORDER
        },
        "route_continuity": {
            flag: {
                "count": sum(values.get(flag, 0) for values in participant_flags.values()),
                "mean_duration_seconds": round(
                    continuity_duration_sums.get(flag, 0)
                    / continuity_duration_counts.get(flag, 1),
                    2,
                ),
                "duration_n": continuity_duration_counts.get(flag, 0),
            }
            for flag in FLAG_ORDER
        },
        "participant_counts": {
            key: {
                "count": participant_counts.get(key, 0),
                "mean_duration_seconds": round(
                    participant_duration_sums.get(key, 0)
                    / participant_duration_counts.get(key, 1),
                    2,
                ),
                "duration_n": participant_duration_counts.get(key, 0),
                "continuous_y": participant_flags[key].get("Y", 0),
                "incomplete_n": participant_flags[key].get("N", 0),
            }
            for key in sorted(participant_counts, key=int)
        },
        "hourly_volume": {
            str(hour): hourly_counts.get(hour, 0) for hour in range(24)
        },
        "weekday_volume": {
            day: weekday_counts.get(day, 0) for day in WEEKDAY_ORDER
        },
        "timezone": args.timezone,
    }
    print("\nVerified chart summary:")
    print(json.dumps(report, indent=2))
    print(f"\nCharts saved under {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
