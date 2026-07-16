from abc import ABC, abstractmethod
import random
import numpy as np
import os

# Try to import PPO for the RL Strategy
try:
    from stable_baselines3 import PPO
    SB3_AVAILABLE = True
except ImportError:
    SB3_AVAILABLE = False
    print("Warning: stable-baselines3 not found. RL Strategy will default to Random.")

def calculate_qos_priority(packet):
    """Standalone helper to calculate QoS priority to prevent code duplication."""
    jitter = random.random()
    if packet.type == 'target':
        return 1.0 + jitter
    elif packet.type == 'feedback':
        return 2.0 + jitter
    else:
        return 3.0 + jitter

# ==========================================
# 1. THE CORE BASE (The 'Static' Blueprint)
# ==========================================
class BaseStrategy(ABC):
    """
    The Base Strategy defines the fundamental actions (API) and telemetry getters.
    By itself, it is completely inert (Static Strategy).
    """
    def __init__(self, ctx, bus, edge, scada, p2p_matrix=None, s2p_matrix=None):
        self.ctx = ctx
        self.env = ctx.env
        self.config = ctx.config
        self.bus = bus
        self.edge = edge
        self.scada = scada

        # Default to Fully Observable if no matrices are provided
        self.p2p_matrix = p2p_matrix if p2p_matrix else [[1, 1, 1, 1] for _ in range(4)]
        self.s2p_matrix = s2p_matrix if s2p_matrix else [[1, 1, 1] for _ in range(4)]

        # --- EVOLVABLE PARAMETERS (The "Genes") ---
        # Threshold: Queue size must be X times flow_rate to trigger upgrade
        self.threshold_mult = 5.0

        # Hysteresis: How long to wait before downgrading (prevent flickering)
        self.cooldown_ticks = 10

        # Register self with context for priority callbacks
        self.ctx.set_strategy(self)

    def setup(self):
        """Base setup does nothing. This creates the pure Static state."""
        pass

    def get_priority(self, packet):
        """Default behavior: Random (Simulates standard Ethernet collision/contention)."""
        return random.random()

    # --- UNIFIED TELEMETRY (DRY) ---
    def get_current_cost(self):
        """Unified tracking of active resources across all mixins."""
        return (len(self.ctx.iiot_list) +
                self.bus.flow_rate +
                self.edge.flow_rate +
                self.scada.flow_rate)

    def get_total_success(self):
        """Unified tracking of accumulated success across all mixins."""
        if self.ctx.successful_operations_total:
            return list(self.ctx.successful_operations_total.values())[-1]
        return 0

    def _check_max_resource(self):
        return self.get_current_cost() < self.config.max_resource

    # --- UNIFIED ACTION API ---
    def add_iiot(self):
        if not self._check_max_resource():
            return False
        from agents import IIoTNode
        next_id = len(self.ctx.iiot_list) + 1
        iiot_chance = self.config.iiot_acc * random.random()
        new_node = IIoTNode(self.ctx, iiot_chance, next_id)
        self.ctx.iiot_list.append(new_node)
        return True

    def remove_sensor(self, specific_node_name=None):
        if not self.ctx.iiot_list:
            return False

        target_node = None
        if specific_node_name:
            for node in self.ctx.iiot_list:
                if node.name == specific_node_name:
                    target_node = node
                    break
        else:
            target_node = random.choice(self.ctx.iiot_list)

        if target_node:
            target_node.is_alive = False
            if target_node in self.ctx.iiot_list:
                self.ctx.iiot_list.remove(target_node)
            return True
        return False

    def modify_flow_rate(self, component_name, delta):
        target_obj = None
        if component_name == "bus":
            target_obj = self.bus
        elif component_name == "edge":
            target_obj = self.edge
        elif component_name == "scada":
            target_obj = self.scada

        if not target_obj:
            return False

        if delta > 0:
            if self._check_max_resource():
                target_obj.flow_rate += delta
                return True
        elif delta < 0:
            if target_obj.flow_rate > 1:
                target_obj.flow_rate += delta
                return True
        return False


