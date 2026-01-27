import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import glob
import numpy as np
import sys

# Try to import your config
try:
    import discretization_config as dc
except ImportError:
    print("Error: 'discretization_config.py' not found. Run optimize_bins.py first.")
    sys.exit(1)

# Configuration
RAW_DATA_DIR = "sim_data/raw_batch"
OUTPUT_DIR = "bin_verification"


def load_data():
    print("--- Loading Global Ensemble Data ---")
    files = glob.glob(os.path.join(RAW_DATA_DIR, "*.csv"))
    if not files: return pd.DataFrame()

    df_list = []
    for f in files:
        try:
            temp_df = pd.read_csv(f)
            strat = os.path.basename(f).split('_')[1]
            temp_df['Strategy'] = strat
            df_list.append(temp_df)
        except Exception:
            pass

    if not df_list: return pd.DataFrame()
    return pd.concat(df_list, ignore_index=True)


def plot_bin_overlay(df):
    if df.empty: return

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    sns.set_theme(style="whitegrid", context="talk")

    print(f"\n--- Generating Verification Plots in '{OUTPUT_DIR}/' ---")

    # Iterate through the variables defined in your config
    for col, bins in dc.DISCRETE_BINS.items():
        if col not in df.columns:
            continue

        print(f"Plotting {col}...", end=" ", flush=True)

        plt.figure(figsize=(12, 7))

        # 1. Plot Data Distribution
        # Use log scale for queue_len to see the bins better
        log_scale = (col == "queue_len")
        plot_data = df.copy()
        if log_scale:
            plot_data[col] = plot_data[col] + 1

        sns.histplot(
            data=plot_data,
            x=col,
            hue="Strategy",
            element="step",
            stat="density",
            common_norm=False,
            palette="viridis",
            log_scale=log_scale,
            alpha=0.25
        )

        # 2. Overlay Bin Edges
        # Filter out -inf and inf for plotting
        valid_edges = [b for b in bins if b != -np.inf and b != np.inf and not np.isnan(b)]

        for i, edge in enumerate(valid_edges):
            # Adjust edge for log plot if necessary
            plot_edge = edge
            if log_scale:
                plot_edge = edge + 1

            plt.axvline(x=plot_edge, color='red', linestyle='--', linewidth=2, alpha=0.9)

            # Label the edge value
            plt.text(plot_edge, plt.gca().get_ylim()[1] * 0.95, f"{edge:.1f}",
                     color='red', ha='center', fontsize=10, backgroundcolor='white')

        plt.title(f"Bin Verification: {col}\n(Red Lines = Configured Edges)")
        plt.tight_layout()

        save_path = os.path.join(OUTPUT_DIR, f"verify_{col}.png")
        plt.savefig(save_path, dpi=150)
        plt.close()
        print("Done.")

    print(f"\nVerification Complete. Open the '{OUTPUT_DIR}' folder.")


if __name__ == "__main__":
    df = load_data()
    plot_bin_overlay(df)