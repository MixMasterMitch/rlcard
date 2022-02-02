import time
import os
import numpy as np
from collections import OrderedDict

from rlcard.envs import Env
from rlcard.games.hearts import Game
from rlcard.games.base import Card
from rlcard.utils.utils import print_card

DEFAULT_GAME_CONFIG = {
    'game_num_players': 2,
    'game_debug': False,
    'game_render_steps': False,
    'game_is_round_mode': False,
}

SUITS = ['S', 'H', 'D', 'C']

class HeartsEnv(Env):

    def __init__(self, config):
        self.name = 'hearts'
        self.default_game_config = DEFAULT_GAME_CONFIG
        self.game = Game()
        super().__init__(config)
        # 1 = hearts are broken
        # 1 = passing cards mode
        # 1 = number of players to the left to pass to
        # 1 = player is to lead next trick
        # 1 = player can sluff
        # 1 * num_players = current round scores of all players
        # 1 * num_players = game scores of all players
        # 4 * num_players = publicly void suits of all players
        # 52 = cards passed by the current player
        # 52 = current trick
        # 52 = player's hand
        # 52 * num_cards = played cards by all players
        self.state_shape_num_elements = 161 + 58 * self.num_players
        self.state_shape = [[self.state_shape_num_elements] for _ in range(self.num_players)]
        self.action_shape = [None for _ in range(self.num_players)]

    def _extract_state(self, state):
        obs = np.zeros((self.state_shape_num_elements), dtype=int)
        obs[0] = state['hearts_are_broken']
        obs[1] = state['passing_cards']
        obs[2] = state['passing_cards_players_to_left']
        obs[3] = state['is_lead']
        obs[4] = state['can_sluff']
        index = 5
        for round_score in state['round_scores']:
            obs[index] = round_score
            index += 1
        for game_score in state['game_scores']:
            obs[index] = game_score
            index += 1
        for public_void_suits in state['public_void_suits']:
            for suit in SUITS:
                if public_void_suits[suit]:
                    obs[index] = 1
                index += 1
        index = self._apply_cards_to_obs(obs, index, state['passed_cards'])
        index = self._apply_cards_to_obs(obs, index, state['trick'])
        index = self._apply_cards_to_obs(obs, index, state['player_hand'])
        for played_cards in state['played_cards']:
            index = self._apply_cards_to_obs(obs, index, played_cards)

        return {
            'obs': obs,
            'legal_actions': self._get_legal_actions(),
            'raw_obs': state,
            'raw_legal_actions': [a for a in state['legal_actions']],
            'action_record': self.action_recorder
        }

    def _apply_cards_to_obs(self, obs, offset, cards):
        for card in cards:
            obs[offset + card.get_numeric_index()] = 1
        return offset + 52

    def step(self, action, raw_action=False):
        state, player_id = Env.step(self, action, raw_action)
        if self.game.render_steps and self.num_players == 4:
            os.system('clear')
            raw_obs = state['raw_obs']
            trick = raw_obs['trick']
            trick_starting_player = (player_id - len(trick)) % self.num_players
            print(trick_starting_player)
            print_card(raw_obs['trick'])

            if player_id > 0 and not state['raw_obs']['passing_cards']:
                time.sleep(1)
        return state, player_id

    def _print_empty_lines(num_lines):
        for _ in range(num_lines):
            print('')

    def get_payoffs(self, is_training):
        return np.array(self.game.get_payoffs(is_training))

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
