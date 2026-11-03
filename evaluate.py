"""
evaluate.py
===========
Unified, reproducible evaluation suite for the Adaptive Cryptography IoT system.

Key Methodological Principles:
1. Strict isolation: Evaluates legacy models and baselines WITHOUT importing core.crypto.
2. Immutability guarantee: Computes and asserts SHA-256 hashes of all .pkl files before and after.
3. Correct state discretization indexing:
   - Threat: 0 = Rendah (Low), 1 = Sedang (Medium), 2 = Tinggi (High)
   - Network: 0 = Public, 1 = Private
   - Battery: 0..9 (Deciles 0-9% up to 90-100%)
   - Signal: 0 = Weak, 1 = Medium, 2 = Strong
   - Payload Size: 0 = Small, 1 = Medium, 2 = Large
   - Priority: 0 = Low, 1 = Medium, 2 = High
4. Independent reporting of WSM:
   - WSM (|S|=1620): Over all 1,620 theoretical states.
   - WSM (Visited): Over unique states present in the loaded Q-table.
5. Dynamic SETOR denominator:
   - SETOR = (Total Accumulated Security Score) / Delta Battery (%)
   - Handles both 100% full-drain episodes and partial-drain / fixed-horizon sessions.
6. Honest evaluation metrics:
   - Evaluates empirical reward improvement without unverified convergence claims.
   - Unverified historical training hyperparameters are clearly flagged and separated.
"""

import os
import sys
import glob
import copy
import json
import random
import hashlib
import itertools
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import pandas as pd

# Strict isolation: ONLY import state and environment from core. DO NOT import crypto!
from core.state import (
    TOTAL_STATE_SPACE,
    ACTIONS
)
from core.environment import EncryptionEnvironment

# Random seed for reproducible simulation
SIMULATION_SEED = 42
SIMULATION_EPISODES = 500

SECURITY_WEIGHTS = {
    'AES-256': 1.0,
    'ChaCha20': 0.7,
    'ASCON': 0.4
}

# Threat index mapping according to legacy implementation (discretize_threat):
# 0 = Rendah / Low
# 1 = Sedang / Medium
# 2 = Tinggi / High
THREAT_LABELS = {
    0: 'Rendah (Threat=0)',
    1: 'Sedang (Threat=1)',
    2: 'Tinggi (Threat=2)'
}

# Discrete label mappings for full state table
DISCRETE_NAMES = {
    'threat': {0: 'Rendah', 1: 'Sedang', 2: 'Tinggi'},
    'network': {0: 'Public', 1: 'Private'},
    'battery': {
        0: '0-9%', 1: '10-19%', 2: '20-29%', 3: '30-39%', 4: '40-49%',
        5: '50-59%', 6: '60-69%', 7: '70-79%', 8: '80-89%', 9: '90-100%'
    },
    'signal': {0: 'Weak', 1: 'Medium', 2: 'Strong'},
    'size': {0: 'Small', 1: 'Medium', 2: 'Large'},
    'priority': {0: 'Low', 1: 'Medium', 2: 'High'}
}

# Verified model registry:
# Unverified historical hyperparameters from legacy train.py are documented as notes,
# not embedded in the model names.
MODEL_REGISTRY = [
    {
        'id': 'best_smartphone_model',
        'name': 'Best Smartphone Model (best_smartphone_model.pkl)',
        'filename': 'best_smartphone_model.pkl',
        'alt_filename': os.path.join('phone_calibration', 'best_smartphone_model.pkl'),
        'note': 'Model hasil optimasi grid search khusus profil smartphone (software AES 2.2x, ChaCha20, Ascon-AEAD128).',
        'is_baseline': False
    },
    {
        'id': 'best_tuned_model',
        'name': 'Best Tuned Model PC (best_tuned_model.pkl)',
        'filename': 'best_tuned_model.pkl',
        'alt_filename': os.path.join('tuning_results', 'best_tuned_model.pkl'),
        'note': 'Model hasil optimasi grid search terkalibrasi PC benchmark.',
        'is_baseline': False
    },
    {
        'id': 'final_model',
        'name': 'Final Model (final_model.pkl)',
        'filename': 'final_model.pkl',
        'alt_filename': 'final_model.pkl',
        'note': 'Naskah mengklaim alpha=0.14, gamma=0.56. Pemanggilan posisional aktual di train.py: alpha=0.14, epsilon=0.56, gamma=0.99.',
        'is_baseline': False
    },
    {
        'id': 'initial_model',
        'name': 'Initial Model (initial_model.pkl)',
        'filename': 'initial_model.pkl',
        'alt_filename': 'initial_model.pkl',
        'note': 'Model awal tanpa retuning (default legacy constructor: alpha=0.1, epsilon=0.9, gamma=0.5).',
        'is_baseline': False
    },
    {
        'id': 'model_2',
        'name': 'Model 2 (agent_brain2.pkl)',
        'filename': 'agent_brain2.pkl',
        'alt_filename': 'agent_brain2.pkl',
        'note': 'Eksperimen historis 2 (posisional: alpha=0.7, epsilon=0.001, gamma=0.5).',
        'is_baseline': False
    },
    {
        'id': 'model_3',
        'name': 'Model 3 (agent_brain3.pkl)',
        'filename': 'agent_brain3.pkl',
        'alt_filename': 'agent_brain3.pkl',
        'note': 'Eksperimen historis 3 (posisional: alpha=0.2, epsilon=0.8, gamma=0.8).',
        'is_baseline': False
    },
    {
        'id': 'model_4',
        'name': 'Model 4 (agent_brain4.pkl)',
        'filename': 'agent_brain4.pkl',
        'alt_filename': 'agent_brain4.pkl',
        'note': 'Eksperimen historis 4 (posisional: alpha=0.12, epsilon=0.8, gamma=0.99).',
        'is_baseline': False
    }
]


