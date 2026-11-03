import matplotlib.pyplot as plt
import numpy as np
import os

os.makedirs('scratch/plots', exist_ok=True)
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['font.family'] = 'sans-serif'

# -----------------------------------------------------------------------------
# PLOT 1: Messages Sent vs Total Security (Smartphone Calibration Profile)
# -----------------------------------------------------------------------------
models = [
    'Best Smartphone (RL)',
    'Best Tuned PC (RL)',
    'Final Model (RL)',
    'Static AES-256',
    'Static ChaCha20',
    'Static Ascon',
    'Heuristic',
    'Random'
]
messages = [94.2, 82.8, 88.6, 71.1, 110.6, 80.7, 88.7, 84.6]
messages_err = [4.7, 4.5, 4.3, 3.7, 4.3, 3.8, 4.0, 3.9]
security = [72.6, 72.2, 49.7, 71.1, 77.4, 32.3, 65.8, 59.5]
security_err = [3.4, 3.5, 3.0, 3.7, 3.0, 1.5, 3.1, 3.2]

x = np.arange(len(models))
width = 0.35

fig, ax = plt.subplots(figsize=(11, 5.5), dpi=300)
rects1 = ax.bar(x - width/2, messages, width, yerr=messages_err, capsize=4, label='Kapasitas Pesan Simulasi (N)', color='#2b5c8f', edgecolor='black', alpha=0.9)
rects2 = ax.bar(x + width/2, security, width, yerr=security_err, capsize=4, label='Skor Keamanan Total', color='#d95f02', edgecolor='black', alpha=0.9)

ax.set_ylabel('Jumlah Pesan / Skor', fontsize=12, fontweight='bold')
ax.set_title('Kapasitas Pesan Simulasi dan Skor Keamanan Total pada Profil Smartphone\n(Software AES-256 2.2x, ChaCha20, Ascon-AEAD128)', fontsize=13, fontweight='bold', pad=15)
ax.set_xticks(x)
ax.set_xticklabels(models, rotation=25, ha='right', fontsize=9.5, fontweight='bold')
ax.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=10)
ax.grid(axis='y', linestyle='--', alpha=0.7)

for rect in rects1:
    h = rect.get_height()
    ax.annotate(f'{h:.1f}', xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 4), textcoords="offset points", ha='center', va='bottom', fontsize=8, fontweight='bold')

for rect in rects2:
    h = rect.get_height()
    ax.annotate(f'{h:.1f}', xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 4), textcoords="offset points", ha='center', va='bottom', fontsize=8, fontweight='bold')

plt.tight_layout()
plt.savefig('scratch/plots/plot1_smartphone_messages_security.png')
plt.close()
print("Plot 1 (Smartphone Messages vs Security) generated successfully.")

# -----------------------------------------------------------------------------
# PLOT 2: Action Distribution Trace (Smartphone Profile)
# -----------------------------------------------------------------------------
candidates = [
    'Best Smartphone RL',
    'Best Tuned PC RL',
    'Final Model RL',
    'Initial Model RL',
    'Model 2 RL',
    'Model 3 RL',
    'Model 4 RL',
    'Threshold Heuristic',
    'Uniform Random'
]
aes_pct = [28.5, 58.5, 9.2, 16.9, 16.9, 10.7, 14.1, 32.4, 33.9]
cha_pct = [66.7, 40.4, 35.0, 15.6, 24.6, 5.2, 29.4, 49.3, 33.5]
asc_pct = [4.8, 1.1, 55.7, 67.5, 58.5, 84.1, 56.5, 18.3, 32.7]

y = np.arange(len(candidates))
fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)

p1 = ax.barh(y, aes_pct, color='#1f77b4', edgecolor='black', alpha=0.9, label='AES-256-GCM', height=0.6)
p2 = ax.barh(y, cha_pct, left=aes_pct, color='#ff7f0e', edgecolor='black', alpha=0.9, label='ChaCha20-Poly1305', height=0.6)
p3 = ax.barh(y, asc_pct, left=np.array(aes_pct)+np.array(cha_pct), color='#2ca02c', edgecolor='black', alpha=0.9, label='Ascon-AEAD128', height=0.6)

