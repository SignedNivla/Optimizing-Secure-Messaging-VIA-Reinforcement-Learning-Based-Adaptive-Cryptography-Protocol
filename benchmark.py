"""
benchmark.py
============
High-Precision Cryptographic Software Benchmark for Standardized AEAD Ciphers:
- AES-256-GCM (NIST SP 800-38D via OpenSSL / cryptography 50.0.2)
- ChaCha20-Poly1305 (IETF RFC 8439 via OpenSSL / cryptography 50.0.2)
- Ascon-AEAD128 (NIST SP 800-232 via official IAIK TU Graz reference implementation, ascon 0.0.9)

Methodological Rigor:
1. Batch-Trial Timing: Measures K=50 independent trials, where each trial executes
   M repetitions in an unrolled inner loop. This eliminates timer call overhead
   (time.perf_counter function call overhead ~60-80 ns) and minimizes OS jitter.
2. Complete Isolation: Warmup phase (100 repetitions) is executed beforehand and
   strictly excluded from recorded samples.
3. Independent Samples: Mean, median, and sample standard deviation are calculated
   over the K=50 independent trial measurements.
4. Consistent Plaintext Throughput: Computed strictly from plaintext payload bytes
   divided by operation latency. Both Decimal MB/s (10^6 B/s) and Binary MiB/s
   (1024^2 B/s) are reported.
5. Raw Data Export: All individual trial timings are automatically saved to
   'benchmark_raw_results.json' for full reproducibility and auditability.

DISCLAIMER ON BATTERY ENERGY:
Execution latency and throughput metrics quantify algorithmic execution speed on this
workstation CPU. They MUST NOT be used as direct proof of battery energy savings, which
depend on mobile SoC power curves, RF radio transmission states, and hardware acceleration.
"""

import os
import sys
import time
import json
import platform
import statistics
from typing import Dict, List, Tuple, Any

import cryptography
import ascon

from core.crypto import (
    AES256GCMCipher,
    ChaCha20Poly1305Cipher,
    AsconAEAD128Cipher,
    AEADCipher
)

PAYLOAD_SIZES: Dict[str, int] = {
    "32 B": 32,
    "128 B": 128,
    "1024 B (1 KB)": 1024,
    "4096 B (4 KB)": 4096
}

ASSOCIATED_DATA: bytes = b"Adaptive-Crypto-Benchmark-AD-2026"
TRIALS_K: int = 50  # 50 independent trial samples


def get_system_metadata() -> Dict[str, str]:
    """Collects host hardware, OS, and software environment metadata."""
    return {
        "Python Version": platform.python_version(),
        "Python Compiler": platform.python_compiler(),
        "OS Platform": platform.platform(),
        "Processor / Architecture": platform.processor() or platform.machine(),
        "Machine Architecture": platform.machine(),
        "cryptography Version": cryptography.__version__,
        "cryptography Backend": "OpenSSL (C-accelerated via CFFI)",
        "ascon Version": getattr(ascon, "__version__", "0.0.9"),
        "ascon Reference": "TU Graz NIST SP 800-232 reference implementation (Maria Eichlseder et al.)",
        "ascon Variant": "Ascon-AEAD128 (Key=128b, Nonce=128b, Rate=128b, a=12, b=8, Tag=128b; NIST SP 800-232)"
    }


def get_repetition_count(cipher: AEADCipher, size_bytes: int) -> int:
    """
    Selects repetition count M per trial based on cipher execution characteristics
    to ensure inner loop duration is well above timer resolution while keeping
    total benchmark runtime reasonable.
    """
    if isinstance(cipher, AsconAEAD128Cipher):
        # Pure Python implementation
        if size_bytes <= 32:
            return 50
        elif size_bytes <= 128:
            return 25
        elif size_bytes <= 1024:
            return 10
        else:
            return 5
    else:
        # C-accelerated hardware ciphers (AES-GCM, ChaCha20-Poly1305)
        if size_bytes <= 128:
            return 500
        elif size_bytes <= 1024:
            return 200
        else:
            return 100


