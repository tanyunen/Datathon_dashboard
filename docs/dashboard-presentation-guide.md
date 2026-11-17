# SWIFT Datathon Dashboard Guide

This guide explains all 11 dashboards in everyday language and gives you a
short way to present each one. The dashboards analyze 10 million rows from a
synthetic (fictional) payment dataset. Say "in this dataset" when describing
results; these findings are not automatically true of the real SWIFT network.

## Export to PDF

From the dashboard hub, select **Convert all to PDF** to prepare a combined
PDF with all 11 dashboards, one per A3 landscape page. In the browser's print
dialog, choose **Save as PDF**. To save only the dashboard you are viewing,
select **Convert to PDF** in its navigation bar.

## A few terms to know

- **Sender / beneficiary:** the party sending / receiving a payment.
- **Business (B) / Consumer (C):** the two party categories used in the data.
- **Participant count:** the number of banks shown in a payment's route.
- **Direct / Indirect / Covered:** transaction-route categories in the dataset.
  Treat these as dataset labels; do not infer unrecorded settlement steps.
- **Path continuity:** `Y` means the recorded route is marked continuous;
  `N` means it is marked incomplete or discontinuous. `N` does not mean the
  payment failed.
- **FX conversion:** a currency exchange recorded for a payment.
- **Baseline:** the comparison group used to make a number easier to interpret.
- **Mean / median / P90:** the average / middle value / value at or below which
  90% of observations fall. A few very large values can pull the mean upward.
- **Anomaly label:** a label in the synthetic data, not a confirmed fraud case,
  loss, or operational incident.
- **Rate per 10,000:** a way to compare groups of different sizes. Always check
  the number of records behind a rate.
- **Spearman correlation:** a way to check whether two ranked measures tend
  to move together. It does not show that one causes the other.

## Dashboard 1 - Route Participants and Duration

[Open Dashboard 1](../dashboard1.html)

**What it shows:** The first chart compares average recorded duration for
payments with different numbers of banks in the route. The second chart shows
how many records are in each route-size group. The table and notes explain the
sample sizes and compare routes of different sizes.

**Simple explanation:** The largest groups have two or three participants:
8.65 million records, or 86.5% of the dataset. Average duration is 663 seconds
for two participants, 841 seconds for three, and 1,042 seconds for four. The
average generally increases in larger route groups, but those groups have fewer
records. The table groups routes with 4-8 participants together (1.34 million
records, with means from 1,042 to 1,834 seconds) and routes with 9-14
participants together (9,176 records). There are only 134 records at 13-14
participants and 21 records at 15 or more.

**Say this:** "In this dataset, payments with more recorded route participants
tend to have longer average durations. Most records have only two or three
participants, so the averages for the largest routes are based on much smaller
samples."

**Be careful:** This is an association, not proof that each extra bank adds a
fixed delay. Within three-participant routes, Covered has a lower mean than
Indirect (810 vs. 845 seconds) but a higher median (288 vs. 87 seconds). That
mean/median reversal is a reason not to claim one fixed Covered-settlement
overhead. Very long durations and differences in currency and route mix can
also affect the averages.

## Dashboard 2 - Transaction Type and Path Continuity

[Open Dashboard 2](../dashboard_2.html)

**What it shows:** One chart counts Direct, Indirect, and Covered records. The
other compares the share marked `Y` or `N` within each transaction type. A
table gives the exact counts.

**Simple explanation:** Direct is the largest group (63.23%), followed by
Indirect (32.61%) and Covered (4.16%). An incomplete-path flag appears in
4.99% of Direct records and about 12.3% of Indirect and Covered records. Across
the whole dataset, 767,204 records (7.67%) are marked `N`.

There are also exact structural patterns in this file: two participants
appears only with Direct; routes with three or more participants are Indirect
or Covered. The literal `...` path marker appears in all 767,204 `N` paths and
none of the 9,232,796 `Y` paths. For `Y` rows, the number of path segments
matches the participant count.

**Say this:** "The route labels and path flag have a strong structural pattern
in this synthetic file. An incomplete path is more common in Indirect and
Covered records, but the flag describes the recorded path, not whether the
payment succeeded."

