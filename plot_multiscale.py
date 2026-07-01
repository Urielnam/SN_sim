import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 1. Load the data
input_file = 'aggregated_multiscale_results.csv'
df = pd.read_csv(input_file)

# 2. Setup Plotting Styles
# Assign consistent colors and markers for each strategy
strategies = df['Strategy'].unique()
colors = {
    'static': 'grey',  # Grey for rigid/baseline
    'biological': 'green',  # Green for organic
    'qos': 'blue',  # Blue for engineered/logic
    'ga': 'orange'  # Orange for genetic algorithm
}
markers = {
    'static': 's',  # Square
    'biological': 'o',  # Circle
    'qos': '^',  # Triangle Up
    'ga': 'D'  # Diamond
}

plt.figure(figsize=(14, 8))

# Track global min/max for scaling y-axis
y_min_overall = 0
y_max_overall = 0

# 3. Plot each strategy
for strategy in strategies:
    # Extract data for this strategy
    subset = df[df['Strategy'] == strategy].sort_values('Scale_k')

    scales = subset['Scale_k'].values
    varieties = subset['Variety_Vk'].values
    capacity = subset['Capacity'].iloc[0]
    n_vars = subset['N_Variables'].iloc[0]

    # Get style (default to black/x if strategy not in dict)
    color = colors.get(strategy, 'black')
    marker = markers.get(strategy, 'x')

    # Plot the V(k) Curve
    plt.plot(scales, varieties,
             marker=marker,
             linewidth=2.5,
             markersize=10,
             color=color,
             label=f'{strategy} (N={n_vars})')

    # Plot the Capacity Line (Theoretical Max)
    # Dashed line to show the "bounds" of the system
    plt.axhline(capacity, color=color, linestyle='--', alpha=0.4)

    # Track limits
    y_min_overall = min(y_min_overall, varieties.min())
    y_max_overall = max(y_max_overall, capacity)

# 4. Add Reference Lines & Zones
plt.axhline(0, color='black', linewidth=3.0)  # Zero line

# Shade the Negative Variance Zone (Emergence)
if y_min_overall < 0:
    plt.fill_between(
        x=[df['Scale_k'].min(), df['Scale_k'].max()],
        y1=-54,
        y2=y_min_overall * 1.1,  # Cover down to the lowest point
        color='red',
        alpha=0.05,
        label='|V(k)|> V(N) (Strong Emergence)'
    )

# 5. Formatting
plt.title('Multiscale Variance V(k): Comparison of Strategies', fontsize=22, fontweight='bold')
plt.xlabel('Scale (k)', fontsize=20)
plt.ylabel('Variance V(k) (bits)', fontsize=20)

# Set Y-limits to focus on the interesting part (zoom out slightly)
plt.ylim(bottom=y_min_overall * 1.1, top=y_max_overall * 1.15)

# Ensure X-axis has integer ticks only
all_scales = sorted(df['Scale_k'].unique())
plt.xticks(all_scales, fontsize=18)
plt.yticks(fontsize=18)

plt.legend(fontsize=18, loc='lower left', frameon=True, shadow=True)
plt.grid(True, linestyle=':', alpha=0.6)

# 6. Save and Show
output_filename = 'multiscale_comparison_plot.png'
plt.tight_layout()
plt.savefig(output_filename, dpi=300)
plt.show()

print(f"Plot saved successfully to {output_filename}")