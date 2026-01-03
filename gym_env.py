import gymnasium as gym
from gymnasium import spaces
import numpy as np
import simpy

from sim_context import SimulationContext
from sim_config import SimulationConfig
from agents import NetworkBus, EdgeProcessor, SCADAActuator, IIoTNode
from strategies import RLStrategy


class ISRSimEnv(gym.Env):
    """
    OpenAI Gym Interface for the ISR Simulation.
    """
    metadata = {'render.modes': ['human']}

    def __init__(self, config_overrides=None):
        super(ISRSimEnv, self).__init__()

        # 1. Define Action Space
        # 0: No Op, 1: Add Sensor, 2: Remove Sensor,
        # 3-4: Bus +/-, 5-6: Edge +/-, 7-8: SCADA +/-
        self.action_space = spaces.Discrete(9)

        # 2. Define Observation Space
        # [Bus_Q, Edge_Q, Scada_Q, Num_Sensors, Bus_Rate, Edge_Rate, Scada_Rate]
        # We use high bounds for queues and resource counts
        low = np.array([0, 0, 0, 0, 1, 1, 1], dtype=np.float32)
        high = np.array([1000, 1000, 1000, 200, 50, 50, 50], dtype=np.float32)
        self.observation_space = spaces.Box(low, high, dtype=np.float32)

        # 3. Config
        self.base_config = SimulationConfig(
            end_time=1000,  # Steps per episode
            optimization_method="rl",
            ui=False
        )
        if config_overrides:
            for k, v in config_overrides.items():
                setattr(self.base_config, k, v)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        # Re-initialize SimPy Environment
        self.env = simpy.Environment()
        self.ctx = SimulationContext(self.env, self.base_config)

        # Re-initialize Agents
        self.bus = NetworkBus(self.ctx)
        self.edge = EdgeProcessor(self.ctx)
        self.scada = SCADAActuator(self.ctx)
        self.ctx.iiot_list.append(IIoTNode(self.ctx, 0.5, 1))

        # Initialize Strategy (The RL Agent controls this)
        self.strategy = RLStrategy(self.ctx, self.bus, self.edge, self.scada)

        # Note: We do NOT call strategy.setup() or strategy.rl_step_loop() here.
        # The Gym 'step' function replaces the 'run' loop.

        # Start background physics (packet generation, transport)
        # We manually process events in the step() function

        return self._get_obs(), {}

    def step(self, action):
        # 1. Apply Action
        self.strategy.apply_action(action)

        # 2. Run Simulation for 1.0 second (Gym Step Duration)
        # We need to run the SimPy environment forward by 1 tick
        try:
            self.env.run(until=self.env.now + 1.0)
        except simpy.core.EmptySchedule:
            pass  # End of sim

        # 3. Get State
        obs = self._get_obs()

        # 4. Calculate Reward (Using Strategy's internal logic)
        reward = self.strategy.calculate_reward()

        # 5. Check Done
        terminated = self.env.now >= self.base_config.end_time
        truncated = False

        return obs, reward, terminated, truncated, {}

    def _get_obs(self):
        # Maps the strategy's state list to a numpy array for Gym
        raw_state = self.strategy.get_state()
        return np.array(raw_state, dtype=np.float32)

    def render(self, mode='human'):
        print(f"Time: {self.env.now} | Action: {self.strategy.last_action} | Reward: {self.strategy.last_reward}")

    def close(self):
        pass