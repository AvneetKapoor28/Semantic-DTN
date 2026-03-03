# node.py

class Node:
    def __init__(self, node_id, role, speed_range, area_size):
        self.id = node_id
        self.role = role
        self.speed_range = speed_range
        self.area_size = area_size

        self.x = 0
        self.y = 0

        self.destination = None
        self.pause_time = 0
        self.speed = 0

        self.buffer = []