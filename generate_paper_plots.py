import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import sys

# Define the output file name from your sweep script
# (Check if your sensitivity_sweep.py outputs 'mega_sweep_results.csv' or 'sensitivity_results.csv')
INPUT_FILE = "mega_sweep_results.csv"


def set_style():
    sns.set_theme(style="whitegrid")
    sns.set_context("paper", font_scale=1.4)


def plot_heatmap_bio_vs_ga(df):
    """
    Fig 5: Biological vs GA.
    Heatmap showing % Improvement of Bio over Genetic Algorithm.
    """
    # 1. Aggregate
    means = df.groupby(["Strategy", "Max_Res", "Sensor_Acc"])["Final_Success"].mean().reset_index()

    # 2. Pivot for easier math
    # We expect columns: 'biological', 'ga'
    pivoted = means.pivot(index=["Max_Res", "Sensor_Acc"], columns="Strategy", values="Final_Success").reset_index()

    if 'biological' not in pivoted.columns or 'ga' not in pivoted.columns:
        print("Skipping Bio vs GA Heatmap: Missing 'biological' or 'ga' data.")
        return

    # 3. Calculate Improvement
    pivoted["Improvement"] = ((pivoted["biological"] - pivoted["ga"]) / pivoted["ga"]) * 100

    # 4. Pivot for Heatmap
    heatmap_data = pivoted.pivot(index="Sensor_Acc", columns="Max_Res", values="Improvement")

    plt.figure(figsize=(8, 6))
    sns.heatmap(heatmap_data, annot=True, fmt=".1f", cmap="RdBu_r", center=0,
                cbar_kws={'label': '% Improvement over GA'})

    plt.title("Bio Gain over GA (%)")
    plt.ylabel("Sensor Accuracy")
    plt.xlabel("Resource Limit")

    plt.tight_layout()
    plt.savefig("paper_plots/fig5_bio_vs_ga.png", dpi=300)
    print("Saved fig5_bio_vs_ga.png")


def plot_heatmap_qos_vs_ga(df):
    """
    Fig 6: QoS vs GA.
    Heatmap showing % Improvement of QoS over Genetic Algorithm.
    """
    means = df.groupby(["Strategy", "Max_Res", "Sensor_Acc"])["Final_Success"].mean().reset_index()
    pivoted = means.pivot(index=["Max_Res", "Sensor_Acc"], columns="Strategy", values="Final_Success").reset_index()

    # Check for 'ga' and 'qos' (case sensitive, assuming lowercase based on your snippet)
    if 'qos' not in pivoted.columns or 'ga' not in pivoted.columns:
        print("Skipping QoS vs GA Heatmap: Missing 'qos' or 'ga' data.")
        return

    # Improvement of QoS relative to GA
    pivoted["Improvement"] = ((pivoted["qos"] - pivoted["ga"]) / pivoted["ga"]) * 100

    heatmap_data = pivoted.pivot(index="Sensor_Acc", columns="Max_Res", values="Improvement")

    plt.figure(figsize=(8, 6))
    sns.heatmap(heatmap_data, annot=True, fmt=".1f", cmap="RdBu_r", center=0,
                cbar_kws={'label': '% Improvement over GA'})

    plt.title("QoS Gain over GA (%)")
    plt.ylabel("Sensor Accuracy")
    plt.xlabel("Resource Limit")

    plt.tight_layout()
    plt.savefig("paper_plots/fig6_qos_vs_ga.png", dpi=300)
    print("Saved fig6_qos_vs_ga.png")


def plot_heatmap_bio_vs_best(df):
    """
    Fig 7: Biological vs Best Baseline.
    Heatmap showing % Improvement of Bio over the BEST of (GA, QoS).
    This is the 'money plot' proving Bio beats the strongest alternative in every condition.
    """
    means = df.groupby(["Strategy", "Max_Res", "Sensor_Acc"])["Final_Success"].mean().reset_index()
    pivoted = means.pivot(index=["Max_Res", "Sensor_Acc"], columns="Strategy", values="Final_Success").reset_index()

    needed = ['biological', 'qos', 'ga']
    if not all(col in pivoted.columns for col in needed):
        print(f"Skipping Bio vs Best Heatmap: Data must contain all of {needed}")
        return

    # 1. Determine the best baseline for each condition (cell)
    pivoted["Best_Baseline"] = pivoted[["qos", "ga"]].max(axis=1)

    # 2. Calculate improvement over that best baseline
    pivoted["Improvement"] = ((pivoted["biological"] - pivoted["Best_Baseline"]) / pivoted["Best_Baseline"]) * 100

    # 3. Pivot for Heatmap
    heatmap_data = pivoted.pivot(index="Sensor_Acc", columns="Max_Res", values="Improvement")

    plt.figure(figsize=(8, 6))
    # Using 'Greens' or 'RdYlGn' helps highlight positive gains clearly
    sns.heatmap(heatmap_data, annot=True, fmt=".1f", cmap="RdYlGn", center=0, cbar_kws={'label': '% Improvement'})

    plt.title("Bio Gain over Best Baseline (GA/QoS) (%)")
    plt.ylabel("Sensor Accuracy")
    plt.xlabel("Resource Limit")

    plt.tight_layout()
    plt.savefig("paper_plots/fig7_bio_vs_best.png", dpi=300)
    print("Saved fig7_bio_vs_best.png")

