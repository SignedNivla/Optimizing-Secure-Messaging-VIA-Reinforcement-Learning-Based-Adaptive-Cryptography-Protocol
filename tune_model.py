"""
tune_model.py
=============
Automated Hyperparameter Grid Search & Model Tuning Suite.

Enables systematic search for optimal Q-Learning agents to maximize:
1. Message Lifetime (N msgs per 100% battery)
2. Security-to-Energy Trade-Off Ratio (SETOR)
3. Cumulative Multi-Objective Reward
4. Security Adaptiveness (high-threat AES utilization vs low-power ChaCha20/Ascon)

Features:
- Automated multi-trial grid search over (alpha, gamma, epsilon_decay, episodes).
- Support for multiple training reward regimes:
  * 'legacy'   : Exact historical reward specification.
  * 'aligned'  : Physically aligned transmission efficiency (E_ChaCha=0.90, E_Ascon=0.80).
  * 'survival' : Adds explicit step-survival incentive (+1.0 per message delivered).
- Comparative evaluation against Static ChaCha20, Static AES, and historical Final Model.
- Automatic leaderboard generation and Pareto ranking.
- Saves the top-performing agent to 'best_tuned_model.pkl' (never overwriting legacy models).
- SHA-256 integrity verification of all legacy files before and after tuning.
"""

import os
import sys
import time
import json
import glob
import random
import hashlib
import argparse
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import pandas as pd

from core.agent import QLearningAgent
from core.environment import EncryptionEnvironment

SECURITY_WEIGHTS = {
    'AES-256': 1.0,
    'ChaCha20': 0.7,
    'ASCON': 0.4
}

STATIC_CHACHA_BASELINE = {
    'name': 'Static ChaCha20',
    'messages': 118.3,
    'security': 82.8,
    'setor': 0.8281,
    'reward': 6526.5
}

FINAL_MODEL_BASELINE = {
    'name': 'Historical Final Model',
    'messages': 106.4,
    'security': 59.4,
    'setor': 0.5944,
    'reward': 6606.5
}


LEGACY_MODEL_FILES = ['final_model.pkl', 'initial_model.pkl', 'agent_brain2.pkl', 'agent_brain3.pkl', 'agent_brain4.pkl']


def compute_file_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def check_all_model_hashes() -> Dict[str, str]:
    hashes = {}
    for pkl_file in LEGACY_MODEL_FILES:
        if os.path.exists(pkl_file):
            hashes[pkl_file] = compute_file_sha256(pkl_file)
    return hashes


class TunedEnvironment(EncryptionEnvironment):
    """Configurable environment supporting legacy, calibrated, smartphone, aligned, and survival reward regimes."""

    def __init__(self, mode: str = 'smartphone', survival_bonus: float = 0.0, energy_scale: float = 1.0):
        if mode in ['smartphone', 'mobile']:
            env_mode = 'smartphone'
        elif mode == 'legacy':
            env_mode = 'simulation_legacy'
        else:
            env_mode = 'benchmark_calibrated'
        super().__init__(mode=env_mode, energy_scale=energy_scale)
        self.reward_regime = mode
        self.survival_bonus = survival_bonus

    def calculate_reward(self, action: str) -> float:
        if self.reward_regime in ['smartphone', 'mobile', 'legacy']:
            return super().calculate_reward(action) + self.survival_bonus

        # Benchmark calibrated specs:
        # AES-256:  S=1.0, E=0.90 (709.7 MB/s, 2.42 us latency)
        # ChaCha20: S=0.7, E=0.95 (849.9 MB/s, 2.26 us latency)
        # ASCON:    S=0.4, E=0.20 (0.58 MB/s, 199.1 us latency)
        if self.reward_regime == 'calibrated':
            specs = {
                'AES-256':  {'S': 1.0, 'E': 0.90},
                'ChaCha20': {'S': 0.7, 'E': 0.95},
                'ASCON':    {'S': 0.4, 'E': 0.20}
            }
        else:
            specs = {
                'AES-256':  {'S': 1.0, 'E': 0.20},
                'ChaCha20': {'S': 0.7, 'E': 0.90},
                'ASCON':    {'S': 0.4, 'E': 0.80}
            }

        threat = self.get_labels()['threat']
        network = self.get_labels()['network']
        battery = self.battery
        signal = self.get_labels()['signal']
        size = self.get_labels()['size']
        priority = self.get_labels()['priority']

        w_sec = 0.5
        w_eff = 0.5

        if priority == 'important':
            w_sec += 0.2
            w_eff -= 0.2
        elif priority == 'unimportant':
            w_sec -= 0.2
            w_eff += 0.2

        if threat == 'high':
            w_sec += 0.3
            w_eff -= 0.3
        elif threat == 'low':
            w_sec -= 0.2
            w_eff += 0.2

        if network == 'public':
            w_sec += 0.1
            w_eff -= 0.1

        if battery < 20:
            w_sec -= 0.4
            w_eff += 0.4
        elif battery < 50:
            w_sec -= 0.2
            w_eff += 0.2

        if signal == 'weak':
            w_eff += 0.2
            w_sec -= 0.2
        elif signal == 'strong':
            w_sec += 0.1
            w_eff -= 0.1

        if size == 'large':
            w_eff += 0.2
            w_sec -= 0.2
        elif size == 'small':
            w_sec += 0.1
            w_eff -= 0.1

        total = w_sec + w_eff
        if total != 0:
            w_sec = w_sec / total
            w_eff = w_eff / total
        else:
            w_sec, w_eff = 0.5, 0.5

        s_score = specs[action]['S']
        e_score = specs[action]['E']
        base_reward = 100.0 * (w_sec * s_score + w_eff * e_score)
        return base_reward + self.survival_bonus


