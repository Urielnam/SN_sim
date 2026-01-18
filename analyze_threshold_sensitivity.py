import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import sys
import numpy as np

# Configuration
INPUT_FILE = "mega_sweep_results.csv"
BASE_OUTPUT_DIR = "paper_plots/threshold_analysis"


def setup_plot_style():
    sns.set_theme(style="whitegrid", context="paper", font_scale=1.4)

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def load_data():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        sys.exit(1)

    df = pd.read_csv(INPUT_FILE)

    # Check if DT exists
    if 'DT' not in df.columns:
        print("Error: Column 'DT' not found in input file.")
        sys.exit(1)

    # Filter for Biological Strategy only
    df_bio = df[df['Strategy'] == 'biological'].copy()

    if df_bio.empty:
        print("Error: No data found for 'biological' strategy.")
        sys.exit(1)

    print(f"Loaded {len(df_bio)} biological records.")
    return df_bio


def get_representative_levels(df, col_name, n=6):
    """
    Selects 'n' evenly spaced representative values from a column.
    Useful for filtering dense data down to a readable number of plot lines.
    """
    unique_vals = sorted(df[col_name].unique())

    if len(unique_vals) <= n:
        return unique_vals

    # Use linspace to find indices evenly distributed across the range
    indices = np.linspace(0, len(unique_vals) - 1, n, dtype=int)
    selected_vals = [unique_vals[i] for i in indices]

    print(f"DEBUG: Auto-selected {col_name} levels: {selected_vals}")
    return selected_vals

def prep_categorical_data(df, hue_col):
    """
    Prepares a DataFrame for Seaborn by converting a numeric column to a
    sorted categorical string column.

    Returns:
        plot_df: Copy of df with a new string column
        hue_order: List of strings sorted numerically (e.g. '50', '100', '1000')
        new_col_name: The name of the new string column to use in hue
    """
    # 1. Sort unique values numerically (so 50 comes before 1000)
    unique_vals = sorted(df[hue_col].unique())

    # 2. Convert to string for the legend
    hue_order = [str(x) for x in unique_vals]

    # 3. Create a copy and add the string column
    plot_df = df.copy()
    new_col_name = f"{hue_col}_Cat"
    plot_df[new_col_name] = plot_df[hue_col].astype(str)

    return plot_df, hue_order, new_col_name

# ---------------------------------------------------------
# PLOTTING FUNCTIONS
# ---------------------------------------------------------

def plot_sweet_spot_curve(df, output_dir):
    """
    Graph A: The "Sweet Spot" Curve (Success vs. Threshold)
    Shows the optimal threshold range with 95% Confidence Intervals.
    """
    plt.figure(figsize=(12, 6))

    # --- Use the helper function ---
    target_resources = get_representative_levels(df, "Max_Res", n=6)

    # Filter the dataframe
    subset_df = df[df["Max_Res"].isin(target_resources)].copy()

    # Use the helper
    plot_df, hue_order, hue_col = prep_categorical_data(subset_df, "Max_Res")


    # Seaborn lineplot calculates mean and 95% CI (the shaded band) automatically
    ax = sns.lineplot(
        data=plot_df,
        x="Threshold",
        y="Final_Success",
        hue=hue_col,
        hue_order=hue_order,
        palette="viridis",
        linewidth=2.5,
        err_style="band",  # The "Shadow of Uncertainty"
        errorbar=("ci", 95),
        marker = "o",
        markersize = 8
    )

    plt.title("The 'Sweet Spot': Optimal Threshold Identification")
    plt.ylabel("Operational Success (Mean ± 95% CI)")
    plt.xlabel("Self-Organization Threshold")

    # 2. Move Legend Outside
    # bbox_to_anchor=(x, y): (1.02, 1) means "Just outside the right edge, aligned to top"
    plt.legend(
        title="Resource Limit",
        bbox_to_anchor=(1.02, 1),
        loc='upper left',
        borderaxespad=0
    )

    save_path = os.path.join(output_dir, "figA_sweet_spot_curve.png")
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    print(f"Saved: {save_path}")
    plt.close()


