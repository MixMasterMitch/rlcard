''' An example of training a reinforcement learning agent on the environments in RLCard
'''
import os
import argparse

import torch
import numpy as np
from datetime import datetime

import rlcard
from rlcard import models
from rlcard.agents import RandomAgent
from rlcard.utils import get_device, set_seed, tournament_random_opponents, reorganize, Logger, plot_curve

def train(args):

    # Check whether gpu is available
    device = get_device()

    # Seed numpy, torch, random
    set_seed(args.seed)

    # Make the environment with seed
    env = rlcard.make(args.env, config={'seed': args.seed, 'game_num_players': args.num_players})

    # Initialize the agent and use random agents as opponents
    if args.algorithm == 'dqn':
        from rlcard.agents import DQNAgent
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
    elif args.algorithm == 'nfsp':
        from rlcard.agents import NFSPAgent
        agent = NFSPAgent(num_actions=env.num_actions,
                          state_shape=env.state_shape[0],
                          hidden_layers_sizes=[64,64],
                          q_mlp_layers=[64,64],
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
    with Logger(args.log_dir) as logger:
        for episode in range(args.num_episodes + 1):
            agents = [agent]
            for i in range(args.num_players - 1):
                agents.append(np.random.choice(opponent_agents))
            env.set_agents(agents)

            if args.algorithm == 'nfsp':
                agents[0].sample_episode_policy()

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
            if episode % args.evaluate_every == 0:
                reward = tournament_random_opponents(env, args.num_eval_games, agent, opponent_agents)[0]
                logger.log_performance(env.timestep, reward)
                plot_curve(logger.csv_path, logger.fig_path, args.algorithm)

                percentage_complete = episode / args.num_episodes
                if percentage_complete > 0:
                    elapsed_time = datetime.now() - start_time
                    total_time_seconds = elapsed_time.total_seconds() / percentage_complete
                    remaining_minutes = (total_time_seconds - elapsed_time.total_seconds()) / 60
                    print('{:.0%} complete ({:.0f} mins remaining)'.format(percentage_complete, remaining_minutes))

                if reward > best_reward:
                    best_reward = reward

                    # Save model
                    print('Saving model')
                    save_path = os.path.join(args.log_dir, 'model.pth')
                    torch.save(agent, save_path)

    print('Model saved in', save_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser("DQN/NFSP example in RLCard")
    parser.add_argument('--env', type=str, default='leduc-holdem',
            choices=['blackjack', 'leduc-holdem', 'limit-holdem', 'doudizhu', 'mahjong', 'no-limit-holdem', 'uno', 'gin-rummy', 'go_fish', 'hearts'])
    parser.add_argument('--algorithm', type=str, default='dqn', choices=['dqn', 'nfsp'])
    parser.add_argument('--cuda', type=str, default='')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--num_episodes', type=int, default=100000)
    parser.add_argument('--num_eval_games', type=int, default=5000)
    parser.add_argument('--evaluate_every', type=int, default=2000)
    parser.add_argument('--log_dir', type=str, default='experiments/leduc_holdem_dqn_result/')
    parser.add_argument('--num_players', type=int, default=4)

    args = parser.parse_args()

    os.environ["CUDA_VISIBLE_DEVICES"] = args.cuda
    train(args)

