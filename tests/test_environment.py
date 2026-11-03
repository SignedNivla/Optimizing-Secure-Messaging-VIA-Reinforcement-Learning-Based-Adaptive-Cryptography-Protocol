import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import Agent.encryption_environment as legacy_env
import core.environment as core_env
import Agent.state_component as sc
from core.state import ACTIONS


class TestEnvironmentEquivalence(unittest.TestCase):
    def test_reward_and_cost_exact_parity(self):
        """Verify that calculate_reward and calculate_cost produce identical floats on legacy vs core."""
        test_cases = [
            # (threat, network, battery, signal, size, priority)
            (3, "public", 10.0, 5, 1, 3),    # survival
            (1, "private", 95.0, 5, 20, 1),  # efficiency
            (3, "public", 50.0, 2, 500, 3),  # heavy_load
            (2, "public", 30.0, 0, 150, 2),  # weak_signal_tax
            (1, "private", 10.0, 0, 200, 0), # lowest_need
            (3, "public", 5.0, 0, 1000, 3),  # critical
        ]

        for tc in test_cases:
            t, n, b, s, sz, p = tc

            # Legacy env
            leg = legacy_env.EncryptionEnvironment(
                threat=sc.ThreatState(t),
                network=sc.NetworkState(n),
                battery=sc.BatteryState(b),
                signal=sc.SignalState(s),
                size=sc.SizeState(sz),
                priority=sc.PriorityState(p)
            )

            # Core env
            cor = core_env.EncryptionEnvironment(
                threat=t,
                network=n,
                battery=b,
                signal=s,
                size=sz,
                priority=p
            )

            # Check state tuple equality
            self.assertEqual(leg._get_current_state(), cor.get_current_state())

            for action in ACTIONS:
                # Compare reward
                r_leg = leg._calculate_reward(action)
                r_cor = cor.calculate_reward(action)
                self.assertAlmostEqual(r_leg, r_cor, places=6, msg=f"Reward mismatch on {action} for tc {tc}")

                # Compare cost calculation
                # In legacy step:
                cost = {'AES-256': 0.25, 'ChaCha20': 0.1, 'ASCON': 0.05}
                size_map = {"small": 1, "medium": 5, "large": 15}
                overhead = {'AES-256': 2.13, 'ChaCha20': 1, 'ASCON': 1.53}
                sz_label = leg.size.get_label()
                expected_tot = (cost[action] * size_map[sz_label]) + (overhead[action] * (size_map[sz_label] * 0.1))

                _, _, cor_tot = cor.calculate_cost(action)
                self.assertAlmostEqual(expected_tot, cor_tot, places=6, msg=f"Cost mismatch on {action} for tc {tc}")

    def test_benchmark_calibrated_mode(self):
        """Verify that benchmark_calibrated mode correctly applies calibrated costs and overheads."""
        env = core_env.EncryptionEnvironment(mode='benchmark_calibrated', size=1) # size=1 -> small
        # For small payload (multiplier 1, overhead 1.500)
        # AES-256: proc = 0.11 * 1 = 0.11, trans = 1.500 * 0.1 = 0.15 -> total = 0.26
        # ChaCha20: proc = 0.10 * 1 = 0.10, trans = 1.500 * 0.1 = 0.15 -> total = 0.25
        # ASCON: proc = 0.35 * 1 = 0.35, trans = 1.500 * 0.1 = 0.15 -> total = 0.50
        p_aes, t_aes, tot_aes = env.calculate_cost('AES-256')
        self.assertAlmostEqual(tot_aes, 0.26, places=4)
        p_cha, t_cha, tot_cha = env.calculate_cost('ChaCha20')
        self.assertAlmostEqual(tot_cha, 0.25, places=4)
        p_asc, t_asc, tot_asc = env.calculate_cost('ASCON')
        self.assertAlmostEqual(tot_asc, 0.50, places=4)

    def test_smartphone_mode_and_sensitivity(self):
        """Verify smartphone mode base costs, specs, and energy_scale sensitivity."""
        env = core_env.EncryptionEnvironment(mode='smartphone', size=1, energy_scale=1.0) # size=1 -> small
        # For small payload (M=1, O=1.500)
        # AES-256: proc = 0.22 * 1 = 0.22, trans = 1.500 * 0.1 = 0.15 -> total = 0.37
        # ChaCha20: proc = 0.10 * 1 = 0.10, trans = 1.500 * 0.1 = 0.15 -> total = 0.25
        # ASCON: proc = 0.18 * 1 = 0.18, trans = 1.500 * 0.1 = 0.15 -> total = 0.33
        p_aes, t_aes, tot_aes = env.calculate_cost('AES-256')
        self.assertAlmostEqual(tot_aes, 0.37, places=4)
        p_cha, t_cha, tot_cha = env.calculate_cost('ChaCha20')
        self.assertAlmostEqual(tot_cha, 0.25, places=4)
        p_asc, t_asc, tot_asc = env.calculate_cost('ASCON')
        self.assertAlmostEqual(tot_asc, 0.33, places=4)

        # Check efficiency scores
        self.assertEqual(env.SMARTPHONE_SPECS['AES-256']['E'], 0.455)
        self.assertEqual(env.SMARTPHONE_SPECS['ChaCha20']['E'], 1.000)
        self.assertEqual(env.SMARTPHONE_SPECS['ASCON']['E'], 0.556)

        # Test -20% sensitivity scaling (energy_scale=0.8)
        env_low = core_env.EncryptionEnvironment(mode='smartphone', size=1, energy_scale=0.8)
        _, _, tot_aes_low = env_low.calculate_cost('AES-256')
        self.assertAlmostEqual(tot_aes_low, 0.37 * 0.8, places=4)

        # Test +20% sensitivity scaling (energy_scale=1.2)
        env_high = core_env.EncryptionEnvironment(mode='smartphone', size=1, energy_scale=1.2)
        _, _, tot_aes_high = env_high.calculate_cost('AES-256')
        self.assertAlmostEqual(tot_aes_high, 0.37 * 1.2, places=4)


if __name__ == '__main__':
    unittest.main()

