"""
Bloom Filter  ->  DESIGN_PATTERNS.md #14, PRACTICE_PROBLEMS.md #9

Question: "have I seen this URL before?" across a billion URLs.
A normal set would need about 100 GB. A Bloom filter needs about 1 GB.

The deal you accept:
    "definitely not seen"  -> always correct
    "maybe seen"           -> occasionally wrong (a false positive)

For a web crawler that is fine: the worst case is skipping one page.
Never use it where a wrong answer costs you something real.
"""

import hashlib
import math


class BloomFilter:
    def __init__(self, expected_items, false_positive_rate=0.01):
        # These two formulas come from the Bloom filter maths.
        # size  = how many bits we need
        # hashes = how many hash functions to use
        self.size = int(-expected_items * math.log(false_positive_rate) / (math.log(2) ** 2))
        self.hash_count = max(1, int(self.size / expected_items * math.log(2)))

        # One bit per slot. A bytearray holds 8 bits per byte.
        self.bits = bytearray(math.ceil(self.size / 8))
        self.items_added = 0

    def add(self, item):
        for position in self._positions(item):
            self.bits[position // 8] |= 1 << (position % 8)
        self.items_added += 1

    def __contains__(self, item):
        """True means 'maybe'. False means 'definitely not'."""
        return all(
            self.bits[position // 8] & (1 << (position % 8))
            for position in self._positions(item)
        )

    def _positions(self, item):
        """
        Turn one item into several bit positions.
        We use two hashes and combine them, which is a standard trick
        that behaves like having many independent hash functions.
        """
        data = str(item).encode()
        h1 = int(hashlib.md5(data).hexdigest(), 16)
        h2 = int(hashlib.sha1(data).hexdigest(), 16)
        return [(h1 + i * h2) % self.size for i in range(self.hash_count)]

    def memory_kb(self):
        return len(self.bits) / 1024


def demo():
    expected = 10000
    bloom = BloomFilter(expected_items=expected, false_positive_rate=0.01)

    print(f"Bloom filter for {expected:,} items, target error rate 1%")
    print(f"  bits used    : {bloom.size:,}")
    print(f"  hash funcs   : {bloom.hash_count}")
    print(f"  memory       : {bloom.memory_kb():.1f} KB")

    added = {f"https://site.com/page/{i}" for i in range(expected)}
    for url in added:
        bloom.add(url)

    print("\nChecking items we DID add:")
    found = sum(1 for url in added if url in bloom)
    print(f"  {found:,} / {len(added):,} found   -> no false negatives, ever")

    print("\nChecking 10,000 items we did NOT add:")
    never_added = [f"https://other.com/page/{i}" for i in range(10000)]
    false_positives = sum(1 for url in never_added if url in bloom)
    print(f"  {false_positives} wrongly reported as seen  ({false_positives/10000:.2%})")
    print("  -> close to the 1% we asked for")

    # memory comparison
    real_set_bytes = sum(len(u.encode()) + 49 for u in added)  # rough python set overhead
    print(f"\nMemory for the same data:")
    print(f"  python set    ~{real_set_bytes/1024:>8,.0f} KB")
    print(f"  bloom filter   {bloom.memory_kb():>8,.1f} KB")
    print(f"  -> about {real_set_bytes/1024/bloom.memory_kb():.0f}x smaller")


if __name__ == "__main__":
    demo()
