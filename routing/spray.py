from environment import BUFFER_SIZE

class SprayAndWaitRouter:

    def exchange(self, node_a, node_b, stats):

        self.forward(node_a, node_b, stats)
        self.forward(node_b, node_a, stats)

    def forward(self, sender, receiver, stats):

        sender_msgs = list(sender.buffer)
        receiver_ids = {m.id for m in receiver.buffer}

        for msg in sender_msgs:

            if msg.id in receiver_ids:
                continue

            # 🔥 BASIC SPRAY
            if msg.copies > 1:

                if len(receiver.buffer) < BUFFER_SIZE:

                    # 🔻 Not optimal: give only 1 copy (slower spread)
                    msg.copies -= 1

                    new_copy = msg.clone()
                    new_copy.copies = 1
                    new_copy.hops += 1

                    receiver.buffer.append(new_copy)
                    stats["transmissions"] += 1

                else:
                    stats["drops"] += 1

            # 🔥 WAIT PHASE (only deliver to destination)
            elif msg.copies == 1:

                if receiver.id == msg.destination:

                    if len(receiver.buffer) < BUFFER_SIZE:

                        new_copy = msg.clone()
                        new_copy.hops += 1

                        receiver.buffer.append(new_copy)
                        stats["transmissions"] += 1

                    else:
                        stats["drops"] += 1