''' Game-related base classes
'''
class Card:
    '''
    Card stores the suit and rank of a single card

    Note:
        The suit variable in a standard card game should be one of [S, H, D, C, BJ, RJ] meaning [Spades, Hearts, Diamonds, Clubs, Black Joker, Red Joker]
        Similarly the rank variable should be one of [A, 2, 3, 4, 5, 6, 7, 8, 9, T, J, Q, K]
    '''
    suit = None
    rank = None
    valid_suit = ['S', 'H', 'D', 'C', 'BJ', 'RJ']
    valid_rank = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']

    def __init__(self, suit, rank):
        ''' Initialize the suit and rank of a card

        Args:
            suit: string, suit of the card, should be one of valid_suit
            rank: string, rank of the card, should be one of valid_rank
        '''
        self.suit = suit
        self.rank = rank
        self._hash = Card.valid_rank.index(self.rank) + 100 * Card.valid_suit.index(self.suit)

    def __lt__(self, other):
        self_rank_index = Card.valid_rank.index(self.rank)
        other_rank_index = Card.valid_rank.index(other.rank)
        if self_rank_index == other_rank_index:
            return Card.valid_suit.index(self.suit) < Card.valid_suit.index(other.suit)
        return self_rank_index < other_rank_index

    def __eq__(self, other):
        if isinstance(other, Card):
            return self.rank == other.rank and self.suit == other.suit
        else:
            # don't attempt to compare against unrelated types
            return NotImplemented

    def __hash__(self):
        return self._hash

    def __str__(self):
        ''' Get string representation of a card.

        Returns:
            string: the combination of rank and suit of a card. Eg: AS, 5H, JD, 3C, ...
        '''
        return self.rank + self.suit

    __repr__ = __str__

    def get_index(self):
        ''' Get index of a card.

        Returns:
            string: the combination of suit and rank of a card. Eg: 1S, 2H, AD, BJ, RJ...
        '''
        return self.suit+self.rank

    def is_a_heart(self):
        return self.suit == 'H'

    def is_the_queen(self):
        return self.suit == 'S' and self.rank == 'Q'

    def breaks_hearts(self):
        return self.is_a_heart() or self.is_the_queen()

    def point_value(self):
        if self.is_the_queen():
            return 13
        if self.is_a_heart():
            return 1
        return 0
