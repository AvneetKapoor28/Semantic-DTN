# mobility.py

import random
import math


class RandomWaypointMobility:
    def __init__(self, area_size):
        self.area_size = area_size
        self.targets = []

    def random_position(self):
        return (
            random.uniform(0, self.area_size),
            random.uniform(0, self.area_size)
        )

    def initialize_node(self, node):
        node.x, node.y = self.random_position()

        if node.role in ["shelter", "responder"]:
            self.targets.append(node)

        if node.speed_range == (0, 0):
            node.destination = None
            node.pause_time = 0
        else:
            if node.role == "drone" and self.targets:
                target = random.choice(self.targets)
                node.destination = (target.x, target.y)
            else:
                node.destination = self.random_position()
            node.speed = random.uniform(*node.speed_range)
            node.pause_time = 0

    def move_node(self, node):
        # Static nodes do not move
        if node.speed_range == (0, 0):
            return

        # Pause if required
        if node.pause_time > 0:
            node.pause_time -= 1
            return

        dx = node.destination[0] - node.x
        dy = node.destination[1] - node.y
        dist = math.hypot(dx, dy)

        # Destination reached
        if dist < node.speed:
            node.pause_time = random.randint(20, 80)
            if node.role == "drone" and self.targets:
                target = random.choice(self.targets)
                node.destination = (target.x, target.y)
            else:
                node.destination = self.random_position()
            node.speed = random.uniform(*node.speed_range)
        else:
            node.x += (dx / dist) * node.speed
            node.y += (dy / dist) * node.speed