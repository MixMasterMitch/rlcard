''' An example of training a reinforcement learning agent on the environments in RLCard
'''
import os
import argparse

import torch
import numpy as np
from datetime import datetime

import rlcard
from rlcard import models
from rlcard.agents import RandomAgent, DQNAgent
from rlcard.utils import get_device, set_seed, tournament_random_opponents, reorganize, Logger, plot_curve

NUM_PLAYERS = 4
NUM_EPISODES = 10_000
NUM_EVAL_GAMES = 1_000
EVAL_EVERY = 1_000
LOGS_DIR = 'experiments/hearts_v1_4_player_model_6'

def train():

    # Check whether gpu is available
    device = get_device()

    # Seed numpy, torch, random
    seed = 42
    set_seed(seed)

    # Make the environment with seed
    env = rlcard.make('hearts', config={'seed': seed, 'game_num_players': NUM_PLAYERS})

    # Initialize the training agent
    agent = DQNAgent(num_actions=env.num_actions,
                     state_shape=env.state_shape[0],
                     mlp_layers=[1024],
                     discount_factor=0.999,
                     # update_target_estimator_every=2000,
                     # replay_memory_init_size=500,
                     batch_size=64,
                     epsilon_decay_steps=500000,
                     # epsilon_end=0.05,
                     learning_rate=0.000005,
                     device=device)

    opponent_agents = []

    # Random agent
    opponent_agents.append(RandomAgent(num_actions=env.num_actions))

    # # Prior trained agent
    # trained_agent = torch.load('experiments/v2_4_player_model_1/model.pth', map_location=device)
    # trained_agent.set_device(device)
    # opponent_agents.append(trained_agent)

    # Rule models
    # rule_agent_v1 = models.load('go-fish-v1').agents[0]
    # opponent_agents.append(rule_agent_v1)
    # rule_agent_v3 = models.load('go-fish-v3').agents[0]
    # opponent_agents.append(rule_agent_v3)

    # Start training
    start_time = datetime.now()
    best_reward = 0
    with Logger(LOGS_DIR) as logger:
        for episode in range(NUM_EPISODES + 1):
            agents = [agent]
            for i in range(NUM_PLAYERS - 1):
                agents.append(np.random.choice(opponent_agents))
            env.set_agents(agents)

            # Generate data from the environment
            trajectories, payoffs = env.run(is_training=True)

            # Reorganaize the data to be state, action, reward, next_state, done
            trajectories = reorganize(trajectories, payoffs)

            # Feed transitions into agent memory, and train the agent
            # Here, we assume that DQN always plays the first position
            # and the other players play randomly (if any)
            for ts in trajectories[0]:
                agent.feed(ts)

            # Evaluate the performance. Play with random agents.
            if episode % EVAL_EVERY == 0:
                reward = tournament_random_opponents(env, NUM_EVAL_GAMES, agent, opponent_agents)[0]
                logger.log_performance(env.timestep, reward)
                plot_curve(logger.csv_path, logger.fig_path)

                percentage_complete = episode / NUM_EPISODES
                if percentage_complete > 0:
                    elapsed_time = datetime.now() - start_time
                    total_time_seconds = elapsed_time.total_seconds() / percentage_complete
                    remaining_minutes = (total_time_seconds - elapsed_time.total_seconds()) / 60
                    print('{:.0%} complete ({:.0f} mins remaining)'.format(percentage_complete, remaining_minutes))

                if reward > best_reward:
                    best_reward = reward

                    # Save model
                    print('Saving model')
                    save_path = os.path.join(LOGS_DIR, 'model.pth')
                    torch.save(agent, save_path)

    print('Model saved in', save_path)

if __name__ == '__main__':
    train()

