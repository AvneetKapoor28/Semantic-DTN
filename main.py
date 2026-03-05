from environment import Environment
from routing.epidemic import EpidemicRouter
from routing.spray import SprayAndWaitRouter
import pandas as pd
import numpy as np

NUM_RUNS = 20

TRAFFIC_LEVELS = {
    "Low": 3/3600,
    "Medium": 8/3600,
    "High": 20/3600
}


def run_experiments():

    all_results = []

    for level_name, prob in TRAFFIC_LEVELS.items():

        print(f"\n=== Traffic Level: {level_name} ===")

        level_results = []

        for i in range(NUM_RUNS):
            print(f"Run {i+1}/{NUM_RUNS}")

            env = Environment(message_gen_prob=prob)
            router = SprayAndWaitRouter()

            metrics = env.run(router)
            level_results.append(metrics)

        df = pd.DataFrame(level_results)
        avg = df.mean()
        std = df.std()

        print("\nAverage:")
        print(avg)

        print("\nStd Dev:")
        print(std)

        avg_dict = avg.to_dict()
        avg_dict["Traffic"] = level_name
        all_results.append(avg_dict)

    final_df = pd.DataFrame(all_results)
    final_df.to_csv("spray_and_wait_traffic_results.csv", index=False)


if __name__ == "__main__":
    run_experiments()