def train_candidate(
    alpha: float,
    gamma: float,
    episodes: int = 10000,
    eps_start: float = 1.0,
    eps_min: float = 0.02,
    eps_decay: float = 0.9995,
    reward_mode: str = 'legacy',
    survival_bonus: float = 0.0
) -> QLearningAgent:
    """Trains a single Q-Learning agent with optional epsilon decay."""
    agent = QLearningAgent(alpha=alpha, gamma=gamma, epsilon=eps_start)
    env = TunedEnvironment(mode=reward_mode, survival_bonus=survival_bonus)

    eps = eps_start
    for _ in range(episodes):
        agent.epsilon = eps
        state = env.reset()
        done = False
        while not done:
            action = agent.get_action(state, training=True)
            next_state, reward, done = env.step(action)
            agent.update_q(state, action, reward, next_state)
            state = next_state
        eps = max(eps_min, eps * decay) if (decay := eps_decay) else eps

    return agent


def evaluate_candidate(
    agent: QLearningAgent,
    eval_episodes: int = 200,
    seed: int = 42,
    env_mode: str = 'benchmark_calibrated'
) -> Dict[str, Any]:
    """
    Evaluates candidate under specified environment mode (calibrated or legacy).
    """
    random.seed(seed)
    np.random.seed(seed)
    env = EncryptionEnvironment(mode=env_mode)

    ep_msgs = []
    ep_secs = []
    ep_rews = []
    ep_setor = []
    action_counts = {'AES-256': 0, 'ChaCha20': 0, 'ASCON': 0}
    high_threat_acts = {'AES-256': 0, 'ChaCha20': 0, 'ASCON': 0}

    for _ in range(eval_episodes):
        state = env.reset()
        start_battery = env.battery
        done = False
        steps = 0
        tot_sec = 0.0
        tot_rew = 0.0

        while not done:
            action = agent.get_action(state, training=False)
            action_counts[action] += 1
            if state[0] == 2:  # Threat == 2 (Tinggi)
                high_threat_acts[action] += 1

            sec_score = SECURITY_WEIGHTS[action]
            tot_sec += sec_score

            next_state, reward, done = env.step(action)
            tot_rew += reward
            steps += 1
            state = next_state

        end_battery = env.battery
        delta_battery = start_battery - end_battery

        ep_msgs.append(steps)
        ep_secs.append(tot_sec)
        ep_rews.append(tot_rew)
        ep_setor.append(tot_sec / max(1e-6, delta_battery) if delta_battery > 0 else 0.0)

    tot_acts = max(1, sum(action_counts.values()))
    tot_high = max(1, sum(high_threat_acts.values()))

    return {
        'messages_mean': float(np.mean(ep_msgs)),
        'messages_std': float(np.std(ep_msgs)),
        'security_mean': float(np.mean(ep_secs)),
        'security_std': float(np.std(ep_secs)),
        'setor_mean': float(np.mean(ep_setor)),
        'setor_std': float(np.std(ep_setor)),
        'reward_mean': float(np.mean(ep_rews)),
        'reward_std': float(np.std(ep_rews)),
        'pct_aes': (action_counts['AES-256'] / tot_acts) * 100.0,
        'pct_chacha': (action_counts['ChaCha20'] / tot_acts) * 100.0,
        'pct_ascon': (action_counts['ASCON'] / tot_acts) * 100.0,
        'high_threat_aes_pct': (high_threat_acts['AES-256'] / tot_high) * 100.0
    }


