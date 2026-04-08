"""
Spatio-Semantic DTN Router  (v2 — Aggressive)
===============================================
Combines semantic role awareness with spatial intelligence:
  1. Encounter History   — tracks how often nodes meet each other
  2. Zone Awareness      — divides the area into zones; nodes record visit freq
  3. Delivery Prediction — utility-based forwarding with adaptive thresholds
  4. Critical Buffer Reserve — 35 % of the buffer is reserved for critical msgs
  5. Hybrid Spray+Utility — initial spray phase then utility-gated wait phase
  6. Transitive Delivery Prediction — 2-hop encounter chain scoring
"""

import math
import random
from environment import BUFFER_SIZE, AREA_SIZE

# --------------- CONSTANTS ---------------

NUM_ZONES_PER_AXIS = 5
ZONE_SIZE = AREA_SIZE / NUM_ZONES_PER_AXIS
CRITICAL_RESERVE = int(BUFFER_SIZE * 0.35)     # 35 % reserved for critical
ENCOUNTER_DECAY = 0.985                         # slow decay — long memory
ZONE_DECAY = 0.997                              # spatial memory decays slower
MIN_UTILITY_GAIN = 0.02                         # very low bar → more forwarding
SPRAY_THRESHOLD = 4                             # copies > this → spray freely


# --------------- HELPERS ---------------

