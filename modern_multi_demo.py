"""
Modern 4-Panel DTN Competition Visualization
=============================================
Premium PyGame visualization comparing all 4 routing protocols
side-by-side with rich animations and real-time metrics.
"""

import pygame
import random
import math
import sys
import colorsys

from environment import Environment, SIM_DURATION, TRANSMISSION_RANGE, AREA_SIZE
from routing.epidemic import EpidemicRouter
from routing.spray import SprayAndWaitRouter
from routing.semantic import SemanticRouter
from routing.spatio_semantic import SpatioSemanticRouter


# ════════════════════ CONFIG ════════════════════

WIDTH, HEIGHT = 1800, 920
NUM_PANELS = 4
PANEL_WIDTH = WIDTH // NUM_PANELS
SIM_AREA_HEIGHT = 540          # upper area for simulation
STATS_HEIGHT = HEIGHT - SIM_AREA_HEIGHT  # lower area for stats
FPS = 60

# ════════════════════ PALETTE ════════════════════

class C:
    BG              = (8, 12, 21)
    PANEL_BG        = (12, 16, 28)
    GRID            = (22, 30, 48)
    SEPARATOR       = (40, 55, 85)
    TEXT            = (180, 195, 220)
    TEXT_DIM        = (100, 115, 140)
    TEXT_BRIGHT     = (240, 245, 255)
    GOLD            = (255, 200, 60)
    CRITICAL_RED    = (255, 65, 75)
    SUCCESS_GREEN   = (50, 220, 120)
    DRONE_YELLOW    = (255, 210, 60)
    CIVILIAN_BLUE   = (80, 150, 255)
    RESPONDER_RED   = (255, 90, 90)
    SHELTER_GREEN   = (80, 230, 110)
    TRANSMISSION    = (60, 255, 160)
    CONTACT_DIM     = (40, 70, 100)
    HALO_CRITICAL   = (255, 50, 50, 80)
    DRONE_RANGE     = (60, 100, 160)
    BAR_BG          = (25, 35, 55)

    # Per-algorithm accent colors
    ACCENTS = [
        (255, 80, 80),    # Epidemic — red
        (80, 210, 160),   # Spray — teal
        (160, 100, 255),  # Semantic — purple
        (60, 180, 255),   # Spatio-Semantic — bright blue
    ]


# ════════════════════ PARTICLES ════════════════════

