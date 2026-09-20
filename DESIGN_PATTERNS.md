# Design Patterns — The Building Blocks

14 reusable pieces. Almost every system is a combination of these.

**Every pattern uses the same 5 boxes:**
`Problem` → `Solution` → `Diagram` → `Use / Avoid` → `Used by`

---

## 1. Load Balancing
**Problem** — One server cannot handle the traffic, and if it dies everything dies.

**Solution** — Put a load balancer in front of several identical servers.

```
          +--> Server 1
Users --> LB --> Server 2
          +--> Server 3   (health-checked; dead ones are skipped)
```

**Use** — Any system with more than one server.
**Avoid** — Nothing. This is a default.
**Used by** — Every web company. Nginx, HAProxy, AWS ELB.

---

## 2. Caching
**Problem** — The same expensive query runs thousands of times.

**Solution** — Store the answer in memory. Check it before touching the database.

```
App --> Cache --hit--> return (1 ms)
          |
         miss --> DB (100 ms) --> fill cache --> return
```

**Use** — Read-heavy data that rarely changes.
**Avoid** — Data that must always be exact, or that changes on every read.
**Used by** — Everyone. Redis, Memcached.

---

## 3. Read Replicas
**Problem** — The database handles writes fine, but reads are drowning it.

**Solution** — Copy the database. Writes go to the leader, reads to followers.

```
Writes --> LEADER --copies--> Follower 1 --> Reads
                     +-------> Follower 2 --> Reads
```

**Use** — Read-heavy systems (most systems).
**Avoid** — Write-heavy systems. This does not help writes at all.
**Watch for** — Replication lag: a user may not see their own change. Read that
user's own data from the leader.
**Used by** — Postgres streaming replication, MySQL read replicas, AWS RDS.

---

## 4. Sharding
**Problem** — The data no longer fits on one machine.

**Solution** — Split it by a key across several databases.

```
user_id % 3 == 0 --> Shard 0
user_id % 3 == 1 --> Shard 1
user_id % 3 == 2 --> Shard 2
```

**Use** — When you have genuinely outgrown one machine, plus replicas.
**Avoid** — Early. It makes joins and transactions much harder.
**Watch for** — Hot shards, where one popular key overloads a single machine.
**Used by** — Vitess (YouTube), MongoDB, Citus, DynamoDB.

---

## 5. Asynchronous Processing (Queues)
**Problem** — Slow work (emails, video encoding) makes the user wait.

**Solution** — Put the job in a queue and reply immediately. Workers handle it.

```
API --> Queue --> Worker 1
           |
           +----> Worker 2   (add workers to go faster)
```

**Use** — Anything slow, or anything calling an unreliable third party.
**Avoid** — When the user needs the result right now.
**Used by** — RabbitMQ, SQS, Kafka.

---

## 6. Fan-out
**Problem** — One event must reach many places.

**Solution** — Choose *when* to do the work.

```
Fan-out on WRITE: do it when posting   -> slow writes, instant reads
Fan-out on READ:  do it when reading   -> instant writes, slow reads
```

**Use** — Feeds and timelines. Reads outnumber writes, so prefer write.
**Avoid** — Pure write fan-out when one user has millions of followers.
**Fix** — Hybrid: fan-out on write for normal users, on read for celebrities.
**Used by** — Twitter timelines, Instagram feeds, Facebook News Feed.

---

## 7. CDN
**Problem** — Users far from your server wait for images and video.

**Solution** — Cache static files in cities worldwide.

```
User (Brazil) --> CDN edge (São Paulo)  20 ms
                       |  miss only
                  Origin (Mumbai)      300 ms
```

**Use** — Images, CSS, JS, video. Anything static.
**Avoid** — Personalised or rapidly changing data.
**Used by** — Cloudflare, CloudFront, Akamai.

---

## 8. Rate Limiting
**Problem** — One client can flood your system, by accident or on purpose.

**Solution** — Cap requests per user per time window. Reject with `429`.

```
Request --> [tokens left?] --yes--> Service
                 |no
              429 Too Many Requests
```

**Use** — Every public API.
**Avoid** — Internal calls where you trust the caller.
**Best default** — Token bucket, counters in Redis.
**Used by** — Stripe, GitHub and almost every public API.