def distance(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def zone_of(node):
    zx = max(0, min(int(node.x / ZONE_SIZE), NUM_ZONES_PER_AXIS - 1))
    zy = max(0, min(int(node.y / ZONE_SIZE), NUM_ZONES_PER_AXIS - 1))
    return (zx, zy)


def _ensure_tables(node):
    if not hasattr(node, "_enc"):
        node._enc = {}
        node._zone_freq = {}
        node._last_zone = None


def _update_tracking(node):
    _ensure_tables(node)
    z = zone_of(node)
    if z != node._last_zone:
        node._zone_freq[z] = node._zone_freq.get(z, 0) + 1.0
        node._last_zone = z
    for k in node._zone_freq:
        node._zone_freq[k] *= ZONE_DECAY


def _record_encounter(a, b):
    a._enc[b.id] = a._enc.get(b.id, 0) + 1.0
    b._enc[a.id] = b._enc.get(a.id, 0) + 1.0
    for k in a._enc:
        a._enc[k] *= ENCOUNTER_DECAY
    for k in b._enc:
        b._enc[k] *= ENCOUNTER_DECAY


# --------------- UTILITY ---------------

def _utility(carrier, dest_node, nodes_dict):
    _ensure_tables(carrier)

    # 1. Spatial proximity (0–1)
    d = distance(carrier, dest_node)
    max_dist = math.hypot(AREA_SIZE, AREA_SIZE)
    prox = 1.0 - (d / max_dist)

    # 2. Direct encounter frequency
    enc_direct = carrier._enc.get(dest_node.id, 0)
    enc_score = min(enc_direct / 8.0, 1.0)

    # 3. Zone co-location
    dest_zone = zone_of(dest_node)
    zone_visits = carrier._zone_freq.get(dest_zone, 0)
    zone_score = min(zone_visits / 12.0, 1.0)

    # 4. Role bonus
    role_bonus = 0.0
    if carrier.role == "drone":
        role_bonus = 0.40
    elif carrier.role == "responder":
        role_bonus = 0.20
    elif carrier.role == "shelter":
        # Shelters are destinations — high value if msg is headed nearby
        role_bonus = 0.10

    # 5. Transitivity (2-hop encounter chain)
    trans_score = 0.0
    top_peers = sorted(carrier._enc.items(), key=lambda x: x[1], reverse=True)[:6]
    for peer_id, peer_enc in top_peers:
        peer_node = nodes_dict.get(peer_id)
        if peer_node is not None:
            _ensure_tables(peer_node)
            indirect = peer_node._enc.get(dest_node.id, 0)
            trans_score += min(peer_enc * indirect, 5.0)
    trans_score = min(trans_score / 20.0, 1.0)

    # Weighted composite
    return (
        0.18 * prox +
        0.28 * enc_score +
        0.20 * zone_score +
        0.14 * role_bonus +
        0.20 * trans_score
    )


# --------------- BUFFER ---------------

def _available_slots(node, for_critical):
    total_used = len(node.buffer)
    critical_in_buf = sum(1 for m in node.buffer if m.critical)
    non_critical_in_buf = total_used - critical_in_buf

    if for_critical:
        return BUFFER_SIZE - total_used
    else:
        return (BUFFER_SIZE - CRITICAL_RESERVE) - non_critical_in_buf


def try_insert(node, msg, stats):
    if _available_slots(node, msg.critical) > 0:
        node.buffer.append(msg)
        return True

    if msg.critical:
        # Evict oldest non-critical with most remaining copies (least useful)
        worst_idx = -1
        worst_score = -1
        for i, m in enumerate(node.buffer):
            if not m.critical:
                score = m.copies  # prefer evicting msgs with many copies (redundant)
                if score > worst_score:
                    worst_score = score
                    worst_idx = i
        if worst_idx >= 0:
            node.buffer.pop(worst_idx)
            node.buffer.append(msg)
            return True

    stats["drops"] += 1
    return False


# --------------- ROUTER ---------------

class SpatioSemanticRouter:

    def __init__(self, nodes):
        self.nodes = nodes
        self.nodes_dict = {n.id: n for n in nodes}

    def exchange(self, node_a, node_b, stats):
        for n in (node_a, node_b):
            _update_tracking(n)
        _record_encounter(node_a, node_b)

        self._forward(node_a, node_b, stats)
        self._forward(node_b, node_a, stats)

    def _forward(self, sender, receiver, stats):

        sender_msgs = list(sender.buffer)
        receiver_ids = {m.id for m in receiver.buffer}

        forwarded = 0

        # ═══════════ PASS 1: CRITICAL (aggressive) ═══════════
        for msg in sender_msgs:
            if not msg.critical:
                continue
            if msg.id in receiver_ids or msg.copies <= 0:
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

            u_s = _utility(sender, dest, self.nodes_dict)
            u_r = _utility(receiver, dest, self.nodes_dict)
            gain = u_r - u_s

            # SPRAY PHASE: many copies → spread aggressively
            if msg.copies > SPRAY_THRESHOLD:
                # Give half, no questions asked (but drone/responder get more)
                give = max(2, msg.copies // 2)
                if receiver.role == "drone":
                    give = max(give, int(msg.copies * 0.6))
                give = min(give, msg.copies - 1)
                msg.copies -= give

                new_copy = msg.clone()
                new_copy.copies = give
                new_copy.hops += 1
                if try_insert(receiver, new_copy, stats):
                    stats["transmissions"] += 1
                    forwarded += 1

            # UTILITY PHASE: few copies → be smart
            elif msg.copies > 1:
                if gain > -0.05:  # very lenient for critical
                    ratio = max(0.3, min(0.7, 0.5 + gain * 2))
                    give = max(1, int(msg.copies * ratio))
                    give = min(give, msg.copies - 1)
                    msg.copies -= give

                    new_copy = msg.clone()
                    new_copy.copies = give
                    new_copy.hops += 1
                    if try_insert(receiver, new_copy, stats):
                        stats["transmissions"] += 1
                        forwarded += 1

            # WAIT PHASE: 1 copy → hand off only to clearly better carrier
            elif msg.copies == 1:
                if gain >= MIN_UTILITY_GAIN or receiver.role == "drone":
                    new_copy = msg.clone()
                    new_copy.copies = 1
                    new_copy.hops += 1
                    msg.copies = 0
                    if try_insert(receiver, new_copy, stats):
                        stats["transmissions"] += 1
                        forwarded += 1

        # ═══════════ PASS 2: NON-CRITICAL (utility-gated) ═══════════
        for msg in sender_msgs:
            if msg.critical:
                continue
            if msg.id in receiver_ids or msg.copies <= 0:
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

            u_s = _utility(sender, dest, self.nodes_dict)
            u_r = _utility(receiver, dest, self.nodes_dict)
            gain = u_r - u_s

            # SPRAY PHASE
            if msg.copies > SPRAY_THRESHOLD:
                if gain > -0.03:  # slightly gated even in spray
                    give = max(1, msg.copies // 2)
                    if receiver.role == "drone":
                        give = max(give, int(msg.copies * 0.55))
                    give = min(give, msg.copies - 1)
                    msg.copies -= give

                    new_copy = msg.clone()
                    new_copy.copies = give
                    new_copy.hops += 1
                    if try_insert(receiver, new_copy, stats):
                        stats["transmissions"] += 1
                        forwarded += 1

            # UTILITY PHASE
            elif msg.copies > 1:
                if gain >= MIN_UTILITY_GAIN:
                    ratio = max(0.3, min(0.65, 0.5 + gain * 2))
                    give = max(1, int(msg.copies * ratio))
                    give = min(give, msg.copies - 1)
                    msg.copies -= give

                    new_copy = msg.clone()
                    new_copy.copies = give
                    new_copy.hops += 1
                    if try_insert(receiver, new_copy, stats):
                        stats["transmissions"] += 1
                        forwarded += 1

            # WAIT PHASE
            elif msg.copies == 1:
                if gain >= MIN_UTILITY_GAIN * 1.5:
                    new_copy = msg.clone()
                    new_copy.copies = 1
                    new_copy.hops += 1
                    msg.copies = 0
                    if try_insert(receiver, new_copy, stats):
                        stats["transmissions"] += 1
                        forwarded += 1

            if forwarded >= 100:
                break
