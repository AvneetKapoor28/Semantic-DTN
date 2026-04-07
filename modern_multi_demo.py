import pygame
import random
import math

from environment import Environment, SIM_DURATION
from routing.epidemic import EpidemicRouter
from routing.spray import SprayAndWaitRouter
from routing.semantic import SemanticRouter
from routing.spatio_semantic import SpatioSemanticRouter


# ---------------- CONFIG ----------------

WIDTH, HEIGHT = 1800, 800
NUM_PANELS = 4
PANEL_WIDTH = WIDTH // NUM_PANELS
FPS = 60

COLORS = {
    "bg": (10, 15, 25),
    "grid": (30, 40, 60),
    "civilian": (100, 180, 255),
    "responder": (255, 100, 100),
    "shelter": (100, 255, 120),
    "drone": (255, 220, 80),
    "text": (200, 220, 255),
    "highlight": (255, 255, 255),
    "critical": (255, 80, 80),
    "separator": (60, 80, 120),
    "gold": (255, 215, 0),
}


# ---------------- VISUALIZER ----------------

class ModernMultiVisualizer:

    def __init__(self, envs, titles):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Spatio-Semantic DTN — 4-Way Competition")

        self.font = pygame.font.SysFont("Consolas", 14)
        self.big_font = pygame.font.SysFont("Consolas", 17, bold=True)

        self.envs = envs
        self.titles = titles

    # ---------- DRAW NODE ----------

    def draw_node(self, panel_x, node, scale):

        x = panel_x + int(node.x * scale)
        y = int(node.y * scale)

        color = COLORS[node.role]

        # Highlight nodes carrying critical messages
        has_critical = any(m.critical for m in node.buffer)

        if has_critical:
            pygame.draw.circle(self.screen, COLORS["critical"], (x, y), 6)

        pygame.draw.circle(self.screen, color, (x, y), 3)

    # ---------- DRAW PANEL ----------

    def draw_panel(self, env, panel_index):

        panel_x = panel_index * PANEL_WIDTH
        scale = PANEL_WIDTH / env.area_size

        # Grid
        for i in range(0, PANEL_WIDTH, 60):
            pygame.draw.line(self.screen, COLORS["grid"],
                             (panel_x + i, 0), (panel_x + i, HEIGHT))
            pygame.draw.line(self.screen, COLORS["grid"],
                             (panel_x, i), (panel_x + PANEL_WIDTH, i))

        # Separator
        if panel_index > 0:
            pygame.draw.line(self.screen, COLORS["separator"],
                             (panel_x, 0), (panel_x, HEIGHT), 2)

        # Nodes
        for node in env.nodes:
            self.draw_node(panel_x, node, scale)

        # Title
        title = self.big_font.render(self.titles[panel_index], True, COLORS["gold"])
        self.screen.blit(title, (panel_x + 10, HEIGHT - 170))

        # Stats
        stats = env.stats

        delivery = stats["delivered"] / stats["generated"] if stats["generated"] else 0
        overhead = stats["transmissions"] / stats["delivered"] if stats["delivered"] else 0

        critical_ratio = (
            stats["critical_delivered"] / stats["critical_generated"]
            if stats["critical_generated"] else 0
        )

        avg_critical_delay = (
            sum(stats["critical_delay"]) / len(stats["critical_delay"])
            if stats["critical_delay"] else 0
        )

        lines = [
            f"Delivery Ratio : {delivery*100:.1f}%",
            f"Critical Delivery : {critical_ratio*100:.1f}%",
            f"Critical Delay : {avg_critical_delay:.0f}s",
            f"Overhead Ratio : {overhead:.1f}",
            f"Drops : {stats['drops']}"
        ]

        for i, line in enumerate(lines):
            text = self.font.render(line, True, COLORS["text"])
            self.screen.blit(text, (panel_x + 10, HEIGHT - 140 + i * 20))

        # Highlight Spatio-Semantic
        if panel_index == 3:
            tag = self.font.render("★ ENCOUNTER + ZONE + UTILITY ROUTING", True, COLORS["critical"])
            self.screen.blit(tag, (panel_x + 10, HEIGHT - 30))

    # ---------- RENDER ----------

    def render(self):
        self.screen.fill(COLORS["bg"])

        for i, env in enumerate(self.envs):
            self.draw_panel(env, i)

        pygame.display.flip()


# ---------------- MAIN DEMO ----------------

def run_scientific_demo():

    prob = 18 / 3600   # balanced traffic

    seed = 42

    envs = []
    for i in range(NUM_PANELS):
        random.seed(seed)
        env = Environment(message_gen_prob=prob)
        envs.append(env)

    routers = [
        EpidemicRouter(),
        SprayAndWaitRouter(),
        SemanticRouter(envs[2].nodes),
        SpatioSemanticRouter(envs[3].nodes),
    ]

    titles = [
        "1) EPIDEMIC",
        "2) SPRAY & WAIT",
        "3) SEMANTIC",
        "4) SPATIO-SEMANTIC",
    ]

    viz = ModernMultiVisualizer(envs, titles)

    clock = pygame.time.Clock()

    for t in range(SIM_DURATION):

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        for i in range(NUM_PANELS):
            random.seed(seed + t)

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

        viz.render()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    run_scientific_demo()