def plot_stability_heatmap(df, output_dir):
    """
    Graph B: The "Stability-Performance" Heatmap
    Plots (Mean - StdDev) to identify the "Safe Bet" parameters.
    Facetted by Resource Limit.
    """
    # 1. Aggregate Statistics
    # We group by the environmental constraints (Acc, Max_Res) and the parameter (Threshold)
    grouped = df.groupby(["Max_Res", "Sensor_Acc", "Threshold"])["Final_Success"].agg(["mean", "std"]).reset_index()

    # 2. Calculate "Conservative Performance" (Lower Bound)
    # This answers: "What is the worst I can expect in a typical run?"
    grouped["Lower_Bound"] = grouped["mean"] - grouped["std"]

    # 3. Create Heatmaps (One per Resource Level)
    resource_levels = sorted(grouped["Max_Res"].unique())

    fig, axes = plt.subplots(1, len(resource_levels), figsize=(6 * len(resource_levels), 6), sharey=True)
    if len(resource_levels) == 1: axes = [axes]  # Handle single resource case

    # Find global min/max for consistent color scaling
    vmin = grouped["Lower_Bound"].min()
    vmax = grouped["Lower_Bound"].max()

    for i, res in enumerate(resource_levels):
        ax = axes[i]
        subset = grouped[grouped["Max_Res"] == res]

        # Pivot for heatmap: Y=Accuracy, X=Threshold, Z=Lower_Bound
        pivot_data = subset.pivot(index="Sensor_Acc", columns="Threshold", values="Lower_Bound")

        sns.heatmap(
            pivot_data,
            ax=ax,
            cmap="mako",  # Darker = Higher/Better
            annot=True,
            fmt=".0f",
            cbar=(i == len(resource_levels) - 1),  # Only show colorbar on last plot
            vmin=vmin,
            vmax=vmax
        )

        ax.set_title(f"Max Resources: {res}\n(Metric: Mean Success - 1 StdDev)")
        ax.set_xlabel("Threshold")
        if i == 0:
            ax.set_ylabel("Sensor Accuracy")
        else:
            ax.set_ylabel("")

    plt.suptitle("Stability Map: Identifying Robust Parameter Zones", y=1.02)

    save_path = os.path.join(output_dir, "figB_stability_heatmap.png")
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    print(f"Saved: {save_path}")
    plt.close()


def plot_efficiency_multires(df, output_dir):
    """
    Graph C (Revised): Efficiency vs. Threshold across Resource Limits

    Visualizes 'Efficiency' (Success / Cost) for ALL resource limits on one plot.
    This allows us to see if the 'shape' of the efficiency curve repeats itself
    regardless of the system scale.
    """
    # 1. Calculate Efficiency
    # We use Final_Cost (Input) as the denominator.
    # Handle potential 0 cost (unlikely) to avoid errors.
    df["Efficiency"] = df["Final_Success"] / df["Final_Cost"].replace(0, 1)

    plt.figure(figsize=(12, 6))

    # --- Use the helper function ---
    target_resources = get_representative_levels(df, "Max_Res", n=6)

    # Filter the dataframe
    subset_df = df[df["Max_Res"].isin(target_resources)].copy()

    # 2. Use the helper
    plot_df, hue_order, hue_col = prep_categorical_data(subset_df, "Max_Res")


    # 3. Plot
    # markers=True helps identify the exact sampled threshold points.
    sns.lineplot(
        data=plot_df,
        x="Threshold",
        y="Efficiency",
        hue=hue_col,
        hue_order=hue_order,
        palette="viridis",
        linewidth=2.5,
        marker="o",
        markersize=8,
        errorbar=("ci", 95) # Keep the "Shadow of Uncertainty"
    )

    plt.title("Efficiency Consistency: Optimal Threshold across Scales")
    plt.ylabel("Efficiency (Success per Unit of Resource)")
    plt.xlabel("Self-Organization Threshold")

    # 4. Legend Outside
    plt.legend(
        title="Global Resource Limit",
        bbox_to_anchor=(1.02, 1),
        loc='upper left',
        borderaxespad=0
    )

    save_path = os.path.join(output_dir, "figC_efficiency_multires.png")
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    print(f"Saved: {save_path}")
    plt.close()




