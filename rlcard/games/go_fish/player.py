from rlcard.games.go_fish.utils import cards_by_rank
from rlcard.games.base import Card
import itertools

class GoFishPlayer:

    def __init__(self, player_id, np_random, debug):
        ''' Initialize a GoFish player class

        Args:
            player_id (int): id for the player
        '''
        self.np_random = np_random
        self.player_id = player_id
        self.hand = [] # card[]
        self.public_cards = {} # rank -> card[]
        self.public_possible_cards_of_rank = {} # rank -> card[]
        self.public_not_possible_cards_of_rank = {} # rank -> card[]
        self.books = [] # rank[]
        self.remaining_ranks = list(Card.valid_rank) # rank[]
        self.debug = debug

    def get_player_id(self):
        ''' Return player's id
        '''
        return self.player_id

    def receive_cards(self, cards, public):
        ''' Return ranks of any completed books
        '''
        for card in cards:
            print('Adding {} to hand of player {}'.format(card, self.player_id))
            self.hand.append(card)
            if public:
                self.reveal_card(card)

        # Extract books from hand
        completed_books = []
        hand_by_rank = cards_by_rank(self.hand)
        for rank, cards_of_rank in hand_by_rank.items():
            if (len(cards_of_rank) == 4):
                if self.debug:
                    print('<< Player {} completed a book of {}s'.format(self.player_id, rank))
                print('Adding {} to books of player {}'.format(rank, self.player_id))
                self.books.append(rank)
                completed_books.append(rank)
                self.mark_book_completed(rank)

        # Sort cards
        self.hand = sorted(self.hand, key=lambda card: '{}{}'.format(card.rank, card.suit))

        return completed_books

    def remove_cards_of_rank(self, rank):
        ''' Return cards of the given rank removed from the player's hand
        '''
        removed_cards = self._clean_up_rank(rank)

        # Mark all remaining cards as not being of the requested rank
        if rank in self.public_not_possible_cards_of_rank:
            print('Removing {} public not possible cards of rank {} for player {}'.format(len(self.public_not_possible_cards_of_rank[rank]), rank, self.player_id))
        non_public_cards_in_hand = self._get_non_public_cards_in_hand()
        print('Marking {} as not of rank {} for player {}'.format(non_public_cards_in_hand, rank, self.player_id))
        self.public_not_possible_cards_of_rank[rank] = non_public_cards_in_hand
        for card in non_public_cards_in_hand:
            if card.rank == rank:
                raise Exception('Attempted to mark a card as not being of its rank')

        self._reveal_cards_by_process_of_elimination()

        return removed_cards

    def mark_rank_as_requested(self, rank):
        ''' Specifically, this player has requested the given rank of another player.
        '''
        # If the rank has already been requested, then re-requesting has no effect
        if rank in self.public_possible_cards_of_rank or rank in self.public_cards:
            return

        # Otherwise, all cards that are not public should be marked as being of the given rank
        # But exclude cards that are already known to not be of the given rank
        non_public_cards_in_hand = self._get_non_public_cards_in_hand()
        if rank in self.public_not_possible_cards_of_rank:
            for not_possible_card in self.public_not_possible_cards_of_rank[rank]:
                non_public_cards_in_hand.remove(not_possible_card)
        print('Marking {} as containing at least one card of rank {} for player {}'.format(non_public_cards_in_hand, rank, self.player_id))
        self.public_possible_cards_of_rank[rank] = non_public_cards_in_hand

        self._reveal_cards_by_process_of_elimination()

    def _get_non_public_cards_in_hand(self):
        non_public_cards_in_hand = list(self.hand)
        for public_cards_of_rank in self.public_cards.values():
            for card in public_cards_of_rank:
                non_public_cards_in_hand.remove(card)
        return non_public_cards_in_hand

    def reveal_card(self, card):
        self._reveal_card(card)
        self._reveal_cards_by_process_of_elimination()

    def _reveal_card(self, card):
        rank = card.rank

        # Add card to public cards
        print('Adding {} to public cards of rank {} for player {}'.format(card, rank, self.player_id))
        public_cards_of_rank = self.public_cards.get(rank, [])
        public_cards_of_rank.append(card)
        self.public_cards[rank] = public_cards_of_rank

        # If the card was in a set of possible cards for the rank, remove the set
        if rank in self.public_possible_cards_of_rank:
            if card in self.public_possible_cards_of_rank[rank]:
                print('Removing {} public possible cards of rank {} for player {}'.format(len(self.public_possible_cards_of_rank[rank]), rank, self.player_id))
                del self.public_possible_cards_of_rank[rank]

        # Clean up the card from the public possible and public not possible data
        self._clean_up_card(card)

    def mark_book_completed(self, book):
        self.remaining_ranks.remove(book)
        self._clean_up_rank(book)
        self._reveal_cards_by_process_of_elimination()

    def _clean_up_rank(self, rank):
        ''' Remove all record of the given rank from this player.
            Returns any removed cards. (There should not be any returned cards if this function is called bacuse another player completed a book)
        '''
        removed_cards = []

        if rank in self.public_cards:
            print('Removing {} public cards of rank {} for player {}'.format(len(self.public_cards[rank]), rank, self.player_id))
            del self.public_cards[rank]
        if rank in self.public_possible_cards_of_rank:
            print('Removing {} public possible cards of rank {} for player {}'.format(len(self.public_possible_cards_of_rank[rank]), rank, self.player_id))
            del self.public_possible_cards_of_rank[rank]
        if rank in self.public_not_possible_cards_of_rank:
            print('Removing {} public not possible cards of rank {} for player {}'.format(len(self.public_not_possible_cards_of_rank[rank]), rank, self.player_id))
            del self.public_not_possible_cards_of_rank[rank]
        for card in list(self.hand):
            if card.rank == rank:
                print('Removing {} from the hand of player {}'.format(card, self.player_id))
                self.hand.remove(card)
                removed_cards.append(card)

        # Remove other records of the removed cards
        for removed_card in removed_cards:
            self._clean_up_card(removed_card)

        return removed_cards

    def _reveal_cards_by_process_of_elimination(self):
        while True:
            cards_to_reveal = []

            # Look if there are any cards that can only be one possible rank based on what it can't be
            for card in self._get_non_public_cards_in_hand():
                possible_ranks = list(self.remaining_ranks)
                for rank, not_possible_cards in self.public_not_possible_cards_of_rank.items():
                    if card in not_possible_cards:
                        possible_ranks.remove(rank)
                if len(possible_ranks) == 1:
                    cards_to_reveal.append(card)

            # Look for matching possible card sets (e.g. if there are 2 possible card sets each with only the same two cards, those cards can be revealed)
            card_sets_by_length = {} # length -> cards[][]
            for rank, card_set in self.public_possible_cards_of_rank.items():
                length = len(card_set)
                card_sets_of_length = card_sets_by_length.get(length, [])
                card_sets_of_length.append(set(card_set))
                card_sets_by_length[length] = card_sets_of_length
            for length, card_sets in card_sets_by_length.items():
                if len(card_sets) < length:
                    continue
                combinations = itertools.combinations(card_sets, length)
                for combination in combinations:
                    matching_combination = True
                    for i in range(1, len(combination)):
                        if combination[i] != combination[0]:
                            print('did not match')
                            print(combination[0])
                            print(combination[i])
                            matching_combination = False
                            break
                    if matching_combination:
                        print('Discovered {} matching card sets. Revealing {} for player {}'.format(length, combination[0], self.player_id))
                        cards_to_reveal.extend(combination[0])

            # It is possible that the same card is marked to be revealed multiple times. So make sure the card still needs to be revealed
            for card_to_reveal in cards_to_reveal:
                rank = card_to_reveal.rank
                if rank not in self.public_cards or card_to_reveal not in self.public_cards[rank]:
                    print('By process of elimination, revealing {} for player {}'.format(card_to_reveal, self.player_id))
                    self._reveal_card(card_to_reveal)

            # Keep iterating until there are no more cards to reveal
            if len(cards_to_reveal) == 0:
                break


    def _clean_up_card(self, card):
        ''' Removes the card from any possible and not possible sets of cards.
            It is possible that this leaves one or more single remaining card in possible rank sets. The remaining card will be revealed.
        '''
        additional_cards_to_reveal = []
        for rank, possible_cards in dict(self.public_possible_cards_of_rank).items():
            if card in possible_cards:
                print('Removing {} from public possible cards of rank {} for player {}'.format(card, rank, self.player_id))
                self.public_possible_cards_of_rank[rank].remove(card)
            if len(possible_cards) == 1:
                print('Removing {} from public possible cards of rank {} for player {} and marking it to be revealed'.format(possible_cards[0], rank, self.player_id))
                del self.public_possible_cards_of_rank[rank]
                additional_cards_to_reveal.append(possible_cards[0])
        for rank, not_possible_cards in dict(self.public_not_possible_cards_of_rank).items():
            if card in not_possible_cards:
                print('Removing {} from public not possible cards of rank {} for player {}'.format(card, rank, self.player_id))
                self.public_not_possible_cards_of_rank[rank].remove(card)
            if len(not_possible_cards) == 0:
                print('Clearning empty public not possible cards of rank {} for player {}'.format(rank, self.player_id))
                del self.public_not_possible_cards_of_rank[rank]
        # Additional cards to reveal should not be revealed until the end to avoid nested manipulating of the public and non public sets while iterating through them.
        for additional_card_to_reveal in additional_cards_to_reveal:
            # It is possible that the same card is marked to be revealed multiple times. So make sure the card still needs to be revealed
            rank = additional_card_to_reveal.rank
            if rank not in self.public_cards or additional_card_to_reveal not in self.public_cards[rank]:
                self.reveal_card(additional_card_to_reveal)


