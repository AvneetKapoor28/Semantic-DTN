"""
Spatio-Semantic DTN Router
==========================
Combines semantic role awareness with spatial intelligence:
  1. Encounter History  — tracks how often nodes meet each other
  2. Zone Awareness     — divides the area into zones; nodes record visit frequency
  3. Delivery Prediction — utility-based forwarding: only forward when the
     receiver has a higher predicted probability of reaching the destination
  4. Critical Buffer Reservation — 30% of the buffer is reserved exclusively
     for critical messages, preventing them from being crowded out
  5. Adaptive Copy Splitting — copies are split proportionally to the
     receiver's utility advantage, not blindly halved
"""

import math
import random
from environment import BUFFER_SIZE, AREA_SIZE

# --------------- CONSTANTS ---------------

NUM_ZONES_PER_AXIS = 5                       # 5×5 grid → 25 zones
ZONE_SIZE = AREA_SIZE / NUM_ZONES_PER_AXIS
CRITICAL_RESERVE = int(BUFFER_SIZE * 0.30)   # 30% reserved for critical
ENCOUNTER_DECAY = 0.98                       # slow decay keeps long memory
ZONE_DECAY = 0.995                           # spatial memory decays even slower
MIN_UTILITY_GAIN = 0.05                      # receiver must be ≥ 5% better


# --------------- HELPERS ---------------

