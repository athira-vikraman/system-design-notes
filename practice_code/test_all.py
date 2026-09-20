"""
Tests for every implementation.

    python test_all.py

Filenames start with numbers, which Python cannot import normally,
so we load them by path.
"""

import importlib.util
import pathlib
import time
import unittest

HERE = pathlib.Path(__file__).parent


def load(filename):
    path = HERE / filename
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lru = load("01_lru_cache.py")
rate = load("02_rate_limiter.py")
ring = load("03_consistent_hashing.py")
bloom = load("04_bloom_filter.py")
shortener = load("05_url_shortener.py")
balancer = load("06_load_balancer.py")
breaker = load("07_circuit_breaker.py")
backoff = load("08_retry_backoff.py")
sharding = load("10_sharding.py")


class TestLRUCache(unittest.TestCase):
    def test_get_and_put(self):
        cache = lru.LRUCache(2)
        cache.put("a", 1)
        self.assertEqual(cache.get("a"), 1)
        self.assertIsNone(cache.get("missing"))

    def test_evicts_least_recently_used(self):
        cache = lru.LRUCache(2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)  # 'a' is oldest, should go
        self.assertIsNone(cache.get("a"))
        self.assertEqual(cache.get("b"), 2)

    def test_get_refreshes_recency(self):
        cache = lru.LRUCache(2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.get("a")     # 'a' is now newest, so 'b' is oldest
        cache.put("c", 3)
        self.assertEqual(cache.get("a"), 1)
        self.assertIsNone(cache.get("b"))

    def test_update_does_not_grow(self):
        cache = lru.LRUCache(2)
        cache.put("a", 1)
        cache.put("a", 99)
        self.assertEqual(cache.get("a"), 99)
        self.assertEqual(len(cache.map), 1)


class TestRateLimiter(unittest.TestCase):
    def test_allows_up_to_capacity(self):
        bucket = rate.TokenBucket(capacity=3, refill_per_second=1)
        self.assertEqual([bucket.allow() for _ in range(5)],
                         [True, True, True, False, False])

    def test_refills_over_time(self):
        bucket = rate.TokenBucket(capacity=2, refill_per_second=10)
        bucket.allow()
        bucket.allow()
        self.assertFalse(bucket.allow())
        time.sleep(0.25)  # ~2 tokens back
        self.assertTrue(bucket.allow())

    def test_users_are_independent(self):
        limiter = rate.PerUserLimiter(capacity=1, refill_per_second=0)
        self.assertTrue(limiter.allow("athira"))
        self.assertFalse(limiter.allow("athira"))
        self.assertTrue(limiter.allow("ravi"))

    def test_sliding_window(self):
        window = rate.SlidingWindow(max_requests=2, window_seconds=0.2)
        self.assertTrue(window.allow())
        self.assertTrue(window.allow())
        self.assertFalse(window.allow())
        time.sleep(0.25)
        self.assertTrue(window.allow())


class TestConsistentHashing(unittest.TestCase):
    def setUp(self):
        self.servers = ["s1", "s2", "s3"]
        self.keys = [f"key_{i}" for i in range(2000)]

    def test_same_key_same_server(self):
        hash_ring = ring.HashRing(self.servers)
        for key in self.keys[:50]:
            self.assertEqual(hash_ring.get(key), hash_ring.get(key))

    def test_moves_far_fewer_keys_than_modulo(self):
        hash_ring = ring.HashRing(self.servers)
        before = {k: hash_ring.get(k) for k in self.keys}
        hash_ring.add("s4")
        after = {k: hash_ring.get(k) for k in self.keys}
        moved = sum(1 for k in self.keys if before[k] != after[k])

        naive_moved = sum(
            1 for k in self.keys
            if ring.naive_get(k, self.servers) != ring.naive_get(k, self.servers + ["s4"])
        )
        # theory says ~1/4 move; modulo moves most of them
        self.assertLess(moved / len(self.keys), 0.35)
        self.assertLess(moved, naive_moved)

    def test_distribution_is_even(self):
        hash_ring = ring.HashRing(self.servers)
        counts = {}
        for key in self.keys:
            server = hash_ring.get(key)
            counts[server] = counts.get(server, 0) + 1
        for count in counts.values():
            share = count / len(self.keys)
            self.assertGreater(share, 0.20)  # ideal is 0.333
            self.assertLess(share, 0.47)

    def test_removing_a_server(self):
        hash_ring = ring.HashRing(self.servers)
        hash_ring.remove("s2")
        servers_used = {hash_ring.get(k) for k in self.keys}
        self.assertNotIn("s2", servers_used)

    def test_empty_ring(self):
        self.assertIsNone(ring.HashRing([]).get("anything"))


class TestBloomFilter(unittest.TestCase):
    def test_no_false_negatives(self):
        """The one guarantee that must never break."""
        bf = bloom.BloomFilter(expected_items=1000, false_positive_rate=0.01)
        items = [f"item_{i}" for i in range(1000)]
        for item in items:
            bf.add(item)
        for item in items:
            self.assertIn(item, bf)

    def test_false_positive_rate_near_target(self):
        bf = bloom.BloomFilter(expected_items=5000, false_positive_rate=0.01)
        for i in range(5000):
            bf.add(f"added_{i}")
        false_positives = sum(1 for i in range(5000) if f"never_{i}" in bf)
        self.assertLess(false_positives / 5000, 0.03)

    def test_empty_filter_contains_nothing(self):
        bf = bloom.BloomFilter(expected_items=100)
        self.assertNotIn("anything", bf)


class TestURLShortener(unittest.TestCase):
    def test_encode_decode_roundtrip(self):
        for number in [0, 1, 61, 62, 12345, 999999999]:
            self.assertEqual(shortener.decode(shortener.encode(number)), number)

    def test_codes_are_unique(self):
        service = shortener.URLShortener()
        codes = {service.shorten(f"https://site.com/{i}") for i in range(500)}
        self.assertEqual(len(codes), 500)

    def test_resolves_back_to_original(self):
        service = shortener.URLShortener()
        url = "https://example.com/page"
        self.assertEqual(service.resolve(service.shorten(url)), url)

    def test_same_url_reuses_code(self):
        service = shortener.URLShortener()
        url = "https://example.com/page"
        self.assertEqual(service.shorten(url), service.shorten(url))

    def test_custom_alias_conflict(self):
        service = shortener.URLShortener()
        service.shorten("https://a.com", custom="mine")
        with self.assertRaises(ValueError):
            service.shorten("https://b.com", custom="mine")

    def test_unknown_code(self):
        self.assertIsNone(shortener.URLShortener().resolve("short.ly/nope"))

    def test_click_counting(self):
        service = shortener.URLShortener()
        short = service.shorten("https://a.com", custom="x")
        for _ in range(3):
            service.resolve(short)
        self.assertEqual(service.clicks["x"], 3)


class TestLoadBalancer(unittest.TestCase):
    def servers(self):
        return [balancer.Server(f"s{i}") for i in range(3)]

    def test_round_robin_is_even(self):
        lb = balancer.LoadBalancer(self.servers(), "round_robin")
        picks = [lb.pick().name for _ in range(9)]
        self.assertEqual(sorted(picks), sorted(["s0", "s1", "s2"] * 3))

    def test_skips_unhealthy_servers(self):
        servers = self.servers()
        servers[1].healthy = False
        lb = balancer.LoadBalancer(servers, "round_robin")
        picks = {lb.pick().name for _ in range(20)}
        self.assertNotIn("s1", picks)

    def test_ip_hash_is_sticky(self):
        lb = balancer.LoadBalancer(self.servers(), "ip_hash")
        self.assertEqual(lb.pick("10.0.0.5").name, lb.pick("10.0.0.5").name)

    def test_least_connections(self):
        servers = self.servers()
        servers[0].active_connections = 10
        servers[1].active_connections = 1
        servers[2].active_connections = 5
        lb = balancer.LoadBalancer(servers, "least_connections")
        self.assertEqual(lb.pick().name, "s1")

    def test_all_servers_down(self):
        servers = self.servers()
        for server in servers:
            server.healthy = False
        with self.assertRaises(RuntimeError):
            balancer.LoadBalancer(servers, "round_robin").pick()


class TestCircuitBreaker(unittest.TestCase):
    def test_opens_after_threshold(self):
        cb = breaker.CircuitBreaker(failure_threshold=3, recovery_timeout=10)
        service = breaker.FlakyService()
        for _ in range(3):
            with self.assertRaises(ConnectionError):
                cb.call(service.fetch)
        self.assertEqual(cb.state, cb.OPEN)

    def test_blocks_calls_while_open(self):
        cb = breaker.CircuitBreaker(failure_threshold=2, recovery_timeout=10)
        service = breaker.FlakyService()
        for _ in range(2):
            with self.assertRaises(ConnectionError):
                cb.call(service.fetch)

        calls_before = service.calls_received
        with self.assertRaises(breaker.CircuitOpenError):
            cb.call(service.fetch)
        # the service was never touched
        self.assertEqual(service.calls_received, calls_before)

    def test_recovers_after_timeout(self):
        cb = breaker.CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        service = breaker.FlakyService()
        for _ in range(2):
            with self.assertRaises(ConnectionError):
                cb.call(service.fetch)

        time.sleep(0.15)
        service.working = True
        self.assertEqual(cb.call(service.fetch), "data")
        self.assertEqual(cb.state, cb.CLOSED)

    def test_success_resets_failures(self):
        cb = breaker.CircuitBreaker(failure_threshold=3, recovery_timeout=10)
        service = breaker.FlakyService()
        with self.assertRaises(ConnectionError):
            cb.call(service.fetch)
        service.working = True
        cb.call(service.fetch)
        self.assertEqual(cb.failures, 0)
        self.assertEqual(cb.state, cb.CLOSED)


class TestRetry(unittest.TestCase):
    def test_succeeds_after_transient_failures(self):
        state = {"calls": 0}

        @backoff.retry(max_attempts=4, base_delay=0.01)
        def flaky():
            state["calls"] += 1
            if state["calls"] < 3:
                raise ConnectionError("temporary")
            return "ok"

        self.assertEqual(flaky(), "ok")
        self.assertEqual(state["calls"], 3)

    def test_gives_up_and_reraises(self):
        state = {"calls": 0}

        @backoff.retry(max_attempts=3, base_delay=0.01)
        def broken():
            state["calls"] += 1
            raise ValueError("permanent")

        with self.assertRaises(ValueError):
            broken()
        self.assertEqual(state["calls"], 3)  # exactly max_attempts, no more

    def test_no_retry_when_it_works(self):
        state = {"calls": 0}

        @backoff.retry(max_attempts=3, base_delay=0.01)
        def fine():
            state["calls"] += 1
            return "ok"

        fine()
        self.assertEqual(state["calls"], 1)


class TestSharding(unittest.TestCase):
    def test_key_always_lands_on_same_shard(self):
        router = sharding.ShardRouter(4, "hash")
        for key in ["athira", "ravi", "priya"]:
            self.assertEqual(router._shard_for(key), router._shard_for(key))

    def test_write_then_read(self):
        router = sharding.ShardRouter(4, "hash")
        router.put("athira", "profile")
        self.assertEqual(router.get("athira"), "profile")
        self.assertIsNone(router.get("missing"))

    def test_hash_spreads_evenly(self):
        router = sharding.ShardRouter(4, "hash")
        for i in range(4000):
            router.put(f"user_{i}", i)
        for count in router.distribution().values():
            self.assertGreater(count / 4000, 0.20)  # ideal is 0.25

    def test_shard_in_valid_range(self):
        router = sharding.ShardRouter(4, "range")
        for key in ["apple", "zebra", "mango", "1numeric"]:
            shard = router._shard_for(key)
            self.assertGreaterEqual(shard, 0)
            self.assertLess(shard, 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
