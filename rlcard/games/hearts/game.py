import random

from rlcard.games.hearts import Dealer
from rlcard.games.hearts import Player
from rlcard.games.base import Card
from rlcard.utils import init_standard_deck

class HeartsGame:

    def __init__(self, allow_step_back=False):
        ''' Initialize the class Hearts Game
        '''

    def configure(self, game_config):
        ''' Specifiy some game specific parameters, such as number of players
        '''
        self.num_players = game_config['game_num_players']
        self.debug = game_config['game_debug']
        self.render_steps = game_config['game_render_steps']
        self.action_list = []
        self.action_space = {}
        self._legal_actions = []
        self._legal_actions_dirty = True
        for card in init_standard_deck():
            action = card.str
            self.action_space[action] = len(self.action_list)
            self.action_list.append(action)

    def init_game(self):
        ''' Initialilze the game

        Returns:
            state (dict): the first state of the game
            player_id (int): current player's id
        '''
        self._legal_actions_dirty = True

        self.current_trick = [] # card[]
        self.current_trick_suit = None
        self.hearts_are_broken = False

        # Setup players
        self.players = []
        for i in range(self.num_players):
            player = Player(i)
            player.game_score = random.randrange(100) # TODO: Not random
            self.players.append(player)

        # Setup dealer and deal cards
        self.dealer = Dealer(self.np_random)
        counter = 0
        while len(self.dealer.deck) > 0:
            player = self.players[counter % self.num_players]
            self.dealer.deal_card(player)
            counter += 1

        # Setup passing
        self.passing_cards_players_to_left = random.randrange(self.num_players) # TODO: Not random
        self.num_passed_cards = 0
        self.passing_cards = self.passing_cards_players_to_left > 0

        # Choose a random starting player
        self.starting_player = random.randrange(self.num_players)
        self.current_player_turn = self.starting_player

        self._print('<< Player {} is starting'.format(self.starting_player))
        if self.passing_cards_players_to_left == 0:
            self._print('<< Not passing any cards; keeper round')
        else:
            self._print('<< Passing 3 cards {} players to the left'.format(self.passing_cards_players_to_left))

        return self.get_state(self.current_player_turn), self.current_player_turn

    def step(self, action):
        ''' Get the next state

        Args:
            action (str): a specific action of hearts

        Returns:/
            dict: next player's state
            int: next plater's id
        '''
        self._legal_actions_dirty = True

        player = self._get_current_player()
        card = Card(action[1], action[0])

        if self.passing_cards:
            target_player = self._get_player_num_to_left(player, self.passing_cards_players_to_left)
            self._print('>> Player {} passed {} to player {}', player.player_id, card, target_player.player_id)
            player.pass_card(card)
            self.num_passed_cards += 1
            if self.num_passed_cards % 3 == 0:
                self._advance_to_next_player()
            if self.num_passed_cards == 3 * self.num_players:
                self._print('<< Passing completed')
                self.passing_cards = False

                # Execute the passes
                for source_player in self.players:
                    target_player = self._get_player_num_to_left(source_player, self.passing_cards_players_to_left)
                    for passed_card in source_player.passed_cards:
                        target_player.receive_card(passed_card)

        else:
            if len(self.current_trick) == 0:
                self._print('>> Player {} led {}', player.player_id, card)
            else:
                self._print('>> Player {} played {}', player.player_id, card)
            self.current_trick.append(card)
            if len(self.current_trick) == 1:
                self.current_trick_suit = card.suit
            player.play_card(card, self.current_trick_suit)

            # Were hearts broken?
            if not self.hearts_are_broken and card.breaks_hearts():
                self._print('<< Hearts have been broken')
                self.hearts_are_broken = True

            # Was trick completed?
            if len(self.current_trick) == self.num_players:
                top_index = 0
                top_card = self.current_trick[0]
                for i in range(1, self.num_players):
                    card_candidate = self.current_trick[i]
                    if top_card < card_candidate and card_candidate.suit == self.current_trick_suit:
                        top_index = i
                        top_card = card_candidate
                trick_winner = self._get_player_num_to_left(player, 1 + top_index)
                trick_value = trick_winner.receive_trick(self.current_trick)
                self._print('<< Player {} won the tick worth {} points', trick_winner.player_id, trick_value)
                self.current_player_turn = trick_winner.player_id

                # Reset trick tracking
                self.current_trick = [] # card[]
                self.current_trick_suit = None

            else:
                self._advance_to_next_player()

        return self.get_state(self.current_player_turn), self.current_player_turn

    def _get_current_player(self):
        return self.players[self.current_player_turn]

    def _get_other_players(self):
        other_players = []
        for i in range(1, self.num_players):
            other_players.append(self.players[(self.current_player_turn + i) % self.num_players])
        return other_players

    def _get_player_num_to_left(self, player, players_to_left):
        return self.players[(player.player_id + players_to_left) % self.num_players]

    def _advance_to_next_player(self):
        self.current_player_turn = (self.current_player_turn + 1) % self.num_players

    def get_num_players(self):
        ''' Return the number of players in hearts

        Returns:
            number_of_player (int)
        '''
        return self.num_players

    def get_num_actions(self):
        ''' Return the number of applicable actions

        Returns:
            number_of_actions (int): number of other players * number of ranks
        '''
        return 52

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
        if not self._legal_actions_dirty:
            return self._legal_actions

        player = self.players[player_id]
        playable_cards = set()
        if self.passing_cards:
            playable_cards = player.hand
        elif self.current_trick_suit == None:
            for card in player.hand:
                if self.hearts_are_broken or not card.is_a_heart():
                    playable_cards.add(card)
            if len(playable_cards) == 0: # The player only has hearts
                playable_cards = player.hand
        elif not player.is_void_of_suit(self.current_trick_suit):
            for card in player.hand:
                if card.suit == self.current_trick_suit:
                    playable_cards.add(card)
        else:
            playable_cards = player.hand

        actions = []
        for i in range(self.num_players - 1):
            for card in playable_cards:
                actions.append(card.str)

        self._legal_actions = actions
        self._legal_actions_dirty = False
        return actions

    def get_state(self, player_id):
        ''' Return player's state

        Args:
            player_id (int): player id

        Returns:
            state (dict): corresponding player's state
                'legal_actions', string[]
                'current_player_id', int - Id of the player whose turn it is currently
                'hearts_are_broken', boolean - If hearts have currently been broken
                'passing_cards', boolean - If currently in the passing cards phase of the round
                'passing_cards_players_to_left', int - Number of players to the left to pass cards to
                'passed_cards', {Card} - Cards passed by the current player.
                'is_lead', boolean - If the player is to lead the next trick (an AI hint)
                'can_sluff', boolean - If the player can currently play a card not of the led suit (an AI hint)
                'played_cards', {Card}[] - Cards played by each player.
                'public_void_suits', {Suit -> boolean}[] - If each player is known to be void of each suit or not
                'trick', Card[] - Current trick
                'player_hand', {Card} - All of the cards in the current player's hand
                'round_scores', int[] - The current round score of each player
                'game_scores', int[] - The game score of each player (not including the current round)
        '''
        state = {}

        current_player = self._get_current_player()
        rotated_players = self.players[current_player.player_id:] + self.players[:current_player.player_id]

        played_cards = []
        public_void_suits = []
        round_scores = []
        game_scores = []
        for player in rotated_players:
            played_cards.append(player.played_cards)
            public_void_suits.append(player.public_void_suits)
            round_scores.append(player.round_score)
            game_scores.append(player.game_score)


        state['legal_actions'] = self._get_legal_actions(player_id)
        state['current_player_id'] = player_id
        state['hearts_are_broken'] = self.hearts_are_broken
        state['passing_cards'] = self.passing_cards
        state['passing_cards_players_to_left'] = self.passing_cards_players_to_left
        state['passed_cards'] = current_player.passed_cards
        state['is_lead'] = not self.passing_cards and self.current_trick_suit == None
        state['can_sluff'] = not self.passing_cards and not self.current_trick_suit == None and current_player.is_void_of_suit(self.current_trick_suit)
        state['played_cards'] = played_cards
        state['public_void_suits'] = public_void_suits
        state['trick'] = self.current_trick
        state['player_hand'] = current_player.hand
        state['round_scores'] = round_scores
        state['game_scores'] = game_scores

        return state

    def get_payoffs(self, is_training=False):
        self._print('<< Round over')
        payoffs = []
        a_player_got_control = False
        for player in self.players:
            if player.round_score == 26:
                a_player_got_control = True
                self._print('<< Player {} took control'.format(player.player_id))
            payoffs.append(player.round_score)

        for i, payoff in enumerate(list(payoffs)):
            if a_player_got_control:
                payoffs[i] = 0 if payoff == 26 else 26
            else:
                self._print('<< Player {} got {} points'.format(i, payoffs[i]))

        if is_training:
            for i, payoff in enumerate(list(payoffs)):
                payoffs[i] = 26 - payoff

        return payoffs

    def is_over(self):
        ''' Check if the game is over

        Returns:
            status (bool): True/False
        '''
        for player in self.players:
            if len(player.hand) > 0:
                return False
        return True

    def _print(self, message, *args):
        if self.debug:
            print(message.format(*args))

