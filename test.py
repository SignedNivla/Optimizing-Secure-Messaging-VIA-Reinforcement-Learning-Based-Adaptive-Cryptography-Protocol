import Agent.state_component as sc
from Agent.agent import QLearningAgent as agent

def transform_test_case(threat,network,battery,signal,size,priority):
    return [sc.ThreatState(threat),sc.NetworkState(network),sc.BatteryState(battery),sc.SignalState(signal),sc.SizeState(size),sc.PriorityState(priority)]

test_case = {
    "survival" : (3,"public",10,100,1,3),
    "efficiency": (1, "private", 95, 5, 20, 1), 
    "heavy_load": (3, "public", 50, 2, 500, 3), 
    "weak_signal_tax": (2, "public", 30, 0, 150, 2),
    "lowest_need":(1,'private',10,0,200,0),
    'critical': (3, "public", 5, 0, 1000, 3)
}

agent_names = ["initial_model.pkl","agent_brain2.pkl","agent_brain3.pkl","agent_brain4.pkl","final_model.pkl"]

for agent_name in agent_names:
    print(f"==========={agent_name}============")
    for test in test_case.keys():
        ag = agent(filename=agent_name)
        print(f'Test for {test}')
        params = transform_test_case(*test_case[test])
        ag.test(*params)