def benchmark_cipher_size(
    cipher: AEADCipher,
    size_bytes: int,
    k_trials: int = TRIALS_K
) -> Dict[str, Any]:
    """
    Executes K independent trials of M repetitions for both encryption and decryption.
    Warmup phase is completely discarded from recorded measurements.
    """
    m_reps = get_repetition_count(cipher, size_bytes)
    key = cipher.generate_key()
    nonce = cipher.generate_nonce()
    plaintext = os.urandom(size_bytes)
    ad = ASSOCIATED_DATA

    # --- 1. WARMUP PHASE (Strictly excluded from timing samples) ---
    for _ in range(100):
        ct_warm = cipher.encrypt(key, nonce, plaintext, ad)
        _ = cipher.decrypt(key, nonce, ct_warm, ad)

    # Pre-generate sample ciphertext for decryption tests
    sample_ct = cipher.encrypt(key, nonce, plaintext, ad)
    ct_len = len(sample_ct)
    tag_overhead = ct_len - size_bytes

    # --- 2. ENCRYPTION BENCHMARK (K independent trials) ---
    enc_trial_latencies_us: List[float] = []
    for _ in range(k_trials):
        t0 = time.perf_counter()
        for _ in range(m_reps):
            _ = cipher.encrypt(key, nonce, plaintext, ad)
        t1 = time.perf_counter()
        # Per-operation latency in microseconds
        op_lat = ((t1 - t0) / m_reps) * 1e6
        enc_trial_latencies_us.append(op_lat)

    # --- 3. DECRYPTION BENCHMARK (K independent trials) ---
    dec_trial_latencies_us: List[float] = []
    for _ in range(k_trials):
        t0 = time.perf_counter()
        for _ in range(m_reps):
            pt = cipher.decrypt(key, nonce, sample_ct, ad)
        t1 = time.perf_counter()
        op_lat = ((t1 - t0) / m_reps) * 1e6
        dec_trial_latencies_us.append(op_lat)

    if pt != plaintext:
        raise RuntimeError(f"Integrity check failed during benchmark for {cipher.name}")

    # --- 4. STATISTICAL AGGREGATION ---
    mean_enc = statistics.mean(enc_trial_latencies_us)
    median_enc = statistics.median(enc_trial_latencies_us)
    std_enc = statistics.stdev(enc_trial_latencies_us)

    mean_dec = statistics.mean(dec_trial_latencies_us)
    median_dec = statistics.median(dec_trial_latencies_us)
    std_dec = statistics.stdev(dec_trial_latencies_us)

    # Throughput (Decimal MB/s: 10^6 Bytes/s)
    enc_tp_mean_dec = (size_bytes / 1e6) / (mean_enc * 1e-6)
    enc_tp_med_dec = (size_bytes / 1e6) / (median_enc * 1e-6)
    dec_tp_mean_dec = (size_bytes / 1e6) / (mean_dec * 1e-6)
    dec_tp_med_dec = (size_bytes / 1e6) / (median_dec * 1e-6)

    # Throughput (Binary MiB/s: 1024^2 Bytes/s)
    enc_tp_med_bin = (size_bytes / (1024 * 1024)) / (median_enc * 1e-6)
    dec_tp_med_bin = (size_bytes / (1024 * 1024)) / (median_dec * 1e-6)

    return {
        "cipher_name": cipher.name,
        "payload_size": size_bytes,
        "k_trials": k_trials,
        "m_reps_per_trial": m_reps,
        "total_operations": k_trials * m_reps,
        "ct_length": ct_len,
        "tag_overhead": tag_overhead,
        "enc_latency_us": {
            "mean": mean_enc,
            "median": median_enc,
            "std": std_enc,
            "min": min(enc_trial_latencies_us),
            "max": max(enc_trial_latencies_us),
            "raw_trials": enc_trial_latencies_us
        },
        "dec_latency_us": {
            "mean": mean_dec,
            "median": median_dec,
            "std": std_dec,
            "min": min(dec_trial_latencies_us),
            "max": max(dec_trial_latencies_us),
            "raw_trials": dec_trial_latencies_us
        },
        "throughput_decimal_mb_s": {
            "enc_mean": enc_tp_mean_dec,
            "enc_median": enc_tp_med_dec,
            "dec_mean": dec_tp_mean_dec,
            "dec_median": dec_tp_med_dec
        },
        "throughput_binary_mib_s": {
            "enc_median": enc_tp_med_bin,
            "dec_median": dec_tp_med_bin
        }
    }


