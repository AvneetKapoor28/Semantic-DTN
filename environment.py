# environment.py

import random
import math
from message import Message
from node import Node
from mobility import RandomWaypointMobility


AREA_SIZE = 2000
TRANSMISSION_RANGE = 100
SIM_DURATION = 7200
BUFFER_SIZE = 50

# Message generation probability per minute
MESSAGE_GEN_PROB = 1/1200  # realistic sparse traffic


class Environment:
    def __init__(self, message_gen_prob):
        self.area_size = AREA_SIZE
        self.nodes = []
        self.mobility = RandomWaypointMobility(AREA_SIZE)
        self.time = 0
        self.message_gen_prob = message_gen_prob

        self.stats = {
            "generated": 0,
            "delivered": 0,
            "transmissions": 0,
            "delay": [],
            "critical_delay": [],
            "drops": 0
        }

        self._create_nodes()

    # --------------------------------------------------
    # Node creation with explicit roles
    # --------------------------------------------------

    def _create_nodes(self):
        node_id = 0

        # 35 civilians
        for _ in range(35):
            node = Node(
                node_id,
                role="civilian",
                speed_range=(0.5, 1.5),
                area_size=self.area_size
            )
            self.mobility.initialize_node(node)
            self.nodes.append(node)
            node_id += 1

        # 10 responders
        for _ in range(10):
            node = Node(
                node_id,
                role="responder",
                speed_range=(1.5, 2.5),
                area_size=self.area_size
            )
            self.mobility.initialize_node(node)
            self.nodes.append(node)
            node_id += 1

        # 3 shelters (static)
        for _ in range(3):
            node = Node(
                node_id,
                role="shelter",
                speed_range=(0, 0),
                area_size=self.area_size
            )
            self.mobility.initialize_node(node)
            self.nodes.append(node)
            node_id += 1

        # 2 drones
        for _ in range(2):
            node = Node(
                node_id,
                role="drone",
                speed_range=(5, 10),
                area_size=self.area_size
            )
            self.mobility.initialize_node(node)
            self.nodes.append(node)
            node_id += 1

    # --------------------------------------------------
    # Message generation (realistic probabilistic)
    # --------------------------------------------------

    def generate_messages(self):
        for node in self.nodes:
            if random.random() < self.message_gen_prob:
                destination = random.choice(self.nodes)
                while destination.id == node.id:
                    destination = random.choice(self.nodes)

                msg = Message(node.id, destination.id, self.time)

                if len(node.buffer) < BUFFER_SIZE:
                    node.buffer.append(msg)
                    self.stats["generated"] += 1
                else:
                    self.stats["drops"] += 1

    # --------------------------------------------------
    # Move all nodes
    # --------------------------------------------------

    def update_mobility(self):
        for node in self.nodes:
            self.mobility.move_node(node)

    # --------------------------------------------------
    # Contact detection
    # --------------------------------------------------

    def get_contacts(self):
        contacts = []
        for i in range(len(self.nodes)):
            for j in range(i + 1, len(self.nodes)):
                n1 = self.nodes[i]
                n2 = self.nodes[j]
                dist = math.hypot(n1.x - n2.x, n1.y - n2.y)
                if dist <= TRANSMISSION_RANGE:
                    contacts.append((n1, n2))
        return contacts

    # --------------------------------------------------
    # Delivery check
    # --------------------------------------------------

    def check_delivery(self):
        # Initialize delivered set once
        if not hasattr(self, "delivered_ids"):
            self.delivered_ids = set()

        # Pass 1: Record all first-time deliveries reliably
        for node in self.nodes:
            for msg in node.buffer:
                if node.id == msg.destination and msg.id not in self.delivered_ids:
                    delay = self.time - msg.creation_time
                    self.stats["delay"].append(delay)

                    if msg.critical:
                        self.stats["critical_delay"].append(delay)

                    self.stats["delivered"] += 1
                    self.delivered_ids.add(msg.id)

        # Pass 2: Oracle - Remove all globally delivered messages from buffers
        for node in self.nodes:
            for msg in list(node.buffer):
                if msg.id in self.delivered_ids:
                    node.buffer.remove(msg)

    # --------------------------------------------------
    # TTL expiration
    # --------------------------------------------------

    def expire_messages(self):
        for node in self.nodes:
            for msg in list(node.buffer):
                if self.time - msg.creation_time > 3600:
                    node.buffer.remove(msg)

    # --------------------------------------------------
    # Run simulation with pluggable router
    # --------------------------------------------------

    def run(self, router):
        for t in range(SIM_DURATION):
            self.time = t

            self.generate_messages()
            self.update_mobility()

            contacts = self.get_contacts()
            self.stats["time"] = self.time
            for n1, n2 in contacts:
                router.exchange(n1, n2, self.stats)

            self.check_delivery()
            self.expire_messages()

        return self.compute_metrics()

    # --------------------------------------------------

    def compute_metrics(self):
        generated = self.stats["generated"]
        delivered = self.stats["delivered"]

        return {
            "DeliveryRatio": delivered / generated if generated else 0,
            "AvgDelay": sum(self.stats["delay"]) / len(self.stats["delay"]) if self.stats["delay"] else 0,
            "AvgCriticalDelay": sum(self.stats["critical_delay"]) / len(self.stats["critical_delay"]) if self.stats["critical_delay"] else 0,
            "OverheadRatio": self.stats["transmissions"] / delivered if delivered else 0,
            "BufferDrops": self.stats["drops"]
        }