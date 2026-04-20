from Agent.agent import QLearningAgent

agent = QLearningAgent(filename='initial_model.pkl')

agent2 = QLearningAgent(0.7,0.001,filename='agent_brain2.pkl')

agent3 = QLearningAgent(0.2,0.8,0.8,filename='agent_brain3.pkl')

agent4 = QLearningAgent(0.12,0.8,0.99,filename='agent_brain4.pkl')

agent5 = QLearningAgent(0.14,0.56,0.99,filename='final_model.pkl')

agent5.train()