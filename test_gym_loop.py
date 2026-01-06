import gymnasium as gym
from gym_env import ISRSimEnv  # Assumes you saved gym_env.py


def run_random_agent():
    # 1. Initialize the Environment
    env = ISRSimEnv()

    # 2. Reset (Start of Episode)
    observation, info = env.reset()
    print(f"Initial State: {observation}")

    terminated = False
    truncated = False
    total_reward = 0
    steps = 0

    print("\n--- Starting Random Agent Loop ---")
    while not terminated and not truncated:
        # 3. Pick a Random Action (0-8)
        action = env.action_space.sample()

        # 4. Step the Environment
        observation, reward, terminated, truncated, info = env.step(action)

        total_reward += reward
        steps += 1

        # Optional: Print every 100 steps
        if steps % 100 == 0:
            print(f"Step {steps}: Action={action}, Reward={reward:.2f}, Resources={observation[3]}")

    print(f"\nEpisode Finished. Total Reward: {total_reward:.2f}")
    env.close()


if __name__ == "__main__":
    run_random_agent()