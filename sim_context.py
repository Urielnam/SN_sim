import random

import simpy
from simpy import PriorityItem

# sim_context.py
class SimulationContext:
    def __init__(self, env, config):
        self.env = env
        self.config = config

        # Event driven queues
        # Central Bus Input (PriorityStore for random access)
        self.bus_input_queue = simpy.PriorityStore(self.env)

        # Destination Queues (FIFO)
        self.bus_edge_queue = simpy.Store(self.env) # Bus -> Edge Processor
        self.bus_scada_queue = simpy.Store(self.env) # Bus -> SCADA Actuator
        self.bus_iiot_queue = simpy.Store(self.env) # Bus -> IIoT Node (Feedback)

        # Local Buffers
        self.edge_sublist = []

        # Agent Registries
        self.iiot_list = []

        # Tracking flow rates for graphs
        self.agent_flow_rates_by_type = {
            "Network Bus": {},
            "Edge Processor": {},
            "SCADA Actuator":{}
        }

        self.number_of_iiots = {}

        # Data Collection (The Logs)
        self.data_age = {}
        self.data_age_by_type = {k: {} for k in self.config.data_type_keys}

        self.successful_operations = []
        self.edge_data_usage_time = []
        self.scada_data_usage_time =[]
        self.timestep_list = []
        self.self_organization_measure = {}
        self.successful_operations_total ={}
        self.total_resource = {}

    def send_to_bus(self, item):
        """
            Helper: Wraps an item with a random priority key and puts it
            onto the central bus queue.
            Returns the SimPy event (do not yield here, let the agent yield).
        """
        random_priority = random.random()
        sent_item = PriorityItem(priority=random_priority, item=item)
        return self.bus_input_queue.put(sent_item)

    def get_all_packets(self):
        """
        Aggregates all DataPackets currently in transit or buffers.
        Handles the difference between PriorityStore (wrapped) and Store (raw).
        :return:
        all_packets as an iterative list
        """

        all_packets = []

        # 1. Main Bus (Unwrap PriorityItem)
        all_packets.extend([x.item for x in self.bus_input_queue.items])

        # 2. FIFO Queues (Direct Access)
        all_packets.extend(self.bus_edge_queue.items)
        all_packets.extend(self.bus_scada_queue.items)
        all_packets.extend(self.bus_iiot_queue.items)

        # 3. Local Buffers (Lists)
        all_packets.extend(self.edge_sublist)

        return all_packets