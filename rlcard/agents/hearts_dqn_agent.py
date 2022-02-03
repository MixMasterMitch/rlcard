import torch
import numpy as np

class HeartsDQNAgent(object):

    def __init__(self, device=None):
        self.use_raw_action = False
        self.use_raw_state = False

        # Torch device
        if device is None:
            self.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = device

    def feed(self, ts):
        return None

    def step(self, state):
        return np.random.choice(list(state['legal_actions'].keys()))

    def eval_step(self, state):
        return self.step(state), None

