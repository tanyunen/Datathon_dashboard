import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Inter', 'Arial', 'Helvetica']

# Standardized 3-Tier Color System
COLOR_OPERATIONAL = '#00875a'  # Mint Green: Operational & Human Errors
COLOR_TECHNICAL   = '#6db6d5'  # Sky Blue: Technical & Protocol Friction
COLOR_FRAUD       = '#f891a0'  # Coral/Rose: Malicious Cyber Fraud & Scams
COLOR_DARK        = '#0f172a'

# ==========================================
# CHART 1: ANOMALY & ERROR TYPE FREQUENCY
# ==========================================
fig, ax = plt.subplots(figsize=(10, 5.2), dpi=300)

anomaly_types = [
    'Fat Finger Mistake',
    'Duplicate Payment',
    'API Token / Metadata Error',
    'CEO Scam',
    'Account Replacement Scam',
    'Romance Scam'
]
counts = [14200, 8900, 9600, 1850, 3100, 4200]

bar_colors = [
    COLOR_OPERATIONAL, 
    COLOR_OPERATIONAL, 
    COLOR_TECHNICAL, 
    COLOR_FRAUD, 
    COLOR_FRAUD, 
    COLOR_FRAUD
]

bars = ax.barh(
    anomaly_types,
    counts,
    color=bar_colors,
    edgecolor='none',
    alpha=0.9,
    height=0.5
)

ax.set_xlabel('Total Incident Frequency (Transaction Count)', fontsize=11, color=COLOR_DARK, fontweight='600')
ax.set_title('Dashboard #8.1: Operational Errors, Token Mismatches & Targeted Scam Frequencies', fontsize=12.5, color=COLOR_DARK, fontweight='700', pad=15)
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: f'{int(x):,}'))
ax.grid(axis='x', linestyle='--', alpha=0.5, color='#cbd5e1')

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#cbd5e1')
ax.spines['bottom'].set_color('#cbd5e1')

plt.tight_layout()
plt.savefig('dashboard8_chart1_anomalies.png', dpi=300)
plt.close()

# ==========================================
# CHART 2: FINANCIAL RISK EXPOSURE BY CATEGORY
# ==========================================
fig, ax = plt.subplots(figsize=(10, 5.2), dpi=300)

categories = ['Fat Finger', 'Duplicate', 'Token Error', 'CEO Scam', 'Account Replace', 'Romance Scam']
risk_exposure_usd = [12.5, 28.4, 45.8, 89.5, 65.2, 34.1] # in Millions USD

bar_colors_2 = [
    COLOR_OPERATIONAL, 
    COLOR_OPERATIONAL, 
    COLOR_TECHNICAL, 
    COLOR_FRAUD, 
    COLOR_FRAUD, 
    COLOR_FRAUD
]

bars2 = ax.bar(
    categories,
    risk_exposure_usd,
    color=bar_colors_2,
    edgecolor='none',
    alpha=0.9,
    width=0.45
)

ax.set_ylabel('Total Financial Risk / Stalled Value ($M USD)', fontsize=11, color=COLOR_DARK, fontweight='600')
ax.set_xlabel('Exception, Token & Scam Classification', fontsize=11, color=COLOR_DARK, fontweight='600')
ax.set_title('Dashboard #8.2: Financial Capital Exposure & Stalled Liquidity by Category', fontsize=12.5, color=COLOR_DARK, fontweight='700', pad=15)
ax.grid(axis='y', linestyle='--', alpha=0.5, color='#cbd5e1')
ax.set_ylim(0, 100)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#cbd5e1')
ax.spines['bottom'].set_color('#cbd5e1')

plt.tight_layout()
plt.savefig('dashboard8_chart2_exposure.png', dpi=300)
plt.close()

print('✨ Successfully regenerated Dashboard #8 charts with CEO Scam included!')