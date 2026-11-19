import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd


STRING_COLUMNS = [
    "ANOMALY_TYPE",
    "BENEFICIARY_ACCOUNT",
    "BENEFICIARY_BIC8",
    "BENEFICIARY_TOKENS",
    "BENEFICIARY_TYPE",
    "BIC8_PATH",
    "CONTINUITY_QFLAG",
    "CURRENCY_CODE",
    "ORDERING_ACCOUNT",
    "ORDERING_BIC8",
    "ORDERING_TOKENS",
    "ORDERING_TYPE",
    "TRANSACTION_TYPE_CODE",
]
NUMERIC_COLUMNS = [
    "CURRENCY_CONVERSION_COUNT",
    "EPOCH_SECONDS",
    "PARTICIPANT_COUNT",
    "TOTAL_DURATION",
    "USD_AMOUNT",
]
REQUIRED_COLUMNS = STRING_COLUMNS + NUMERIC_COLUMNS
ANOMALY_LABELS = [
    "ROMANCE_SCAM",
    "FAT_FINGER_MISTAKE",
    "CEO_SCAM",
    "DUPLICATE_PAYMENT",
    "ACCOUNT_REPLACEMENT_SCAM",
    "CUSTOMER_RECALL",
]
PARTY_PAIRS = [("B", "B"), ("B", "C"), ("C", "B"), ("C", "C")]


def append_group_arrays(store, frame, group_columns, value_column):
    grouped = frame.groupby(group_columns, observed=True, dropna=True)[value_column]
    for key, values in grouped:
        if not isinstance(key, tuple):
            key = (key,)
        store[key].append(values.to_numpy(dtype="float64"))


def summarize_arrays(groups):
    summary = {}
    for key, pieces in groups.items():
        values = np.concatenate(pieces)
        values = values[np.isfinite(values)]
        if not len(values):
            continue
        summary[" | ".join(map(str, key))] = {
            "n": int(len(values)),
            "mean": round(float(np.mean(values)), 3),
            "median": round(float(np.median(values)), 3),
            "p90": round(float(np.quantile(values, 0.9)), 3),
        }
    return summary


def summarize_iban_jurisdiction(raw_counts, minimum_party_records=1_000):
    country_groups = defaultdict(Counter)
    for key, count in raw_counts.items():
        role, country, party_type, marker = key.split(" | ")
        country_groups[(role, country, party_type)][marker == "iban=True"] += count

    summary = {"overall_rates_by_role_and_party_type": {}, "country_standardized": {}}
    for role in ("sender", "beneficiary"):
        for party_type in ("B", "C"):
            total = sum(
                counts[True] + counts[False]
                for (group_role, _, group_type), counts in country_groups.items()
                if group_role == role and group_type == party_type
            )
            present = sum(
                counts[True]
                for (group_role, _, group_type), counts in country_groups.items()
                if group_role == role and group_type == party_type
            )
            summary["overall_rates_by_role_and_party_type"][
                f"{role} | {party_type}"
            ] = {
                "records": int(total),
                "iban_marker_records": int(present),
                "rate_pct": round(100 * present / total, 3) if total else None,
            }

        candidate_countries = {
            country
            for group_role, country, _ in country_groups
            if group_role == role
        }
        countries = sorted(
            country
            for country in candidate_countries
            if all(
                sum(
                    country_groups.get((role, country, party_type), Counter()).values()
                )
                >= minimum_party_records
                for party_type in ("B", "C")
            )
        )
        common_records = sum(
            sum(country_groups[(role, country, party_type)].values())
            for country in countries
            for party_type in ("B", "C")
        )
        standardized_rates = {}
        for party_type in ("B", "C"):
            weighted_marker_count = sum(
                (
                    sum(country_groups[(role, country, "B")].values())
                    + sum(country_groups[(role, country, "C")].values())
                )
                * country_groups[(role, country, party_type)][True]
                / sum(country_groups[(role, country, party_type)].values())
                for country in countries
            )
            standardized_rates[party_type] = (
                weighted_marker_count / common_records if common_records else None
            )
        rate_b = standardized_rates["B"]
        rate_c = standardized_rates["C"]
        summary["country_standardized"][role] = {
            "minimum_records_per_party_type": minimum_party_records,
            "countries": len(countries),
            "records_in_common_country_mix": int(common_records),
            "business_rate_pct": round(100 * rate_b, 3) if rate_b is not None else None,
            "consumer_rate_pct": round(100 * rate_c, 3) if rate_c is not None else None,
            "business_minus_consumer_percentage_points": (
                round(100 * (rate_b - rate_c), 3)
                if rate_b is not None and rate_c is not None
                else None
            ),
        }

    summary["country_examples"] = {}
    for role in ("sender", "beneficiary"):
        summary["country_examples"][role] = {}
        for country in ("US", "SG", "CN", "DE"):
            counts = Counter()
            for party_type in ("B", "C"):
                counts.update(country_groups[(role, country, party_type)])
            total = sum(counts.values())
            summary["country_examples"][role][country] = {
                "records": int(total),
                "iban_marker_records": int(counts[True]),
                "rate_pct": round(100 * counts[True] / total, 3) if total else None,
            }
    return summary


