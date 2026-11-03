import matplotlib.pyplot as plt
import numpy as np
import os

os.makedirs('scratch/plots', exist_ok=True)
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['font.family'] = 'sans-serif'

# -----------------------------------------------------------------------------
# PLOT 1: Messages Sent vs Total Security (Calibrated Environment)
# -----------------------------------------------------------------------------
models = [
    'Best Tuned (RL)',
    'Final Model (RL)',
    'Static AES-256',
    'Static ChaCha20',
    'Static ASCON',
    'Heuristic',
    'Random'
]
messages = [106.9, 67.7, 105.7, 110.6, 51.3, 97.2, 79.5]
messages_err = [4.3, 4.6, 4.2, 4.3, 3.0, 4.1, 4.8]
security = [93.4, 38.0, 105.7, 77.4, 20.5, 77.7, 56.0]
security_err = [4.0, 3.7, 4.2, 3.0, 1.2, 3.4, 4.8]

x = np.arange(len(models))
width = 0.35

fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
rects1 = ax.bar(x - width/2, messages, width, yerr=messages_err, capsize=4, label='Messages Sent (N)', color='#2b5c8f', edgecolor='black', alpha=0.9)
rects2 = ax.bar(x + width/2, security, width, yerr=security_err, capsize=4, label='Total Security Score', color='#d95f02', edgecolor='black', alpha=0.9)

ax.set_ylabel('Skor / Jumlah Pesan', fontsize=12, fontweight='bold')
ax.set_title('Perbandingan Jumlah Pesan Terkirim (N) dan Skor Keamanan Total\n(Lingkungan Terkalibrasi Benchmark)', fontsize=13, fontweight='bold', pad=15)
ax.set_xticks(x)
ax.set_xticklabels(models, rotation=25, ha='right', fontsize=10, fontweight='bold')
ax.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=10)
ax.grid(axis='y', linestyle='--', alpha=0.7)

for rect in rects1:
    h = rect.get_height()
    ax.annotate(f'{h:.1f}', xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 4), textcoords="offset points", ha='center', va='bottom', fontsize=8, fontweight='bold')

for rect in rects2:
    h = rect.get_height()
    ax.annotate(f'{h:.1f}', xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 4), textcoords="offset points", ha='center', va='bottom', fontsize=8, fontweight='bold')

plt.tight_layout()
plt.savefig('scratch/plots/plot1_messages_security.png')
plt.close()
print("Plot 1 generated successfully.")

# -----------------------------------------------------------------------------
# PLOT 2: SETOR Score Comparison (Calibrated Environment)
# -----------------------------------------------------------------------------
setor_models = [
    'Static AES-256',
    'Best Tuned RL',
    'Threshold Heuristic',
    'Static ChaCha20',
    'Uniform Random',
    'Final Model (RL)',
    'Model 2 (RL)',
    'Model 4 (RL)',
    'Initial Model (RL)',
    'Model 3 (RL)',
    'Static ASCON'
]
setor_scores = [1.0572, 0.9341, 0.7766, 0.7742, 0.5595, 0.3803, 0.3838, 0.3812, 0.3420, 0.2767, 0.2052]
colors = ['#1f77b4', '#2ca02c', '#9467bd', '#ff7f0e', '#7f7f7f', '#d62728', '#8c564b', '#e377c2', '#bcbd22', '#17becf', '#8c564b']
# Make Best Tuned standout
colors = ['#4682b4' if m != 'Best Tuned RL' and m != 'Static ChaCha20' else ('#2e7d32' if m == 'Best Tuned RL' else '#d95f02') for m in setor_models]

fig, ax = plt.subplots(figsize=(11, 6), dpi=300)
bars = ax.barh(setor_models[::-1], setor_scores[::-1], color=colors[::-1], edgecolor='black', alpha=0.9, height=0.65)

ax.set_xlabel('Skor SETOR (Security-Energy Trade-Off Ratio)', fontsize=12, fontweight='bold')
ax.set_title('Peringkat Efisiensi SETOR Antar Model & Baseline\n(Lingkungan Terkalibrasi Benchmark)', fontsize=13, fontweight='bold', pad=15)
ax.grid(axis='x', linestyle='--', alpha=0.7)