def compute_pareto_score(
    metrics: Dict[str, Any],
    w_msg: float = 0.35,
    w_sec: float = 0.35,
    w_adapt: float = 0.30,
    regime: str = 'smartphone'
) -> float:
    """
    Calculates multi-objective score normalized against baseline targets:
    - w_msg: Message lifetime normalized to baseline capacity
    - w_sec: SETOR normalized to baseline
    - w_adapt: High-threat AES usage (ensures security adaptiveness)
    """
    if regime in ['smartphone', 'mobile']:
        norm_msg = metrics['messages_mean'] / 110.0
        norm_setor = metrics['setor_mean'] / 0.85
        norm_adapt = metrics['high_threat_aes_pct'] / 50.0
    elif regime == 'calibrated':
        norm_msg = metrics['messages_mean'] / 110.6
        norm_setor = metrics['setor_mean'] / 1.0572
        norm_adapt = metrics['high_threat_aes_pct'] / 70.0
    else:
        norm_msg = metrics['messages_mean'] / 118.3
        norm_setor = metrics['setor_mean'] / 0.8281
        norm_adapt = metrics['high_threat_aes_pct'] / 35.0
    return (w_msg * norm_msg) + (w_sec * norm_setor) + (w_adapt * norm_adapt)


def run_grid_search(
    alpha_list: List[float],
    gamma_list: List[float],
    episodes: int = 10000,
    reward_mode: str = 'legacy',
    survival_bonus: float = 0.0,
    output_model_path: str = 'best_tuned_model.pkl',
    results_dir: str = 'tuning_results'
) -> Tuple[pd.DataFrame, QLearningAgent]:
    """Executes hyperparameter grid search across specified configurations."""
    os.makedirs(results_dir, exist_ok=True)

    print("=" * 100)
    print("HYPERPARAMETER GRID SEARCH & MODEL TUNING SUITE")
    print("=" * 100)
    print(f"Target Reward Regime : {reward_mode.upper()} (survival bonus: {survival_bonus})")
    print(f"Episodes per Trial   : {episodes}")
    print(f"Alpha Candidates     : {alpha_list}")
    print(f"Gamma Candidates     : {gamma_list}")
    print(f"Total Trials         : {len(alpha_list) * len(gamma_list)}")
    print("-" * 100)
    print(f"BENCHMARK TARGETS:")
    print(f"  - Static ChaCha20   : {STATIC_CHACHA_BASELINE['messages']:.1f} msgs | SETOR {STATIC_CHACHA_BASELINE['setor']:.4f} | Reward {STATIC_CHACHA_BASELINE['reward']:.1f} (0% AES)")
    print(f"  - Hist. Final Model : {FINAL_MODEL_BASELINE['messages']:.1f} msgs | SETOR {FINAL_MODEL_BASELINE['setor']:.4f} | Reward {FINAL_MODEL_BASELINE['reward']:.1f} (8.9% AES)")
    print("=" * 100)

    # SHA-256 pre-check to guarantee zero mutation of legacy models
    pre_hashes = check_all_model_hashes()

    leaderboard = []
    best_agent = None
    best_score = -float('inf')
    best_trial_info = None

    trial_idx = 1
    total_trials = len(alpha_list) * len(gamma_list)

    for alpha in alpha_list:
        for gamma in gamma_list:
            t0 = time.perf_counter()
            print(f"[{trial_idx:02d}/{total_trials:02d}] Training: alpha={alpha:<4}, gamma={gamma:<5} ...", end="", flush=True)

            agent = train_candidate(
                alpha=alpha,
                gamma=gamma,
                episodes=episodes,
                eps_start=1.0,
                eps_min=0.02,
                eps_decay=0.9995,
                reward_mode=reward_mode,
                survival_bonus=survival_bonus
            )

            # Evaluate candidate on 200 episodes
            if reward_mode in ['smartphone', 'mobile']:
                target_env = 'smartphone'
            elif reward_mode == 'legacy':
                target_env = 'simulation_legacy'
            else:
                target_env = 'benchmark_calibrated'

            metrics = evaluate_candidate(agent, eval_episodes=200, seed=42, env_mode=target_env)
            score = compute_pareto_score(metrics, regime=reward_mode)
            elapsed = time.perf_counter() - t0

            print(f" Done ({elapsed:.1f}s) | N: {metrics['messages_mean']:5.1f} | SETOR: {metrics['setor_mean']:.4f} | Rew: {metrics['reward_mean']:6.1f} | Score: {score:.4f} | AES(High): {metrics['high_threat_aes_pct']:4.1f}%")

            trial_record = {
                'trial': trial_idx,
                'alpha': alpha,
                'gamma': gamma,
                'reward_mode': reward_mode,
                'survival_bonus': survival_bonus,
                'episodes': episodes,
                'messages': f"{metrics['messages_mean']:.1f} +- {metrics['messages_std']:.1f}",
                'messages_val': metrics['messages_mean'],
                'security': f"{metrics['security_mean']:.1f} +- {metrics['security_std']:.1f}",
                'setor': f"{metrics['setor_mean']:.4f} +- {metrics['setor_std']:.4f}",
                'setor_val': metrics['setor_mean'],
                'reward': f"{metrics['reward_mean']:.1f} +- {metrics['reward_std']:.1f}",
                'reward_val': metrics['reward_mean'],
                'pct_aes': f"{metrics['pct_aes']:.1f}%",
                'pct_chacha': f"{metrics['pct_chacha']:.1f}%",
                'pct_ascon': f"{metrics['pct_ascon']:.1f}%",
                'high_threat_aes': f"{metrics['high_threat_aes_pct']:.1f}%",
                'pareto_score': score
            }
            leaderboard.append(trial_record)

            if score > best_score:
                best_score = score
                best_agent = agent
                best_trial_info = trial_record

            trial_idx += 1

    df_leaderboard = pd.DataFrame(leaderboard).sort_values(by='pareto_score', ascending=False)
    csv_path = os.path.join(results_dir, 'tuning_leaderboard.csv')
    df_leaderboard.to_csv(csv_path, index=False)

    # Save best candidate model
    if best_agent is not None:
        best_agent.save_brain(output_model_path)
        print(f"\n[SAVED] Top-performing candidate model saved to: '{output_model_path}'")

    # Display Top 5 Leaderboard
    print("\n" + "=" * 100)
    print("TUNING LEADERBOARD (TOP 5 CANDIDATES BY PARETO SCORE)")
    print("=" * 100)
    display_cols = [
        'trial', 'alpha', 'gamma', 'messages', 'setor', 'reward',
        'pct_aes', 'pct_chacha', 'pct_ascon', 'high_threat_aes', 'pareto_score'
    ]
    print(df_leaderboard[display_cols].head(5).to_string(index=False))
    print(f"\nFull leaderboard exported to: {csv_path}")

    # SHA-256 post-check assertion
    post_hashes = check_all_model_hashes()
    for f_name, pre_h in pre_hashes.items():
        assert pre_h == post_hashes[f_name], f"CRITICAL: Legacy file {f_name} was mutated!"
    print("\n[VERIFIED] All legacy models (.pkl) confirmed 100% UNCHANGED via SHA-256.")
    print("=" * 100)

    return df_leaderboard, best_agent


