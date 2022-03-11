import torch
import torch.nn as nn
import numpy as np
import copy
import random
from collections import deque

from rlcard.agents import DQNAgent

class HyperParams():
    def __init__(self):
        # How many experiences to keep in memory. Should be in the thousands. A larger memory gives a larger
        # range of experiences to learn from, but also means that older experiences are still around that
        # have already been throughly learned from and not adding value.
        self.replay_memory_size = 20000

        # How many experiences from the replay memory to use at a time when training. Should be a value between 1 and 128.
        # A larger value helps average out noise in the experiences, but also increases training computation.
        self.batch_size = 64

        # The minimum number of experiences needed in memory before starting training. A larger number enables more experiences
        # to be collected quickly without slowing down to do training. But too large a number reduces to value those early
        # experiences provide to the training.
        self.burnin = 200

        # How often to update the network after receiving a new transition. Should be an integer >= 1.
        # A larger value enables the model to see more new experiences before measuring loss and updating again.
        self.train_every = 3

        # How often to copy the online network to the target network in DDQN. Should be in the thousands.
        # A larger value keeps the target network locked for longer, increasing the stability of the target,
        # but a larger value also causes the target and online networks to get further out of sync with each other
        # meaning that when a sync does happen it is a larger shock to the training process.
        self.sync_target_network_every = 1000

        # How strongly to adjust network weights by on each update. A higher value speeds up learning
        # but increases risk of overfitting or thrashing of the weights. Should be a value
        self.learning_rate = 0.00025

        # The Q function is recursive (reward of action + Q value of best action for next state).
        # So to incentivize getting to a solution quicker (i.e. reduce wandering and looping action sequences)
        # each future action Q value is slightly discounted a small amount. This is often called gamma.
        # Should be a value just below 1.0. A lower value will cut out longer action sequences. This trims
        # the fat of unnecessarily long action sequences, but could accidentally cut out a longer optimal path.
        self.discount_factor = 0.9

        # Exploration Rate (also called epsilon) dictates what percentage of the time the model makes a random choice
        # instead of using the network. Making random choices allows the network to explore, evolve, learn, and try
        # new actions.

        # Should be a high value (e.g. 0.9 - 1.0) in order to effectively explore lots of options
        # and not get sucked into converging on a sub-optimal network.
        self.exploration_rate_max = 1.0
        # Should be a low value (e.g. 0.05 - 0.2) in order for the network to refine itself and
        # work towards an optimal network. Too low and it will take a long time to learn.
        # Too high and it will be thrown off by the randomness and have a hard time converging.
        self.exploration_rate_min = 0.1
        # Should be value just below 1.0. Faster decay will help the model converge quicker.
        # Slower decay will give it more opportunity to explore and land on a more globablly optimal network.
        self.exploration_rate_decay = 0.99999