for bar in bars:
    w = bar.get_width()
    ax.annotate(f'{w:.4f}', xy=(w, bar.get_y() + bar.get_height()/2), xytext=(5, 0), textcoords="offset points", ha='left', va='center', fontsize=9, fontweight='bold')

# Add callout for Best Tuned vs ChaCha
ax.annotate('Best Tuned RL (+20.7% vs ChaCha20)', xy=(0.9341, 9), xytext=(0.55, 6.5),
            arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=8),
            fontsize=10, fontweight='bold', color='#1b5e20',
            bbox=dict(boxstyle="round,pad=0.3", fc="#e8f5e9", ec="#2e7d32", lw=1.5))

plt.tight_layout()
plt.savefig('scratch/plots/plot2_setor_comparison.png')
plt.close()
print("Plot 2 generated successfully.")

# -----------------------------------------------------------------------------
# PLOT 3: Action Selection Distribution (Trace)
# -----------------------------------------------------------------------------
candidates = [
    'Best Tuned RL',
    'Final Model RL',
    'Initial Model RL',
    'Model 2 RL',
    'Model 3 RL',
    'Model 4 RL',
    'Threshold Heuristic',
    'Uniform Random'
]
aes_pct = [59.1, 9.2, 17.9, 17.9, 12.1, 14.4, 43.9, 33.9]
cha_pct = [39.9, 35.4, 15.3, 24.3, 5.3, 29.2, 45.2, 33.5]
asc_pct = [1.0, 55.4, 66.8, 57.8, 82.6, 56.4, 10.9, 32.7]

y = np.arange(len(candidates))
fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)

p1 = ax.barh(y, aes_pct, color='#1f77b4', edgecolor='black', alpha=0.9, label='AES-256-GCM', height=0.6)
p2 = ax.barh(y, cha_pct, left=aes_pct, color='#ff7f0e', edgecolor='black', alpha=0.9, label='ChaCha20-Poly1305', height=0.6)
p3 = ax.barh(y, asc_pct, left=np.array(aes_pct)+np.array(cha_pct), color='#2ca02c', edgecolor='black', alpha=0.9, label='ASCON-128a', height=0.6)

ax.set_yticks(y)
ax.set_yticklabels(candidates, fontsize=10, fontweight='bold')
ax.set_xlabel('Persentase Pemilihan Aksi (%)', fontsize=12, fontweight='bold')
ax.set_title('Distribusi Pemilihan Algoritma Kriptografi Selama Evaluasi Episode', fontsize=13, fontweight='bold', pad=15)
ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.22), ncol=3, frameon=True, fontsize=10)
ax.set_xlim(0, 100)
ax.grid(axis='x', linestyle='--', alpha=0.7)

for i in range(len(candidates)):
    # Annotate AES
    if aes_pct[i] > 10:
        ax.text(aes_pct[i]/2, i, f'{aes_pct[i]:.1f}%', ha='center', va='center', color='white', fontweight='bold', fontsize=8)
    # Annotate ChaCha
    if cha_pct[i] > 10:
        ax.text(aes_pct[i] + cha_pct[i]/2, i, f'{cha_pct[i]:.1f}%', ha='center', va='center', color='white', fontweight='bold', fontsize=8)
    # Annotate Ascon
    if asc_pct[i] > 10:
        ax.text(aes_pct[i] + cha_pct[i] + asc_pct[i]/2, i, f'{asc_pct[i]:.1f}%', ha='center', va='center', color='white', fontweight='bold', fontsize=8)

plt.tight_layout()
plt.savefig('scratch/plots/plot3_action_distribution.png')
plt.close()
print("Plot 3 generated successfully.")

# -----------------------------------------------------------------------------
# PLOT 4: Policy Matrix Heatmap (Final Model vs Best Tuned Model)
# -----------------------------------------------------------------------------
# 0 = AES, 1 = ChaCha, 2 = Ascon
# Let's map the dominant action in each cell
# Battery Bins 9 down to 0, Threat Low=0, Med=1, High=2
matrix_final = [
    [2, 2, 2], # Bin 9
    [2, 2, 1], # Bin 8
    [2, 1, 2], # Bin 7
    [2, 2, 2], # Bin 6
    [2, 2, 2], # Bin 5
    [2, 2, 2], # Bin 4
    [2, 2, 1], # Bin 3
    [2, 1, 2], # Bin 2
    [2, 2, 2], # Bin 1
    [2, 2, 2]  # Bin 0
]

