"""
Load Balancer  ->  DESIGN_PATTERNS.md #1

Spreading requests across servers, and skipping dead ones.
Four strategies, so you can see how the choice changes the spread.
"""

import hashlib
import itertools
import random
from collections import Counter


class Server:
    def __init__(self, name, weight=1):
        self.name = name
        self.weight = weight
        self.active_connections = 0
        self.healthy = True

    def __repr__(self):
        return self.name


class LoadBalancer:
    def __init__(self, servers, strategy="round_robin"):
        self.servers = servers
        self.strategy = strategy
        self._counter = itertools.count()

    @property
    def healthy_servers(self):
        return [s for s in self.servers if s.healthy]

    def pick(self, client_ip=None):
        available = self.healthy_servers
        if not available:
            raise RuntimeError("No healthy servers")

        if self.strategy == "round_robin":
            # one after another, in order
            return available[next(self._counter) % len(available)]

        if self.strategy == "least_connections":
            # whoever is least busy right now
            return min(available, key=lambda s: s.active_connections)

        if self.strategy == "random":
            return random.choice(available)

        if self.strategy == "ip_hash":
            # the same client always lands on the same server.
            # useful when a server holds session state (but prefer stateless!)
            digest = int(hashlib.md5(client_ip.encode()).hexdigest(), 16)
            return available[digest % len(available)]

        raise ValueError(f"Unknown strategy: {self.strategy}")

    def handle(self, client_ip="0.0.0.0"):
        server = self.pick(client_ip)
        server.active_connections += 1
        return server


def demo():
    def fresh():
        return [Server("server-1"), Server("server-2"), Server("server-3")]

    print("100 requests, spread across 3 servers\n")

    for strategy in ["round_robin", "least_connections", "random"]:
        servers = fresh()
        lb = LoadBalancer(servers, strategy)
        counts = Counter(lb.handle().name for _ in range(100))
        spread = "  ".join(f"{name}:{counts[name]}" for name in sorted(counts))
        print(f"  {strategy:<18} {spread}")

    print("\nip_hash: the same client always gets the same server\n")
    servers = fresh()
    lb = LoadBalancer(servers, "ip_hash")
    for ip in ["10.0.0.1", "10.0.0.2", "10.0.0.3", "10.0.0.1"]:
        print(f"  {ip:<12} -> {lb.pick(ip)}")
    print("  -> notice 10.0.0.1 goes to the same place both times")

    print("\nHealth checks: server-2 dies\n")
    servers = fresh()
    lb = LoadBalancer(servers, "round_robin")
    servers[1].healthy = False
    counts = Counter(lb.handle().name for _ in range(60))
    for name in sorted(counts):
        print(f"  {name}  {counts[name]} requests")
    print("  -> traffic reroutes automatically, users notice nothing")


if __name__ == "__main__":
    demo()
