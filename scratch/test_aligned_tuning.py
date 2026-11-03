import sys, os, random, numpy as np
sys.path.insert(0, os.getcwd())
from core.agent import QLearningAgent
from core.environment import EncryptionEnvironment

class AlignedEnv(EncryptionEnvironment):
    """
    Environment where reward efficiency reflects physical transmission reality:
    ChaCha20 has lowest transmission cost -> E=0.90 (or 1.0)
    Ascon has higher transmission overhead -> E=0.80
    AES has highest cost -> E=0.20
    """
    def calculate_reward(self, action: str) -> float:
        specs = {
            'AES-256':  {'S': 1.0, 'E': 0.20},
            'ChaCha20': {'S': 0.7, 'E': 0.90},  # physically most efficient in transmission
            'ASCON':    {'S': 0.4, 'E': 0.80}   # slightly higher transmission cost
        }
        # Everything else identical to legacy
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
        return 100.0 * (w_sec * s_score + w_eff * e_score)

agent = QLearningAgent(alpha=0.14, gamma=0.99, epsilon=1.0)
env = AlignedEnv(mode='simulation_legacy')

eps = 1.0
decay = 0.9995
for ep in range(10000):
    agent.epsilon = eps
    s = env.reset()
    done = False
    while not done:
        a = agent.get_action(s, training=True)
        ns, r, done = env.step(a)
        agent.update_q(s, a, r, ns)
        s = ns
    eps = max(0.02, eps * decay)

# Evaluate on standard legacy environment to see how it performs physically!
from core.environment import EncryptionEnvironment as StandardEnv
eval_env = StandardEnv(mode='simulation_legacy')
random.seed(42)
np.random.seed(42)

msgs = []
secs = []
acts = {'AES-256': 0, 'ChaCha20': 0, 'ASCON': 0}
for _ in range(500):
    s = eval_env.reset()
    done = False
    st = 0
    t_sec = 0.0
    while not done:
        a = agent.get_action(s, training=False)
        acts[a] += 1
        t_sec += (1.0 if a == 'AES-256' else (0.7 if a == 'ChaCha20' else 0.4))
        ns, r, done = eval_env.step(a)
        st += 1
        s = ns
    msgs.append(st)
    secs.append(t_sec)

tot = sum(acts.values())
print(f"ALIGNED REWARD AGENT EVALUATION (500 ep):")
print(f"Messages: {np.mean(msgs):.1f} +- {np.std(msgs):.1f} (vs Static ChaCha: 118.3)")
print(f"Security: {np.mean(secs):.1f} +- {np.std(secs):.1f} (vs Static ChaCha: 82.8)")
print(f"SETOR   : {np.mean(secs)/100.0:.4f} (vs Static ChaCha: 0.8281)")
print(f"Actions : AES={acts['AES-256']/tot:.1%}, ChaCha={acts['ChaCha20']/tot:.1%}, ASCON={acts['ASCON']/tot:.1%}")

