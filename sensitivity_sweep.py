import pandas as pd
import multiprocessing
import itertools
from sim_config import SimulationConfig
import Simulation
import time
from datetime import timedelta
import traceback

# --- CONFIGURATION FOR MEGA SWEEP ---

SWEEP_CONFIG = {

    # 1. Physics Parameters
    "dt": [1],  # Granularity of decision making
    "iiot_acc": [0.1,0.3,0.5,0.7,0.9],  # Sensor quality
    # 100, 500,1000,1500,
    "max_resource": [2000],  # Budget constraint
    "self_org_threshold": [5],  # Volatility tolerance (Bio only)

    # 2. Strategies to Compare
    # "optimization_method": ["biological", "qos", "ga","fundamental", "qos_bio"],
    "optimization_method": ["qos_bio"],

    # 3. Statistical Rigor
    "iterations_per_combo": 30  # Keep low (3-5) for mega sweeps, or it will run for days
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

    # --- START TIMER ---
    start_time = time.time()



    # Run Simulation
    # We catch errors to prevent one crash from killing the whole sweep
    try:
        data = Simulation.main_run(config, overrides)
        success = data["final_success_count"]
        cost = data["final_resource_cost"]

        # Calculate the average volatility (Self-Org Measure) over the run
        self_org_values = list(data["self_organization_measure"].values())
        max_self_org = max(self_org_values) if self_org_values else 0

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
        max_self_org = 0  # Default on fail
        avg_latency = 0

    # --- END TIMER ---
    end_time = time.time()
    duration = end_time - start_time

    return {
        "Strategy": strat,
        "DT": dt,
        "Sensor_Acc": acc,
        "Max_Res": res,
        "Threshold": thresh,
        "Run_ID": run_id,
        "Final_Success": success,
        "Final_Cost": cost,
        "Avg_Latency": round(avg_latency, 2),
        "Execution_Time_Sec": round(duration, 4),
        "Avg_Self_Org": round(max_self_org, 2)
    }


if __name__ == "__main__":
    print("Generating Task List...")

    # Create all combinations using Cartesian Product
    keys = ["dt", "iiot_acc", "max_resource", "self_org_threshold", "optimization_method"]
    values = [SWEEP_CONFIG[k] for k in keys]

    # Add iteration count to the combinations
    combinations = list(itertools.product(*values, range(SWEEP_CONFIG["iterations_per_combo"])))

    filtered_combinations = []
    seen_non_bio = set()

    for combo in combinations:
        (dt, acc, res, thresh, strat, run_id) = combo

        if strat in ["biological","qos_bio"]:
            filtered_combinations.append(combo)
        else:
            # For non-bio, only run if thresh is the first value in the list
            # (Assuming the first value is the "default" for comparisons)
            if thresh == SWEEP_CONFIG["self_org_threshold"][0]:
                filtered_combinations.append(combo)

    print(f"Total Simulations to Run: {len(filtered_combinations)}")
    per_sim = 14.5
    total_seconds = per_sim * len(filtered_combinations) / 8
    time_delta = timedelta(seconds=int(total_seconds))
    print(f"Estimated Time (at {per_sim} sec/sim on 8 cores): {time_delta}")

    # Execute in Parallel
    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        # Use imap_unordered for better progress tracking if you wanted to add tqdm later
        results = pool.map(run_single_worker, filtered_combinations)

    # Save
    df = pd.DataFrame(results)
    filename = "mega_sweep_results.csv"
    df.to_csv(filename, index=False)

    print(f"\n--- Mega Sweep Complete. Saved to {filename} ---")
    print(df.groupby(["Strategy"]).mean(numeric_only=True)[["Final_Success", "Final_Cost"]])
    print(f"Average Sim Time: {df['Execution_Time_Sec'].mean():.4f} seconds")