import pickle
import random

from Agent.encryption_environment import EncryptionEnvironment
from Agent.state_component import BatteryState, NetworkState, PriorityState, SignalState, SizeState, ThreatState

class QLearningAgent:
    def __init__(self,alpha=0.1,epsilon=0.5, gamma = 0.9):
        self.q_table = {}
        self.alpha = alpha
        self.epsilon = epsilon
        self.gamma = gamma
        self.action = ['AES-256','ChaCha20','ASCON']

    def _save_brain(self, filename="agent_brain.pkl"):
        """Saves the Q-Table to your computer."""
        with open(filename, 'wb') as f:
            pickle.dump(self.q_table, f)
        print("Brain saved successfully!")

    def _load_brain(self, filename="agent_brain.pkl"):
        """Uploads a previously saved Q-Table."""
        try:
            with open(filename, 'rb') as f:
                self.q_table = pickle.load(f)
            print("Brain loaded! I remember my training.")
            return False
        except FileNotFoundError:
            print("No saved brain found. Starting fresh.")
            return True

    def _initialize_state(self,state):
        if state not in self.q_table:
            self.q_table[state] = {action: 0.0 for action in self.action}
    
    def _choose_action(self,state,training=True):
        """Strategi Epsilon-Greedy"""
        self._initialize_state(state)
        curr_epsilon = self.epsilon if training else 0
        if random.uniform(0, 1) < curr_epsilon:
            return random.choice(self.action)
        else:
            state_scores = self.q_table[state]
            best_action = max(state_scores, key=state_scores.get)
            return best_action
        
    def _update_q_table(self,state, action, reward, next_state):
        """Tulis hasil ujian (Reward) ke dalam buku catatan menggunakan rumus matematika"""
        self._initialize_state(state)
        self._initialize_state(next_state)

        future_rewards = self.q_table[next_state].values()
        max_future = max(future_rewards)
        
        old_value = self.q_table[state][action]
        target = reward + (self.gamma * max_future)
        new_value = old_value + self.alpha * (target -old_value)
        self.q_table[state][action] = new_value

    def train(self,epsiodes = 5000):
        is_new = self._load_brain()
        history = {'reward':[],'battery_life':[]}
        env = EncryptionEnvironment()
        for i in range(epsiodes):
            total_reward = 0
            steps = 0
            current_state = env.reset()
            done = False
            while not done:
                action = self._choose_action(current_state,is_new)
                next_state,reward,done = env.step(action)

                self._update_q_table(current_state,action,reward,next_state)

                current_state = next_state
                total_reward += reward
                steps += 1
            history['reward'].append(total_reward)
            history['battery_life'].append(steps)
            
            if i % 100 == 0:
                print(f"Threat: {env.threat.get_label()}, Battery: {env.battery.get_label()}, Size: {env.size.get_label()} -> Action: {action}")
                print(f"Episode {i}: Avg Reward: {sum(history['reward'][-100:])/100}, Battery Life: {history['battery_life'][-1]}")
        self._save_brain()
        return history
    
    def test(self, threat:ThreatState = None,network:NetworkState = None,battery:BatteryState = None,signal:SignalState = None,size:SizeState = None,priority:PriorityState = None):
        is_not_exist = self._load_brain()
        if is_not_exist: 
            print("Error: No brain found. Train the agent first.")
            return
        env = EncryptionEnvironment(threat,network,battery,signal,size,priority)
        action = self._choose_action(env,False)
        print("--- Agent Decision Report ---")
        print(f"Context: {env.threat.get_label()} threat on a {env.network.get_label()} network.")
        print(f"Device Status: Battery at {env.battery.get_label()}%, Signal is {env.signal.get_label()}.")
        print(f"Data Info: {env.size.get_label()} payload with {env.priority.get_label()} priority.")
        print(f"RESULT >> Agent selected: **{action}**")