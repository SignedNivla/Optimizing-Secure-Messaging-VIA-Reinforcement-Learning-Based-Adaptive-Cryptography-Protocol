import random

from Agent.state_component import NetworkState, BatteryState,PriorityState,SignalState,SizeState, ThreatState


class EncryptionEnvironment:
    def __init__(self,threat:ThreatState = None,network:NetworkState = None,battery:BatteryState = None,signal:SignalState = None,size:SizeState = None,priority:PriorityState = None):
        self.threat = ThreatState(self.generate_random_threat()) if not threat else threat
        self.network = NetworkState(self.generate_random_network()) if not network else network
        self.battery = BatteryState(100) if not battery else battery
        self.signal = SignalState(self.generate_random_signal()) if not signal else signal
        self.size = SizeState(self.generate_random_size()) if not size else size
        self.priority= PriorityState(self.generate_random_priority()) if not priority else priority

    def reset(self):
        self.threat.set_value(self.generate_random_threat())
        self.network.set_value(self.generate_random_network())
        self.battery.set_value(100)
        self.signal.set_value(self.generate_random_signal())
        self.size.set_value(self.generate_random_size())
        self.priority.set_value(self.generate_random_priority())

        return self._get_current_state()

    def generate_random_threat(self):
        return random.randint(0,3)
    
    def generate_random_network(self):
        return random.choice(['private','public'])
    
    def generate_random_signal(self):
        return random.randint(0,5)
    
    def generate_random_size(self):
        return random.randint(0,250)
    
    def generate_random_priority(self):
        return random.randint(0,3)
    
    def _get_current_state(self):
        s1 = self.threat.get_index()
        s2 = self.network.get_index()
        s3 = self.battery.get_index()
        s4 = self.signal.get_index()
        s5 = self.size.get_index()
        s6 = self.priority.get_index()

        return (s1,s2,s3,s4,s5,s6)
    
    def _calculate_reward(self,action):
        specs = {
            'AES-256':  {'S': 1.0, 'E': 0.2},
            'ChaCha20': {'S': 0.7, 'E': 0.5},
            'ASCON':    {'S': 0.4, 'E': 1.0}
        }

        reward = 0

        threat = self.threat.get_label()
        network = self.network.get_label()
        battery = self.battery.get_label()
        signal = self.signal.get_label()
        size =self.size.get_label()
        priority=self.priority.get_label()

        w_sec = 0.5
        w_eff = 0.5

        # ------------
        # First Layer
        # ------------
        if network == "public" or threat == "high":
            if battery == 'low' or signal =='low' or size == 'large' or priority == 'important':
                w_sec = 0.8
                w_eff = 0.2
            else:
                w_sec = 0.9
                w_eff = 0.1
        elif battery == "low" or signal == 'low':
            w_sec = 0.2
            w_eff = 0.8
        elif size == 'large' or priority == 'important':
            w_sec = 0.4
            w_eff = 0.6


        res = specs[action]
        reward = (w_sec * res['S']) + (w_eff * res['E'])
    
        return reward * 100
        
    def step(self,action):
        cost = {'AES-256':0.25,'ChaCha20':0.1,'ASCON':0.05}
        size_map = {"small":1,"medium":5,"large":15}
        overhead = {'AES-256':2.13,'ChaCha20':1,'ASCON':1.53}

        processing_cost = cost[action] * size_map[self.size.get_label()]
        transmission_cost = overhead[action] * (size_map[self.size.get_label()] * 0.1)

        total_cost = processing_cost * transmission_cost

        new_battery = max(0,self.battery.get_value() - total_cost)
        self.battery.set_value(new_battery)

        reward = self._calculate_reward(action)
        done = self.battery.get_value()<=0
        if done:
            reward -= 500

        if not done:
            self.threat.set_value(self.generate_random_threat())
            self.network.set_value(self.generate_random_network())
            self.signal.set_value(self.generate_random_signal())
            self.size.set_value(self.generate_random_size())
            self.priority.set_value(self.generate_random_priority())

        return self._get_current_state(),reward,done