def plot_success_vs_resource(df):
    """
    Fig 1: The Main Result.
    Does the Biological Strategy beat the Baseline at different resource caps?
    """
    plt.figure(figsize=(10, 6))

    # We filter for a "standard" scenario (e.g., standard sensor accuracy)
    # to make the comparison fair and clear, or aggregate all.
    # Here we aggregate to show general robustness.
    ax = sns.barplot(
        data=df,
        x="Max_Res",
        y="Final_Success",
        hue="Strategy",
        palette="viridis",
        errorbar=('ci', 95),  # 95% Confidence Interval
        capsize=.1
    )

    plt.title("Operational Success vs Resource Constraints")
    plt.ylabel("Total Successful Operations")
    plt.xlabel("Global Resource Limit")
    plt.legend(title="Strategy", loc='upper left')

    plt.tight_layout()
    plt.savefig("paper_plots/fig1_success_comparison.png", dpi=300)
    print("Saved fig1_success_comparison.png")


def plot_efficiency_frontier(df):
    """
    Fig 2: Efficiency.
    Cost (X) vs Success (Y). Ideally, we want points in the Top-Left (Low Cost, High Success).
    """
    plt.figure(figsize=(10, 6))

    sns.scatterplot(
        data=df,
        x="Final_Cost",
        y="Final_Success",
        hue="Strategy",
        style="Strategy",
        s=120,
        alpha=0.7,
        palette="deep"
    )

    plt.title("Cost-Efficiency Frontier")
    plt.ylabel("Success (Output)")
    plt.xlabel("Resource Cost (Input)")

    plt.tight_layout()
    plt.savefig("paper_plots/fig2_efficiency_frontier.png", dpi=300)
    print("Saved fig2_efficiency_frontier.png")


def plot_heatmap_bio_improvement(df):
    """
    Fig 3: Where does Bio shine?
    Heatmap showing % Improvement of Bio over QoS across Accuracy and Resource levels.
    """
    # 1. Aggregate to unique conditions (averaging over DT and Run_ID)
    means = df.groupby(["Strategy", "Max_Res", "Sensor_Acc"])["Final_Success"].mean().reset_index()

    # 2. Pivot to separate strategies
    bio = means[means["Strategy"] == "biological"]
    qos = means[means["Strategy"] == "qos"]

    if bio.empty or qos.empty:
        print("Skipping Heatmap: Missing 'biological' or 'qos' data.")
        return

    # 3. Merge and Calculate Delta
    merged = pd.merge(bio, qos, on=["Max_Res", "Sensor_Acc"], suffixes=("_bio", "_qos"))
    merged["Improvement"] = ((merged["Final_Success_bio"] - merged["Final_Success_qos"]) / merged[
        "Final_Success_qos"]) * 100

    # 4. Pivot for Heatmap format
    heatmap_data = merged.pivot(index="Sensor_Acc", columns="Max_Res", values="Improvement")

    plt.figure(figsize=(8, 6))
    sns.heatmap(heatmap_data, annot=True, fmt=".1f", cmap="RdBu_r", center=0, cbar_kws={'label': '% Improvement'})

    plt.title("Biological Optimization Gain (%)")
    plt.ylabel("Sensor Accuracy")
    plt.xlabel("Resource Limit")

    plt.tight_layout()
    plt.savefig("paper_plots/fig3_sensitivity_heatmap.png", dpi=300)
    print("Saved fig3_sensitivity_heatmap.png")


def plot_latency_analysis(df):
    """
    Fig 4: Latency (Data Age).
    Does self-organization introduce lag?
    """
    plt.figure(figsize=(10, 6))

    sns.boxplot(
        data=df,
        x="Strategy",
        y="Avg_Latency",
        palette="Set2"
    )

    plt.title("System Latency Distribution by Strategy")
    plt.ylabel("Avg Data Age (Ticks)")
    plt.xlabel("Strategy")

    plt.tight_layout()
    plt.savefig("paper_plots/fig4_latency_box.png", dpi=300)
    print("Saved fig4_latency_box.png")


def main():
    if not os.path.exists("paper_plots"):
        os.makedirs("paper_plots")

        # File loading logic
    file_to_open = INPUT_FILE
    if not os.path.exists(file_to_open) and os.path.exists("sensitivity_results.csv"):
        file_to_open = "sensitivity_results.csv"

    try:
        df = pd.read_csv(file_to_open)
        # Ensure Strategy names are consistent (e.g., lowercase) to avoid KeyErrors
        df['Strategy'] = df['Strategy'].str.lower()
        print(f"Loaded {len(df)} rows from {file_to_open}")
    except FileNotFoundError:
        print(f"Error: Could not find {INPUT_FILE} or sensitivity_results.csv.")
        return

    set_style()

    # Original Plots
    plot_success_vs_resource(df)
    plot_efficiency_frontier(df)
    plot_heatmap_bio_improvement(df)  # Bio vs QoS
    plot_latency_analysis(df)

    # New Comparison Plots
    print("Generating extended comparisons...")
    plot_heatmap_bio_vs_ga(df)
    plot_heatmap_qos_vs_ga(df)
    plot_heatmap_bio_vs_best(df)


if __name__ == "__main__":
    main()