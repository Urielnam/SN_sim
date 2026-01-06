import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import EvalCallback
import os

# Import your custom environment
# Ensure gym_env.py is in the same directory
from gym_env import ISRSimEnv


def main():
    # 1. Create Directories for Logs and Models
    models_dir = "models/PPO"
    log_dir = "logs"

    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 2. Instantiate the Environment
    # We wrap it in a DummyVecEnv for SB3 compatibility
    env = make_vec_env(lambda: ISRSimEnv(), n_envs=1)

    # 3. Define the Model (The "Brain")
    # PPO is robust and generally works well for discrete action spaces
    model = PPO(
        "MlpPolicy",  # Multi-layer Perceptron (Standard Neural Net)
        env,
        verbose=1,
        tensorboard_log=log_dir,
        learning_rate=0.0003,
        gamma=0.99,  # Discount factor (values future rewards)
        n_steps=2048  # Steps to run before updating the network
    )

    print("--- Starting Training (This may take a while) ---")

    # 4. Train
    # 100k timesteps is a good "sanity check" starting point.
    # For "superhuman" performance, you might eventually need 1M+.
    TIMESTEPS = 100000
    model.learn(total_timesteps=TIMESTEPS)

    # 5. Save the final model
    model.save(f"{models_dir}/isr_final_model")
    print("--- Training Complete. Model Saved. ---")


if __name__ == "__main__":
    main()