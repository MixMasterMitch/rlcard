from rlcard.utils.utils import print_card
from rlcard.games.base import Card


class HumanAgent(object):
    ''' A human agent for Hearts.
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

        passing_cards = raw_state['passing_cards']
        pass_player_id = raw_state['passing_cards_players_to_left']
        trick = raw_state['trick']

        print('\n===============   State   ===============')
        print('Hearts broken: {}'.format(raw_state['hearts_are_broken']))

        if raw_state['can_sluff']:
            print('You get to sluff this trick')

        if not passing_cards:
            print('\n===============   Trick   ===============')
            print_card(trick)

        print('\n===============   Your Hand   ===============')
        hand_list = sorted(list(raw_state['player_hand']), key=lambda card: '{}{:02d}'.format(card.suit, Card.valid_rank.index(card.rank)))
        print_card(hand_list)

        print('\n=========== Actions You Can Choose ===========')
        actions_by_number = {}
        current_action_number = 0
        for suit in Card.valid_suit:
            for rank in Card.valid_rank:
                action = '{}{}'.format(suit, rank)
                if action in state['raw_legal_actions']:
                    if passing_cards:
                        print('{}: Pass {} to Player {}'.format(current_action_number, action, pass_player_id))
                    else:
                        print('{}: Play {}'.format(current_action_number, action))
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