ax.set_yticks(y)
ax.set_yticklabels(candidates, fontsize=10, fontweight='bold')
ax.set_xlabel('Distribusi Pemilihan Aksi Simulasi (%)', fontsize=12, fontweight='bold')
ax.set_title('Distribusi Pemilihan Algoritma Kriptografi pada Profil Smartphone', fontsize=13, fontweight='bold', pad=15)
ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.22), ncol=3, frameon=True, fontsize=10)
ax.set_xlim(0, 100)
ax.grid(axis='x', linestyle='--', alpha=0.7)

for i in range(len(candidates)):
    if aes_pct[i] > 8:
        ax.text(aes_pct[i]/2, i, f'{aes_pct[i]:.1f}%', ha='center', va='center', color='white', fontweight='bold', fontsize=8)
    if cha_pct[i] > 8:
        ax.text(aes_pct[i] + cha_pct[i]/2, i, f'{cha_pct[i]:.1f}%', ha='center', va='center', color='white', fontweight='bold', fontsize=8)
    if asc_pct[i] > 8:
        ax.text(aes_pct[i] + cha_pct[i] + asc_pct[i]/2, i, f'{asc_pct[i]:.1f}%', ha='center', va='center', color='white', fontweight='bold', fontsize=8)

plt.tight_layout()
plt.savefig('scratch/plots/plot2_smartphone_action_distribution.png')
plt.close()
print("Plot 2 (Smartphone Action Distribution) generated successfully.")

# -----------------------------------------------------------------------------
# PLOT 3: 2D Policy Heatmap (Best Smartphone Model)
# -----------------------------------------------------------------------------
matrix_phone = [
    [0, 0, 1], # Bin 9: AES, AES, Cha
    [1, 0, 0], # Bin 8: Cha, AES, AES
    [0, 0, 0], # Bin 7: AES, AES, AES
    [1, 0, 0], # Bin 6: Cha, AES, AES
    [1, 0, 0], # Bin 5: Cha, AES, AES
    [1, 1, 0], # Bin 4: Cha, Cha, AES
    [1, 0, 1], # Bin 3: Cha, AES, Cha
    [1, 1, 1], # Bin 2: Cha, Cha, Cha
    [1, 1, 0], # Bin 1: Cha, Cha, AES
    [1, 1, 1]  # Bin 0: Cha, Cha, Cha
]

labels_phone = [
    ["AES\n(52%)", "AES\n(48%)", "Cha\n(44%)"],
    ["Cha\n(57%)", "AES\n(52%)", "AES\n(44%)"],
    ["AES\n(52%)", "AES\n(54%)", "AES\n(43%)"],
    ["Cha\n(61%)", "AES\n(46%)", "AES\n(56%)"],
    ["Cha\n(48%)", "AES\n(44%)", "AES\n(56%)"],
    ["Cha\n(48%)", "Cha\n(43%)", "AES\n(56%)"],
    ["Cha\n(50%)", "AES\n(48%)", "Cha\n(48%)"],
    ["Cha\n(65%)", "Cha\n(54%)", "Cha\n(50%)"],
    ["Cha\n(63%)", "Cha\n(61%)", "AES\n(43%)"],
    ["Cha\n(61%)", "Cha\n(65%)", "Cha\n(61%)"]
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
threat_labels = ['Rendah (T=0)', 'Sedang (T=1)', 'Tinggi (T=2)']

from matplotlib.colors import ListedColormap
cmap = ListedColormap(['#1f77b4', '#ff7f0e', '#2ca02c']) # 0: Blue (AES), 1: Orange (Cha), 2: Green (Asc)

fig, ax = plt.subplots(figsize=(7.5, 6.5), dpi=300)
im = ax.imshow(matrix_phone, cmap=cmap, vmin=0, vmax=2, aspect='auto')

ax.set_title('Matriks Kebijakan 2D Best Smartphone Model (best_smartphone_model.pkl)\nDominasi ChaCha20 Hemat Daya & Seleksi AES pada Ancaman Tinggi', fontsize=11, fontweight='bold', pad=12)
ax.set_xticks(range(3))
ax.set_xticklabels(threat_labels, fontweight='bold', fontsize=10)
ax.set_yticks(range(10))
ax.set_yticklabels(battery_labels, fontweight='bold', fontsize=10)
ax.set_ylabel('Level Baterai (Desil)', fontsize=11, fontweight='bold')

for i in range(10):
    for j in range(3):
        ax.text(j, i, labels_phone[i][j], ha="center", va="center", color="white", fontweight='bold', fontsize=8.5)

import matplotlib.patches as mpatches
patch_aes = mpatches.Patch(color='#1f77b4', label='AES-256-GCM (Aksi 0)')
patch_cha = mpatches.Patch(color='#ff7f0e', label='ChaCha20-Poly1305 (Aksi 1)')
patch_asc = mpatches.Patch(color='#2ca02c', label='Ascon-AEAD128 (Aksi 2)')
ax.legend(handles=[patch_aes, patch_cha, patch_asc], loc='lower center', bbox_to_anchor=(0.5, -0.16), ncol=3, frameon=True, fontsize=9.5)

plt.tight_layout()
plt.subplots_adjust(bottom=0.15)
plt.savefig('scratch/plots/plot3_smartphone_policy_heatmap.png')
plt.close()
print("Plot 3 (Smartphone Policy Heatmap) generated successfully.")

# -----------------------------------------------------------------------------
# PLOT 4: Sensitivity Analysis (+/- 20% Energy Variation)
# -----------------------------------------------------------------------------
scenarios = ['Low Cost (-20%)', 'Nominal (k=1.0)', 'High Cost (+20%)']
n_phone = [117.2, 94.2, 78.4]
n_aes = [88.6, 71.1, 59.2]
n_cha = [138.2, 110.4, 92.2]
n_asc = [100.5, 80.5, 67.3]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.2), dpi=300)