---

## 9. Circuit Breaker
**Problem** — A dead service is called repeatedly; every call hangs until timeout,
and the failure spreads to healthy services.

**Solution** — After N failures, stop calling it. Fail instantly. Retry later.

```
CLOSED --too many errors--> OPEN --after 30s--> HALF-OPEN
   ^                                                |
   +--------------- success ------------------------+
```

**Use** — Every call to another service or third party.
**Avoid** — Local, in-process calls.
**Pairs with** — Graceful degradation: show something useful instead of an error.
**Used by** — Netflix (Hystrix), Resilience4j, Istio.

---

## 10. Retry with Backoff and Jitter
**Problem** — A request failed. Retrying immediately makes the overload worse.

**Solution** — Wait longer each time, plus a random amount.

```
attempt 1 --fail--> wait 1s  + random
attempt 2 --fail--> wait 2s  + random
attempt 3 --fail--> wait 4s  + random
attempt 4 --fail--> give up
```

**Use** — Any network call.
**Avoid** — Retrying non-idempotent operations blindly. You may charge twice.
**Why jitter** — Without randomness, 10,000 clients retry at the exact same
instant and knock the service over again.
**Used by** — Every AWS SDK does this by default.

---

## 11. Idempotency Key
**Problem** — A retried request must not run twice. Nobody wants a double charge.

**Solution** — The client sends a unique key. The server remembers keys it has
already processed and returns the original result.

```
POST /payment   Idempotency-Key: abc-123
   first time  --> charge, store result under abc-123
   retry       --> key seen, return stored result. No second charge
```

**Use** — Payments, orders, anything that creates something.
**Avoid** — Reads. They are already idempotent.
**Used by** — Stripe, PayPal, and most payment APIs.

---

## 12. Consistent Hashing
**Problem** — With `hash % N` servers, adding one server reshuffles almost all keys
and empties every cache at once.

**Solution** — Place servers on a ring. Each key goes clockwise to the next
server. Adding a server moves only its immediate neighbour's keys.

```
      A
    /   \
  key    B
    \   /
      C
```

**Use** — Distributed caches and databases.
**Avoid** — Fixed, never-changing server counts.
**Used by** — Cassandra, DynamoDB, Memcached clients.

---

## 13. Saga (Distributed Transactions)
**Problem** — One action spans several services. Step 3 fails after 1 and 2 succeeded.

**Solution** — Give each step an undo step. On failure, undo backwards.

```
Book flight  ok
Book hotel   ok
Book taxi    FAIL
             --> cancel hotel --> cancel flight
```

**Use** — Multi-service workflows where 2PC is too slow.
**Avoid** — Single-database work. Just use a normal transaction.
**Cost** — Other users may briefly see a half-finished state.
**Used by** — Booking and order systems; Temporal, Camunda.

---

## 14. Bloom Filter
**Problem** — "Have I seen this before?" across a billion items, without a
billion items in memory.

**Solution** — A compact bit array. Answers "definitely not seen" or "maybe seen".

```
1B URLs in a set      -> ~100 GB
1B URLs in a Bloom    -> ~1 GB
```

**Use** — Crawler dedupe; skipping pointless database lookups.
**Avoid** — When a wrong answer is unacceptable, or when you need deletion.
**Key property** — False positives are possible, false negatives are not.
**Used by** — Cassandra, HBase, Chrome Safe Browsing, web crawlers.

---

# Choosing a pattern

```
Reads too slow?          -> Cache (2), then Read Replicas (3)
Writes too slow?         -> Queues (5), then Sharding (4)
Data too big?            -> Sharding (4)
Users far away?          -> CDN (7)
Feeds and timelines?     -> Fan-out (6)
A service keeps dying?   -> Circuit Breaker (9) + Retry (10)
Duplicate requests?      -> Idempotency Key (11)
Servers come and go?     -> Consistent Hashing (12)
Multi-service workflow?  -> Saga (13)
"Have I seen this?"      -> Bloom Filter (14)
Someone abusing the API? -> Rate Limiting (8)
```

**The order matters.** Try them roughly top to bottom. Caching solves more
problems than sharding, and costs far less.
