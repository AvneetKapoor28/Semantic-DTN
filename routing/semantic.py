from environment import BUFFER_SIZE

class SemanticRouter:

    MAX_FORWARD = 5   # limit transmissions per contact
    TTL = 3600

    def utility(self, msg, node_receiver, current_time):

        age = current_time - msg.creation_time
        age_score = age / self.TTL

        critical_score = 1 if msg.critical else 0

        destination_score = 1 if node_receiver.id == msg.destination else 0

        utility = (
            0.5 * critical_score +
            0.3 * age_score +
            0.2 * destination_score
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
                score = self.utility(msg, node_b, stats["time"])
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
                score = self.utility(msg, node_a, stats["time"])
                candidates.append((score, msg))

        candidates.sort(reverse=True, key=lambda x: x[0])

        for score, msg in candidates[:self.MAX_FORWARD]:

            if len(node_a.buffer) >= BUFFER_SIZE:
                break

            new_copy = msg.clone()
            new_copy.hops += 1

            node_a.buffer.append(new_copy)
            stats["transmissions"] += 1