import gymnasium as gym
from stable_baselines3 import PPO
from gym_env import ISRSimEnv


def main():
    # 1. Load the Environment
    env = ISRSimEnv()

    # 2. Load the Trained Model
    model_path = "models/PPO/isr_final_model.zip"
    try:
        model = PPO.load(model_path)
    except FileNotFoundError:
        print("Model not found! Run train_rl.py first.")
        return

    # 3. Run a Test Episode
    obs, _ = env.reset()
    terminated = False
    truncated = False
    total_reward = 0

    print("--- Running Trained Agent ---")
    while not terminated and not truncated:
        # Ask the model for the best action based on the observation
        action, _states = model.predict(obs, deterministic=True)

        # Take the action
        obs, reward, terminated, truncated, info = env.step(action)

        total_reward += reward

        # Optional: Print "Decisions" to see what it's doing
        # Action 1=Add Sensor, 2=Remove Sensor, etc.
        if action != 0:  # Ignore "No-Op" to reduce noise
            print(f"Time: {env.env.now:.1f} | Agent Chose: {action} | Reward: {reward:.2f}")

    print(f"--- Episode Finished. Total Reward: {total_reward} ---")


if __name__ == "__main__":
    main()