matrix_tuned = [
    [0, 0, 0], # Bin 9
    [0, 0, 0], # Bin 8
    [0, 0, 0], # Bin 7
    [0, 0, 0], # Bin 6
    [0, 0, 0], # Bin 5
    [0, 0, 0], # Bin 4
    [0, 0, 0], # Bin 3
    [0, 0, 0], # Bin 2
    [1, 0, 1], # Bin 1 (Critical: ChaCha in Low & High)
    [0, 0, 1]  # Bin 0 (Critical: ChaCha in High)
]

labels_final = [
    ["ASC\n(41%)", "ASC\n(52%)", "ASC\n(44%)"],
    ["ASC\n(39%)", "ASC\n(44%)", "Cha\n(41%)"],
    ["ASC\n(50%)", "Cha\n(41%)", "ASC\n(44%)"],
    ["ASC\n(48%)", "ASC\n(52%)", "ASC\n(41%)"],
    ["ASC\n(48%)", "ASC\n(54%)", "ASC\n(39%)"],
    ["ASC\n(54%)", "ASC\n(50%)", "ASC\n(43%)"],
    ["ASC\n(50%)", "ASC\n(48%)", "Cha\n(41%)"],
    ["ASC\n(54%)", "Cha\n(43%)", "ASC\n(46%)"],
    ["ASC\n(46%)", "ASC\n(52%)", "ASC\n(50%)"],
    ["ASC\n(52%)", "ASC\n(65%)", "ASC\n(48%)"]
]

labels_tuned = [
    ["AES\n(69%)", "AES\n(61%)", "AES\n(72%)"],
    ["AES\n(65%)", "AES\n(61%)", "AES\n(67%)"],
    ["AES\n(54%)", "AES\n(65%)", "AES\n(69%)"],
    ["AES\n(67%)", "AES\n(57%)", "AES\n(69%)"],
    ["AES\n(59%)", "AES\n(67%)", "AES\n(69%)"],
    ["AES\n(50%)", "AES\n(72%)", "AES\n(78%)"],
    ["AES\n(48%)", "AES\n(56%)", "AES\n(69%)"],
    ["AES\n(54%)", "AES\n(57%)", "AES\n(67%)"],
    ["Cha\n(50%)", "AES\n(52%)", "Cha\n(44%)"],
    ["AES\n(54%)", "AES\n(56%)", "Cha\n(48%)"]
]

battery_labels = [
    '90-100% (Bin 9)',
    '80-89%  (Bin 8)',
    '70-79%  (Bin 7)',
    '60-69%  (Bin 6)',
    '50-59%  (Bin 5)',
    '40-49%  (Bin 4)',
    '30-39%  (Bin 3)',
    '20-29%  (Bin 2)',
    '10-19%  (Bin 1)',
    '0-9%    (Bin 0)'
]
threat_labels = ['Low Threat', 'Med Threat', 'High Threat']

from matplotlib.colors import ListedColormap
cmap = ListedColormap(['#1f77b4', '#ff7f0e', '#2ca02c']) # 0: Blue (AES), 1: Orange (Cha), 2: Green (Asc)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 7), dpi=300)

im1 = ax1.imshow(matrix_final, cmap=cmap, vmin=0, vmax=2, aspect='auto')
ax1.set_title('(A) Final Model (Historis Legacy)\nDominasi ASCON (Asumsi Lama)', fontsize=11, fontweight='bold', pad=10)
ax1.set_xticks(range(3))
ax1.set_xticklabels(threat_labels, fontweight='bold', fontsize=9)
ax1.set_yticks(range(10))
ax1.set_yticklabels(battery_labels, fontweight='bold', fontsize=9)
ax1.set_ylabel('Level Baterai (Desil)', fontsize=11, fontweight='bold')

for i in range(10):
    for j in range(3):
        ax1.text(j, i, labels_final[i][j], ha="center", va="center", color="white", fontweight='bold', fontsize=8)

