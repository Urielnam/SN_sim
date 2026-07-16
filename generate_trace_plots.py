import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from sim_config import SimulationConfig
import Simulation
import sys
import os
import glob
import math

def load_trace_file(filepath):
    """
    loads a Parquet trace file and calculates the Total_Resource Column.
    :param filepath:
    :return df:
    """
    df = pd.read_parquet(filepath)

    # Reconstruct Total_Resource from the saved microstate variables
    df["Total_Resource"] = df["num_iiots"] + df["bus_flow"] + df["edge_flow"] + df["scada_flow"]

    return df

def rerun_trace(filepath):
    """Reads a single simulation trace file and extracts time-series data."""
    print(f"Loading trace from {filepath}...")

    # Use the new DRY helper to load data and calculate Total_Resource
    df_raw = load_trace_file(filepath)

    # Map to the DataFrame format expected by your existing Seaborn plots
    df = pd.DataFrame({
        "Time": df_raw["time"],
        "Resource_Usage": df_raw["Total_Resource"],
        "IIoT_Nodes": df_raw["num_iiots"],
        "Bus_Flow": df_raw["bus_flow"],
        "Edge_Flow": df_raw["edge_flow"],
        "SCADA_Flow": df_raw["scada_flow"],
        "Cumulative_Success": df_raw["cumulative_success"], # Vector logs 'success_count' under this key
        "Feedback_State": df_raw["feedback_state"],
        "Strategy": df_raw["Strategy"],
        "Run_ID": df_raw["Run_ID"],
        "Max_Resource": df_raw["Max_Resource"],
        "Sensor_Acc": df_raw["Sensor_Acc"]

    })
    return df


def test_single_plot(filepath):
    """
    Loads one trace and displays a detailed component and success plot.
    """
    df = rerun_trace(filepath)
    strategy = df["Strategy"].iloc[0]

    fig, ax1 = plt.subplots(figsize=(12, 7))

    # Plot individual resource components (thin/dotted lines)
    ax1.plot(df["Time"], df["IIoT_Nodes"], label="IIoT Nodes", linestyle=':', alpha=0.7)
    ax1.plot(df["Time"], df["Bus_Flow"], label="Bus Flow", linestyle=':', alpha=0.7)
    ax1.plot(df["Time"], df["Edge_Flow"], label="Edge Flow", linestyle=':', alpha=0.7)
    ax1.plot(df["Time"], df["SCADA_Flow"], label="SCADA Flow", linestyle=':', alpha=0.7)

    # Plot total resource usage prominently
    ax1.plot(df["Time"], df["Resource_Usage"], label="Total Resource Usage", color='black', linewidth=2)

    # Draw the Max Resource ceiling
    max_limit = df["Max_Resource"].iloc[0]
    ax1.axhline(y=max_limit, color='red', linestyle='--', alpha=0.7, label=f"Max Resource ({max_limit})")

    ax1.set_xlabel("Simulation Time / Tick")
    ax1.set_ylabel("Resource Level")

    # Create a secondary Y-axis for Cumulative Success
    ax2 = ax1.twinx()
    ax2.plot(df["Time"], df["Cumulative_Success"], color='green', linewidth=2, label="Cumulative Success")
    ax2.set_ylabel("Cumulative Success Count", color='green')
    ax2.tick_params(axis='y', labelcolor='green')

    # Combine legends from both axes into one box
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper left")

    plt.title(f"Single Trace Components & Success | Strategy: {strategy}")
    plt.tight_layout()

    plt.savefig("test_trace_plot.png")
    print("Plot saved to test_trace_plot.png")


