import pandas as pd
from scipy import stats
import sys

# Constants matching your Industrial naming convention
BASELINE_STRAT = "qos"
TEST_STRAT = "biological"
METRIC = "Final_Success"


def main():
    try:
        df = pd.read_csv("sensitivity_results.csv")
    except FileNotFoundError:
        print("Error: 'sensitivity_results.csv' not found. Run sensitivity_sweep.py first.")
        sys.exit(1)

    print("--- Statistical Validation (T-Test) ---")

    # 1. Group by Conditions (Resource Limit & Accuracy)
    # We want to compare Bio vs QoS only within the same conditions.
    grouped = df.groupby(["Resource_Limit", "Sensor_Accuracy"])

    results = []

    for name, group in grouped:
        res_limit, acc = name

        # Extract data vectors
        baseline_data = group[group["Strategy"] == BASELINE_STRAT][METRIC]
        test_data = group[group["Strategy"] == TEST_STRAT][METRIC]

        # Check for sufficient data
        if len(baseline_data) < 2 or len(test_data) < 2:
            print(f"Skipping {name}: Insufficient samples for t-test.")
            continue

        # 2. Perform Welch's t-test (assumes unequal variance, safer for sim data)
        t_stat, p_val = stats.ttest_ind(test_data, baseline_data, equal_var=False)

        # 3. Interpret Result
        is_significant = p_val < 0.05
        mean_diff = test_data.mean() - baseline_data.mean()
        improvement_pct = (mean_diff / baseline_data.mean()) * 100 if baseline_data.mean() != 0 else 0

        results.append({
            "Resource_Limit": res_limit,
            "Accuracy": acc,
            "Mean_Diff": mean_diff,
            "Improvement_%": round(improvement_pct, 2),
            "P_Value": round(p_val, 4),
            "Significant": is_significant
        })

    # 4. Output Report
    results_df = pd.DataFrame(results)
    print(results_df.to_string(index=False))

    # 5. Overall Conclusion
    significant_wins = results_df[results_df["Significant"] == True]
    print(
        f"\nConclusion: The Biological strategy showed statistically significant improvement in {len(significant_wins)}/{len(results_df)} scenarios tested.")


if __name__ == "__main__":
    main()