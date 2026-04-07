from environment import BUFFER_SIZE

class SemanticRouter:

    MAX_FORWARD = 1000   # effectively no limit

    def __init__(self, nodes):
        self.nodes = nodes

    # ---------------- UTILITY ----------------

    def utility(self, msg, sender, receiver):

        score = 0

        # Destination → absolute priority
        if receiver.id == msg.destination:
            score += 1000

        # Critical messages
        if msg.critical:
            score += 10

        # Role awareness
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

        # Collect all possible messages (NO filtering)
        for msg in sender_msgs:
            if msg.id not in receiver_ids:
                score = self.utility(msg, sender, receiver)
                candidates.append((score, msg))

        # Sort by priority
        candidates.sort(reverse=True, key=lambda x: x[0])

        # 🔥 KEY: behave like epidemic but ordered
        for score, msg in candidates:

            if len(receiver.buffer) >= BUFFER_SIZE:
                break

            new_copy = msg.clone()
            new_copy.hops += 1

            receiver.buffer.append(new_copy)
            stats["transmissions"] += 1