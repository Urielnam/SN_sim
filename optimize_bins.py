import pandas as pd
import numpy as np
import os
import glob
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import warnings

warnings.filterwarnings("ignore")

RAW_DATA_DIR = "sim_data/raw_batch"
VARIABLES = ["num_iiots", "bus_flow", "edge_flow", "scada_flow", "queue_len", "success_rate"]

# --- CONFIGURATION ---
# Set strict limits to FORCE higher resolution
MIN_BINS = 6  # Minimum number of states to detect (unless data is too sparse)
MAX_BINS = 12  # Maximum number of states


def load_data():
    print("--- Loading Global Ensemble Data ---")
    files = glob.glob(os.path.join(RAW_DATA_DIR, "*.csv"))
    if not files: return pd.DataFrame()

    df_list = []
    for f in files:
        try:
            temp_df = pd.read_csv(f)
            df_list.append(temp_df)
        except Exception:
            pass

    if not df_list: return pd.DataFrame()
    return pd.concat(df_list, ignore_index=True)


def get_natural_breaks(series, var_name):
    """
    Finds optimal bins with a bias towards HIGH RESOLUTION.
    """
    clean = series.dropna()
    clean = clean[clean >= 0]

    if len(clean) < 100:
        return 3, [-np.inf, np.inf]

    # 1. Discrete Data Check
    unique_vals = sorted(clean.unique())
    n_unique = len(unique_vals)

    # If the data naturally has fewer states than our minimum target,
    # we MUST use the natural states (can't invent data).
    if n_unique < MIN_BINS:
        edges = [-np.inf] + [x + 0.5 for x in unique_vals[:-1]] + [np.inf]
        return n_unique, edges

    # 2. Log Transformation
    # Essential for high-dynamic range variables (queues, iiot counts)
    use_log = False
    if clean.max() > 20 and (clean.skew() > 2 or var_name in ["queue_len", "num_iiots"]):
        use_log = True
        data_for_clustering = np.log1p(clean).values.reshape(-1, 1)
    else:
        data_for_clustering = clean.values.reshape(-1, 1)

    # 3. High-Res Optimization Loop
    best_k = MIN_BINS
    best_score = -1.0
    best_kmeans = None

    # Cap the search at the number of unique values found
    search_limit = min(MAX_BINS, n_unique)
    search_start = min(MIN_BINS, n_unique)

    # If start >= limit, just take all unique values
    if search_start >= search_limit:
        search_range = [search_limit]
    else:
        search_range = range(search_start, search_limit + 1)

    for k in search_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(data_for_clustering)

        try:
            score = silhouette_score(data_for_clustering, labels, sample_size=3000)

            # BIAS FACTOR: We add a small bonus for having MORE bins.
            # This encourages the algorithm to pick k=8 over k=4 if the scores are close.
            # Bonus: +0.02 per extra bin
            adjusted_score = score + (k * 0.02)

        except:
            adjusted_score = 0

        if adjusted_score > best_score:
            best_score = adjusted_score
            best_k = k
            best_kmeans = kmeans

    # 4. Extract Edges
    centers = sorted(best_kmeans.cluster_centers_.flatten())
    inner_edges = [(centers[i] + centers[i + 1]) / 2 for i in range(len(centers) - 1)]

    if use_log:
        inner_edges = [np.expm1(x) for x in inner_edges]

    inner_edges = [round(x, 1) for x in inner_edges]

    # 5. Zero-Inflation Handling
    # Ensure 0 is separated if it's significant
    if (clean == 0).mean() > 0.05:
        # If no edge falls between 0 and 1, force one
        if not any(0 < e < 1 for e in inner_edges):
            inner_edges.insert(0, 0.5)
            inner_edges = sorted(list(set(inner_edges)))

    final_edges = [-np.inf] + inner_edges + [np.inf]
    M = len(final_edges) - 1

    return M, final_edges


def main():
    df = load_data()
    if df.empty:
        print("No data found.")
        return

    print("\n--- HIGH-RESOLUTION CONFIGURATION (M_target = 6-12) ---")
    print("# Copy to 'discretization_config.py'\n")
    print("import numpy as np\n")

    capacities = {}
    bins_config = {}

    for col in VARIABLES:
        if col not in df.columns: continue

        print(f"Analyzing '{col}'...", end=" ", flush=True)
        M, edges = get_natural_breaks(df[col], col)

        capacities[col] = M
        edges_str = str(edges).replace("inf", "np.inf")
        bins_config[col] = edges_str
        print(f"Done (M={M})")

    print("\n" + "=" * 40)
    print("CAPACITIES = {")
    for k, v in capacities.items():
        print(f'    "{k}": {v},')
    print("}\n")

    print("DISCRETE_BINS = {")
    for k, v in bins_config.items():
        print(f'    "{k}": {v},')
    print("}")
    print("=" * 40 + "\n")


if __name__ == "__main__":
    main()