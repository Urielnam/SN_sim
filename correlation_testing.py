import pandas as pd
import numpy as np
import glob
import os
import matplotlib.pyplot as plt
from scipy.stats import pearsonr

# Configuration
RAW_DATA_DIR = "sim_data/raw_batch"
OUTPUT_IMG = "correlation_analysis.png"


def analyze_correlations():
    # 1. Load Data
    all_files = glob.glob(os.path.join(RAW_DATA_DIR, "*.csv"))
    data_map = {}  # { 'static': DataFrame, 'biological': DataFrame ... }

    print(f"Found {len(all_files)} files.")

    for f in all_files:
        try:
            # Extract strategy name from filename (e.g., run_static_41.csv -> static)
            strategy = os.path.basename(f).split('_')[1]

            df = pd.read_csv(f)

            # Select only relevant columns
            if 'queue_len' in df.columns and 'avg_latency' in df.columns:
                subset = df[['queue_len', 'avg_latency']].copy()

                # Append to the strategy's massive dataframe
                if strategy not in data_map:
                    data_map[strategy] = subset
                else:
                    data_map[strategy] = pd.concat([data_map[strategy], subset], ignore_index=True)
        except Exception as e:
            print(f"Skipping {f}: {e}")

    # 2. Calculate & Plot
    strategies = sorted(data_map.keys())
    fig, axes = plt.subplots(1, len(strategies), figsize=(5 * len(strategies), 5), sharey=True)

    # Handle case of single strategy (axes is not a list)
    if len(strategies) == 1: axes = [axes]

    print("\n--- Correlation Results ---")

    for i, strat in enumerate(strategies):
        df = data_map[strat]
        ax = axes[i]

        # Drop NaNs or infinite values
        df = df.replace([np.inf, -np.inf], np.nan).dropna()

        # Add slight jitter to seeing overlapping points (optional)
        jitter_x = df['queue_len'] + np.random.normal(0, 0.1, size=len(df))
        jitter_y = df['avg_latency'] + np.random.normal(0, 0.1, size=len(df))

        # Scatter Plot
        ax.scatter(jitter_x, jitter_y, alpha=0.1, s=10, c='blue')

        # Calculate Pearson Correlation
        if len(df) > 2 and df['avg_latency'].std() > 0:
            corr, _ = pearsonr(df['queue_len'], df['avg_latency'])
        else:
            corr = 0.0  # Constant values have 0 correlation by definition

        title = f"{strat.upper()}\nCorr: {corr:.4f}"
        print(f"{strat}: Pearson r = {corr:.4f}")

        # Aesthetics
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_xlabel("Queue Length")
        if i == 0: ax.set_ylabel("Avg Latency")
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(OUTPUT_IMG)
    print(f"\nPlot saved to {OUTPUT_IMG}")
    plt.show()


if __name__ == "__main__":
    analyze_correlations()