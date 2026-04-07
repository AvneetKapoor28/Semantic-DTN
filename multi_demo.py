import pygame
import sys
import math
import random
import argparse

from environment import Environment, SIM_DURATION
from routing.epidemic import EpidemicRouter
from routing.spray import SprayAndWaitRouter
from routing.semantic import SemanticRouter

class MultiVisualizer:
    def __init__(self, envs, titles, width=1200, height=550):
        pygame.init()
        self.envs = envs
        self.titles = titles
        self.num_envs = len(envs)
        
        self.width = width
        self.height = height
        
        # Split width equally
        self.panel_width = self.width // self.num_envs
        self.panel_height = self.panel_width  # square view
        
        # We need extra height for stats
        self.height = self.panel_height + 150
        
        # Use an area_size from first env (they are identical)
        self.env_area_size = self.envs[0].area_size
        self.scale = min(self.panel_width, self.panel_height) / self.env_area_size
        
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Live Multi-Routing Competition Simulator")
        self.clock = pygame.time.Clock()
        self.title_font = pygame.font.SysFont(None, 28)
        self.font = pygame.font.SysFont(None, 20)
        
        # Colors
        self.BG_COLOR = (15, 15, 20)
        self.GRID_COLOR = (30, 30, 40)
        self.TEXT_COLOR = (220, 220, 220)
        self.RANGE_COLOR = (40, 60, 80)
        self.CONTACT_COLOR = (255, 255, 100)
        self.MSG_COLOR = (0, 255, 150)
        
        self.ROLE_COLORS = {
            "civilian": (100, 150, 255),
            "responder": (255, 100, 100),
            "shelter": (100, 255, 100),
            "drone": (255, 200, 50)
        }
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
    
    def render(self, fps=60):
        self.handle_events()
        self.screen.fill(self.BG_COLOR)
        
        for idx, env in enumerate(self.envs):
            offset_x = idx * self.panel_width
            offset_y = 0
            
            # Draw panel separator
            if idx > 0:
                pygame.draw.line(self.screen, (100, 100, 100), (offset_x, 0), (offset_x, self.height), 2)
            
            # --- TACTICAL DRAWING ---
            
            # 1. Grid
            grid_spacing = 200
            for x in range(0, env.area_size, grid_spacing):
                scaled_x = offset_x + int(x * self.scale)
                pygame.draw.line(self.screen, self.GRID_COLOR, (scaled_x, 0), (scaled_x, self.panel_height))
            for y in range(0, env.area_size, grid_spacing):
                scaled_y = int(y * self.scale)
                pygame.draw.line(self.screen, self.GRID_COLOR, (offset_x, scaled_y), (offset_x + self.panel_width, scaled_y))
            
            # 2. Transmissions/Contacts (Glowing lines)
            contacts = env.get_contacts()
            for n1, n2 in contacts:
                px1 = offset_x + int(n1.x * self.scale)
                py1 = int(n1.y * self.scale)
                px2 = offset_x + int(n2.x * self.scale)
                py2 = int(n2.y * self.scale)
                
                # Check if there's actual data exchange happening (simplification: if both have buffers, it's lit)
                if len(n1.buffer) > 0 or len(n2.buffer) > 0:
                    pygame.draw.line(self.screen, self.MSG_COLOR, (px1, py1), (px2, py2), 2)
                else:
                    pygame.draw.line(self.screen, self.CONTACT_COLOR, (px1, py1), (px2, py2), 1)

            # 3. Nodes
            from environment import TRANSMISSION_RANGE
            scaled_range = int(TRANSMISSION_RANGE * self.scale)
            
            for node in env.nodes:
                px = offset_x + int(node.x * self.scale)
                py = int(node.y * self.scale)
                color = self.ROLE_COLORS.get(node.role, (200, 200, 200))
                
                # Draw Drone Transmission Range
                if node.role == "drone":
                    # Pulse effect based on time
                    pulse_radius = scaled_range + int(math.sin(env.time * 0.5) * 5)
                    pygame.draw.circle(self.screen, self.RANGE_COLOR, (px, py), pulse_radius, 1)
                    # Drone shape
                    pygame.draw.polygon(self.screen, color, [
                        (px, py-8), (px-6, py+6), (px+6, py+6)
                    ])
                elif node.role == "shelter":
                    pygame.draw.rect(self.screen, color, (px-6, py-6, 12, 12))
                else:
                    # Civilian/Responder
                    pygame.draw.circle(self.screen, color, (px, py), 4)

                # Nodes carrying thick buffers glow brighter
                if len(node.buffer) > 0:
                    glow_radius = 6 + min(len(node.buffer), 10) // 2
                    pygame.draw.circle(self.screen, (255, 255, 255), (px, py), glow_radius, 1)

            # --- STATS OVERLAY ---
            stats_y = self.panel_height + 10
            
            # Title
            title_surf = self.title_font.render(self.titles[idx], True, (255, 215, 0))
            self.screen.blit(title_surf, (offset_x + 10, stats_y))
            
            stats = env.stats
            gen = stats['generated']
            delivered = stats['delivered']
            ratio = (delivered / gen) if gen > 0 else 0.0
            
            # Calculate overhead quickly
            overhead = stats['transmissions'] / delivered if delivered > 0 else 0
            
            info_lines = [
                f"Time: {env.time}s",
                f"Delivery Ratio: {ratio*100:.1f}%",
                f"Overhead Ratio: {overhead:.1f}",
                f"Drops: {stats['drops']}",
                f"Active Msg in Buffers: {sum(len(n.buffer) for n in env.nodes)}"
            ]
            
            y_pos = stats_y + 35
            for text in info_lines:
                surface = self.font.render(text, True, self.TEXT_COLOR)
                self.screen.blit(surface, (offset_x + 10, y_pos))
                y_pos += 20
                
        pygame.display.flip()
        self.clock.tick(fps)
        
    def close(self):
        pygame.quit()

