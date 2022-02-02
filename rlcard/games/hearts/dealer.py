from rlcard.utils import init_standard_deck
import numpy as np

class HeartsDealer:

    def __init__(self, np_random):
        ''' Initialize a Hearts dealer class
        '''
        self.np_random = np_random

    def shuffle(self):
        ''' Shuffle the deck
        '''
        self.deck = init_standard_deck()
        shuffle_deck = np.array(self.deck)
        self.np_random.shuffle(shuffle_deck)
        self.deck = list(shuffle_deck)

    def deal_card(self, player):
        ''' Distribute one card to the player

        Args:
            player_id (int): the target player's id
        '''
        card = self.deck.pop()
        completed_books = player.receive_card(card)