def run_full_benchmark(export_file: str = "benchmark_raw_results.json"):
    metadata = get_system_metadata()

    print("=" * 100)
    print("STANDARDIZED AEAD CRYPTOGRAPHIC BENCHMARK REPORT (HIGH-PRECISION BATCH-TRIAL METHOD)")
    print("=" * 100)
    print("System & Hardware Environment:")
    for k, v in metadata.items():
        print(f"  - {k:<26}: {v}")
    print("-" * 100)
    print(f"Methodology:")
    print(f"  - Sampling Protocol : {TRIALS_K} independent trials of M repetitions (inner loop)")
    print(f"  - Warmup Phase      : 100 iterations (strictly discarded from timing samples)")
    print(f"  - Associated Data   : {len(ASSOCIATED_DATA)} bytes authenticated header")
    print(f"  - Throughput Metric : Plaintext size / latency (reported in decimal MB/s and binary MiB/s)")
    print("=" * 100)

    ciphers = [
        AES256GCMCipher(),
        ChaCha20Poly1305Cipher(),
        AsconAEAD128Cipher()
    ]

    all_results = []

    for size_label, size_bytes in PAYLOAD_SIZES.items():
        print(f"\n[PAYLOAD SIZE: {size_label} ({size_bytes} Bytes)]")
        header = f"{'Algorithm':<20} | {'Enc Latency (Mean +- Std / Med)':<32} | {'Dec Latency (Mean +- Std / Med)':<32} | {'Throughput Enc/Dec'}"
        print(header)
        print("-" * 100)

        for cipher in ciphers:
            res = benchmark_cipher_size(cipher, size_bytes, k_trials=TRIALS_K)
            all_results.append(res)

            enc_s = f"{res['enc_latency_us']['mean']:.3f} +- {res['enc_latency_us']['std']:.3f} / {res['enc_latency_us']['median']:.3f} us"
            dec_s = f"{res['dec_latency_us']['mean']:.3f} +- {res['dec_latency_us']['std']:.3f} / {res['dec_latency_us']['median']:.3f} us"
            tp_s = f"{res['throughput_decimal_mb_s']['enc_median']:.1f} / {res['throughput_decimal_mb_s']['dec_median']:.1f} MB/s ({res['throughput_binary_mib_s']['enc_median']:.1f} MiB/s)"

            print(f"{cipher.name:<20} | {enc_s:<32} | {dec_s:<32} | {tp_s}")

    # Export raw data to JSON
    export_payload = {
        "metadata": metadata,
        "benchmark_results": all_results
    }
    with open(export_file, "w") as f:
        json.dump(export_payload, f, indent=2)

    print("\n" + "=" * 100)
    print(f"Raw measurement data successfully exported to: {os.path.abspath(export_file)}")
    print("=" * 100)
    print("IMPORTANT DISCLAIMER ON BATTERY ENERGY SAVINGS:")
    print("1. Latency (microseconds) and throughput (MB/s) reflect CPU execution cycles on this host.")
    print("2. Hardware with dedicated AES extensions (e.g., AES-NI, ARMv8 Cryptography) accelerates")
    print("   AES-GCM to gigabytes per second, whereas software implementations exhibit different curves.")
    print("3. These metrics MUST NOT be taken as direct proof of battery energy preservation.")
    print("   Energy consumption on mobile devices is governed by physical power states, display,")
    print("   modem radio duty cycle, and SoC architecture, as evaluated in the MDP simulation.")
    print("=" * 100)

    return metadata, all_results


if __name__ == "__main__":
    run_full_benchmark()
