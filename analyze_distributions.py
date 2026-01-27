import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import glob
import numpy as np

# Configuration
RAW_DATA_DIR = "sim_data/raw_batch"
OUTPUT_DIR = "distribution_analysis"
VARIABLES = ["num_iiots", "bus_flow", "edge_flow", "scada_flow", "queue_len", "success_rate"]


def load_all_data():
    print("--- Loading Global Ensemble Data ---")
    files = glob.glob(os.path.join(RAW_DATA_DIR, "*.csv"))

    if not files:
        print("No data found!")
        return pd.DataFrame()

    df_list = []
    for f in files:
        try:
            temp_df = pd.read_csv(f)
            # Extract strategy from filename (e.g., run_biological_01.csv)
            strat = os.path.basename(f).split('_')[1]
            temp_df['Strategy'] = strat
            df_list.append(temp_df)
        except Exception:
            pass

    if not df_list:
        return pd.DataFrame()

    full_df = pd.concat(df_list, ignore_index=True)
    print(f"Loaded {len(full_df)} rows across {len(files)} files.")
    return full_df


def suggest_intelligent_bins(df, col):
    """
    Analyzes the column and suggests bins based on:
    1. Zero-inflated logic (if 0 is frequent).
    2. Percentiles (33%, 66%) for the rest.
    """
    series = df[col].dropna()
    if series.empty: return "[]"

    # 1. Check for Zero
    has_zero = (series == 0).any()
    non_zero = series[series > 0]

    suggestions = [-np.inf]

    # 2. Discrete Integer Logic (for low counts like flow rates)
    unique_vals = sorted(series.unique())
    if len(unique_vals) < 15 and (series % 1 == 0).all():
        # If few integers, suggest midway points (e.g. 0.5, 1.5) to capture them perfectly
        for val in unique_vals:
            suggestions.append(val + 0.5)
        # Remove the last one to act as the upper bound or keep inf
        suggestions.pop()
        suggestions.append(np.inf)
        return str(suggestions).replace("inf", "np.inf")

    # 3. Percentile Logic (for continuous or high-range data)
    if not non_zero.empty:
        # We want 3 main states: Low, Med, High
        p33 = np.percentile(non_zero, 33)
        p66 = np.percentile(non_zero, 66)

        if has_zero:
            suggestions.append(0.5)  # Separates 0 from 1

        suggestions.append(round(p33, 2))
        suggestions.append(round(p66, 2))

    suggestions.append(np.inf)
    suggestions = sorted(list(set(suggestions)))

    return str(suggestions).replace("inf", "np.inf")


def generate_individual_plots(df):
    if df.empty: return

    # Create Output Directory
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created directory: {OUTPUT_DIR}")

    sns.set_theme(style="whitegrid", context="talk")  # 'talk' context for bigger fonts

    print("\n--- SUGGESTED BINS (Copy to discretization_config.py) ---")

    for col in VARIABLES:
        if col not in df.columns:
            continue

        plt.figure(figsize=(10, 6))

        # Logic: Log Scale for Queue, Linear for others
        log_scale = False
        plot_data = df.copy()

        if col == "queue_len":
            log_scale = True
            plot_data[col] = plot_data[col] + 1  # Shift for log vis

        # Plot Histogram / KDE
        sns.histplot(
            data=plot_data,
            x=col,
            hue="Strategy",
            element="step",
            stat="density",
            common_norm=False,
            log_scale=log_scale,
            palette="viridis",
            kde=True,  # Add density line for clarity
            alpha=0.3
        )

        plt.title(f"Distribution Analysis: {col}")
        plt.tight_layout()

        # Save Plot
        save_path = os.path.join(OUTPUT_DIR, f"dist_{col}.png")
        plt.savefig(save_path, dpi=300)
        plt.close()  # Free memory

        # Print Suggestion
        suggestion = suggest_intelligent_bins(df, col)
        print(f"'{col}': {suggestion},")

    print(f"\nAnalysis Complete. Plots saved to '{OUTPUT_DIR}/'.")


if __name__ == "__main__":
    df = load_all_data()
    generate_individual_plots(df)