from environment import Environment
from routing.epidemic import EpidemicRouter
from routing.spray import SprayAndWaitRouter
from routing.semantic import SemanticRouter
from routing.spatio_semantic import SpatioSemanticRouter
import pandas as pd
import numpy as np
import argparse
import random
import os

NUM_RUNS = 20

TRAFFIC_LEVELS = {
    "Low": 3/3600,
    "Medium": 8/3600,
    "High": 20/3600
}


def run_single_protocol(name, make_router, output_csv):
    """Run all traffic levels for a single routing protocol."""
    all_results = []

    for level_name, prob in TRAFFIC_LEVELS.items():
        print(f"\n=== [{name}] Traffic Level: {level_name} ===")

        level_results = []

        for i in range(NUM_RUNS):
            print(f"  Run {i+1}/{NUM_RUNS}", end="\r")

            env = Environment(message_gen_prob=prob)
            router = make_router(env)
            metrics = env.run(router)
            level_results.append(metrics)

        df = pd.DataFrame(level_results)
        avg = df.mean()

        print(f"\n  Avg Delivery Ratio : {avg['DeliveryRatio']*100:.1f}%")
        print(f"  Avg Critical Ratio : {avg['CriticalDeliveryRatio']*100:.1f}%")
        print(f"  Avg Critical Delay : {avg['AvgCriticalDelay']:.0f}s")
        print(f"  Avg Overhead Ratio : {avg['OverheadRatio']:.1f}")
        print(f"  Avg Buffer Drops   : {avg['BufferDrops']:.0f}")

        avg_dict = avg.to_dict()
        avg_dict["Traffic"] = level_name
        all_results.append(avg_dict)

    final_df = pd.DataFrame(all_results)
    final_df.to_csv(output_csv, index=False)
    print(f"\n✅ Saved → {output_csv}")


def run_all_experiments():
    """Run all 4 protocols and save results to plots/ directory."""
    os.makedirs("plots", exist_ok=True)

    protocols = [
        ("Epidemic",        lambda env: EpidemicRouter(),              "plots/epidemic_results.csv"),
        ("Spray & Wait",    lambda env: SprayAndWaitRouter(),          "plots/spray_results.csv"),
        ("Semantic",        lambda env: SemanticRouter(env.nodes),     "plots/semantic_results.csv"),
        ("Spatio-Semantic", lambda env: SpatioSemanticRouter(env.nodes), "plots/spatio_semantic_results.csv"),
    ]

    for name, factory, csv_path in protocols:
        print(f"\n{'='*60}")
        print(f"  PROTOCOL: {name}")
        print(f"{'='*60}")
        run_single_protocol(name, factory, csv_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DTN Routing Experiment")
    parser.add_argument("--demo", action="store_true", help="Run visual demo")
    parser.add_argument("--protocol", type=str, default="all",
                        choices=["epidemic", "spray", "semantic", "spatio", "all"],
                        help="Which protocol to benchmark (default: all)")
    args, _ = parser.parse_known_args()

    if args.demo:
        import demo
        demo.run_demo()
    elif args.protocol == "all":
        run_all_experiments()
    else:
        mapping = {
            "epidemic":  ("Epidemic",        lambda env: EpidemicRouter(),                "plots/epidemic_results.csv"),
            "spray":     ("Spray & Wait",    lambda env: SprayAndWaitRouter(),             "plots/spray_results.csv"),
            "semantic":  ("Semantic",        lambda env: SemanticRouter(env.nodes),        "plots/semantic_results.csv"),
            "spatio":    ("Spatio-Semantic", lambda env: SpatioSemanticRouter(env.nodes),  "plots/spatio_semantic_results.csv"),
        }
        name, factory, csv_path = mapping[args.protocol]
        os.makedirs("plots", exist_ok=True)
        run_single_protocol(name, factory, csv_path)