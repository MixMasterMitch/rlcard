from rlcard.games.go_fish.utils import cards_by_rank

class GoFishPlayer:

    def __init__(self, player_id, np_random, debug):
        ''' Initialize a GoFish player class

        Args:
            player_id (int): id for the player
        '''
        self.np_random = np_random
        self.player_id = player_id
        self.hand = []
        self.known_hand = {} # rank -> count
        self.known_not_hand = {} # card -> rank[]
        self.books = []
        self.debug = debug

    def get_player_id(self):
        ''' Return player's id
        '''
        return self.player_id

    def receive_cards(self, cards, public):
        for card in cards:
            self.hand.append(card)
            self.known_not_hand[card] = []
            if public:
                self.known_hand[card.rank] = self.known_hand.get(card.rank, 0) + 1

        # Extract books from hand
        hand_by_rank = cards_by_rank(self.hand)
        for cards_of_rank in hand_by_rank.values():
            if (len(cards_of_rank) == 4):
                rank = cards_of_rank[0].rank
                if self.debug:
                    print('<< Player {} completed a book of {}s'.format(self.player_id, rank))
                self.books.append(rank)
                if rank in self.known_hand:
                    del self.known_hand[rank]
                for card in cards_of_rank:
                    self.hand.remove(card)

        # Sort cards
        self.hand = sorted(self.hand, key=lambda card: '{}{}'.format(card.rank, card.suit))


    def remove_cards_of_rank(self, rank):
        ''' Return cards of the given rank removed from the player's hand
        '''
        removed_cards = []

        for card in list(self.hand):
            if card.rank == rank:
                self.hand.remove(card)
                del self.known_not_hand[card]
                removed_cards.append(card)
            else:
                self.known_not_hand[rank].append(card)
        if rank in self.known_hand:
            del self.known_hand[rank]

        return removed_cards