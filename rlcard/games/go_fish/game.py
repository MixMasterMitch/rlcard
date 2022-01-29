import numpy as np

from rlcard.games.go_fish import Dealer
from rlcard.games.go_fish import Player
from rlcard.games.base import Card
from rlcard.utils import StatsTracker

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
        self.stats_tracker = game_config['game_stats_tracker']
        self.action_list = []
        self.action_space = {}
        self._legal_actions = []
        self._legal_actions_dirty = True
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
        self._legal_actions_dirty = True

        # Setup players
        self.players = []
        for i in range(self.num_players):
            self.players.append(Player(i, self.np_random, self.debug))

        # Setup dealer and deal cards
        self.dealer = Dealer(self.np_random)
        hand_size = 5 if self.num_players >= 4 else 7
        for i in range(hand_size):
            for player in self.players:
                self.current_player_turn = player.player_id
                _, completed_books = self.dealer.deal_card(player)
                self._report_completed_books_to_other_players(completed_books)

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
        self._legal_actions_dirty = True

        player = self._get_current_player()
        target_players_to_left = int(action[0])
        target_player = self.players[(self.current_player_turn + target_players_to_left) % self.num_players]
        target_rank = action[2]
        self._print('>> Player {} requested {}s from player {}', player.player_id, target_rank, target_player.player_id)
        next_players_turn = True

        player.mark_rank_as_requested(target_rank)
        netted_cards = target_player.remove_cards_of_rank(target_rank)
        completed_books = player.receive_cards(netted_cards, True)
        self._report_completed_books_to_other_players(completed_books)

        # got what the player was looking for
        if len(netted_cards) > 0:
            self._print('<< Got {} cards', len(netted_cards))
            next_players_turn = False

        # go fish (if there are cards left)
        else:
            self._print('<< GO FISH!')

            if len(self.dealer.deck) > 0:
                fished_card, completed_books = self.dealer.deal_card(player)

                # fished the card they requested
                # player must reveal the card but it remains their turn
                if fished_card.rank == target_rank:
                    self._print('<< But drew what was asked!')
                    next_players_turn = False
                    if fished_card in player.hand: # It is possible that the fished card created a completed book and is implicitly revealed
                        player.reveal_card(fished_card)

                # If a book was completed using the drawn card, cleanup the rank data for the other players
                self._report_completed_books_to_other_players(completed_books)
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

        if self.stats_tracker:
            expected_quantity = self._players_rank_expected_values[target_players_to_left - 1][target_rank]
            final_quantity = 4 if target_rank in player.books else len(set(filter(lambda c: c.rank == target_rank, player.hand)))
            self._print('Expected {} {}s and ended with {}', expected_quantity, target_rank, final_quantity)
            self.stats_tracker.update(final_quantity - expected_quantity)

        if next_players_turn:
            for candidate_next_player in self._get_other_players():
                self._print('-- Next player turn')
                if len(candidate_next_player.hand) == 0:
                    self._print('>> Player {} has no cards', candidate_next_player.player_id)
                else:
                    self.current_player_turn = candidate_next_player.player_id
                    break

        return self.get_state(self.current_player_turn), self.current_player_turn

    def _report_completed_books_to_other_players(self, completed_books):
        for book in completed_books:
            for other_player in self._get_other_players():
                other_player.mark_book_completed(book)

    def _get_current_player(self):
        return self.players[self.current_player_turn]

    def _get_other_players(self):
        other_players = []
        for i in range(1, self.num_players):
            other_players.append(self.players[(self.current_player_turn + i) % self.num_players])
        return other_players


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
        if not self._legal_actions_dirty:
            return self._legal_actions

        player_hand = self.players[player_id].hand
        player_hand_ranks = set()
        for card in player_hand:
            player_hand_ranks.add(card.rank)
        actions = []
        for i in range(self.num_players - 1):
            for player_hand_rank in player_hand_ranks:
                actions.append('{}-{}'.format(i + 1, player_hand_rank))
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
                'card_counts', int[] - The number of cards in each player's hand
                'public_cards', {rank -> quantity}[] - The publicly known quantity of cards of each rank in each player's hand
                'public_possible_cards_of_rank', {rank -> quantity}[] - The publicly known quantity of cards for each rank in each player's hand where there must be at least one card of the rank. This known card is counted in public_cards too.
                'public_not_possible_cards_of_rank', {rank -> quantity}[] - The publicly known quantity of cards that must not be of each rank in each player's hand
                'players_rank_expected_values', {rank -> expected_quantity}[] - The expected number of cards to end up with by guessing each rank of each player
                'books', int[] - The number of completed books for each player
                'remaining_ranks' = rank[] - The ranks that have not be converted to completed books yet.
                'player_hand', {Card} - All of the cards in the current player's hand
                'player_hand_by_rank', {rank -> quantity} - The quantity of each rank in the current player's hand
                'deck_size'
        '''
        state = {}

        current_player = self._get_current_player()
        other_players = self._get_other_players()
        rotated_players = self.players[current_player.player_id:] + self.players[:current_player.player_id]

        card_counts = [] # int[]
        public_cards = [] # {rank -> quantity}[]
        public_possible_cards_of_rank = [] # {rank -> quantity}[]
        public_not_possible_cards_of_rank = [] # {rank -> quantity}[]
        books = [] # int[]
        for player in rotated_players:

            # Card counts
            card_counts.append(len(player.hand))

            # Public cards
            player_public_cards = {}
            for rank, cards in player.public_cards.items():
                player_public_cards[rank] = len(cards)
            for rank in player.public_possible_cards_of_rank.keys():
                player_public_cards[rank] = player_public_cards.get(rank, 0) + 1
            public_cards.append(player_public_cards)

            # Public possible cards
            player_public_possible_cards_of_rank = {}
            for rank, cards in player.public_possible_cards_of_rank.items():
                player_public_possible_cards_of_rank[rank] = len(cards)
            public_possible_cards_of_rank.append(player_public_possible_cards_of_rank)

            # Public not possible cards
            player_public_not_possible_cards_of_rank = {}
            for rank, cards in player.public_not_possible_cards_of_rank.items():
                player_public_not_possible_cards_of_rank[rank] = len(cards)
            public_not_possible_cards_of_rank.append(player_public_not_possible_cards_of_rank)

            # Books
            books.append(len(player.books))

        # Unkown cards
        # Determine the number of cards of each rank that are in an unknown location (e.g. still in the deck)
        unknown_cards = {} # rank -> quantity
        for remaining_rank in current_player.remaining_ranks:
            reamining_cards = 4
            if remaining_rank in current_player.hand_by_rank:
                reamining_cards = reamining_cards - current_player.hand_by_rank[remaining_rank]
            for i, other_player in enumerate(other_players):
                other_player_public_cards = public_cards[i + 1]
                if remaining_rank in other_player_public_cards:
                    reamining_cards = reamining_cards - other_player_public_cards[remaining_rank]
            if reamining_cards > 0:
                unknown_cards[remaining_rank] = reamining_cards
        total_unknown_cards = sum(unknown_cards.values())

        # Card not possible ranks
        # For each card in the other players' hands, determine the set of ranks the card can't be.
        card_not_possible_ranks = {} # card -> {rank}
        for other_player in other_players:
            for rank, card_set in other_player.public_not_possible_cards_of_rank.items():
                for card in card_set:
                    not_possible_ranks = card_not_possible_ranks.get(card, set())
                    not_possible_ranks.add(rank)
                    card_not_possible_ranks[card] = not_possible_ranks


        # Determine the weight on probabilities associated with each card. If a card is known to be one of n cards that are of a particular rank,
        # then the probability of the card being of a different rank is reduced. The probability is increased for each rank the card can't be.
        card_weights = {} # card -> weight
        for other_player in other_players:
            for card in other_player.hand:
                card_possible_ranks = unknown_cards.keys() - card_not_possible_ranks.get(card, set())
                card_not_possible_quantity = sum(map(lambda r: unknown_cards[r], card_possible_ranks))
                card_weights[card] = 1 if card_not_possible_quantity == 0 else total_unknown_cards / card_not_possible_quantity
            for card_set in other_player.public_possible_cards_of_rank.values():
                weight_factor = 1 - 1 / len(card_set)
                for card in card_set:
                    card_weights[card] = card_weights[card] * weight_factor

        # Player rank points
        # For each other player, determine the cards that can be of each rank. Then sum the weights of those cards for each rank to determine the rank points
        players_rank_points = [] # {rank -> points}[]
        for other_player in other_players:
            player_non_public_cards = other_player.non_public_cards_in_hand
            player_rank_points = {} # {rank -> points}
            for remaining_rank in unknown_cards.keys():
                candidate_cards = player_non_public_cards - other_player.public_not_possible_cards_of_rank.get(remaining_rank, set())
                points = 0
                for candidate_card in candidate_cards:
                    points = points + card_weights[candidate_card]
                if points > 0:
                    player_rank_points[remaining_rank] = points
            players_rank_points.append(player_rank_points)

        # Total rank points
        # Determine the total number of points in the game (i.e. in the deck and with the other players) for each rank
        deck_size = len(self.dealer.deck)
        total_rank_points = {} # {rank -> points}
        for remaining_rank in unknown_cards.keys():
            points = deck_size
            for player_rank_points in players_rank_points:
                points = points + player_rank_points.get(remaining_rank, 0)
            total_rank_points[remaining_rank] = points

        # Deck top card rank expected_values
        deck_top_card_expected_value = {} # {rank -> expected_value}
        for rank, total_points in total_rank_points.items():
            deck_top_card_expected_value[rank] = unknown_cards[rank] / total_points

        # Player rank expected values
        players_rank_expected_values = [] # {rank -> expected_value}[]
        for i, other_player in enumerate(other_players):
            player_rank_expected_values = {} # {rank -> expected_value}
            for rank in current_player.hand_by_rank.keys():
                # TODO handle special case where all cards are known, but from different players. Expected value should just be 4
                expected_value_from_players_known_cards = public_cards[i + 1].get(rank, 0)
                expected_value_from_players_unknown_cards = players_rank_points[i].get(rank, 0) * unknown_cards.get(rank, 0) / total_rank_points.get(rank, 1) # If total_rank_points is 0, then player_rank_points will also be 0. But we don't want a divide by 0, so we default total to 1.
                expected_value_from_drawing_from_deck = 0 if expected_value_from_players_known_cards > 0 else deck_top_card_expected_value.get(rank, 0) # TODO: I think this value should decrease based on the probability that one of the unknown cards is the desired rank.
                expected_value_from_current_players_hand = current_player.hand_by_rank.get(rank, 0)
                player_rank_expected_values[rank] = expected_value_from_players_known_cards + expected_value_from_players_unknown_cards + expected_value_from_drawing_from_deck + expected_value_from_current_players_hand
            players_rank_expected_values.append(player_rank_expected_values)

        if self.stats_tracker:
            self._players_rank_expected_values = players_rank_expected_values

        state['legal_actions'] = self._get_legal_actions(player_id)
        state['current_player_id'] = player_id
        state['card_counts'] = card_counts
        state['public_cards'] = public_cards
        state['public_possible_cards_of_rank'] = public_possible_cards_of_rank
        state['public_not_possible_cards_of_rank'] = public_not_possible_cards_of_rank
        state['players_rank_expected_values'] = players_rank_expected_values
        state['books'] = books
        state['remaining_ranks'] = current_player.remaining_ranks
        state['player_hand'] = current_player.hand
        state['player_hand_by_rank'] = current_player.hand_by_rank
        state['deck_size'] = deck_size

        return state

    def get_payoffs(self, is_training=False):
        if is_training:
            payoffs = []
            for player in self.players:
                # payoff = len(player.books) - 6.5
                # squared_payoff = payoff * payoff
                # payoffs.append(-squared_payoff if payoff < 0 else squared_payoff)
                payoffs.append(len(player.books) - 13 / self.num_players)
            return payoffs

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
        winner_payoff = 100 if players_with_top_score == 1 else 50
        for player in self.players:
            payoffs.append(winner_payoff if len(player.books) == top_score else 0)
        return payoffs


    def is_over(self):
        ''' Check if the game is over

        Returns:
            status (bool): True/False
        '''
        return len(self.players[0].remaining_ranks) == 0

    def _print(self, message, *args):
        if self.debug:
            print(message.format(*args))

