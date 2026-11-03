"""
Agent.agent (Backward Compatibility Shim)
=========================================
Compatibility shim delegating to the unified `core.agent.QLearningAgent`.

Preserves 100% API compatibility for legacy scripts (test.py, legacy callers):
- _choose_action(state, training)
- _update_q_table(state, action, reward, next_state)
- _load_brain()
- _save_brain()
- test(threat, network, battery, signal, size, priority)
- train(episodes, training)
"""

import os
from typing import Optional, Any

from core.agent import QLearningAgent as CoreQLearningAgent
from core.environment import EncryptionEnvironment as CoreEnv
from Agent.state_component import (
    BatteryState,
    NetworkState,
    PriorityState,
    SignalState,
    SizeState,
    ThreatState
)


class QLearningAgent(CoreQLearningAgent):
    """Legacy-compatible QLearningAgent wrapper delegating to core.agent.QLearningAgent."""

    def __init__(
        self,
        alpha: float = 0.1,
        epsilon: float = 0.5,
        gamma: float = 0.9,
        filename: str = 'agent_brain.pkl'
    ):
        # NOTE: Positional arguments in legacy: (alpha, epsilon, gamma, filename)
        super().__init__(
            alpha=alpha,
            gamma=gamma,
            epsilon=epsilon,
            filename=filename
        )
        self.action = self.actions  # Legacy alias
        if filename and os.path.exists(filename):
            self._load_brain()

    def _choose_action(self, state: Any, training: bool = True) -> str:
        return self.select_action(state, training=training)

    def _update_q_table(self, state: Any, action: str, reward: float, next_state: Any) -> None:
        self.update_q(state, action, reward, next_state)

    def _initialize_state(self, state: Any) -> None:
        self._init_state(state)

    def _load_brain(self) -> bool:
        success = self.load_brain()
        if success:
            print("Brain loaded! I remember my training.")
            return False
        else:
            print("No saved brain found. Starting fresh.")
            return True

    def _save_brain(self) -> None:
        self.save_brain()
        print("Brain saved successfully!")

    def test(
        self,
        threat: Optional[Any] = None,
        network: Optional[Any] = None,
        battery: Optional[Any] = None,
        signal: Optional[Any] = None,
        size: Optional[Any] = None,
        priority: Optional[Any] = None
    ) -> None:
        """Executes a single test case report matching legacy formatting."""
        t_val = threat.get_value() if hasattr(threat, 'get_value') else threat
        n_val = network.get_value() if hasattr(network, 'get_value') else network
        b_val = battery.get_value() if hasattr(battery, 'get_value') else battery
        s_val = signal.get_value() if hasattr(signal, 'get_value') else signal
        sz_val = size.get_value() if hasattr(size, 'get_value') else size
        p_val = priority.get_value() if hasattr(priority, 'get_value') else priority

        env = CoreEnv(
            threat=t_val,
            network=n_val,
            battery=b_val,
            signal=s_val,
            size=sz_val,
            priority=p_val,
            mode='simulation_legacy'
        )
        action = self.select_action(env.get_current_state(), training=False)
        labels = env.get_labels()

        print("--- Agent Decision Report ---")
        print(f"Context: {labels['threat']} threat on a {labels['network']} network.")
        print(f"Device Status: Battery at {labels['battery']}%, Signal is {labels['signal']}.")
        print(f"Data Info: {labels['size']} payload with {labels['priority']} priority.")
        print(f"RESULT >> Agent selected: **{action}**")