im2 = ax2.imshow(matrix_tuned, cmap=cmap, vmin=0, vmax=2, aspect='auto')
ax2.set_title('(B) Best Tuned Model (Terkalibrasi)\nAdaptasi AES & ChaCha Baterai Kritis', fontsize=11, fontweight='bold', pad=10)
ax2.set_xticks(range(3))
ax2.set_xticklabels(threat_labels, fontweight='bold', fontsize=9)
ax2.set_yticks(range(10))
ax2.set_yticklabels(['']*10)

for i in range(10):
    for j in range(3):
        ax2.text(j, i, labels_tuned[i][j], ha="center", va="center", color="white", fontweight='bold', fontsize=8)

# Legend
import matplotlib.patches as mpatches
patch_aes = mpatches.Patch(color='#1f77b4', label='AES-256-GCM (Aksi 0)')
patch_cha = mpatches.Patch(color='#ff7f0e', label='ChaCha20-Poly1305 (Aksi 1)')
patch_asc = mpatches.Patch(color='#2ca02c', label='ASCON-128a (Aksi 2)')
fig.legend(handles=[patch_aes, patch_cha, patch_asc], loc='lower center', bbox_to_anchor=(0.5, -0.02), ncol=3, frameon=True, fontsize=10)

plt.tight_layout()
plt.subplots_adjust(bottom=0.1)
plt.savefig('scratch/plots/plot4_policy_heatmap.png')
plt.close()
print("Plot 4 generated successfully.")

# -----------------------------------------------------------------------------
# PLOT 5: Benchmark Latency & Throughput
# -----------------------------------------------------------------------------
payloads = ['32B (Small)', '128B (Med)', '1024B (Large)', '4096B (XLarge)']
aes_latency = [2.47, 1.59, 1.47, 4.82]
cha_latency = [2.24, 1.57, 1.81, 5.84]
asc_latency = [201.08, 335.37, 2705.90, 7148.53]

aes_thru = [12.94, 80.40, 694.45, 850.04]
cha_thru = [14.31, 81.35, 567.01, 700.97]
asc_thru = [0.16, 0.38, 0.38, 0.57]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), dpi=300)

x = np.arange(len(payloads))
w = 0.25

# Latency plot (log scale because Ascon is ~100x slower in pure Python)
ax1.bar(x - w, aes_latency, w, label='AES-256-GCM', color='#1f77b4', edgecolor='black')
ax1.bar(x, cha_latency, w, label='ChaCha20-Poly1305', color='#ff7f0e', edgecolor='black')
ax1.bar(x + w, asc_latency, w, label='ASCON-128a', color='#2ca02c', edgecolor='black')
ax1.set_yscale('log')
ax1.set_ylabel('Latensi Enkripsi (us) [Skala Log]', fontsize=11, fontweight='bold')
ax1.set_title('Perbandingan Latensi Enkripsi CPU', fontsize=12, fontweight='bold', pad=10)
ax1.set_xticks(x)
ax1.set_xticklabels(payloads, fontsize=9, fontweight='bold')
ax1.legend(fontsize=9)
ax1.grid(axis='y', linestyle='--', alpha=0.7)

# Throughput plot
ax2.bar(x - w, aes_thru, w, label='AES-256-GCM', color='#1f77b4', edgecolor='black')
ax2.bar(x, cha_thru, w, label='ChaCha20-Poly1305', color='#ff7f0e', edgecolor='black')
ax2.bar(x + w, asc_thru, w, label='ASCON-128a', color='#2ca02c', edgecolor='black')
ax2.set_ylabel('Throughput Enkripsi (MB/s)', fontsize=11, fontweight='bold')
ax2.set_title('Perbandingan Throughput CPU', fontsize=12, fontweight='bold', pad=10)
ax2.set_xticks(x)
ax2.set_xticklabels(payloads, fontsize=9, fontweight='bold')
ax2.legend(fontsize=9)
ax2.grid(axis='y', linestyle='--', alpha=0.7)

plt.tight_layout()
plt.savefig('scratch/plots/plot5_benchmark_performance.png')
plt.close()
print("Plot 5 generated successfully.")