def main():
    parser = argparse.ArgumentParser(description="Adaptive Cryptography IoT - Hyperparameter Tuning & Grid Search")
    parser.add_argument('--mode', type=str, default='smartphone', choices=['smartphone', 'calibrated', 'legacy', 'aligned', 'survival'],
                        help="Reward regime: 'smartphone' (ARM mobile cpb aggregate), 'calibrated' (PC benchmark figures), 'legacy' (original), 'aligned' (transmission cost), 'survival' (longevity bonus)")
    parser.add_argument('--survival-bonus', type=float, default=0.0,
                        help="Step survival reward bonus when --mode survival is selected (default: 0.0)")
    parser.add_argument('--episodes', type=int, default=10000,
                        help="Number of training episodes per candidate trial (default: 10000)")
    parser.add_argument('--outdir', type=str, default='phone_calibration',
                        help="Directory to save leaderboard and model (default: phone_calibration)")
    parser.add_argument('--output', type=str, default='best_smartphone_model.pkl',
                        help="Target output pickle file for best candidate (default: best_smartphone_model.pkl)")
    parser.add_argument('--fast', action='store_true',
                        help="Fast sweep mode (fewer trials with 5000 episodes for quick feedback)")

    args = parser.parse_args()

    # Safety check: prevent overwriting historical models
    legacy_files = ['final_model.pkl', 'initial_model.pkl', 'agent_brain2.pkl', 'agent_brain3.pkl', 'agent_brain4.pkl']
    if os.path.basename(args.output) in legacy_files:
        print(f"[BLOCKED] Target '{args.output}' is an original legacy model.")
        print("Please specify a new output name via `--output <new_model_name>.pkl`.")
        sys.exit(1)

    if args.fast:
        alpha_candidates = [0.08, 0.10, 0.14]
        gamma_candidates = [0.90, 0.95, 0.99]
        episodes = 5000
    else:
        alpha_candidates = [0.05, 0.08, 0.10, 0.14, 0.20]
        gamma_candidates = [0.85, 0.90, 0.95, 0.98, 0.999]
        episodes = args.episodes

    s_bonus = args.survival_bonus if args.mode == 'survival' else 0.0

    target_path = os.path.join(args.outdir, os.path.basename(args.output))

    run_grid_search(
        alpha_list=alpha_candidates,
        gamma_list=gamma_candidates,
        episodes=episodes,
        reward_mode=args.mode,
        survival_bonus=s_bonus,
        output_model_path=target_path,
        results_dir=args.outdir
    )

    # Also save a copy to root output name if different
    if target_path != args.output and os.path.exists(target_path):
        import shutil
        shutil.copy2(target_path, args.output)


if __name__ == '__main__':
    main()

