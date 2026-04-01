import argparse
from environment import Environment, SIM_DURATION
from routing.semantic import SemanticRouter
from routing.epidemic import EpidemicRouter
from routing.spray import SprayAndWaitRouter
from visualizer import Visualizer

def run_demo():
    parser = argparse.ArgumentParser(description="DTN Routing Visual Demo")
    parser.add_argument("--fps", type=int, default=120, help="Frames per second for simulation speed")
    parser.add_argument("--traffic", type=str, choices=["Low", "Medium", "High"], default="High")
    parser.add_argument("--router", type=str, choices=["semantic", "epidemic", "spray"], default="semantic", help="Choose the routing protocol")
    args, _ = parser.parse_known_args()

    # Match traffic level from main.py
    traffic_probs = {
        "Low": 3/3600,
        "Medium": 8/3600,
        "High": 20/3600
    }
    
    print(f"Starting Visual Demo with {args.traffic} Traffic Level")
    
    env = Environment(message_gen_prob=traffic_probs[args.traffic])
    if args.router == "semantic":
        router = SemanticRouter(env.nodes)
    elif args.router == "epidemic":
        router = EpidemicRouter()
    elif args.router == "spray":
        router = SprayAndWaitRouter()

    viz = Visualizer(env)
    
    # Run the equivalent of env.run() but with visualization
    for t in range(SIM_DURATION):
        env.time = t
        env.generate_messages()
        env.update_mobility()
        
        contacts = env.get_contacts()
        env.stats["time"] = env.time
        for n1, n2 in contacts:
            router.exchange(n1, n2, env.stats)
            
        env.check_delivery()
        env.expire_messages()
        
        # Visualize!
        viz.render(fps=args.fps)
        
    metrics = env.compute_metrics()
    print("\nDemo Complete! Final Metrics:")
    for key, val in metrics.items():
        if isinstance(val, float):
            print(f"  {key}: {val:.4f}")
        else:
            print(f"  {key}: {val}")

if __name__ == "__main__":
    run_demo()
