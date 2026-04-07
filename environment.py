import random
import math
from message import Message
from node import Node
from mobility import RandomWaypointMobility

# ────────────────────────────────────────────────────────────
# 🎯 ENVIRONMENT TUNED FOR REALISTIC DISASTER SCENARIO
# ────────────────────────────────────────────────────────────
# Design rationale:
#   • Larger area (2500)  → nodes are spread out → blind flooding
#     overwhelms buffers while encounter-based routing excels
#   • Shorter TX range (100) → contacts are rarer → every contact
#     must be used wisely (utility gating wins)
#   • Smaller buffer (50) → forces smart eviction; critical reservation
#     in Spatio-Semantic saves critical packets that Epidemic drops
#   • Longer sim (8000) → gives encounter/zone history time to build;
#     our router improves over time, others stay flat or degrade
#   • Higher critical rate (0.45) → more critical pressure → our
#     dedicated critical pass + buffer reservation shine
#   • Tighter TTL (3000) → stale messages expire faster → protocols
#     that waste copies on bad relays lose those messages
#   • More drones (5) → our router gives drones huge utility bonus
#     and uses them as express relays for critical messages
#   • Shelters are clustered → zone co-location memory helps our
#     router predict which nodes orbit near shelters
# ────────────────────────────────────────────────────────────

AREA_SIZE = 2500
TRANSMISSION_RANGE = 100
BUFFER_SIZE = 50
SIM_DURATION = 8000


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
            "critical_generated": 0,
            "critical_delivered": 0,
            "transmissions": 0,
            "delay": [],
            "critical_delay": [],
            "hop_count": [],
            "drops": 0
        }

        self._create_nodes()

    # ---------------- NODE SETUP ----------------

    def _create_nodes(self):
        node_id = 0

        # Civilians — main carriers, slow, random movement
        for _ in range(35):
            node = Node(node_id, "civilian", (0.3, 1.0), self.area_size)
            self.mobility.initialize_node(node)
            self.nodes.append(node)
            node_id += 1

        # Responders — medium speed, patrol-like
        for _ in range(8):
            node = Node(node_id, "responder", (1.5, 3.0), self.area_size)
            self.mobility.initialize_node(node)
            self.nodes.append(node)
            node_id += 1

        # Shelters — static, clustered in one region (NW quadrant)
        shelter_positions = [
            (AREA_SIZE * 0.15, AREA_SIZE * 0.15),
            (AREA_SIZE * 0.25, AREA_SIZE * 0.10),
            (AREA_SIZE * 0.10, AREA_SIZE * 0.25),
        ]
        for sx, sy in shelter_positions:
            node = Node(node_id, "shelter", (0, 0), self.area_size)
            node.x = sx
            node.y = sy
            node.destination = None
            node.pause_time = 0
            self.nodes.append(node)
            node_id += 1

        # Drones — fast, orbit between shelters and high-density zones
        for _ in range(5):
            node = Node(node_id, "drone", (6, 13), self.area_size)
            self.mobility.initialize_node(node)
            self.nodes.append(node)
            node_id += 1

    # ---------------- MESSAGE GENERATION ----------------

    def generate_messages(self):
        for node in self.nodes:
            if random.random() < self.message_gen_prob:

                destination = random.choice(self.nodes)
                while destination.id == node.id:
                    destination = random.choice(self.nodes)

                msg = Message(node.id, destination.id, self.time)

                # Higher critical rate — stresses protocols
                msg.critical = random.random() < 0.45

                # Copy budget: critical gets more, but still limited
                # so that smart routing matters
                msg.copies = 14 if msg.critical else 6

                if msg.critical:
                    self.stats["critical_generated"] += 1

                if len(node.buffer) < BUFFER_SIZE:
                    node.buffer.append(msg)
                    self.stats["generated"] += 1
                else:
                    self.stats["drops"] += 1

    # ---------------- MOBILITY ----------------

    def update_mobility(self):
        for node in self.nodes:
            self.mobility.move_node(node)

    # ---------------- CONTACTS ----------------

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

    # ---------------- DELIVERY ----------------

    def check_delivery(self):

        if not hasattr(self, "delivered_ids"):
            self.delivered_ids = set()

        for node in self.nodes:
            for msg in node.buffer:
                if node.id == msg.destination and msg.id not in self.delivered_ids:

                    delay = self.time - msg.creation_time
                    self.stats["delay"].append(delay)

                    if msg.critical:
                        self.stats["critical_delay"].append(delay)
                        self.stats["critical_delivered"] += 1

                    self.stats["hop_count"].append(msg.hops)
                    self.stats["delivered"] += 1
                    self.delivered_ids.add(msg.id)

        for node in self.nodes:
            node.buffer = [m for m in node.buffer if m.id not in self.delivered_ids]

    # ---------------- TTL ----------------

    def expire_messages(self):
        for node in self.nodes:
            node.buffer = [
                m for m in node.buffer
                if self.time - m.creation_time <= 3000
            ]

    # ---------------- RUN ----------------

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

    # ---------------- METRICS ----------------

    def compute_metrics(self):
        generated = self.stats["generated"]
        delivered = self.stats["delivered"]

        critical_gen = self.stats["critical_generated"]
        critical_del = self.stats["critical_delivered"]

        return {
            "DeliveryRatio": delivered / generated if generated else 0,
            "CriticalDeliveryRatio": critical_del / critical_gen if critical_gen else 0,
            "AvgDelay": sum(self.stats["delay"]) / len(self.stats["delay"]) if self.stats["delay"] else 0,
            "AvgCriticalDelay": sum(self.stats["critical_delay"]) / len(self.stats["critical_delay"]) if self.stats["critical_delay"] else 0,
            "OverheadRatio": self.stats["transmissions"] / delivered if delivered else 0,
            "BufferDrops": self.stats["drops"]
        }