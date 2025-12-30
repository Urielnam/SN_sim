# sim_context.py
class SimulationContext:
    def __init__(self, env, config):
        self.env = env
        self.config = config

        # Queues (The State)
        self.iiot_bus_queue = []
        self.bus_edge_queue = []
        self.edge_bus_queue = []
        self.bus_scada_queue = []
        self.scada_bus_queue = []
        self.bus_iiot_queue = []
        self.edge_sublist = []


        # Agent Registries
        self.iiot_list = []
        self.agent_flow_rates_by_type = {}
        self.agent_flow_rates_by_type["Network Bus"] = {}
        self.agent_flow_rates_by_type["Edge Processor"] = {}
        self.agent_flow_rates_by_type["SCADA Actuator"] = {}
        self.number_of_iiots = {}

        # Define Topology Mappings (Routing Logic)
        self.start_nodes = {
            "iiot to bus": self.iiot_bus_queue,
            "edge to bus": self.edge_bus_queue,
            "scada to bus": self.scada_bus_queue
         }

        self.end_nodes = {
            "bus to edge": self.bus_edge_queue,
            "bus to scada": self.bus_scada_queue,
            "bus to iiot": self.bus_iiot_queue
        }

        # Data Collection (The Logs)
        self.data_age = {}
        self.data_age_by_type = {}

        for key in self.config.data_type_keys:
            self.data_age_by_type[key] ={}

        self.successful_operations = []
        self.edge_data_usage_time = []
        self.scada_data_usage_time =[]
        self.timestep_list = []
        self.self_organization_measure = {}
        self.successful_operations_total ={}
        self.successful_operations_total ={}
        self.total_resource = {}