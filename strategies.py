from abc import ABC, abstractmethod
import random


# Base Class
class OptimizationStrategy(ABC):
    def __init__(self, ctx, bus, edge, scada):
        self.ctx = ctx
        self.env = ctx.env
        self.config = ctx.config
        self.bus = bus
        self.edge = edge
        self.scada = scada

        # --- EVOLVABLE PARAMETERS (The "Genes") ---
        # Threshold: Queue size must be X times flow_rate to trigger upgrade
        self.threshold_mult = 5.0

        # Hysteresis: How long to wait before downgrading (prevent flickering)
        self.cooldown_ticks = 10

        # Register self with context for priority callbacks
        self.ctx.set_strategy(self)

    @abstractmethod
    def setup(self):
        """
        Default Setup: Starts the fundamental reactive loops.
        Override this to add extra processes (like Vibration) or
        to disable growth (for a pure Static mode).
        """

        self.env.process(self.monitor_sensors())
        self.env.process(self.monitor_component("bus", self.bus, self.ctx.bus_input_queue))
        self.env.process(self.monitor_component("edge", self.edge, self.ctx.bus_edge_queue))
        self.env.process(self.monitor_component("scada", self.scada, self.ctx.bus_scada_queue))

    def get_priority(self, packet):
        """
        Determines the priority of a packet.
        Default behavior: Random (Simulates standard Ethernet collision/contention).
        Override this for QoS strategies.
        """
        return random.random()

        # --- FUNDAMENTAL GROWTH LOOPS (Reactive Logic) ---

    def monitor_sensors(self):
        """
        Fundamental: Consumes Feedback to grow/shrink Sensor population.
        """
        while True:
            # 1. Wait for Feedback (Blocking)
            feedback = yield self.ctx.bus_iiot_queue.get()

            # 2. React to Feedback
            if feedback.status:
                # Success -> Survival/Growth
                self.add_iiot()
            else:
                # Failure -> Pruning
                # If specific creator is known, kill them.
                self.remove_sensor(feedback.creator)

                # Prevent total extinction (System Resilience)
                if len(self.ctx.iiot_list) == 0:
                    self.add_iiot()

            # 3. Global Constraint Check (Optional random pruning if over capacity)
            # This mimics resource shedding under load
            if not self._check_max_resource() and len(self.ctx.iiot_list) > 1:
                self.remove_sensor()

            # Yield briefly to let other processes run
            yield self.env.timeout(0.01)

    def monitor_component(self, name, agent, queue):
        """
        Fundamental: Monitors Queue length to adjust Bandwidth (Flow Rate).
        """
        # Track the last time we reduced resources for this specific component
        last_downgrade_time = -self.cooldown_ticks

        while True:
            yield self.env.timeout(0.1)
            q_len = len(queue.items)

            # 1. Scale Up Logic (Aggressive)
            # If queue exceeds the evolved threshold, upgrade immediately.
            if q_len > agent.flow_rate * self.threshold_mult:
                self.modify_flow_rate(name, 1)

            # 2. Scale Down Logic (Conservative / Hysteresis)
            # Only downgrade if queue is empty AND we haven't downgraded recently.
            elif q_len == 0:
                # Check if enough time has passed since the last downgrade
                if (self.env.now - last_downgrade_time) >= self.cooldown_ticks:
                    if self.modify_flow_rate(name, -1):
                        last_downgrade_time = self.env.now

    # --- UNIFIED API ---

    def _check_max_resource(self):
        current_usage = (len(self.ctx.iiot_list) +
                         self.bus.flow_rate +
                         self.edge.flow_rate +
                         self.scada.flow_rate)
        return current_usage < self.config.max_resource

    def add_iiot(self):
        """Action: Try to spawn a new IIoT Node."""
        if not self._check_max_resource():
            return False # Action Failed: Resource Cap

        from agents import IIoTNode

        # Logic: Assign ID based on count
        next_id = len(self.ctx.iiot_list) + 1

        # Logic: Inherit accuracy from config
        iiot_chance = self.config.iiot_acc * random.random()

        new_node = IIoTNode(self.ctx, iiot_chance, next_id)
        self.ctx.iiot_list.append(new_node)
        return True

    def remove_sensor(self, specific_node_name=None):
        """Action: Remove a sensor (pruning)."""
        if not self.ctx.iiot_list:
            return False

        target_node = None
        if specific_node_name:
            for node in self.ctx.iiot_list:
                if node.name == specific_node_name:
                    target_node = node
                    break
        else:
            # Random removal (strandard for resource shedding)
            target_node = random.choice(self.ctx.iiot_list)

        if target_node:
            target_node.is_alive = False
            if target_node in self.ctx.iiot_list:
                self.ctx.iiot_list.remove(target_node)
            return True
        return False

    def modify_flow_rate(self, component_name, delta):
        """Action: Increase/Decrease bandwidth of a component."""

        # Map name to object
        target_obj = None
        if component_name == "bus":
            target_obj = self.bus
        elif component_name == "edge":
            target_obj = self.edge
        elif component_name == "scada":
            target_obj = self.scada

        if not target_obj:
            return False

        # Apply Delta
        if delta > 0:
            if self._check_max_resource():
                target_obj.flow_rate += delta
                return True
        elif delta < 0:
            if target_obj.flow_rate > 1:
                target_obj.flow_rate += delta  # delta is negative
                return True

        return False

