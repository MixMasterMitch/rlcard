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
        # 1 * num_players = which player leading this round
        # 1 * num_players = which player cards were passed to
        # 1 * num_players = game scores of all players
        # 52 = cards passed by the current player
        # 52 = player's hand
        self.passing_state_shape = [104 + 3 * self.num_players]
        # 1 * num_players = which player cards were passed to
        # 1 * num_players = current round scores of all players
        # 1 * num_players = game scores of all players
        # 4 * num_players = publicly void suits of all players
        # 52 = current trick
        # 52 = cards passed by the current player
        # 52 = player's hand
        # 52 * num_players = played cards by all players
        self.playing_state_shape = [156 + 59 * self.num_players]
        self.action_shape = [52]

    def _extract_state(self, state):
        if state['passing_cards']:
            obs = np.zeros((self.passing_state_shape[0]), dtype=int)
            index = 0
            index = self._apply_player_position_to_obs(obs, index, state['starting_players_to_left'])
            index = self._apply_player_position_to_obs(obs, index, state['passing_cards_players_to_left'])
            for game_score in state['game_scores']:
                obs[index] = game_score / 100 # Normalized
                index += 1
            index = self._apply_cards_to_obs(obs, index, state['passed_cards'])
            index = self._apply_cards_to_obs(obs, index, state['player_hand'])
        else:
            obs = np.zeros((self.playing_state_shape[0]), dtype=int)
            index = 0
            index = self._apply_player_position_to_obs(obs, index, state['passing_cards_players_to_left'])
            for round_score in state['round_scores']:
                obs[index] = round_score / 26 # Normalized
                index += 1
            for game_score in state['game_scores']:
                obs[index] = game_score / 100 # Normalized
                index += 1
            for public_void_suits in state['public_void_suits']:
                for suit in SUITS:
                    if public_void_suits[suit]:
                        obs[index] = 1
                    index += 1
            index = self._apply_cards_to_obs(obs, index, state['trick'])
            index = self._apply_cards_to_obs(obs, index, state['passed_cards'])
            index = self._apply_cards_to_obs(obs, index, state['player_hand'])
            for played_cards in state['played_cards']:
                index = self._apply_cards_to_obs(obs, index, played_cards)

        return {
            'obs': obs,
            'legal_actions_mask': self._get_legal_actions_mask(state['raw_legal_actions']),
            'raw_obs': state,
            'raw_legal_actions': state['raw_legal_actions'],
            'action_record': self.action_recorder
        }

    def _apply_cards_to_obs(self, obs, offset, cards):
        ''' Marks the given cards as present in a 52 value block in obs starting at the given offset '''
        for card in cards:
            obs[offset + card.get_numeric_index()] = 1
        return offset + 52

    def _apply_player_position_to_obs(self, obs, offset, position):
        ''' Marks the given player position with a 1 in a block in obs the same size as the number of players starting at the given offset '''
        obs[offset + position] = 1
        return offset + self.num_players

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
        return self.game.action_list[action_id]

    def _get_legal_actions_mask(self, raw_legal_actions):
        mask = -np.inf * np.ones(self.action_shape[0], dtype=float)
        for action in raw_legal_actions:
            mask[self.game.action_space[action]] = 0
        return mask

    @staticmethod
    def rank_quantity_dict_to_list(rank_dict):
        rank_list = []
        for rank in Card.valid_rank:
            rank_list.append(rank_dict.get(rank, 0))
        return rank_list