**Be careful:** The transaction-type shares are shares of this dataset, not
SWIFT-wide market shares. The patterns do not explain why a path is incomplete
or prove a rejection, fraud, or compliance hold.

## Dashboard 3 - Route Observability and Duration

[Open Dashboard 3](../dashboard_3.html)

**What it shows:** One chart compares incomplete-path rates across route
sizes. The other compares average duration for continuous (`Y`) and incomplete
(`N`) paths. The table lists their counts and means.

**Simple explanation:** 92.33% of records are marked `Y`; 7.67% are marked
`N`. The mean duration is 762.94 seconds for `Y` and 874.68 seconds for `N`,
about 112 seconds higher for `N`. The `...` marker and segment-count checks
show that the path flag is closely tied to how the route text is recorded.

**Say this:** "Records marked as having an incomplete route have a higher
average duration in this dataset. That is a useful association to investigate,
but it does not tell us that an incomplete path caused the longer duration."

**Be careful:** Route size and transaction type can affect both path
completeness and duration. Compare similar routes before interpreting the
difference. High-participant groups have small samples. `N` does not mean
payment failure, settlement delay, or liquidity lockup.

## Dashboard 4 - Party Types and Payment Amounts

[Open Dashboard 4](../try4.html)

**What it shows:** The charts compare payment counts and median normalized
amounts by sender party type and by sender/beneficiary pair. A table lists the
four pair combinations: B -> B, B -> C, C -> B, and C -> C.

**Simple explanation:** Business senders account for 78.75% of records. Their
median amount is $5,537.36, compared with $772.62 for Consumer senders
(7.17 times higher). Business-to-Consumer (B -> C) is the largest pair at
56.04% of all records. The median for B -> B is $22,887.71, about 49.4 times
the C -> C median of $463.17.

**Say this:** "Business senders are common in this dataset, and the typical
amounts differ by party type. The most common route is Business to Consumer.
These are descriptive amount patterns, not evidence of why the payments were
made."

**Be careful:** Amounts are normalized to USD for comparison and are not
adjusted for currency or route. Do not conclude that B -> C means payroll,
payouts, or any particular purpose; the dataset does not establish that.

## Dashboard 5 - Text Structure and Identity Patterns

[Open Dashboard 5](../dashboard5.html)

**What it shows:** The charts compare text length and the number of detected
tokens in Business and Consumer descriptions. The table shows how often
different tokens (such as `first_name`, `business`, `city`, or `iban`) appear
in sender and beneficiary text. The findings and rules summarize the
comparisons.

**Simple explanation:** Consumer descriptions average 7.62 sender tokens,
compared with 6.79 for Business; beneficiary averages are 7.55 and 6.84.
Consumer records more often contain name tokens. The `business` token appears
in 85.38% of Business sender descriptions and 0% of Consumer sender
descriptions. Typical text length stays around 66-68 characters across the
groups.

The raw table shows different `iban` token percentages by party type. But BIC
country is a stronger signal: the marker is absent for US, Singapore, and
China BICs and appears in about 92% of German BICs. After comparing party
types within the same countries, the Business-Consumer gaps are only 0.47
percentage points for senders and 0.01 for beneficiaries.

**Say this:** "The text fields have different patterns for Business and
Consumer parties, especially around names and business words. However, the
apparent party-type difference in IBAN markers mostly disappears when we
compare within the same country. These are patterns in engineered text fields,
not proof of identity quality or valid IBANs."

**Be careful:** A token is a detected field or word marker, not a verified
identity fact. Country standardization helps separate country mix from party
type; the remaining small differences should not be treated as meaningful
without further testing.

## Dashboard 6 - Payment Currency and FX Conversion Count

[Open Dashboard 6](../dashboard6/dashboard6_version2.html)

**What it shows:** The table ranks currencies and shows what share of each
currency's payments has zero, one, or two-or-more recorded conversions. The
donut chart shows each currency's share of all payments. The analysis brief
compares currency usage with the share having two or more conversions.

**Simple explanation:** The dataset contains 155 currencies. EUR is the most
common (31.99%), followed by USD (17.03%); the five most common currencies
account for 69.47% of records, and all other currencies together make up
30.53%. For the 21 currencies with at least 50,000
records, more-used currencies tend to have a lower share of payments with
two-or-more FX steps (Spearman correlation -0.55). Across all 155 currencies,
there is no clear relationship (correlation +0.055).

