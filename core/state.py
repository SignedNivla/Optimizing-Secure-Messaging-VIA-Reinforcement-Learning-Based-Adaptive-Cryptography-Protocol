"""
core.state
==========
State representation, discretization, and encoding for the Adaptive Cryptography MDP.
Enforces 100% backward compatibility with legacy StateComponent behavior while eliminating
redundant class hierarchies.
"""

from typing import Tuple, Dict, Any, Union

# Standard action set matching existing Q-table keys
ACTIONS: Tuple[str, str, str] = ('AES-256', 'ChaCha20', 'ASCON')

# State cardinality definitions
THREAT_BINS = ('low', 'medium', 'high')          # 3 bins
NETWORK_BINS = ('private', 'public')             # 2 bins
BATTERY_BINS = 10                                # 10 decile bins (0-10% .. 90-100%)
SIGNAL_BINS = ('weak', 'medium', 'strong')       # 3 bins
SIZE_BINS = ('small', 'medium', 'large')         # 3 bins
PRIORITY_BINS = ('unimportant', 'medium', 'important') # 3 bins

TOTAL_STATE_SPACE = 3 * 2 * 10 * 3 * 3 * 3       # 1,620 states


def discretize_threat(value: Union[int, float]) -> Tuple[str, int]:
    """
    Threat discretization matching legacy ThreatState:
    - > 2: 'high' (index 2)
    - > 1: 'medium' (index 1)
    - else: 'low' (index 0)
    """
    if value > 2:
        return 'high', 2
    elif value > 1:
        return 'medium', 1
    return 'low', 0


def discretize_network(value: Any) -> Tuple[str, int]:
    """
    Network discretization matching legacy NetworkState:
    - 'public': 'public' (index 1)
    - else: 'private' (index 0)
    """
    val_str = str(value).strip().lower()
    if val_str == 'public':
        return 'public', 1
    return 'private', 0


def discretize_battery(value: Union[int, float]) -> Tuple[str, int]:
    """
    Battery discretization matching legacy BatteryState:
    - index: min(value // 10, 9)
    - label: '{digit*10}-{(digit+1)*10}'
    """
    digit = int(min(value // 10, 9))
    label = f"{digit * 10}-{(digit + 1) * 10}"
    return label, digit


def discretize_signal(value: Union[int, float]) -> Tuple[str, int]:
    """
    Signal discretization matching legacy SignalState:
    - == 5: 'strong' (index 2)
    - > 2: 'medium' (index 1) (includes out-of-range values like 100)
    - else: 'weak' (index 0)
    """
    if value == 5:
        return 'strong', 2
    elif value > 2:
        return 'medium', 1
    return 'weak', 0


def discretize_size(value: Union[int, float]) -> Tuple[str, int]:
    """
    Payload size discretization matching legacy SizeState:
    - >= 250: 'large' (index 2)
    - >= 50: 'medium' (index 1)
    - else: 'small' (index 0)
    """
    if value >= 250:
        return 'large', 2
    elif value >= 50:
        return 'medium', 1
    return 'small', 0


def discretize_priority(value: Union[int, float]) -> Tuple[str, int]:
    """
    Priority discretization matching legacy PriorityState:
    - > 2: 'important' (index 2)
    - > 1: 'medium' (index 1)
    - else: 'unimportant' (index 0)
    """
    if value > 2:
        return 'important', 2
    elif value > 1:
        return 'medium', 1
    return 'unimportant', 0


def encode_state(
    threat: Union[int, float],
    network: Any,
    battery: Union[int, float],
    signal: Union[int, float],
    size: Union[int, float],
    priority: Union[int, float]
) -> Tuple[int, int, int, int, int, int]:
    """
    Encodes raw environment variables into the 6-tuple state key:
    (threat_idx, network_idx, battery_idx, signal_idx, size_idx, priority_idx)
    guaranteeing exact key parity with legacy Q-tables.
    """
    _, s1 = discretize_threat(threat)
    _, s2 = discretize_network(network)
    _, s3 = discretize_battery(battery)
    _, s4 = discretize_signal(signal)
    _, s5 = discretize_size(size)
    _, s6 = discretize_priority(priority)
    return (s1, s2, s3, s4, s5, s6)


def get_state_labels(
    threat: Union[int, float],
    network: Any,
    battery: Union[int, float],
    signal: Union[int, float],
    size: Union[int, float],
    priority: Union[int, float]
) -> Dict[str, str]:
    """Returns human-readable labels for given raw values."""
    l1, _ = discretize_threat(threat)
    l2, _ = discretize_network(network)
    l3, _ = discretize_battery(battery)
    l4, _ = discretize_signal(signal)
    l5, _ = discretize_size(size)
    l6, _ = discretize_priority(priority)
    return {
        'threat': l1,
        'network': l2,
        'battery': l3,
        'signal': l4,
        'size': l5,
        'priority': l6
    }

