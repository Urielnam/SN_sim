import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from sim_config import SimulationConfig
import Simulation


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
    main()