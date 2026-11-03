"""
Agent.encryption_environment (Backward Compatibility Shim)
==========================================================
Compatibility wrapper around modern `core.environment.EncryptionEnvironment`.

Preserves legacy method names:
- _get_current_state()
- _calculate_reward(action)
- _calculate_cost(action)
- reset()
- step(action)
- generate_random_*()
"""

import random
from typing import Optional, Any, Tuple

from core.environment import EncryptionEnvironment as CoreEnv
from Agent.state_component import (
    NetworkState,
    BatteryState,
    PriorityState,
    SignalState,
    SizeState,
    ThreatState
)


class EncryptionEnvironment:
    """Legacy-compatible environment wrapper wrapping core.environment.EncryptionEnvironment."""

    def __init__(
        self,
        threat: Optional[ThreatState] = None,
        network: Optional[NetworkState] = None,
        battery: Optional[BatteryState] = None,
        signal: Optional[SignalState] = None,
        size: Optional[SizeState] = None,
        priority: Optional[PriorityState] = None
    ):
        self.threat = threat if threat else ThreatState(self.generate_random_threat())
        self.network = network if network else NetworkState(self.generate_random_network())
        self.battery = battery if battery else BatteryState(100)
        self.signal = signal if signal else SignalState(self.generate_random_signal())
        self.size = size if size else SizeState(self.generate_random_size())
        self.priority = priority if priority else PriorityState(self.generate_random_priority())

        self._core_env = CoreEnv(
            threat=self.threat.get_value(),
            network=self.network.get_value(),
            battery=float(self.battery.get_value()),
            signal=self.signal.get_value(),
            size=self.size.get_value(),
            priority=self.priority.get_value(),
            mode='simulation_legacy'
        )

    def _sync_to_core(self) -> None:
        self._core_env.set_context(
            threat=self.threat.get_value(),
            network=self.network.get_value(),
            battery=float(self.battery.get_value()),
            signal=self.signal.get_value(),
            size=self.size.get_value(),
            priority=self.priority.get_value()
        )

    def _sync_from_core(self) -> None:
        self.threat.set_value(self._core_env.threat)
        self.network.set_value(self._core_env.network)
        self.battery.set_value(int(self._core_env.battery))
        self.signal.set_value(self._core_env.signal)
        self.size.set_value(self._core_env.size)
        self.priority.set_value(self._core_env.priority)

    def generate_random_threat(self) -> int:
        return random.randint(0, 3)

    def generate_random_network(self) -> str:
        return random.choice(['private', 'public'])

    def generate_random_signal(self) -> int:
        return random.randint(0, 5)

    def generate_random_size(self) -> int:
        return random.randint(0, 250)

    def generate_random_priority(self) -> int:
        return random.randint(0, 3)

    def reset(self) -> Tuple[int, int, int, int, int, int]:
        self.threat.set_value(self.generate_random_threat())
        self.network.set_value(self.generate_random_network())
        self.battery.set_value(100)
        self.signal.set_value(self.generate_random_signal())
        self.size.set_value(self.generate_random_size())
        self.priority.set_value(self.generate_random_priority())
        self._sync_to_core()
        return self._get_current_state()

    def _get_current_state(self) -> Tuple[int, int, int, int, int, int]:
        self._sync_to_core()
        return self._core_env.get_current_state()

    def _calculate_reward(self, action: str) -> float:
        self._sync_to_core()
        return self._core_env.calculate_reward(action)

    def _calculate_cost(self, action: str) -> Tuple[float, float, float]:
        self._sync_to_core()
        return self._core_env.calculate_cost(action)

    def step(self, action: str) -> Tuple[Tuple[int, int, int, int, int, int], float, bool]:
        self._sync_to_core()
        next_state, reward, done = self._core_env.step(action)
        self._sync_from_core()
        return next_state, reward, done
