import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(8, 6))
fig.patch.set_facecolor('#f1f5f9')
ax.set_facecolor('white')

participants = np.arange(2, 13)
expected = 100 * (1 - np.power(0.95, participants - 1))
observed = [5.0, 9.9, 14.3, 18.5, 22.6, 26.8, 31.0, 33.2, 38.4, 41.8, 43.3]

ax.plot(participants, expected, label='Expected N rate (5% per segment)', color='#c7a056', linestyle='--', linewidth=2.5)
ax.plot(participants, observed, label='Observed N rate (approx.)', color='#267c67', marker='o', linewidth=2.5, markersize=6)
ax.set_title('Incomplete-path rate by participant count', fontsize=14, fontweight='bold', pad=14, color='#25343a')
ax.set_xlabel('Participants in route', fontweight='bold', color='#44515b')
ax.set_ylabel('Incomplete paths (%)', fontweight='bold', color='#44515b')
ax.set_ylim(0, 50)
ax.set_xticks(participants)
ax.grid(True, color='#e9eeed', linestyle='-', linewidth=1)
ax.legend(loc='upper left', frameon=True, facecolor='white')

plt.tight_layout()
plt.savefig('incomplete_path_chart.png', dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
plt.show()

import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(8, 6))
fig.patch.set_facecolor('#f1f5f9')
ax.set_facecolor('white')

labels = ['Observed · N minus Y: +111.74 s', 'Same participant mix · N minus Y: +0.44 s']
x = np.arange(len(labels))
width = 0.35

y_continuous = [762.94, 771.49]
n_incomplete = [874.68, 771.93]

rects1 = ax.bar(x - width/2, y_continuous, width, label='Y · Continuous', color='#7cc2a5')
rects2 = ax.bar(x + width/2, n_incomplete, width, label='N · Incomplete', color='#df9aaa')

ax.set_title('MEAN DURATION BY PATH FLAG\n(Before and After Participant-Count Adjustment)', fontsize=12, fontweight='bold', pad=14, color='#096f54')
ax.set_ylabel('Mean duration (s)', fontweight='bold', color='#44515b')
ax.set_ylim(0, 1000)
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=10, color='#30383b')
ax.grid(True, color='#e9eeed', linestyle='-', linewidth=1, axis='y')
ax.legend(loc='upper right', frameon=True, facecolor='white')

for rects in [rects1, rects2]:
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.2f} s',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 6),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=10, fontweight='bold', color='#30383b')

plt.tight_layout()
plt.savefig('duration_comparison_chart.png', dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
plt.show()