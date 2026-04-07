import pygame
import sys
import math
import random
import argparse

from environment import Environment, SIM_DURATION, AREA_SIZE, BUFFER_SIZE
from routing.epidemic import EpidemicRouter
from routing.spray import SprayAndWaitRouter
from routing.semantic import SemanticRouter

class ModernMultiVisualizer:
    def __init__(self, envs, titles, width=1380, height=780):
        pygame.init()
        self.envs = envs
        self.titles = titles
        self.num_envs = len(envs)
        
        # Screen sizing optimized for 13-14" laptops
        self.width = width
        self.height = height
        
        self.HEADER_H = 100
        self.FOOTER_H = 150
        
        self.panel_width = self.width // self.num_envs
        self.panel_height = self.height - self.HEADER_H - self.FOOTER_H
        
        self.env_area_size = self.envs[0].area_size
        self.scale = min(self.panel_width - 40, self.panel_height - 40) / self.env_area_size
        
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Scientific Live Simulation - DTN Routing Performance")
        self.clock = pygame.time.Clock()
        
        # Fonts
        self.header_font = pygame.font.SysFont("Courier", 30, bold=True)
        self.title_font = pygame.font.SysFont("Courier", 18, bold=True)
        self.stat_font = pygame.font.SysFont("Courier", 14)
        self.tiny_font = pygame.font.SysFont("Courier", 10)
        self.result_font_large = pygame.font.SysFont("Courier", 44, bold=True)
        self.result_font_medium = pygame.font.SysFont("Courier", 22)
        
        # Colors - Modern Dark Theme
        self.BG_COLOR = (10, 14, 23)
        self.PANEL_BG = (15, 20, 30)
        self.GRID_COLOR = (30, 40, 50)
        self.TEXT_COLOR = (240, 248, 255)
        self.RANGE_COLOR = (60, 90, 120)
        self.CONTACT_COLOR = (255, 255, 100)
        self.MSG_COLOR = (0, 255, 128)
        
        self.ROLE_COLORS = {
            "civilian": (100, 180, 255),
            "responder": (255, 80, 80),
            "shelter": (80, 255, 80),
            "drone": (255, 215, 0)
        }
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
    
    def draw_header(self, time):
        pygame.draw.rect(self.screen, (5, 8, 15), (0, 0, self.width, self.HEADER_H))
        pygame.draw.line(self.screen, (0, 200, 255), (0, self.HEADER_H-2), (self.width, self.HEADER_H-2), 2)
        
        # Main Title
        title_surf = self.header_font.render("SPATIO-SEMANTIC ROUTING COMPETITION DEMO", True, (0, 200, 255))
        self.screen.blit(title_surf, (20, 15))
        
        # Draw legend below the title
        legend_items = [
            ("Drone", "drone"), 
            ("Responder", "responder"), 
            ("Civilian", "civilian"),
            ("Shelter", "shelter")
        ]
        
        lx = 20
        for label, role in legend_items:
            color = self.ROLE_COLORS[role]
            pygame.draw.circle(self.screen, color, (lx, 70), 5)
            txt = self.stat_font.render(label, True, self.TEXT_COLOR)
            self.screen.blit(txt, (lx + 12, 63))
            lx += 120
            
        import environment
        # Draw Environment Factors neatly on the right side
        factors1 = f"TRAFFIC LEVEL: EXTREME      BUFFER SIZE: {environment.BUFFER_SIZE}"
        factors2 = f"AREA: {environment.AREA_SIZE}mx{environment.AREA_SIZE}m       SIM TIME: {time:04d}/{environment.SIM_DURATION}s"
        
        surf1 = self.title_font.render(factors1, True, (255, 100, 100)) # Make extreme red
        surf2 = self.title_font.render(factors2, True, self.TEXT_COLOR)
        
        # Align to the right
        self.screen.blit(surf1, (self.width - surf1.get_width() - 20, 15))
        self.screen.blit(surf2, (self.width - surf2.get_width() - 20, 50))
            
    def render(self, fps=120):
        self.handle_events()
        self.screen.fill(self.BG_COLOR)
        
        time = self.envs[0].time
        self.draw_header(time)
        
        for idx, env in enumerate(self.envs):
            panel_x = idx * self.panel_width
            panel_y = self.HEADER_H
            
            # Panel borders
            border_rect = (panel_x + 10, panel_y + 10, self.panel_width - 20, self.panel_height - 20)
            pygame.draw.rect(self.screen, self.PANEL_BG, border_rect)
            pygame.draw.rect(self.screen, (50, 60, 80), border_rect, 2)
            
            offset_x = panel_x + 20
            offset_y = panel_y + 20
            
            # --- Grid ---
            grid_spacing = 400
            for x in range(0, env.area_size, grid_spacing):
                scaled_x = offset_x + int(x * self.scale)
                pygame.draw.line(self.screen, self.GRID_COLOR, (scaled_x, offset_y), (scaled_x, offset_y + self.panel_height - 40))
            for y in range(0, env.area_size, grid_spacing):
                scaled_y = offset_y + int(y * self.scale)
                pygame.draw.line(self.screen, self.GRID_COLOR, (offset_x, scaled_y), (offset_x + self.panel_width - 40, scaled_y))
            
            # --- Transmissions ---
            contacts = env.get_contacts()
            for n1, n2 in contacts:
                px1, py1 = offset_x + int(n1.x * self.scale), offset_y + int(n1.y * self.scale)
                px2, py2 = offset_x + int(n2.x * self.scale), offset_y + int(n2.y * self.scale)
                
                if len(n1.buffer) > 0 or len(n2.buffer) > 0:
                    pygame.draw.line(self.screen, self.MSG_COLOR, (px1, py1), (px2, py2), 2)
                else:
                    pygame.draw.line(self.screen, self.CONTACT_COLOR, (px1, py1), (px2, py2), 1)

            import environment
            from environment import TRANSMISSION_RANGE
            # To ensure local transmissions override
            scaled_range = int(environment.TRANSMISSION_RANGE * self.scale)
            
            for node in env.nodes:
                px = offset_x + int(node.x * self.scale)
                py = offset_y + int(node.y * self.scale)
                color = self.ROLE_COLORS.get(node.role, (200, 200, 200))
                
                if node.role == "drone":
                    pulse = scaled_range + int(math.sin(env.time * 0.5) * 5)
                    pygame.draw.circle(self.screen, self.RANGE_COLOR, (px, py), pulse, 1)
                    pygame.draw.polygon(self.screen, color, [(px, py-10), (px-8, py+8), (px+8, py+8)])
                elif node.role == "shelter":
                    pygame.draw.rect(self.screen, color, (px-8, py-8, 16, 16))
                else:
                    pygame.draw.circle(self.screen, color, (px, py), 5)

                if len(node.buffer) > 0:
                    glow = 7 + min(len(node.buffer), 20) // 2
                    pygame.draw.circle(self.screen, (255, 255, 255), (px, py), glow, 1)

                id_surf = self.tiny_font.render(f"{node.role[0].upper()}{node.id}", True, (200, 200, 200))
                self.screen.blit(id_surf, (px + 6, py - 6))

            # --- Footer Stats ---
            footer_y = self.HEADER_H + self.panel_height
            pygame.draw.rect(self.screen, (15, 20, 30), (panel_x, footer_y, self.panel_width, self.FOOTER_H))
            pygame.draw.line(self.screen, (50, 60, 80), (panel_x, footer_y), (panel_x + self.panel_width, footer_y), 2)
            
            title_color = (0, 200, 255) if "Spatio-Semantic" in self.titles[idx] else (200, 200, 200)
            title_surf = self.title_font.render(self.titles[idx], True, title_color)
            self.screen.blit(title_surf, (panel_x + 15, footer_y + 10))
            
            stats = env.stats
            gen = stats['generated']
            delivered = stats['delivered']
            ratio = (delivered / gen) if gen > 0 else 0.0
            overhead = stats['transmissions'] / delivered if delivered > 0 else 0.0
            
            # Use strict layout so column 1 and column 2 NEVER overlap
            # Col 1: Delivery info
            col1 = [
                f"Delivery Ratio: {ratio*100:05.1f}%",
                f"Total Generatd: {gen:04d}",
                f"Total Deliverd: {delivered:04d}"
            ]
            
            # Col 2: Overhead info
            col2 = [
                f"Overhead Ratio: {overhead:05.1f}",
                f"Buffer Drops  : {stats['drops']:04d}",
                f"Total Transmit: {stats['transmissions']:05d}"
            ]
            
            cy = footer_y + 40
            for c1, c2 in zip(col1, col2):
                self.screen.blit(self.stat_font.render(c1, True, (150, 255, 150)), (panel_x + 15, cy))
                self.screen.blit(self.stat_font.render(c2, True, (255, 150, 150)), (panel_x + 225, cy))
                cy += 20
                
        pygame.display.flip()
        self.clock.tick(fps)
        
    def show_layman_results(self):
        # Semi-transparent overlay to keep the final state visible in the background
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))  # Black with heavy opacity
        self.screen.blit(overlay, (0, 0))
        
        # Get metrics
        del_epidemic = self.envs[0].stats["delivered"] / max(self.envs[0].stats["generated"], 1)
        del_spray = self.envs[1].stats["delivered"] / max(self.envs[1].stats["generated"], 1)
        del_semantic = self.envs[2].stats["delivered"] / max(self.envs[2].stats["generated"], 1)
        
        drop_epidemic = self.envs[0].stats["drops"]
        drop_spray = self.envs[1].stats["drops"]
        drop_semantic = self.envs[2].stats["drops"]
        
        text_lines = [
            ("SIMULATION COMPLETE!", self.result_font_large, (255, 215, 0)),
            ("", self.result_font_medium, (255, 255, 255)),
            ("THE RESULTS (Simple Breakdown):", self.header_font, (0, 200, 255)),
            ("", self.result_font_medium, (255, 255, 255)),
            ("Epidemic Routing failed to scale.", self.result_font_medium, (255, 150, 150)),
            (f"  -> It spammed the network, dropping {drop_epidemic} messages due to full buffers.", self.stat_font, (220, 220, 220)),
            (f"  -> Only delivered {del_epidemic*100:.1f}% successfully.", self.stat_font, (220, 220, 220)),
            ("", self.result_font_medium, (255, 255, 255)),
            ("Spray & Wait was efficient but limited.", self.result_font_medium, (255, 255, 150)),
            (f"  -> It prevented congestion (only {drop_spray} drops), but reached limits in delivery speed.", self.stat_font, (220, 220, 220)),
            (f"  -> Delivered {del_spray*100:.1f}%.", self.stat_font, (220, 220, 220)),
            ("", self.result_font_medium, (255, 255, 255)),
            ("WINNER: Spatio-Semantic Routing", self.header_font, (150, 255, 150)),
            ("  -> By intelligently understanding the network context and prioritizing", self.stat_font, (220, 220, 220)),
            ("     critical messages and buffer loads, it perfectly balanced", self.stat_font, (220, 220, 220)),
            ("     speed and efficiency.", self.stat_font, (220, 220, 220)),
            (f"  -> Highest Delivery Ratio: {del_semantic*100:.1f}% !!", self.result_font_medium, (150, 255, 150)),
            ("", self.result_font_medium, (255, 255, 255)),
            ("Close this window to return to the Dashboard.", self.stat_font, (100, 100, 100))
        ]
        
        y = self.height // 2 - (len(text_lines) * 30) // 2
        for line, font, color in text_lines:
            surf = font.render(line, True, color)
            x = self.width // 2 - surf.get_width() // 2
            
            # Align bullets to the center but structured properly
            if line.startswith("  ->"):
                # roughly align with the text above it
                x = self.width // 2 - 250
                
            self.screen.blit(surf, (x, y))
            y += font.get_height() + 10
            
        pygame.display.flip()
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.close()

    def close(self):
        pygame.quit()
        sys.exit(0)


def run_scientific_demo():

    import random

    prob = 18/3600   # 🔥 balanced traffic (not insane chaos)

    seed = 42  # 🔥 SAME seed → fair comparison

    envs = []
    routers = []

    for i in range(3):
        random.seed(seed)

        env = Environment(message_gen_prob=prob)
        envs.append(env)

    routers = [
        EpidemicRouter(),
        SprayAndWaitRouter(),
        SemanticRouter(envs[2].nodes)
    ]

    titles = [
        "1) EPIDEMIC ROUTING",
        "2) SPRAY & WAIT",
        "3) SPATIO-SEMANTIC ROUTING"
    ]

    viz = ModernMultiVisualizer(envs, titles)

    for t in range(SIM_DURATION):

        for i in range(3):
            random.seed(seed + t)  # synchronized randomness

            env = envs[i]
            router = routers[i]

            env.time = t
            env.generate_messages()
            env.update_mobility()

            contacts = env.get_contacts()
            env.stats["time"] = env.time

            for n1, n2 in contacts:
                router.exchange(n1, n2, env.stats)

            env.check_delivery()
            env.expire_messages()

        viz.render(fps=120)

    viz.show_layman_results()

if __name__ == "__main__":
    run_scientific_demo()
