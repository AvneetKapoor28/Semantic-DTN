from environment import BUFFER_SIZE
import math
import random


def distance(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def try_insert(node, msg, stats):
    if len(node.buffer) < BUFFER_SIZE:
        node.buffer.append(msg)
        return True

    if msg.critical:
        for i, m in enumerate(node.buffer):
            if not m.critical:
                node.buffer.pop(i)
                node.buffer.append(msg)
                return True

    stats["drops"] += 1
    return False


class SemanticRouter:

    def __init__(self, nodes):
        self.nodes = nodes

    def exchange(self, node_a, node_b, stats):
        self.forward(node_a, node_b, stats)
        self.forward(node_b, node_a, stats)

    def forward(self, sender, receiver, stats):

        sender_msgs = list(sender.buffer)
        receiver_ids = {m.id for m in receiver.buffer}

        forwarded = 0
        forward_limit = 100   # 🔥 HIGH → this is key

        for msg in sender_msgs:

            if msg.id in receiver_ids:
                continue

            if msg.copies <= 0:
                continue

            dest = self.nodes[msg.destination]

            # 🔥 BASIC BIAS (NOT STRICT)
            d_sender = distance(sender, dest)
            d_receiver = distance(receiver, dest)

            score = 0

            if d_receiver < d_sender:
                score += 1

            if msg.critical:
                score += 2

            if receiver.role == "drone":
                score += 2
            elif receiver.role == "responder":
                score += 1

            # 🔥 IMPORTANT: ALWAYS allow some forwarding
            prob = 0.6 + 0.1 * score   # between 0.6 → 1.0

            if random.random() > prob:
                continue

            # 🔥 SIMPLE BUT POWERFUL COPY RULE
            give = max(1, msg.copies // 2)
            msg.copies -= give

            new_copy = msg.clone()
            new_copy.copies = give
            new_copy.hops += 1

            if try_insert(receiver, new_copy, stats):
                stats["transmissions"] += 1
                forwarded += 1

            if forwarded >= forward_limit:
                break

        # 🔥 EXTRA PUSH FOR CRITICAL (THIS WINS DEMOS)
        for msg in sender_msgs:

            if not msg.critical:
                continue

            if msg.id in receiver_ids:
                continue

            if msg.copies <= 1:
                continue

            msg.copies -= 2

            new_copy = msg.clone()
            new_copy.copies = 2
            new_copy.hops += 1

            if try_insert(receiver, new_copy, stats):
                stats["transmissions"] += 1