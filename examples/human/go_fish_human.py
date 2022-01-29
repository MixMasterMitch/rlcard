''' A toy example of self playing for go_fish
'''

import torch
import rlcard
from rlcard.agents import RandomAgent as RandomAgent
from rlcard.agents import GoFishHumanAgent as HumanAgent
from rlcard.utils.utils import print_card, get_device

# Make environment
num_players = 4
env = rlcard.make('go_fish', config={'game_num_players': num_players, 'game_debug': True})
human_agent = HumanAgent(env.num_actions)
device = get_device()
# ai_agent = torch.load('experiments/leduc_holdem_dqn_result_19/model.pth', map_location=device)
# ai_agent.set_device(device)
random_agent_1 = RandomAgent(env.num_actions)
env.set_agents([human_agent, random_agent_1, RandomAgent(env.num_actions), RandomAgent(env.num_actions)])

print(">> Gofish human agent")

while (True):
    print(">> Start a new game")

    trajectories, payoffs = env.run(is_training=False)

    print('===============     Result     ===============')
    for i in range(num_players):
        if payoffs[i] == 100:
            print('Player {} wins!'.format(i))
        elif payoffs[i] == 50:
            print('Player {} tied!'.format(i))
        else:
            print('Player {} lost!'.format(i))
        print('')

    input("Press any key to continue...")