def plot_spaghetti_xray(traces_directory, strategy_filter=None):
    """
    Loads all traces, creates an output folder, and iterates through every combination
    of Max_Resource and Sensor_Acc to generate color-coded trace and success plots.
    """
    print(f"Loading traces from {traces_directory}...")

    search_pattern = os.path.join(traces_directory, "*.parquet")
    if strategy_filter:
        search_pattern = os.path.join(traces_directory, f"*_{strategy_filter}_*.parquet")

    files = glob.glob(search_pattern)
    if not files:
        print("No Parquet files found in the specified directory.")
        return

    # 1. Load all data into a single master DataFrame
    all_dfs = [rerun_trace(file) for file in files]
    master_df = pd.concat(all_dfs, ignore_index=True)

    # Create the output directory for the plots
    plots_dir = os.path.join(traces_directory, "plots")
    os.makedirs(plots_dir, exist_ok=True)
    print(f"Outputting plots to: {plots_dir}")

    # Generate a consistent color palette for the strategies
    strategies = master_df["Strategy"].unique()
    colors = sns.color_palette("husl", len(strategies))
    color_map = dict(zip(strategies, colors))

    # Generate a consistent shape (marker) palette for up to 11+ strategies
    marker_list = ['o', 's', '^', 'D', 'p', '*', 'h', 'v', 'X', 'P', 'd', '<', '>']
    marker_map = dict(zip(strategies, marker_list))

    # 2. Find all unique combinations of Max_Resource and Sensor_Acc
    combinations = master_df[["Max_Resource", "Sensor_Acc"]].drop_duplicates().values

    for res, acc in combinations:
        print(f"Generating plots for Max Resource: {res} | Sensor Acc: {acc}")

        # Filter master data for this specific configuration combination
        subset_df = master_df[(master_df["Max_Resource"] == res) & (master_df["Sensor_Acc"] == acc)]

        # Calculate Aggregates for this subset
        agg_df = subset_df.groupby(["Strategy", "Time"]).agg(
            Mean_Resource=("Resource_Usage", "mean"),
            Std_Resource=("Resource_Usage", "std"),
            Mean_Success=("Cumulative_Success", "mean"),
            Std_Success=("Cumulative_Success", "std")
        ).reset_index()

        title_suffix = f" | Res: {res}, Acc: {acc}"
        file_base = f"res{res}_acc{acc}"

        # =========================================================
        # PLOT 1: Resource Spaghetti & Lighter X-Ray (Small Multiples)
        # =========================================================
        n_strats = len(strategies)
        n_panels = n_strats + 1  # +1 for the combined overview panel
        cols = 4
        rows = math.ceil(n_panels / cols)

        fig1, axes1 = plt.subplots(rows, cols, figsize=(16, 3.5 * rows), sharex=True, sharey=True)
        axes1_flat = axes1.flatten() if n_panels > 1 else [axes1]

        for i, strategy in enumerate(strategies):
            ax1 = axes1_flat[i]
            strat_color = color_map.get(strategy, 'black')
            strat_data = subset_df[subset_df["Strategy"] == strategy]

            if strat_data.empty:
                ax1.set_title(f"{strategy} (No Data)", fontsize=10)
                continue

            for run_id in strat_data["Run_ID"].unique():
                run_df = strat_data[strat_data["Run_ID"] == run_id]
                ax1.plot(run_df["Time"], run_df["Resource_Usage"], color=strat_color, alpha=0.05, linewidth=1)

                successes = run_df[run_df["Feedback_State"] == 1]
                if not successes.empty:
                    ax1.scatter(successes["Time"], successes["Resource_Usage"],
                                color=strat_color, marker='*', s=20, zorder=5, alpha=0.3, edgecolors='none')

            strat_agg = agg_df[agg_df["Strategy"] == strategy]
            ax1.plot(strat_agg["Time"], strat_agg["Mean_Resource"], color=strat_color, linewidth=2, label="Mean")
            ax1.fill_between(strat_agg["Time"],
                             strat_agg["Mean_Resource"] - strat_agg["Std_Resource"],
                             strat_agg["Mean_Resource"] + strat_agg["Std_Resource"],
                             color=strat_color, alpha=0.2)

            ax1.axhline(y=res, color='red', linestyle='--', alpha=0.7)
            ax1.set_title(strategy, fontsize=11, fontweight='bold')

        # --- THE 12TH PANEL: ALL STRATEGIES COMBINED ---
        ax_all_1 = axes1_flat[n_strats]
        for i, strategy in enumerate(strategies):
            strat_color = color_map.get(strategy, 'black')
            strat_marker = marker_map.get(strategy, 'o')
            strat_agg = agg_df[agg_df["Strategy"] == strategy]

            # markevery=(start_offset, step_size)
            # i * 12 staggers the start so shapes don't overlap vertically; 150 spreads them out horizontally
            ax_all_1.plot(strat_agg["Time"], strat_agg["Mean_Resource"],
                          color=strat_color, marker=strat_marker, markevery=(i * 12, 300), markersize=6,
                          linewidth=1.5, label=strategy)

        ax_all_1.axhline(y=res, color='red', linestyle='--', alpha=0.7)
        ax_all_1.set_title("OVERVIEW (All Means)", fontsize=11, fontweight='heavy', color='darkblue')
        ax_all_1.legend(fontsize=7, loc='upper right', ncol=2)

        # Hide any unused subplots in the grid (if strategies count changes later)
        for j in range(n_panels, len(axes1_flat)):
            axes1_flat[j].set_visible(False)

        fig1.suptitle(f"Resource Lifespans & Success X-Ray{title_suffix}", fontsize=14, y=0.98)
        fig1.supxlabel("Simulation Time / Tick", fontsize=12)
        fig1.supylabel("Current Resource Level", fontsize=12)
        fig1.tight_layout(rect=[0, 0, 1, 0.96])  # Leave room for suptitle

        fig1.savefig(os.path.join(plots_dir, f"spaghetti_resource_{file_base}.png"), dpi=600)

        plt.close(fig1)

        # =========================================================Cumulative_Success
        # PLOT 2: Success Rate Trajectory (Small Multiples)
        # =========================================================
        fig2, axes2 = plt.subplots(rows, cols, figsize=(16, 3.5 * rows), sharex=True, sharey=True)
        axes2_flat = axes2.flatten() if n_panels > 1 else [axes2]

        for i, strategy in enumerate(strategies):
            ax2 = axes2_flat[i]
            strat_color = color_map.get(strategy, 'black')
            strat_data = subset_df[subset_df["Strategy"] == strategy]

            if strat_data.empty:
                ax2.set_title(f"{strategy} (No Data)", fontsize=10)
                continue

            for run_id in strat_data["Run_ID"].unique():
                run_df = strat_data[strat_data["Run_ID"] == run_id]
                ax2.plot(run_df["Time"], run_df["Cumulative_Success"], color=strat_color, alpha=0.05, linewidth=1)

            strat_agg = agg_df[agg_df["Strategy"] == strategy]
            ax2.plot(strat_agg["Time"], strat_agg["Mean_Success"], color=strat_color, linewidth=2)
            ax2.fill_between(strat_agg["Time"],
                             strat_agg["Mean_Success"] - strat_agg["Std_Success"],
                             strat_agg["Mean_Success"] + strat_agg["Std_Success"],
                             color=strat_color, alpha=0.2)

            ax2.set_title(strategy, fontsize=11, fontweight='bold')

        # --- THE 12TH PANEL: ALL STRATEGIES COMBINED ---
        ax_all_2 = axes2_flat[n_strats]
        for i, strategy in enumerate(strategies):
            strat_color = color_map.get(strategy, 'black')
            strat_marker = marker_map.get(strategy, 'o')
            strat_agg = agg_df[agg_df["Strategy"] == strategy]

            # Stagger the markers to prevent vertical collision
            ax_all_2.plot(strat_agg["Time"], strat_agg["Mean_Success"],
                          color=strat_color, marker=strat_marker, markevery=(i * 12, 300), markersize=6,
                          linewidth=1.5, label=strategy)

        ax_all_2.set_title("OVERVIEW (All Means)", fontsize=11, fontweight='heavy', color='darkblue')
        ax_all_2.legend(fontsize=7, loc='upper left', ncol=2)

        # Hide any unused subplots
        for j in range(n_panels, len(axes2_flat)):
            axes2_flat[j].set_visible(False)

        fig2.suptitle(f"Success Rate Trajectories{title_suffix}", fontsize=14, y=0.98)
        fig2.supxlabel("Simulation Time / Tick", fontsize=12)
        fig2.supylabel("Cumulative Success Count", fontsize=12)
        fig2.tight_layout(rect=[0, 0, 1, 0.96])
        fig2.savefig(os.path.join(plots_dir, f"spaghetti_success_{file_base}.png"), dpi=600)
        plt.close(fig2)

    print("All combinations plotted successfully.")

