from environment import Environment
from routing.epidemic import EpidemicRouter
import pandas as pd

NUM_RUNS = 10   # change to 20 later for paper


def run_experiments():

    results = []

    for i in range(NUM_RUNS):
        print(f"\nRunning Simulation {i+1}/{NUM_RUNS}")

        env = Environment()
        router = EpidemicRouter()

        metrics = env.run(router)
        results.append(metrics)

        print(metrics)

    df = pd.DataFrame(results)
    print("\n===== Average Results =====")
    print(df.mean())

    df.to_csv("epidemic_results.csv", index=False)


if __name__ == "__main__":
    run_experiments()