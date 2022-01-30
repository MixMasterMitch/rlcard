from rlcard.games.base import Card
import itertools

class HeartsPlayer:

    def __init__(self, player_id):
        ''' Initialize a HeartsPlayer player class

        Args:
            player_id (int): id for the player
        '''
        self.player_id = player_id
        self.hand = set() # {Card} - Cards in this player's hand
        self.hand_by_suit = { 'S': 0, 'H': 0, 'D': 0, 'C': 0 } # suit -> quantity
        self.public_void_suits = { 'S': False, 'H': False, 'D': False, 'C': False } # suit -> boolean
        self.played_cards = set() # {Card} - Cards played by this player
        self.passed_cards = set() # {Card} - Cards passed by this player to another player
        self.round_score = 0
        self.game_score = 0

    def receive_card(self, card):
        self.hand.add(card)
        self.hand_by_suit[card.suit] += 1

    def pass_card(self, card):
        self._remove_card_from_hand(card)
        self.passed_cards.add(card)

    def play_card(self, card, suit_lead):
        self._remove_card_from_hand(card)
        self.played_cards.add(card)
        if not card.suit == suit_lead:
            self.public_void_suits[suit_lead] = True

    def _remove_card_from_hand(self, card):
        self.hand.remove(card)
        self.hand_by_suit[card.suit] -= 1

    def receive_trick(self, trick):
        trick_value = 0
        for card in trick:
            trick_value += card.point_value()
        self.round_score += trick_value
        return trick_value

    def is_void_of_suit(self, suit):
        return self.hand_by_suit[suit] == 0
