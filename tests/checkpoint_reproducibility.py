"""
Checkpoint Reproducibility Verification Script
Validates 100% exact numerical and decision parity between legacy and core modules.
"""

import sys
import os
import pickle

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import legacy_archive.Agent.state_component as legacy_sc
from legacy_archive.Agent.agent import QLearningAgent as LegacyAgent
import legacy_archive.Agent.encryption_environment as legacy_env

import core.state as cs
from core.agent import QLearningAgent as CoreAgent
import core.environment as core_env

# 6 Canonical test cases from test.py
# (threat, network, battery, signal, size, priority)
TEST_CASES = {
    "survival": (3, "public", 10, 100, 1, 3), # legacy used signal 100
    "efficiency": (1, "private", 95, 5, 20, 1),
    "heavy_load": (3, "public", 50, 2, 500, 3),
    "weak_signal_tax": (2, "public", 30, 0, 150, 2),
    "lowest_need": (1, "private", 10, 0, 200, 0),
    "critical": (3, "public", 5, 0, 1000, 3)
}

MODEL_FILES = [
    "initial_model.pkl",
    "agent_brain2.pkl",
    "agent_brain3.pkl",
    "agent_brain4.pkl",
    "final_model.pkl"
]


def run_checkpoint():
    print("=" * 80)
    print("CHECKPOINT TAHAP 3: UJI REPRODUKSIBILITAS MODEL LAMA (LEGACY VS CORE)")
    print("=" * 80)

    # 1. Keputusan Greedy pada 6 Kasus Uji untuk Semua Model
    print("\n[1] PERBANDINGAN KEPUTUSAN GREEDY (6 KASUS UJI x 5 MODEL)")
    print("-" * 80)
    header = f"{'Model File':<18} | {'Test Case':<16} | {'Legacy Action':<15} | {'Core Action':<15} | {'Match'}"
    print(header)
    print("-" * 80)

    all_matched = True
    for mf in MODEL_FILES:
        leg_ag = LegacyAgent(filename=mf)
        leg_ag._load_brain()
        core_ag = CoreAgent(filename=mf)

        for tc_name, raw in TEST_CASES.items():
            # Legacy decision
            leg_params = [
                legacy_sc.ThreatState(raw[0]),
                legacy_sc.NetworkState(raw[1]),
                legacy_sc.BatteryState(raw[2]),
                legacy_sc.SignalState(raw[3]),
                legacy_sc.SizeState(raw[4]),
                legacy_sc.PriorityState(raw[5])
            ]
            leg_st = (
                leg_params[0].get_index(),
                leg_params[1].get_index(),
                leg_params[2].get_index(),
                leg_params[3].get_index(),
                leg_params[4].get_index(),
                leg_params[5].get_index()
            )
            # Legacy get greedy
            leg_scores = leg_ag.q_table.get(leg_st, {})
            leg_action = max(leg_scores, key=leg_scores.get) if leg_scores else "N/A"

            # Core decision
            core_st = cs.encode_state(*raw)
            core_action = core_ag.get_action(core_st, training=False)

            is_match = (leg_action == core_action)
            if not is_match:
                all_matched = False
            print(f"{mf:<18} | {tc_name:<16} | {leg_action:<15} | {core_action:<15} | {is_match}")
    
    print(f"\nStatus Kecocokan Keputusan Greedy: {'100% MATCH' if all_matched else 'MISMATCH DETECTED'}")

    # 2. Perbandingan Q-Values Detail pada Kasus Uji untuk Model Final & Initial
    print("\n[2] RINCIAN Q-VALUES PADA MODEL FINAL (final_model.pkl)")
    print("-" * 80)
    final_core_ag = CoreAgent(filename="final_model.pkl")
    print(f"{'Test Case':<16} | {'Encoded State':<22} | {'Q(AES-256)':<12} | {'Q(ChaCha20)':<12} | {'Q(ASCON)':<12} | {'Greedy Pick'}")
    print("-" * 80)
    for tc_name, raw in TEST_CASES.items():
        st = cs.encode_state(*raw)
        q_vals = final_core_ag.get_state_q_values(st)
        best = max(q_vals, key=q_vals.get)
        print(f"{tc_name:<16} | {str(st):<22} | {q_vals['AES-256']:>10.2f} | {q_vals['ChaCha20']:>10.2f} | {q_vals['ASCON']:>10.2f} | {best}")

    # 3. Perbandingan Reward dan Biaya Baterai pada 6 Kasus Uji x 3 Aksi
    print("\n[3] PERBANDINGAN REWARD & BIAYA BATERAI (LEGACY ENV VS CORE ENV)")
    print("-" * 85)
    print(f"{'Test Case':<16} | {'Action':<10} | {'Reward (Leg)':<13} | {'Reward (Cor)':<13} | {'Cost % (Leg)':<13} | {'Cost % (Cor)':<13}")
    print("-" * 85)

    reward_matches = True
    cost_matches = True

    for tc_name, raw in TEST_CASES.items():
        t, n, b, s, sz, p = raw
        
        # Legacy env
        leg_e = legacy_env.EncryptionEnvironment(
            threat=legacy_sc.ThreatState(t),
            network=legacy_sc.NetworkState(n),
            battery=legacy_sc.BatteryState(b),
            signal=legacy_sc.SignalState(s),
            size=legacy_sc.SizeState(sz),
            priority=legacy_sc.PriorityState(p)
        )

        # Core env
        cor_e = core_env.EncryptionEnvironment(
            threat=t,
            network=n,
            battery=b,
            signal=s,
            size=sz,
            priority=p,
            mode='simulation_legacy'
        )

        for act in cs.ACTIONS:
            r_leg = leg_e._calculate_reward(act)
            r_cor = cor_e.calculate_reward(act)

            # In legacy, cost is computed in step()
            cost_map = {'AES-256': 0.25, 'ChaCha20': 0.1, 'ASCON': 0.05}
            size_map = {"small": 1, "medium": 5, "large": 15}
            overhead_map = {'AES-256': 2.13, 'ChaCha20': 1, 'ASCON': 1.53}
            sz_label = leg_e.size.get_label()
            c_leg = (cost_map[act] * size_map[sz_label]) + (overhead_map[act] * (size_map[sz_label] * 0.1))

            _, _, c_cor = cor_e.calculate_cost(act)

            if abs(r_leg - r_cor) > 1e-5:
                reward_matches = False
            if abs(c_leg - c_cor) > 1e-5:
                cost_matches = False

            print(f"{tc_name:<16} | {act:<10} | {r_leg:>11.4f} | {r_cor:>11.4f} | {c_leg:>11.4f}% | {c_cor:>11.4f}%")

    print("-" * 85)
    print(f"Status Paritas Reward : {'100% IDENTIK' if reward_matches else 'MISMATCH'}")
    print(f"Status Paritas Biaya  : {'100% IDENTIK' if cost_matches else 'MISMATCH'}")
    print("=" * 80)


if __name__ == '__main__':
    run_checkpoint()