class HeartsDQNAgent(object):

    def __init__(self, env, device):
        self.use_raw_action = False
        self.use_raw_state = False
        self.device = device
        self.hyper_params = HyperParams()

        self.pass_selection_model = Model(env.passing_state_shape, [256], env.action_shape, self.hyper_params, device)
        self.lead_model           = Model(env.playing_state_shape, [1028], env.action_shape, self.hyper_params, device)
        self.sluff_model          = Model(env.playing_state_shape, [1028], env.action_shape, self.hyper_params, device)
        self.second_player_model  = Model(env.playing_state_shape, [1028], env.action_shape, self.hyper_params, device)
        self.thrid_player_model   = Model(env.playing_state_shape, [1028], env.action_shape, self.hyper_params, device)
        self.fourth_player_model  = Model(env.playing_state_shape, [1028], env.action_shape, self.hyper_params, device)

    def feed(self, ts):
        (state, action, reward, next_state, done) = tuple(ts)
        model = self._get_model_for_state(state['raw_obs'])
        next_state_model = self._get_model_for_state(next_state['raw_obs'])
        model.record_experience(state['obs'], action, reward, next_state_model, next_state['obs'], next_state['legal_actions_mask'], done)
        return model.train()

    def step(self, state, eval_mode=False):
        model = self._get_model_for_state(state['raw_obs'])

        # In not evaluation mode, a random action should be taken based on the exploration rate
        if not eval_mode:

            # Determine if a random action should be taken
            explore = np.random.rand() < model.exploration_rate

            # Decay the exploration rate
            model.exploration_rate = max(self.hyper_params.exploration_rate_min, model.exploration_rate * self.hyper_params.exploration_rate_decay)

            # If exploring, choose a random action
            if explore:
                legal_action_ids = (state['legal_actions_mask'] >= 0).nonzero()[0]
                return np.random.choice(legal_action_ids)

        # Otherwise, use the model to determine the best action
        state_tensor = torch.from_numpy(state['obs']).float().to(self.device)
        legal_actions_mask_tensor = torch.from_numpy(state['legal_actions_mask']).float().to(self.device)
        return model.get_best_action(state_tensor, legal_actions_mask_tensor).item()

    def eval_step(self, state):
        return self.step(state, eval_mode=True)

    def _get_model_for_state(self, raw_state):
        ''' Determines which model to use for the given input state '''
        if raw_state['passing_cards']:
            return self.pass_selection_model
        if raw_state['is_lead']:
            return self.lead_model
        if raw_state['can_sluff']:
            return self.sluff_model
        player_trick_position = raw_state['player_trick_position']
        if player_trick_position == 1:
            return self.second_player_model
        if player_trick_position == 2:
            return self.thrid_player_model
        if player_trick_position == 3:
            return self.fourth_player_model
        raise Exception('Could not determine correct model for state')


class Model():
    def __init__(self, state_shape, mlp_layers, action_shape, hyper_params, device):
        self.memory = Memory(hyper_params, device)
        self.online_network = Network(state_shape, mlp_layers, action_shape).to(device)
        self.target_network = self.online_network.create_target_copy().to(device)
        self.optimizer = torch.optim.Adam(self.online_network.parameters(), lr=hyper_params.learning_rate)
        self.loss_fn = torch.nn.SmoothL1Loss()
        self.num_experiences = 0
        self.training_step = 0
        self.hyper_params = hyper_params
        self.exploration_rate = hyper_params.exploration_rate_max # This value is read and updated by the HeartsDQNAgent class

    def record_experience(self, state, action, reward, next_state_model, next_state, next_legal_actions_mask, done):
        self.memory.save(state, action, reward, next_state_model, next_state, next_legal_actions_mask, done)
        self.num_experiences += 1

    def get_best_action(self, state, legal_actions_mask):
        ''' Gets the index of the action with the highest Q value (works with batches or single values) '''
        masked_q_values = self._get_masked_q_values(state, legal_actions_mask, self.online_network)
        return torch.argmax(masked_q_values)

    def _get_predicted_q_value(self, state, action):
        ''' Calculate `Q(s, a)` (predicted Q value) using the online network '''
        return self._get_q_value(state, action, self.online_network)

    def _get_actual_q_value(self, reward, next_state_model, next_state, legal_actions_mask, done):
        ''' Calculate `r(s, a) + gamma * max[Q(s',a')]` (actual Q value) using target network
            This first requires calculating the value of a' which maximizes Q(s',a'), which is done on the online network
        '''
        if done:
            return reward
        next_q_value = next_state_model.get_next_q_value(next_state, legal_actions_mask)
        return (reward + self.hyper_params.discount_factor * next_q_value).float()

    @torch.no_grad()
    def get_next_q_value(self, next_state, legal_actions_mask):
        ''' Returns the `max[Q(s',a')]` portion of the Q function.
            This method is expected to be called from other models during their training
        '''
        best_next_action = self.get_best_action(next_state, legal_actions_mask)
        return self._get_q_value(next_state, best_next_action, self.target_network)

    def train(self):

        # Make sure we have enough experiences to start training
        if self.num_experiences < self.hyper_params.burnin:
            return (None, None, None)

        # Make sure we are on a training iteration
        if self.num_experiences % self.hyper_params.train_every != 0:
            return (None, None, None)

        self.training_step += 1

        # Sync online and target networks as needed
        if self.training_step % self.hyper_params.sync_target_network_every == 0:
            self.target_network.load_state_dict(self.online_network.state_dict())

        # Sample from memory
        samples = self.memory.sample()

        # Get prediced Q values and actual Q values of the batch
        predicted_q_value_batch = torch.zeros(len(samples))
        actual_q_value_batch = torch.zeros(len(samples))
        for i, sample in enumerate(samples):
            state, action, reward, next_state_model, next_state, next_legal_actions_mask, done = sample
            # print(reward)
            predicted_q_value_batch[i] = self._get_predicted_q_value(state, action)
            # print(predicted_q_value_batch[i])
            actual_q_value_batch[i] = self._get_actual_q_value(reward, next_state_model, next_state, next_legal_actions_mask, done)
            # print(actual_q_value_batch[i])

        # Determine loss and update model
        # print('before')
        # for name, param in self.online_network.named_parameters():
        #     print(name, param.data)
        loss = self.loss_fn(predicted_q_value_batch, actual_q_value_batch)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        # print('after')
        # for name, param in self.online_network.named_parameters():
        #     print(name, param.data)
        return (predicted_q_value_batch.mean().item(), loss.item(), self.exploration_rate)

    def _get_q_value(self, state, action, network):
        return network(state)[action]

    def _get_masked_q_values(self, state, legal_actions_mask, network):
        q_values = network(state)
        return q_values.add(legal_actions_mask) # Addition is used here because the mask isn't a true "mask". The mask uses values of -inf and 0 so that it can effectively kill illegal actions

