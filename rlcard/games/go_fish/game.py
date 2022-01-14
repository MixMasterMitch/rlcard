import numpy as np

from rlcard.games.go_fish import Dealer
from rlcard.games.go_fish import Player
from rlcard.games.base import Card

class GoFishGame:

    def __init__(self, allow_step_back=False):
        ''' Initialize the class GoFish Game
        '''
        self.np_random = np.random.RandomState()

    def configure(self, game_config):
        ''' Specifiy some game specific parameters, such as number of players
        '''
        self.num_players = game_config['game_num_players']
        self.debug = game_config['game_debug']
        self.action_list = []
        self.action_space = {}
        for player_num in range(self.num_players - 1):
            for rank in Card.valid_rank:
                action = '{}-{}'.format(player_num + 1, rank)
                self.action_space[action] = len(self.action_list)
                self.action_list.append(action)

    def init_game(self):
        ''' Initialilze the game

        Returns:
            state (dict): the first state of the game
            player_id (int): current player's id
        '''
        # Setup players
        self.players = []
        for i in range(self.num_players):
            self.players.append(Player(i, self.np_random, self.debug))

        # Setup dealer and deal cards
        self.dealer = Dealer(self.np_random)
        hand_size = 5 if self.num_players >= 4 else 7
        for i in range(hand_size):
            for j in range(self.num_players):
                self.dealer.deal_card(self.players[j])

        # Choose a random starting player
        self.current_player_turn = self.np_random.randint(self.num_players)

        return self.get_state(self.current_player_turn), self.current_player_turn

    def step(self, action):
        ''' Get the next state

        Args:
            action (str): a specific action of go fish. (Card to guess from a player)

        Returns:/
            dict: next player's state
            int: next plater's id
        '''
        player = self.players[self.current_player_turn]
        target_players_to_left = int(action[0])
        target_player = self.players[(self.current_player_turn + target_players_to_left) % self.num_players]
        target_rank = action[2]
        self._print('>> Player {} requested {}s from player {}'.format(player.player_id, target_rank, target_player.player_id))
        next_players_turn = True

        if target_rank not in player.known_hand:
            player.known_hand[target_rank] = 1

        netted_cards = target_player.remove_cards_of_rank(target_rank)

        # got what the player was looking for
        if len(netted_cards) > 0:
            self._print('<< Got {} cards'.format(len(netted_cards)))
            next_players_turn = False
            player.receive_cards(netted_cards, True)

        # go fish (if there are cards left)
        else:
            self._print('<< GO FISH!')

            if len(self.dealer.deck) > 0:
                fished_card = self.dealer.deal_card(player)

                # fished the card they requested
                # player must reveal the card but it remains their turn
                if fished_card.rank == target_rank:
                    self._print('<< But drew what was asked!')
                    next_players_turn = False
                    if target_rank in player.known_hand: # if the target rank is not in the known hand then a book was just made
                        player.known_hand[target_rank] = player.known_hand[target_rank] + 1
            else:
                self._print('<< Could not draw a card because there are none left')

        # if the player is supposed to play again but does not have any cards they are supposed to draw
        if not next_players_turn and len(player.hand) == 0:
            if len(self.dealer.deck) > 0:
                self._print('<< Drew a card because your hand was empty')
                self.dealer.deal_card(player)
            # if there are no cards left to draw then the players turn is over
            else:
                self._print('<< Could not draw a card because there are none left')
                next_players_turn = True

        if next_players_turn:
            for i in range(self.num_players - 1):
                self._print('-- Next player turn')
                candidate_next_player_id = (self.current_player_turn + 1 + i) % self.num_players
                if len(self.players[candidate_next_player_id].hand) == 0:
                    self._print('>> Player {} has no cards'.format(candidate_next_player_id))
                else:
                    self.current_player_turn = candidate_next_player_id
                    break

        return self.get_state(self.current_player_turn), self.current_player_turn

    def get_num_players(self):
        ''' Return the number of players in go fish

        Returns:
            number_of_player (int)
        '''
        return self.num_players

    def get_num_actions(self):
        ''' Return the number of applicable actions

        Returns:
            number_of_actions (int): number of other players * number of ranks
        '''
        return (self.num_players - 1) * 13

    def get_player_id(self):
        ''' Return the current player's id

        Returns:
            player_id (int): current player's id
        '''
        return self.current_player_turn

    def get_legal_actions(self):
        return self._get_legal_actions(self.current_player_turn)

    def _get_legal_actions(self, player_id):
        ''' Return the legal actions for current player

        Returns:
            (list): A list of legal actions
        '''
        player_hand = self.players[player_id].hand
        player_hand_ranks = set()
        for card in player_hand:
            player_hand_ranks.add(card.rank)
        actions = []
        for i in range(self.num_players - 1):
            for player_hand_rank in player_hand_ranks:
                actions.append('{}-{}'.format(i + 1, player_hand_rank))
        return actions

    def get_state(self, player_id):
        ''' Return player's state

        Args:
            player_id (int): player id

        Returns:
            state (dict): corresponding player's state
                'legal_actions',
                'card_counts',
                'known_hands',
                'books',
                'player_hand',
                'deck_size'
        '''
        state = {}
        card_counts = []
        known_hands = []
        books = []
        for player in self.players:
            card_counts.append(len(player.hand))
            known_hands.append(player.known_hand)
            books.append(player.books)

        state['legal_actions'] = self._get_legal_actions(player_id)
        state['card_counts'] = card_counts
        state['known_hands'] = known_hands
        state['books'] = books
        state['player_hand'] = self.players[player_id].hand
        state['deck_size'] = len(self.dealer.deck)

        return state

    def get_payoffs(self):
        # payoffs = []
        # for player in self.players:
        #     payoffs.append(len(player.books) - 6.5)

        # return payoffs

        top_score = 0
        players_with_top_score = 0
        for player in self.players:
            player_score = len(player.books)
            if player_score > top_score:
                top_score = player_score
                players_with_top_score = 1
            elif player_score == top_score:
                players_with_top_score = players_with_top_score + 1
        payoffs = []
        winner_payoff = 1 if players_with_top_score == 1 else 0
        for player in self.players:
            payoffs.append(winner_payoff if len(player.books) == top_score else -1)

        return payoffs


    def is_over(self):
        ''' Check if the game is over

        Returns:
            status (bool): True/False
        '''
        for i in range(self.num_players):
            if len(self.players[i].hand) > 0:
                return False

        return True

    def _print(self, message):
        if self.debug:
            print(message)