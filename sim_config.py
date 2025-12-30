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
    iiot_acc: float = 0.1
    self_org_active: bool = False
    self_org_threshold: float = 35

    data_type_keys = ["intel", "feedback", "target"]

    # Topology (Moved from Simulation.py global scope)
    connecting_graph: Dict = field(default_factory=lambda: {
        "scada to bus": {
            "intel": "bus to edge",
            "feedback": "bus to edge",
            "target": "bus to edge"
        },
        "edge to bus": {
            "intel": "bus to scada",
            "feedback": "bus to iiot",
            "target": "bus to scada"
        },
        "iiot to bus": {
            "intel": "bus to edge",
            "feedback": "bus to edge",
            "target": "bus to edge"
        }
    })

    ui: bool = False
    print_excel: bool = False