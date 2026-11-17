import matplotlib.pyplot as plt
import seaborn as sns

# Set global font and style
plt.rcParams['font.sans-serif'] = 'Inter'
plt.rcParams['axes.edgecolor'] = '#cbd5e1'
plt.rcParams['axes.linewidth'] = 0.8

# Color Palette
mint_primary = "#036b49"
mint_light = "#3ba880"
slate_dark = '#0f172a'
bg_color = '#f8fafc'

# ==========================================
# CHART 1: Volume & Median Amount by Sender Type
# ==========================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5), facecolor=bg_color)
for ax in [ax1, ax2]:
    ax.set_facecolor('#ffffff')

# Subplot 1: Transaction Volume by Sender Type
senders = ['Business (B)', 'Consumer (C)']
volumes = [7874687, 2125313] # 78.75% vs 21.25%
bars1 = ax1.bar(senders, [v / 1e6 for v in volumes], color=[mint_primary, mint_light], width=0.5)
ax1.set_title('Transaction Volume (Millions)', fontsize=10, fontweight='bold', color=slate_dark)
ax1.set_ylabel('Millions of Transactions', fontsize=9, color=slate_dark)
#ax1.grid(axis='y', linestyle='--', alpha=0.5)
ax1.set_ylim(0, 9)

# Add data labels on top of bars
for bar in bars1:
    yval = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 0.2, f'{yval:.2f}M', ha='center', va='bottom', fontsize=9, fontweight='bold')

# Subplot 2: Median Transaction Amount ($)
medians = [5537.36, 772.62] # 7.17x difference
bars2 = ax2.bar(senders, medians, color=[mint_primary, mint_light], width=0.5)
ax2.set_title('Median Transaction Amount (USD)', fontsize=10, fontweight='bold', color=slate_dark)
ax2.set_ylabel('USD ($)', fontsize=9, color=slate_dark)
#ax2.grid(axis='y', linestyle='--', alpha=0.5)
ax2.set_ylim(0, 6500)

for bar in bars2:
    yval = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 150, f'${yval:,.2f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

plt.tight_layout()
plt.savefig('dashboard4_chart1_volume.png', dpi=300)
plt.close()


# ==========================================
# CHART 2: Transaction Volume by Party Pair
# ==========================================
fig, ax = plt.subplots(figsize=(10, 4.5), facecolor=bg_color)
ax.set_facecolor('#ffffff')

pairs = ['B → C\n(Payroll / Payouts)', 'B → B\n(Trade Finance)', 'C → C\n(Retail P2P)', 'C → B\n(Bills & Retail)']
pair_volumes = [5603692, 2270949, 1514768, 610605] # In absolute values

# Highlight B -> C with a distinct color to emphasize dominance
bar_colors = [mint_primary, mint_light, '#94a3b8', '#cbd5e1']
bars3 = ax.bar(pairs, [v / 1e6 for v in pair_volumes], color=bar_colors, width=0.55)

ax.set_title('Transaction Volume Density by Party-Pair Category', fontsize=11, fontweight='bold', color=slate_dark, pad=10)
ax.set_ylabel('Transaction Volume (Millions)', fontsize=9, color=slate_dark)
#ax.grid(axis='y', linestyle='--', alpha=0.5)
ax.set_ylim(0, 6.5)

# Value annotations
for bar in bars3:
    yval = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2.0, yval + 0.15, f'{yval:.2f}M', ha='center', va='bottom', fontsize=9, fontweight='bold')

# Callout annotation for B -> C dominance
ax.annotate('Dominant B → C Batch Flow\n(56.04% of Total Network)', 
            xy=(0, 5.6), xytext=(0.5, 6.0),
            arrowprops=dict(facecolor=slate_dark, arrowstyle='->', lw=1),
            fontsize=8.5, fontweight='bold', color=mint_primary)

plt.tight_layout()
plt.savefig('dashboard4_chart2_pairs.png', dpi=300)
plt.close()