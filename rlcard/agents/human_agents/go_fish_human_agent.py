from rlcard.utils.utils import print_card
from rlcard.games.base import Card


class HumanAgent(object):
    ''' A human agent for Go Fish.
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
            It is always assumed that the human player is player 0

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
            print('Books: {}'.format(raw_state['books'][i]))

            public_cards = raw_state['public_cards'][i]
            num_public_cards = 0
            print('Public cards:')
            if len(public_cards) > 0:
                for rank, num_cards in public_cards.items():
                    print('\t{} cards of rank {}'.format(num_cards, rank))
                    num_public_cards = num_public_cards + num_cards
            else:
                print('\tNone')
            
            public_possible_cards_of_rank = raw_state['public_possible_cards_of_rank'][i]
            print('Public possible cards of rank:')
            if len(public_possible_cards_of_rank) > 0:
                for rank, num_cards in public_possible_cards_of_rank.items():
                    print('\t1 of {} cards must be of rank {}'.format(num_cards, rank))
                    num_public_cards = num_public_cards - 1
            else:
                print('\tNone')
            
            public_not_possible_cards_of_rank = raw_state['public_not_possible_cards_of_rank'][i]
            print('Public possible cards of rank:')
            if len(public_not_possible_cards_of_rank) > 0:
                for rank, num_cards in public_not_possible_cards_of_rank.items():
                    print('\t{} cards in the hand must not be of rank {}'.format(num_public_cards + num_cards, rank))
            else:
                print('\tNone')

            if i == 0:
                print_card(raw_state['player_hand'])
            else:
                print_card([None] * raw_state['card_counts'][i])

        print('\n=========== Actions You Can Choose ===========')
        actions_by_number = {}
        current_action_number = 0
        for player_id in range(num_players):
            for rank in Card.valid_rank:
                action = '{}-{}'.format(player_id, rank)
                if action in state['raw_legal_actions']:
                    expected_quantity = raw_state['players_rank_expected_values'][player_id - 1][rank]
                    print('{}: Ask for {}s from Player {} [{:.2f}]'.format(current_action_number, rank, player_id, expected_quantity))
                    actions_by_number[current_action_number] = action
                    current_action_number = current_action_number + 1
        print('')
        input_action_string = input('>> You choose action (integer): ')
        action_number = int(input_action_string) if input_action_string.isnumeric() else -1
        while action_number < 0 or action_number >= len(state['legal_actions']):
            print('Action illegal...')
            input_action_string = input('>> Re-choose action (integer): ')
            action_number = int(input_action_string) if input_action_string.isnumeric() else -1
        return actions_by_number[action_number]

    def eval_step(self, state):
        ''' Predict the action given the current state for evaluation. The same to step here.

        Args:
            state (numpy.array): an numpy array that represents the current state

        Returns:
            action (int): the action predicted (randomly chosen) by the random agent
        '''
        return self.step(state), {}