Every row also satisfies the structural check that the number of recorded
conversions is no more than the participant count minus one. About 89.39% of
instructions use the sender country's usual currency; the other 10.61% is not
explained by the available columns.

**Say this:** "Currency use and conversion patterns vary. A relationship
appears when we focus on the 21 currencies with larger samples, but it does
not appear across all currencies. We also found no records that break the
conversion-count bound."

**Be careful:** In the correlation, each currency is one observation, not
each payment. Small currency groups can have unstable rates. The result does
not show that currency choice causes more or fewer conversions; route and
country mix may matter. The remaining non-home-currency choices may depend on
account or business details not present here.

## Dashboard 7 - FX Conversion Count and Duration

[Open Dashboard 7](<../dashboard7/dashboard7_slide(final).html>)

**What it shows:** The first chart compares median duration for each exact
conversion count. The second shows what share of all payments has zero, one,
two, or more conversions. A table gives record counts, medians, and P90
durations for the most common groups.

**Simple explanation:** One recorded conversion is the most common group
(58.96%). The median duration is 41 seconds for one conversion and 181 seconds
for two. It is 47 seconds for zero, 453 seconds for three, and rises further
in the small high-conversion groups.

**Say this:** "The typical duration is higher for payments with two or more
recorded conversions than for payments with one. This is a raw comparison
across the whole dataset, not proof that conversions themselves caused the
difference."

**Be careful:** The chart combines different route sizes, transaction types,
currencies, and corridors. Compare like-for-like payments before making a
cause-and-effect claim. P90 describes the slower end of a group; estimates for
rare conversion counts are uncertain (only 109 records have exactly 11).

## Dashboard 8 - Anomaly Labels and Payment Amounts

[Open Dashboard 8](../dashboard_8.html)

**What it shows:** One chart counts six anomaly-label categories. The other
compares median normalized USD amounts for each category with records that
have none of the six displayed labels. The table shows each label's count and
median. The text also explores repeated-payment sequences and shared
beneficiaries.

**Simple explanation:** 7,006 of 10 million records (0.0701%) have one of the
displayed labels. Romance scam is the most frequent label (2,476 records).
Fat-finger-labelled records have the largest median amount:
$260,241.23, versus $3,662.58 for records without the displayed labels
(about 71 times higher). The six label counts are Romance Scam 2,476,
Fat-finger 1,940, CEO Scam 945, Duplicate Payment 679, Account Replacement
649, and Customer Recall 317.

The sequence checks add detail to the category counts. Of 1,976 linked
same-pair Romance Scam transitions, 1,920 (97.2%) happen within 18 minutes;
1,642 (83.1%) increase in normalized amount, and the median next/previous
amount ratio is 1.50. For Duplicate Payment, 494 linked transitions repeat the
same normalized amount; their median gap is 1,099 seconds, and 242 occur
within 18 minutes. Seven CEO Scam and three Account Replacement beneficiary
accounts each connect to at least seven distinct senders (maximum 10 and 13).
Most Fat-finger and all Customer Recall sender-beneficiary pairs occur only
once, so their trigger is not visible in these fields.

**Say this:** "The labelled groups differ in count, amount, and repeated
transaction patterns. Those patterns may help prioritize follow-up analysis,
but the labels are synthetic annotations and do not confirm real fraud or
loss."

**Be careful:** The baseline means records without these labels, not records
confirmed to be normal. Amount comparisons use normalized USD. Sequence
counts refer to linked transitions, so they can be fewer than the number of
labelled records. No balances, confirmed losses, or intervention outcomes are
available.

## Dashboard 9 - Anomaly-label Rates by Currency

[Open Dashboard 9](../dashboard_9.html)

**What it shows:** The main chart compares records with a listed anomaly label
per 10,000 payments for currencies with at least 50,000 records. A second
chart shows the sample size for each currency. The dashed line is the overall
rate for the eligible currencies.

**Simple explanation:** The eligible-currency baseline is 6.074 labelled
records per 10,000. INR has the highest observed rate:
87.954 per 10,000 (450 of 51,163 records), about 14.48 times the baseline.
The minimum sample-size rule avoids displaying very small currency groups
whose rates could swing sharply from a few records.

