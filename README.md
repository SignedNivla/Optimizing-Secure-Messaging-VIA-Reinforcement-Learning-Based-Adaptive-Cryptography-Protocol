# Adaptive Cryptography for Resource-Constrained IoT using Q-Learning

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.15-blue.svg)](https://www.python.org/)
[![Cryptography](https://img.shields.io/badge/Cryptography-AEAD%20Standardized-green.svg)](https://cryptography.io/)
[![NIST](https://img.shields.io/badge/NIST-SP%20800--232%20KAT%20Verified-brightgreen.svg)](https://csrc.nist.gov/publications/detail/sp/800-232/final)
[![Tests](https://img.shields.io/badge/Tests-14%2F14%20Passing-success.svg)](file:///tests/)

Implementasi resmi arsitektur kriptografi adaptif berbasis **Reinforcement Learning (Q-Learning)** untuk perangkat *Internet of Things* (IoT) dengan keterbatasan sumber daya. Sistem ini mengoptimalkan keseimbangan *trade-off* multi-objektif antara **keamanan data** dan **konsumsi daya baterai** melalui pemilihan dinamis tiga algoritma *Authenticated Encryption with Associated Data* (AEAD):

1. **AES-256-GCM** (NIST SP 800-38D): Keamanan tingkat tinggi untuk data kritikal.
2. **ChaCha20-Poly1305** (IETF RFC 8439): Efisiensi tinggi pada arsitektur tanpa akselerasi perangkat keras AES.
3. **Ascon-AEAD128** (NIST SP 800-232): Kriptografi berbobot sangat ringan (*lightweight*) untuk kondisi daya sekarat.

---

## Daftar Isi
- [Ringkasan Hasil Eksperimen](#ringkasan-hasil-eksperimen)
- [Struktur Repositori](#struktur-repositori)
- [Instalasi & Dependensi](#instalasi--dependensi)
- [Panduan Pengujian & Evaluasi](#panduan-pengujian--evaluasi)
  - [1. Evaluasi Komparatif Penuh (`evaluate.py`)](#1-evaluasi-komparatif-penuh-evaluatepy)
  - [2. Benchmark AEAD Presisi Tinggi (`benchmark.py`)](#2-benchmark-aead-presisi-tinggi-benchmarkpy)
  - [3. Pengujian Unit & Known-Answer Test NIST (`tests/`)](#3-pengujian-unit--known-answer-test-nist-tests)
  - [4. Pengujian Kompatibilitas Legacy (`test.py`)](#4-pengujian-kompatibilitas-legacy-testpy)
- [Panduan Training Model Baru (`train.py`)](#panduan-training-model-baru-trainpy)
- [Representasi State & Metrik Matematis](#representasi-state--metrik-matematis)
  - [Ruang State (1.620 Status Diskret)](#ruang-state-1620-status-diskret)
  - [Formulasi WSM & Penanganan Unvisited States](#formulasi-wsm--penanganan-unvisited-states)
  - [Formulasi Dinamis SETOR](#formulasi-dinamis-setor)
- [Matriks Kebijakan 2D (Battery Decile x Threat Level)](#matriks-kebijakan-2d-battery-decile-x-threat-level)
- [Audit File Duplikat & Rekomendasi Pembersihan](#audit-file-duplikat--rekomendasi-pembersihan)

---

## Ringkasan Hasil Eksperimen

Evaluasi dijalankan pada 500 episode pengurasan baterai penuh (100% hingga 0%) menggunakan kebijakan *greedy* ($\epsilon=0$):

| Kandidat / Kebijakan | Tipe | Pesan Terkirim ($N$) $\uparrow$ | Total Skor Keamanan $\uparrow$ | WSM ($|\mathcal{S}|=1.620$) | WSM (Visited) | State Coverage | SETOR (Skor/%) $\uparrow$ | Rerata Reward Evaluasi $\uparrow$ | Proporsi Aksi Trace (AES / Cha / ASC) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Final Model (`final_model.pkl`)** | **RL** | **106.4 ± 6.2** | **59.4 ± 3.2** | **0.6257** | **0.6253** | **1618/1620 (99.9%)** | **0.5944 ± 0.0324** | **6606.5 ± 435.6** | **8.9% / 35.1% / 56.0%** |
| Initial Model (`initial_model.pkl`) | RL | 98.4 ± 6.0 | 53.2 ± 2.9 | 0.6548 | 0.6509 | 1602/1620 (98.9%) | 0.5323 ± 0.0290 | 6321.7 ± 442.5 | 15.4% / 16.0% / 68.5% |
| Model 2 (`agent_brain2.pkl`) | RL | 98.0 ± 5.5 | 55.8 ± 2.9 | 0.6343 | 0.6343 | 1620/1620 (100.0%) | 0.5576 ± 0.0286 | 6102.8 ± 392.1 | 15.7% / 24.9% / 59.4% |
| Model 3 (`agent_brain3.pkl`) | RL | 104.4 ± 5.5 | 49.2 ± 2.3 | 0.5650 | 0.5631 | 1613/1620 (99.6%) | 0.4923 ± 0.0229 | 6953.7 ± 402.8 | 9.4% / 5.0% / 85.5% |
| Model 4 (`agent_brain4.pkl`) | RL | 101.3 ± 5.6 | 57.7 ± 3.1 | 0.6317 | 0.6280 | 1604/1620 (99.0%) | 0.5768 ± 0.0312 | 6351.5 ± 397.5 | 13.3% / 29.9% / 56.9% |
| *Baseline 1: Static AES-256* | Base | 51.3 ± 3.2 | 51.3 ± 3.2 | 1.0000 | 1.0000 | 1620/1620 (100.0%) | 0.5132 ± 0.0317 | 2457.7 ± 185.8 | 100.0% / 0.0% / 0.0% |
| *Baseline 2: Static ChaCha20* | Base | 118.3 ± 4.8 | 82.8 ± 3.4 | 0.7000 | 0.7000 | 1620/1620 (100.0%) | 0.8281 ± 0.0338 | 6526.5 ± 287.9 | 0.0% / 100.0% / 0.0% |
| *Baseline 3: Static ASCON* | Base | 116.7 ± 4.8 | 46.7 ± 1.9 | 0.4000 | 0.4000 | 1620/1620 (100.0%) | 0.4667 ± 0.0191 | 7880.1 ± 346.6 | 0.0% / 0.0% / 100.0% |
| *Baseline 4: Threshold Heuristic* | Base | 90.6 ± 4.2 | 62.7 ± 3.0 | 0.7600 | 0.7600 | 1620/1620 (100.0%) | 0.6274 ± 0.0300 | 5263.7 ± 268.2 | 23.2% / 51.2% / 25.6% |
| *Baseline 5: Uniform Random* | Base | 82.0 ± 5.5 | 57.7 ± 3.1 | 0.7000 | 0.7000 | 1620/1620 (100.0%) | 0.5770 ± 0.0308 | 4657.7 ± 376.0 | 33.9% / 33.4% / 32.7% |

### Temuan Kunci
1. **Peningkatan Ketersediaan (+107.2% vs Static AES-256):** Final Model mengirimkan rata-rata **106.4 pesan**, lebih dari 2 kali lipat dibandingkan kebijakan statis AES-256 yang mati setelah **51.3 pesan**.
2. **Peningkatan Masa Pakai & Reward (+8.1% & +4.5% vs Initial Model):** Optimasi kebijakan meningkatkan masa pakai dari 98.4 menjadi 106.4 pesan dan reward evaluasi dari 6321.7 menjadi 6606.5.
3. **ChaCha20 sebagai Jembatan Efisiensi:** Pada trace eksekusi baterai, porsi pemilihan ChaCha20 meningkat tajam dari **16.0%** (Initial) menjadi **35.1%** (Final), memberikan efisiensi optimal pada tingkat baterai menengah.

---

## Struktur Repositori

```text
├── core/                                # Paket Inti Terpadu (Modern Core Package)
│   ├── state.py                         # Representasi state diskret 6-tuple & diskritisasi
│   ├── agent.py                         # Watkins & Dayan QLearningAgent (pure keyword-only)
│   ├── environment.py                   # Enkapsulasi MDP IoT EncryptionEnvironment
│   ├── crypto.py                        # Standarisasi AEAD (AES-GCM, ChaCha20, Ascon-AEAD128)
│   ├── _ascon_nist.py                   # Referensi resmi NIST SP 800-232 Ascon-AEAD128
│   └── __init__.py
├── tests/                               # Rangkaian Pengujian Otomatis
│   ├── test_state.py                    # Uji diskritisasi seluruh 1.620 status (100% lulus)
│   ├── test_agent.py                    # Uji QLearningAgent & Watkins Q-update
│   ├── test_environment.py              # Uji reward & konsumsi baterai legacy
│   ├── test_crypto.py                   # Uji fungsionalitas AEAD & validasi tag 16-byte
│   ├── test_ascon_kat.py                # Known-Answer Test resmi NIST SP 800-232
│   └── checkpoint_reproducibility.py    # Uji paritas 30 kasus keputusan & Q-value
├── evaluation_results/                  # Hasil Evaluasi Terpadu
│   ├── baseline_comparison.csv          # Tabel evaluasi komparatif 5 model & 5 baseline
│   ├── policy_1620_states.csv           # Pemetaan aksi & Q-value untuk seluruh 1.620 state
│   ├── policy_matrix_final.csv          # Matriks 2D (Battery Decile x Threat) Final Model
│   ├── policy_matrix_initial.csv        # Matriks 2D (Battery Decile x Threat) Initial Model
│   └── evaluation_summary.json          # Metrik terstruktur JSON
├── legacy_archive/                      # Arsip Lengkap Kode Sumber Asli
│   ├── Agent/                           # Arsip modul Agent lama
│   ├── Benchmark/                       # Arsip modul benchmark lama
│   └── DeepLearningAgent/               # Arsip prototipe DQN
├── Agent/                               # Compatibility Shims (Mendukung skrip legacy)
│   ├── agent.py                         # Wrapper kelas QLearningAgent menuju core.agent
│   ├── encryption_environment.py        # Wrapper menuju core.environment
│   └── state_component.py               # Komponen diskritisasi legacy
├── evaluate.py                          # Skrip utama evaluasi komparatif terisolasi
├── benchmark.py                         # Skrip benchmark AEAD batch-trial presisi tinggi
├── train.py                             # Pipeline training Q-Learning modern dengan safety guard
├── test.py                              # Skrip uji 6 skenario kanonikal legacy
├── requirements.txt                     # Daftar dependensi Python
└── Adaptive_Cryptography_Revisions_Resolution.md  # Resolusi 32 butir revisi naskah
```

---

## Instalasi & Dependensi

Proyek ini membutuhkan Python 3.10 atau versi yang lebih baru (telah diuji pada Python 3.11 dan Python 3.15.2 di Windows 11).

```powershell
# 1. Pastikan virtual environment aktif (opsional namun direkomendasikan)
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2. Instal dependensi resmi
pip install -r requirements.txt
```

Dependensi utama:
- `cryptography >= 42.0.0`: Implementasi AES-256-GCM dan ChaCha20-Poly1305 berbasis C/OpenSSL.
- `ascon >= 0.0.9`: Pustaka dasar Ascon (didukung modul internal `core/_ascon_nist.py` untuk NIST SP 800-232).
- `pandas >= 2.0.0` & `numpy >= 1.24.0`: Pemrosesan matriks dan analisis data evaluasi.

---

## Panduan Pengujian & Evaluasi

### 1. Evaluasi Komparatif Penuh (`evaluate.py`)

Skrip ini mengevaluasi 5 model Q-table historis beserta 5 baseline pembanding dalam 500 episode pengurasan baterai penuh.

> [!IMPORTANT]
> Skrip ini **terisolasi secara ketat** dari modul kriptografi CPU (`core.crypto`) untuk menjamin validitas ilmiah model baterai legacy, serta memverifikasi hash SHA-256 seluruh file model sebelum dan sesudah eksekusi.

Jalankan evaluasi:
```powershell
python evaluate.py
```

Output terminal akan menampilkan:
1. Verifikasi SHA-256 pre-check model `.pkl`.
2. Hasil simulasi komparatif 5 model vs 5 baseline.
3. Matriks Kebijakan 2D (Battery Decile x Threat Level) untuk Final Model dan Initial Model.
4. Export file CSV dan JSON ke folder `evaluation_results/`.
5. Verifikasi SHA-256 post-check yang membuktikan bahwa seluruh file model tidak termutasi (`100% UNCHANGED`).

### 2. Benchmark AEAD Presisi Tinggi (`benchmark.py`)

Mengukur performa eksekusi CPU murni dari tiga algoritma AEAD dengan tag autentikasi 16 byte dan *Associated Data* (AD) 33 byte menggunakan protokol **batch-trial** (50 sampel independen, 100 iterasi *warmup* dieliminasi):

```powershell
python benchmark.py
```

Data mentah latensi dan *median-derived throughput* (desimal MB/s dan biner MiB/s) untuk payload 32 B, 128 B, 1 KB, dan 4 KB akan diekspor ke `benchmark_raw_results.json`.

> [!NOTE]
> **Pernyataan Penyangkalan Daya (*Energy Disclaimer*):**
> Latensi dan throughput pada benchmark CPU host **bukan bukti langsung penghematan daya fisik baterai**. Dinamika konsumsi energi pada mikrokontroler IoT dipengaruhi oleh siklus radio, transmisi data, dan *sleep mode*, yang dimodelkan secara terpisah dalam lingkungan MDP.

### 3. Pengujian Unit & Known-Answer Test NIST (`tests/`)

Jalankan seluruh 14 unit test regresi:
```powershell
python -m unittest discover tests
```

Untuk menjalankan pengujian spesifik Known-Answer Test (KAT) NIST SP 800-232 untuk Ascon-AEAD128:
```powershell
python -m unittest tests/test_ascon_kat.py
```

Untuk memverifikasi reproduksibilitas 100% antara model legacy dan paket `core/`:
```powershell
python tests/checkpoint_reproducibility.py
```

### 4. Pengujian Kompatibilitas Legacy (`test.py`)

Menjalankan 6 kasus uji kanonikal (*survival*, *efficiency*, *heavy_load*, *weak_signal_tax*, *lowest_need*, *critical*) menggunakan *compatibility shim* pada folder `Agent/`:

```powershell
python test.py
```

---

## Panduan Training Model Baru (`train.py`)

Pipeline training pada `train.py` telah diperbarui dengan fitur keselamatan (*safety guard*) untuk mencegah penimpaan file model historis secara tidak sengaja.

### Melihat Konfigurasi Tanpa Menjalankan Training (Aman)
```powershell
python train.py --help
python train.py --config final_model
```

### Melatih Model Baru dengan Parameter Eksplisit
```powershell
# Melatih agent baru dengan keyword arguments aman
python train.py --train --config final_model --episodes 10000 --output trained_experiment_v1.pkl

# Melatih dengan penyesuaian hyperparameter khusus
python train.py --train --alpha 0.15 --gamma 0.95 --epsilon 0.50 --episodes 15000 --output my_custom_model.pkl
```

> [!CAUTION]
> Skrip `train.py` akan **memblokir secara otomatis** jika Anda mengarahkan output ke nama file model historis (`final_model.pkl`, `initial_model.pkl`, dll.) demi melindungi validitas eksperimen.

---

## Representasi State & Metrik Matematis

### Ruang State (1.620 Status Diskret)
Status sistem IoT direpresentasikan sebagai 6-tuple bilangan bulat diskret:
$$s = (t, n, b, s, sz, p) \in \mathcal{S}, \quad |\mathcal{S}| = 3 \times 2 \times 10 \times 3 \times 3 \times 3 = 1.620$$

1. **Threat Level ($t \in \{0, 1, 2\}$):**
   - `0`: Rendah / Low (`value <= 1`)
   - `1`: Sedang / Medium (`1 < value <= 2`)
   - `2`: Tinggi / High (`value > 2`)
2. **Network Environment ($n \in \{0, 1\}$):**
   - `0`: Public (`'public'`)
   - `1`: Private (`'private'`)
3. **Battery Deciles ($b \in \{0, 1, \dots, 9\}$):**
   - Rentang 10%: `0` (0–9%) hingga `9` (90–100%).
4. **Signal Strength ($s \in \{0, 1, 2\}$):**
   - `0`: Lemah / Weak (`value <= 2`)
   - `1`: Sedang / Medium (`2 < value < 5`)
   - `2`: Kuat / Strong (`value == 5`)
5. **Payload Size ($sz \in \{0, 1, 2\}$):**
   - `0`: Kecil / Small (`< 50 B`)
   - `1`: Sedang / Medium (`50–249 B`)
   - `2`: Besar / Large (`>= 250 B`)
6. **Data Priority ($p \in \{0, 1, 2\}$):**
   - `0`: Rendah / Low (`value <= 1`)
   - `1`: Sedang / Medium (`1 < value <= 2`)
   - `2`: Tinggi / High (`value > 2`)

### Formulasi WSM & Penanganan Unvisited States
Metrik *Weighted Sum Model* (WSM) mengukur rata-rata tingkat keamanan dari kebijakan *greedy*:
- Bobot keamanan: $S(\text{AES-256}) = 1.0$, $S(\text{ChaCha20}) = 0.7$, $S(\text{ASCON}) = 0.4$.

1. **WSM Seluruh Status ($\text{WSM}_{1620}$):**
   $$\text{WSM}_{1620} = \frac{N_{\text{AES}} \times 1.0 + N_{\text{ChaCha}} \times 0.7 + N_{\text{ASCON}} \times 0.4}{1.620}$$
   Untuk 2 status yang tidak pernah dikunjungi pada `final_model.pkl` ($(1, 1, 4, 2, 2, 1)$ dan $(1, 1, 4, 2, 2, 2)$), sistem menggunakan kebijakan *fail-secure* bawaan `'AES-256'`, menghasilkan $\text{WSM}_{1620} = \mathbf{0.6257}$.
2. **WSM Status yang Dikunjungi ($\text{WSM}_{\text{visited}}$):**
   $$\text{WSM}_{\text{visited}} = \frac{358 \times 1.0 + 499 \times 0.7 + 761 \times 0.4}{1.618} = \frac{1011.7}{1.618} = \mathbf{0.6253}$$
   Nilai ini seragam di seluruh berkas CSV, JSON, dan naskah publikasi.

### Formulasi Dinamis SETOR
*Security-to-Energy Trade-Off Ratio* (SETOR) mengukur efisiensi keamanan per unit persentase baterai:
$$\text{SETOR} = \begin{cases} \frac{\sum_{t=1}^N S(a_t)}{B_{\text{start}} - B_{\text{end}}}, & \text{jika } \Delta \text{Battery} > 0 \\ 0.0, & \text{jika } \Delta \text{Battery} \le 0 \end{cases}$$

- Pada simulasi pengurasan penuh: $B_{\text{start}} = 100.0\%$, $B_{\text{end}} = 0.0\%$, sehingga denominator bernilai konstan $100.0\%$.
- Pada pengujian parsial (*fixed-horizon*): denominator menghitung selisih baterai aktual yang terkonsumsi secara proporsional.
- Pada episode tanpa konsumsi daya: nilai SETOR secara aman diatur ke `0.0` (bebas pembagian dengan nol).

---

## Matriks Kebijakan 2D (Battery Decile x Threat Level)

Setiap sel mengagregasikan 54 variasi status (*network*, *signal*, *size*, *priority*) menjadi aksi mayoritas dan persentase pilihan `[AES% / ChaCha% / ASCON%]`:

| Desil Baterai | Rendah (Threat=0) | Sedang (Threat=1) | Tinggi (Threat=2) |
| :--- | :---: | :---: | :---: |
| **90–100% (Bin 9)** | ASCON [24% / 35% / 41%] | ASCON [26% / 22% / 52%] | **ASCON [35% / 20% / 44%]** |
| **80–89%  (Bin 8)** | ASCON [30% / 31% / 39%] | ASCON [26% / 30% / 44%] | **ChaCha [26% / 41% / 33%]** |
| **70–79%  (Bin 7)** | ASCON [26% / 24% / 50%] | ChaCha [19% / 41% / 41%] | **ASCON [26% / 30% / 44%]** |
| **60–69%  (Bin 6)** | ASCON [20% / 31% / 48%] | ASCON [26% / 22% / 52%] | **ASCON [26% / 33% / 41%]** |
| **50–59%  (Bin 5)** | ASCON [20% / 31% / 48%] | ASCON [26% / 20% / 54%] | **ASCON [28% / 33% / 39%]** |
| **40–49%  (Bin 4)** | ASCON [22% / 24% / 54%] | ASCON [22% / 28% / 50%] | **ASCON [19% / 39% / 43%]** |
| **30–39%  (Bin 3)** | ASCON [28% / 22% / 50%] | ASCON [24% / 28% / 48%] | **ChaCha [20% / 41% / 39%]** |
| **20–29%  (Bin 2)** | ASCON [20% / 26% / 54%] | ChaCha [15% / 43% / 43%] | **ASCON [19% / 35% / 46%]** |
| **10–19%  (Bin 1)** | ASCON [17% / 37% / 46%] | ASCON [17% / 31% / 52%] | **ASCON [24% / 26% / 50%]** |
| **0–9%    (Bin 0)** | ASCON [ 6% / 43% / 52%] | ASCON [13% / 22% / 65%] | **ASCON [19% / 33% / 48%]** |

> [!NOTE]
> **Analisis Ilmiah Perilaku Ancaman Tinggi:**
> Pemilihan AES-256 pada ancaman tinggi saat baterai kritis (18.5%) meningkat lebih dari 3 kali lipat dibandingkan saat ancaman rendah (5.6%). Namun, model RL tidak menerapkan *hard constraint* 100% AES karena formulasi reward linier tetap menyeimbangkan efisiensi energi (menggunakan Ascon dan ChaCha20) untuk menghindari penalti baterai habis (-500).

---

## Audit File Duplikat & Rekomendasi Pembersihan

Berdasarkan audit arsitektur sistem pada Fase 6, berikut adalah inventaris berkas duplikat dan usang (*obsolete*) beserta status pengarsipannya:

| Nama File / Folder | Kategori | Alasan Redundansi | Tindakan Rekomendasi |
| :--- | :---: | :--- | :--- |
| `convert.py` | Skrip Utilitas | Skrip sederhana 13 baris untuk mengubah pickle ke CSV mentah tanpa label. Fungsinya telah disempurnakan oleh `evaluate.py`. | **Bisa Dihapus** (atau diarsipkan). |
| `initial_model.csv` & `final_model.csv` | File Data | Merupakan output mentah dari `convert.py`. Telah digantikan secara komprehensif oleh `evaluation_results/policy_1620_states.csv` yang memiliki label lengkap dan nilai Q. | **Bisa Dihapus**. |
| `Benchmark/` (folder root) | Modul Lama | Modul pengujian lama sebelum standarisasi AEAD. Seluruh isinya telah disalin aman ke `legacy_archive/Benchmark/`. | **Bisa Dihapus dari root** (karena sudah aman di arsip). |
| `DeepLearningAgent/` (folder root) | Prototipe | Berisi `dqn.py` (prototipe eksplorasi yang tidak digunakan dalam hasil skripsi). Sudah disalin ke `legacy_archive/DeepLearningAgent/`. | **Bisa Dihapus dari root**. |
| `Adaptive Cryptography Revisions (Copy).html` | File Referensi | Berisi komentar reviewer asli. Seluruh 32 butir revisi telah diselesaikan dan didokumentasikan di `Adaptive_Cryptography_Revisions_Resolution.md`. | **Bisa Dipindahkan ke Arsip**. |
| Cache `.pycache` & `*.cpython-311.pyc` | Cache Build | Berkas bytecode sisa Python 3.11 versi lama. | **Bisa Dibersihkan** (`clean`). |

*(Catatan: Folder `Agent/` dipertahankan di root sebagai compatibility shim agar skrip `test.py` bawaan tetap dapat berjalan langsung).*