x = np.arange(len(scenarios))
w = 0.2

ax1.bar(x - 1.5*w, n_phone, w, label='Best Smartphone RL', color='#2e7d32', edgecolor='black')
ax1.bar(x - 0.5*w, n_cha, w, label='Static ChaCha20', color='#ff7f0e', edgecolor='black')
ax1.bar(x + 0.5*w, n_asc, w, label='Static Ascon', color='#2ca02c', edgecolor='black')
ax1.bar(x + 1.5*w, n_aes, w, label='Static AES-256', color='#1f77b4', edgecolor='black')

ax1.set_ylabel('Kapasitas Pesan Simulasi (N)', fontsize=11, fontweight='bold')
ax1.set_title('(A) Kapasitas Pesan pada Variasi Parameter Energi (+/- 20%)', fontsize=11, fontweight='bold', pad=10)
ax1.set_xticks(x)
ax1.set_xticklabels(scenarios, fontsize=10, fontweight='bold')
ax1.legend(fontsize=9)
ax1.grid(axis='y', linestyle='--', alpha=0.7)

# SETOR Comparison
setor_phone = [0.9031, 0.7263, 0.6062]
setor_cha = [0.9672, 0.7731, 0.6453]
setor_aes = [0.8863, 0.7111, 0.5919]
setor_asc = [0.4022, 0.3222, 0.2691]

ax2.plot(scenarios, setor_phone, marker='o', linewidth=2.5, markersize=8, label='Best Smartphone RL', color='#2e7d32')
ax2.plot(scenarios, setor_cha, marker='s', linewidth=2, markersize=7, label='Static ChaCha20', color='#ff7f0e')
ax2.plot(scenarios, setor_aes, marker='^', linewidth=2, markersize=7, label='Static AES-256', color='#1f77b4')
ax2.plot(scenarios, setor_asc, marker='d', linewidth=2, markersize=7, label='Static Ascon', color='#2ca02c')

ax2.set_ylabel('Skor SETOR', fontsize=11, fontweight='bold')
ax2.set_title('(B) Kestabilan Skor SETOR pada Analisis Sensitivitas', fontsize=11, fontweight='bold', pad=10)
ax2.legend(fontsize=9)
ax2.grid(True, linestyle='--', alpha=0.7)

plt.tight_layout()
plt.savefig('scratch/plots/plot4_smartphone_sensitivity.png')
plt.close()
print("Plot 4 (Smartphone Sensitivity Analysis) generated successfully.")