**Say this:** "The label rate differs across the larger currency groups, with
INR highest in this sample. That is a signal for checking the labels and
currency mix, not evidence that INR caused anomalies."

**Be careful:** Currency, route, amount, and transaction-type mixes are not
controlled here. Labels are not confirmed real-world incidents. Do not call
this a fraud-risk ranking.

## Dashboard 10 - Hourly Anomaly-label Rates

[Open Dashboard 10](../daahboard_10.html)

**What it shows:** One chart compares the hourly label rate with each
transaction type's own all-hour rate. The second chart shows the number of
records behind each hour/type rate. The table lists the highest observed hour
for each type.

**Simple explanation:** The highest type/hour cell is Indirect at 13:00:
108 labelled records out of 101,213, or 10.671 per 10,000. This is 1.41 times
the Indirect all-hour baseline. It is the highest of 72 comparisons, so it
may simply be an exploratory peak.

The other highest-hour cells are Direct at 10:00 (131 of 147,411; 8.887 per
10,000, or 1.28 times its baseline) and Covered at 10:00 (7 of 8,128; 8.612
per 10,000, or 2.44 times its baseline). Covered's rate is based on only
seven labels in that hour, so it is especially uncertain.

**Say this:** "We compared label rates within each transaction type and
included sample sizes. Indirect at 13:00 is the highest cell in this dataset,
but it needs confirmation before we treat it as a regular pattern."

**Be careful:** Hours use Malaysia time (Asia/Kuala_Lumpur), not the sender's
local time. The data has no sender time zone, clearing outcome, or queue
status. These are hourly label rates, not clearing windows or proof of staff
fatigue or settlement stress.

## Dashboard 11 - Transaction Traffic Over Time

[Open Dashboard 11](../dashboard11/dashboard11.html)

**What it shows:** Four charts compare hourly and daily record counts with
even-distribution reference lines, mean normalized payment amount by hour,
and mean observed duration by hour. A table and brief compare busy and quiet
periods with simple reference points.

**Simple explanation:** 23:00 is the busiest hour (585,888 records) and
11:00 the quietest (218,010). Friday has the most records (1,862,981) and
Sunday the fewest (552,588). The six busiest hours contain 32.77% of records,
compared with 25% if all hours were equally busy. Against the Monday-Friday
average of 1,705,507 records per day, Saturday is 46.1% lower and Sunday is
67.6% lower. The mean normalized payment amount is highest at 09:00
($159,855.58); mean duration also varies by hour.

**Say this:** "The timestamps in this dataset are not evenly distributed.
There are clear hourly and weekday differences, including lower weekend row
counts. These are patterns in the synthetic data, not measured delays in
payment clearing."

**Be careful:** Times are displayed in Malaysia time. There is no sender time
zone, queue, route-availability, settlement-window, or clearing-outcome
field. Do not describe the weekend changes as clearing delays or use these
numbers as a real-world staffing forecast.

## One-minute overall presentation

"We analyzed 10 million synthetic payment records across route structure,
party types, currencies, anomaly labels, and timing. We found exact patterns
in how route length, path markers, and recorded currency conversions fit
together. We also found differences in typical amounts, text tokens, anomaly
labels, and timestamp distributions. These are useful leads for further
analysis, but most are descriptive associations: the data does not prove why
they occur, confirm fraud, or describe real-world SWIFT clearing performance."

## Questions you may get

- **Does an incomplete path mean the payment failed?** No. It describes the
  recorded route; the dataset does not make that flag a payment-failure result.
- **Are the anomaly labels confirmed fraud?** No. They are labels in a
  synthetic dataset, not verified incidents or losses.
- **Do more banks or more FX conversions cause delays?** These dashboards show
  associations. Route, currency, transaction type, and other factors need to
  be controlled before making a causal claim.
- **Why compare rates instead of raw counts?** Rates make groups of different
  sizes easier to compare. The sample-size chart or record count should still
  be checked.
- **Can we infer real SWIFT behavior from the weekend pattern?** No. Times
  are in Malaysia time and sender-local time, queue, and clearing outcomes
  are not available.