def run_multi_demo():
    parser = argparse.ArgumentParser(description="DTN Multi-Routing Protocol Live Split-Screen")
    parser.add_argument("--fps", type=int, default=120)
    parser.add_argument("--traffic", type=str, choices=["Low", "Medium", "High"], default="High")
    args, _ = parser.parse_known_args()

    traffic_probs = {
        "Low": 3/3600,
        "Medium": 8/3600,
        "High": 20/3600
    }
    prob = traffic_probs[args.traffic]
    
    print("Preparing 3 identical parallel environments perfectly synced...")
    
    envs = [
        Environment(message_gen_prob=prob),
        Environment(message_gen_prob=prob),
        Environment(message_gen_prob=prob)
    ]
    
    routers = [
        EpidemicRouter(),
        SprayAndWaitRouter(),
        SemanticRouter(envs[2].nodes)
    ]
    titles = ["Epidemic Routing", "Spray & Wait", "Semantic Routing"]
    
    viz = MultiVisualizer(envs, titles, width=1200)
    
    # Run loop
    for t in range(SIM_DURATION):
        # We enforce exactly the same RNG state at the start of each environment's turn
        # This guarantees that node generation (random destinations) and mobility (random directions)
        # happen identically across all environments despite buffer variations!
        
        for i in range(3):
            random.seed(t + 4242) # magical seed purely for locking identical states per step
            
            env = envs[i]
            router = routers[i]
            
            env.time = t
            env.generate_messages()
            env.update_mobility()
            
            contacts = env.get_contacts()
            env.stats["time"] = env.time
            
            # The router exchange handles actual routing logic and transmissions
            for n1, n2 in contacts:
                router.exchange(n1, n2, env.stats)
                
            env.check_delivery()
            env.expire_messages()
            
        viz.render(fps=args.fps)
        
    print("\n--- Final Metrics ---")
    for i, env in enumerate(envs):
        print(f"\n[{titles[i]}]")
        metrics = env.compute_metrics()
        for k, v in metrics.items():
            if isinstance(v, float):
                print(f"  {k}: {v:.4f}")
            else:
                print(f"  {k}: {v}")
                
if __name__ == "__main__":
    run_multi_demo()
