"""
train.py
========
Reinforcement Learning training pipeline using modern `core/` package.

Key Architecture & Safety Improvements:
1. Pure keyword arguments (`alpha=`, `gamma=`, `epsilon=`, `filename=`) preventing positional parameter inversion.
2. Direct integration with `core.agent.QLearningAgent` and `core.environment.EncryptionEnvironment`.
3. Strict safety guard: Retraining is disabled by default to prevent accidental overwrite
   of legacy models (`initial_model.pkl`, `final_model.pkl`, etc.).
4. Requires explicit CLI arguments (`--train`, `--output <file>`) to run training sessions.
"""

import argparse
import sys
import os
from typing import Dict, List, Optional

from core.agent import QLearningAgent
from core.environment import EncryptionEnvironment

# Historic agent configurations documented explicitly with keyword arguments.
# NOTE: In legacy code, positional arguments passed (0.14, 0.56, 0.99) mapped to:
#   alpha = 0.14
#   epsilon = 0.56 (exploration rate)
#   gamma = 0.99 (discount factor)
# All configurations now explicitly specify parameter roles via keyword-only arguments.
HISTORIC_CONFIGS = {
    'initial_model': {
        'alpha': 0.1,
        'gamma': 0.5,
        'epsilon': 0.9,
        'filename': 'initial_model.pkl'
    },
    'model_2': {
        'alpha': 0.7,
        'gamma': 0.5,      # Default in legacy Agent.__init__
        'epsilon': 0.001,  # Passed as 2nd positional argument
        'filename': 'agent_brain2.pkl'
    },
    'model_3': {
        'alpha': 0.2,
        'gamma': 0.8,      # Passed as 3rd positional argument
        'epsilon': 0.8,    # Passed as 2nd positional argument
        'filename': 'agent_brain3.pkl'
    },
    'model_4': {
        'alpha': 0.12,
        'gamma': 0.99,     # Passed as 3rd positional argument
        'epsilon': 0.8,    # Passed as 2nd positional argument
        'filename': 'agent_brain4.pkl'
    },
    'final_model': {
        'alpha': 0.14,
        'gamma': 0.99,     # Passed as 3rd positional argument
        'epsilon': 0.56,   # Passed as 2nd positional argument
        'filename': 'final_model.pkl'
    }
}


def run_training_loop(
    agent: QLearningAgent,
    env: EncryptionEnvironment,
    episodes: int = 10000,
    save_filename: Optional[str] = None
) -> Dict[str, List[float]]:
    """
    Executes Watkins & Dayan Q-learning training across full battery-drain episodes.
    """
    history = {'reward': [], 'battery_life': []}

    print(f"Starting Q-Learning Training ({episodes} episodes)...")
    print(f"Agent Parameters: alpha={agent.alpha}, gamma={agent.gamma}, epsilon={agent.epsilon}")

    for i in range(1, episodes + 1):
        total_reward = 0.0
        steps = 0
        current_state = env.reset()
        done = False

        while not done:
            action = agent.select_action(current_state, training=True)
            next_state, reward, done = env.step(action)

            agent.update_q(current_state, action, reward, next_state)

            current_state = next_state
            total_reward += reward
            steps += 1

        history['reward'].append(total_reward)
        history['battery_life'].append(steps)

        if i % 1000 == 0 or i == episodes:
            avg_rew = sum(history['reward'][-100:]) / min(len(history['reward']), 100)
            avg_life = sum(history['battery_life'][-100:]) / min(len(history['battery_life']), 100)
            print(f"Episode {i:5d}/{episodes} | Avg Reward (last 100): {avg_rew:7.1f} | Avg Battery Life: {avg_life:5.1f} msgs")

    if save_filename:
        agent.save_brain(save_filename)
        print(f"Trained Q-table successfully saved to '{save_filename}'.")

    return history


def main():
    parser = argparse.ArgumentParser(
        description="Adaptive Cryptography IoT - Q-Learning Agent Training Harness"
    )
    parser.add_argument(
        '--train',
        action='store_true',
        help="Execute training session. If omitted, displays configuration without training."
    )
    parser.add_argument(
        '--config',
        type=str,
        default='final_model',
        choices=list(HISTORIC_CONFIGS.keys()),
        help="Historic configuration preset to train or inspect."
    )
    parser.add_argument(
        '--alpha',
        type=float,
        default=None,
        help="Learning rate alpha (overrides config preset)."
    )
    parser.add_argument(
        '--gamma',
        type=float,
        default=None,
        help="Discount factor gamma (overrides config preset)."
    )
    parser.add_argument(
        '--epsilon',
        type=float,
        default=None,
        help="Exploration rate epsilon (overrides config preset)."
    )
    parser.add_argument(
        '--episodes',
        type=int,
        default=10000,
        help="Number of training episodes (default: 10000)."
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help="Target output pickle file. NOTE: Existing legacy files cannot be overwritten without explicit permission."
    )
    parser.add_argument(
        '--force-overwrite',
        action='store_true',
        help="Force overwrite existing model files (use with extreme caution)."
    )

    args = parser.parse_args()

    cfg = HISTORIC_CONFIGS[args.config]
    alpha = args.alpha if args.alpha is not None else cfg['alpha']
    gamma = args.gamma if args.gamma is not None else cfg['gamma']
    epsilon = args.epsilon if args.epsilon is not None else cfg['epsilon']
    output_file = args.output if args.output else f"trained_{args.config}.pkl"

    print("=" * 70)
    print("Q-LEARNING AGENT CONFIGURATION SUMMARY")
    print("=" * 70)
    print(f"Preset Configuration : {args.config}")
    print(f"Alpha (Learning Rate): {alpha}")
    print(f"Gamma (Discount)     : {gamma}")
    print(f"Epsilon (Explore)    : {epsilon}")
    print(f"Episodes             : {args.episodes}")
    print(f"Target Output Path   : {output_file}")
    print("=" * 70)

    if not args.train:
        print("[INFO] Safety check active: Training was not executed.")
        print("To execute training, run:")
        print(f"  python train.py --train --config {args.config} --episodes {args.episodes} --output {output_file}")
        return

    # Check overwrite safety
    if os.path.exists(output_file) and not args.force_overwrite:
        if output_file in [c['filename'] for c in HISTORIC_CONFIGS.values()]:
            print(f"[BLOCKED] Target '{output_file}' is an original legacy model file.")
            print("To protect historical evaluation reproducibility, overwriting original files is prohibited.")
            print("Please specify a new output name via `--output <new_filename>.pkl`.")
            sys.exit(1)

    agent = QLearningAgent(
        alpha=alpha,
        gamma=gamma,
        epsilon=epsilon,
        filename=output_file
    )
    env = EncryptionEnvironment(mode='simulation_legacy')
    run_training_loop(agent, env, episodes=args.episodes, save_filename=output_file)


if __name__ == '__main__':
    main()
