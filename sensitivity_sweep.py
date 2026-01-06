import pandas as pd
import multiprocessing
import itertools
from sim_config import SimulationConfig
import Simulation

# --- CONFIGURATION FOR MEGA SWEEP ---

SWEEP_CONFIG = {

    # 1. Physics Parameters
    "dt": [1, 5, 10],  # Granularity of decision making
    "iiot_acc": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],  # Sensor quality
    "max_resource": [50, 100, 150, 500, 1000],  # Budget constraint
    "self_org_threshold": [25, 35, 45, 100, 500, 1000],  # Volatility tolerance (Bio/GA only)

    # 2. Strategies to Compare
    "optimization_method": ["biological", "qos", "ga"],

    # 3. Statistical Rigor
    "iterations_per_combo": 5  # Keep low (3-5) for mega sweeps, or it will run for days
}


def run_single_worker(params):
    """
    Unpacks parameters and runs one simulation.
    """
    # Unpack the tuple from itertools
    (dt, acc, res, thresh, strat, run_id) = params

    # Base Config
    config = SimulationConfig(
        end_time=800,  # Slightly shorter for speed
        ui=False,
        print_excel=False,
        optimization_method=strat
    )

    # Overrides
    overrides = {
        "dt": dt,
        "iiot_acc": acc,
        "max_resource": res,
        "self_org_threshold": thresh
    }

    # Run Simulation
    # We catch errors to prevent one crash from killing the whole sweep
    try:
        data = Simulation.main_run(config, overrides)
        success = data["final_success_count"]
        cost = data["final_resource_cost"]

        # Calculate Average Data Age (Latency)
        # We need to extract the individual floats.
        all_ages = []
        for time_entry in data["data_age"].values():
            for packet_batch in time_entry:
                # packet_batch is a list of floats (e.g., [1.5, 2.3])
                all_ages.extend(packet_batch)

        avg_latency = sum(all_ages) / len(all_ages) if all_ages else 0
    except Exception as e:
        print(f"Run Failed: {params} | Error: {e}")
        success = 0
        cost = 0

    return {
        "Strategy": strat,
        "DT": dt,
        "Sensor_Acc": acc,
        "Max_Res": res,
        "Threshold": thresh,
        "Run_ID": run_id,
        "Final_Success": success,
        "Final_Cost": cost,
        "Avg_Latency": round(avg_latency, 2)
    }


if __name__ == "__main__":
    print("Generating Task List...")

    # Create all combinations using Cartesian Product
    keys = ["dt", "iiot_acc", "max_resource", "self_org_threshold", "optimization_method"]
    values = [SWEEP_CONFIG[k] for k in keys]

    # Add iteration count to the combinations
    combinations = list(itertools.product(*values, range(SWEEP_CONFIG["iterations_per_combo"])))

    print(f"Total Simulations to Run: {len(combinations)}")
    print(f"Estimated Time (at 1 sec/sim on 8 cores): {len(combinations) / 8 / 60:.2f} minutes")

    # Execute in Parallel
    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        # Use imap_unordered for better progress tracking if you wanted to add tqdm later
        results = pool.map(run_single_worker, combinations)

    # Save
    df = pd.DataFrame(results)
    filename = "mega_sweep_results.csv"
    df.to_csv(filename, index=False)

    print(f"\n--- Mega Sweep Complete. Saved to {filename} ---")
    print(df.groupby(["Strategy"]).mean(numeric_only=True)[["Final_Success", "Final_Cost"]])