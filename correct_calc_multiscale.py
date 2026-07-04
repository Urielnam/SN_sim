import pandas as pd
import numpy as np
import os
import glob
import itertools
import math
from scipy.stats import entropy

# --- Configuration ---
RAW_DATA_DIR = "sim_data/raw_batch"
OUTPUT_FILE = "aggregated_multiscale_results.csv"

# The full list of potential variables
ALL_VARIABLES = [
    "num_iiots",
    "bus_flow",
    "edge_flow",
    "scada_flow",
    "queue_len",
    "success_rate",
    "avg_latency",
    "feedback_state"
]


def calculate_entropy_bits(df):
    """
    Calculates Shannon Entropy in bits for the unique rows in the dataframe.
    H(X) = - sum(p * log2(p))
    """
    if df.empty:
        return 0.0

    # Count unique occurrences of joint states
    # value_counts(normalize=True) gives probabilities directly
    probs = df.value_counts(normalize=True, sort=False)

    # Calculate entropy with base 2
    return entropy(probs, base=2)


def calculate_Q(data, active_vars, N):
    """
    Equation 1: Q(m) - sum over information in all groups of size m.
    Inputs:
        data: DataFrame containing only the active variables.
        active_vars: List of column names.
        N: Total number of active variables.
    """
    Q = {0: 0.0}
    for m in range(1, N + 1):
        subsets = list(itertools.combinations(active_vars, m))
        q_sum = 0.0
        for S in subsets:
            q_sum += calculate_entropy_bits(data[list(S)])
        Q[m] = q_sum
    return Q


def calculate_D(N, Q):
    """
    Equation 2: D(k) - exact amount of variety from exactly k components together.
    Inputs:
        N: Total number of active variables.
        Q: Dictionary of Q(m) values calculated from Equation 1.
    """
    D = {}
    for k in range(1, N + 1):
        d_val = 0.0
        # j ranges from 0 to k, corresponding to the sigma sum
        for j in range(0, k + 1):
            sign = (-1) ** (k - j + 1)
            binom = math.comb(N - j, k - j)
            # N - j will always be >= 0 because j <= k and k <= N
            term = sign * binom * Q[N - j]
            d_val += term
        D[k] = d_val
    return D


def calculate_V(N, D):
    """
    Equation 3: V(k) - Cumulative variety at scale k.
    Inputs:
        N: Total number of active variables.
        D: Dictionary of D(k) values calculated from Equation 2.
    """
    V = {}
    for k in range(1, N + 1):
        # Sum D(k') from k'=k to N
        v_val = sum(D[k_prime] for k_prime in range(k, N + 1))
        V[k] = v_val
    return V


def process_strategy(strategy_name, file_list):
    """
    Main pipeline to process a specific strategy's batch data and calculate its multiscale variety.

    Ingredients (Inputs):
        - strategy_name (str): Name of the strategy (e.g., 'biological', 'static').
        - file_list (list): List of file paths (CSVs) containing raw simulation snapshots.

    Yields (Output):
        - results (list of dicts): The variety metrics for each scale k, ready for export.
    """
    print(f"\nProcessing Strategy: {strategy_name} ({len(file_list)} files)...")

    # ==========================================
    # STEP 1: Aggregate Raw Data
    # Ingredients: file_list
    # Action: Load all CSVs and concatenate them into a single massive DataFrame (full_df)
    # ==========================================
    df_list = []
    for f in file_list:
        try:
            temp_df = pd.read_csv(f)
            df_list.append(temp_df)
        except Exception as e:
            print(f"  [Warning] Could not read {f}: {e}")

    if not df_list:
        return []

    full_df = pd.concat(df_list, ignore_index=True)

    # ==========================================
    # STEP 2: Filter Variables & Calculate Capacity
    # Ingredients: ALL_VARIABLES (list), full_df (DataFrame)
    # Action: Find columns that actually change. Drop constants and known clones.
    # ==========================================
    active_vars = []
    capacities = []

    for col in ALL_VARIABLES:
        if col in full_df.columns:
            # Count how many unique states this variable actually hit
            unique_vals = full_df[col].nunique()

            # Rule 1: It must actually vary (more than 1 state)
            if unique_vals > 1:
                # Rule 2: Global Exclusion (Edge Flow is a strict clone of Bus Flow in this sim)
                if col == 'edge_flow':
                    continue

                # Rule 3: Static Exclusion (Latency is perfectly correlated to Queue in static mode)
                if strategy_name == 'static' and col == 'avg_latency':
                    continue

                active_vars.append(col)
                capacities.append(np.log2(unique_vals))  # log2(states) = bits of capacity

    N = len(active_vars)
    total_capacity = sum(capacities)
    print(f"  -> Active Variables (N={N}): {active_vars}")
    print(f"  -> Total Capacity: {total_capacity:.4f} bits")

    if N < 2:
        print("  [Skipping] Less than 2 active variables. No interaction possible.")
        return []

    # Isolate the data to just the valid ingredients
    data = full_df[active_vars]

    # ==========================================
    # STEP 3: Multiscale Math Execution
    # Ingredients: data (DataFrame), active_vars (list), N (int)
    # Action: Pass the cleaned data through the three formal emergence equations
    # ==========================================
    Q = calculate_Q(data, active_vars, N)
    D = calculate_D(N, Q)
    V = calculate_V(N, D)

    # ==========================================
    # STEP 4: Detect Emergence & Format Output
    # Ingredients: V (dict of scales), total_capacity (float)
    # Action: Check signatures of emergence and structure the final list of dictionaries
    # ==========================================
    results = []

    # Signature 1: Negative tail (Top-down causation)
    is_emergent = V[N] < 0

    # Signature 2: Oscillation (Synergistic constraints exceed total capacity)
    has_oscillation = any(abs(val) > total_capacity for val in V.values())

    final_emergence_verdict = is_emergent or has_oscillation

    for k in sorted(V.keys()):
        results.append({
            "Strategy": strategy_name,
            "Scale_k": k,
            "Variety_Vk": V[k],
            "Capacity": total_capacity,
            "Is_Emergent": final_emergence_verdict,
            "Active_Variables": str(active_vars),
            "N_Variables": N
        })

    return results


def main():
    all_files = glob.glob(os.path.join(RAW_DATA_DIR, "*.csv"))

    files_by_strategy = {}
    for f in all_files:
        filename = os.path.basename(f)
        parts = filename.split('_')
        if len(parts) >= 2:
            strategy = parts[1]
            if strategy not in files_by_strategy:
                files_by_strategy[strategy] = []
            files_by_strategy[strategy].append(f)

    all_results = []
    for strategy, file_list in files_by_strategy.items():
        results = process_strategy(strategy, file_list)
        all_results.extend(results)

    if all_results:
        output_df = pd.DataFrame(all_results)
        output_df.to_csv(OUTPUT_FILE, index=False)
        print(f"\nCalculation complete. Aggregated results saved to {OUTPUT_FILE}")
    else:
        print("\nNo valid data found to process.")


if __name__ == "__main__":
    main()