# ==========================================
# 2. THE MIXINS (Modular Behaviors)
# ==========================================
class FundamentalMixin:
    """Reactive scaling feedback loops based on queue sizes and feedback successes."""
    def setup_fundamental(self):
        self.env.process(self.monitor_sensors())
        self.env.process(self.monitor_component("bus", self.bus, self.ctx.bus_input_queue))
        self.env.process(self.monitor_component("edge", self.edge, self.ctx.bus_edge_queue))
        self.env.process(self.monitor_component("scada", self.scada, self.ctx.bus_scada_queue))

    def monitor_sensors(self):
        while True:
            feedback = yield self.ctx.bus_iiot_queue.get()
            if feedback.status:
                self.add_iiot()
            else:
                self.remove_sensor(feedback.creator)
                if len(self.ctx.iiot_list) == 0:
                    self.add_iiot()

            if not self._check_max_resource() and len(self.ctx.iiot_list) > 1:
                self.remove_sensor()
            yield self.env.timeout(0.01)

    def monitor_component(self, name, agent, queue):
        last_downgrade_time = -self.cooldown_ticks
        while True:
            yield self.env.timeout(0.1)
            q_len = len(queue.items)

            if q_len > agent.flow_rate * self.threshold_mult:
                self.modify_flow_rate(name, 1)
            elif q_len == 0:
                if (self.env.now - last_downgrade_time) >= self.cooldown_ticks:
                    if self.modify_flow_rate(name, -1):
                        last_downgrade_time = self.env.now

class BiologicalMixin:
    """Injects entropy/vibration to escape local minima in self-organization."""
    def setup_biological(self):
        self.env.process(self.self_org_manager())

    def self_org_manager(self):
        while True:
            yield self.env.timeout(1.0)
            if len(self.ctx.self_organization_measure) > 10:
                last_measure = list(self.ctx.self_organization_measure.values())[-1]
                if last_measure < self.config.self_org_threshold:
                    self._inject_entropy()

    def _inject_entropy(self):
        action_type = random.choice(['sensor', 'bus', 'edge', 'scada'])
        direction = random.choice([1, -1])

        if action_type == 'sensor':
            if direction == 1: self.add_iiot()
            else: self.remove_sensor()
        else:
            self.modify_flow_rate(action_type, direction)

class QoSMixin:
    """Prioritizes critical traffic dynamically (Overloads get_priority method)."""
    def get_priority(self, packet):
        return calculate_qos_priority(packet)

class GAMixin:
    """Online (1+1)-Evolution Strategy Hill-Climber."""
    def setup_ga(self):
        self.current_reward = -float('inf')
        self.env.process(self.evolution_loop())

    def evolution_loop(self):
        evaluation_window = 10.0
        while True:
            prev_params = self.threshold_mult
            mutation = random.uniform(-1.0, 1.0)
            self.threshold_mult = max(2.0, min(10.0, self.threshold_mult + mutation))

            start_success = self.get_total_success()
            start_cost = self.get_current_cost()

            yield self.env.timeout(evaluation_window)

            end_success = self.get_total_success()
            end_cost = self.get_current_cost()

            delta_success = end_success - start_success
            avg_cost = (start_cost + end_cost) / 2
            fitness = (delta_success * 10) - avg_cost

            if fitness > self.current_reward:
                self.current_reward = fitness
            else:
                self.threshold_mult = prev_params

