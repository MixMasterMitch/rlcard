import numpy as np

import rlcard
from rlcard.models.model import Model
from rlcard.games.base import Card
from collections import OrderedDict

PASS_ORDER = [
    'AS', 'KS', 'QS', 'AH', 'KH', 'QH', 'AD', 'AC', 'JH', 'KD', 'KC', 'TH', 'QD',
    'QC', '9H', 'JD', 'JC', '8H', 'TD', 'TC', '7H', '9D', '9C', '6H', '8D', '8C',
    '7D', '7C', '6D', '6C', '5D', '5C', '4D', '4C', '3D', '3C', '2D', '2C', 'JS',
    'TS', '9S', '8S', '7S', '6S', '5S', '4S', '3S', '2S', '5H', '4H', '3H', '2H'
]

SLUFF_ORDER = [
    'QS', 'AS', 'KS', 'AH', 'KH', 'QH', 'AD', 'AC', 'JH', 'KD', 'KC', 'TH', 'QD',
    'QC', '9H', 'JD', 'JC', '8H', 'TD', 'TC', '7H', '9D', '9C', '6H', '8D', '8C',
    '7D', '7C', '6D', '6C', '5D', '5C', '4D', '4C', '3D', '3C', '2D', '2C', 'JS',
    'TS', '9S', '8S', '7S', '6S', '5S', '4S', '3S', '2S', '5H', '4H', '3H', '2H'
]

class HeartsRuleAgentV1(object):
    ''' Hearts Rule agent version 1
    '''

    def __init__(self):
        self.use_raw_action = True
        self.use_raw_state = True

    def step(self, state):
        '''
        Args:
            state (dict): Raw state from the game

        Returns:
            action (str): Predicted action
        '''
        legal_actions = state['raw_legal_actions']

        # If passing cards, then pick best card from predefined order
        if state['passing_cards']:
            return self._pick_best_action_from_order(legal_actions, PASS_ORDER)

        # If can sluff a card, then pick best card from predefined order
        if state['can_sluff']:
            return self._pick_best_action_from_order(legal_actions, SLUFF_ORDER)

        # If player has the lead, play lowest card
        if state['is_lead']:
            return self._pick_lowest_action(legal_actions)

        # If player is the last to play and there are no points in the trick, then play the highest card
        trick = state['trick']
        if len(trick) == len(state['game_scores']) - 1 and not self._trick_contains_hearts_or_the_queen(trick):
            return self._pick_highest_action(legal_actions)

        # Otherwise, play the highest card possible below the current top card or the lowest card possible if not possible to stay under the current top card
        highest_rank = self._get_highest_rank_of_lead_suit_in_trick(trick)
        highest_action_below_rank = self._pick_highest_action_below_rank(legal_actions, highest_rank)
        if highest_action_below_rank is not None:
            return highest_action_below_rank
        return self._pick_lowest_action(legal_actions)

    def eval_step(self, state):
        ''' Step for evaluation. The same to step
        '''
        return self.step(state), None

    def _pick_best_action_from_order(self, legal_actions, order):
        indexes = []
        for legal_action in legal_actions:
            indexes.append(order.index(legal_action))
        min_index = np.argmin(indexes)
        return legal_actions[min_index]

    def _trick_contains_hearts_or_the_queen(self, trick):
        for card in trick:
            if card.breaks_hearts():
                return True
        return False

    def _get_highest_rank_of_lead_suit_in_trick(self, trick):
        lead_suit = trick[0].suit
        highest_card = trick[0]
        for i in range(1, len(trick)):
            candidate = trick[i]
            if candidate.suit == lead_suit and highest_card < candidate:
                highest_card = candidate
        return highest_card.rank

    def _pick_highest_action(self, legal_actions):
        highest_action = legal_actions[0]
        highest_action_numeric = Card.valid_rank.index(highest_action[0])
        for i in range(1, len(legal_actions)):
            candidate = legal_actions[i]
            candidate_numeric = Card.valid_rank.index(candidate[0])
            if candidate_numeric > highest_action_numeric:
                highest_action = candidate
                highest_action_numeric = candidate_numeric
        return highest_action

    def _pick_lowest_action(self, legal_actions):
        lowest_action = legal_actions[0]
        lowest_action_numeric = Card.valid_rank.index(lowest_action[0])
        for i in range(1, len(legal_actions)):
            candidate = legal_actions[i]
            candidate_numeric = Card.valid_rank.index(candidate[0])
            if candidate_numeric < lowest_action_numeric:
                lowest_action = candidate
                lowest_action_numeric = candidate_numeric
        return lowest_action

    def _pick_highest_action_below_rank(self, legal_actions, rank):
        rank_numeric = Card.valid_rank.index(rank)
        highest_action = None
        highest_action_numeric = None
        for legal_action in legal_actions:
            action_numeric = Card.valid_rank.index(legal_action[0])
            if action_numeric < rank_numeric and (highest_action == None or action_numeric > highest_action_numeric):
                highest_action = legal_action
                highest_action_numeric = action_numeric
        return highest_action


class HeartsRuleModelV1(Model):
    ''' Hearts Rule Model version 1
    '''

    def __init__(self):
        ''' Load pretrained model
        '''
        rule_agent = HeartsRuleAgentV1()
        self.rule_agents = [rule_agent for _ in range(4)]

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
