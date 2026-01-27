import pandas as pd
import numpy as np
import os
import glob
import itertools
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


def process_strategy(strategy_name, file_list):
    print(f"\nProcessing Strategy: {strategy_name} ({len(file_list)} files)...")

    # 1. Aggregate all runs into one Dataframe
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

    # 2. Filter Variables (Remove constants to prevent "ghost redundancy")
    # We only keep variables that have more than 1 unique value in the dataset.
    active_vars = []
    capacities = []

    for col in ALL_VARIABLES:
        if col in full_df.columns:
            # Get raw unique values (No binning!)
            unique_vals = full_df[col].nunique()

            if unique_vals > 1:
                active_vars.append(col)
                # Capacity = log2(Number of observed states)
                # Note: If you want theoretical limits (e.g. max possible queue),
                # hardcode them. Otherwise, this uses observed capacity.
                capacities.append(np.log2(unique_vals))
            else:
                print(f"  - Excluding constant variable: {col} (Unique values: {unique_vals})")

    N = len(active_vars)
    total_capacity = sum(capacities)
    print(f"  -> Active Variables (N={N}): {active_vars}")
    print(f"  -> Total Capacity: {total_capacity:.4f} bits")

    # If fewer than 2 variables vary, we cannot calculate multiscale interactions
    if N < 2:
        print("  [Skipping] Less than 2 active variables. No interaction possible.")
        return []

    # 3. Reduce DataFrame to only active columns to speed up entropy calc
    data = full_df[active_vars]

    # --- Multiscale Calculation (Step-by-Step according to formal method) ---
    v_curve = {}

    # Step 1: Initialization (Scale 1)
    # V(1) = Total Joint Entropy H(X1, ..., XN)
    v1 = calculate_entropy_bits(data)
    v_curve[1] = v1

    # Step 2: Recursive Stripping (Intermediate Scales k=2 to N-1)
    # V(k) = V(k-1) - D(k-1)
    # D(k-1) = Sum over subsets S of size (k-1) of [H(X) - H(X \ S)]

    current_v = v1

    # Loop from scale k=2 up to N-1
    # We stop before N because V(N) is calculated via the Sum Rule
    for k in range(2, N):
        subset_size = k - 1

        # Generate all combinations of variables of size (k-1)
        subsets = list(itertools.combinations(active_vars, subset_size))

        d_total_at_scale = 0

        for S in subsets:
            # Identify the Complement (Rest of the system)
            # Rest = X \ S
            rest_vars = [v for v in active_vars if v not in S]

            # H(Rest)
            h_rest = calculate_entropy_bits(data[rest_vars])

            # Independent Info Contribution = H(Total) - H(Rest)
            # Logic: If I remove S, how much info do I lose?
            info_gain = v1 - h_rest
            d_total_at_scale += info_gain

        # Update V(k)
        next_v = current_v - d_total_at_scale
        v_curve[k] = next_v
        current_v = next_v

    # Step 3: Global Correction (Scale N)
    # Sum Rule: Sum(V(k)) must equal Total Capacity
    # V(N) = Capacity - Sum(V(1)...V(N-1))

    sum_prev_v = sum(v_curve.values())
    v_curve[N] = total_capacity - sum_prev_v

    # Format Results
    results = []
    is_emergent = v_curve[N] < 0  # Check criterion B (Negative tail)

    # Also check criterion A (Oscillation)
    # |V(k)| > Capacity for some k
    has_oscillation = any(abs(val) > total_capacity for val in v_curve.values())

    final_emergence_verdict = is_emergent or has_oscillation

    for k in sorted(v_curve.keys()):
        results.append({
            "Strategy": strategy_name,
            "Scale_k": k,
            "Variety_Vk": v_curve[k],
            "Capacity": total_capacity,
            "Is_Emergent": final_emergence_verdict,
            "Active_Variables": str(active_vars),
            "N_Variables": N
        })

    return results


def main():
    # Find all CSV files
    all_files = glob.glob(os.path.join(RAW_DATA_DIR, "*.csv"))

    # Group files by strategy
    # Assuming filename format like: "run_static_41.csv" -> strategy is "static"
    files_by_strategy = {}

    for f in all_files:
        filename = os.path.basename(f)
        parts = filename.split('_')
        if len(parts) >= 2:
            strategy = parts[1]  # "static", "biological", etc.
            if strategy not in files_by_strategy:
                files_by_strategy[strategy] = []
            files_by_strategy[strategy].append(f)

    all_results = []

    for strategy, file_list in files_by_strategy.items():
        results = process_strategy(strategy, file_list)
        all_results.extend(results)

    # Save to CSV
    if all_results:
        output_df = pd.DataFrame(all_results)
        output_df.to_csv(OUTPUT_FILE, index=False)
        print(f"\nCalculation complete. Aggregated results saved to {OUTPUT_FILE}")
    else:
        print("\nNo valid data found to process.")


if __name__ == "__main__":
    main()