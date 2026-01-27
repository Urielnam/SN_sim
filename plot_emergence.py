import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import sys

# Input from the Calculation Engine
INPUT_FILE = "emergence_results.csv"


def set_style():
    sns.set_theme(style="whitegrid")
    sns.set_context("paper", font_scale=1.4)


def load_data():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found. Run 'calc_emergence.py' first.")
        sys.exit(1)
    df = pd.read_csv(INPUT_FILE)
    # Normalize strategy names
    df['Strategy'] = df['Strategy'].str.lower()
    return df


def plot_emergence_comparison(df):
    """
    Fig 8: Strong Emergence Score (V(N))
    Comparison of the final Emergence term across strategies.
    Hypothesis: Biological > QoS > Static.
    """
    plt.figure(figsize=(10, 6))

    # Bar plot with Error Bars (95% CI)
    ax = sns.barplot(
        data=df,
        x="Strategy",
        y="Emergence_Score",
        palette="magma",
        errorbar=('ci', 95),
        capsize=.1
    )

    plt.title("Strong Emergence Comparison (Type 2)")
    plt.ylabel("Emergence V(N) (Bits of Constraint)")
    plt.xlabel("Control Strategy")

    # Add explicit label explanation
    plt.text(x=0.5, y=1.05, s="Higher Score = Greater Phase Space Contraction",
             transform=ax.transAxes, ha='center', fontsize=10, style='italic')

    plt.tight_layout()
    output_path = "paper_plots/fig8_emergence_score.png"
    plt.savefig(output_path, dpi=300)
    print(f"Saved {output_path}")


def plot_phase_space_contraction(df):
    """
    Fig 9: Phase Space Contraction
    Visualizes the "Gap" between Theoretical Capacity and Observed Entropy.
    This gap IS the Emergence.
    """
    # 1. Melt the dataframe to stack "Observed Entropy" and "Emergence"
    # (Since Capacity = Entropy + Emergence)
    # We want to show how much of the Capacity is "filled" by Entropy vs "constrained" by Emergence.

    # We'll plot Theoretical Capacity as a baseline, and Observed Entropy as bars.
    # The difference visually represents the emergence.

    plt.figure(figsize=(10, 6))

    # We need to reshape slightly to plot both metrics side-by-side or overlaid
    plot_df = pd.melt(df,
                      id_vars=["Strategy"],
                      value_vars=["Theoretical_Capacity", "Observed_Entropy"],
                      var_name="Metric",
                      value_name="Bits")

    # Bar plot
    sns.barplot(
        data=plot_df,
        x="Strategy",
        y="Bits",
        hue="Metric",
        palette=["#d3d3d3", "#2b2b2b"],  # Grey for Capacity (Potential), Black for Entropy (Actual)
        errorbar=('ci', 95),
        capsize=.05
    )

    plt.title("Phase Space Contraction Analysis")
    plt.ylabel("Information (Bits)")
    plt.xlabel("Strategy")
    plt.legend(title="Metric")

    # Annotation
    ax = plt.gca()
    plt.text(x=0.5, y=0.9, s="Gap = Emergence (Constraints)",
             transform=ax.transAxes, ha='center', color='red', fontsize=12, fontweight='bold')

    plt.tight_layout()
    output_path = "paper_plots/fig9_phase_space_contraction.png"
    plt.savefig(output_path, dpi=300)
    print(f"Saved {output_path}")


def plot_emergence_distribution(df):
    """
    Fig 10: Statistical Distribution of Emergence
    Box plot to show the variance and stability of the emergence.
    """
    plt.figure(figsize=(8, 6))

    sns.boxplot(
        data=df,
        x="Strategy",
        y="Emergence_Score",
        palette="viridis",
        width=0.5
    )

    sns.stripplot(
        data=df,
        x="Strategy",
        y="Emergence_Score",
        color=".25",
        alpha=0.6,
        size=4
    )

    plt.title("Statistical Distribution of Emergence")
    plt.ylabel("Emergence Score (Bits)")
    plt.xlabel("Strategy")

    plt.tight_layout()
    output_path = "paper_plots/fig10_emergence_distribution.png"
    plt.savefig(output_path, dpi=300)
    print(f"Saved {output_path}")


def main():
    if not os.path.exists("paper_plots"):
        os.makedirs("paper_plots")

    set_style()
    df = load_data()

    print(f"Loaded {len(df)} runs. Generating plots...")

    plot_emergence_comparison(df)
    plot_phase_space_contraction(df)
    plot_emergence_distribution(df)

    print("\n--- Emergence Plots Complete ---")


if __name__ == "__main__":
    main()