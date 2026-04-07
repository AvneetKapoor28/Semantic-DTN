# environment.py

import random
import math
from message import Message
from node import Node
from mobility import RandomWaypointMobility

AREA_SIZE = 2000
TRANSMISSION_RANGE = 120   # slightly increased → fairer contacts
SIM_DURATION = 7200
BUFFER_SIZE = 40           # balanced (not too harsh, not too easy)


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

        for _ in range(35):
            node = Node(node_id, "civilian", (0.5, 1.5), self.area_size)
            self.mobility.initialize_node(node)
            self.nodes.append(node)
            node_id += 1

        for _ in range(10):
            node = Node(node_id, "responder", (1.5, 2.5), self.area_size)
            self.mobility.initialize_node(node)
            self.nodes.append(node)
            node_id += 1

        for _ in range(3):
            node = Node(node_id, "shelter", (0, 0), self.area_size)
            self.mobility.initialize_node(node)
            self.nodes.append(node)
            node_id += 1

        for _ in range(2):
            node = Node(node_id, "drone", (5, 10), self.area_size)
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

                # 🔥 CONTROLLED CRITICALITY
                msg.critical = random.random() < 0.3

                # 🔥 COPY CONTROL (CRUCIAL)
                msg.copies = 20 if msg.critical else 6

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

        # remove globally delivered
        for node in self.nodes:
            node.buffer = [m for m in node.buffer if m.id not in self.delivered_ids]

    # ---------------- TTL ----------------

    def expire_messages(self):
        for node in self.nodes:
            node.buffer = [
                m for m in node.buffer
                if self.time - m.creation_time <= 3600
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