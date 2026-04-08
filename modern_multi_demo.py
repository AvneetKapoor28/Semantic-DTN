"""
4-Panel DTN Competition Visualization
======================================
Side-by-side comparison of Epidemic, Spray & Wait,
Semantic, and Spatio-Semantic routing protocols.
"""

import pygame
import random
import math
import sys

from environment import Environment, SIM_DURATION, TRANSMISSION_RANGE, AREA_SIZE
from routing.epidemic import EpidemicRouter
from routing.spray import SprayAndWaitRouter
from routing.semantic import SemanticRouter
from routing.spatio_semantic import SpatioSemanticRouter


# ═══════════════ LAYOUT ═══════════════

NUM_PANELS = 4
PANEL_W = 340
SIM_H = 340                          # simulation area per panel
STATS_H = 200                        # stats area per panel
WIDTH = PANEL_W * NUM_PANELS          # 1360
HEIGHT = SIM_H + STATS_H             # 540
FPS = 60


# ═══════════════ PALETTE ═══════════════

class C:
    BG         = (8, 12, 21)
    GRID       = (20, 28, 42)
    SEP        = (35, 50, 75)
    TEXT       = (170, 185, 210)
    DIM        = (90, 105, 130)
    BRIGHT     = (235, 240, 250)
    GOLD       = (255, 200, 60)
    RED        = (255, 65, 75)
    GREEN      = (50, 215, 115)
    TX         = (55, 240, 145)
    CONTACT    = (35, 60, 90)
    DRONE_RNG  = (50, 85, 140)
    BAR_BG     = (22, 32, 50)

    ROLE = {
        "civilian":  (75, 140, 245),
        "responder": (245, 85, 85),
        "shelter":   (75, 220, 105),
        "drone":     (245, 205, 55),
    }
    ACCENT = [
        (245, 75, 75),     # Epidemic — red
        (75, 200, 150),    # Spray — teal
        (150, 95, 245),    # Semantic — purple
        (55, 170, 245),    # Spatio — blue
    ]


# ═══════════════ VISUALIZER ═══════════════