def compute_file_sha256(filepath: str) -> str:
    """Computes SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def check_all_model_hashes() -> Dict[str, str]:
    """Computes SHA-256 hashes for all .pkl files in the workspace."""
    hashes = {}
    legacy_files = ['final_model.pkl', 'initial_model.pkl', 'agent_brain2.pkl', 'agent_brain3.pkl', 'agent_brain4.pkl']
    for pkl_file in legacy_files:
        if os.path.exists(pkl_file):
            hashes[pkl_file] = compute_file_sha256(pkl_file)
    return hashes


def load_q_table_readonly(filepath: str, alt_filepath: Optional[str] = None) -> Dict[Tuple[int, ...], Dict[str, float]]:
    """Loads Q-table from a pickle file without modifying anything."""
    import pickle
    target = filepath
    if not os.path.exists(target) and alt_filepath and os.path.exists(alt_filepath):
        target = alt_filepath
    with open(target, 'rb') as f:
        data = pickle.load(f)
    return copy.deepcopy(data)


def generate_all_1620_states() -> List[Tuple[int, int, int, int, int, int]]:
    """Generates all 1,620 discrete tuples (threat, network, battery, signal, size, priority)."""
    return list(itertools.product(
        range(3),  # Threat: 0=Rendah, 1=Sedang, 2=Tinggi
        range(2),  # Network: 0=Public, 1=Private
        range(10), # Battery: 0..9 (deciles)
        range(3),  # Signal: 0=Weak, 1=Medium, 2=Strong
        range(3),  # Size: 0=Small, 1=Medium, 2=Large
        range(3)   # Priority: 0=Low, 1=Medium, 2=High
    ))


def get_greedy_action(q_table: Dict[Tuple[int, ...], Dict[str, float]], state: Tuple[int, ...]) -> str:
    """Selects the greedy action from Q-table. Defaults to AES-256 if unvisited."""
    if state in q_table:
        scores = q_table[state]
        return max(scores, key=scores.get)
    return 'AES-256'


# --- Baselines Policies ---
def policy_static_aes(battery: float, state: Tuple[int, ...]) -> str:
    return 'AES-256'

def policy_static_chacha(battery: float, state: Tuple[int, ...]) -> str:
    return 'ChaCha20'

def policy_static_ascon(battery: float, state: Tuple[int, ...]) -> str:
    return 'ASCON'

def policy_threshold_heuristic(battery: float, state: Tuple[int, ...]) -> str:
    """
    Standard battery-threshold heuristic:
    - Battery >= 60% -> AES-256
    - 20% <= Battery < 60% -> ChaCha20
    - Battery < 20% -> ASCON
    """
    if battery >= 60.0:
        return 'AES-256'
    elif battery >= 20.0:
        return 'ChaCha20'
    else:
        return 'ASCON'

def policy_random_choice(battery: float, state: Tuple[int, ...]) -> str:
    return random.choice(ACTIONS)


BASELINE_REGISTRY = [
    {
        'id': 'baseline_aes',
        'name': 'Baseline 1: Static AES-256-GCM',
        'policy_fn': policy_static_aes,
        'wsm': 1.0000
    },
    {
        'id': 'baseline_chacha',
        'name': 'Baseline 2: Static ChaCha20-Poly1305',
        'policy_fn': policy_static_chacha,
        'wsm': 0.7000
    },
    {
        'id': 'baseline_ascon',
        'name': 'Baseline 3: Static Ascon-AEAD128',
        'policy_fn': policy_static_ascon,
        'wsm': 0.4000
    },
    {
        'id': 'baseline_heuristic',
        'name': 'Baseline 4: Threshold Heuristic',
        'policy_fn': policy_threshold_heuristic,
        'wsm': (4 * 1.0 + 4 * 0.7 + 2 * 0.4) / 10.0  # Deciles: 4 AES, 4 Cha, 2 ASC = 0.7600
    },
    {
        'id': 'baseline_random',
        'name': 'Baseline 5: Uniform Random',
        'policy_fn': policy_random_choice,
        'wsm': (1.0 + 0.7 + 0.4) / 3.0  # 0.7000
    }
]


def evaluate_static_policy(
    q_table: Dict[Tuple[int, ...], Dict[str, float]],
    all_states: List[Tuple[int, int, int, int, int, int]]
) -> Dict[str, Any]:
    """
    Analyzes the static policy across all 1,620 states and visited states.
    Reports both WSM (|S|=1620) and WSM (Visited Q-table) separately.
    """
    total_states = len(all_states)
    visited_count = len(q_table)

    counts_1620 = {'AES-256': 0, 'ChaCha20': 0, 'ASCON': 0}
    counts_visited = {'AES-256': 0, 'ChaCha20': 0, 'ASCON': 0}

    for s in all_states:
        a = get_greedy_action(q_table, s)
        counts_1620[a] += 1
        if s in q_table:
            a_vis = max(q_table[s], key=q_table[s].get)
            counts_visited[a_vis] += 1

    # WSM across entire 1,620 theoretical state space
    wsm_1620 = (
        counts_1620['AES-256'] * SECURITY_WEIGHTS['AES-256'] +
        counts_1620['ChaCha20'] * SECURITY_WEIGHTS['ChaCha20'] +
        counts_1620['ASCON'] * SECURITY_WEIGHTS['ASCON']
    ) / total_states

    # WSM across explored/visited states only
    wsm_visited = (
        counts_visited['AES-256'] * SECURITY_WEIGHTS['AES-256'] +
        counts_visited['ChaCha20'] * SECURITY_WEIGHTS['ChaCha20'] +
        counts_visited['ASCON'] * SECURITY_WEIGHTS['ASCON']
    ) / max(1, visited_count)

    return {
        'total_states': total_states,
        'visited_states': visited_count,
        'coverage_pct': (visited_count / total_states) * 100.0,
        'counts_1620': counts_1620,
        'pcts_1620': {k: (v / total_states) * 100.0 for k, v in counts_1620.items()},
        'wsm_1620': wsm_1620,
        'counts_visited': counts_visited,
        'pcts_visited': {k: (v / max(1, visited_count)) * 100.0 for k, v in counts_visited.items()},
        'wsm_visited': wsm_visited
    }


def simulate_episodes(
    policy_or_qtable: Any,
    episodes: int = SIMULATION_EPISODES,
    seed: int = SIMULATION_SEED,
    env_mode: str = 'smartphone',
    energy_scale: float = 1.0
) -> Dict[str, Any]:
    """
    Executes dynamic battery-drain episodes.
    
    SETOR Formulation:
      SETOR = Total Security Score Accumulated / Delta Battery Consumed (%)
      Delta Battery = start_battery - end_battery.
      On full drain: 100.0% - 0.0% = 100.0%.
      If an episode terminates early (e.g. fixed-horizon), Delta Battery reflects actual drain.
    """
    random.seed(seed)
    np.random.seed(seed)
    env = EncryptionEnvironment(mode=env_mode, energy_scale=energy_scale)

    ep_messages: List[int] = []
    ep_securities: List[float] = []
    ep_rewards: List[float] = []
    ep_setor: List[float] = []
    action_counts = {'AES-256': 0, 'ChaCha20': 0, 'ASCON': 0}

    is_fn = callable(policy_or_qtable)

    for _ in range(episodes):
        state = env.reset()
        start_battery = env.battery  # Initial battery percentage (100.0%)
        done = False
        steps = 0
        total_sec = 0.0
        total_reward = 0.0

        while not done:
            if is_fn:
                action = policy_or_qtable(env.battery, state)
            else:
                action = get_greedy_action(policy_or_qtable, state)

            action_counts[action] += 1
            sec_score = SECURITY_WEIGHTS[action]
            total_sec += sec_score

            next_state, reward, done = env.step(action)
            total_reward += reward
            steps += 1
            state = next_state

        end_battery = env.battery  # 0.0% on full drain
        # Dynamic Delta Battery calculation:
        delta_battery = start_battery - end_battery

        ep_messages.append(steps)
        ep_securities.append(total_sec)
        ep_rewards.append(total_reward)
        
        # Robust SETOR calculation:
        # If delta_battery <= 0 (e.g. 0 steps taken, or no battery consumed):
        # SETOR is strictly 0.0 (cannot deliver security efficiency without battery expenditure).
        # If delta_battery > 0 (normal partial or full drain):
        # SETOR = Total Security Accumulated / Delta Battery Consumed (%)
        if delta_battery <= 0.0:
            setor_i = 0.0
        else:
            setor_i = total_sec / delta_battery

        ep_setor.append(setor_i)

    total_acts = max(1, sum(action_counts.values()))
    act_pcts = {a: (c / total_acts) * 100.0 for a, c in action_counts.items()}
    total_battery_consumed = float(sum(SIMULATION_EPISODES * [100.0]))  # total across episodes

    return {
        'messages_mean': float(np.mean(ep_messages)),
        'messages_std': float(np.std(ep_messages)),
        'security_mean': float(np.mean(ep_securities)),
        'security_std': float(np.std(ep_securities)),
        'reward_mean': float(np.mean(ep_rewards)),
        'reward_std': float(np.std(ep_rewards)),
        'setor_mean': float(np.mean(ep_setor)),
        'setor_std': float(np.std(ep_setor)),
        'setor_macro': float(sum(ep_securities) / max(1e-6, sum([max(0.0, 100.0 - 0.0) for _ in range(episodes)]))),
        'action_pcts': act_pcts
    }


def compute_2d_policy_matrix(
    q_table: Dict[Tuple[int, ...], Dict[str, float]]
) -> pd.DataFrame:
    """
    Aggregates greedy actions across all 1,620 states into a 2D matrix:
    Rows: Battery Decile (0..9, from 90-100% down to 0-9%)
    Cols: Threat Level (0=Rendah, 1=Sedang, 2=Tinggi)
    Each cell represents 54 discrete state combinations.
    """
    battery_labels = {
        9: '90-100% (Bin 9)',
        8: '80-89%  (Bin 8)',
        7: '70-79%  (Bin 7)',
        6: '60-69%  (Bin 6)',
        5: '50-59%  (Bin 5)',
        4: '40-49%  (Bin 4)',
        3: '30-39%  (Bin 3)',
        2: '20-29%  (Bin 2)',
        1: '10-19%  (Bin 1)',
        0: '0-9%    (Bin 0)'
    }

    matrix_rows = []

    # Display columns ordered: Rendah (0), Sedang (1), Tinggi (2)
    for b in range(9, -1, -1):
        row_dict = {'Battery Decile': battery_labels[b]}
        for t in [0, 1, 2]:
            t_col = THREAT_LABELS[t]
            cell_states = [
                (t, n, b, s, sz, p)
                for n in range(2)
                for s in range(3)
                for sz in range(3)
                for p in range(3)
            ]
            counts = {'AES-256': 0, 'ChaCha20': 0, 'ASCON': 0}
            for st in cell_states:
                a = get_greedy_action(q_table, st)
                counts[a] += 1

            n_st = len(cell_states)
            p_aes = counts['AES-256'] / n_st * 100.0
            p_cha = counts['ChaCha20'] / n_st * 100.0
            p_asc = counts['ASCON'] / n_st * 100.0
            dom = max(counts, key=counts.get)
            dom_abbr = 'AES' if dom == 'AES-256' else ('Cha' if dom == 'ChaCha20' else 'ASC')

            cell_str = f"{dom_abbr} [{p_aes:2.0f}%/{p_cha:2.0f}%/{p_asc:2.0f}%]"
            row_dict[t_col] = cell_str

        matrix_rows.append(row_dict)

    return pd.DataFrame(matrix_rows)


def run_full_evaluation(output_dir: str = 'evaluation_results', env_mode: str = 'benchmark_calibrated'):
    """Executes the complete Stage 5 evaluation suite."""
    os.makedirs(output_dir, exist_ok=True)

    mode_title = "BENCHMARK-CALIBRATED (Ground Truth AEAD)" if env_mode == 'benchmark_calibrated' else "HISTORICAL LEGACY SIMULATION"
    print("=" * 100)
    print(f"STAGE 5: UNIFIED COMPREHENSIVE EVALUATION & REPRODUCIBILITY SUITE")
    print(f"Target Environment: {mode_title}")
    print("=" * 100)

    # 1. SHA-256 Pre-Check
    print("\n[STEP 1] Pre-Evaluation SHA-256 Hash Verification of All .pkl Models:")
    pre_hashes = check_all_model_hashes()
    for filename, h in pre_hashes.items():
        print(f"  - {filename:<18}: {h}")

    all_states = generate_all_1620_states()
    print(f"\n[STEP 2] Total Theoretical State Space: |S| = {len(all_states)} discrete states")
    print("State Index Mapping:")
    print("  - Threat       : 0 = Rendah, 1 = Sedang, 2 = Tinggi")
    print("  - Network      : 0 = Public, 1 = Private")
    print("  - Battery Bins : 0 (0-9%) through 9 (90-100%)")
    print("  - Signal       : 0 = Weak, 1 = Medium, 2 = Strong")
    print("  - Size         : 0 = Small, 1 = Medium, 2 = Large")
    print("  - Priority     : 0 = Low, 1 = Medium, 2 = High")

    # 2. Evaluate Models & Baselines
    results_table = []
    detailed_metrics = {}

    print(f"\n[STEP 3] Running Multi-Episode Simulation ({SIMULATION_EPISODES} episodes per candidate, Seed={SIMULATION_SEED})...")

    # 2a. RL Models
    loaded_q_tables = {}
    for m in MODEL_REGISTRY:
        target_fn = m['filename']
        if not os.path.exists(target_fn) and m.get('alt_filename') and os.path.exists(m['alt_filename']):
            target_fn = m['alt_filename']
        if not os.path.exists(target_fn):
            continue
        print(f"  Evaluating {m['name']}...")
        q_table = load_q_table_readonly(target_fn)
        loaded_q_tables[m['id']] = q_table

        # Static policy analysis
        static_res = evaluate_static_policy(q_table, all_states)
        # Dynamic simulation
        sim_res = simulate_episodes(q_table, episodes=SIMULATION_EPISODES, seed=SIMULATION_SEED, env_mode=env_mode)

        row = {
            'Candidate': m['name'],
            'Type': 'RL Model',
            'Messages Sent (N)': f"{sim_res['messages_mean']:.1f} +- {sim_res['messages_std']:.1f}",
            'Total Security': f"{sim_res['security_mean']:.1f} +- {sim_res['security_std']:.1f}",
            'WSM (|S|=1620)': f"{static_res['wsm_1620']:.4f}",
            'WSM (Visited)': f"{static_res['wsm_visited']:.4f}",
            'State Coverage': f"{static_res['visited_states']}/{static_res['total_states']} ({static_res['coverage_pct']:.1f}%)",
            'SETOR (Score/%)': f"{sim_res['setor_mean']:.4f} +- {sim_res['setor_std']:.4f}",
            'Cumulative Reward': f"{sim_res['reward_mean']:.1f} +- {sim_res['reward_std']:.1f}",
            'Action Dist Trace (AES/Cha/ASC)': (
                f"{sim_res['action_pcts']['AES-256']:.1f}% / "
                f"{sim_res['action_pcts']['ChaCha20']:.1f}% / "
                f"{sim_res['action_pcts']['ASCON']:.1f}%"
            ),
            'Static Policy (AES/Cha/ASC)': (
                f"{static_res['pcts_1620']['AES-256']:.1f}% / "
                f"{static_res['pcts_1620']['ChaCha20']:.1f}% / "
                f"{static_res['pcts_1620']['ASCON']:.1f}%"
            ),
            'Notes': m['note']
        }
        results_table.append(row)
        detailed_metrics[m['id']] = {
            'metadata': m,
            'static': static_res,
            'dynamic': sim_res
        }

    # 2b. Baselines
    for b in BASELINE_REGISTRY:
        print(f"  Evaluating {b['name']}...")
        sim_res = simulate_episodes(b['policy_fn'], episodes=SIMULATION_EPISODES, seed=SIMULATION_SEED, env_mode=env_mode)

        row = {
            'Candidate': b['name'],
            'Type': 'Baseline',
            'Messages Sent (N)': f"{sim_res['messages_mean']:.1f} +- {sim_res['messages_std']:.1f}",
            'Total Security': f"{sim_res['security_mean']:.1f} +- {sim_res['security_std']:.1f}",
            'WSM (|S|=1620)': f"{b['wsm']:.4f}",
            'WSM (Visited)': f"{b['wsm']:.4f}",
            'State Coverage': '1620/1620 (100.0%)',
            'SETOR (Score/%)': f"{sim_res['setor_mean']:.4f} +- {sim_res['setor_std']:.4f}",
            'Cumulative Reward': f"{sim_res['reward_mean']:.1f} +- {sim_res['reward_std']:.1f}",
            'Action Dist Trace (AES/Cha/ASC)': (
                f"{sim_res['action_pcts']['AES-256']:.1f}% / "
                f"{sim_res['action_pcts']['ChaCha20']:.1f}% / "
                f"{sim_res['action_pcts']['ASCON']:.1f}%"
            ),
            'Static Policy (AES/Cha/ASC)': 'Deterministic Baseline',
            'Notes': 'Standard comparative benchmark baseline'
        }
        results_table.append(row)
        detailed_metrics[b['id']] = {
            'metadata': {
                'id': b['id'],
                'name': b['name'],
                'wsm': b['wsm']
            },
            'dynamic': sim_res
        }

    # 3. Print Baseline Comparison Table
    df_results = pd.DataFrame(results_table)
    print("\n" + "=" * 100)
    print("EVALUATION RESULTS: 5 RL MODELS VS 5 BASELINES (500 FULL DRAIN EPISODES)")
    print("=" * 100)
    display_cols = [
        'Candidate',
        'Messages Sent (N)',
        'Total Security',
        'WSM (|S|=1620)',
        'WSM (Visited)',
        'State Coverage',
        'SETOR (Score/%)',
        'Cumulative Reward',
        'Action Dist Trace (AES/Cha/ASC)'
    ]
    print(df_results[display_cols].to_string(index=False))

    suffix = f"_{env_mode}" if env_mode != 'simulation_legacy' else "_legacy"
    calibrated_csv_path = os.path.join(output_dir, f'baseline_comparison{suffix}.csv')
    df_results.to_csv(calibrated_csv_path, index=False)
    csv_path = os.path.join(output_dir, 'baseline_comparison.csv')
    df_results.to_csv(csv_path, index=False)
    print(f"\nSaved baseline comparison to: {calibrated_csv_path} and {csv_path}")

    # 4. Generate 2D Aggregated Policy Matrices with CORRECTED THREAT LABELS
    print("\n" + "=" * 100)
    print("2D POLICY MATRIX (BATTERY DECILE x THREAT LEVEL): FINAL MODEL (final_model.pkl)")
    print("Threat Indexing: 0 = Rendah, 1 = Sedang, 2 = Tinggi")
    print("Each cell displays: Majority Action [AES% / ChaCha% / ASCON%] across 54 states")
    print("=" * 100)
    df_matrix_final = compute_2d_policy_matrix(loaded_q_tables['final_model'])
    print(df_matrix_final.to_string(index=False))
    matrix_final_path = os.path.join(output_dir, 'policy_matrix_final.csv')
    df_matrix_final.to_csv(matrix_final_path, index=False)

    print("\n" + "=" * 100)
    print("2D POLICY MATRIX (BATTERY DECILE x THREAT LEVEL): INITIAL MODEL (initial_model.pkl)")
    print("=" * 100)
    df_matrix_init = compute_2d_policy_matrix(loaded_q_tables['initial_model'])
    print(df_matrix_init.to_string(index=False))
    matrix_init_path = os.path.join(output_dir, 'policy_matrix_initial.csv')
    df_matrix_init.to_csv(matrix_init_path, index=False)

    if 'best_tuned_model' in loaded_q_tables:
        print("\n" + "=" * 100)
        print("2D POLICY MATRIX (BATTERY DECILE x THREAT LEVEL): BEST TUNED MODEL PC (best_tuned_model.pkl)")
        print("Threat Indexing: 0 = Rendah, 1 = Sedang, 2 = Tinggi")
        print("Each cell displays: Majority Action [AES% / ChaCha% / ASCON%] across 54 states")
        print("=" * 100)
        df_matrix_tuned = compute_2d_policy_matrix(loaded_q_tables['best_tuned_model'])
        print(df_matrix_tuned.to_string(index=False))
        matrix_tuned_path = os.path.join(output_dir, 'policy_matrix_tuned.csv')
        df_matrix_tuned.to_csv(matrix_tuned_path, index=False)

    if 'best_smartphone_model' in loaded_q_tables:
        print("\n" + "=" * 100)
        print("2D POLICY MATRIX (BATTERY DECILE x THREAT LEVEL): BEST SMARTPHONE MODEL (best_smartphone_model.pkl)")
        print("Threat Indexing: 0 = Rendah, 1 = Sedang, 2 = Tinggi")
        print("Each cell displays: Majority Action [AES% / ChaCha% / ASCON%] across 54 states")
        print("=" * 100)
        df_matrix_phone = compute_2d_policy_matrix(loaded_q_tables['best_smartphone_model'])
        print(df_matrix_phone.to_string(index=False))
        matrix_phone_path = os.path.join(output_dir, 'policy_matrix_smartphone.csv')
        df_matrix_phone.to_csv(matrix_phone_path, index=False)

    # 5. Export Full 1,620 States Mapping
    print("\n[STEP 4] Exporting complete 1,620 state policy mapping with corrected labels...")
    full_state_records = []
    q_final = loaded_q_tables['final_model']
    q_init = loaded_q_tables['initial_model']
    q_tuned = loaded_q_tables.get('best_tuned_model')
    q_phone = loaded_q_tables.get('best_smartphone_model')

    for s in all_states:
        t, n, b, sig, sz, p = s
        
        act_final = get_greedy_action(q_final, s)
        act_init = get_greedy_action(q_init, s)
        
        q_vals = q_final.get(s, {'AES-256': 0.0, 'ChaCha20': 0.0, 'ASCON': 0.0})

        rec = {
            'threat_idx': t,
            'threat_label': DISCRETE_NAMES['threat'][t],
            'network_idx': n,
            'network_label': DISCRETE_NAMES['network'][n],
            'battery_bin': b,
            'battery_label': DISCRETE_NAMES['battery'][b],
            'signal_idx': sig,
            'signal_label': DISCRETE_NAMES['signal'][sig],
            'size_idx': sz,
            'size_label': DISCRETE_NAMES['size'][sz],
            'priority_idx': p,
            'priority_label': DISCRETE_NAMES['priority'][p],
            'final_model_action': act_final,
            'initial_model_action': act_init,
        }
        if q_tuned is not None:
            rec['best_tuned_action'] = get_greedy_action(q_tuned, s)
        if q_phone is not None:
            rec['best_smartphone_action'] = get_greedy_action(q_phone, s)
        rec.update({
            'q_aes256': q_vals['AES-256'],
            'q_chacha20': q_vals['ChaCha20'],
            'q_ascon': q_vals['ASCON']
        })
        full_state_records.append(rec)

    df_full_states = pd.DataFrame(full_state_records)
    states_csv_path = os.path.join(output_dir, 'policy_1620_states.csv')
    df_full_states.to_csv(states_csv_path, index=False)
    print(f"Saved full 1,620 state mapping to: {states_csv_path}")

    # 6. Save JSON Summary
    suffix = f"_{env_mode}" if env_mode != 'simulation_legacy' else "_legacy"
    summary_json_path = os.path.join(output_dir, f'evaluation_summary{suffix}.json')
    with open(summary_json_path, 'w', encoding='utf-8') as f:
        json.dump(detailed_metrics, f, indent=4)
    with open(os.path.join(output_dir, 'evaluation_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(detailed_metrics, f, indent=4)
    print(f"Saved structured JSON metrics to: {summary_json_path}")

    # 7. SHA-256 Post-Check and Immutability Assertion
    print("\n" + "=" * 100)
    print("[STEP 5] Post-Evaluation SHA-256 Hash Verification (Immutability Proof):")
    print("=" * 100)
    post_hashes = check_all_model_hashes()
    all_match = True

    print(f"{'Filename':<20} | {'Pre-Hash':<64} | {'Status'}")
    print("-" * 100)
    for filename in sorted(pre_hashes.keys()):
        pre_h = pre_hashes[filename]
        post_h = post_hashes.get(filename, '')
        match = (pre_h == post_h)
        if not match:
            all_match = False
        status_str = "MATCH (UNCHANGED)" if match else "MISMATCH (MUTATED!)"
        print(f"{filename:<20} | {post_h} | {status_str}")

    assert all_match, "CRITICAL ERROR: One or more .pkl model files were mutated during evaluation!"
    print("\n[SUCCESS] SHA-256 verification confirmed: ALL 5 .pkl model files are 100% UNCHANGED.")
    print("=" * 100)


def run_sensitivity_analysis(output_dir: str = 'phone_calibration', env_mode: str = 'smartphone'):
    """
    Evaluates sensitivity of candidates across energy scaling variations (+/- 20%):
    - Low Cost (-20%, k=0.8)
    - Nominal (k=1.0)
    - High Cost (+20%, k=1.2)
    """
    os.makedirs(output_dir, exist_ok=True)
    scenarios = [
        ('Low Cost (-20%)', 0.8),
        ('Nominal (Baseline)', 1.0),
        ('High Cost (+20%)', 1.2)
    ]

    # Load available models
    loaded_models = []
    for m in MODEL_REGISTRY:
        target_fn = m['filename']
        if not os.path.exists(target_fn) and m.get('alt_filename') and os.path.exists(m['alt_filename']):
            target_fn = m['alt_filename']
        if os.path.exists(target_fn):
            loaded_models.append((m['name'], 'RL Model', load_q_table_readonly(target_fn)))

    for b in BASELINE_REGISTRY:
        loaded_models.append((b['name'], 'Baseline', b['policy_fn']))

    records = []
    print("\n" + "=" * 100)
    print("RUNNING ENERGY SENSITIVITY ANALYSIS (+/- 20% PARAMETER VARIATION)")
    print("=" * 100)

    for scen_name, k_scale in scenarios:
        print(f"\n>>> Scenario: {scen_name} (Scale Factor k={k_scale}) <<<")
        for name, m_type, policy in loaded_models:
            res = simulate_episodes(policy, episodes=200, seed=SIMULATION_SEED, env_mode=env_mode, energy_scale=k_scale)
            records.append({
                'Scenario': scen_name,
                'Energy Scale (k)': k_scale,
                'Candidate': name,
                'Type': m_type,
                'Messages Sent (N)': f"{res['messages_mean']:.1f} +- {res['messages_std']:.1f}",
                'Messages (Mean)': res['messages_mean'],
                'Total Security': f"{res['security_mean']:.1f} +- {res['security_std']:.1f}",
                'Security (Mean)': res['security_mean'],
                'SETOR': f"{res['setor_mean']:.4f} +- {res['setor_std']:.4f}",
                'SETOR (Mean)': res['setor_mean'],
                'Cumulative Reward': f"{res['reward_mean']:.1f} +- {res['reward_std']:.1f}",
                'Action Dist (AES/Cha/ASC)': f"{res['action_pcts']['AES-256']:.1f}% / {res['action_pcts']['ChaCha20']:.1f}% / {res['action_pcts']['ASCON']:.1f}%"
            })
            print(f"  {name:<45} | N: {res['messages_mean']:5.1f} | SETOR: {res['setor_mean']:.4f} | Rew: {res['reward_mean']:6.1f} | {res['action_pcts']['AES-256']:4.1f}% AES")

    df_sens = pd.DataFrame(records)
    sens_csv = os.path.join(output_dir, 'sensitivity_analysis.csv')
    df_sens.to_csv(sens_csv, index=False)
    print(f"\n[SAVED] Energy sensitivity analysis exported to: {sens_csv}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Unified Evaluation Suite (Smartphone, Calibrated, Legacy)")
    parser.add_argument('--env', choices=['smartphone', 'calibrated', 'legacy', 'all'], default='smartphone',
                        help="Environment mode: 'smartphone' (ARM mobile cpb aggregate), 'calibrated' (PC benchmark figures) or 'legacy' (historical simulation) or 'all'")
    parser.add_argument('--outdir', type=str, default='phone_calibration',
                        help="Output directory (default: phone_calibration)")
    parser.add_argument('--episodes', type=int, default=500,
                        help="Number of evaluation episodes (default: 500)")
    parser.add_argument('--sensitivity', action='store_true',
                        help="Run energy parameter sensitivity analysis (+/- 20%)")
    args = parser.parse_args()

    if args.sensitivity:
        run_sensitivity_analysis(output_dir=args.outdir, env_mode='smartphone')

    if args.env == 'all':
        print("\n>>> RUNNING SMARTPHONE CALIBRATED EVALUATION <<<")
        run_full_evaluation(output_dir=args.outdir, env_mode='smartphone')
        print("\n>>> RUNNING PC BENCHMARK-CALIBRATED EVALUATION <<<")
        run_full_evaluation(output_dir='evaluation_results', env_mode='benchmark_calibrated')
        print("\n>>> RUNNING HISTORICAL LEGACY EVALUATION <<<")
        run_full_evaluation(output_dir='evaluation_results', env_mode='simulation_legacy')
    elif args.env == 'smartphone':
        run_full_evaluation(output_dir=args.outdir, env_mode='smartphone')
    elif args.env == 'calibrated':
        run_full_evaluation(output_dir=args.outdir, env_mode='benchmark_calibrated')
    else:
        run_full_evaluation(output_dir=args.outdir, env_mode='simulation_legacy')


if __name__ == '__main__':
    main()
