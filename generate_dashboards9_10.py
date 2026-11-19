import argparse
from html import escape
import json
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from chart_palette import AMBER, FOREST, GREEN, SAGE, SLATE, TYPE_COLORS


REQUIRED_COLUMNS = [
    "ANOMALY_TYPE",
    "CURRENCY_CODE",
    "EPOCH_SECONDS",
    "TRANSACTION_TYPE_CODE",
]
TYPE_ORDER = ["Direct", "Indirect", "Covered"]
MIN_CURRENCY_COUNT = 50_000
def clean_text(values, missing_label):
    cleaned = values.astype("string").str.strip()
    return cleaned.mask(cleaned.eq(""), pd.NA).fillna(missing_label)


def save_currency_chart(output_dir, currency_counts, currency_flags, baseline_rate):
    eligible = [
        code
        for code, count in currency_counts.items()
        if code != "(missing)" and count >= MIN_CURRENCY_COUNT
    ]
    eligible.sort(
        key=lambda code: (
            currency_flags[code] / currency_counts[code],
            currency_counts[code],
        ),
        reverse=True,
    )
    rates_per_10k = [
        currency_flags[code] / currency_counts[code] * 10_000 for code in eligible
    ]
    labels = [
        f"{code}  (n={currency_counts[code]:,})"
        for code in eligible
    ]
    colors = [
        AMBER if rate > baseline_rate * 10_000 else SAGE
        for rate in rates_per_10k
    ]

    fig, ax = plt.subplots(figsize=(11, max(5.5, len(eligible) * 0.34)), facecolor="white")
    y = np.arange(len(eligible))
    ax.barh(y, rates_per_10k, color=colors, height=0.72)
    ax.axvline(
        baseline_rate * 10_000,
        color=SLATE,
        linestyle="--",
        linewidth=1.5,
        label=f"All valid-currency records: {baseline_rate * 10_000:.2f} per 10,000",
    )
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlabel("Records with a listed anomaly label per 10,000 records")
    ax.set_title(f"Anomaly-label rate by currency (n ≥ {MIN_CURRENCY_COUNT:,})")
    ax.legend(frameon=False, loc="lower right")
    ax.grid(axis="x", linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_dir / "dashboard9_currency_anomaly.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    volume_order = sorted(eligible, key=lambda code: currency_counts[code], reverse=True)
    fig, ax = plt.subplots(figsize=(11, 5), facecolor="white")
    y = np.arange(len(volume_order))
    bars = ax.barh(
        y,
        [currency_counts[code] for code in volume_order],
        color=GREEN,
        height=0.72,
    )
    ax.set_yticks(y, volume_order)
    ax.invert_yaxis()
    ax.set_xlabel("Records")
    ax.set_title("Sample size by currency (eligible groups only)")
    ax.bar_label(bars, labels=[f"{currency_counts[code]:,}" for code in volume_order], padding=3, fontsize=8)
    ax.grid(axis="x", linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_dir / "dashboard9_currency_sample_size.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def save_hourly_chart(output_dir, types, hourly_counts, hourly_flags, type_baselines):
    fig, ax = plt.subplots(figsize=(11, 4.8), facecolor="white")
    hours = np.arange(24)
    for kind in types:
        counts = np.array([hourly_counts[kind][hour] for hour in hours], dtype=float)
        flags = np.array([hourly_flags[kind][hour] for hour in hours], dtype=float)
        rates = np.divide(
            flags * 10_000,
            counts,
            out=np.zeros_like(flags),
            where=counts > 0,
        )
        baseline = type_baselines[kind] * 10_000
        ratios = np.divide(
            rates,
            baseline,
            out=np.zeros_like(rates),
            where=baseline > 0,
        )
        color = TYPE_COLORS.get(kind, SAGE)
        ax.plot(hours, ratios, marker="o", markersize=3.5, linewidth=1.8, color=color, label=kind)
    ax.axhline(1, color=SLATE, linestyle="--", linewidth=1.4, label="Same-type all-hour baseline")
    ax.set_xticks(range(24), [f"{hour:02d}:00" for hour in range(24)], rotation=45, ha="right")
    ax.set_ylabel("Hourly rate ÷ same-type all-hour rate")
    ax.set_xlabel("Hour in Malaysia time (UTC+8)")
    ax.set_title("Hourly anomaly-label rate relative to each transaction type's baseline")
    ax.legend(frameon=False, ncol=2)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_dir / "dashboard10_hourly_anomaly_rate.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 3.8), facecolor="white")
    bottom = np.zeros(24)
    for kind in types:
        counts = np.array([hourly_counts[kind][hour] for hour in hours])
        ax.bar(
            hours,
            counts,
            bottom=bottom,
            color=TYPE_COLORS.get(kind, SAGE),
            width=0.82,
            label=kind,
        )
        bottom += counts
    ax.set_xticks(range(24), [f"{hour:02d}" for hour in range(24)])
    ax.set_xlabel("Hour in Malaysia time (UTC+8)")
    ax.set_ylabel("Records")
    ax.set_title("Hourly sample size (all transaction types)")
    ax.legend(frameon=False, ncol=min(4, max(1, len(types))))
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_dir / "dashboard10_hourly_sample_size.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def page_style():
    return """
      :root { color-scheme: light; --ink:#153f32; --muted:#526b61; --green:#07583e; --mint:#e6f4ea; --line:#dce7e0; }
      * { box-sizing:border-box; }
      body { margin:0; padding:24px; background:#f1f5f2; color:var(--ink); font:15px/1.5 "Segoe UI",Arial,sans-serif; }
      main { max-width:1500px; margin:auto; }
      header { padding:22px 26px; border-radius:12px; color:#fff; background:linear-gradient(110deg,#087a50,#104b38); }
      header .eyebrow { margin:0 0 4px; color:#d6f4e8; font-size:12px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; }
      h1 { margin:0; font-size:clamp(24px,3vw,34px); }
      header p { margin:6px 0 0; color:#e4f8ee; }
      header a { color:#fff; }
      h2 { margin:26px 0 12px; color:var(--green); font-size:20px; }
      .metrics { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin:14px 0; }
      .metric,.card,figure { border:1px solid var(--line); border-radius:10px; background:#fff; box-shadow:0 2px 6px #153f320d; }
      .metric { padding:14px; border-left:4px solid #168052; }
      .metric span { display:block; color:var(--muted); font-size:12px; font-weight:700; text-transform:uppercase; }
      .metric strong { display:block; margin-top:4px; color:var(--green); font-size:20px; line-height:1.25; }
      .charts { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px; }
      figure { margin:0; padding:12px; }
      figure img { display:block; width:100%; height:auto; }
      figcaption { margin-top:8px; color:var(--muted); font-size:13px; }
      .content { display:grid; grid-template-columns:minmax(0,1.2fr) minmax(300px,.8fr); gap:14px; align-items:start; }
      .card { padding:16px; }
      .table-wrap { max-height:620px; overflow:auto; }
      table { width:100%; border-collapse:collapse; font-size:13px; }
      th,td { padding:7px 8px; border-bottom:1px solid var(--line); text-align:left; white-space:nowrap; }
      th { position:sticky; top:0; background:#e6f4ea; color:var(--green); }
      .card h3 { margin:0 0 6px; color:var(--green); font-size:16px; }
      .card p { margin:0 0 12px; }
      .card p:last-child { margin-bottom:0; }
      .note { padding:12px 14px; border-left:4px solid #d5a72d; border-radius:7px; background:#fffaf0; }
      .note strong { color:#78350f; }
      footer { margin:22px 0 4px; color:var(--muted); font-size:13px; }
      @media(max-width:850px) { body{padding:14px}.metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.charts,.content{grid-template-columns:1fr} }
      @media(max-width:480px) { .metrics{grid-template-columns:1fr} header{padding:18px} }
    """


def render_dashboard9(report):
    currency = report["currency_analysis"]
    baseline = currency["eligible_baseline_rate_per_10000"]
    rows = []
    for item in currency["currencies"]:
        ratio = item["label_rate_per_10000"] / baseline if baseline else 0
        rows.append(
            "<tr>"
            f"<td>{escape(item['currency'])}</td>"
            f"<td>{item['records']:,}</td>"
            f"<td>{item['labelled_records']:,}</td>"
            f"<td>{item['label_rate_per_10000']:.3f}</td>"
            f"<td>{ratio:.2f}x</td>"
            "</tr>"
        )
    highest = currency["currencies"][0]
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Dashboard 9 | Anomaly Labels by Currency</title>
  <style>{page_style()}</style>
  <link rel="stylesheet" href="dashboard_shared.css">
</head>
<body data-dashboard="9" data-dashboard-root=".">
<main>
  <header>
    <p class="eyebrow">SWIFT Datathon 2026 | Dashboard 9</p>
    <h1>Anomaly-label rate by currency</h1>
    <p>Observed label frequency across currency groups with at least {currency['minimum_currency_group_size']:,} records.</p>
    <p><a href="index.html">Back to dashboard hub</a></p>
  </header>
  <section class="metrics" aria-label="Dashboard 9 key measures">
    <div class="metric"><span>Records with a currency code</span><strong>{currency['valid_currency_records']:,}</strong></div>
    <div class="metric"><span>Currency groups shown</span><strong>{currency['eligible_currency_count']}</strong></div>
    <div class="metric"><span>Eligible-group baseline</span><strong>{baseline:.3f} / 10,000</strong></div>
    <div class="metric"><span>Highest observed rate</span><strong>{escape(highest['currency'])}: {highest['label_rate_per_10000']:.3f} / 10,000</strong></div>
  </section>
  <section class="charts" aria-label="Currency anomaly charts">
    <figure>
      <img src="dashboard9_currency_anomaly.png" alt="Records with a listed anomaly label per 10,000 records by currency. Dashed line is the overall baseline for the 21 eligible currencies.">
      <figcaption>Comparison baseline: {currency['eligible_labelled_records']:,} labelled records among {currency['eligible_records']:,} records in eligible currencies ({baseline:.3f} per 10,000).</figcaption>
    </figure>
    <figure>
      <img src="dashboard9_currency_sample_size.png" alt="Sample size for every currency group included in the Dashboard 9 rate comparison.">
      <figcaption>Currency groups below the pre-set {currency['minimum_currency_group_size']:,}-record threshold are omitted from the rate chart.</figcaption>
    </figure>
  </section>
  <h2>Observed rates by currency</h2>
  <section class="content">
    <div class="card">
      <h3>All eligible currency groups</h3>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Currency</th><th>Records</th><th>Listed labels</th><th>Per 10,000</th><th>Rate / baseline</th></tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
      </div>
    </div>
    <aside class="card">
      <h3>Question and reconstructed rule</h3>
      <p><strong>Question:</strong> Does the share of records with a listed <code>ANOMALY_TYPE</code> label differ across <code>CURRENCY_CODE</code> groups?</p>
      <p><strong>Rule:</strong> For each currency with n &gt;= {currency['minimum_currency_group_size']:,}, divide rows with a non-empty anomaly label by all records in that currency, then scale to 10,000 records. Compare with the {currency['eligible_currency_count']} eligible groups' pooled baseline.</p>
      <h3>What the data shows</h3>
      <p>{escape(highest['currency'])} has the highest observed rate among eligible groups: {highest['label_rate_per_10000']:.3f} per 10,000 ({highest['labelled_records']:,} of {highest['records']:,}), versus {baseline:.3f} per 10,000 overall in the eligible groups. This is a descriptive difference, not evidence that the currency caused an anomaly.</p>
      <p><strong>Interpretation:</strong> The difference can guide a follow-up check of label definitions and currency mix. It does not show currency errors, fraud losses, liquidity shortages, or operational risk.</p>
      <p class="note"><strong>Method and limits:</strong> {currency['valid_currency_records']:,} records had a currency code; {currency['missing_currency_records']:,} had none. The 21 shown groups cover {currency['eligible_records']:,} records; smaller groups are excluded to avoid unstable rates. Labels are dataset annotations, not confirmed real-world incidents. Currency, amount, route, and transaction-type mix are not controlled here.</p>
    </aside>
  </section>
  <footer>Source: supplied fictitious payment dataset. Generated by generate_dashboards9_10.py. Rates are descriptive and apply only to this dataset.</footer>
</main>
<script src="dashboard_nav.js"></script>
</body>
</html>
"""


def render_dashboard10(report):
    hourly = report["hourly_analysis"]
    types = hourly["transaction_types"]
    rows = []
    for kind, values in types.items():
        ratio = (
            values["highest_hour_rate_per_10000"] / values["baseline_rate_per_10000"]
            if values["baseline_rate_per_10000"]
            else 0
        )
        rows.append(
            "<tr>"
            f"<td>{escape(kind)}</td>"
            f"<td>{values['records']:,}</td>"
            f"<td>{values['labelled_records']:,}</td>"
            f"<td>{values['baseline_rate_per_10000']:.3f}</td>"
            f"<td>{escape(values['highest_hour'])}</td>"
            f"<td>{values['highest_hour_labelled_records']:,} / {values['highest_hour_records']:,}</td>"
            f"<td>{values['highest_hour_rate_per_10000']:.3f}</td>"
            f"<td>{ratio:.2f}x</td>"
            "</tr>"
        )
    peak_kind, peak = max(
        types.items(),
        key=lambda item: item[1]["highest_hour_rate_per_10000"],
    )
    total_labels = sum(values["labelled_records"] for values in types.values())
    overall_rate = total_labels / hourly["valid_timestamp_records"] * 10_000
    type_baseline_range = (
        min(values["baseline_rate_per_10000"] for values in types.values()),
        max(values["baseline_rate_per_10000"] for values in types.values()),
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Dashboard 10 | Hourly Anomaly-label Rates</title>
  <style>{page_style()}</style>
  <link rel="stylesheet" href="dashboard_shared.css">
</head>
<body data-dashboard="10" data-dashboard-root=".">
<main>
  <header>
    <p class="eyebrow">SWIFT Datathon 2026 | Dashboard 10</p>
    <h1>Anomaly-label rates by hour and transaction type</h1>
    <p>Hourly rates are compared with each transaction type's own all-hour baseline.</p>
    <p><a href="index.html">Back to dashboard hub</a></p>
  </header>
  <section class="metrics" aria-label="Dashboard 10 key measures">
    <div class="metric"><span>Records with valid timestamps</span><strong>{hourly['valid_timestamp_records']:,}</strong></div>
    <div class="metric"><span>Records with a listed label</span><strong>{total_labels:,} ({overall_rate / 100:.4f}%)</strong></div>
    <div class="metric"><span>Overall descriptive rate</span><strong>{overall_rate:.3f} / 10,000</strong></div>
    <div class="metric"><span>Highest observed type/hour rate</span><strong>{escape(peak_kind)} {escape(peak['highest_hour'])}: {peak['highest_hour_rate_per_10000']:.3f} / 10,000</strong></div>
  </section>
  <section class="charts" aria-label="Hourly anomaly rate and sample-size charts">
    <figure>
      <img src="dashboard10_hourly_anomaly_rate.png" alt="Hourly anomaly-label rate divided by each transaction type's all-hour baseline. An index of 1 equals that type's baseline.">
      <figcaption>Index 1.0 is each type's own all-hour baseline ({type_baseline_range[0]:.3f} to {type_baseline_range[1]:.3f} labelled records per 10,000, depending on type).</figcaption>
    </figure>
    <figure>
      <img src="dashboard10_hourly_sample_size.png" alt="Number of records by local hour and transaction type, showing the denominators behind hourly rates.">
      <figcaption>Sample sizes by hour and type are shown so rates are not mistaken for raw label counts.</figcaption>
    </figure>
  </section>
  <h2>Within-type baseline and highest observed hour</h2>
  <section class="content">
    <div class="card">
      <div class="table-wrap">
        <table>
          <thead><tr><th>Transaction type</th><th>Records</th><th>Listed labels</th><th>All-hour baseline / 10,000</th><th>Highest hour</th><th>Labels / records at hour</th><th>Rate / 10,000</th><th>Rate / baseline</th></tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
      </div>
    </div>
    <aside class="card">
      <h3>Question and reconstructed rule</h3>
      <p><strong>Question:</strong> Does the rate of records with a listed <code>ANOMALY_TYPE</code> label vary by local hour within each <code>TRANSACTION_TYPE_CODE</code>?</p>
      <p><strong>Rule:</strong> Convert <code>EPOCH_SECONDS</code> to {escape(hourly['timezone'])}. For every type and hour, calculate labelled records / all valid-timestamp records x 10,000; compare with that type's pooled all-hour rate.</p>
      <h3>What the data shows</h3>
      <p>The highest observed type/hour cell is {escape(peak_kind)} at {escape(peak['highest_hour'])}: {peak['highest_hour_labelled_records']:,} of {peak['highest_hour_records']:,} records ({peak['highest_hour_rate_per_10000']:.3f} per 10,000, {peak['highest_hour_rate_per_10000'] / peak['baseline_rate_per_10000']:.2f}x its type baseline). This is an exploratory maximum across {len(types) * 24} cells, not proof of a recurring peak.</p>
      <p><strong>Interpretation:</strong> Hour/type differences can identify where to inspect label composition next. They do not establish operator fatigue, settlement stress, or that automation would prevent labelled records.</p>
      <p class="note"><strong>Method and limits:</strong> All {hourly['valid_timestamp_records']:,} records had valid timestamps. A listed label means a non-empty dataset annotation; an unlabelled record is not confirmed normal. Rates are unadjusted for currency, route, or amount. The highest cell is descriptive and should be checked in another sample before drawing operational conclusions.</p>
    </aside>
  </section>
  <footer>Source: supplied fictitious payment dataset. Times are {escape(hourly['timezone'])}. Generated by generate_dashboards9_10.py. Rates are descriptive and apply only to this dataset.</footer>
</main>
<script src="dashboard_nav.js"></script>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(
        description="Build evidence-based currency and hourly anomaly dashboards."
    )
    parser.add_argument("csv_path", type=Path, help="Path to the competition CSV file")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Project root for generated chart images",
    )
    parser.add_argument("--chunksize", type=int, default=500_000)
    parser.add_argument("--timezone", default="Asia/Kuala_Lumpur")
    args = parser.parse_args()

    if not args.csv_path.is_file():
        parser.error(f"CSV file not found: {args.csv_path}")
    if args.chunksize < 1:
        parser.error("--chunksize must be a positive integer")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    currency_counts = Counter()
    currency_flags = Counter()
    hourly_counts = defaultdict(Counter)
    hourly_flags = defaultdict(Counter)
    type_counts = Counter()
    type_flags = Counter()
    valid_time_records = 0
    valid_currency_records = 0
    missing_currency_records = 0
    total_rows = 0

    for chunk in pd.read_csv(
        args.csv_path,
        usecols=REQUIRED_COLUMNS,
        dtype={
            "ANOMALY_TYPE": "string",
            "CURRENCY_CODE": "string",
            "TRANSACTION_TYPE_CODE": "string",
        },
        chunksize=args.chunksize,
        low_memory=True,
        encoding="utf-8",
    ):
        total_rows += len(chunk)
        anomaly = clean_text(chunk["ANOMALY_TYPE"], "")
        labelled = anomaly.ne("")

        currency = clean_text(chunk["CURRENCY_CODE"], "(missing)")
        currency_frame = pd.DataFrame({"currency": currency, "labelled": labelled})
        currency_grouped = currency_frame.groupby("currency", observed=True)["labelled"].agg(
            ["size", "sum"]
        )
        for code, row in currency_grouped.iterrows():
            currency_counts[str(code)] += int(row["size"])
            currency_flags[str(code)] += int(row["sum"])

        missing_currency_records += int(currency.eq("(missing)").sum())
        valid_currency_records += int(currency.ne("(missing)").sum())

        type_name = clean_text(chunk["TRANSACTION_TYPE_CODE"], "(missing)")
        epoch = pd.to_numeric(chunk["EPOCH_SECONDS"], errors="coerce")
        local_time = pd.to_datetime(epoch, unit="s", utc=True, errors="coerce").dt.tz_convert(
            args.timezone
        )
        hour = local_time.dt.hour
        valid_time = hour.notna()
        valid_time_records += int(valid_time.sum())
        time_frame = pd.DataFrame(
            {
                "type": type_name[valid_time],
                "hour": hour[valid_time].astype(int),
                "labelled": labelled[valid_time],
            }
        )
        type_grouped = time_frame.groupby("type", observed=True)["labelled"].agg(["size", "sum"])
        for kind, row in type_grouped.iterrows():
            type_counts[str(kind)] += int(row["size"])
            type_flags[str(kind)] += int(row["sum"])
        hourly_grouped = time_frame.groupby(["type", "hour"], observed=True)["labelled"].agg(
            ["size", "sum"]
        )
        for (kind, hour_value), row in hourly_grouped.iterrows():
            hourly_counts[str(kind)][int(hour_value)] += int(row["size"])
            hourly_flags[str(kind)][int(hour_value)] += int(row["sum"])

        if total_rows % (args.chunksize * 10) == 0:
            print(f"Processed {total_rows:,} records...", flush=True)

    if not valid_currency_records or not valid_time_records:
        parser.error("The dataset has no valid currency or timestamp records to analyze.")

    eligible_codes = [
        code
        for code, count in currency_counts.items()
        if code != "(missing)" and count >= MIN_CURRENCY_COUNT
    ]
    eligible_count = sum(currency_counts[code] for code in eligible_codes)
    eligible_flags = sum(currency_flags[code] for code in eligible_codes)
    eligible_baseline = eligible_flags / eligible_count if eligible_count else 0
    types = sorted(type_counts, key=lambda value: (TYPE_ORDER.index(value) if value in TYPE_ORDER else len(TYPE_ORDER), value))
    type_baselines = {
        kind: type_flags[kind] / type_counts[kind] if type_counts[kind] else 0
        for kind in types
    }

    plot_colors = {
        "font.family": "sans-serif",
        "font.sans-serif": ["Inter", "Arial", "DejaVu Sans"],
        "axes.edgecolor": "#cbd5e1",
        "axes.linewidth": 0.8,
        "axes.titleweight": "bold",
    }
    plt.rcParams.update(plot_colors)
    save_currency_chart(
        args.output_dir,
        currency_counts,
        currency_flags,
        eligible_baseline,
    )
    save_hourly_chart(
        args.output_dir,
        types,
        hourly_counts,
        hourly_flags,
        type_baselines,
    )

    currency_results = []
    for code in sorted(eligible_codes):
        count = currency_counts[code]
        flags = currency_flags[code]
        currency_results.append(
            {
                "currency": code,
                "records": count,
                "labelled_records": flags,
                "label_rate_pct": round(flags / count * 100, 5),
                "label_rate_per_10000": round(flags / count * 10_000, 3),
            }
        )
    currency_results.sort(key=lambda result: result["label_rate_per_10000"], reverse=True)

    type_results = {}
    for kind in types:
        peak_hour = max(
            range(24),
            key=lambda hour_value: (
                hourly_flags[kind][hour_value] / hourly_counts[kind][hour_value]
                if hourly_counts[kind][hour_value]
                else 0
            ),
        )
        peak_count = hourly_counts[kind][peak_hour]
        peak_flags = hourly_flags[kind][peak_hour]
        type_results[kind] = {
            "records": type_counts[kind],
            "labelled_records": type_flags[kind],
            "baseline_rate_pct": round(type_baselines[kind] * 100, 5),
            "baseline_rate_per_10000": round(type_baselines[kind] * 10_000, 3),
            "highest_hour": f"{peak_hour:02d}:00",
            "highest_hour_records": peak_count,
            "highest_hour_labelled_records": peak_flags,
            "highest_hour_rate_per_10000": round(
                peak_flags / peak_count * 10_000 if peak_count else 0,
                3,
            ),
        }

    report = {
        "total_records": total_rows,
        "currency_analysis": {
            "valid_currency_records": valid_currency_records,
            "missing_currency_records": missing_currency_records,
            "minimum_currency_group_size": MIN_CURRENCY_COUNT,
            "eligible_currency_count": len(eligible_codes),
            "eligible_records": eligible_count,
            "eligible_labelled_records": eligible_flags,
            "eligible_baseline_rate_pct": round(eligible_baseline * 100, 5),
            "eligible_baseline_rate_per_10000": round(eligible_baseline * 10_000, 3),
            "currencies": currency_results,
        },
        "hourly_analysis": {
            "timezone": args.timezone,
            "valid_timestamp_records": valid_time_records,
            "transaction_types": type_results,
        },
    }
    (args.output_dir / "dashboard_9.html").write_text(
        render_dashboard9(report),
        encoding="utf-8",
    )
    (args.output_dir / "daahboard_10.html").write_text(
        render_dashboard10(report),
        encoding="utf-8",
    )
    print("\nVerified Dashboard 9/10 summary:")
    print(json.dumps(report, indent=2))
    print(f"\nCharts saved under {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
