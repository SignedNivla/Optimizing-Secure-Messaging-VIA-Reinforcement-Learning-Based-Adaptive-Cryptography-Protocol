import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.agent import QLearningAgent
import core.state as cs


class TestAgent(unittest.TestCase):
    def test_keyword_arguments_enforcement(self):
        """Constructor MUST enforce keyword arguments for alpha, gamma, epsilon."""
        # Valid keyword construction
        ag = QLearningAgent(alpha=0.14, gamma=0.56, epsilon=0.99)
        self.assertEqual(ag.alpha, 0.14)
        self.assertEqual(ag.gamma, 0.56)
        self.assertEqual(ag.epsilon, 0.99)

        # Positional arguments must raise TypeError
        with self.assertRaises(TypeError):
            QLearningAgent(0.14, 0.56, 0.99)

    def test_load_legacy_model(self):
        """Must load final_model.pkl and match the exact Q-values and greedy decisions."""
        pkl_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'final_model.pkl'))
        ag = QLearningAgent(filename=pkl_path)
        self.assertTrue(len(ag.q_table) > 1600)

        # Test Lowest Need state (0, 0, 1, 0, 1, 0)
        st = (0, 0, 1, 0, 1, 0)
        self.assertIn(st, ag.q_table)
        q_vals = ag.get_state_q_values(st)
        self.assertIn('ChaCha20', q_vals)
        self.assertIn('ASCON', q_vals)
        self.assertIn('AES-256', q_vals)

        # ChaCha20 has highest Q-value
        best = ag.get_action(st, training=False)
        self.assertEqual(best, 'ChaCha20')

    def test_bellman_update(self):
        """Verify standard Watkins Bellman equation update."""
        ag = QLearningAgent(alpha=0.5, gamma=0.8, epsilon=0.0)
        s1 = (0, 0, 0, 0, 0, 0)
        s2 = (0, 0, 1, 0, 0, 0)
        
        # Init s2 with some max future value
        ag._init_state(s2)
        ag.q_table[s2]['AES-256'] = 100.0
        
        # Update s1 with reward = 10.0
        # target = 10.0 + 0.8 * 100.0 = 90.0
        # new_val = 0.0 + 0.5 * (90.0 - 0.0) = 45.0
        ag.update_q(s1, 'ChaCha20', 10.0, s2)
        self.assertAlmostEqual(ag.q_table[s1]['ChaCha20'], 45.0)


if __name__ == '__main__':
    unittest.main()

