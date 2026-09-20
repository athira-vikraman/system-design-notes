"""
LRU Cache  ->  DESIGN_PATTERNS.md #2 (Caching)

The cache is full. Which item do we throw away?
LRU = throw away whatever nobody has touched for the longest time.

Both get() and put() must be O(1). That is the whole challenge.

Trick: a dictionary gives O(1) lookup but no order.
       A doubly linked list gives O(1) reordering but no lookup.
       Use both together.
"""


class Node:
    """One item in the linked list."""

    def __init__(self, key=None, value=None):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None


class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.map = {}  # key -> Node, for O(1) lookup

        # Two fake nodes at the ends. They remove all the
        # "is this the first item?" edge cases.
        self.head = Node()  # most recently used side
        self.tail = Node()  # least recently used side
        self.head.next = self.tail
        self.tail.prev = self.head

    # ---------- public ----------

    def get(self, key):
        if key not in self.map:
            return None

        node = self.map[key]
        self._move_to_front(node)  # it was just used
        return node.value

    def put(self, key, value):
        if key in self.map:
            node = self.map[key]
            node.value = value
            self._move_to_front(node)
            return

        if len(self.map) >= self.capacity:
            self._evict()

        node = Node(key, value)
        self.map[key] = node
        self._add_to_front(node)

    def keys_newest_first(self):
        """Helper so you can see the order."""
        result = []
        node = self.head.next
        while node is not self.tail:
            result.append(node.key)
            node = node.next
        return result

    # ---------- internal ----------

    def _remove(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev

    def _add_to_front(self, node):
        node.next = self.head.next
        node.prev = self.head
        self.head.next.prev = node
        self.head.next = node

    def _move_to_front(self, node):
        self._remove(node)
        self._add_to_front(node)

    def _evict(self):
        """Drop the item just before tail: the least recently used."""
        oldest = self.tail.prev
        self._remove(oldest)
        del self.map[oldest.key]
        return oldest.key


def demo():
    print("LRU Cache, capacity 3\n")
    cache = LRUCache(3)

    for key, value in [("a", 1), ("b", 2), ("c", 3)]:
        cache.put(key, value)
        print(f"  put {key}  -> {cache.keys_newest_first()}")

    print(f"\n  get a -> {cache.get('a')}   (now 'a' is newest)")
    print(f"           {cache.keys_newest_first()}")

    print("\n  put d -> cache is full, so the oldest is dropped")
    cache.put("d", 4)
    print(f"           {cache.keys_newest_first()}   <- 'b' was evicted")

    print(f"\n  get b -> {cache.get('b')}   (gone, as expected)")


if __name__ == "__main__":
    demo()
