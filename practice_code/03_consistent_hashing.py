"""
Consistent Hashing  ->  DESIGN_PATTERNS.md #12

The problem with `hash(key) % number_of_servers`:
add one server and almost every key moves to a different server.
Every cache empties at once and your database gets crushed.

Consistent hashing moves only a small share of keys instead.

This file measures the difference, so you can see it rather than trust it.
"""

import hashlib
from collections import Counter

# Virtual nodes: place each server at many points around the ring.
# Without this, 3 servers land at 3 random spots and the split is very uneven.
VIRTUAL_NODES = 150


def _hash(text):
    return int(hashlib.md5(text.encode()).hexdigest(), 16)


class HashRing:
    def __init__(self, servers=None, virtual_nodes=VIRTUAL_NODES):
        self.virtual_nodes = virtual_nodes
        self.ring = {}          # hash position -> server name
        self.sorted_keys = []   # positions, kept sorted for binary search
        for server in servers or []:
            self.add(server)

    def add(self, server):
        for i in range(self.virtual_nodes):
            position = _hash(f"{server}:{i}")
            self.ring[position] = server
            self.sorted_keys.append(position)
        self.sorted_keys.sort()

    def remove(self, server):
        for i in range(self.virtual_nodes):
            position = _hash(f"{server}:{i}")
            del self.ring[position]
            self.sorted_keys.remove(position)

    def get(self, key):
        """Walk clockwise from the key to the next server."""
        if not self.ring:
            return None

        position = _hash(key)

        # binary search for the first position >= ours
        low, high = 0, len(self.sorted_keys)
        while low < high:
            mid = (low + high) // 2
            if self.sorted_keys[mid] < position:
                low = mid + 1
            else:
                high = mid

        # past the end means wrap around to the start of the ring
        if low == len(self.sorted_keys):
            low = 0

        return self.ring[self.sorted_keys[low]]


def naive_get(key, servers):
    """The simple approach we are comparing against."""
    return servers[_hash(key) % len(servers)]


def demo():
    servers = ["server-1", "server-2", "server-3"]
    keys = [f"user_{i}" for i in range(10000)]

    print("Adding a 4th server to a 3-server cluster.")
    print("How many of 10,000 keys have to move?\n")

    # --- naive modulo ---
    before = {k: naive_get(k, servers) for k in keys}
    after = {k: naive_get(k, servers + ["server-4"]) for k in keys}
    moved = sum(1 for k in keys if before[k] != after[k])
    print(f"  hash % N            {moved:>6,} keys moved  ({moved/len(keys):.1%})")

    # --- consistent hashing ---
    ring = HashRing(servers)
    before = {k: ring.get(k) for k in keys}
    ring.add("server-4")
    after = {k: ring.get(k) for k in keys}
    moved = sum(1 for k in keys if before[k] != after[k])
    print(f"  consistent hashing  {moved:>6,} keys moved  ({moved/len(keys):.1%})")

    print("\n  -> roughly 1/4 of keys move, which is the theoretical minimum")
    print("     when going from 3 servers to 4.")

    print("\nHow evenly are keys spread across the 4 servers?")
    counts = Counter(after.values())
    for server in sorted(counts):
        share = counts[server] / len(keys)
        bar = "#" * int(share * 100)
        print(f"  {server}  {counts[server]:>5,}  {share:>5.1%}  {bar}")


if __name__ == "__main__":
    demo()
