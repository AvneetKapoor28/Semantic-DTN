from environment import BUFFER_SIZE

class EpidemicRouter:
    def exchange(self, node_a, node_b, stats):
        
        # Snapshot messages to simulate simultaneous exchange
        a_msgs = list(node_a.buffer)
        b_msgs = list(node_b.buffer)
        
        # Use sets for O(1) membership lookup
        a_ids = {m.id for m in a_msgs}
        b_ids = {m.id for m in b_msgs}

        # A -> B
        for msg in a_msgs:
            if msg.id not in b_ids:
                if len(node_b.buffer) < BUFFER_SIZE:
                    node_b.buffer.append(msg)
                    stats["transmissions"] += 1

        # B -> A
        for msg in b_msgs:
            if msg.id not in a_ids:
                if len(node_a.buffer) < BUFFER_SIZE:
                    node_a.buffer.append(msg)
                    stats["transmissions"] += 1