class Network(nn.Module):
    '''
        A neural network with an input of the current state and an output of Q values.
        In other words, the output is Q(state, action) for all possible actions.
    '''

    def __init__(self, state_shape=None, mlp_layers=None, action_shape=None):
        ''' Initialize the Q network

        Args:
            state_shape (list): shape of state tensor (must be a 1D shape)
            mlp_layers (list): output size of each fully connected hidden layer
            action_shape (list): shape of action space
        '''
        super(Network, self).__init__()

        if len(state_shape) != 1:
            raise ValueError("Expecting 1D state shape")
        if len(action_shape) != 1:
            raise ValueError("Expecting 1D action shape")

        # Build the Q network
        layer_dims = state_shape + mlp_layers + action_shape
        fc = []
        for i in range(len(layer_dims)-2):
            fc.append(nn.Linear(layer_dims[i], layer_dims[i+1], bias=True))
            fc.append(nn.ReLU())
            # TODO: Try fc.append(nn.Tanh())
        fc.append(nn.Linear(layer_dims[-2], layer_dims[-1], bias=True))
        self.fc_layers = nn.Sequential(*fc)


    def create_target_copy(self):
        ''' Creates a copy of this network with frozen parameters to use as a target model for DDQN '''

        target = copy.deepcopy(self)

        # Freeze parameters to prevent back propagation in the network
        for p in target.parameters():
            p.requires_grad = False

        return target

    def forward(self, s):
        return self.fc_layers(s)

class Memory(object):
    ''' Memory for saving transitions
    '''

    def __init__(self, hyper_params, device):
        self.batch_size = hyper_params.batch_size
        self.memory = deque(maxlen=hyper_params.replay_memory_size)
        self.device = device

    def save(self, state, action, reward, next_state_model, next_state, next_legal_actions_mask, done):
        ''' Save experience into memory

        Args:
        TODO Update
            state (numpy.array): the current state
            action (int): the performed action ID
            reward (float): the reward received
            next_state (numpy.array): the next state after performing the action
            next_legal_actions_mask (numpy.array): a mask of the legal actions of the next state (-inf for illegal actions and 0 for legal actions)
            done (boolean): whether the episode is finished
        '''
        experience = (
            torch.from_numpy(state).float().to(self.device),
            torch.tensor([action], device=self.device),
            torch.tensor([reward], device=self.device),
            next_state_model,
            torch.from_numpy(next_state).float().to(self.device),
            torch.from_numpy(next_legal_actions_mask).float().to(self.device),
            done,
        )
        self.memory.append(experience)

    def sample(self):
        ''' Sample a minibatch from the replay memory '''
        return random.sample(self.memory, self.batch_size)