class RLMixin:
    """Reinforcement Learning inference loop."""
    def setup_rl(self):
        # Initialize internal state trackers locally for the mixin
        self.last_success_count = 0
        self.last_time = 0
        self.model = None
        model_path = "models/PPO/isr_final_model.zip"

        if SB3_AVAILABLE and os.path.exists(model_path):
            try:
                self.model = PPO.load(model_path)
            except Exception as e:
                print(f"RL Strategy: Failed to load model. Error: {e}")
        else:
            if not SB3_AVAILABLE:
                print("RL Strategy: SB3 library missing.")
            else:
                print(f"RL Strategy: Model not found at {model_path}")

        self.env.process(self.rl_step_loop())

    def rl_step_loop(self):
        while True:
            yield self.env.timeout(1.0)
            state_list = self.get_state()
            obs = np.array(state_list, dtype=np.float32)

            if self.model:
                action, _ = self.model.predict(obs, deterministic=True)
                action = int(action)
            else:
                action = random.choice(range(9))

            self.apply_action(action)

    def get_state(self):
        return [
            len(self.ctx.bus_input_queue.items),
            len(self.ctx.bus_edge_queue.items),
            len(self.ctx.bus_scada_queue.items),
            len(self.ctx.iiot_list),
            self.bus.flow_rate,
            self.edge.flow_rate,
            self.scada.flow_rate
        ]

    def calculate_reward(self):
        current_total_success = self.get_total_success()
        new_successes = current_total_success - self.last_success_count
        self.last_success_count = current_total_success
        reward = (new_successes * 50) - self.get_current_cost()
        return reward

    def apply_action(self, action_idx):
        if action_idx == 0: pass
        elif action_idx == 1: self.add_iiot()
        elif action_idx == 2:
            if len(self.ctx.iiot_list) > 1: self.remove_sensor()
        elif action_idx == 3: self.modify_flow_rate("bus", 1)
        elif action_idx == 4: self.modify_flow_rate("bus", -1)
        elif action_idx == 5: self.modify_flow_rate("edge", 1)
        elif action_idx == 6: self.modify_flow_rate("edge", -1)
        elif action_idx == 7: self.modify_flow_rate("scada", 1)
        elif action_idx == 8: self.modify_flow_rate("scada", -1)

# ==========================================
# 3. ASSEMBLED STRATEGIES (Assembly Only)
# ==========================================

# 1. Pure Control
class StaticStrategy(BaseStrategy):
    pass

# 2. Fundamental Combinations
class PureFundamentalStrategy(FundamentalMixin, BaseStrategy):
    def setup(self):
        self.setup_fundamental()

# 3. Biological Combinations
class PureBiologicalStrategy(BiologicalMixin, BaseStrategy):
    def setup(self):
        self.setup_biological()

class BiologicalStrategy(BiologicalMixin, FundamentalMixin, BaseStrategy):
    """The original Bio loop: Fundamental scaling + Entropy injections."""
    def setup(self):
        self.setup_fundamental()
        self.setup_biological()

# 4. QoS Combinations
class PureQoSStrategy(QoSMixin, BaseStrategy):
    pass

class QoSStrategy(QoSMixin, FundamentalMixin, BaseStrategy):
    """The original QoS benchmark: Prioritization + Fundamental scaling."""
    def setup(self):
        self.setup_fundamental()

class PureQoSBioStrategy(QoSMixin, BiologicalMixin, BaseStrategy):
    """QoS prioritization + Entropy injections (No queue-based reactive scaling)."""
    def setup(self):
        self.setup_biological()

class QoSBioStrategy(QoSMixin, BiologicalMixin, FundamentalMixin, BaseStrategy):
    """The ultimate combo: Prioritization + Scaling + Entropy."""
    def setup(self):
        self.setup_fundamental()
        self.setup_biological()

# 5. GA Combinations
class PureGAStrategy(GAMixin, BaseStrategy):
    def setup(self):
        self.setup_ga()

class GAStrategy(GAMixin, FundamentalMixin, BaseStrategy):
    """GA Tuning the Fundamental reactive threshold."""
    def setup(self):
        self.setup_fundamental()
        self.setup_ga()

# 6. Reinforcement Learning
class RLStrategy(RLMixin, BaseStrategy):
    def setup(self):
        self.setup_rl()


