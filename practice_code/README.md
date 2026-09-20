# Practice Code

The theory files tell you *what* a pattern is. These files let you *run* it.

Every file is standalone, uses **only the Python standard library**, and
prints a demo that proves the idea with real numbers.

```bash
python 01_lru_cache.py      # run any file directly
python test_all.py          # run all 39 tests
```

## Files

| File | Pattern | What the demo proves |
| --- | --- | --- |
| [01_lru_cache.py](01_lru_cache.py) | Caching | O(1) get and put using a dict + linked list |
| [02_rate_limiter.py](02_rate_limiter.py) | Rate limiting | Token bucket allows bursts; users are independent |
| [03_consistent_hashing.py](03_consistent_hashing.py) | Consistent hashing | 26% of keys move instead of 75% |
| [04_bloom_filter.py](04_bloom_filter.py) | Bloom filter | 63x less memory, 0.99% false positives, zero false negatives |
| [05_url_shortener.py](05_url_shortener.py) | Base62 encoding | 7 chars = 3.5 trillion codes, no collisions |
| [06_load_balancer.py](06_load_balancer.py) | Load balancing | 4 strategies; traffic reroutes when a server dies |
| [07_circuit_breaker.py](07_circuit_breaker.py) | Circuit breaker | A dead service receives 3 calls instead of 6 |
| [08_retry_backoff.py](08_retry_backoff.py) | Retry + jitter | Delays grow 1s, 2s, 4s; jitter spreads the herd |
| [09_message_queue.py](09_message_queue.py) | Async queue | User waits 0 ms; retries work; dead letter queue |
| [10_sharding.py](10_sharding.py) | Sharding | Hash spreads evenly, range creates a hot shard |
| [test_all.py](test_all.py) | — | 39 tests covering all of the above |

## Numbers worth seeing for yourself

Run `03` and `04`. These are the two where the theory sounds like hand-waving
until you measure it:

```
Adding a 4th server to a 3-server cluster (10,000 keys):
  hash % N             7,466 keys moved  (74.7%)   <- every cache empties
  consistent hashing   2,626 keys moved  (26.3%)   <- 25% is the theoretical floor

Bloom filter, 10,000 URLs:
  python set    ~731 KB
  bloom filter    11.7 KB     63x smaller
  false positives  0.99%      exactly the 1% we asked for
  false negatives  0          the guarantee never breaks
```

## Exercises

The files are deliberately incomplete. Try these, then run `test_all.py`.

**Beginner**
1. Add `delete(key)` to `LRUCache`.
2. Add an LFU cache (evict *least frequently* used) next to the LRU one.
3. Make the URL shortener reject URLs that do not start with `http`.
4. Add a `weighted_round_robin` strategy to the load balancer, so a bigger
   server gets more traffic.

**Intermediate**
5. Add TTL expiry to `LRUCache`: entries older than N seconds are gone.
6. In `03`, plot how the spread changes with `VIRTUAL_NODES = 1, 10, 150`.
   Explain in one sentence why 1 is bad.
7. Add a "fail open" mode to the rate limiter: if Redis (here, the bucket
   store) is unavailable, allow traffic rather than block the site.
8. Add an idempotency key to the message queue so a job published twice
   runs once. (See `DESIGN_PATTERNS.md` #11.)

**Advanced**
9. Give the circuit breaker a half-open limit: allow 3 test requests, and
   only close if all 3 succeed.
10. In `10_sharding.py`, rebuild the router on top of `HashRing` from `03`
    so adding a shard does not reshuffle everything.
11. Add replication to the sharding router: write each key to 2 shards, and
    read from either. What happens when they disagree?
12. Combine files: put the rate limiter in front of the load balancer, and a
    circuit breaker behind it. That is roughly a real API gateway.

## How this maps to the notes

```
01, 02, 06        -> DESIGN_PATTERNS.md  #1, #2, #8
03, 04, 10        -> DESIGN_PATTERNS.md  #4, #12, #14
07, 08            -> DESIGN_PATTERNS.md  #9, #10
09                -> DESIGN_PATTERNS.md  #5
05                -> PRACTICE_PROBLEMS.md #1
```

## A warning

These are teaching versions. Real systems use Redis, Kafka, Envoy and so on.
The point is not to build your own — it is that when an interviewer asks
*"how would you implement a rate limiter?"*, you have written one and can
answer from memory instead of from a blog post.