def distance(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def zone_of(node):
    """Return (zx, zy) grid coordinate for the node's current position."""
    zx = min(int(node.x / ZONE_SIZE), NUM_ZONES_PER_AXIS - 1)
    zy = min(int(node.y / ZONE_SIZE), NUM_ZONES_PER_AXIS - 1)
    return (zx, zy)


def _ensure_tables(node):
    """Lazily attach tracking tables to a node the first time we see it."""
    if not hasattr(node, "_enc"):
        node._enc = {}          # encounter counts: peer_id → float
        node._zone_freq = {}    # zone visit frequency: (zx,zy) → float
        node._last_zone = None


def _update_tracking(node):
    """Called every exchange opportunity — maintain zone history."""
    _ensure_tables(node)

    z = zone_of(node)
    if z != node._last_zone:
        node._zone_freq[z] = node._zone_freq.get(z, 0) + 1.0
        node._last_zone = z

    # Gentle decay on all zone frequencies to age out stale info
    for k in node._zone_freq:
        node._zone_freq[k] *= ZONE_DECAY


def _record_encounter(a, b):
    """Symmetrically record that a and b have met."""
    a._enc[b.id] = a._enc.get(b.id, 0) + 1.0
    b._enc[a.id] = b._enc.get(a.id, 0) + 1.0

    # Decay all encounter counters
    for k in a._enc:
        a._enc[k] *= ENCOUNTER_DECAY
    for k in b._enc:
        b._enc[k] *= ENCOUNTER_DECAY


# --------------- UTILITY ---------------

def _utility(carrier, dest_node, nodes_dict):
    """
    Composite utility of *carrier* for delivering to *dest_node*.
    Higher is better.  Components:

      1. Spatial proximity   — inverse distance (0–1)
      2. Encounter frequency — how often carrier has met the destination
      3. Zone co-location    — does carrier frequent the destination's zone?
      4. Role bonus          — drones and responders are fast relays
      5. Transitivity        — does carrier frequently meet nodes that
                               frequently meet the destination? (2-hop)
    """
    _ensure_tables(carrier)

    # ---- 1. Spatial proximity (0–1) ----
    d = distance(carrier, dest_node)
    max_dist = math.hypot(AREA_SIZE, AREA_SIZE)
    prox = 1.0 - (d / max_dist)

    # ---- 2. Direct encounter frequency ----
    enc_direct = carrier._enc.get(dest_node.id, 0)
    enc_score = min(enc_direct / 10.0, 1.0)  # cap at 1

    # ---- 3. Zone co-location ----
    dest_zone = zone_of(dest_node)
    zone_visits = carrier._zone_freq.get(dest_zone, 0)
    zone_score = min(zone_visits / 15.0, 1.0)

    # ---- 4. Role bonus ----
    role_bonus = 0.0
    if carrier.role == "drone":
        role_bonus = 0.35
    elif carrier.role == "responder":
        role_bonus = 0.18
    elif carrier.role == "shelter":
        role_bonus = 0.05

    # ---- 5. Transitivity (2-hop encounter prediction) ----
    trans_score = 0.0
    # Look at carrier's top encounter peers and check if *they* have
    # encountered the destination.
    top_peers = sorted(carrier._enc.items(), key=lambda x: x[1], reverse=True)[:5]
    for peer_id, peer_enc in top_peers:
        peer_node = nodes_dict.get(peer_id)
        if peer_node is not None:
            _ensure_tables(peer_node)
            indirect_enc = peer_node._enc.get(dest_node.id, 0)
            trans_score += min(peer_enc * indirect_enc, 5.0)
    trans_score = min(trans_score / 25.0, 1.0)

    # ---- Weighted composite ----
    utility = (
        0.20 * prox +
        0.25 * enc_score +
        0.20 * zone_score +
        0.15 * role_bonus +
        0.20 * trans_score
    )
    return utility


# --------------- BUFFER ---------------

def _available_slots(node, for_critical):
    """How many slots are free?  Critical msgs can use the reserved band."""
    total_used = len(node.buffer)
    critical_in_buf = sum(1 for m in node.buffer if m.critical)
    non_critical_in_buf = total_used - critical_in_buf

    if for_critical:
        return BUFFER_SIZE - total_used          # can use everything
    else:
        # Non-critical cannot use reserved band
        return (BUFFER_SIZE - CRITICAL_RESERVE) - non_critical_in_buf


def try_insert(node, msg, stats):
    """Insert with critical-buffer reservation and smart eviction."""
    if _available_slots(node, msg.critical) > 0:
        node.buffer.append(msg)
        return True

    # Eviction: critical message can evict a non-critical one
    if msg.critical:
        # Evict the oldest non-critical message
        for i, m in enumerate(node.buffer):
            if not m.critical:
                node.buffer.pop(i)
                node.buffer.append(msg)
                return True

    stats["drops"] += 1
    return False


# --------------- ROUTER ---------------

class SpatioSemanticRouter:

    def __init__(self, nodes):
        self.nodes = nodes
        self.nodes_dict = {n.id: n for n in nodes}

    # ---------- PUBLIC ----------

    def exchange(self, node_a, node_b, stats):
        # Housekeeping
        for n in (node_a, node_b):
            _update_tracking(n)
        _record_encounter(node_a, node_b)

        # Bi-directional forwarding
        self._forward(node_a, node_b, stats)
        self._forward(node_b, node_a, stats)

    # ---------- INTERNAL ----------

    def _forward(self, sender, receiver, stats):

        sender_msgs = list(sender.buffer)
        receiver_ids = {m.id for m in receiver.buffer}

        forwarded = 0

        # Pass 1 — Critical messages get priority
        for msg in sender_msgs:
            if not msg.critical:
                continue
            if msg.id in receiver_ids:
                continue
            if msg.copies <= 0:
                continue

            dest = self.nodes_dict.get(msg.destination)
            if dest is None:
                continue

            # Direct delivery — always
            if receiver.id == msg.destination:
                new_copy = msg.clone()
                new_copy.copies = 1
                new_copy.hops += 1
                if try_insert(receiver, new_copy, stats):
                    stats["transmissions"] += 1
                    forwarded += 1
                continue

            u_sender = _utility(sender, dest, self.nodes_dict)
            u_receiver = _utility(receiver, dest, self.nodes_dict)

            # For critical: aggressively forward even with modest utility
            gain = u_receiver - u_sender
            if gain > -0.02:  # very lenient for critical
                # Adaptive copy split: more copies to higher-utility carrier
                if msg.copies > 1:
                    ratio = max(0.3, min(0.7, 0.5 + gain))
                    give = max(2, int(msg.copies * ratio))
                    give = min(give, msg.copies - 1)
                    msg.copies -= give

                    new_copy = msg.clone()
                    new_copy.copies = give
                    new_copy.hops += 1

                    if try_insert(receiver, new_copy, stats):
                        stats["transmissions"] += 1
                        forwarded += 1
                else:
                    # Single copy left: forward only if receiver is clearly better
                    if gain >= MIN_UTILITY_GAIN:
                        new_copy = msg.clone()
                        new_copy.copies = 1
                        new_copy.hops += 1
                        msg.copies = 0  # hand off

                        if try_insert(receiver, new_copy, stats):
                            stats["transmissions"] += 1
                            forwarded += 1

        # Pass 2 — Non-critical messages (utility-gated)
        for msg in sender_msgs:
            if msg.critical:
                continue
            if msg.id in receiver_ids:
                continue
            if msg.copies <= 0:
                continue

            dest = self.nodes_dict.get(msg.destination)
            if dest is None:
                continue

            # Direct delivery
            if receiver.id == msg.destination:
                new_copy = msg.clone()
                new_copy.copies = 1
                new_copy.hops += 1
                if try_insert(receiver, new_copy, stats):
                    stats["transmissions"] += 1
                    forwarded += 1
                continue

            u_sender = _utility(sender, dest, self.nodes_dict)
            u_receiver = _utility(receiver, dest, self.nodes_dict)
            gain = u_receiver - u_sender

            if gain >= MIN_UTILITY_GAIN:
                if msg.copies > 1:
                    ratio = max(0.3, min(0.7, 0.5 + gain))
                    give = max(1, int(msg.copies * ratio))
                    give = min(give, msg.copies - 1)
                    msg.copies -= give

                    new_copy = msg.clone()
                    new_copy.copies = give
                    new_copy.hops += 1

                    if try_insert(receiver, new_copy, stats):
                        stats["transmissions"] += 1
                        forwarded += 1
                else:
                    if gain >= MIN_UTILITY_GAIN * 2:
                        new_copy = msg.clone()
                        new_copy.copies = 1
                        new_copy.hops += 1
                        msg.copies = 0

                        if try_insert(receiver, new_copy, stats):
                            stats["transmissions"] += 1
                            forwarded += 1

            if forwarded >= 80:
                break
