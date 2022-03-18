''' An example of training a reinforcement learning agent on the environments in RLCard
'''
import os
import argparse

import torch
import numpy as np
from pathlib import Path
from datetime import datetime

import rlcard
from rlcard import models
from rlcard.agents import RandomAgent, HeartsDQNAgent
from rlcard.utils import get_device, set_seed, tournament_random_opponents, reorganize, Logger, plot_curve, MetricLogger

TEST = 20

NUM_PLAYERS = 4
NUM_EPISODES = 150000
NUM_EVAL_GAMES = 1000
EVAL_EVERY = 5000
LOGS_DIR = Path('experiments/hearts_v2_4_player_model_{}'.format(TEST))
LOGS_DIR.mkdir(parents=True)

def train():

    # Check whether gpu is available
    device = get_device()

    # Seed numpy, torch, random
    # MAC 1-9 are 51-59 (double check)
    # MAC 10-19 are 70-79
    # MAC 20+ are 120+
    # PC 1-9 are 41-49 (double check)
    # PC 10 is 60
    # PC 11+ are 211+
    seed = 100 + TEST
    set_seed(seed)

    # Make the environment with seed
    env = rlcard.make('hearts', config={'seed': seed, 'game_num_players': NUM_PLAYERS, 'game_debug': False, 'game_is_round_mode': True })
    eval_env = rlcard.make('hearts', config={'seed': seed, 'game_num_players': NUM_PLAYERS, 'game_debug': False, 'game_is_round_mode': False })

    # Initialize the training agent
    agent = HeartsDQNAgent(env, device=device, test=TEST)

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
    logger = MetricLogger(LOGS_DIR)
    with Logger(LOGS_DIR) as episode_logger:
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
                q, loss, epsilon = agent.feed(ts)
                reward = ts[2]
                logger.log_step(reward, loss, q, epsilon)
            logger.log_episode()

            if episode % 50  == 0:
                logger.record(episode, step=env.timestep)

            # Evaluate the performance. Play with random agents.
            if episode % EVAL_EVERY == 0:
                reward = tournament_random_opponents(eval_env, NUM_EVAL_GAMES, agent, opponent_agents)[0]
                episode_logger.log_performance(env.timestep, reward)
                plot_curve(episode_logger.csv_path, episode_logger.fig_path)

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

