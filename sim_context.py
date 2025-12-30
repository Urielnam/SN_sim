# sim_context.py
class SimulationContext:
    def __init__(self, env, config):
        self.env = env
        self.config = config

        # Queues (The State)
        self.sensor_array_queue = []
        self.array_analysis_queue = []
        self.analysis_array_queue = []
        self.array_action_queue = []
        self.action_array_queue = []
        self.array_sensor_queue = []
        self.analysis_sublist = []


        # Agent Registries
        self.sensor_list = []
        self.agent_flow_rates_by_type = {}
        self.agent_flow_rates_by_type["Array"] = {}
        self.agent_flow_rates_by_type["Analysis Station"] = {}
        self.agent_flow_rates_by_type["Action Station"] = {}
        self.number_of_sensors = {}

        # Define Topology Mappings (Routing Logic)
        self.start_nodes = {
            "sensor to array": self.sensor_array_queue,
            "analysis to array": self.analysis_array_queue,
            "action to array": self.action_array_queue
         }

        self.end_nodes = {
            "array to analysis": self.array_analysis_queue,
            "array to action": self.array_action_queue,
            "array to sensor": self.array_sensor_queue
        }

        # Data Collection (The Logs)
        self.data_age = {}
        self.data_age_by_type = {}

        for key in self.config.data_type_keys:
            self.data_age_by_type[key] ={}

        self.successful_operations = []
        self.analysis_data_usage_time = []
        self.action_data_usage_time =[]
        self.timestep_list = []
        self.self_organization_measure = {}
        self.successful_operations_total ={}
        self.total_resource = {}