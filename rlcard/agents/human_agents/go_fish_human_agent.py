from rlcard.utils.utils import print_card


class HumanAgent(object):
    ''' A human agent for Blackjack. It can be used to play alone for understand how the blackjack code runs
    '''

    def __init__(self, num_actions):
        ''' Initilize the human agent

        Args:
            num_actions (int): the size of the output action space
        '''
        self.use_raw = True

    @staticmethod
    def step(state):
        ''' Human agent will display the state and make decisions through interfaces

        Args:
            state (dict): A dictionary that represents the current state

        Returns:
            action (int): The action decided by human
        '''
        raw_state = state['raw_obs']
        print('\n=============   State   ===============')
        print('Number of cards in the deck: {}'.format(raw_state['deck_size']))

        num_players = len(raw_state['books'])
        for i in range(num_players):
            print('===============   Player {} Hand   ==============='.format(i))
            print('Books: {}'.format(len(raw_state['books'][i])))

            public_cards = raw_state['public_cards'][i]
            num_public_cards = 0
            print('Public cards:')
            if len(public_cards) > 0:
                for rank, cards_of_rank in public_cards.items():
                    num_cards = len(cards_of_rank)
                    print('\t{} cards of rank {}'.format(num_cards, rank))
                    num_public_cards = num_public_cards + num_cards
            else:
                print('\tNone')
            
            public_possible_cards_of_rank = raw_state['public_possible_cards_of_rank'][i]
            print('Public possible cards of rank:')
            if len(public_possible_cards_of_rank) > 0:
                for rank, cards_of_rank in public_possible_cards_of_rank.items():
                    print('\t1 of {} cards must be of rank {}'.format(len(cards_of_rank), rank))
            else:
                print('\tNone')
            
            public_not_possible_cards_of_rank = raw_state['public_not_possible_cards_of_rank'][i]
            print('Public possible cards of rank:')
            if len(public_not_possible_cards_of_rank) > 0:
                for rank, cards_of_rank in public_not_possible_cards_of_rank.items():
                    print('\t{} cards in the hand must not be of rank {}'.format(num_public_cards + len(cards_of_rank), rank))
            else:
                print('\tNone')

            if i == 0:
                print_card(raw_state['player_hand'])
            else:
                print_card([None] * raw_state['card_counts'][i])

        print('\n=========== Actions You Can Choose ===========')
        for index, action in enumerate(state['raw_legal_actions']):
            player = action[0]
            rank = action[2]
            print('{}: Ask for {}s from Player {}'.format(index, rank, player))
        print('')
        action = int(input('>> You choose action (integer): '))
        while action < 0 or action >= len(state['legal_actions']):
            print('Action illegal...')
            action = int(input('>> Re-choose action (integer): '))
        return state['raw_legal_actions'][action]

    def eval_step(self, state):
        ''' Predict the action given the current state for evaluation. The same to step here.

        Args:
            state (numpy.array): an numpy array that represents the current state

        Returns:
            action (int): the action predicted (randomly chosen) by the random agent
        '''
        return self.step(state), {}
