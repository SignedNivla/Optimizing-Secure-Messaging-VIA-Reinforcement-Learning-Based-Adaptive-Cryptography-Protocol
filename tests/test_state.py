import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import Agent.state_component as legacy_sc
import core.state as cs


class TestStateEquivalence(unittest.TestCase):
    def test_full_state_space_discretization(self):
        """Verify that core.state produces 100% identical indices across all 1,620 state permutations."""
        raw_threats = [0, 2, 3]                  # low, medium, high
        raw_networks = ['private', 'public']     # private, public
        raw_batteries = [5, 15, 25, 35, 45, 55, 65, 75, 85, 95] # 10 deciles
        raw_signals = [1, 3, 5]                  # weak, medium, strong
        raw_sizes = [20, 100, 300]               # small, medium, large
        raw_priorities = [0, 2, 3]               # unimportant, medium, important

        tested = 0
        for t in raw_threats:
            for n in raw_networks:
                for b in raw_batteries:
                    for s in raw_signals:
                        for sz in raw_sizes:
                            for p in raw_priorities:
                                tested += 1
                                legacy_tuple = (
                                    legacy_sc.ThreatState(t).get_index(),
                                    legacy_sc.NetworkState(n).get_index(),
                                    legacy_sc.BatteryState(b).get_index(),
                                    legacy_sc.SignalState(s).get_index(),
                                    legacy_sc.SizeState(sz).get_index(),
                                    legacy_sc.PriorityState(p).get_index()
                                )
                                new_tuple = cs.encode_state(t, n, b, s, sz, p)
                                self.assertEqual(legacy_tuple, new_tuple, f"Mismatch on raw input: {(t, n, b, s, sz, p)}")

        self.assertEqual(tested, 1620)

    def test_out_of_range_and_legacy_edge_cases(self):
        """Verify legacy quirks such as signal=100 mapping to index 1 ('medium')."""
        # Signal 100 (from legacy test_case['survival'])
        leg_sig = legacy_sc.SignalState(100).get_index()
        _, new_sig = cs.discretize_signal(100)
        self.assertEqual(leg_sig, 1)
        self.assertEqual(new_sig, 1)

        # Threat negative or very large
        self.assertEqual(legacy_sc.ThreatState(-10).get_index(), cs.discretize_threat(-10)[1])
        self.assertEqual(legacy_sc.ThreatState(999).get_index(), cs.discretize_threat(999)[1])

        # Battery 0, 100, >100
        self.assertEqual(legacy_sc.BatteryState(0).get_index(), cs.discretize_battery(0)[1])
        self.assertEqual(legacy_sc.BatteryState(100).get_index(), cs.discretize_battery(100)[1])
        self.assertEqual(legacy_sc.BatteryState(150).get_index(), cs.discretize_battery(150)[1])


if __name__ == '__main__':
    unittest.main()

