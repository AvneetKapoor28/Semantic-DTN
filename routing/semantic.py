from environment import BUFFER_SIZE

class SemanticRouter:

    MAX_FORWARD = 5   # limit transmissions per contact
    TTL = 3600

    def __init__(self, nodes):
        self.nodes = nodes

    def utility(self, msg, node_sender, node_receiver, current_time):

        age = current_time - msg.creation_time
        age_score = age / self.TTL

        critical_score = 1 if msg.critical else 0
        destination_score = 1 if node_receiver.id == msg.destination else 0

        buffer_ratio = len(node_receiver.buffer) / BUFFER_SIZE

        # Find destination node
        destination_node = self.nodes[msg.destination]

        current_dist = self.distance(node_sender, destination_node)
        neighbor_dist = self.distance(node_receiver, destination_node)

        spatial_progress = 0
        if current_dist > 0:
            spatial_progress = (current_dist - neighbor_dist) / current_dist

        utility = (
            0.4 * critical_score +
            0.2 * age_score +
            0.2 * destination_score +
            0.3 * spatial_progress -
            0.3 * buffer_ratio
        )

        return utility

    def exchange(self, node_a, node_b, stats):

        a_msgs = list(node_a.buffer)
        b_msgs = list(node_b.buffer)

        a_ids = {m.id for m in a_msgs}
        b_ids = {m.id for m in b_msgs}

        # Messages A could send
        candidates = []

        for msg in a_msgs:
            if msg.id not in b_ids:
                score = self.utility(msg,node_a, node_b, stats["time"])
                candidates.append((score, msg))

        # sort by utility
        candidates.sort(reverse=True, key=lambda x: x[0])

        # forward only top messages
        for score, msg in candidates[:self.MAX_FORWARD]:

            if len(node_b.buffer) >= BUFFER_SIZE:
                break

            new_copy = msg.clone()
            new_copy.hops += 1

            node_b.buffer.append(new_copy)
            stats["transmissions"] += 1

        # Repeat B → A

        candidates = []

        for msg in b_msgs:
            if msg.id not in a_ids:
                score = self.utility(msg, node_b, node_a, stats["time"])
                candidates.append((score, msg))

        candidates.sort(reverse=True, key=lambda x: x[0])

        for score, msg in candidates[:self.MAX_FORWARD]:

            if len(node_a.buffer) >= BUFFER_SIZE:
                break

            new_copy = msg.clone()
            new_copy.hops += 1

            node_a.buffer.append(new_copy)
            stats["transmissions"] += 1
    
    # --------------------------------------------------
    # Distance calculation
    # --------------------------------------------------
    def distance(self, node_a, node_b):
        dx = node_a.x - node_b.x
        dy = node_a.y - node_b.y
        return (dx*dx + dy*dy) ** 0.5