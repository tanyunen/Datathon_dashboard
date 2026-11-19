import argparse
import json
from collections import Counter
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = [
    "ANOMALY_TYPE",
    "BENEFICIARY_TYPE",
    "CONTINUITY_QFLAG",
    "CURRENCY_CODE",
    "CURRENCY_CONVERSION_COUNT",
    "EPOCH_SECONDS",
    "ORDERING_TYPE",
    "PARTICIPANT_COUNT",
    "TOTAL_DURATION",
    "TRANSACTION_TYPE_CODE",
    "USD_AMOUNT",
]


def display_counts(counts, total):
    return {
        key: {
            "count": count,
            "share_pct": round(count / total * 100, 4) if total else 0,
        }
        for key, count in counts.most_common()
    }


def main():
    parser = argparse.ArgumentParser(
        description="Summarize the supplied SWIFT Datathon CSV in memory-safe chunks."
    )
    parser.add_argument("csv_path", type=Path, help="Path to the competition CSV file")
    parser.add_argument(
        "--timezone",
        default="Asia/Kuala_Lumpur",
        help="Timezone for hourly and weekday summaries (default: Asia/Kuala_Lumpur)",
    )
    parser.add_argument(
        "--chunksize",
        type=int,
        default=500_000,
        help="Rows per batch (default: 500000)",
    )
    args = parser.parse_args()

    if not args.csv_path.is_file():
        parser.error(f"CSV file not found: {args.csv_path}")
    if args.chunksize < 1:
        parser.error("--chunksize must be a positive integer")

    counters = {column: Counter() for column in REQUIRED_COLUMNS}
    pairs = Counter()
    fx_groups = Counter()
    hours = Counter()
    weekdays = Counter()
    total_rows = 0

    chunks = pd.read_csv(
        args.csv_path,
        usecols=REQUIRED_COLUMNS,
        dtype={"ANOMALY_TYPE": "string"},
        chunksize=args.chunksize,
        low_memory=True,
        encoding="utf-8",
    )
    for chunk_number, chunk in enumerate(chunks, start=1):
        total_rows += len(chunk)

        for column in REQUIRED_COLUMNS:
            values = chunk[column].fillna("(missing)").astype(str)
            counters[column].update(values.value_counts().to_dict())

        ordering = chunk["ORDERING_TYPE"].fillna("(missing)").astype(str)
        beneficiary = chunk["BENEFICIARY_TYPE"].fillna("(missing)").astype(str)
        pairs.update((f"{sender} -> {receiver}" for sender, receiver in zip(ordering, beneficiary)))

        fx = pd.to_numeric(chunk["CURRENCY_CONVERSION_COUNT"], errors="coerce")
        fx_labels = pd.Series("(missing)", index=chunk.index, dtype="object")
        fx_labels.loc[fx.eq(0)] = "0"
        fx_labels.loc[fx.eq(1)] = "1"
        fx_labels.loc[fx.ge(2)] = "2+"
        fx_labels.loc[fx.lt(0)] = "(negative)"
        fx_groups.update(fx_labels.value_counts().to_dict())

        epoch = pd.to_numeric(chunk["EPOCH_SECONDS"], errors="coerce")
        timestamps = pd.to_datetime(epoch, unit="s", utc=True, errors="coerce")
        local_timestamps = timestamps.dt.tz_convert(args.timezone)
        hours.update(local_timestamps.dt.hour.dropna().astype(int).value_counts().to_dict())
        weekdays.update(local_timestamps.dt.day_name().dropna().value_counts().to_dict())

        print(f"Processed {total_rows:,} records...", flush=True)

    report = {
        "source_file": str(args.csv_path.resolve()),
        "records_scanned": total_rows,
        "timezone": args.timezone,
        "transaction_types": display_counts(counters["TRANSACTION_TYPE_CODE"], total_rows),
        "route_continuity": display_counts(counters["CONTINUITY_QFLAG"], total_rows),
        "anomaly_labels": display_counts(counters["ANOMALY_TYPE"], total_rows),
        "ordering_party_types": display_counts(counters["ORDERING_TYPE"], total_rows),
        "beneficiary_party_types": display_counts(counters["BENEFICIARY_TYPE"], total_rows),
        "party_pairs": display_counts(pairs, total_rows),
        "unique_currency_codes": len(counters["CURRENCY_CODE"]),
        "top_currencies": display_counts(
            Counter(dict(counters["CURRENCY_CODE"].most_common(10))), total_rows
        ),
        "fx_conversion_groups": display_counts(fx_groups, total_rows),
        "participant_counts": display_counts(counters["PARTICIPANT_COUNT"], total_rows),
        "hourly_volume": display_counts(hours, total_rows),
        "weekday_volume": display_counts(weekdays, total_rows),
    }

    print("\nSummary (synthetic competition data; not actual SWIFT network statistics):")
    print(json.dumps(report, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
