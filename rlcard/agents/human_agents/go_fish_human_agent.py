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
            if i == 0:
                print_card(raw_state['player_hand'])
            else:
                print_card([None] * raw_state['card_counts'][i])

        print('\n=========== Actions You Can Choose ===========')
        print(', '.join([str(index) + ': ' + str(action) for index, action in enumerate(state['raw_legal_actions'])]))
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
