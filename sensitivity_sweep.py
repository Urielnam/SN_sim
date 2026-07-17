import pandas as pd
import multiprocessing
import itertools
from sim_config import SimulationConfig
import Simulation
import time
from datetime import timedelta, datetime
import traceback
import os

# --- CONFIGURATION FOR MEGA SWEEP ---

# Define the matrix topologies you want to test
FULLY_OBSERVABLE = {
    "name": "full_vis",
    "p2p": [[1, 1, 1, 1] for _ in range(4)],
    "s2p": [[1, 1, 1] for _ in range(4)]
}

ISOLATED_AGENTS = {
    "name": "isolated",
    "p2p": [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ],
    "s2p": [
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
        [0, 0, 0]
    ]
}

SWEEP_CONFIG = {

    # 1. Physics Parameters
    "dt": [1],  # Granularity of decision making
    #0.1,0.3,0.5,0.7,0.9
    "iiot_acc": [0.5],  # Sensor quality
    # 100, 500,1000,1500,2000
    "max_resource": [100],  # Budget constraint
    "self_org_threshold": [5],  # Volatility tolerance (Bio only)

    # 2. Strategies to Compare
    # "optimization_method": ["static", "pure_fundamental", "pure_biological", "biological", "pure_qos", "qos", "ga",
    # "pure_qos_bio", "qos_bio", "pure_ga", "ga", "rl", "masked_random"],
    "optimization_method": ["masked_random"],

    # 3. Information Topologies
    "topology": [FULLY_OBSERVABLE, ISOLATED_AGENTS],

    # 4. Statistical Rigor
    "iterations_per_combo": 1  # Keep low (3-5) for mega sweeps, or it will run for days
}


def run_single_worker(params):
    """
    Unpacks parameters and runs one simulation.
    """
    # Unpack the tuple from itertools
    (dt, acc, res, thresh, strat, topology, run_id, traces_dir) = params

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
        "self_org_threshold": thresh,
        "p2p_matrix": topology["p2p"],
        "s2p_matrix": topology["s2p"]
    }

    # --- START TIMER ---
    start_time = time.time()



    # Run Simulation
    # We catch errors to prevent one crash from killing the whole sweep
    try:
        data = Simulation.main_run(config, overrides)

        # Save Timeline Trace to Parquet directly from the worker
        # Create a deterministic, collision-proof filename using the parameter space
        trace_file = os.path.join(traces_dir, f"run_{strat}_{topology['name']}_res{res}_acc{acc}_th{thresh}_id{run_id}.parquet")
        if "state_snapshots" in data and data["state_snapshots"]:
            df_trace = pd.DataFrame(data["state_snapshots"])
            # Inject Metadata for downstream plotting
            df_trace["Strategy"] = strat
            df_trace["Topology"] = topology["name"]
            df_trace["Run_ID"] = run_id
            df_trace["Max_Resource"] = res
            df_trace["Sensor_Acc"] = acc
            df_trace.to_parquet(trace_file, index=False)

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

    # Setup unique run directories using existing BackendClasses method
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_dir = os.path.join("results", "raw_data", now)
    traces_dir = os.path.join(base_dir, "traces")
    os.makedirs(traces_dir, exist_ok=True)

    master_csv = os.path.join(base_dir, "master_summary.csv")

    # Initialize empty master CSV with headers
    headers = ["Strategy", "Topology", "DT", "Sensor_Acc", "Max_Res", "Threshold", "Run_ID", "Final_Success", "Final_Cost",
               "Avg_Latency", "Execution_Time_Sec", "Avg_Self_Org"]
    pd.DataFrame(columns=headers).to_csv(master_csv, index=False)

    # Create all combinations using Cartesian Product
    keys = ["dt", "iiot_acc", "max_resource", "self_org_threshold", "optimization_method", "topology"]
    values = [SWEEP_CONFIG[k] for k in keys]

    # Add iteration count to the combinations
    combinations = list(itertools.product(*values, range(SWEEP_CONFIG["iterations_per_combo"])))

    filtered_combinations = []
    seen_non_bio = set()

    for combo in combinations:
        (dt, acc, res, thresh, strat, topology, run_id) = combo

        # Inject traces_dir into the task parameters
        task_params = (dt, acc, res, thresh, strat, topology, run_id, traces_dir)

        if strat in ["biological","qos_bio"]:
            filtered_combinations.append(task_params)
        else:
            # For non-bio, only run if thresh is the first value in the list
            # (Assuming the first value is the "default" for comparisons)
            if thresh == SWEEP_CONFIG["self_org_threshold"][0]:
                filtered_combinations.append(task_params)

    print(f"Total Simulations to Run: {len(filtered_combinations)}")
    per_sim = 14.5
    total_seconds = per_sim * len(filtered_combinations) / 8
    time_delta = timedelta(seconds=int(total_seconds))
    print(f"Estimated Time (at {per_sim} sec/sim on 8 cores): {time_delta}")

    # Execute in Parallel
    # old unlimited line:  "with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:"
    with multiprocessing.Pool(processes=2) as pool:
        # Use imap_unordered for better progress tracking if you wanted to add tqdm later
        for result in pool.imap_unordered(run_single_worker, filtered_combinations):
            # Append single row to master CSV immediately (avoids race conditions)
            pd.DataFrame([result]).to_csv(master_csv, mode='a', header=False, index=False)
            print(f"Finished: {result['Strategy']} | Run_ID: {result['Run_ID']} | Success: {result['Final_Success']}")

    print(f"\n--- Mega Sweep Complete. Master summary saved to {master_csv} ---")

    # Reload the master CSV for the final printouts
    final_df = pd.read_csv(master_csv)
    print(final_df.groupby(["Strategy"]).mean(numeric_only=True)[["Final_Success", "Final_Cost"]])
    print(f"Average Sim Time: {final_df['Execution_Time_Sec'].mean():.4f} seconds")