def plot_efficiency_landscape(df, output_dir):
    """
    Graph E: Global Efficiency Landscape
    Visualizes 'Bang for Buck' (Success/Cost) as a terrain map.

    Bright spots = Highly efficient configurations.
    Dark spots = Wasteful configurations.
    """
    # 1. Calculate Efficiency (if not already done)
    # We use a copy to ensure we don't affect the main df multiple times if called repeatedly
    plot_df = df.copy()
    plot_df["Efficiency"] = plot_df["Final_Success"] / plot_df["Final_Cost"].replace(0, 1)

    # 2. Pivot: Matrix format for Heatmap
    # Rows (Y) = Resource Limit, Columns (X) = Threshold, Values = Efficiency
    matrix = plot_df.pivot_table(
        index="Max_Res",
        columns="Threshold",
        values="Efficiency",
        aggfunc="mean"  # Average over the mixed sensor accuracies
    )

    plt.figure(figsize=(12, 10))

    # 3. Plot Heatmap
    sns.heatmap(
        matrix,
        cmap="inferno",  # 'inferno' or 'magma' are great for intensity/efficiency
        cbar_kws={'label': 'Efficiency (Success / Cost)'},
        robust=True  # Ignores extreme outliers to keep colors visible
    )

    plt.title("Efficiency Landscape: Finding the Economic Sweet Spot")
    plt.ylabel("Resource Limit (Max_Res)")
    plt.xlabel("Self-Organization Threshold")

    # Invert Y axis so 2000 is at the top (optional)
    plt.gca().invert_yaxis()

    save_path = os.path.join(output_dir, "figE_efficiency_landscape.png")
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    print(f"Saved: {save_path}")
    plt.close()


def plot_global_landscape(df,output_dir):
    """
    Graph D: Global Parameter Landscape
    Visualizes Success as a terrain map (Heatmap).
    X = Threshold, Y = Resource Limit, Color = Success
    """
    # Pivot the data to get a matrix format
    # We use pivot_table with aggregation in case there are multiple runs per point
    matrix = df.pivot_table(
        index="Max_Res",
        columns="Threshold",
        values="Final_Success",
        aggfunc="mean"
    )

    plt.figure(figsize=(12, 10))

    sns.heatmap(
        matrix,
        cmap="viridis",
        cbar_kws={'label': 'Mean Operational Success'},
        robust=True  # Handles outliers better for color scaling
    )

    plt.title("Global Parameter Landscape: Resource vs. Threshold")
    plt.ylabel("Resource Limit (Max_Res)")
    plt.xlabel("Self-Organization Threshold")

    # Invert Y axis so higher resources are at the top (optional, often more intuitive)
    plt.gca().invert_yaxis()

    save_path = os.path.join(output_dir, "figD_global_landscape.png")
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    print(f"Saved: {save_path}")
    plt.close()


