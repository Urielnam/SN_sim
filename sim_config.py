# sim_config.py
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class SimulationConfig:
    # Simulation Control
    end_time: int = 1000
    dt: float = 5
    max_resource: int = 100

    # Physics/Logic
    sensor_acc: float = 0.1
    self_org_active: bool = False
    self_org_threshold: float = 35

    data_type_keys = ["intel", "feedback", "target"]

    # Topology (Moved from Simulation.py global scope)
    connecting_graph: Dict = field(default_factory=lambda: {
        "action to array": {
            "intel": "array to analysis",
            "feedback": "array to analysis",
            "target": "array to analysis"
        },
        "analysis to array": {
            "intel": "array to action",
            "feedback": "array to sensor",
            "target": "array to action"
        },
        "sensor to array": {
            "intel": "array to analysis",
            "feedback": "array to analysis",
            "target": "array to analysis"
        }
    })

    ui: bool = False
    print_excel: bool = False