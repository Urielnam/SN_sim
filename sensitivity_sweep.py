import pandas as pd
import multiprocessing
from sim_config import SimulationConfig
import Simulation

# CONFIGURATION FOR SWEEP
SWEEP_CONFIG = {
    "iterations_per_combo": 5,  # Statistical significance
    "resource_limits": [50, 100, 150],
    "sensor_accuracies": [0.7, 0.8, 0.9],
    "strategies": ["biological", "qos"]  # Compare Bio vs Baseline
}


def run_single_worker(params):
    """
    Worker function for multiprocessing.
    """
    res_limit, acc, strat, run_id = params

    # Base Config
    config = SimulationConfig(
        end_time=500,  # Shorter runs for sweep
        ui=False,
        print_excel=False,
        optimization_method=strat
    )

    # Overrides
    overrides = {
        "max_resource": res_limit,
        "iiot_acc": acc
    }

    # Run Simulation
    print(f"Running: Strat={strat}, Res={res_limit}, Acc={acc}, Run={run_id}")
    data = Simulation.main_run(config, overrides)

    return {
        "Strategy": strat,
        "Resource_Limit": res_limit,
        "Sensor_Accuracy": acc,
        "Run_ID": run_id,
        "Final_Success": data["final_success_count"],
        "Final_Cost": data["final_resource_cost"]
    }


if __name__ == "__main__":
    tasks = []

    # Generate Task List
    for strat in SWEEP_CONFIG["strategies"]:
        for res in SWEEP_CONFIG["resource_limits"]:
            for acc in SWEEP_CONFIG["sensor_accuracies"]:
                for i in range(SWEEP_CONFIG["iterations_per_combo"]):
                    tasks.append((res, acc, strat, i))

    print(f"Starting Sensitivity Sweep: {len(tasks)} total runs...")

    # Execute in Parallel
    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        results = pool.map(run_single_worker, tasks)

    # Aggregate and Save
    df = pd.DataFrame(results)
    df.to_csv("sensitivity_results.csv", index=False)

    print("\n--- Sweep Complete ---")
    print("Results saved to sensitivity_results.csv")
    print(df.groupby(["Strategy", "Resource_Limit", "Sensor_Accuracy"]).mean())