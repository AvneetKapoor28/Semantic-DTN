# message.py

import uuid
import random

CRITICAL_PERCENT = 0.3
INITIAL_COPIES = 8

class Message:
    def __init__(self, source, destination, creation_time, msg_id=None):
        self.id = msg_id if msg_id else str(uuid.uuid4())
        self.source = source
        self.destination = destination
        self.creation_time = creation_time
        self.critical = random.random() < CRITICAL_PERCENT
        self.hops = 0
        self.copies = INITIAL_COPIES

    def clone(self):
        new_msg = Message(
            source=self.source,
            destination=self.destination,
            creation_time=self.creation_time,
            msg_id=self.id
        )
        new_msg.critical = self.critical
        new_msg.hops = self.hops
        new_msg.copies = self.copies
        return new_msg