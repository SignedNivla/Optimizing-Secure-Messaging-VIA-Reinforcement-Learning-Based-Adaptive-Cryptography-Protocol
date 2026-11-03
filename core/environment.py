"""
core.environment
================
Markov Decision Process Environment for Adaptive Cryptography.
Faithfully implements the simulation dynamics, cost model, and multi-objective
reward function. Defaults to 'simulation_legacy' to guarantee 100% exact numerical
reproducibility with legacy experimental results.
"""

import random
from typing import Tuple, Dict, Any, Optional
from core.state import (
    encode_state,
    get_state_labels,
    discretize_threat,
    discretize_network,
    discretize_battery,
    discretize_signal,
    discretize_size,
    discretize_priority,
    ACTIONS
)


class EncryptionEnvironment:
    """
    Simulation Environment for Adaptive Cryptographic Decision Policy.
    
    Modes:
    - 'simulation_legacy' (default): Preserves the exact simulation cost model,
      reward specifications, and terminal penalty (-500) of the paper.
    """

    # Legacy simulation specifications (matching Agent/encryption_environment.py)
    LEGACY_SPECS = {
        'AES-256':  {'S': 1.0, 'E': 0.2},
        'ChaCha20': {'S': 0.7, 'E': 0.5},
        'ASCON':    {'S': 0.4, 'E': 1.0}
    }
    LEGACY_COST = {'AES-256': 0.25, 'ChaCha20': 0.10, 'ASCON': 0.05}
    LEGACY_OVERHEAD = {'AES-256': 2.13, 'ChaCha20': 1.00, 'ASCON': 1.53}
    LEGACY_SIZE_MAP = {'small': 1, 'medium': 5, 'large': 15}

    # Empirical benchmark-calibrated specifications (derived from benchmark_raw_results.json):
    # 1. Processing cost derived from median encryption latency (32 B payload):
    #    ChaCha20-Poly1305: 2.26 us -> baseline 0.10%
    #    AES-256-GCM: 2.42 us -> (2.42 / 2.26) * 0.10 = 0.107% -> 0.11%
    #    Ascon-AEAD128: 199.09 us -> pure-Python reference execution cost -> 0.35%
    BENCHMARK_COST = {'AES-256': 0.11, 'ChaCha20': 0.10, 'ASCON': 0.35}

    # 2. Standardized AEAD tag transmission overhead (16-byte raw authentication tag, no Base64 bloat):
    #    Small (32 B)  : (32 + 16) / 32 = 1.500
    #    Medium (128 B): (128 + 16) / 128 = 1.125
    #    Large (1024 B): (1024 + 16) / 1024 = 1.016
    BENCHMARK_OVERHEAD = {'small': 1.500, 'medium': 1.125, 'large': 1.016}

    # 3. Efficiency ratings S and E derived from empirical throughput and security level:
    BENCHMARK_SPECS = {
        'AES-256':  {'S': 1.0, 'E': 0.90},  # High throughput (13.2 - 709.7 MB/s), 256-bit security
        'ChaCha20': {'S': 0.7, 'E': 0.95},  # Highest throughput (14.2 - 849.9 MB/s), 256-bit security
        'ASCON':    {'S': 0.4, 'E': 0.20}   # Python benchmark throughput (0.16 - 0.58 MB/s), 128-bit
    }

    # 4. Smartphone mobile calibration specifications (literature aggregate eBACS/RFC 8439 on ARM):
    #    ChaCha20-Poly1305: 10 cpb -> BaseCost 0.10% -> E = 0.10 / 0.10 = 1.000
    #    AES-256-GCM      : 22 cpb -> BaseCost 0.22% -> E = 0.10 / 0.22 = 0.455
    #    Ascon-AEAD128    : 18 cpb -> BaseCost 0.18% -> E = 0.10 / 0.18 = 0.556
    SMARTPHONE_COST = {'AES-256': 0.22, 'ChaCha20': 0.10, 'ASCON': 0.18}
    SMARTPHONE_SPECS = {
        'AES-256':  {'S': 1.0, 'E': 0.455},  # Software AES on ARM without AES-NI (22 cpb)
        'ChaCha20': {'S': 0.7, 'E': 1.000},  # ARX constant-time ARM integer ALU (10 cpb)
        'ASCON':    {'S': 0.4, 'E': 0.556}   # Ascon-AEAD128 (NIST SP 800-232, 18 cpb)
    }

    def __init__(
        self,
        threat: Optional[int] = None,
        network: Optional[str] = None,
        battery: Optional[float] = None,
        signal: Optional[int] = None,
        size: Optional[int] = None,
        priority: Optional[int] = None,
        mode: str = 'simulation_legacy',
        energy_scale: float = 1.0
    ):
        self.mode = mode
        self.energy_scale = float(energy_scale)
        self.threat: int = threat if threat is not None else self._sample_threat()
        self.network: str = network if network is not None else self._sample_network()
        self.battery: float = float(battery if battery is not None else 100.0)
        self.signal: int = signal if signal is not None else self._sample_signal()
        self.size: int = size if size is not None else self._sample_size()
        self.priority: int = priority if priority is not None else self._sample_priority()

    @staticmethod
    def _sample_threat() -> int:
        return random.randint(0, 3)

    @staticmethod
    def _sample_network() -> str:
        return random.choice(['private', 'public'])

    @staticmethod
    def _sample_signal() -> int:
        return random.randint(0, 5)

    @staticmethod
    def _sample_size() -> int:
        return random.randint(0, 250)

    @staticmethod
    def _sample_priority() -> int:
        return random.randint(0, 3)

    def reset(self) -> Tuple[int, int, int, int, int, int]:
        """Resets the environment to initial 100% battery and fresh random context."""
        self.battery = 100.0
        self.threat = self._sample_threat()
        self.network = self._sample_network()
        self.signal = self._sample_signal()
        self.size = self._sample_size()
        self.priority = self._sample_priority()
        return self.get_current_state()

    def get_current_state(self) -> Tuple[int, int, int, int, int, int]:
        """Returns the current 6-tuple state representation."""
        return encode_state(
            self.threat,
            self.network,
            self.battery,
            self.signal,
            self.size,
            self.priority
        )

    def get_labels(self) -> Dict[str, str]:
        """Returns the current human-readable labels."""
        return get_state_labels(
            self.threat,
            self.network,
            self.battery,
            self.signal,
            self.size,
            self.priority
        )

    def set_context(
        self,
        threat: Optional[int] = None,
        network: Optional[str] = None,
        battery: Optional[float] = None,
        signal: Optional[int] = None,
        size: Optional[int] = None,
        priority: Optional[int] = None
    ) -> None:
        """Explicitly sets environmental state variables (useful for deterministic tests)."""
        if threat is not None:
            self.threat = threat
        if network is not None:
            self.network = network
        if battery is not None:
            self.battery = float(battery)
        if signal is not None:
            self.signal = signal
        if size is not None:
            self.size = size
        if priority is not None:
            self.priority = priority

    def calculate_reward(self, action: str) -> float:
        """
        Calculates multi-objective step reward according to legacy formulation (M1).
        Reward = 100 * [w_sec * S(a) + w_eff * E(a)]
        """
        labels = self.get_labels()
        threat = labels['threat']
        network = labels['network']
        signal = labels['signal']
        size = labels['size']
        priority = labels['priority']

        w_sec = 0.5
        w_eff = 0.5

        # Battery ratio adjustment
        w_eff += (100.0 - self.battery) / 200.0

        if network == "public" or threat == "high":
            w_sec += 0.3
        if priority == "important":
            w_sec += 0.4
            w_eff += 0.2
        elif size == 'large' or signal == 'weak':
            w_eff += 0.2

        total = w_sec + w_eff
        w_sec /= total
        w_eff /= total

        if self.mode in ['smartphone', 'mobile']:
            specs = self.SMARTPHONE_SPECS
        elif self.mode == 'benchmark_calibrated':
            specs = self.BENCHMARK_SPECS
        else:
            specs = self.LEGACY_SPECS

        spec = specs[action]
        reward = (w_sec * spec['S']) + (w_eff * spec['E'])
        return reward * 100.0

    def calculate_cost(self, action: str) -> Tuple[float, float, float]:
        """
        Calculates battery consumption for the chosen action and current payload size:
        Returns: (processing_cost, transmission_cost, total_cost)
        """
        size_label = self.get_labels()['size']
        size_multiplier = self.LEGACY_SIZE_MAP[size_label]

        if self.mode in ['smartphone', 'mobile']:
            proc_cost = (self.SMARTPHONE_COST[action] * self.energy_scale) * size_multiplier
            overhead_val = self.BENCHMARK_OVERHEAD[size_label]
            trans_cost = (overhead_val * (size_multiplier * 0.1)) * self.energy_scale
            total_cost = proc_cost + trans_cost
            return proc_cost, trans_cost, total_cost

        if self.mode == 'benchmark_calibrated':
            proc_cost = (self.BENCHMARK_COST[action] * self.energy_scale) * size_multiplier
            overhead_val = self.BENCHMARK_OVERHEAD[size_label]
            trans_cost = (overhead_val * (size_multiplier * 0.1)) * self.energy_scale
            total_cost = proc_cost + trans_cost
            return proc_cost, trans_cost, total_cost

        proc_cost = (self.LEGACY_COST[action] * self.energy_scale) * size_multiplier
        trans_cost = (self.LEGACY_OVERHEAD[action] * (size_multiplier * 0.1)) * self.energy_scale
        total_cost = proc_cost + trans_cost
        return proc_cost, trans_cost, total_cost

    def step(self, action: str) -> Tuple[Tuple[int, int, int, int, int, int], float, bool]:
        """
        Executes one environment transition step:
        1. Calculates cost and drains battery.
        2. Calculates immediate reward.
        3. Checks battery terminal condition (B <= 0).
        4. Applies terminal penalty (-500) if battery is depleted.
        5. Samples new context if not depleted.
        """
        if action not in ACTIONS:
            raise ValueError(f"Unknown action '{action}'. Valid actions: {ACTIONS}")

        _, _, total_cost = self.calculate_cost(action)
        reward = self.calculate_reward(action)

        new_battery = max(0.0, self.battery - total_cost)
        self.battery = new_battery

        done = self.battery <= 0.0
        if done:
            reward -= 500.0
        else:
            self.threat = self._sample_threat()
            self.network = self._sample_network()
            self.signal = self._sample_signal()
            self.size = self._sample_size()
            self.priority = self._sample_priority()

        return self.get_current_state(), reward, done