def plot_activation_curve(df, output_dir):
    """
    Graph F: System Activation Curve
    Visualizes "Which self-organization measures we received".

    Checks if the system actually reacted to the Threshold.
    Ideally, we want to see high Self-Org at low thresholds, dropping to near-zero
    at high thresholds.
    """
    # Safety Check: Does the column exist?
    if "Avg_Self_Org" not in df.columns:
        print("Warning: 'Avg_Self_Org' column missing. Skipping Activation Curve.")
        print("Tip: Update sensitivity_sweep.py to export this metric.")
        return

    plt.figure(figsize=(12, 6))

    # --- Use the helper function for clean legend ---
    target_resources = get_representative_levels(df, "Max_Res", n=6)
    subset_df = df[df["Max_Res"].isin(target_resources)].copy()
    plot_df, hue_order, hue_col = prep_categorical_data(subset_df, "Max_Res")

    sns.lineplot(
        data=plot_df,
        x="Threshold",
        y="Avg_Self_Org",
        hue=hue_col,
        hue_order=hue_order,
        palette="magma",  # 'Magma' implies heat/activity
        linewidth=2.5,
        marker="d",  # Diamond marker
        markersize=8,
        errorbar=("ci", 95)
    )

    plt.title("System Activation: Realized Volatility vs. Threshold")
    plt.ylabel("Average Self-Organization Measure (Activity)")
    plt.xlabel("Input Threshold")

    # Add a semantic annotation (optional, helps interpretation)
    plt.text(x=plot_df["Threshold"].min(), y=plot_df["Avg_Self_Org"].max(),
             s="High Adaptation\n(Chaos)", color='black', ha='left', va='top', fontsize=10)

    plt.text(x=plot_df["Threshold"].max(), y=plot_df["Avg_Self_Org"].min(),
             s="Static State\n(Stability)", color='black', ha='right', va='bottom', fontsize=10)

    # Legend placement
    plt.legend(
        title="Global Resource Limit",
        bbox_to_anchor=(1.02, 1),
        loc='upper left',
        borderaxespad=0
    )

    save_path = os.path.join(output_dir, "figF_activation_curve.png")
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    print(f"Saved: {save_path}")
    plt.close()

def main():
    setup_plot_style()
    df = load_data()

    # 1. GENERATE "ALL DATA" PLOTS (The Original Behavior)
    # These will be saved directly in paper_plots/threshold_analysis/
    print("\n>>> Processing Combined Data (All DTs)...")
    ensure_dir(BASE_OUTPUT_DIR)

    plot_sweet_spot_curve(df, BASE_OUTPUT_DIR)
    plot_efficiency_multires(df, BASE_OUTPUT_DIR)
    plot_global_landscape(df, BASE_OUTPUT_DIR)
    plot_efficiency_landscape(df, BASE_OUTPUT_DIR)
    plot_activation_curve(df, BASE_OUTPUT_DIR)
    print(f"   [✓] Combined plots saved to {BASE_OUTPUT_DIR}")

    # 2. GENERATE PER-DT PLOTS

        # 1. Get unique values of DT
    dt_values = sorted(df['DT'].unique())
    print(f"Found {len(dt_values)} unique DT values: {dt_values}")

        # 2. Loop through each DT value
    for dt in dt_values:
        print(f"\n>>> Processing DT = {dt}...")

        # 3. Create a specific directory for this DT
        # Example: paper_plots/threshold_analysis/DT_10
        current_output_dir = os.path.join(BASE_OUTPUT_DIR, f"DT_{dt}")
        ensure_dir(current_output_dir)

        # 4. Filter the data for this specific DT
        dt_subset = df[df['DT'] == dt].copy()

        # 5. Generate all plots using the SUBSET and the NEW DIRECTORY
        if not dt_subset.empty:
            plot_sweet_spot_curve(dt_subset, current_output_dir)
            plot_efficiency_multires(dt_subset, current_output_dir)
            plot_global_landscape(dt_subset, current_output_dir)
            plot_efficiency_landscape(dt_subset, current_output_dir)
            plot_activation_curve(dt_subset, current_output_dir)
            print(f"   [✓] Plots saved to {current_output_dir}")
        else:
            print(f"   [!] No data for DT={dt}, skipping.")

    print("\n--- All DT configurations processed ---")


if __name__ == "__main__":
    main()