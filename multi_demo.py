import pygame
import sys
import math
import random
import argparse

from environment import Environment, SIM_DURATION, TRANSMISSION_RANGE, AREA_SIZE
from routing.epidemic import EpidemicRouter
from routing.spray import SprayAndWaitRouter
from routing.semantic import SemanticRouter
from routing.spatio_semantic import SpatioSemanticRouter


# ═══════════════════ PALETTE ═══════════════════

class C:
    BG           = (8, 12, 21)
    GRID         = (22, 30, 48)
    SEP          = (40, 55, 85)
    TEXT         = (180, 195, 220)
    TEXT_DIM     = (100, 115, 140)
    TEXT_BRIGHT  = (240, 245, 255)
    GOLD         = (255, 200, 60)
    RED          = (255, 65, 75)
    GREEN        = (50, 220, 120)
    TX_LINE      = (60, 255, 160)
    CONTACT      = (40, 70, 100)
    DRONE_RANGE  = (60, 100, 160)
    BAR_BG       = (25, 35, 55)

    ROLE = {
        "civilian":  (80, 150, 255),
        "responder": (255, 90, 90),
        "shelter":   (80, 230, 110),
        "drone":     (255, 210, 60),
    }
    ACCENT = [
        (255, 80, 80),
        (80, 210, 160),
        (160, 100, 255),
        (60, 180, 255),
    ]


# ═══════════════════ VISUALIZER ═══════════════════

class MultiVisualizer:
    def __init__(self, envs, titles, width=1600, height=860):
        pygame.init()
        self.envs = envs
        self.titles = titles
        self.n = len(envs)
        self.width = width
        self.pw = width // self.n          # panel width
        self.sim_h = self.pw               # square sim area (height = panel width)
        self.height = height

        self.scale = self.pw / AREA_SIZE
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("DTN 4-Way Routing Competition")
        self.clock = pygame.time.Clock()

        self.font_sm  = pygame.font.SysFont("Menlo", 11)
        self.font_md  = pygame.font.SysFont("Menlo", 13)
        self.font_lg  = pygame.font.SysFont("Menlo", 16, bold=True)
        self.font_hdr = pygame.font.SysFont("Menlo", 10)

    # ────── events ──────

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit(0)

    # ────── bar helper ──────

    def _bar(self, x, y, w, h, val, mx, color, label, fmt):
        pygame.draw.rect(self.screen, C.BAR_BG, (x, y, w, h), border_radius=3)
        fw = max(0, min(int(w * (val / mx)), w))
        if fw > 0:
            pygame.draw.rect(self.screen, color, (x, y, fw, h), border_radius=3)
        pygame.draw.rect(self.screen, color, (x, y, w, h), 1, border_radius=3)
        lbl = self.font_hdr.render(label, True, C.TEXT_DIM)
        self.screen.blit(lbl, (x, y - 13))
        v = self.font_md.render(fmt.format(val), True, C.TEXT_BRIGHT)
        self.screen.blit(v, (x + w + 5, y - 1))

    # ────── render ──────

    def render(self, t, fps=60):
        self.handle_events()
        self.screen.fill(C.BG)

        # Progress bar
        prog = t / SIM_DURATION
        pygame.draw.rect(self.screen, (30, 45, 70), (0, 0, self.width, 2))
        pygame.draw.rect(self.screen, C.GOLD, (0, 0, int(self.width * prog), 2))

        for idx, env in enumerate(self.envs):
            px = idx * self.pw
            accent = C.ACCENT[idx]

            # Separator
            if idx > 0:
                pygame.draw.line(self.screen, C.SEP, (px, 0), (px, self.height), 1)

            # Grid
            sp = int(AREA_SIZE / 8 * self.scale)
            for i in range(1, 8):
                gx = px + i * sp
                pygame.draw.line(self.screen, C.GRID, (gx, 3), (gx, self.sim_h))
                gy = i * sp
                if gy < self.sim_h:
                    pygame.draw.line(self.screen, C.GRID, (px, gy), (px + self.pw, gy))

            # Contacts
            contacts = env.get_contacts()
            for n1, n2 in contacts:
                x1 = px + int(n1.x * self.scale)
                y1 = int(n1.y * self.scale)
                x2 = px + int(n2.x * self.scale)
                y2 = int(n2.y * self.scale)
                if y1 < self.sim_h and y2 < self.sim_h:
                    if len(n1.buffer) > 0 or len(n2.buffer) > 0:
                        pygame.draw.line(self.screen, C.TX_LINE, (x1,y1),(x2,y2), 1)
                    else:
                        pygame.draw.line(self.screen, C.CONTACT, (x1,y1),(x2,y2), 1)

            # Nodes
            sr = int(TRANSMISSION_RANGE * self.scale)
            for node in env.nodes:
                nx = px + int(node.x * self.scale)
                ny = int(node.y * self.scale)
                if ny >= self.sim_h:
                    continue
                color = C.ROLE.get(node.role, (200,200,200))

                if node.role == "drone":
                    pulse = sr + int(math.sin(env.time * 0.08) * 3)
                    s = pygame.Surface((pulse*2, pulse*2), pygame.SRCALPHA)
                    pygame.draw.circle(s, (*C.DRONE_RANGE, 20), (pulse, pulse), pulse, 1)
                    self.screen.blit(s, (nx - pulse, ny - pulse))
                    pygame.draw.polygon(self.screen, color, [(nx,ny-6),(nx-4,ny+4),(nx+4,ny+4)])
                elif node.role == "shelter":
                    pygame.draw.rect(self.screen, color, (nx-4,ny-4,8,8))
                    pygame.draw.rect(self.screen, (150,255,180), (nx-4,ny-4,8,8), 1)
                else:
                    pygame.draw.circle(self.screen, color, (nx, ny), 3)

                if any(m.critical for m in node.buffer):
                    s2 = pygame.Surface((14,14), pygame.SRCALPHA)
                    pygame.draw.circle(s2, (255,50,50,45), (7,7), 7)
                    self.screen.blit(s2, (nx-7, ny-7))

                if len(node.buffer) > 5:
                    load = min(len(node.buffer) / 30.0, 1.0)
                    rc = (int(80+175*load), int(200-150*load), 80)
                    pygame.draw.circle(self.screen, rc, (nx,ny), int(5+load*4), 1)

            # ──── STATS ────
            sy = self.sim_h + 5
            pygame.draw.line(self.screen, C.SEP, (px, self.sim_h), (px + self.pw, self.sim_h), 2)
            pygame.draw.rect(self.screen, accent, (px, sy, self.pw, 3))

            title = self.font_lg.render(self.titles[idx], True, accent)
            self.screen.blit(title, (px + 10, sy + 8))

            s = env.stats
            gen = max(s["generated"],1)
            dr = s["delivered"] / gen * 100
            cg = max(s["critical_generated"],1)
            cdr = s["critical_delivered"] / cg * 100
            oh = s["transmissions"] / max(s["delivered"],1)
            cd = sum(s["critical_delay"])/max(len(s["critical_delay"]),1)

            bx = px + 10
            bw = self.pw - 75
            bh = 12

            y = sy + 35
            self._bar(bx, y, bw, bh, dr, 100, C.GREEN, "DELIVERY", "{:.1f}%")
            y += 30
            self._bar(bx, y, bw, bh, cdr, 100, C.RED, "CRITICAL DEL", "{:.1f}%")
            y += 30
            dc = (int(50+200*min(cd/2000,1)), int(200-150*min(cd/2000,1)), int(120-80*min(cd/2000,1)))
            self._bar(bx, y, bw, bh, cd, 2000, dc, "CRIT DELAY", "{:.0f}s")

            y += 28
            for line in [f"OH: {oh:.1f}x", f"Drops: {s['drops']:,}", f"t={t}"]:
                surf = self.font_sm.render(line, True, C.TEXT_DIM)
                self.screen.blit(surf, (bx, y)); y += 14

            if idx == 3 and t > 300:
                tag = self.font_sm.render("★ ENCOUNTER+ZONE+UTILITY", True, C.GOLD)
                self.screen.blit(tag, (px + 10, self.height - 18))

        pygame.display.flip()
        self.clock.tick(fps)

    def close(self):
        pygame.quit()


