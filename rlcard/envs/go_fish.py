import numpy as np
from collections import OrderedDict

from rlcard.envs import Env
from rlcard.games.go_fish import Game
from rlcard.games.base import Card

DEFAULT_GAME_CONFIG = {
    'game_num_players': 2,
    'game_debug': False,
    'game_stats_tracker': None,
    'game_is_training_mode': False,
}

class GoFishEnv(Env):

    def __init__(self, config):
        self.name = 'go_fish'
        self.default_game_config = DEFAULT_GAME_CONFIG
        self.game = Game()
        super().__init__(config)
        # 1 * num_players = card counts of all players
        # 1 * num_players = scored books of all players
        # 13 * (num_players - 1) = expected quantities for a request of every rank for each other player
        # 1 = remaining cards in deck
        # 13 = quantity of each rank in current player hand
        # 13 = public quantities of every rank in current player hand
        # 13 = percentage of non public cards that can't be of each rank
        self.state_shape_num_elements = 1 + 3 * 13 + 2 * self.num_players + 13 * (self.num_players - 1)
        self.state_shape = [[self.state_shape_num_elements] for _ in range(self.num_players)]
        self.action_shape = [None for _ in range(self.num_players)]

    def _extract_state(self, state):
        obs_list = []
        player_id = self.game.current_player_turn
        obs_list.extend(state['card_counts'])
        obs_list.extend(state['books'])
        expected_values = [self.rank_quantity_dict_to_list(player_expected_values) for player_expected_values in state['players_rank_expected_values']]
        obs_list.extend([x for y in expected_values for x in y])
        obs_list.append(state['deck_size'])
        player_hand = self.rank_quantity_dict_to_list(state['player_hand_by_rank'])
        obs_list.extend(player_hand)
        player_public_hand = self.rank_quantity_dict_to_list(state['public_cards'][0])
        obs_list.extend(player_public_hand)

        public_not_revealed_count = state['card_counts'][0] - sum(player_public_hand) + len(state['public_possible_cards_of_rank'][0])
        player_public_not_possible_percentage = []
        not_possible = state['public_not_possible_cards_of_rank'][0]
        for rank in Card.valid_rank:
            if rank not in state['remaining_ranks'] or public_not_revealed_count == 0:
                percentage = 1
            elif rank not in not_possible:
                percentage = 0
            else:
                percentage = not_possible[rank] / public_not_revealed_count
            player_public_not_possible_percentage.append(percentage)
        obs_list.extend(player_public_not_possible_percentage)

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