def summarize_anomaly_sequences(anomaly_rows):
    if not anomaly_rows:
        return {}
    frame = pd.concat(anomaly_rows, ignore_index=True)
    frame["ANOMALY_TYPE"] = frame["ANOMALY_TYPE"].str.strip()
    frame["EPOCH_SECONDS"] = pd.to_numeric(frame["EPOCH_SECONDS"], errors="coerce")
    frame["USD_AMOUNT"] = pd.to_numeric(frame["USD_AMOUNT"], errors="coerce")

    results = {}
    for label in ANOMALY_LABELS:
        subset = frame.loc[frame["ANOMALY_TYPE"].eq(label)].copy()
        if subset.empty:
            continue
        result = {"records": int(len(subset))}
        result["median_usd_amount"] = round(
            float(subset["USD_AMOUNT"].median()), 2
        )

        valid_pairs = subset.dropna(
            subset=["ORDERING_ACCOUNT", "BENEFICIARY_ACCOUNT", "EPOCH_SECONDS", "USD_AMOUNT"]
        ).copy()
        valid_pairs = valid_pairs.sort_values(
            ["ORDERING_ACCOUNT", "BENEFICIARY_ACCOUNT", "EPOCH_SECONDS"],
        )
        paired = valid_pairs.groupby(
            ["ORDERING_ACCOUNT", "BENEFICIARY_ACCOUNT"], observed=True
        )
        previous_time = paired["EPOCH_SECONDS"].shift()
        previous_amount = paired["USD_AMOUNT"].shift()
        elapsed = valid_pairs["EPOCH_SECONDS"] - previous_time
        ratio = valid_pairs["USD_AMOUNT"] / previous_amount
        transitions = elapsed.ge(0) & previous_amount.gt(0) & np.isfinite(ratio)
        elapsed = elapsed.loc[transitions]
        ratio = ratio.loc[transitions]
        result["same_sender_beneficiary_transitions"] = int(transitions.sum())
        if len(elapsed):
            result["median_transition_seconds"] = round(float(elapsed.median()), 2)
            result["median_next_to_previous_usd_ratio"] = round(float(ratio.median()), 3)
            result["transitions_within_18_minutes"] = int(elapsed.le(18 * 60).sum())
            result["identical_usd_amount_transitions"] = int(ratio.eq(1).sum())
            result["transitions_with_amount_increase"] = int(ratio.gt(1).sum())
            result["transitions_with_ratio_1_4_to_1_6"] = int(
                ratio.between(1.4, 1.6).sum()
            )

        if label in {"CEO_SCAM", "ACCOUNT_REPLACEMENT_SCAM"}:
            hubs = subset.dropna(
                subset=["BENEFICIARY_ACCOUNT", "ORDERING_ACCOUNT"]
            ).groupby("BENEFICIARY_ACCOUNT", observed=True)["ORDERING_ACCOUNT"].agg(
                ["size", "nunique"]
            )
            result["beneficiary_accounts"] = int(len(hubs))
            if len(hubs):
                result["median_distinct_sender_accounts_per_beneficiary"] = round(
                    float(hubs["nunique"].median()), 2
                )
                result["beneficiaries_with_at_least_7_distinct_senders"] = int(
                    hubs["nunique"].ge(7).sum()
                )
                result["maximum_distinct_sender_accounts_per_beneficiary"] = int(
                    hubs["nunique"].max()
                )

        if label in {"FAT_FINGER_MISTAKE", "CUSTOMER_RECALL"}:
            pair_counts = subset.groupby(
                ["ORDERING_ACCOUNT", "BENEFICIARY_ACCOUNT"],
                observed=True,
                dropna=True,
            ).size()
            result["single_record_sender_beneficiary_pairs"] = int(
                pair_counts.eq(1).sum()
            )
            result["sender_beneficiary_pairs"] = int(len(pair_counts))

        results[label] = result
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Compute evidence summaries for the Datathon judging criteria."
    )
    parser.add_argument("csv_path", type=Path, help="Path to the competition CSV")
    parser.add_argument("--chunksize", type=int, default=200_000)
    args = parser.parse_args()
    if not args.csv_path.is_file():
        parser.error(f"CSV file not found: {args.csv_path}")
    if args.chunksize < 1:
        parser.error("--chunksize must be positive")

    counters = defaultdict(Counter)
    arrays = {
        "amount_by_party_pair": defaultdict(list),
        "duration_by_participant_count": defaultdict(list),
        "duration_by_participant_and_type": defaultdict(list),
        "duration_by_continuity": defaultdict(list),
    }
    all_amounts = []
    unlabeled_amounts = []
    anomaly_rows = []
    total_rows = 0
    valid_time_rows = 0

    reader = pd.read_csv(
        args.csv_path,
        usecols=REQUIRED_COLUMNS,
        dtype={column: "string" for column in STRING_COLUMNS},
        chunksize=args.chunksize,
        low_memory=True,
        encoding="utf-8",
    )
    for chunk in reader:
        total_rows += len(chunk)
        for column in NUMERIC_COLUMNS:
            chunk[column] = pd.to_numeric(chunk[column], errors="coerce")

        participants = chunk["PARTICIPANT_COUNT"]
        transaction_type = chunk["TRANSACTION_TYPE_CODE"].fillna("(missing)").str.strip()
        continuity = chunk["CONTINUITY_QFLAG"].fillna("(missing)").str.strip()
        path = chunk["BIC8_PATH"].fillna("").str.strip()
        path_present = path.ne("")
        path_has_ellipsis = path.str.contains("...", regex=False)
        segment_count = path.str.count(";") + 1
        path_frame = pd.DataFrame(
            {
                "participants": participants,
                "segments": segment_count,
                "continuity": continuity,
                "ellipsis": path_has_ellipsis,
            }
        )
        path_frame = path_frame.loc[path_present & participants.notna()]
        counters["path_segment_agreement"].update(
            {
                str(key): int(value)
                for key, value in path_frame.assign(
                    agrees=path_frame["participants"].eq(path_frame["segments"])
                )["agrees"].value_counts().items()
            }
        )
        counters["path_ellipsis_by_continuity"].update(
            {
                f"{flag} | ellipsis={bool(has_ellipsis)}": int(count)
                for (flag, has_ellipsis), count in path_frame.groupby(
                    ["continuity", "ellipsis"], observed=True
                ).size().items()
            }
        )
        counters["participant_by_type"].update(
            {
                f"{int(count)} | {kind}": int(value)
                for (count, kind), value in pd.DataFrame(
                    {"participants": participants, "type": transaction_type}
                ).dropna(subset=["participants"]).groupby(
                    ["participants", "type"], observed=True
                ).size().items()
            }
        )
        counters["continuity_by_participant"].update(
            {
                f"{int(count)} | {flag}": int(value)
                for (count, flag), value in pd.DataFrame(
                    {"participants": participants, "flag": continuity}
                ).dropna(subset=["participants"]).groupby(
                    ["participants", "flag"], observed=True
                ).size().items()
            }
        )

        conversions = chunk["CURRENCY_CONVERSION_COUNT"]
        valid_bounds = participants.notna() & conversions.notna()
        violations = valid_bounds & conversions.gt(participants - 1)
        counters["fx_bound"]["rows_with_both_values"] += int(valid_bounds.sum())
        counters["fx_bound"]["violations"] += int(violations.sum())
        if valid_bounds.any():
            excess = conversions.loc[valid_bounds] - (
                participants.loc[valid_bounds] - 1
            )
            counters["fx_bound_excess"].update(
                {str(key): int(value) for key, value in excess.value_counts().items()}
            )

        ordering_bic = chunk["ORDERING_BIC8"].str.strip().str.upper()
        sender_country = ordering_bic.str.slice(4, 6)
        currency = chunk["CURRENCY_CODE"].fillna("(missing)").str.strip().str.upper()
        counters["sender_country_currency"].update(
            {
                f"{country} | {code}": int(count)
                for (country, code), count in pd.DataFrame(
                    {"country": sender_country, "currency": currency}
                ).dropna(subset=["country"]).groupby(
                    ["country", "currency"], observed=True
                ).size().items()
            }
        )
        for role, bic_column, token_column, party_column in [
            ("sender", "ORDERING_BIC8", "ORDERING_TOKENS", "ORDERING_TYPE"),
            (
                "beneficiary",
                "BENEFICIARY_BIC8",
                "BENEFICIARY_TOKENS",
                "BENEFICIARY_TYPE",
            ),
        ]:
            bic = chunk[bic_column].str.strip().str.upper()
            country = bic.str.slice(4, 6)
            has_iban = chunk[token_column].fillna("").str.contains(
                "<iban:", regex=False
            )
            party_type = chunk[party_column].fillna("(missing)").str.strip()
            iban_frame = pd.DataFrame(
                {
                    "country": country,
                    "party_type": party_type,
                    "has_iban": has_iban,
                }
            ).dropna(subset=["country"])
            counters["iban_by_country_and_role_type"].update(
                {
                    f"{role} | {country_code} | {kind} | iban={bool(marker)}": int(
                        count
                    )
                    for (country_code, kind, marker), count in iban_frame.groupby(
                        ["country", "party_type", "has_iban"], observed=True
                    ).size().items()
                }
            )

        durations = chunk["TOTAL_DURATION"]
        duration_frame = pd.DataFrame(
            {
                "participants": participants,
                "type": transaction_type,
                "flag": continuity,
                "duration": durations,
            }
        ).dropna(subset=["participants", "duration"])
        append_group_arrays(
            arrays["duration_by_participant_count"],
            duration_frame,
            ["participants"],
            "duration",
        )
        append_group_arrays(
            arrays["duration_by_participant_and_type"],
            duration_frame,
            ["participants", "type"],
            "duration",
        )
        append_group_arrays(
            arrays["duration_by_continuity"],
            duration_frame,
            ["flag"],
            "duration",
        )

        amounts = chunk["USD_AMOUNT"]
        finite_amounts = amounts.loc[np.isfinite(amounts)]
        if len(finite_amounts):
            all_amounts.append(finite_amounts.to_numpy(dtype="float64"))
        anomaly = chunk["ANOMALY_TYPE"].fillna("").str.strip()
        labeled = anomaly.ne("")
        finite_unlabeled = amounts.loc[np.isfinite(amounts) & ~labeled]
        if len(finite_unlabeled):
            unlabeled_amounts.append(finite_unlabeled.to_numpy(dtype="float64"))
        party_frame = pd.DataFrame(
            {
                "sender": chunk["ORDERING_TYPE"].str.strip(),
                "beneficiary": chunk["BENEFICIARY_TYPE"].str.strip(),
                "amount": amounts,
            }
        ).dropna()
        append_group_arrays(
            arrays["amount_by_party_pair"],
            party_frame,
            ["sender", "beneficiary"],
            "amount",
        )

        epoch = chunk["EPOCH_SECONDS"]
        valid_time = epoch.notna() & np.isfinite(epoch)
        if valid_time.any():
            timestamps = pd.to_datetime(
                epoch.loc[valid_time], unit="s", utc=True, errors="coerce"
            ).dt.tz_convert("Asia/Kuala_Lumpur")
            counters["weekday_malaysia"].update(
                timestamps.dt.day_name().dropna().value_counts().to_dict()
            )
            counters["hour_malaysia"].update(
                {
                    str(int(hour)): int(count)
                    for hour, count in timestamps.dt.hour.dropna().value_counts().items()
                }
            )
            valid_time_rows += int(timestamps.notna().sum())

        if labeled.any():
            anomaly_rows.append(
                chunk.loc[
                    labeled,
                    [
                        "ANOMALY_TYPE",
                        "ORDERING_ACCOUNT",
                        "BENEFICIARY_ACCOUNT",
                        "EPOCH_SECONDS",
                        "USD_AMOUNT",
                    ],
                ].copy()
            )
            counters["anomaly_labels"].update(anomaly.loc[labeled].value_counts().to_dict())

        if total_rows % (args.chunksize * 5) == 0:
            print(f"Processed {total_rows:,} rows...", file=sys.stderr, flush=True)

    all_amount_values = np.concatenate(all_amounts)
    unlabeled_amount_values = np.concatenate(unlabeled_amounts)
    report = {
        "records": total_rows,
        "valid_timestamp_records": valid_time_rows,
        "participant_count_by_transaction_type": dict(counters["participant_by_type"]),
        "continuity_by_participant_count": dict(counters["continuity_by_participant"]),
        "path_segments_match_participant_count": dict(
            counters["path_segment_agreement"]
        ),
        "path_ellipsis_by_continuity": dict(counters["path_ellipsis_by_continuity"]),
        "fx_bound": {
            "rows_with_both_values": counters["fx_bound"]["rows_with_both_values"],
            "violations_count_conversion_gt_participants_minus_1": counters[
                "fx_bound"
            ]["violations"],
            "conversion_minus_maximum_distribution": dict(
                counters["fx_bound_excess"]
            ),
        },
        "sender_country_currency_counts": dict(counters["sender_country_currency"]),
        "iban_by_country_party_type_and_role": dict(
            counters["iban_by_country_and_role_type"]
        ),
        "iban_jurisdiction_summary": summarize_iban_jurisdiction(
            counters["iban_by_country_and_role_type"]
        ),
        "party_pair_amounts": summarize_arrays(arrays["amount_by_party_pair"]),
        "duration_by_participant_count": summarize_arrays(
            arrays["duration_by_participant_count"]
        ),
        "duration_by_participant_and_type": summarize_arrays(
            arrays["duration_by_participant_and_type"]
        ),
        "duration_by_continuity": summarize_arrays(arrays["duration_by_continuity"]),
        "overall_usd_amount": {
            "n": int(len(all_amount_values)),
            "median": round(float(np.median(all_amount_values)), 2),
            "p90": round(float(np.quantile(all_amount_values, 0.9)), 2),
        },
        "unlabeled_usd_amount": {
            "n": int(len(unlabeled_amount_values)),
            "median": round(float(np.median(unlabeled_amount_values)), 2),
            "p90": round(float(np.quantile(unlabeled_amount_values, 0.9)), 2),
        },
        "weekday_volume_malaysia_time": dict(counters["weekday_malaysia"]),
        "hourly_volume_malaysia_time": dict(counters["hour_malaysia"]),
        "anomaly_counts": dict(counters["anomaly_labels"]),
        "anomaly_sequences": summarize_anomaly_sequences(anomaly_rows),
        "time_zone_note": (
            "Weekday and hour summaries use Asia/Kuala_Lumpur. The CSV has no "
            "sender-local time-zone field; BIC country alone cannot resolve "
            "multiple time zones within a country."
        ),
        "amount_note": (
            "USD_AMOUNT is the dataset's normalized amount, not a confirmed "
            "loss or raw-currency transfer amount."
        ),
    }
    print(json.dumps(report, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