# ═══════════════════ MAIN ═══════════════════

def run_multi_demo():
    parser = argparse.ArgumentParser(description="DTN 4-Way Competition")
    parser.add_argument("--fps", type=int, default=120)
    parser.add_argument("--traffic", type=str, choices=["Low","Medium","High"], default="High")
    args, _ = parser.parse_known_args()

    prob = {"Low": 3/3600, "Medium": 8/3600, "High": 20/3600}[args.traffic]
    seed = 42

    envs = []
    for i in range(4):
        random.seed(seed)
        envs.append(Environment(message_gen_prob=prob))

    routers = [
        EpidemicRouter(),
        SprayAndWaitRouter(),
        SemanticRouter(envs[2].nodes),
        SpatioSemanticRouter(envs[3].nodes),
    ]
    titles = ["EPIDEMIC", "SPRAY & WAIT", "SEMANTIC", "SPATIO-SEMANTIC"]

    viz = MultiVisualizer(envs, titles, width=1600)

    for t in range(SIM_DURATION):
        for i in range(4):
            random.seed(seed + t)
            env, router = envs[i], routers[i]
            env.time = t
            env.generate_messages()
            env.update_mobility()
            contacts = env.get_contacts()
            env.stats["time"] = env.time
            for n1, n2 in contacts:
                router.exchange(n1, n2, env.stats)
            env.check_delivery()
            env.expire_messages()

        viz.render(t, fps=args.fps)

    print("\n── FINAL ──")
    for i, env in enumerate(envs):
        m = env.compute_metrics()
        print(f"\n[{titles[i]}]")
        for k,v in m.items():
            print(f"  {k}: {v:.4f}" if isinstance(v,float) else f"  {k}: {v}")

    while True:
        for event in pygame.event.get():
            if event.type in (pygame.QUIT,) or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit(); return
        pygame.time.Clock().tick(10)


if __name__ == "__main__":
    run_multi_demo()
