import numpy as np
from collections import OrderedDict

from rlcard.envs import Env
from rlcard.games.go_fish import Game
from rlcard.games.go_fish.utils import cards_by_rank
from rlcard.games.base import Card

DEFAULT_GAME_CONFIG = {
    'game_num_players': 2,
    'game_debug': False,
    'game_stats_tracker': None
}

class GoFishEnv(Env):

    def __init__(self, config):
        self.name = 'go_fish'
        self.default_game_config = DEFAULT_GAME_CONFIG
        self.game = Game()
        super().__init__(config)
        # 1 * num_players = card counts of all players
        # 1 * num_players = scored books of all players
        # 13 * num_players = public quantities of every card for each player
        # 1 = remaining cards in deck
        # 13 = current player hand
        self.state_shape_num_elements = 14 + 15 * self.num_players
        self.state_shape = [[self.state_shape_num_elements] for _ in range(self.num_players)]
        self.action_shape = [None for _ in range(self.num_players)]

    def _extract_state(self, state):
        obs_list = []
        player_id = self.game.current_player_turn
        obs_list.extend(state['card_counts'])
        obs_list.extend(state['books'])
        known_hands = [self.rank_quantity_dict_to_list(known_hand) for known_hand in state['public_cards']]
        obs_list.extend([x for y in known_hands for x in y])
        obs_list.append(state['deck_size'])
        player_hand = self.rank_quantity_dict_to_list(state['current_player_hand_by_rank'])
        obs_list.extend(player_hand)
        obs = np.zeros((self.state_shape_num_elements), dtype=int)
        obs[0:] = obs_list

        legal_action_ids = self._get_legal_actions()
        extracted_state = {'obs': obs, 'legal_actions': legal_action_ids}
        extracted_state['raw_obs'] = state
        extracted_state['raw_legal_actions'] = [a for a in state['legal_actions']]
        extracted_state['action_record'] = self.action_recorder
        return extracted_state

    def get_payoffs(self):
        return np.array(self.game.get_payoffs())

    def _decode_action(self, action_id):
        legal_ids = self._get_legal_actions()
        return self.game.action_list[action_id]

    def _get_legal_actions(self):
        legal_actions = self.game.get_legal_actions()
        legal_ids = {self.game.action_space[action]: None for action in legal_actions}
        return OrderedDict(legal_ids)

    @staticmethod
    def rank_quantity_dict_to_list(rank_dict):
        rank_list = []
        for rank in Card.valid_rank:
            rank_list.append(rank_dict.get(rank, 0))
        return rank_list

