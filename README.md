# Adaptive Cryptography for Resource-Constrained IoT using Q-Learning

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.15-blue.svg)](https://www.python.org/)
[![Cryptography](https://img.shields.io/badge/Cryptography-AEAD%20Standardized-green.svg)](https://cryptography.io/)
[![NIST](https://img.shields.io/badge/NIST-SP%20800--232%20KAT%20Verified-brightgreen.svg)](https://csrc.nist.gov/publications/detail/sp/800-232/final)
[![Tests](https://img.shields.io/badge/Tests-14%2F14%20Passing-success.svg)](file:///tests/)

Implementasi resmi arsitektur kriptografi adaptif berbasis **Reinforcement Learning (Q-Learning)** untuk perangkat _Internet of Things_ (IoT) dengan keterbatasan sumber daya. Sistem ini mengoptimalkan keseimbangan _trade-off_ multi-objektif antara **keamanan data** dan **konsumsi daya baterai** melalui pemilihan dinamis tiga algoritma _Authenticated Encryption with Associated Data_ (AEAD):

1. **AES-256-GCM** (NIST SP 800-38D): Keamanan tingkat tinggi untuk data kritikal.
2. **ChaCha20-Poly1305** (IETF RFC 8439): Efisiensi tinggi pada arsitektur tanpa akselerasi perangkat keras AES.
3. **Ascon-AEAD128** (NIST SP 800-232): Kriptografi berbobot sangat ringan (_lightweight_) untuk kondisi daya sekarat.

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
- [Panduan Pencarian Hyperparameter & Optimasi Model (`tune_model.py`)](#panduan-pencarian-hyperparameter--optimasi-model-tune_modelpy)
- [Representasi State & Metrik Matematis](#representasi-state--metrik-matematis)
  - [Ruang State (1.620 Status Diskret)](#ruang-state-1620-status-diskret)
  - [Formulasi WSM & Penanganan Unvisited States](#formulasi-wsm--penanganan-unvisited-states)
  - [Formulasi Dinamis SETOR](#formulasi-dinamis-setor)
- [Matriks Kebijakan 2D (Battery Decile x Threat Level)](#matriks-kebijakan-2d-battery-decile-x-threat-level)
- [Audit File Duplikat & Rekomendasi Pembersihan](#audit-file-duplikat--rekomendasi-pembersihan)

---

## Ringkasan Hasil Eksperimen

Sistem dievaluasi pada 500 episode pengurasan baterai penuh (100% hingga 0%) menggunakan kebijakan *greedy* ($\epsilon=0$). Tersedia dua lingkungan evaluasi:
1. **Lingkungan Terkalibrasi Benchmark (Ground Truth AEAD):** Menggunakan angka pemrosesan CPU riil dari OpenSSL/C (`benchmark_raw_results.json`) dan tag autentikasi standar 16-byte (tanpa penalti Base64).
2. **Lingkungan Simulasi Historis Legacy:** Menggunakan asumsi konstanta awal skripsi untuk pembuktian integritas dan reproduksibilitas naskah.

### 1. Hasil Evaluasi Terkalibrasi Benchmark (`--env calibrated`)

| Kandidat / Kebijakan | Tipe | Pesan Terkirim ($N$) $\uparrow$ | Total Skor Keamanan $\uparrow$ | WSM ($|\mathcal{S}|=1.620$) | WSM (Visited) | State Coverage | SETOR (Skor/%) $\uparrow$ | Rerata Reward Evaluasi $\uparrow$ | Proporsi Aksi Trace (AES / Cha / ASC) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Best Tuned Model (`best_tuned_model.pkl`)** | **RL** | **106.8 ± 4.6** | **90.1 ± 4.3** | **0.8380** | **0.8323** | **1565/1620 (96.6%)** | **0.9013 ± 0.0434** | **8909.8 ± 428.3** | **50.2% / 47.8% / 2.1%** |
| Final Model (`final_model.pkl`) | RL | 67.7 ± 4.6 | 38.0 ± 3.7 | 0.6257 | 0.6253 | 1618/1620 (99.9%) | 0.3803 ± 0.0372 | 3187.2 ± 431.9 | 9.2% / 35.4% / 55.4% |
| Initial Model (`initial_model.pkl`) | RL | 61.8 ± 4.1 | 34.2 ± 3.5 | 0.6548 | 0.6509 | 1602/1620 (98.9%) | 0.3420 ± 0.0351 | 2546.6 ± 368.4 | 17.9% / 15.3% / 66.8% |
| Model 2 (`agent_brain2.pkl`) | RL | 66.1 ± 4.5 | 38.4 ± 3.9 | 0.6343 | 0.6343 | 1620/1620 (100.0%) | 0.3838 ± 0.0385 | 3093.0 ± 420.0 | 17.9% / 24.3% / 57.8% |
| Model 3 (`agent_brain3.pkl`) | RL | 56.7 ± 3.4 | 27.7 ± 2.6 | 0.5650 | 0.5631 | 1613/1620 (99.6%) | 0.2767 ± 0.0262 | 1773.9 ± 266.0 | 12.1% / 5.3% / 82.6% |
| Model 4 (`agent_brain4.pkl`) | RL | 66.4 ± 4.6 | 38.1 ± 4.0 | 0.6317 | 0.6280 | 1604/1620 (99.0%) | 0.3812 ± 0.0405 | 3110.5 ± 450.6 | 14.4% / 29.2% / 56.4% |
| *Baseline 1: Static AES-256* | Base | 105.7 ± 4.2 | 105.7 ± 4.2 | 1.0000 | 1.0000 | 1620/1620 (100.0%) | 1.0572 ± 0.0418 | 9511.0 ± 395.4 | 100.0% / 0.0% / 0.0% |
| *Baseline 2: Static ChaCha20* | Base | 110.6 ± 4.3 | 77.4 ± 3.0 | 0.7000 | 0.7000 | 1620/1620 (100.0%) | 0.7742 ± 0.0304 | 8708.2 ± 361.9 | 0.0% / 100.0% / 0.0% |
| *Baseline 3: Static ASCON* | Base | 51.3 ± 3.0 | 20.5 ± 1.2 | 0.4000 | 0.4000 | 1620/1620 (100.0%) | 0.2052 ± 0.0122 | 1008.6 ± 90.0 | 0.0% / 0.0% / 100.0% |
| *Baseline 4: Threshold Heuristic* | Base | 97.2 ± 4.1 | 77.7 ± 3.4 | 0.7600 | 0.7600 | 1620/1620 (100.0%) | 0.7766 ± 0.0340 | 7537.0 ± 351.3 | 43.9% / 45.2% / 10.9% |
| *Baseline 5: Uniform Random* | Base | 79.5 ± 4.8 | 56.0 ± 4.8 | 0.7000 | 0.7000 | 1620/1620 (100.0%) | 0.5595 ± 0.0480 | 5029.5 ± 512.3 | 33.9% / 33.5% / 32.7% |

> [!TIP]
> **Keunggulan Best Tuned Model:**
> Pada lingkungan terkalibrasi benchmark nyata, **Best Tuned Model mengungguli Static ChaCha20 pada rasio SETOR (0.9013 vs 0.7742, +16.4%) dan Cumulative Reward (8909.8 vs 8708.2)** dengan selisih masa pakai pesan yang sangat kecil (106.8 vs 110.6 pesan), sembari memberikan **50.2% enkripsi AES-256 tingkat tinggi** yang tidak dimiliki Static ChaCha20.

### 2. Hasil Evaluasi Simulasi Historis Legacy (`--env legacy`)

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
├── tune_model.py                        # Automated Grid Search & hyperparameter tuning suite
├── test.py                              # Skrip uji 6 skenario kanonikal legacy
├── tuning_results/                      # Hasil Log Tuning & Leaderboard Hyperparameter
│   └── tuning_leaderboard.csv           # Papan peringkat seluruh kandidat tuning
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

Mengukur performa eksekusi CPU murni dari tiga algoritma AEAD dengan tag autentikasi 16 byte dan _Associated Data_ (AD) 33 byte menggunakan protokol **batch-trial** (50 sampel independen, 100 iterasi _warmup_ dieliminasi):

```powershell
python benchmark.py
```

Data mentah latensi dan _median-derived throughput_ (desimal MB/s dan biner MiB/s) untuk payload 32 B, 128 B, 1 KB, dan 4 KB akan diekspor ke `benchmark_raw_results.json`.

> [!NOTE]
> **Pernyataan Penyangkalan Daya (_Energy Disclaimer_):**
> Latensi dan throughput pada benchmark CPU host **bukan bukti langsung penghematan daya fisik baterai**. Dinamika konsumsi energi pada mikrokontroler IoT dipengaruhi oleh siklus radio, transmisi data, dan _sleep mode_, yang dimodelkan secara terpisah dalam lingkungan MDP.

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

Menjalankan 6 kasus uji kanonikal (_survival_, _efficiency_, _heavy_load_, _weak_signal_tax_, _lowest_need_, _critical_) menggunakan _compatibility shim_ pada folder `Agent/`:

```powershell
python test.py
```

---

## Panduan Training Model Baru (`train.py`)

Pipeline training pada `train.py` telah diperbarui dengan fitur keselamatan (_safety guard_) untuk mencegah penimpaan file model historis secara tidak sengaja.

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

## Panduan Pencarian Hyperparameter & Optimasi Model (`tune_model.py`)

Skrip `tune_model.py` adalah rangkaian pengujian otomatis (_automated grid search & hyperparameter tuning suite_) yang dirancang untuk mencari model agen Q-Learning terbaik yang mampu menandingi atau melampaui efisiensi _Static ChaCha20_ pada metrik masa pakai pesan ($N$) dan rasio efisiensi keamanan **SETOR**, sembari tetap mempertahankan adaptivitas keamanan penuh pada ancaman tinggi.

### Latar Belakang & Rasional Ilmiah

Pada baseline evaluasi awal, _Static ChaCha20_ menghasilkan rata-rata 118.3 pesan karena memiliki transmisi fisik paling hemat daya. Sebaliknya, model RL historis (`final_model.pkl`) menghasilkan 106.4 pesan karena bias terhadap Ascon (56% pemilihan aksi) akibat bobot reward teoritis legacy, padahal transmisi radio Ascon memakan energi $1.53\times$ lebih besar. Melalui `tune_model.py`, agen dilatih ulang dengan variasi hyperparameter dan penyesuaian fungsi reward agar mengenali keunggulan efisiensi fisik transmisi.

### 3 Rezim Reward Tuning (`--mode`)

1. **`--mode legacy`**: Menggunakan formula reward historis asli, mencari pasangan $(\alpha, \gamma)$ optimal dengan $\gamma \ge 0.99$ agar agen berorientasi pada ketahanan jangka panjang.
2. **`--mode aligned`**: Menyelaraskan efisiensi reward ($E_{\text{ChaCha}}=0.90, E_{\text{ASCON}}=0.80$) sesuai temuan konsumsi energi transmisi fisik nyata pada modul radio IoT.
3. **`--mode survival`**: Memberikan insentif bertahan hidup tambahan (_survival step bonus_, default: $+0.5$ hingga $+1.0$) per pesan terkirim untuk memotivasi agen memperpanjang masa aktif baterai.

### Pemeringkatan Pareto Multi-Objektif

Setiap kandidat dievaluasi secara otomatis pada 200 episode simulasi dan diberi peringkat berdasarkan skor multi-objektif Pareto:
$$\text{Score} = 0.35 \times \frac{N}{118.3} + 0.35 \times \frac{\text{SETOR}}{0.8281} + 0.30 \times \frac{\% \text{AES}_{\text{High Threat}}}{35\%}$$
Formula ini memastikan model yang menang tidak hanya awet baterai, tetapi juga secara cerdas menaikkan enkripsi AES-256 saat kondisi ancaman tinggi (`Threat = Tinggi / 2`).

### Contoh Perintah Eksekusi

```powershell
# 1. Melihat bantuan dan seluruh opsi argumen CLI
python tune_model.py --help

# 2. Uji Cepat (Fast Sweep, 4 kombinasi alpha x gamma, 5.000 episode, ~15-20 detik)
python tune_model.py --fast --mode aligned

# 3. Pencarian Penuh (Full Grid Search, 20 kombinasi alpha x gamma, 10.000 episode per trial)
python tune_model.py --mode aligned --episodes 10000 --output best_aligned_model.pkl

# 4. Mode Survival Longevity (Memaksimalkan masa pakai baterai dengan bonus bertahan hidup)
python tune_model.py --mode survival --survival-bonus 1.0 --episodes 10000 --output best_survival_model.pkl
```

### Hasil & Rekam Jejak

- **Penyimpanan Model**: Model dengan skor Pareto tertinggi secara otomatis disimpan ke file pickle baru (default: `best_tuned_model.pkl`).
- **Papan Peringkat (Leaderboard)**: Tabel peringkat lengkap seluruh kandidat diekspor ke file CSV:
  ```text
  tuning_results/tuning_leaderboard.csv
  ```

> [!IMPORTANT]
> **Jaminan Keamanan Model Asli:**
> `tune_model.py` melakukan verifikasi hash SHA-256 terhadap seluruh berkas model historis (`final_model.pkl`, `initial_model.pkl`, `agent_brain2.pkl`, `agent_brain3.pkl`, `agent_brain4.pkl`) sebelum dan sesudah eksekusi. Sistem secara otomatis menolak apabila output diarahkan ke nama file model lama demi menjaga integritas data penelitian.

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

Metrik _Weighted Sum Model_ (WSM) mengukur rata-rata tingkat keamanan dari kebijakan _greedy_:

- Bobot keamanan: $S(\text{AES-256}) = 1.0$, $S(\text{ChaCha20}) = 0.7$, $S(\text{ASCON}) = 0.4$.

1. **WSM Seluruh Status ($\text{WSM}_{1620}$):**
   $$\text{WSM}_{1620} = \frac{N_{\text{AES}} \times 1.0 + N_{\text{ChaCha}} \times 0.7 + N_{\text{ASCON}} \times 0.4}{1.620}$$
   Untuk 2 status yang tidak pernah dikunjungi pada `final_model.pkl` ($(1, 1, 4, 2, 2, 1)$ dan $(1, 1, 4, 2, 2, 2)$), sistem menggunakan kebijakan _fail-secure_ bawaan `'AES-256'`, menghasilkan $\text{WSM}_{1620} = \mathbf{0.6257}$.
2. **WSM Status yang Dikunjungi ($\text{WSM}_{\text{visited}}$):**
   $$\text{WSM}_{\text{visited}} = \frac{358 \times 1.0 + 499 \times 0.7 + 761 \times 0.4}{1.618} = \frac{1011.7}{1.618} = \mathbf{0.6253}$$
   Nilai ini seragam di seluruh berkas CSV, JSON, dan naskah publikasi.

### Formulasi Dinamis SETOR

_Security-to-Energy Trade-Off Ratio_ (SETOR) mengukur efisiensi keamanan per unit persentase baterai:
$$\text{SETOR} = \begin{cases} \frac{\sum_{t=1}^N S(a_t)}{B_{\text{start}} - B_{\text{end}}}, & \text{jika } \Delta \text{Battery} > 0 \\ 0.0, & \text{jika } \Delta \text{Battery} \le 0 \end{cases}$$

- Pada simulasi pengurasan penuh: $B_{\text{start}} = 100.0\%$, $B_{\text{end}} = 0.0\%$, sehingga denominator bernilai konstan $100.0\%$.
- Pada pengujian parsial (_fixed-horizon_): denominator menghitung selisih baterai aktual yang terkonsumsi secara proporsional.
- Pada episode tanpa konsumsi daya: nilai SETOR secara aman diatur ke `0.0` (bebas pembagian dengan nol).

---

## Matriks Kebijakan 2D (Battery Decile x Threat Level)

Setiap sel mengagregasikan 54 variasi status (_network_, _signal_, _size_, _priority_) menjadi aksi mayoritas dan persentase pilihan `[AES% / ChaCha% / ASCON%]`:

| Desil Baterai       |    Rendah (Threat=0)    |    Sedang (Threat=1)     |      Tinggi (Threat=2)       |
| :------------------ | :---------------------: | :----------------------: | :--------------------------: |
| **90–100% (Bin 9)** | ASCON [24% / 35% / 41%] | ASCON [26% / 22% / 52%]  | **ASCON [35% / 20% / 44%]**  |
| **80–89% (Bin 8)**  | ASCON [30% / 31% / 39%] | ASCON [26% / 30% / 44%]  | **ChaCha [26% / 41% / 33%]** |
| **70–79% (Bin 7)**  | ASCON [26% / 24% / 50%] | ChaCha [19% / 41% / 41%] | **ASCON [26% / 30% / 44%]**  |
| **60–69% (Bin 6)**  | ASCON [20% / 31% / 48%] | ASCON [26% / 22% / 52%]  | **ASCON [26% / 33% / 41%]**  |
| **50–59% (Bin 5)**  | ASCON [20% / 31% / 48%] | ASCON [26% / 20% / 54%]  | **ASCON [28% / 33% / 39%]**  |
| **40–49% (Bin 4)**  | ASCON [22% / 24% / 54%] | ASCON [22% / 28% / 50%]  | **ASCON [19% / 39% / 43%]**  |
| **30–39% (Bin 3)**  | ASCON [28% / 22% / 50%] | ASCON [24% / 28% / 48%]  | **ChaCha [20% / 41% / 39%]** |
| **20–29% (Bin 2)**  | ASCON [20% / 26% / 54%] | ChaCha [15% / 43% / 43%] | **ASCON [19% / 35% / 46%]**  |
| **10–19% (Bin 1)**  | ASCON [17% / 37% / 46%] | ASCON [17% / 31% / 52%]  | **ASCON [24% / 26% / 50%]**  |
| **0–9% (Bin 0)**    | ASCON [ 6% / 43% / 52%] | ASCON [13% / 22% / 65%]  | **ASCON [19% / 33% / 48%]**  |

> [!NOTE]
> **Analisis Ilmiah Perilaku Ancaman Tinggi:**
> Pemilihan AES-256 pada ancaman tinggi saat baterai kritis (18.5%) meningkat lebih dari 3 kali lipat dibandingkan saat ancaman rendah (5.6%). Namun, model RL tidak menerapkan _hard constraint_ 100% AES karena formulasi reward linier tetap menyeimbangkan efisiensi energi (menggunakan Ascon dan ChaCha20) untuk menghindari penalti baterai habis (-500).

---
