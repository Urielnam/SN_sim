import numpy as np
from itertools import combinations, product
import math


def calculate_shannon_entropy(data_matrix):
    """
    Calculates the joint Shannon entropy (in bits) for a subset of variables.
    data_matrix: A 2D numpy array where rows are time steps (T)
                 and columns are the chosen variables.
    """
    # Find all unique states (rows) and how many times they occur
    _, counts = np.unique(data_matrix, axis=0, return_counts=True)

    # Convert frequencies to probabilities
    probabilities = counts / counts.sum()

    # Calculate entropy in base 2 (bits)
    entropy = -np.sum(probabilities * np.log2(probabilities))
    return entropy


def compute_multiscale_variety(history_matrix):
    """
    Computes Q, D, and V profiles based on Bar-Yam's SoS emergence equations.

    Args:
        history_matrix: A 2D numpy array of shape (T, N)
                        T = number of timesteps
                        N = total number of variables in the system

    Returns:
        Q, D, V: Dictionaries keyed by scale k (from 1 to N)
    """
    history_matrix = np.asarray(history_matrix)
    T, N = history_matrix.shape

    # --- Step 1: Calculate Q(m) for all subset sizes m from 1 to N ---
    # Q[m] is the sum of entropies for all possible subsets of size m.
    # We explicitly define Q(0) = 0 for the empty set.
    Q = {0: 0.0}

    for m in range(1, N + 1):
        q_sum = 0.0
        # Generate all combinations of column indices of size m
        for cols in combinations(range(N), m):
            subset_data = history_matrix[:, cols]
            q_sum += calculate_shannon_entropy(subset_data)
        Q[m] = q_sum

    # --- Step 2: Calculate D(k) using Equation 2 ---
    D = {}
    for k in range(1, N + 1):
        d_val = 0.0
        for j in range(0, k + 1):
            sign_term = (-1) ** (k - j + 1)
            binom_term = math.comb(N - j, k - j)
            q_term = Q[N - j]

            d_val += sign_term * binom_term * q_term

        D[k] = d_val

    # --- Step 3: Calculate V(k) using Equation 3 ---
    V = {}
    for k in range(1, N + 1):
        # V(k) is the sum of D(k') from k'=k to N
        v_val = sum(D[k_prime] for k_prime in range(k, N + 1))
        V[k] = v_val

    return Q, D, V


# --- Test Matrix Generator ---
def generate_parity_matrix(n_bits):
    """
    Generates a history matrix for an N-bit even parity system.
    Returns a matrix of shape (2^(N-1), N) containing all valid states.
    """
    states = []
    # Generate all possible combinations of the independent bits
    for seq in product([0, 1], repeat=n_bits - 1):
        # Calculate the dependent parity bit (even parity)
        parity_bit = sum(seq) % 2
        state = list(seq) + [parity_bit]
        states.append(state)
    return np.array(states)


# --- Test Suite ---
def run_tests():
    # Known values from the literature
    expected_results = {
        3: {
            'D': {1: 0, 2: 3, 3: -1},
            'V': {1: 2, 2: 2, 3: -1}
        },
        4: {
            'D': {1: 0, 2: 6, 3: -4, 4: 1},
            'V': {1: 3, 2: 3, 3: -3, 4: 1}
        },
        5: {
            'D': {1: 0, 2: 10, 3: -10, 4: 5, 5: -1},
            'V': {1: 4, 2: 4, 3: -6, 4: 4, 5: -1}
        }
    }

    tolerance = 1e-5  # Float comparison tolerance

    for N, expected in expected_results.items():
        print(f"\n--- Testing Parity Bit System for N={N} ---")
        history_matrix = generate_parity_matrix(N)
        print(f"Generated history matrix shape: {history_matrix.shape}")

        Q, D, V = compute_multiscale_variety(history_matrix)

        # If your function is not fully implemented yet, skip assertions
        if not D or not V:
            print("Engine returned empty dicts. Implement the engine to see results.")
            continue

        print(f"Calculated D(k): {D}")
        print(f"Calculated V(k): {V}")

        # Validate D(k)
        for k, expected_val in expected['D'].items():
            actual_val = D.get(k, 0)
            assert abs(actual_val - expected_val) < tolerance, \
                f"N={N} D({k}) Failed: Expected {expected_val}, got {actual_val}"

        # Validate V(k)
        for k, expected_val in expected['V'].items():
            actual_val = V.get(k, 0)
            assert abs(actual_val - expected_val) < tolerance, \
                f"N={N} V({k}) Failed: Expected {expected_val}, got {actual_val}"

        # Validate Sum Rule: Sum of V(k) must equal N
        v_sum = sum(V.values())
        assert abs(v_sum - N) < tolerance, \
            f"N={N} Sum Rule Failed: Sum of V(k) = {v_sum}, expected {N}"

        print(f"SUCCESS: N={N} Parity System perfectly matches the theoretical profile!")


if __name__ == "__main__":
    run_tests()