# -----------------------------------------------------------
# STRATEGY 1: BIOLOGICAL (The Original "Self-Org" Logic)
# -----------------------------------------------------------
class BiologicalStrategy(OptimizationStrategy):
    """
    The original logic:
    Extends Fundamental Growth with "Vibration":
    If the system settles into a stable but suboptimal state (low self-org measure),
    this strategy injects entropy to shake it out of the local minimum.
    """

    def setup(self):
        # 1. Start Fundamental Loops (Growth/Shrinkage)
        super().setup()

        # 2. Start Biological Vibration Loop
        self.env.process(self.self_org_manager())

    def self_org_manager(self):
        """
        Monitors the 'Self-Organization Measure' (Entropy).
        If the system is too static (< Threshold), randomly perturb agents.
        """
        while True:
            yield self.env.timeout(1.0)  # Check every 1s (less aggressive)

            # Need enough history
            if len(self.ctx.self_organization_measure) > 10:
                # Get latest measure
                last_measure = list(self.ctx.self_organization_measure.values())[-1][0]

                if last_measure < self.config.self_org_threshold:
                    # System is Stagnant -> Inject Entropy
                    self._inject_entropy()

    def _inject_entropy(self):
        # Randomly pick an action
        action_type = random.choice(['sensor', 'bus', 'edge', 'scada'])
        direction = random.choice([1, -1])

        if action_type == 'sensor':
            if direction == 1:
                self.add_iiot()
            else:
                self.remove_sensor()
        else:
            self.modify_flow_rate(action_type, direction)

# -----------------------------------------------------------
# STRATEGY 2: QoS (Quality of Service - get important information first)
# -----------------------------------------------------------

class QoSStrategy(OptimizationStrategy):
    """
    Static Benchmark Strategy:
    - Topology remains fixed (no growth/pruning).
    - Prioritizes traffic: Target > Feedback > Intel.
    - Consumes feedback only to prevent memory leaks.
    """

    def setup(self):
        # Start Fundamental Loops
        super().setup()

    def get_priority(self, packet):
        # High Priority for Critical Actions, Low for Raw Data
        jitter = random.random()
        if packet.type == 'target':
            return 1.0 + jitter
        elif packet.type == 'feedback':
            return 2.0 + jitter
        else:
            return 3.0 + jitter


