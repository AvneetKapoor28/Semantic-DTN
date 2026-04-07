from environment import BUFFER_SIZE

class SemanticRouter:

    MAX_FORWARD = 1000   # effectively no limit

    def __init__(self, nodes):
        self.nodes = nodes

    # ---------------- UTILITY ----------------

    def utility(self, msg, sender, receiver):

        score = 0

        # 🔥 DESTINATION (must dominate)
        if receiver.id == msg.destination:
            score += 1000

        # 🔥 CRITICAL (strong but not insane)
        if msg.critical:
            score += 20

        # 🔥 ROLE AWARENESS
        if receiver.role == "drone":
            score += 5
        elif receiver.role == "responder":
            score += 3

        return score

    # ---------------- EXCHANGE ----------------

    def exchange(self, node_a, node_b, stats):

        self.forward(node_a, node_b, stats)
        self.forward(node_b, node_a, stats)

    def forward(self, sender, receiver, stats):

        sender_msgs = list(sender.buffer)
        receiver_ids = {m.id for m in receiver.buffer}

        candidates = []

        for msg in sender_msgs:
            if msg.id in receiver_ids:
                continue

            score = self.utility(msg, sender, receiver)
            candidates.append((score, msg))

        # 🔥 SORT: Critical automatically comes first via utility
        candidates.sort(reverse=True, key=lambda x: x[0])

        forwarded = 0

        for score, msg in candidates:

            if forwarded >= 80:   # controlled but strong spreading
                break

            if len(receiver.buffer) >= BUFFER_SIZE:
                break

            new_copy = msg.clone()
            new_copy.hops += 1

            receiver.buffer.append(new_copy)
            stats["transmissions"] += 1
            forwarded += 1