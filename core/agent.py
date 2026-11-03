"""
core.agent
==========
Tabular Q-Learning Agent implementation for Adaptive Cryptography.
Enforces keyword-only hyperparameters (alpha, gamma, epsilon) to prevent positional
order bugs, and strictly separates training exploration (epsilon-greedy) from evaluation (100% greedy).
"""

import pickle
import random
from typing import Dict, Tuple, Optional, List
from core.state import ACTIONS


class QLearningAgent:
    """
    Tabular Q-Learning Agent.
    
    Q-table data format:
        Dict[Tuple[int, int, int, int, int, int], Dict[str, float]]
        e.g. { (1, 1, 9, 1, 1, 1): {'AES-256': 4507.12, 'ChaCha20': 4513.52, 'ASCON': 4557.05} }
    """
    def __init__(
        self,
        *,
        alpha: float = 0.10,
        gamma: float = 0.90,
        epsilon: float = 0.50,
        filename: Optional[str] = None
    ):
        self.alpha: float = alpha
        self.gamma: float = gamma
        self.epsilon: float = epsilon
        self.filename: Optional[str] = filename
        self.actions: Tuple[str, ...] = ACTIONS
        self.q_table: Dict[Tuple[int, ...], Dict[str, float]] = {}

        if self.filename:
            self.load_brain(self.filename)

    def load_brain(self, filename: Optional[str] = None) -> bool:
        """
        Loads Q-table from a pickle file.
        Returns True if loaded successfully, False if file not found.
        """
        target = filename or self.filename
        if not target:
            return False
        try:
            with open(target, 'rb') as f:
                loaded = pickle.load(f)
            if not isinstance(loaded, dict):
                raise ValueError(f"Expected dict in {target}, got {type(loaded)}")
            self.q_table = loaded
            self.filename = target
            return True
        except FileNotFoundError:
            return False

    def save_brain(self, filename: Optional[str] = None) -> None:
        """Saves current Q-table to a pickle file."""
        target = filename or self.filename
        if not target:
            raise ValueError("No filename specified to save Q-table.")
        with open(target, 'wb') as f:
            pickle.dump(self.q_table, f)

    def _init_state(self, state: Tuple[int, ...]) -> None:
        """Ensures state exists in Q-table initialized with zeros."""
        if state not in self.q_table:
            self.q_table[state] = {action: 0.0 for action in self.actions}

    def get_action(self, state: Tuple[int, ...], training: bool = False) -> str:
        """
        Action selection strategy:
        - If training=False (Evaluation): 100% GREEDY (epsilon = 0).
        - If training=True (Training): Epsilon-greedy with probability self.epsilon.
        """
        self._init_state(state)
        curr_epsilon = self.epsilon if training else 0.0
        if curr_epsilon > 0 and random.uniform(0, 1) < curr_epsilon:
            return random.choice(self.actions)
        else:
            state_scores = self.q_table[state]
            return max(state_scores, key=state_scores.get)

    # Alias for backward and forward compatibility
    select_action = get_action
    choose_action = get_action

    def update_q(
        self,
        state: Tuple[int, ...],
        action: str,
        reward: float,
        next_state: Tuple[int, ...]
    ) -> None:
        """
        Watkins & Dayan Q-learning update:
        Q(s, a) <- Q(s, a) + alpha * [reward + gamma * max_a'(Q(s', a')) - Q(s, a)]
        """
        self._init_state(state)
        self._init_state(next_state)

        old_value = self.q_table[state][action]
        max_future = max(self.q_table[next_state].values())
        target = reward + (self.gamma * max_future)
        new_value = old_value + self.alpha * (target - old_value)
        self.q_table[state][action] = new_value

    def get_state_q_values(self, state: Tuple[int, ...]) -> Dict[str, float]:
        """Returns Q-values for a given state tuple."""
        return self.q_table.get(state, {a: 0.0 for a in self.actions})

