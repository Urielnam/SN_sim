import pandas as pd
import os
import glob
import multiprocessing
import Simulation
from sim_config import SimulationConfig
import traceback

# --- CONFIGURATION ---
OUTPUT_DIR = "sim_data/raw_batch"
STRATEGIES = ["static", "qos", "biological", "ga"]

# --- APPEND MODE SETTINGS ---
# This is "X": The number of NEW files to generate per strategy.
# If you have 5 files and set this to 50, you will end up with 55 files.
RUNS_TO_ADD = 99

# SIMULATION SETTINGS
SIM_DURATION = 1000


def get_next_start_index(strategy, output_dir):
    """
    Scans the directory for existing run files for a strategy
    and returns the next available index.
    """
    # Pattern matches: run_biological_*.csv
    pattern = os.path.join(output_dir, f"run_{strategy}_*.csv")
    files = glob.glob(pattern)

    if not files:
        return 0

    indices = []
    prefix = f"run_{strategy}_"

    for f in files:
        try:
            filename = os.path.basename(f)
            # Strip "run_biological_" and ".csv" to get the number
            if filename.startswith(prefix) and filename.endswith(".csv"):
                idx_str = filename[len(prefix):-4]
                indices.append(int(idx_str))
        except ValueError:
            continue

    if not indices:
        return 0

    # Return max index + 1 (e.g., if 04 exists, return 5)
    return max(indices) + 1


def run_single_batch_worker(params):
    """
    Worker function running in a separate process.
    """
    (strategy, run_index, output_dir, duration) = params

    run_id = f"{strategy}_{run_index:02d}"
    save_path = os.path.join(output_dir, f"run_{run_id}.csv")

    # Safety check: ideally the logic in main() prevents this,
    # but we check to avoid accidental overwrites.
    if os.path.exists(save_path):
        return f"Skipped (Collision): {run_id}"

    # 1. Config
    config = SimulationConfig(
        end_time=duration,
        dt=1,
        optimization_method=strategy,
        max_resource=1000,
        ui=False,
        print_excel=False,
        iiot_acc = 0.5,
        self_org_threshold = 5
    )

    try:
        # 2. Run Simulation
        data = Simulation.main_run(config)

        # 3. Extract Snapshots
        raw_snapshots = data.get("state_snapshots", [])

        if not raw_snapshots:
            return f"[WARNING] {run_id}: No snapshots captured."

        # 4. Save Raw Data
        df = pd.DataFrame(raw_snapshots)
        df.to_csv(save_path, index=False)
        return f"Saved: {run_id} ({len(df)} rows)"

    except Exception as e:
        traceback.print_exc()
        return f"[ERROR] {run_id} Failed: {e}"


if __name__ == "__main__":
    # 1. Setup Directory
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print(f"--- Starting Append-Batch Generation ---")
    print(f"Strategies: {STRATEGIES}")
    print(f"Runs to ADD: {RUNS_TO_ADD}")

    # 2. Generate Task List (Dynamic Ranges)
    tasks = []

    for strat in STRATEGIES:
        start_index = get_next_start_index(strat, OUTPUT_DIR)
        end_index = start_index + RUNS_TO_ADD

        print(f"Strategy '{strat}': Existing max index found. Generating indices {start_index} -> {end_index - 1}")

        for i in range(start_index, end_index):
            tasks.append((strat, i, OUTPUT_DIR, SIM_DURATION))

    print(f"Total Jobs Queued: {len(tasks)}")
    print(f"CPUs Available: {multiprocessing.cpu_count()}")
    print("-" * 30)

    # 3. Execute in Parallel
    if tasks:
        with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
            for result in pool.imap_unordered(run_single_batch_worker, tasks):
                print(result)
    else:
        print("No tasks generated. Check logic.")

    print("\n--- Batch Generation Complete ---")