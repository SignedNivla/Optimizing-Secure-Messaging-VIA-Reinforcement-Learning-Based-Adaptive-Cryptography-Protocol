import sys, os, random, numpy as np
sys.path.insert(0, os.getcwd())
from core.agent import QLearningAgent
from core.environment import EncryptionEnvironment

def evaluate_agent(agent, env, episodes=100, seed=42):
    random.seed(seed)
    np.random.seed(seed)
    msgs = []
    secs = []
    rews = []
    acts = {'AES-256': 0, 'ChaCha20': 0, 'ASCON': 0}

    for _ in range(episodes):
        s = env.reset()
        done = False
        step = 0
        tot_sec = 0.0
        tot_rew = 0.0
        while not done:
            a = agent.get_action(s, training=False)
            acts[a] += 1
            tot_sec += (1.0 if a == 'AES-256' else (0.7 if a == 'ChaCha20' else 0.4))
            ns, r, done = env.step(a)
            tot_rew += r
            step += 1
            s = ns
        msgs.append(step)
        secs.append(tot_sec)
        rews.append(tot_rew)

    tot_a = sum(acts.values())
    return {
        'msgs': np.mean(msgs),
        'sec': np.mean(secs),
        'rew': np.mean(rews),
        'setor': np.mean(secs) / 100.0,
        'pct_aes': acts['AES-256'] / tot_a * 100,
        'pct_cha': acts['ChaCha20'] / tot_a * 100,
        'pct_asc': acts['ASCON'] / tot_a * 100
    }

print("Running tuning trials...")

# Let's test different gamma and alpha on legacy env
for alpha in [0.05, 0.10, 0.20]:
    for gamma in [0.99, 0.999]:
        agent = QLearningAgent(alpha=alpha, gamma=gamma, epsilon=1.0)
        env = EncryptionEnvironment(mode='simulation_legacy')
        # Train with epsilon decay
        eps = 1.0
        decay = 0.9995
        min_eps = 0.02
        for ep in range(10000):
            agent.epsilon = eps
            s = env.reset()
            done = False
            while not done:
                a = agent.get_action(s, training=True)
                ns, r, done = env.step(a)
                agent.update_q(s, a, r, ns)
                s = ns
            eps = max(min_eps, eps * decay)

        res = evaluate_agent(agent, env, episodes=100)
        print(f"Alpha={alpha:<4} Gamma={gamma:<5} | Msgs: {res['msgs']:5.1f} | Sec: {res['sec']:4.1f} | SETOR: {res['setor']:.4f} | Rew: {res['rew']:6.1f} | Dist: AES {res['pct_aes']:4.1f}% / Cha {res['pct_cha']:4.1f}% / ASC {res['pct_asc']:4.1f}%")
