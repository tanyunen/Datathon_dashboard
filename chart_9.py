import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Inter', 'Arial', 'Helvetica']

COLOR_DARK = '#0f172a'

# ==========================================
# CHART 1: DUAL-METRIC COMPARATIVE GROUPED BAR CHART
# (Grid lines removed)
# ==========================================
fig, ax = plt.subplots(figsize=(10, 5.2), dpi=300)

categories = [
    'JPY Zero-Decimal Traps',
    '2-Digit Right Shift (USD)',
    'Emerging Corridor (USD/MYR)',
    'KWD 3-Decimal Error',
    'Trailing Zero Omission'
]

frequency = [42, 68, 35, 24, 50] 
capital_risk = [62.4, 54.2, 45.6, 38.1, 28.5]

x = np.arange(len(categories))
width = 0.35

rects1 = ax.bar(x - width/2, frequency, width, label='Incident Volume (Hundreds)', color='#34d399', alpha=0.9)
rects2 = ax.bar(x + width/2, capital_risk, width, label='Capital Skew Risk (\$M USD)', color='#00875a', alpha=0.9)

ax.set_ylabel('Metric Magnitude (Count vs \$M USD)', fontsize=11, color=COLOR_DARK, fontweight='600')
ax.set_title('Frequency vs. Capital Skew Exposure by Currency Error', fontsize=12.5, color=COLOR_DARK, fontweight='700', pad=18)
ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=9, fontweight='600')
ax.legend(frameon=True, facecolor='#f8fafc', edgecolor='#cbd5e1', fontsize=9)

# Dotted grid lines removed for a clean look

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#cbd5e1')
ax.spines['bottom'].set_color('#cbd5e1')

plt.tight_layout()
plt.savefig('dashboard9_chart1_magnitude.png', dpi=300)
plt.close()

# ==========================================
# CHART 2: ERROR FREQUENCY BY OPERATIONAL STRESS WINDOW
# (Grid lines removed)
# ==========================================
fig, ax = plt.subplots(figsize=(10, 5.2), dpi=300)

time_windows = [
    'Morning Open\n(08:00 - 10:00)',
    'Midday Clearing\n(11:00 - 14:00)',
    'Late Afternoon\n(15:00 - 17:00)',
    'End-of-Day Batch\n(17:00 - 20:00)',
    'Night / Weekend\nClearing'
]
incident_counts = [2400, 3100, 5800, 8900, 1200]

bar_colors_2 = [
    '#a7f3d0', 
    '#34d399', 
    '#10b981', 
    '#006644', 
    '#cbd5e1'  
]

bars2 = ax.bar(
    time_windows,
    incident_counts,
    color=bar_colors_2,
    edgecolor='none',
    alpha=0.95,
    width=0.48
)

ax.set_ylabel('Total Typing Incident Frequency', fontsize=11, color=COLOR_DARK, fontweight='600')
ax.set_xlabel('Operational Stress Window & Time-of-Day', fontsize=11, color=COLOR_DARK, fontweight='600')
ax.set_title('Typing Error Frequency Across Operational Stress Windows', fontsize=12.5, color=COLOR_DARK, fontweight='700', pad=18)
plt.xticks(fontsize=9, fontweight='600')
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: f'{int(x):,}'))

# Dotted grid lines removed for a clean look

ax.set_ylim(0, 10000)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#cbd5e1')
ax.spines['bottom'].set_color('#cbd5e1')

plt.tight_layout()
plt.savefig('dashboard9_chart2_stress.png', dpi=300)
plt.close()

print('✨ Successfully generated clean, grid-free Dashboard #9 charts!')