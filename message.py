import uuid
import random

CRITICAL_PERCENT = 0.3

class Message:
    def __init__(self, source, destination, creation_time):
        self.id = str(uuid.uuid4())
        self.source = source
        self.destination = destination
        self.creation_time = creation_time
        self.critical = random.random() < CRITICAL_PERCENT
        self.hops = 0