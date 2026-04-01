import pygame
import sys
import math

class Visualizer:
    def __init__(self, env, width=800, height=800):
        pygame.init()
        self.env = env
        self.width = width
        self.height = height
        
        # Calculate scale factor based on environment area size
        self.scale = min(self.width, self.height) / self.env.area_size
        
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("DTN Routing Demo")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 24)
        
        # Colors
        self.BG_COLOR = (24, 24, 32)
        self.GRID_COLOR = (40, 40, 50)
        self.TEXT_COLOR = (220, 220, 220)
        self.RANGE_COLOR = (60, 60, 80)
        
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
        
        # Draw grid
        grid_spacing = 200
        for x in range(0, self.env.area_size, grid_spacing):
            scaled_x = int(x * self.scale)
            pygame.draw.line(self.screen, self.GRID_COLOR, (scaled_x, 0), (scaled_x, self.height))
            
        for y in range(0, self.env.area_size, grid_spacing):
            scaled_y = int(y * self.scale)
            pygame.draw.line(self.screen, self.GRID_COLOR, (0, scaled_y), (self.width, scaled_y))
            
        # Draw transmission range for drone just to be fancy, or for everyone
        from environment import TRANSMISSION_RANGE
        scaled_range = int(TRANSMISSION_RANGE * self.scale)
        
        # Draw all nodes
        for node in self.env.nodes:
            px = int(node.x * self.scale)
            py = int(node.y * self.scale)
            
            color = self.ROLE_COLORS.get(node.role, (200, 200, 200))
            
            # Nodes with buffered messages get a highlight
            if len(node.buffer) > 0:
                pygame.draw.circle(self.screen, (255, 255, 255), (px, py), 8, 1)
                
            # Role specific drawing
            if node.role == "shelter":
                # Draw square
                pygame.draw.rect(self.screen, color, (px-6, py-6, 12, 12))
            elif node.role == "drone":
                # Draw triangle
                pygame.draw.polygon(self.screen, color, [
                    (px, py-8), (px-6, py+6), (px+6, py+6)
                ])
                # Show communication range for drone
                pygame.draw.circle(self.screen, self.RANGE_COLOR, (px, py), scaled_range, 1)
            else:
                # Normal circle
                pygame.draw.circle(self.screen, color, (px, py), 5)
                
            # Show ID optionally? Too cluttered.
            
        # Draw contacts
        contacts = self.env.get_contacts()
        for n1, n2 in contacts:
            px1, py1 = int(n1.x * self.scale), int(n1.y * self.scale)
            px2, py2 = int(n2.x * self.scale), int(n2.y * self.scale)
            pygame.draw.line(self.screen, (255, 255, 100), (px1, py1), (px2, py2), 1)
            
        # Draw stats overlay
        stats = self.env.stats
        info_lines = [
            f"Time: {self.env.time}s / {7200}s",
            f"Generated: {stats['generated']}",
            f"Delivered: {stats['delivered']}",
            f"Drops: {stats['drops']}",
            f"Nodes: {len(self.env.nodes)}",
            "",
            "Legend:",
            "  Blue: Civilian",
            "  Red: Responder",
            "  Green Square: Shelter",
            "  Yellow Triangle: Drone",
            "  White Circle: Has Messages",
            "  Yellow Line: Contact"
        ]
        
        # Optional: calculate delivery ratio on the fly
        if stats['generated'] > 0:
            ratio = stats['delivered'] / stats['generated']
            info_lines.insert(3, f"Delivery Ratio: {ratio:.2%}")
            
        y_pos = 10
        for text in info_lines:
            surface = self.font.render(text, True, self.TEXT_COLOR)
            self.screen.blit(surface, (10, y_pos))
            y_pos += 25
            
        pygame.display.flip()
        self.clock.tick(fps)
        
    def close(self):
        pygame.quit()
