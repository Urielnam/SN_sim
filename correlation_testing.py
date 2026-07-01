import pandas as pd
import numpy as np
import glob
import os
import matplotlib.pyplot as plt
import seaborn as sns

# --- Configuration ---
RAW_DATA_DIR = "sim_data/raw_batch"
OUTPUT_IMG = "correlation_heatmaps_all.png"

# The variables to test
VARIABLES = [
    "num_iiots", "bus_flow", "edge_flow", "scada_flow",
    "queue_len", "success_rate", "avg_latency", "feedback_state"
]


def plot_correlation_matrices():
    # 1. Load and Group Data
    all_files = glob.glob(os.path.join(RAW_DATA_DIR, "*.csv"))
    data_map = {}

    print(f"Found {len(all_files)} files. Loading data...")

    for f in all_files:
        try:
            # Infer strategy from filename (e.g. run_biological_X.csv)
            parts = os.path.basename(f).split('_')
            if len(parts) < 2: continue
            strategy = parts[1]

            df = pd.read_csv(f)

            # Keep only existing columns from our target list
            cols_to_use = [c for c in VARIABLES if c in df.columns]
            if not cols_to_use: continue

            subset = df[cols_to_use]

            if strategy not in data_map:
                data_map[strategy] = subset
            else:
                data_map[strategy] = pd.concat([data_map[strategy], subset], ignore_index=True)

        except Exception as e:
            print(f"Skipping {f}: {e}")

    # 2. Create "Combined" Dataset
    if not data_map:
        print("No valid data found.")
        return

    combined_df = pd.concat(data_map.values(), ignore_index=True)
    data_map['Combined'] = combined_df

    # Sort strategies but keep 'Combined' at the end/beginning
    strategies = sorted([k for k in data_map.keys() if k != 'Combined'])
    plot_order = strategies + ['Combined']

    n_plots = len(plot_order)

    # 3. Setup Plot
    # Adjust width based on number of plots
    fig, axes = plt.subplots(1, n_plots, figsize=(5.5 * n_plots, 6), constrained_layout=True)

    if n_plots == 1: axes = [axes]

    print("\n--- Correlation Highlights ---")

    for i, strat in enumerate(plot_order):
        df = data_map[strat]
        ax = axes[i]

        # Calculate Matrix
        # dropna(how='all') removes constant columns (std=0) which return NaN correlation
        corr_matrix = df.corr(method='pearson')
        corr_matrix = corr_matrix.dropna(axis=0, how='all').dropna(axis=1, how='all')

        # Highlight "Combined" with a different color map or title color
        is_combined = (strat == 'Combined')
        title_color = 'darkred' if is_combined else 'black'
        cmap = "RdBu_r" if is_combined else "coolwarm"

        # Plot Heatmap
        sns.heatmap(
            corr_matrix,
            annot=True,
            fmt=".2f",
            cmap=cmap,
            vmin=-1, vmax=1,
            center=0,
            square=True,
            cbar=False,  # We will add a single shared colorbar if needed, or just individual ones
            ax=ax,
            annot_kws={"size": 9}
        )

        ax.set_title(f"{strat.upper()}", fontsize=14, fontweight='bold', color=title_color)
        ax.tick_params(axis='x', rotation=45, labelsize=9)
        ax.tick_params(axis='y', rotation=0, labelsize=9)

        # Print Strong Links
        print(f"\n[{strat.upper()}] Strongest Links (>0.9):")
        upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        strong_links = upper.unstack().dropna()
        strong_links = strong_links[abs(strong_links) > 0.9]

        if not strong_links.empty:
            for idx, val in strong_links.items():
                print(f"  - {idx[0]} <-> {idx[1]}: {val:.4f}")
        else:
            print("  (None found)")

    # 4. Save (No plt.show)
    print(f"\nSaving plot to {OUTPUT_IMG}...")
    plt.savefig(OUTPUT_IMG, dpi=150)
    plt.close()  # Close memory
    print("Done.")


if __name__ == "__main__":
    plot_correlation_matrices()