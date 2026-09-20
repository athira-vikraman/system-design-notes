"""
Sharding  ->  DESIGN_PATTERNS.md #4

The data no longer fits on one machine, so split it across several.

The question that matters: WHICH shard does this row live on?
Pick the wrong shard key and one machine gets all the traffic.
"""

import hashlib
from collections import Counter, defaultdict


class ShardRouter:
    def __init__(self, shard_count, strategy="hash"):
        self.shard_count = shard_count
        self.strategy = strategy
        self.shards = defaultdict(dict)  # shard number -> {key: value}

    def _shard_for(self, key):
        if self.strategy == "hash":
            # even spread, but adding a shard reshuffles everything.
            # see 03_consistent_hashing.py for the fix.
            digest = int(hashlib.md5(str(key).encode()).hexdigest(), 16)
            return digest % self.shard_count

        if self.strategy == "range":
            # split by first letter. Simple, but uneven in practice:
            # far more names start with S than with X.
            first = str(key)[0].lower()
            bucket = (ord(first) - ord("a")) if first.isalpha() else 0
            return min(bucket * self.shard_count // 26, self.shard_count - 1)

        raise ValueError(f"Unknown strategy: {self.strategy}")

    def put(self, key, value):
        self.shards[self._shard_for(key)][key] = value

    def get(self, key):
        return self.shards[self._shard_for(key)].get(key)

    def distribution(self):
        return Counter({shard: len(data) for shard, data in self.shards.items()})


def show(title, router, keys):
    for key in keys:
        router.put(key, f"data-for-{key}")

    print(f"\n{title}")
    counts = router.distribution()
    for shard in range(router.shard_count):
        count = counts.get(shard, 0)
        share = count / len(keys)
        bar = "#" * int(share * 60)
        print(f"  shard {shard}  {count:>5,}  {share:>5.1%}  {bar}")

    biggest = max(counts.values())
    smallest = min(counts.get(s, 0) for s in range(router.shard_count))
    print(f"  imbalance: biggest shard holds {biggest/max(smallest,1):.1f}x the smallest")


def demo():
    # realistic names: heavily weighted to certain letters, like real data
    prefixes = ["sam", "sara", "sandeep", "sunil", "shreya", "arun", "anita",
                "ravi", "rahul", "priya", "maya", "kiran", "deepak", "xavier"]
    keys = [f"{prefixes[i % len(prefixes)]}_{i}" for i in range(10000)]

    print("Sharding 10,000 user records across 4 shards")

    show("Hash sharding: hash(key) % 4", ShardRouter(4, "hash"), keys)
    show("Range sharding: split by first letter", ShardRouter(4, "range"), keys)

    print("\n  -> Hash gives an even spread. Range does not, because real")
    print("     names cluster around certain letters. That overloaded")
    print("     shard is called a HOT SHARD.")

    print("\n\nReading data back:\n")
    router = ShardRouter(4, "hash")
    for key in ["athira", "ravi", "priya"]:
        router.put(key, f"profile of {key}")
    for key in ["athira", "ravi", "priya", "unknown"]:
        shard = router._shard_for(key)
        print(f"  {key:<9} -> shard {shard} -> {router.get(key)}")

    print("\n  The router always computes the same shard for the same key,")
    print("  so reads and writes agree without any lookup table.")


if __name__ == "__main__":
    demo()
