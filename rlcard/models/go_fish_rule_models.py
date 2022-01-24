''' GoFish rule models
'''

import numpy as np

import rlcard
from rlcard.models.model import Model
from collections import OrderedDict

class GoFishRuleAgentV1(object):
    ''' GoFish Rule agent version 1
    '''

    def __init__(self):
        self.use_raw = True

    def step(self, state):
        '''
        Args:
            state (dict): Raw state from the game

        Returns:
            action (str): Predicted action
        '''
        legal_actions = state['raw_legal_actions']
        state = state['raw_obs']

        # If we have a card that we known another player has, take it.
        for card in state['player_hand']:
            for target_player_index in range(1, len(state['public_cards'])):
                target_player_hand = state['public_cards'][target_player_index]
                if card.rank in target_player_hand:
                    return '{}-{}'.format(target_player_index, card.rank)



        # Otherwise we randomly choose one
        action = np.random.choice(legal_actions)
        return action

    def eval_step(self, state):
        ''' Step for evaluation. The same to step
        '''
        return self.step(state), []

class GoFishRuleModelV1(Model):
    ''' GoFish Rule Model version 1
    '''

    def __init__(self):
        ''' Load pretrained model
        '''
        env = rlcard.make('go_fish')

        rule_agent = GoFishRuleAgentV1()
        self.rule_agents = [rule_agent for _ in range(env.num_players)]

    @property
    def agents(self):
        ''' Get a list of agents for each position in a the game

        Returns:
            agents (list): A list of agents

        Note: Each agent should be just like RL agent with step and eval_step
              functioning well.
        '''
        return self.rule_agents

    @property
    def use_raw(self):
        ''' Indicate whether use raw state and action

        Returns:
            use_raw (boolean): True if using raw state and action
        '''
        return True

class GoFishRuleAgentV2(object):
    ''' GoFish Rule agent version 2
    '''

    def __init__(self):
        self.use_raw = True

    def step(self, state):
        '''
        Args:
            state (dict): Raw state from the game

        Returns:
            action (str): Predicted action
        '''
        legal_actions = state['raw_legal_actions']
        state = state['raw_obs']
        other_player_indexs = range(1, len(state['public_cards']))

        # If we have a card that we known another player has and combined they make a book, take them.
        hand_by_rank = state['current_player_hand_by_rank']
        for rank, num_cards_in_hand_of_rank in hand_by_rank.items():
            for target_player_index in other_player_indexs:
                target_player_hand = state['public_cards'][target_player_index]
                if rank in target_player_hand and target_player_hand[rank] + num_cards_in_hand_of_rank == 4:
                    return '{}-{}'.format(target_player_index, rank)

        # Ask for a card its known we have the most of from a random player
        public_ranks_by_quantity = OrderedDict({ 3: [], 2: [], 1: []})
        for rank, quantity_of_rank in state['public_cards'][0].items():
            public_ranks_by_quantity[quantity_of_rank].append(rank)
        for ranks in public_ranks_by_quantity.values():
            if len(ranks) > 0:
                rank = np.random.choice(ranks)
                player_index = np.random.choice(other_player_indexs)
                return '{}-{}'.format(player_index, rank)

        # Ask for a card we have the most of from a random player
        ranks_by_quantity = OrderedDict({ 3: [], 2: [], 1: []})
        for rank, num_cards_in_hand_of_rank in hand_by_rank.items():
            ranks_by_quantity[num_cards_in_hand_of_rank].append(rank)
        for ranks in ranks_by_quantity.values():
            if len(ranks) > 0:
                rank = np.random.choice(ranks)
                player_index = np.random.choice(other_player_indexs)
                return '{}-{}'.format(player_index, rank)

        # Otherwise we randomly choose one (this shouldn't happen)
        raise 'error'
        action = np.random.choice(legal_actions)
        return action

    def eval_step(self, state):
        ''' Step for evaluation. The same to step
        '''
        return self.step(state), []

class GoFishRuleModelV2(Model):
    ''' GoFish Rule Model version 1
    '''

    def __init__(self):
        ''' Load pretrained model
        '''
        env = rlcard.make('go_fish')

        rule_agent = GoFishRuleAgentV2()
        self.rule_agents = [rule_agent for _ in range(env.num_players)]

    @property
    def agents(self):
        ''' Get a list of agents for each position in a the game

        Returns:
            agents (list): A list of agents

        Note: Each agent should be just like RL agent with step and eval_step
              functioning well.
        '''
        return self.rule_agents

    @property
    def use_raw(self):
        ''' Indicate whether use raw state and action

        Returns:
            use_raw (boolean): True if using raw state and action
        '''
        return True

class GoFishRuleAgentV3(object):
    ''' GoFish Rule agent version 3
    '''

    def __init__(self):
        self.use_raw = True

    def step(self, state):
        '''
        Args:
            state (dict): Raw state from the game

        Returns:
            action (str): Predicted action
        '''
        legal_actions = state['raw_legal_actions']
        state = state['raw_obs']
        players_rank_expected_values = state['players_rank_expected_values']
        top_actions = []
        top_actions_value = 0
        for action in legal_actions:
            target_players_to_left = int(action[0])
            target_player_rank_expected_values = players_rank_expected_values[target_players_to_left - 1]
            target_rank = action[2]
            expected_quantity = target_player_rank_expected_values[target_rank]
            if expected_quantity > top_actions_value:
                top_actions = []
                top_actions_value = expected_quantity
            if expected_quantity == top_actions_value:
                top_actions.append(action)

        action = np.random.choice(top_actions)
        return action

    def eval_step(self, state):
        ''' Step for evaluation. The same to step
        '''
        return self.step(state), []

class GoFishRuleModelV3(Model):
    ''' GoFish Rule Model version 3
    '''

    def __init__(self):
        ''' Load pretrained model
        '''
        env = rlcard.make('go_fish')

        rule_agent = GoFishRuleAgentV3()
        self.rule_agents = [rule_agent for _ in range(env.num_players)]

    @property
    def agents(self):
        ''' Get a list of agents for each position in a the game

        Returns:
            agents (list): A list of agents

        Note: Each agent should be just like RL agent with step and eval_step
              functioning well.
        '''
        return self.rule_agents

    @property
    def use_raw(self):
        ''' Indicate whether use raw state and action

        Returns:
            use_raw (boolean): True if using raw state and action
        '''
        return True



