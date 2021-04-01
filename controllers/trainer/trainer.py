#!/usr/bin/env python3.8
from controller import Robot
from environment import Environment
from agent_dqn import DQN_Agent
from agent_sac import SAC_Agent
from agent_ppo import PPO_Agent

# Create an environment
env = Environment()
#agent = DQN_Agent()
agent = PPO_Agent(input_dims=[18], action_range=[2], n_actions=6, batch_size=256)


timestep = env.TIME_STEP

total_rewards = 0
total_reward = 0
record = 0
counter = 0
actions = [0.1, 0, 0, 0, 0.1, 0.1]

# Helper functions
plot_rewards = []
plot_mean_rewards = []
n_episode_step = 0
N = 256
learn_iters = 0

while env.supervisor.step(timestep) != -1:
    # Observe the environment to get the state
    state = agent.observe(env)
    
    # Decide on a action
    action, prob, val = agent.choose_action(state)
    
    # Execute the action
    reward, done = env.play_step(action)
    
    # Observe the new environment
    #new_state = agent.observe(env)
    
    # remember
    agent.remember(state, action, prob, val, reward, done)
    if n_episode_step % N == 0:
        agent.learn()
        learn_iters += 1
    # train short memory (for single step)
    #agent.learn(state, action, reward, new_state, done)
    #agent.learn()

    # Keep track of the total rewards
    total_reward += reward
    print("Episode {} \t Step {} \t Reward {}".format(agent.n_games, n_episode_step, reward))

    # Increase episode's step number
    n_episode_step += 1
    
    
    
    if done:
        env.reset()
        agent.n_games += 1
        n_episode_step = 0
        #agent.train_long_memory()
        
        total_rewards += total_reward
        
        if total_reward > record:
            record = total_reward
            #agent.model.save()
            agent.save_models()
            
        plot_rewards.append(total_reward)
        mean_reward = total_reward / agent.n_games
        plot_mean_rewards.append(mean_reward)
        
        total_reward = 0
        print('Episode', agent.n_games, ' Done! \t Score: ', total_reward, 'Record: ', record)   
