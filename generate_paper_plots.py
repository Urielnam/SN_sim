import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os


def set_style():
    # Set publication style (white background, grid)
    sns.set_theme(style="whitegrid")
    sns.set_context("paper", font_scale=1.4)


def plot_bar_comparison(df):
    plt.figure(figsize=(10, 6))

    # Bar plot with Error Bars (95% CI is default in Seaborn)
    # We aggregate over Sensor Accuracy to show general Resource vs Success trend
    ax = sns.barplot(
        data=df,
        x="Resource_Limit",
        y="Final_Success",
        hue="Strategy",
        palette="viridis",
        capsize=.1
    )

    plt.title("Operational Success: Self-Organizing vs Static Baseline")
    plt.ylabel("Total Successful Operations (Count)")
    plt.xlabel("Global Resource Constraint (Units)")
    plt.legend(title="Strategy")

    plt.tight_layout()
    plt.savefig("paper_plots/fig1_success_comparison.png", dpi=300)
    print("Saved fig1_success_comparison.png")


def plot_efficiency_scatter(df):
    plt.figure(figsize=(10, 6))

    # Scatter plot: Cost vs Success
    sns.scatterplot(
        data=df,
        x="Final_Cost",
        y="Final_Success",
        hue="Strategy",
        style="Strategy",
        s=100,
        alpha=0.8
    )

    plt.title("Cost-Efficiency Frontier")
    plt.ylabel("Success (Output)")
    plt.xlabel("Resource Cost (Input)")

    plt.tight_layout()
    plt.savefig("paper_plots/fig2_efficiency_frontier.png", dpi=300)
    print("Saved fig2_efficiency_frontier.png")


def plot_interaction_heatmap(df):
    # Pivot for Heatmap: Shows Improvement % of Bio over QoS

    # 1. Calculate means
    means = df.groupby(["Strategy", "Resource_Limit", "Sensor_Accuracy"])["Final_Success"].mean().reset_index()

    # 2. Split and Merge to get Delta
    bio = means[means["Strategy"] == "biological"]
    qos = means[means["Strategy"] == "qos"]

    merged = pd.merge(bio, qos, on=["Resource_Limit", "Sensor_Accuracy"], suffixes=("_bio", "_qos"))
    merged["Improvement"] = ((merged["Final_Success_bio"] - merged["Final_Success_qos"]) / merged[
        "Final_Success_qos"]) * 100

    # 3. Pivot
    heatmap_data = merged.pivot(index="Sensor_Accuracy", columns="Resource_Limit", values="Improvement")

    plt.figure(figsize=(8, 6))
    sns.heatmap(heatmap_data, annot=True, fmt=".1f", cmap="RdBu_r", center=0)

    plt.title("Biological Strategy Improvement (%) over Baseline")
    plt.ylabel("Sensor Accuracy (p)")
    plt.xlabel("Resource Limit (Max Capacity)")

    plt.tight_layout()
    plt.savefig("paper_plots/fig3_sensitivity_heatmap.png", dpi=300)
    print("Saved fig3_sensitivity_heatmap.png")


def main():
    if not os.path.exists("paper_plots"):
        os.makedirs("paper_plots")

    try:
        df = pd.read_csv("sensitivity_results.csv")
    except FileNotFoundError:
        print("sensitivity_results.csv not found.")
        return

    set_style()
    plot_bar_comparison(df)
    plot_efficiency_scatter(df)
    plot_interaction_heatmap(df)


if __name__ == "__main__":
    main()