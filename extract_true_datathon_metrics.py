import os
import pandas as pd

# Make sure this matches your exact CSV filename
file_path = r'c:\Users\User\Downloads\swift_umdac_datathon_2026_fictitious_payment_data\swift_umdac_datathon_2026_fictitious_payment_data.csv'

print(
    '🚀 Running full analysis across the ENTIRE 83,806,704 rows. Please wait'
    ' until it finishes...'
)
chunk_size = 2_000_000  # Process in 2-million row batches for speed

total_rows = 0
msg_type_counts = {}
status_counts = {}
anomaly_counts = {}
hourly_congestion = {hour: 0 for hour in range(24)}

# This loop automatically reads until the end of the file (EOF)
for chunk_idx, chunk in enumerate(
    pd.read_csv(file_path, chunksize=chunk_size, low_memory=False, encoding='utf-8')
):
  total_rows += len(chunk)

  # 1. Transaction Type Distribution
  if 'TRANSACTION_TYPE_CODE' in chunk.columns:
    m_counts = chunk['TRANSACTION_TYPE_CODE'].value_counts().to_dict()
    for k, v in m_counts.items():
      msg_type_counts[k] = msg_type_counts.get(k, 0) + v

  # 2. Status / Continuity QFlag Distribution
  if 'CONTINUITY_QFLAG' in chunk.columns:
    s_counts = chunk['CONTINUITY_QFLAG'].value_counts().to_dict()
    for k, v in s_counts.items():
      status_counts[k] = status_counts.get(k, 0) + v

  # 3. Anomaly Type Distribution
  if 'ANOMALY_TYPE' in chunk.columns:
    a_counts = chunk['ANOMALY_TYPE'].value_counts().to_dict()
    for k, v in a_counts.items():
      anomaly_counts[k] = anomaly_counts.get(k, 0) + v

  # 4. Hourly Traffic Distribution (UTC via Epoch Seconds)
  if 'EPOCH_SECONDS' in chunk.columns:
    valid_epochs = pd.to_numeric(chunk['EPOCH_SECONDS'], errors='coerce')
    hours = ((valid_epochs // 3600) % 24).dropna().astype(int)
    h_counts = hours.value_counts().to_dict()
    for h, count in h_counts.items():
      hourly_congestion[h] = hourly_congestion.get(h, 0) + count

  print(
      f'   Processed batch {chunk_idx + 1} (Total rows scanned so far:'
      f' {total_rows:,})...'
  )

print('\n==================================================')
print('📊 FINAL 100% COMPLETE DATATHON RESULTS (ALL 83.8M ROWS)')
print('==================================================')
print(f'✅ Total Rows Scanned: {total_rows:,}')
print(f'✅ Transaction Types: {msg_type_counts}')
print(f'✅ Continuity QFlag Status: {status_counts}')
print(f'✅ Anomaly Types: {anomaly_counts}')
print(f'✅ Hourly Traffic Distribution (UTC): {hourly_congestion}')
print('==================================================')