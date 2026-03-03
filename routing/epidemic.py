from environment import BUFFER_SIZE

class EpidemicRouter:
    def exchange(self, node_a, node_b, stats):

        a_msgs = list(node_a.buffer)
        b_msgs = list(node_b.buffer)

        a_ids = {m.id for m in a_msgs}
        b_ids = {m.id for m in b_msgs}

        # A -> B
        for msg in a_msgs:
            if msg.id not in b_ids:
                if len(node_b.buffer) < BUFFER_SIZE:
                    new_copy = msg.clone()
                    new_copy.hops += 1
                    node_b.buffer.append(new_copy)
                    stats["transmissions"] += 1

        # B -> A
        for msg in b_msgs:
            if msg.id not in a_ids:
                if len(node_a.buffer) < BUFFER_SIZE:
                    new_copy = msg.clone()
                    new_copy.hops += 1
                    node_a.buffer.append(new_copy)
                    stats["transmissions"] += 1