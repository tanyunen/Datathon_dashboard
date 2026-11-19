import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Inter', 'Arial', 'Helvetica']

COLOR_DARK = '#0f172a'

# ==========================================
# CHART 10.1: HORIZONTAL CORRIDOR LIQUIDITY & FRICTION
# ==========================================
fig, ax = plt.subplots(figsize=(10, 5.2), dpi=300)

corridors = [
    'GBP / USD (Transatlantic)',
    'EUR / SGD (Euro-Asia)',
    'USD / THB (Mekong)',
    'USD / MYR (ASEAN)',
    'USD / JPY (North Asia)'
]

liquidity_deficit = [18.2, 29.1, 38.6, 45.2, 52.4] # in $M
routing_friction = [25, 45, 62, 74, 88]          # in ms delay

y = np.arange(len(corridors))
height = 0.35

rects1 = ax.barh(y - height/2, liquidity_deficit, height, label='Nostro Liquidity Deficit ($M)', color='#34d399', alpha=0.9)
rects2 = ax.barh(y + height/2, [f/1.5 for f in routing_friction], height, label='Routing Friction Score (Scaled)', color='#00875a', alpha=0.9)

ax.set_xlabel('Deficit Magnitude ($M) & Friction Index', fontsize=11, color=COLOR_DARK, fontweight='600')
ax.set_title('Cross-Border Corridor Liquidity Deficit & Routing Friction', fontsize=12.5, color=COLOR_DARK, fontweight='700', pad=18)
ax.set_yticks(y)
ax.set_yticklabels(corridors, fontsize=9.5, fontweight='600')
ax.legend(frameon=True, facecolor='#f8fafc', edgecolor='#cbd5e1', fontsize=9, loc='lower right')

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#cbd5e1')
ax.spines['bottom'].set_color('#cbd5e1')

plt.tight_layout()
plt.savefig('dashboard10_chart1_liquidity.png', dpi=300)
plt.close()

# ==========================================
# CHART 10.2: 24-HOUR MINT-GRADIENT AREA CHART (NOSTRO BUFFER)
# ==========================================
fig, ax = plt.subplots(figsize=(10, 5.2), dpi=300)

hours = ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00']
buffer_levels = [120, 160, 280, 390, 480, 310, 140] # $M

# Create smooth interpolated curve points for area filling
x_vals = np.linspace(0, len(hours)-1, 300)
y_vals = np.interp(x_vals, np.arange(len(hours)), buffer_levels)

ax.plot(x_vals, y_vals, color='#00875a', linewidth=3, label='Pre-Positioned Nostro Buffer ($M)')
ax.fill_between(x_vals, 0, y_vals, color='#34d399', alpha=0.3)

# Highlight peak window
ax.axvspan(4.0, 5.3, color='#e6f4ea', alpha=0.8, hatch='//', label='Peak Settlement Window (16:00-20:00 UTC)')

ax.set_ylabel('Pre-Positioned Buffer ($M USD)', fontsize=11, color=COLOR_DARK, fontweight='600')
ax.set_xlabel('Global Settlement Timeline (UTC)', fontsize=11, color=COLOR_DARK, fontweight='600')
ax.set_title('Dynamic Nostro Buffer Allocation Across 24-Hour Settlement Cycles', fontsize=12.5, color=COLOR_DARK, fontweight='700', pad=18)

ax.set_xticks(np.arange(len(hours)))
ax.set_xticklabels(hours, fontsize=9.5, fontweight='600')
ax.set_ylim(0, 550)
ax.legend(frameon=True, facecolor='#f8fafc', edgecolor='#cbd5e1', fontsize=9, loc='upper left')

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#cbd5e1')
ax.spines['bottom'].set_color('#cbd5e1')

plt.tight_layout()
plt.savefig('dashboard10_chart2_buffer.png', dpi=300)
plt.close()

print('✨ Updated Dashboard #10 charts generated successfully!')