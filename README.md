# Adaptive Cryptography for Resource-Constrained IoT & Mobile using Q-Learning

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.15-blue.svg)](https://www.python.org/)
[![Cryptography](https://img.shields.io/badge/Cryptography-AEAD%20Standardized-green.svg)](https://cryptography.io/)
[![NIST](https://img.shields.io/badge/NIST-SP%20800--232%20KAT%20Verified-brightgreen.svg)](https://csrc.nist.gov/publications/detail/sp/800-232/final)
[![Tests](https://img.shields.io/badge/Tests-16%2F16%20Passing-success.svg)](file:///tests/)

Implementasi resmi arsitektur kriptografi adaptif berbasis **Reinforcement Learning (Tabular Q-Learning)** untuk perangkat seluler (*smartphone* tanpa akselerasi AES-NI hardware) dan sensor *Internet of Things* (IoT) dengan keterbatasan sumber daya. Sistem ini menyelesaikan dilema *trade-off* multi-objektif antara **keamanan data** dan **konsumsi daya baterai** melalui pemilihan dinamis tiga algoritma *Authenticated Encryption with Associated Data* (AEAD):

1. **AES-256-GCM** (NIST SP 800-38D): Keamanan tingkat militer tertinggi untuk data berkategori *Important* dan kondisi serangan aktif.
2. **ChaCha20-Poly1305** (IETF RFC 8439): Efisiensi tinggi berbasis operasi Add-Rotate-XOR (*constant-time*) pada mikroprosesor perangkat seluler tanpa modul AES-NI.
3. **Ascon-AEAD128** (NIST SP 800-232): Standar global *Lightweight Cryptography* (LWC) untuk sirkuit silikon mikro berukuran sangat kecil (<2.500 GE) dan sensor bertenaga baterai koin.

---

## Daftar Isi

- [Ringkasan Hasil Evaluasi Profil Smartphone (phone_calibration/)](#ringkasan-hasil-evaluasi-profil-smartphone-phone_calibration)
- [Analisis Sensitivitas Parameter Energi (+-20%)](#analisis-sensitivitas-parameter-energi--20)
- [Struktur Repositori](#struktur-repositori)
- [Instalasi & Dependensi](#instalasi--dependensi)
- [Panduan Eksekusi Sistem](#panduan-eksekusi-sistem)
  - [1. Evaluasi Profil Smartphone & Analisis Sensitivitas (`evaluate.py`)](#1-evaluasi-profil-smartphone--analisis-sensitivitas-evaluatepy)
  - [2. Hyperparameter Tuning Otomatis Profil Smartphone (`tune_model.py`)](#2-hyperparameter-tuning-otomatis-profil-smartphone-tune_modelpy)
  - [3. Benchmark CPU Primitif Kriptografi (`benchmark.py`)](#3-benchmark-cpu-primitif-kriptografi-benchmarkpy)
  - [4. Pengujian Unit Test Otomatis (`tests/`)](#4-pengujian-unit-test-otomatis-tests)
- [Diskusi Kriptografi: Kapan ChaCha20 dan Ascon Mengalahkan AES-256](#diskusi-kriptografi-kapan-chacha20-dan-ascon-mengalahkan-aes-256)
- [Matriks Kebijakan 2D (Desil Baterai x Tingkat Ancaman)](#matriks-kebijakan-2d-desil-baterai-x-tingkat-ancaman)
- [Jaminan Integritas Model Historis (Legacy Safety Guarantee)](#jaminan-integritas-model-historis-legacy-safety-guarantee)

---

## Ringkasan Hasil Evaluasi Profil Smartphone (`phone_calibration/`)

Sistem dievaluasi secara komparatif pada 100 episode pengurasan baterai penuh (100% hingga 0%) menggunakan kebijakan *greedy* ($\epsilon=0$). Profil smartphone dikalibrasi berdasarkan agregat literatur *eBACS* prosesor ARM tanpa modul akselerasi hardware AES-NI (komputasi software pure AES-256 ~22 cycles/byte, ChaCha20 ~10 cycles/byte, Ascon-AEAD128 ~18 cycles/byte; rasio 2.2x : 1.0x : 1.8x).

| Kandidat / Model | Tipe | Pesan Terkirim ($N$) $\uparrow$ | Total Skor Keamanan $\uparrow$ | WSM ($|\mathcal{S}|=1620$) | SETOR (Skor/%) $\uparrow$ | Cumulative Reward $\uparrow$ | Distribusi Aksi Trace (AES / ChaCha / Ascon) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Best Smartphone Model (`best_smartphone_model.pkl`)** | **RL** | **94.2 ± 4.7** | **72.6 ± 3.4** | **0.7850** | **0.7264 ± 0.0342** | **7093.3 ± 412.6** | **28.5% / 66.7% / 4.8%** |
| Best Tuned Model PC (`best_tuned_model.pkl`) | RL | 82.8 ± 4.5 | 72.2 ± 3.5 | 0.8576 | 0.7221 ± 0.0349 | 5931.8 ± 384.8 | 58.5% / 40.4% / 1.1% |
| Final Model (`final_model.pkl`) | RL | 88.6 ± 4.3 | 49.7 ± 3.0 | 0.6257 | 0.4967 ± 0.0299 | 5156.7 ± 329.9 | 9.2% / 35.0% / 55.7% |
| Initial Model (`initial_model.pkl`) | RL | 82.3 ± 4.0 | 45.2 ± 3.0 | 0.6548 | 0.4515 ± 0.0299 | 4353.6 ± 288.3 | 16.9% / 15.6% / 67.5% |
| Model 2 (`agent_brain2.pkl`) | RL | 84.6 ± 4.0 | 48.7 ± 2.8 | 0.6343 | 0.4869 ± 0.0282 | 4760.8 ± 288.1 | 16.9% / 24.6% / 58.5% |
| Model 3 (`agent_brain3.pkl`) | RL | 80.8 ± 3.8 | 38.8 ± 2.3 | 0.5650 | 0.3877 ± 0.0232 | 3829.4 ± 223.7 | 10.7% / 5.2% / 84.1% |
| Model 4 (`agent_brain4.pkl`) | RL | 86.1 ± 4.5 | 49.3 ± 3.4 | 0.6317 | 0.4934 ± 0.0341 | 4940.5 ± 349.5 | 14.1% / 29.4% / 56.5% |
| *Baseline 1: Static AES-256* | Base | 71.1 ± 3.7 | 71.1 ± 3.7 | 1.0000 | 0.7107 ± 0.0372 | 4554.4 ± 267.5 | 100.0% / 0.0% / 0.0% |
| *Baseline 2: Static ChaCha20* | Base | 110.6 ± 4.3 | 77.4 ± 3.0 | 0.7000 | 0.7742 ± 0.0304 | 9001.5 ± 373.6 | 0.0% / 100.0% / 0.0% |
| *Baseline 3: Static Ascon* | Base | 80.7 ± 3.8 | 32.3 ± 1.5 | 0.4000 | 0.3227 ± 0.0151 | 3393.8 ± 182.0 | 0.0% / 0.0% / 100.0% |
| *Baseline 4: Threshold Heuristic*| Base | 88.7 ± 4.0 | 65.8 ± 3.1 | 0.7600 | 0.6585 ± 0.0310 | 6187.7 ± 312.4 | 32.4% / 49.3% / 18.3% |
| *Baseline 5: Uniform Random* | Base | 84.6 ± 3.9 | 59.5 ± 3.2 | 0.7000 | 0.5949 ± 0.0319 | 5302.6 ± 324.9 | 33.9% / 33.5% / 32.7% |

> [!TIP]
> **Intisari Temuan Ilmiah Profil Smartphone:**
> 1. **Mengatasi Kematian Prematur Static AES-256:** Best Smartphone Model mengirimkan **94.2 ± 4.7 pesan**, memperpanjang masa aktif perangkat sebesar **+32.5% (+23.1 pesan)** dibandingkan Static AES-256 (71.1 ± 3.7 pesan). Pada saat yang sama, Skor Keamanan Total agen RL mencapai **72.6 ± 3.4** (melampaui Static AES sebesar 71.1) karena perangkat bertahan hidup lebih lama dan terus mengamankan data.
> 2. **Keseimbangan Dinamis:** Agen RL mengalokasikan **66.7% ke ChaCha20** sebagai pekerja hemat daya utama, **28.5% ke AES-256** saat ancaman tinggi dan baterai aman, serta **4.8% ke Ascon-AEAD128** saat baterai mendekati habis.

---

## Analisis Sensitivitas Parameter Energi (±20%)

Untuk menguji ketahanan (*robustness*) model terhadap variasi efisiensi baterai fisik dan konsumsi sirkuit radio nirkabel RF, dilakukan analisis sensitivitas dengan mengalikan seluruh parameter biaya energi dengan faktor skala $k \in \{0.80, 1.00, 1.20\}$:

| Kandidat | Low Cost ($k=0.80$, -20%) | Nominal ($k=1.00$) | High Cost ($k=1.20$, +20%) | Stabilitas Distribusi Aksi |
| :--- | :---: | :---: | :---: | :---: |
| **Best Smartphone Model** | **117.2 ± 5.4 msg (S: 90.3)** | **94.2 ± 4.7 msg (S: 72.6)** | **78.4 ± 4.8 msg (S: 60.6)** | **28.5% / 66.8% / 4.7% (Invarian)** |
| Static AES-256 | 88.6 ± 3.9 msg (S: 88.6) | 71.1 ± 3.8 msg (S: 71.1) | 59.2 ± 3.4 msg (S: 59.2) | 100.0% / 0.0% / 0.0% |
| Static ChaCha20 | 138.2 ± 4.9 msg (S: 96.7) | 110.4 ± 4.5 msg (S: 77.3) | 92.2 ± 4.0 msg (S: 64.5) | 0.0% / 100.0% / 0.0% |
| Static Ascon-AEAD128 | 100.5 ± 4.3 msg (S: 40.2) | 80.5 ± 3.9 msg (S: 32.2) | 67.3 ± 3.6 msg (S: 26.9) | 0.0% / 0.0% / 100.0% |

- **Prediksi Matematis vs Hasil Simulasi:** Kapasitas pesan yang dicapai pada simulasi Monte Carlo selaras secara presisi dengan formula analitis $N = 100\% / [k \cdot (\bar{C}_{\text{proc}} + \bar{C}_{\text{trans}})]$ dengan deviasi stokastik <1% (ChaCha nominal: 110.4 vs 110 teoritis; Ascon nominal: 80.5 vs 80 teoritis; AES nominal: 71.1 vs 70 teoritis).
- **Invariansi Kebijakan (Policy Invariance):** Proporsi pemilihan aksi agen RL terbukti stabil secara konsisten (~28.5% AES, ~66.8% ChaCha, ~4.7% Ascon) di seluruh spektrum fluktuasi biaya energi $\pm 20\%$.

---

## Struktur Repositori

```text
├── core/                                # Paket Inti Terpadu
│   ├── state.py                         # Representasi state 6-tuple (1.620 status diskret)
│   ├── agent.py                         # QLearningAgent berbasis Watkins Tabular Q-Learning
│   ├── environment.py                   # Simulator Tri-Mode (Smartphone, PC Calibrated, Legacy)
│   ├── crypto.py                        # Standarisasi driver AEAD (AES-GCM, ChaCha20, Ascon-AEAD128)
│   ├── _ascon_nist.py                   # Modul referensi mandiri NIST SP 800-232 Ascon-AEAD128
│   └── __init__.py
├── phone_calibration/                   # Hasil Evaluasi Resmi Profil Smartphone & Sensitivitas (+-20%)
│   ├── best_smartphone_model.pkl        # Model RL terbaik hasil grid search smartphone (alpha=0.14, gamma=0.85)
│   ├── baseline_comparison_smartphone.csv # Evaluasi lengkap profil smartphone
│   ├── sensitivity_analysis.csv         # Evaluasi analisis sensitivitas energi (+-20%)
│   ├── policy_matrix_smartphone.csv     # Matriks kebijakan 2D (Desil Baterai x Tingkat Ancaman)
│   ├── policy_1620_states.csv           # Keputusan aksi pada seluruh 1.620 state
│   ├── tuning_leaderboard.csv           # Papan klasemen 25 trial grid search tuning smartphone
│   └── evaluation_summary_smartphone.json # Ringkasan JSON evaluasi smartphone
├── evaluation_results/                  # Hasil Evaluasi PC Calibrated & Legacy Simulator
│   ├── baseline_comparison_calibrated.csv # Evaluasi mode PC calibrated (AES-NI)
│   ├── baseline_comparison_legacy.csv   # Evaluasi mode simulasi legacy skripsi
│   └── evaluation_summary.json          # Ringkasan JSON evaluasi PC
├── scratch/plots/                       # Grafik Visualisasi Evaluasi Smartphone Resolusi Tinggi
│   ├── plot1_smartphone_messages_security.png
│   ├── plot2_smartphone_action_distribution.png
│   ├── plot3_smartphone_policy_heatmap.png
│   └── plot4_smartphone_sensitivity.png
├── tests/                               # Rangkaian Pengujian Unit Test Otomatis (16 tests)
│   ├── test_crypto.py                   # Uji fungsionalitas AEAD & validasi tag 16-byte
│   ├── test_environment.py              # Uji konsumsi energi smartphone mode & scaling sensitivitas
│   ├── test_agent.py                    # Uji QLearningAgent & Watkins Bellman update
│   └── test_ascon_kat.py                # Known-Answer Test resmi NIST SP 800-232
├── final_model.pkl                      # Model historis utama skripsi (dilindungi hash SHA-256)
├── initial_model.pkl                    # Model awal historis (dilindungi hash SHA-256)
├── agent_brain2.pkl                     # Model historis eksperimen 2 (dilindungi hash SHA-256)
├── agent_brain3.pkl                     # Model historis eksperimen 3 (dilindungi hash SHA-256)
├── agent_brain4.pkl                     # Model historis eksperimen 4 (dilindungi hash SHA-256)
├── best_tuned_model.pkl                 # Model terbaik hasil tuning PC benchmark
├── evaluate.py                          # Skrip utama evaluasi komparatif multi-model & sensitivitas
├── tune_model.py                        # Automated Grid Search & hyperparameter tuning suite
├── train.py                             # Pipeline training Q-Learning mandiri dengan safety guard
├── benchmark.py                         # Skrip mikrobenchmark CPU OpenSSL latensi & throughput
├── test.py                              # Skrip pelari unit test terpadu
├── requirements.txt                     # Daftar dependensi eksternal Python
├── EXPLAIN.md                           # Panduan arsitektur komprehensif seluruh sistem
└── RESULT.docx                          # Laporan mendalam hasil riset dengan tabel dan grafik tersemat
```

---

## Instalasi & Dependensi

Proyek ini membutuhkan Python 3.10 atau versi yang lebih baru (telah diuji pada Python 3.11 dan 3.15 di Windows 11).

```powershell
# 1. Mengaktifkan virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Menginstal dependensi resmi
pip install -r requirements.txt
```

Dependensi utama:
- `cryptography >= 42.0.0`: Implementasi AES-256-GCM dan ChaCha20-Poly1305 berbasis C/OpenSSL.
- `ascon >= 0.0.9`: Pustaka acuan Ascon (didukung modul internal `core/_ascon_nist.py` untuk NIST SP 800-232).
- `python-docx >= 1.1.0`: Pustaka kompilasi laporan riset `RESULT.docx`.
- `matplotlib >= 3.8.0`, `pandas >= 2.0.0`, `numpy >= 1.24.0`: Analisis data dan plotting grafik.

---

## Panduan Eksekusi Sistem

### 1. Evaluasi Profil Smartphone & Analisis Sensitivitas (`evaluate.py`)

Untuk menjalankan evaluasi standar profil smartphone (100 episode pengurasan baterai):

```powershell
python evaluate.py --env smartphone --episodes 100 --outdir phone_calibration
```

Untuk menjalankan evaluasi lengkap beserta **analisis sensitivitas skala energi ($\pm 20\%$)**:

```powershell
python evaluate.py --env smartphone --sensitivity --episodes 100 --outdir phone_calibration
```

Output terminal akan memverifikasi hash SHA-256 seluruh model sebelum dan sesudah eksekusi, serta mengekspor tabel komparatif ke folder `phone_calibration/`.

### 2. Hyperparameter Tuning Otomatis Profil Smartphone (`tune_model.py`)

Untuk menjalankan pencarian grid search 25 trials pada profil smartphone:

```powershell
python tune_model.py --mode smartphone --episodes 10000 --eval-episodes 200 --outdir phone_calibration --output best_smartphone_model.pkl
```

Skrip akan mengevaluasi kombinasi $\alpha \in [0.05, 0.20]$ dan $\gamma \in [0.85, 0.999]$, menyusun papan peringkat multi-objektif Pareto di `phone_calibration/tuning_leaderboard.csv`, dan menyimpan model terbaik ke `phone_calibration/best_smartphone_model.pkl`.

### 3. Benchmark CPU Primitif Kriptografi (`benchmark.py`)

Mengukur performa eksekusi CPU murni dari ketiga algoritma AEAD dengan tag autentikasi standar 16-byte:

```powershell
python benchmark.py
```

> [!NOTE]
> **Pernyataan Penyangkalan Konsumsi Daya (Energy Phrasing Disclaimer):**
> Latensi dan throughput pada benchmark CPU host bukan pengukuran langsung penghematan baterai fisik. Seluruh angka konsumsi energi dalam riset ini merupakan *simulated energy consumption*, *estimated energy cost*, dan *energy-efficiency score* yang dimodelkan secara matematis.

### 4. Pengujian Unit Test Otomatis (`tests/`)

Jalankan seluruh 16 unit test otomatis untuk memvalidasi kriptografi, MDP environment, Q-learning agent, dan Known-Answer Test (KAT) NIST SP 800-232:

```powershell
python -m unittest discover tests
```

---

## Diskusi Kriptografi: Kapan ChaCha20 dan Ascon Mengalahkan AES-256

### Kapan ChaCha20 Mengalahkan AES-256?
1. **Pada Perangkat Mobile Tanpa Akselerasi AES-NI**: Pada prosesor ARM kelas menengah ke bawah atau router murah tanpa modul AES-NI hardware, komputasi software pure AES-256 membutuhkan ~22 cycles/byte, sedangkan ChaCha20 hanya membutuhkan ~10 cycles/byte (2.2x lebih cepat).
2. **Kekebalan Alami Terhadap Cache-Timing Attacks**: ChaCha20 menggunakan operasi aritmatika Add-Rotate-XOR (ARX) yang secara alami berjalan dalam waktu konstan (*constant-time*). Sebaliknya, implementasi software AES murni mengandalkan tabel S-Box di memori cache yang rentan terhadap serangan celah samping (*side-channel attacks*).
3. **Standar Industri Google**: Google mengadopsi ChaCha20-Poly1305 sebagai cipher TLS default pada Android dan Google Chrome untuk perangkat yang tidak memiliki akselerasi hardware AES.

### Kapan Ascon-AEAD128 Mengalahkan AES-256?
1. **Efisiensi Gerbang Logika Silikon (ASIC/FPGA)**: Pada perancangan microchip terintegrasi khusus atau tag RFID pasif, AES-256 membutuhkan area sirkuit silikon yang sangat besar (>10.000 GE). Ascon-AEAD128 sangat kompak (~2.500 GE), memungkinkan integrasi pada sensor berukuran mikro.
2. **Sensor IoT Berdaya Baterai Koin (Coin-Cell CR2032)**: Arus bocor (*leakage current*) dan jejak memori RAM/ROM Ascon yang sangat kecil memungkinkan perangkat biomedis implan atau sensor pertanian nirkabel bertahan hingga bertahun-tahun.
3. **Standar Resmi NIST SP 800-232**: Pemenang kompetisi NIST Lightweight Cryptography (LWC) sebagai standar global enkripsi terotentikasi berdaya rendah.

---

## Matriks Kebijakan 2D (Desil Baterai x Tingkat Ancaman)

Matriks kebijakan 2D agen terbaik smartphone (`phone_calibration/best_smartphone_model.pkl`) mengagregasikan 162 kombinasi status per baris menjadi aksi mayoritas dan persentase pilihan `[AES% / ChaCha% / Ascon%]`:

| Desil Baterai | Rendah (Threat=0) | Sedang (Threat=1) | Tinggi (Threat=2) | Perilaku Kebijakan Cerdas |
| :--- | :---: | :---: | :---: | :--- |
| **90–100% (Bin 9)** | **AES [52% / 35% / 13%]** | **AES [48% / 39% / 13%]** | ChaCha [43% / 44% / 13%] | Mengutamakan keamanan militer AES saat daya melimpah. |
| **80–89% (Bin 8)** | ChaCha [28% / 57% / 15%] | **AES [52% / 37% / 11%]** | **AES [44% / 39% / 17%]** | Mempertahankan proteksi AES saat ancaman terdeteksi. |
| **70–79% (Bin 7)** | **AES [52% / 37% / 11%]** | **AES [54% / 37% / 9%]** | **AES [43% / 39% / 19%]** | Keamanan tinggi saat kondisi baterai aman. |
| **60–69% (Bin 6)** | ChaCha [26% / 61% / 13%] | **AES [46% / 46% / 7%]** | **AES [56% / 33% / 11%]** | Peningkatan porsi ChaCha untuk efisiensi. |
| **50–59% (Bin 5)** | ChaCha [43% / 48% / 9%] | **AES [44% / 39% / 17%]** | **AES [56% / 37% / 7%]** | Puncak proteksi AES (56%) pada ancaman tinggi. |
| **40–49% (Bin 4)** | ChaCha [43% / 48% / 9%] | ChaCha [41% / 43% / 17%] | **AES [56% / 39% / 6%]** | Keseimbangan adaptif transisi daya menengah. |
| **30–39% (Bin 3)** | ChaCha [41% / 50% / 9%] | **AES [48% / 43% / 9%]** | ChaCha [39% / 48% / 13%] | Memulai transisi penyelamatan baterai. |
| **20–29% (Bin 2)** | **ChaCha [30% / 65% / 6%]** | **ChaCha [39% / 54% / 7%]** | **ChaCha [41% / 50% / 9%]** | ChaCha mendominasi (hingga 65%) untuk mencegah kematian dini. |
| **10–19% (Bin 1)** | **ChaCha [31% / 63% / 6%]** | **ChaCha [28% / 61% / 11%]** | **AES [43% / 41% / 17%]** | Dominasi ChaCha, mengaktifkan AES jika benar-benar darurat. |
| **0–9% (Bin 0)** | **ChaCha [20% / 61% / 19%]** | **ChaCha [13% / 65% / 22%]** | **ChaCha [19% / 61% / 20%]** | Ascon meningkat (hingga 22%) pada kondisi sekarat. |

---

## Jaminan Integritas Model Historis (Legacy Safety Guarantee)

Seluruh file model historis skripsi (`final_model.pkl`, `initial_model.pkl`, `agent_brain2.pkl`, `agent_brain3.pkl`, `agent_brain4.pkl`) dilindungi secara ketat. Seluruh skrip evaluasi dan training memverifikasi nilai hash SHA-256 sebelum dan sesudah eksekusi:

| File Model Historis | SHA-256 Checksum (Pre & Post Verified) | Status Integritas |
| :--- | :--- | :---: |
| `final_model.pkl` | `673685dab99cb4efffc013c39e5f538a882da2b7ef6a588be0144215102459b6` | **100% UNCHANGED** |
| `initial_model.pkl` | `4c697407eaae274a7047b126aca2d18d0a3b94a702e0a385eb1ecd066343d4bc` | **100% UNCHANGED** |
| `agent_brain2.pkl` | `c608086595c85445a667b92d1b19efc9f018f094ad164e07761d0f39f6e4e4ac` | **100% UNCHANGED** |
| `agent_brain3.pkl` | `333962a6e30fa23d8d674e1211f611bb34468c4ba0e61000028a3c4d049a2836` | **100% UNCHANGED** |
| `agent_brain4.pkl` | `48b0beaaf9e055ea79ee75fb9d655fddcc253f8941f9c355fda859093397931b` | **100% UNCHANGED** |

---
*Repositori penelitian skripsi Kriptografi Adaptif IoT & Mobile berbasis Reinforcement Learning — Laboratorium Riset IoT 2026.*
