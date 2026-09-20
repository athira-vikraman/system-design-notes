# Cheatsheet — Revise in 10 Minutes

Read this the morning of an interview. Nothing new here — only what you
must be able to recall instantly.

---

## The framework

```
1. Clarify      5 min   Ask before you design. Never assume
2. Scope        2 min   Say what you will and will not build
3. Estimate     5 min   Users, QPS, storage
4. Design      10 min   Draw the boxes and the request flow
5. Deep dive   15 min   Go deep where they point
6. Trade-offs   5 min   Name the bottleneck and the fix
```

**Biggest mistake:** designing before asking. **Second biggest:** going quiet.

---

## Questions to ask first

```
How many users? Daily active?
Read-heavy or write-heavy?
How fast must it be?
Does it need to be exact, or is slightly stale fine?
Which features are in scope? Which are out?
Mobile, web, or both?
```

---

## Estimation

```
1 day = 86,400 sec   ->  use 100,000

QPS      = daily requests / 100,000
Peak QPS = QPS x 2  (x3 if spiky)
Storage  = items/day x size x 365
```

**Latency ladder — memorise the shape, not the digits:**

```
RAM                    100 ns      instant
SSD                    100 us      1,000x slower than RAM
Inside datacenter      500 us
Disk seek               10 ms      100x slower than SSD
Across the world       150 ms      physics; you cannot fix this
```

**Rules of thumb:** reads are usually ~100x writes · assume 500 bytes per text
record · 2 MB per photo.

---

## Numbers for a 30-second estimate

```
Twitter-scale:   300M users · 3,000 writes/sec · 300,000 reads/sec
Instagram-scale: 500M daily · 100M photos/day  · 200 TB/day
Chat-scale:      50M daily  · 23,000 msgs/sec
```

---

## CAP — pick one when the network breaks

```
CP  -> refuse rather than be wrong   -> money, inventory, bookings
AP  -> always answer, may be stale   -> feeds, likes, analytics
```

P is never optional. Networks fail.

---

## SQL or NoSQL

```
SQL     relationships, transactions, money        <- the default
NoSQL   huge simple data, logs, feeds, chat
```

Say *why*. "I chose Postgres because orders need ACID transactions" scores.
"I chose MongoDB because it scales" does not.

---

## Fixing bottlenecks, in order

```
Too much traffic     -> load balancer + more servers (stateless!)
Reads slow           -> cache, then read replicas
Writes slow          -> queue it, batch it
Data too big         -> shard (last resort)
Users far away       -> CDN
Something will fail   -> timeout, retry + backoff + jitter, circuit breaker
```

**Cache reads. Queue writes.** That sentence solves most of the problem.

---

## Words that earn marks

| Say this | Because it shows |
| --- | --- |
| "The trade-off here is..." | You know nothing is free |
| "This is read-heavy, so..." | You design from the data |
| "The bottleneck will be..." | You can see your own weakness |
| "I'd start simple and scale when..." | Judgement, not buzzwords |
| "What happens if this server dies?" | You think about failure |
| "Let me estimate that" | You are not guessing |

---

## Traps

```
Designing before asking questions
Saying "microservices" with no reason
Sharding a database that fits on one machine
Forgetting the system can fail
Averages instead of p99
Going silent while thinking
Defending a bad choice instead of adjusting
```

If the interviewer pushes back, **change your design.** They are testing whether
you can take input, not whether you can win an argument.

---

## The 60-second answer skeleton

> "Let me clarify a few things first — how many users, and is this read-heavy?
>
> Scope: I'll cover A, B, C, and skip D.
>
> Roughly N users means X writes/sec and Y reads/sec, about Z TB per year.
>
> Clients hit a load balancer, then stateless app servers. Reads check a Redis
> cache first, then the database. Slow work goes on a queue. Static files go
> through a CDN.
>
> The bottleneck is the database under read load. I'd add replicas first, and
> shard by user_id only if we outgrow that.
>
> If the cache dies we take the hit on the database; if a service dies, a
> circuit breaker stops the failure spreading."

Memorise the *shape* of this. Fill in the specifics per question.
