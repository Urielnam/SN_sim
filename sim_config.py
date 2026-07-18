# sim_config.py
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class SimulationConfig:
    # Simulation Control
    end_time: int = 1000
    dt: float = 5
    max_resource: int = 100
    sampling_interval: float = 0.1



    # Physics/Logic
    iiot_acc: float = 0.1
    self_org_threshold: float = 35

    # Optimization Strategy Selector
    optimization_method: str = "biological"

    p2p_matrix: list = None
    s2p_matrix: list = None

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

    # ==========================================
    # Machine Learning Configuration
    # ==========================================

    # Frame Stacking (Memory): How many past observations the agent sees at once.
    # Solves Partial Observability by giving agents a sense of velocity/time.
    frame_stack_size: int = 4

    # The Stride: How often (in ticks) the neural network runs backpropagation.
    # Set to 10 to cut CPU overhead by 90% while allowing rapid adaptation.
    training_stride: int = 10

    # Rolling Window Cap: The maximum T window for the Multiscale Variety calculation.
    max_history_window: int = 100

    # Alpha Penalty: The tuning coefficient for the Requisite Variety Loss (J).
    # Balances physical task success against structural complexity matching.
    alpha_penalty: float = 0.5

    # Standard RL Hyperparameters
    learning_rate: float = 1e-3
    gamma_discount: float = 0.99  # Discount factor for future rewards