def run_trace(strategy_name):
    """Runs a single simulation and extracts time-series data."""
    print(f"Running trace for: {strategy_name}...")

    config = SimulationConfig(
        end_time=800,
        ui=False,
        optimization_method=strategy_name,
        iiot_acc=0.4,
        max_resource=1000
    )

    # Run
    data = Simulation.main_run(config)

    # Extract Time Series
    # 'total_resource' is a dict {time: count}
    times = list(data["total_resource"].keys())
    values = list(data["total_resource"].values())

    # Create DataFrame
    df = pd.DataFrame({
        "Time": times,
        "Resource_Usage": values,
        "Strategy": strategy_name
    })
    return df


def main():
    strategies = ["biological", "qos", "ga"]
    all_data = []

    # 1. Run Simulations
    for s in strategies:
        df = run_trace(s)
        all_data.append(df)

    full_df = pd.concat(all_data)

    # 2. Plotting (Seaborn)
    sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)

    # Figure 1: Combined Overlay
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=full_df, x="Time", y="Resource_Usage", hue="Strategy", linewidth=2)
    plt.title("System Behavior: Dynamic Resource Allocation Over Time")
    plt.ylabel("Total Active Resources (Sensors + Bandwidth)")
    plt.xlabel("Simulation Time (Ticks)")
    plt.savefig("paper_plots/trace_overlay.png", dpi=300)
    print("Saved trace_overlay.png")

    # Figure 2: Facet Grid (Side-by-Side for Clarity)
    g = sns.FacetGrid(full_df, col="Strategy", col_wrap=2, height=4, aspect=1.5, hue="Strategy")
    g.map(sns.lineplot, "Time", "Resource_Usage", linewidth=2)
    g.set_titles("{col_name} Strategy")
    g.set_axis_labels("Time", "Resource Usage")
    plt.savefig("paper_plots/trace_facet.png", dpi=300)
    print("Saved trace_facet.png")

    # --- Figure 3: Zoomed-in Steady State (NEW) ---
    plt.figure(figsize=(10, 6))

    # We filter the data slightly to ensure the plot focuses on the relevant lines
    # changing alpha helps see overlapping noise
    sns.lineplot(data=full_df, x="Time", y="Resource_Usage", hue="Strategy", linewidth=1.5, alpha=0.8)

    plt.title("Steady State Stability (Zoomed)")
    plt.ylabel("Total Active Resources")
    plt.xlabel("Simulation Time (Ticks)")

    # ZOOM SETTINGS
    # X-axis: Start at 150 to skip the initial ramp-up
    plt.xlim(150, 800)

    # Y-axis: Focus tight around 1000.
    # Adjust these numbers if your fluctuations are larger/smaller than expected.
    plt.ylim(980, 1005)

    plt.savefig("paper_plots/trace_zoomed.png", dpi=300)
    print("Saved trace_zoomed.png")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        target_path = sys.argv[1]

        # If the user passed a specific file, do the single plot
        if target_path.endswith(".parquet"):
            test_single_plot(target_path)
        # If the user passed a directory, do the spaghetti plot
        elif os.path.isdir(target_path):
            plot_spaghetti_xray(target_path)
        else:
            print("Error: Path is neither a .parquet file nor a valid directory.")
    else:
        print("Please provide a path to a .parquet file or a folder of .parquet files via terminal.")
        print("Example: python generate_trace_plots.py results/raw_data/20260710_210551/traces/")