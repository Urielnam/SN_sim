import torch
import torch.nn as nn
import torch.optim as optim
import random
import numpy as np
from collections import deque


class ReplayBuffer:
    """
    The Memory Bank.
    In continuous online learning, if agents only train on the newest data,
    they suffer from 'Catastrophic Forgetting' and overwrite past crisis protocols.
    This buffer stores past experiences so the network trains on a mix of
    recent and historical data, ensuring true systemic resilience.
    """

    def __init__(self, capacity=10000):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state):
        # Store the transition tuple
        self.buffer.append((state, action, reward, next_state))

    def sample(self, batch_size):
        # Randomly sample historical chunks to break temporal correlation
        batch = random.sample(self.buffer, batch_size)
        state, action, reward, next_state = map(np.stack, zip(*batch))
        return state, action, reward, next_state

    def __len__(self):
        return len(self.buffer)


class ShallowQNetwork(nn.Module):
    """
    The Brain.
    A deliberately shallow Multi-Layer Perceptron (MLP).
    Performance Engineering: Deep networks (e.g., 5+ layers) are wasted on
    low-dimensional control tasks and will bottleneck the SimPy event loop.
    Two layers of 64 neurons are mathematically sufficient to map our
    stacked 1D array to a discrete action space.
    """

    def __init__(self, input_dim, output_dim):
        super(ShallowQNetwork, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, output_dim)
        )

    def forward(self, x):
        return self.network(x)


class MicroAgent:
    """
    The Agent Wrapper.
    Abstracts the PyTorch complexity away from the Strategy file.
    Implements a standard Deep Q-Learning (DQN) algorithm tailored for
    continuous, uninterrupted execution (no episodes or resets).
    """

    def __init__(self, input_dim, action_dim=3, lr=1e-3, gamma=0.99):
        self.action_dim = action_dim
        self.gamma = gamma

        # Initialize the shallow network and optimizer
        self.model = ShallowQNetwork(input_dim, action_dim)
        self.optimizer = optim.Adam(self.model.parameters(), lr=lr)
        self.loss_fn = nn.MSELoss()

        self.memory = ReplayBuffer(capacity=5000)

        # Exploration rate (Epsilon-greedy)
        # Starts high so agents explore during the "Cold Start" phase
        self.epsilon = 1.0
        self.epsilon_decay = 0.995
        self.epsilon_min = 0.05

    def act(self, state):
        """
        Determines the next action. Uses Epsilon-Greedy to balance
        exploring new structural configurations vs exploiting known optimal paths.
        """
        if random.random() <= self.epsilon:
            # Explore: Random action
            return random.randrange(self.action_dim)

        # Exploit: Ask the Neural Network
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        with torch.no_grad():
            q_values = self.model(state_tensor)

        # Return the index of the highest Q-value
        return torch.argmax(q_values[0]).item()

    def learn(self, batch_size=32):
        """
        The Adaptation Phase.
        Fires every N ticks (The Stride). Pulls a batch from the Replay Buffer
        and updates the network weights using backpropagation.
        """
        if len(self.memory) < batch_size:
            return  # Not enough data to train yet (Cold Start protection)

        # 1. Sample from memory
        states, actions, rewards, next_states = self.memory.sample(batch_size)

        states = torch.FloatTensor(states)
        actions = torch.LongTensor(actions).unsqueeze(1)
        rewards = torch.FloatTensor(rewards).unsqueeze(1)
        next_states = torch.FloatTensor(next_states)

        # 2. Calculate current Q values
        current_q = self.model(states).gather(1, actions)

        # 3. Calculate target Q values (Bellman Equation)
        with torch.no_grad():
            max_next_q = self.model(next_states).max(1)[0].unsqueeze(1)
            target_q = rewards + (self.gamma * max_next_q)

        # 4. Compute Loss and Backpropagate
        loss = self.loss_fn(current_q, target_q)

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # 5. Decay exploration rate slowly over time
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay