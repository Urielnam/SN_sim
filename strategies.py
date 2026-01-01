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

        # Register self with context for priority callbacks
        self.ctx.set_strategy(self)

    @abstractmethod
    def setup(self):
        """
        Called once at the start of the simulation.
        Use this to register SimPy processes (env.process) or initialize agents.
        """
        pass

    def get_priority(self, packet):
        """
        Determines the priority of a packet.
        Default behavior: Random (Simulates standard Ethernet collision/contention).
        Override this for QoS strategies.
        """
        return random.random()

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
    - Sensors reproduce on success, die on failure.
    - Components (Bus/Edge/SCADA) increase bandwidth if queues overflow.
    - "Vibration" logic if self-org metric is low.
    """

    def setup(self):
        # Register all the independent monitoring loops
        self.env.process(self.iiot_maker())
        self.env.process(self.bus_upgrade())
        self.env.process(self.edge_upgrade())
        self.env.process(self.scada_upgrade())

    # --- Logic moved from Simulation.py ---


    def iiot_maker(self):
        """
        Monitors feedback queue and adds/removes IIoT Nodes based on performance.
        """

        while True:
            # Wait for Feedback
            feedback = yield self.ctx.bus_iiot_queue.get()

            # Logic: Positive Feedback -> Grow
            if feedback.status:
                self.add_iiot()

            # Logic: Negative Feedback -> Prune
            else:
                self.remove_sensor(feedback.creator)
                if len(self.ctx.iiot_list) ==0:
                    self.add_iiot()

            # Max resource constraint check
            if not self._check_max_resource() and len(self.ctx.iiot_list) > 1:
                self.remove_sensor() # Random kill

            # "Vibration" / Self-Org Logic (The active flag check)
            if self.config.self_org_active:
                # If self org is less than threshold, have every agent type "vibrate"
                # if self_org less than threshold - increase agents
                # if no resources to increase agents, reduce agents.

                if len(self.ctx.self_organization_measure) > 600:
                    last_measure = list(self.ctx.self_organization_measure.values())[-1][0]
                    if last_measure < self.config.self_org_threshold:
                        # Force entropy if system is too stable
                        if len(self.ctx.iiot_list) == list(self.ctx.number_of_iiots.values())[-1][0]:
                            if not self.add_iiot():
                                # If add failed (resources), try remove
                                if len(self.ctx.iiot_list) > 1:
                                    self.remove_sensor()

            yield self.ctx.env.timeout(0.01)

            pass

    def increase_self_org(self, agent, agent_name, agent_str_id):
        # Helper for the upgrade functions
        if self.config.self_org_active and len(self.ctx.self_organization_measure) > 600:
            last_measure = list(self.ctx.self_organization_measure.values())[-1][0]
            if last_measure < self.config.self_org_threshold:
                # Check stability
                hist = list(self.ctx.agent_flow_rates_by_type[agent_name].values())
                if agent.flow_rate == hist[-1]:
                    # Try Up, if fail, Try Down
                    if not self.modify_flow_rate(agent_str_id, 1):
                        self.modify_flow_rate(agent_str_id, -1)

    def bus_upgrade(self):
        while True:
            yield self.env.timeout(0.1)
            q_len = len(self.ctx.bus_input_queue.items)

            # Reactive Logic
            if q_len > self.bus.flow_rate * 5:
                self.modify_flow_rate("bus", 1)
            elif q_len == 0:
                self.modify_flow_rate("bus", -1)

            # Proactive/Vibration Logic
            self.increase_self_org(self.bus, "Network Bus", "bus")

    def edge_upgrade(self):
        while True:
            yield self.env.timeout(0.1)
            q_len = len(self.ctx.bus_edge_queue.items)

            if q_len > self.edge.flow_rate * 5:
                self.modify_flow_rate("edge", 1)
            elif q_len == 0:
                self.modify_flow_rate("edge", -1)

            self.increase_self_org(self.edge, "Edge Processor", "edge")

    def scada_upgrade(self):
        while True:
            yield self.env.timeout(0.1)
            q_len = len(self.ctx.bus_scada_queue.items)

            if q_len > self.scada.flow_rate * 5:
                self.modify_flow_rate("scada", 1)
            elif q_len == 0:
                self.modify_flow_rate("scada", -1)

            self.increase_self_org(self.scada, "SCADA Actuator", "scada")