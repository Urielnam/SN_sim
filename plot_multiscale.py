import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

INPUT_FILE = "multiscale_data.csv"


def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    df = pd.read_csv(INPUT_FILE)
    df['Strategy'] = df['Strategy'].str.lower()

    # Legend Mapping
    strat_map = {
        "static": "Baseline (Static)",
        "biological": "Self-Org (Biological)",
        "qos": "QoS",
        "ga": "Genetic Algorithm"
    }
    df['Strategy_Label'] = df['Strategy'].map(strat_map).fillna(df['Strategy'])

    sns.set_theme(style="whitegrid", context="paper", font_scale=1.4)
    plt.figure(figsize=(10, 7))

    # 1. Capacity Threshold
    capacity_val = df["Capacity"].mean()
    plt.axhline(y=capacity_val, color='black', linestyle='--', linewidth=2, label="Theoretical Capacity")

    # 2. Zero Line (Emergence Threshold)
    plt.axhline(y=0, color='red', linestyle='-', linewidth=1.5, alpha=0.5, label="Emergence Threshold ($V<0$)")

    # 3. Main Plot
    sns.lineplot(
        data=df,
        x="Scale_k",
        y="Variety_Vk",
        hue="Strategy_Label",
        style="Strategy_Label",
        markers=True,
        dashes=False,
        linewidth=3,
        palette="viridis"
    )

    plt.title("Recursive Multiscale Profile: $V(k) = V(k-1) - D$", fontsize=16, pad=15)
    plt.xlabel("Scale $k$ (Partition Size)", fontsize=14)
    plt.ylabel("Remaining Variety $V(k)$ (Bits)", fontsize=14)

    # Formatting
    plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
    plt.tight_layout()

    output_path = "paper_plots/fig_phase5_recursive.png"
    if not os.path.exists("paper_plots"): os.makedirs("paper_plots")
    plt.savefig(output_path, dpi=300)
    print(f"Plot Generated: {output_path}")


if __name__ == "__main__":
    main()