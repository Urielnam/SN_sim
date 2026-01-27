import pandas as pd
import numpy as np
import os
import glob
from scipy.stats import entropy
import itertools
import discretization_config as dc

RAW_DATA_DIR = "sim_data/raw_batch"
OUTPUT_FILE = "multiscale_data.csv"

# The 6 Variables (N=6)
VARIABLES = ["num_iiots", "bus_flow", "edge_flow", "scada_flow", "queue_len", "success_rate"]
N = len(VARIABLES)


def calculate_shannon_entropy(series):
    """H(X) in bits."""
    if len(series) == 0: return 0
    probs = series.value_counts(normalize=True, sort=False)
    return entropy(probs, base=2)


def get_subset_entropy(df, variables):
    """Calculates H(S) for a specific subset of variables."""
    if not variables: return 0
    subset_df = df[variables].copy()
    joint_state = subset_df.apply(tuple, axis=1)
    return calculate_shannon_entropy(joint_state)


def analyze_run_recursive(file_path):
    df = pd.read_csv(file_path)

    # 1. Discretize
    disc_df = pd.DataFrame()
    capacity_bits = 0

    for col in VARIABLES:
        if col in df.columns:
            bins = dc.DISCRETE_BINS[col]
            # Use 'labels=False' to get integers
            disc_df[col] = pd.cut(df[col], bins=bins, labels=False, include_lowest=True)
            capacity_bits += np.log2(dc.CAPACITIES[col])
        else:
            # If column missing, assume single state (0 entropy, 0 capacity contribution if not in config)
            pass

    available_vars = [v for v in VARIABLES if v in disc_df.columns]
    curr_N = len(available_vars)

    # 2. Recursive Independence Subtraction
    # V(0) = Theoretical Capacity
    # V(k) = V(k-1) - Average_Independence(k)

    v_curve = {}
    v_current = capacity_bits

    # Store V(0)
    v_curve[0] = v_current

    # H(Total) is constant for the dataset
    h_total = get_subset_entropy(disc_df, available_vars)

    for k in range(1, curr_N):
        # Find all bipartitions of size k vs (N-k)
        subsets = list(itertools.combinations(available_vars, k))
        independences = []

        for subset in subsets:
            S = list(subset)
            S_bar = [x for x in available_vars if x not in S]

            h_s = get_subset_entropy(disc_df, S)
            h_s_bar = get_subset_entropy(disc_df, S_bar)

            # D = H(S) + H(S_bar) - H(Total)
            # This measures how much info is lost by splitting the system here
            d = h_s + h_s_bar - h_total
            independences.append(d)

        avg_independence = np.mean(independences)

        # Apply Subtraction
        v_current = v_current - avg_independence
        v_curve[k] = v_current

    # Final Step (k=N)
    # Usually we define V(N) based on the trend or specific metric.
    # Let's keep it consistent.
    v_curve[curr_N] = v_current

    strategy = os.path.basename(file_path).split('_')[1]
    return strategy, v_curve, capacity_bits


def main():
    print("--- Calculating Recursive Multiscale Variety V(k) ---")
    all_files = glob.glob(os.path.join(RAW_DATA_DIR, "*.csv"))

    rows = []

    for f in all_files:
        try:
            strat, profile, cap = analyze_run_recursive(f)

            for k, val in profile.items():
                rows.append({
                    "Strategy": strat,
                    "Scale_k": k,
                    "Variety_Vk": val,
                    "Capacity": cap,
                    "Run": os.path.basename(f)
                })
        except Exception as e:
            print(f"Skipping {f}: {e}")

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Done. Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()