class Visualizer:

    def __init__(self, envs, titles):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("DTN Routing — 4-Way Competition")
        self.clock = pygame.time.Clock()

        self.font_sm  = pygame.font.SysFont("Menlo", 10)
        self.font_md  = pygame.font.SysFont("Menlo", 12)
        self.font_lg  = pygame.font.SysFont("Menlo", 14, bold=True)
        self.font_hdr = pygame.font.SysFont("Menlo", 9)

        self.envs = envs
        self.titles = titles
        self.scale = PANEL_W / AREA_SIZE

    def _bar(self, x, y, w, h, val, mx, color, label, fmt):
        pygame.draw.rect(self.screen, C.BAR_BG, (x, y, w, h), border_radius=2)
        fw = max(0, min(int(w * val / mx), w))
        if fw > 0:
            pygame.draw.rect(self.screen, color, (x, y, fw, h), border_radius=2)
        pygame.draw.rect(self.screen, color, (x, y, w, h), 1, border_radius=2)
        self.screen.blit(self.font_hdr.render(label, True, C.DIM), (x, y - 12))
        self.screen.blit(self.font_md.render(fmt.format(val), True, C.BRIGHT), (x + w + 4, y - 1))

    def render(self, t):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit(); sys.exit(0)

        self.screen.fill(C.BG)

        # Progress bar
        prog = int(WIDTH * t / SIM_DURATION)
        pygame.draw.rect(self.screen, (30, 42, 65), (0, 0, WIDTH, 2))
        pygame.draw.rect(self.screen, C.GOLD, (0, 0, prog, 2))

        for idx, env in enumerate(self.envs):
            px = idx * PANEL_W
            accent = C.ACCENT[idx]

            # Vertical separator
            if idx > 0:
                pygame.draw.line(self.screen, C.SEP, (px, 0), (px, HEIGHT), 1)

            # Grid
            step = int(AREA_SIZE / 6 * self.scale)
            for i in range(1, 6):
                gx = px + i * step
                pygame.draw.line(self.screen, C.GRID, (gx, 3), (gx, SIM_H))
                gy = i * step
                if gy < SIM_H:
                    pygame.draw.line(self.screen, C.GRID, (px, gy), (px + PANEL_W, gy))

            # Contacts
            for n1, n2 in env.get_contacts():
                x1, y1 = px + int(n1.x * self.scale), int(n1.y * self.scale)
                x2, y2 = px + int(n2.x * self.scale), int(n2.y * self.scale)
                if y1 < SIM_H and y2 < SIM_H:
                    c = C.TX if (n1.buffer or n2.buffer) else C.CONTACT
                    pygame.draw.line(self.screen, c, (x1, y1), (x2, y2), 1)

            # Nodes
            sr = int(TRANSMISSION_RANGE * self.scale)
            for node in env.nodes:
                nx, ny = px + int(node.x * self.scale), int(node.y * self.scale)
                if ny >= SIM_H:
                    continue
                col = C.ROLE.get(node.role, (180, 180, 180))

                if node.role == "drone":
                    pulse = sr + int(math.sin(t * 0.08) * 2)
                    s = pygame.Surface((pulse*2, pulse*2), pygame.SRCALPHA)
                    pygame.draw.circle(s, (*C.DRONE_RNG, 20), (pulse, pulse), pulse, 1)
                    self.screen.blit(s, (nx - pulse, ny - pulse))
                    pygame.draw.polygon(self.screen, col, [(nx, ny-5), (nx-4, ny+4), (nx+4, ny+4)])
                elif node.role == "shelter":
                    pygame.draw.rect(self.screen, col, (nx-4, ny-4, 8, 8))
                elif node.role == "responder":
                    pygame.draw.circle(self.screen, col, (nx, ny), 3)
                else:
                    pygame.draw.circle(self.screen, col, (nx, ny), 2)

                # Critical halo
                if any(m.critical for m in node.buffer):
                    s2 = pygame.Surface((12, 12), pygame.SRCALPHA)
                    pygame.draw.circle(s2, (255, 45, 45, 45), (6, 6), 6)
                    self.screen.blit(s2, (nx - 6, ny - 6))

                # Buffer load ring
                if len(node.buffer) > 5:
                    ld = min(len(node.buffer) / 30, 1)
                    pygame.draw.circle(self.screen, (int(80+170*ld), int(195-145*ld), 75), (nx, ny), int(4+ld*3), 1)

            # ──── STATS AREA ────
            sy = SIM_H + 2
            pygame.draw.line(self.screen, C.SEP, (px, SIM_H), (px + PANEL_W, SIM_H), 1)
            pygame.draw.rect(self.screen, accent, (px, sy, PANEL_W, 2))

            self.screen.blit(self.font_lg.render(self.titles[idx], True, accent), (px + 8, sy + 6))

            s = env.stats
            gen = max(s["generated"], 1)
            dr  = s["delivered"] / gen * 100
            cg  = max(s["critical_generated"], 1)
            cdr = s["critical_delivered"] / cg * 100
            oh  = s["transmissions"] / max(s["delivered"], 1)
            cd  = sum(s["critical_delay"]) / max(len(s["critical_delay"]), 1)

            bx, bw, bh = px + 10, PANEL_W - 70, 11

            y = sy + 28
            self._bar(bx, y, bw, bh, dr, 100, C.GREEN, "DELIVERY", "{:.1f}%")
            y += 28
            self._bar(bx, y, bw, bh, cdr, 100, C.RED, "CRITICAL", "{:.1f}%")
            y += 28
            dn = min(cd / 2000, 1)
            self._bar(bx, y, bw, bh, cd, 2000, (int(50+200*dn), int(195-145*dn), int(115-75*dn)), "CRIT DELAY", "{:.0f}s")

            y += 24
            for line in [f"Overhead: {oh:.1f}x", f"Drops: {s['drops']:,}", f"t={t}/{SIM_DURATION}"]:
                self.screen.blit(self.font_sm.render(line, True, C.DIM), (bx, y))
                y += 13

            if idx == 3 and t > 300:
                self.screen.blit(self.font_sm.render("★ ENCOUNTER+ZONE+UTILITY", True, C.GOLD), (px + 8, HEIGHT - 16))

        pygame.display.flip()
        self.clock.tick(FPS)


# ═══════════════ MAIN ═══════════════

def run():
    prob = 10 / 3600
    seed = 42

    envs = []
    for _ in range(NUM_PANELS):
        random.seed(seed)
        envs.append(Environment(message_gen_prob=prob))

    routers = [
        EpidemicRouter(),
        SprayAndWaitRouter(),
        SemanticRouter(envs[2].nodes),
        SpatioSemanticRouter(envs[3].nodes),
    ]
    titles = ["EPIDEMIC", "SPRAY & WAIT", "SEMANTIC", "SPATIO-SEMANTIC"]

    viz = Visualizer(envs, titles)

    for t in range(SIM_DURATION):
        for i in range(NUM_PANELS):
            random.seed(seed + t)
            env = envs[i]
            env.time = t
            env.generate_messages()
            env.update_mobility()
            contacts = env.get_contacts()
            env.stats["time"] = t
            for n1, n2 in contacts:
                routers[i].exchange(n1, n2, env.stats)
            env.check_delivery()
            env.expire_messages()

        viz.render(t)

    # Print final results
    print("\n── FINAL ──")
    for i, env in enumerate(envs):
        m = env.compute_metrics()
        print(f"\n[{titles[i]}]")
        for k, v in m.items():
            print(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")

    # Hold until close
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit(); return
        pygame.time.Clock().tick(10)


if __name__ == "__main__":
    run()