# ==========================================
# 7. MULTI-AGENT INFORMATION STREAM TEST RIG
# ==========================================
class MaskedRandomStrategy(BaseStrategy):
    """
    A 'Dumb' test rig to verify information streams.
    Agents act randomly, but their actions are driven by a loop that
    strictly filters the global state through p2p and s2p matrices.
    """

    def setup(self):
        """Starts 4 independent decision loops for the 4 agents."""
        # print(f"DEBUG - Strategy received p2p: {self.p2p_matrix}")
        self.env.process(self.agent_loop(agent_id=0))  # Sensor Controller
        self.env.process(self.agent_loop(agent_id=1))  # Bus Controller
        self.env.process(self.agent_loop(agent_id=2))  # Edge Controller
        self.env.process(self.agent_loop(agent_id=3))  # SCADA Controller

    def get_global_state(self):
        """
        Constructs the exact 7-variable global state vector by pulling
        from the most recent snapshot generated by BackendClasses.py.
        """
        # Fallback for tick 0 if the metric monitor hasn't run yet
        if not self.ctx.state_snapshots:
            return [len(self.ctx.iiot_list), self.bus.flow_rate, self.edge.flow_rate,
                    self.scada.flow_rate, len(self.ctx.bus_input_queue.items), 0, 0]

        # Pull the latest snapshot vector
        latest_snapshot = self.ctx.state_snapshots[-1]

        # Map the dictionary keys directly to our 7 variables
        x1 = latest_snapshot["num_iiots"]
        x2 = latest_snapshot["bus_flow"]
        x3 = latest_snapshot["edge_flow"]
        x4 = latest_snapshot["scada_flow"]
        x5 = latest_snapshot["queue_len"]
        x6 = latest_snapshot["success_rate"]
        x7 = latest_snapshot["avg_latency"]

        return [x1, x2, x3, x4, x5, x6, x7]

    def get_restricted_view(self, global_state, agent_id):
        """Applies the matrices to hide unauthorized variables."""
        agent_states = global_state[0:4]
        system_metrics = global_state[4:7]

        p2p_mask = self.p2p_matrix[agent_id]
        s2p_mask = self.s2p_matrix[agent_id]

        # Replace hidden values (mask == 0) with -1
        masked_agents = [val if mask == 1 else -1 for val, mask in zip(agent_states, p2p_mask)]
        masked_metrics = [val if mask == 1 else -1 for val, mask in zip(system_metrics, s2p_mask)]

        return masked_agents + masked_metrics

    def agent_loop(self, agent_id):
        """The independent decision-making loop for each agent."""
        while True:
            # Wait 1 simulation tick (adjust frequency as needed)
            yield self.env.timeout(1.0)

            # 1. Get true global state
            global_state = self.get_global_state()

            # 2. Filter it through the matrices
            restricted_view = self.get_restricted_view(global_state, agent_id)

            # Uncomment this print statement to watch the matrices working in your console!
            # print(f"Time {self.env.now} | Agent {agent_id} View: {restricted_view}")

            # 3. Agent executes a random action (Dumb Agent)
            # They use the unified API provided by BaseStrategy
            if agent_id == 0:
                # Sensor Agent: Pass, Add, or Remove
                action = random.choice(['pass', 'add', 'remove'])
                if action == 'add':
                    self.add_iiot()
                elif action == 'remove':
                    if len(self.ctx.iiot_list) > 1:
                        self.remove_sensor()

            elif agent_id == 1:
                # Bus Agent: Pass, Flow +1, Flow -1
                action = random.choice([0, 1, -1])
                if action != 0: self.modify_flow_rate("bus", action)

            elif agent_id == 2:
                # Edge Agent: Pass, Flow +1, Flow -1
                action = random.choice([0, 1, -1])
                if action != 0: self.modify_flow_rate("edge", action)

            elif agent_id == 3:
                # SCADA Agent: Pass, Flow +1, Flow -1
                action = random.choice([0, 1, -1])
                if action != 0: self.modify_flow_rate("scada", action)