class Particle:
    __slots__ = ['x', 'y', 'vx', 'vy', 'life', 'max_life', 'color', 'size']

    def __init__(self, x, y, color, speed=1.5):
        angle = random.uniform(0, math.tau)
        v = random.uniform(0.3, speed)
        self.x = x
        self.y = y
        self.vx = math.cos(angle) * v
        self.vy = math.sin(angle) * v
        self.life = random.randint(10, 25)
        self.max_life = self.life
        self.color = color
        self.size = random.uniform(1.0, 2.5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        return self.life > 0

    def draw(self, surface):
        alpha = self.life / self.max_life
        r = int(self.color[0] * alpha)
        g = int(self.color[1] * alpha)
        b = int(self.color[2] * alpha)
        sz = max(1, int(self.size * alpha))
        pygame.draw.circle(surface, (r, g, b), (int(self.x), int(self.y)), sz)


# ════════════════════ VISUALIZER ════════════════════

class PremiumVisualizer:

    def __init__(self, envs, titles, routers):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("DTN Routing Protocol Competition — Spatio-Semantic vs Baselines")

        # Fonts
        self.font_sm   = pygame.font.SysFont("Menlo", 12)
        self.font_md   = pygame.font.SysFont("Menlo", 14)
        self.font_lg   = pygame.font.SysFont("Menlo", 18, bold=True)
        self.font_xl   = pygame.font.SysFont("Menlo", 22, bold=True)
        self.font_hdr  = pygame.font.SysFont("Menlo", 11)

        self.envs = envs
        self.titles = titles
        self.routers = routers
        self.particles = [[] for _ in range(NUM_PANELS)]
        self.delivery_flashes = [[] for _ in range(NUM_PANELS)]  # (x, y, timer)
        self.prev_delivered = [0] * NUM_PANELS

        # Scale
        self.scale = PANEL_WIDTH / AREA_SIZE

    # ─────────── EVENT HANDLING ───────────

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit(0)

    # ─────────── DRAW GRID ───────────

    def draw_grid(self, panel_x):
        spacing = int(AREA_SIZE / 10 * self.scale)
        for i in range(1, 10):
            x = panel_x + i * spacing
            pygame.draw.line(self.screen, C.GRID, (x, 0), (x, SIM_AREA_HEIGHT), 1)
        for i in range(1, 10):
            y = i * spacing
            if y < SIM_AREA_HEIGHT:
                pygame.draw.line(self.screen, C.GRID, (panel_x, y), (panel_x + PANEL_WIDTH, y), 1)

    # ─────────── DRAW NODES ───────────

    def draw_nodes(self, env, panel_x, panel_idx, t):
        for node in env.nodes:
            x = panel_x + int(node.x * self.scale)
            y = int(node.y * self.scale)

            if y >= SIM_AREA_HEIGHT:
                continue

            # Node type rendering
            if node.role == "drone":
                # Pulsing range circle
                pulse = int(math.sin(t * 0.08) * 3)
                r = int(TRANSMISSION_RANGE * self.scale) + pulse
                s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*C.DRONE_RANGE, 25), (r, r), r, 2)
                self.screen.blit(s, (x - r, y - r))

                # Triangle drone shape
                pts = [(x, y-7), (x-5, y+5), (x+5, y+5)]
                pygame.draw.polygon(self.screen, C.DRONE_YELLOW, pts)
                pygame.draw.polygon(self.screen, (255, 240, 150), pts, 1)

            elif node.role == "shelter":
                pygame.draw.rect(self.screen, C.SHELTER_GREEN, (x-5, y-5, 10, 10))
                pygame.draw.rect(self.screen, (150, 255, 180), (x-5, y-5, 10, 10), 1)

            elif node.role == "responder":
                pygame.draw.circle(self.screen, C.RESPONDER_RED, (x, y), 4)
                # Speed trail
                if node.destination:
                    dx = node.destination[0] - node.x
                    dy = node.destination[1] - node.y
                    d = math.hypot(dx, dy)
                    if d > 0:
                        tx = x - int((dx/d) * 8)
                        ty = y - int((dy/d) * 8)
                        pygame.draw.line(self.screen, (255, 100, 100, 60), (x, y), (tx, ty), 1)

            else:  # civilian
                pygame.draw.circle(self.screen, C.CIVILIAN_BLUE, (x, y), 3)

            # Critical message halo
            has_critical = any(m.critical for m in node.buffer)
            if has_critical:
                s = pygame.Surface((18, 18), pygame.SRCALPHA)
                pygame.draw.circle(s, (255, 50, 50, 50), (9, 9), 9)
                self.screen.blit(s, (x - 9, y - 9))

            # Buffer load indicator (subtle ring)
            if len(node.buffer) > 5:
                load = min(len(node.buffer) / 30.0, 1.0)
                ring_color = (
                    int(80 + 175 * load),
                    int(200 - 150 * load),
                    int(80)
                )
                pygame.draw.circle(self.screen, ring_color, (x, y), int(6 + load * 4), 1)

    # ─────────── DRAW CONTACTS ───────────

    def draw_contacts(self, env, panel_x, panel_idx):
        contacts = env.get_contacts()
        for n1, n2 in contacts:
            x1 = panel_x + int(n1.x * self.scale)
            y1 = int(n1.y * self.scale)
            x2 = panel_x + int(n2.x * self.scale)
            y2 = int(n2.y * self.scale)

            if y1 >= SIM_AREA_HEIGHT or y2 >= SIM_AREA_HEIGHT:
                continue

            if len(n1.buffer) > 0 and len(n2.buffer) > 0:
                pygame.draw.line(self.screen, C.TRANSMISSION, (x1, y1), (x2, y2), 1)
                # Spawn particles at midpoint occasionally
                if random.random() < 0.06:
                    mx, my = (x1+x2)//2, (y1+y2)//2
                    self.particles[panel_idx].append(
                        Particle(mx, my, C.TRANSMISSION, speed=1.0)
                    )
            else:
                pygame.draw.line(self.screen, C.CONTACT_DIM, (x1, y1), (x2, y2), 1)

    # ─────────── DRAW DELIVERY FLASHES ───────────

    def check_deliveries(self, env, panel_idx):
        current = env.stats["delivered"]
        if current > self.prev_delivered[panel_idx]:
            # New deliveries happened — flash at random delivered nodes
            for node in env.nodes:
                for msg in node.buffer:
                    if node.id == msg.destination:
                        x = panel_idx * PANEL_WIDTH + int(node.x * self.scale)
                        y = int(node.y * self.scale)
                        if y < SIM_AREA_HEIGHT:
                            self.delivery_flashes[panel_idx].append([x, y, 20])
                            # Spawn green success particles
                            for _ in range(3):
                                self.particles[panel_idx].append(
                                    Particle(x, y, C.SUCCESS_GREEN, speed=2.0)
                                )
                        break
            self.prev_delivered[panel_idx] = current

    def draw_delivery_flashes(self, panel_idx):
        alive = []
        for flash in self.delivery_flashes[panel_idx]:
            x, y, timer = flash
            alpha = int(255 * (timer / 20))
            radius = int(15 - (timer / 20) * 10)
            s = pygame.Surface((radius*2+2, radius*2+2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*C.SUCCESS_GREEN, alpha), (radius+1, radius+1), radius, 2)
            self.screen.blit(s, (x - radius - 1, y - radius - 1))
            flash[2] -= 1
            if flash[2] > 0:
                alive.append(flash)
        self.delivery_flashes[panel_idx] = alive

    # ─────────── DRAW PARTICLES ───────────

    def draw_particles(self, panel_idx):
        alive = []
        for p in self.particles[panel_idx]:
            if p.update():
                p.draw(self.screen)
                alive.append(p)
        self.particles[panel_idx] = alive[:200]  # cap

    # ─────────── DRAW STAT BAR ───────────

    def _draw_bar(self, x, y, w, h, value, max_val, color, label, fmt="{:.1f}%"):
        # Background
        pygame.draw.rect(self.screen, C.BAR_BG, (x, y, w, h), border_radius=3)
        # Fill
        fill_w = max(0, min(int(w * (value / max_val)), w))
        if fill_w > 0:
            pygame.draw.rect(self.screen, color, (x, y, fill_w, h), border_radius=3)
        # Border
        pygame.draw.rect(self.screen, (*color, 120), (x, y, w, h), 1, border_radius=3)
        # Label
        lbl = self.font_hdr.render(label, True, C.TEXT_DIM)
        self.screen.blit(lbl, (x, y - 14))
        # Value
        val_text = fmt.format(value)
        val_surf = self.font_md.render(val_text, True, C.TEXT_BRIGHT)
        self.screen.blit(val_surf, (x + w + 6, y - 1))

    # ─────────── DRAW STATS PANEL ───────────

    def draw_stats(self, env, panel_idx, t):
        panel_x = panel_idx * PANEL_WIDTH
        stats_y = SIM_AREA_HEIGHT + 5

        accent = C.ACCENTS[panel_idx]

        # Separator line
        pygame.draw.line(self.screen, C.SEPARATOR,
                         (panel_x, SIM_AREA_HEIGHT),
                         (panel_x + PANEL_WIDTH, SIM_AREA_HEIGHT), 2)

        # Vertical separator
        if panel_idx > 0:
            pygame.draw.line(self.screen, C.SEPARATOR,
                             (panel_x, 0), (panel_x, HEIGHT), 1)

        # Panel accent bar
        pygame.draw.rect(self.screen, accent, (panel_x, stats_y, PANEL_WIDTH, 3))

        # Title
        title = self.font_lg.render(self.titles[panel_idx], True, accent)
        self.screen.blit(title, (panel_x + 12, stats_y + 10))

        # Algorithm number badge
        badge_text = str(panel_idx + 1)
        badge = self.font_xl.render(badge_text, True, C.BG)
        bw, bh = badge.get_size()
        badge_rect = pygame.Rect(panel_x + PANEL_WIDTH - bw - 22, stats_y + 8, bw + 14, bh + 4)
        pygame.draw.rect(self.screen, accent, badge_rect, border_radius=6)
        self.screen.blit(badge, (badge_rect.x + 7, badge_rect.y + 2))

        # Compute metrics
        s = env.stats
        gen = max(s["generated"], 1)
        delivered = s["delivered"]
        dr = (delivered / gen) * 100
        cg = max(s["critical_generated"], 1)
        cd = s["critical_delivered"]
        cdr = (cd / cg) * 100
        overhead = s["transmissions"] / max(delivered, 1)
        c_delay = sum(s["critical_delay"]) / max(len(s["critical_delay"]), 1)

        bar_x = panel_x + 14
        bar_w = PANEL_WIDTH - 85
        bar_h = 14

        # Delivery Ratio bar
        y = stats_y + 44
        self._draw_bar(bar_x, y, bar_w, bar_h, dr, 100,
                       C.SUCCESS_GREEN, "DELIVERY RATIO", "{:.1f}%")

        # Critical Delivery bar
        y += 36
        self._draw_bar(bar_x, y, bar_w, bar_h, cdr, 100,
                       C.CRITICAL_RED, "CRITICAL DELIVERY", "{:.1f}%")

        # Critical Delay bar (inverted — lower is better)
        y += 36
        delay_norm = min(c_delay / 2000, 1.0)
        delay_color = (
            int(50 + 200 * delay_norm),
            int(200 - 150 * delay_norm),
            int(120 - 80 * delay_norm)
        )
        self._draw_bar(bar_x, y, bar_w, bar_h, c_delay, 2000,
                       delay_color, "CRITICAL DELAY", "{:.0f}s")

        # Text stats
        y += 40
        lines = [
            f"Overhead: {overhead:.1f}x",
            f"Drops: {s['drops']:,}",
            f"Active: {sum(len(n.buffer) for n in env.nodes)}",
            f"Time: {t}/{SIM_DURATION}",
        ]
        for line in lines:
            surf = self.font_sm.render(line, True, C.TEXT_DIM)
            self.screen.blit(surf, (bar_x, y))
            y += 16

        # Winner crown on spatio-semantic
        if panel_idx == 3 and t > 500:
            crown = self.font_sm.render("★ ENCOUNTER + ZONE + UTILITY GATED", True, C.GOLD)
            self.screen.blit(crown, (panel_x + 12, HEIGHT - 22))

    # ─────────── DRAW HEADER ───────────

    def draw_header(self, t):
        # Progress bar at very top
        progress = t / SIM_DURATION
        bar_w = int(WIDTH * progress)
        pygame.draw.rect(self.screen, (40, 60, 100), (0, 0, WIDTH, 2))
        pygame.draw.rect(self.screen, C.GOLD, (0, 0, bar_w, 2))

    # ─────────── MAIN RENDER ───────────

    def render(self, t):
        self.handle_events()
        self.screen.fill(C.BG)

        self.draw_header(t)

        for i, env in enumerate(self.envs):
            self.draw_grid(i * PANEL_WIDTH)
            self.draw_contacts(env, i * PANEL_WIDTH, i)
            self.draw_nodes(env, i * PANEL_WIDTH, i, t)
            self.check_deliveries(env, i)
            self.draw_delivery_flashes(i)
            self.draw_particles(i)
            self.draw_stats(env, i, t)

        pygame.display.flip()


# ════════════════════ MAIN ════════════════════

def run_scientific_demo():

    prob = 10 / 3600  # medium-high traffic

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
        "EPIDEMIC",
        "SPRAY & WAIT",
        "SEMANTIC",
        "SPATIO-SEMANTIC",
    ]

    viz = PremiumVisualizer(envs, titles, routers)
    clock = pygame.time.Clock()

    for t in range(SIM_DURATION):

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

        viz.render(t)
        clock.tick(FPS)

    # Hold final frame
    print("\n── FINAL RESULTS ──")
    for i, env in enumerate(envs):
        m = env.compute_metrics()
        print(f"\n[{titles[i]}]")
        for k, v in m.items():
            if isinstance(v, float):
                print(f"  {k}: {v:.4f}")
            else:
                print(f"  {k}: {v}")

    # Wait for close
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                return
        clock.tick(10)


if __name__ == "__main__":
    run_scientific_demo()