# -----------------------------------------------------------
# STRATEGY 3: REINFORCEMENT LEARNING (Direct Control)
# -----------------------------------------------------------
class RLStrategy(OptimizationStrategy):
    """
    RL Strategy:
    - Disables background reactive heuristics.
    - Implements a periodic 'Step' loop (1.0s interval).
    - Defines State, Action, and Reward for an agent to learn.
    - Currently uses a RANDOM AGENT as a placeholder to demonstrate the API.
    """

    def setup(self):
        # NOTE: We do NOT call super().setup() here.
        # We want the RL agent to have full, exclusive control over the topology,
        # rather than fighting against the hardcoded 'monitor_sensors' logic.

        # Initialize internal state tracker
        self.last_success_count = 0
        self.last_time = 0

        # Start the RL Decision Loop
        self.env.process(self.rl_step_loop())

    def rl_step_loop(self):
        """
        The 'Gym Step' equivalent.
        Runs every 1.0 simulation seconds.
        """
        while True:
            # 1. Wait for next step (Simulates discrete time steps)
            yield self.env.timeout(1.0)

            # 2. Observe (Get State)
            state = self.get_state()

            # 3. Calculate Reward (Utility of previous step)
            reward = self.calculate_reward()

            # 4. Decide (Policy)
            # TODO: Connect this to a real Neural Net / Q-Table.
            # For now, we use a Random Agent to prove the Action API works.
            action = random.choice(range(9))

            # 5. Act (Apply)
            self.apply_action(action)

    def get_state(self):
        """
        Returns a simplified state vector (could be normalized in a real env):
        [Bus_Q, Edge_Q, Scada_Q, Num_Sensors, Bus_Rate, Edge_Rate, Scada_Rate]
        """
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
        """
        Reward = (New Successes * Weight) - (Resource Cost * Weight)
        """
        # Get total successes so far (safe access)
        if self.ctx.successful_operations_total:
            current_total_success = list(self.ctx.successful_operations_total.values())[-1][0]
        else:
            current_total_success = 0

        new_successes = current_total_success - self.last_success_count
        self.last_success_count = current_total_success

        # Calculate Cost (Active Agents + Bandwidth)
        current_resources = (len(self.ctx.iiot_list) +
                             self.bus.flow_rate +
                             self.edge.flow_rate +
                             self.scada.flow_rate)

        # Reward Function
        # We value 1 Success as worth 5 Resource units (Arbitrary Tuning)
        reward = (new_successes * 5) - current_resources
        return reward

    def apply_action(self, action_idx):
        """
        Maps discrete action indices to the Unified Action API.

        0: No Op
        1: Add Sensor
        2: Remove Sensor
        3: Bus Rate +
        4: Bus Rate -
        5: Edge Rate +
        6: Edge Rate -
        7: SCADA Rate +
        8: SCADA Rate -
        """
        if action_idx == 0:
            pass
        elif action_idx == 1:
            self.add_iiot()
        elif action_idx == 2:
            self.remove_sensor()
        elif action_idx == 3:
            self.modify_flow_rate("bus", 1)
        elif action_idx == 4:
            self.modify_flow_rate("bus", -1)
        elif action_idx == 5:
            self.modify_flow_rate("edge", 1)
        elif action_idx == 6:
            self.modify_flow_rate("edge", -1)
        elif action_idx == 7:
            self.modify_flow_rate("scada", 1)
        elif action_idx == 8:
            self.modify_flow_rate("scada", -1)


# -----------------------------------------------------------
# STRATEGY 4: GENETIC ALGORITHM (Online Hill-Climber)
# -----------------------------------------------------------
class GAStrategy(OptimizationStrategy):
    """
    Online Evolutionary Strategy:
    - Instead of controlling actions directly, it evolves the *Parameters* used by the reactive loops (e.g. threshold_mult).
    - Uses a (1+1)-ES (Evolution Strategy) approach:
      1. Mutate current params.
      2. Run for window 'W'.
      3. If Reward > Prev_Reward: Keep mutation. Else: Revert.
    """

    def setup(self):
        # 1. Start the standard reactive loops (which use self.threshold_mult)
        super().setup()

        # 2. Start the Evolution Loop
        self.current_reward = -float('inf')
        self.env.process(self.evolution_loop())

    def evolution_loop(self):
        evaluation_window = 10.0  # Time to test new genes

        while True:
            # --- SNAPSHOT BEFORE ---
            prev_params = self.threshold_mult

            # --- MUTATE ---
            # Randomly adjust the threshold multiplier (Range 2.0 to 10.0)
            mutation = random.uniform(-1.0, 1.0)
            self.threshold_mult = max(2.0, min(10.0, self.threshold_mult + mutation))

            # --- EVALUATE ---
            # Run simulation for the window
            start_success = self.get_total_success()
            start_cost = self.get_current_cost()

            yield self.env.timeout(evaluation_window)

            end_success = self.get_total_success()
            end_cost = self.get_current_cost()

            # Calculate Fitness (Gain in success vs Cost)
            delta_success = end_success - start_success
            avg_cost = (start_cost + end_cost) / 2
            fitness = (delta_success * 10) - avg_cost

            # --- SELECTION ---
            if fitness > self.current_reward:
                # Keep the mutation (It worked!)
                self.current_reward = fitness
                # Optional: print(f"GA Improved: New Threshold = {self.threshold_mult:.2f}, Fitness = {fitness}")
            else:
                # Revert (It failed)
                self.threshold_mult = prev_params
                # We do not update self.current_reward, keeping the high watermark

    def get_total_success(self):
        if self.ctx.successful_operations_total:
            return list(self.ctx.successful_operations_total.values())[-1][0]
        return 0

    def get_current_cost(self):
        return (len(self.ctx.iiot_list) +
                self.bus.flow_rate +
                self.edge.flow_rate +
                self.scada.flow_rate)