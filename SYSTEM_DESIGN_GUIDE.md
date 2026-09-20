# System Design — Beginner to Advanced

Short explanations in simple English, with a real example for each idea.

**How to use this file:** read Part 1 fully before touching Part 2. Most people
fail system design interviews because their basics are shaky, not because they
do not know exotic topics.

---

# PART 0 — WHAT IS SYSTEM DESIGN?

Designing how the pieces of a software system fit together so it stays fast,
stays up, and handles many users.

Writing code = "make this function work."
System design = "make this work for 10 million people, at 3 AM, when one server catches fire."

**Two types:**

| Type | Meaning | Example question |
| --- | --- | --- |
| **HLD** (High Level Design) | Boxes and arrows. Which servers, databases, queues. | "Design Instagram" |
| **LLD** (Low Level Design) | Classes, functions, database tables. | "Design the class structure for a parking lot" |

This guide is mostly HLD, which is what most interviews ask.

**There is no correct answer.** Every choice trades one thing for another.
Interviewers watch *how you decide*, not *what you decide*.

---

# PART 1 — BEGINNER

## 1. What happens when you open a website

The most important question in all of system design. Every topic below is a
piece of this.

```
You type google.com
     |
 1.  DNS             turns "google.com" into an IP address like 142.250.x.x
     |
 2.  TCP handshake   your computer and the server agree to talk
     |
 3.  HTTPS           they agree on encryption
     |
 4.  Load balancer   picks one of many servers
     |
 5.  Web server      runs the code
     |
 6.  Cache?          is the answer already saved? -> send it back fast
     |
 7.  Database        if not, fetch the real data
     |
 8.  Response        HTML/JSON travels back to you
```

## 2. Client and Server

- **Client** — asks for something (your browser, a phone app).
- **Server** — answers.

Clients should be dumb and replaceable. Servers hold the real logic.

## 3. Latency vs Throughput

| Term | Meaning | Example |
| --- | --- | --- |
| **Latency** | Time for ONE request | "The page loads in 200 ms" |
| **Throughput** | How many requests per second | "We handle 5,000 requests/second" |

They are different. A system can be fast for one user and still collapse under
1,000 users.

**Numbers worth memorising** (rough, but enough for interviews):

```
Read from memory (RAM)        ~100 nanoseconds     <- instant
Read from SSD                 ~100 microseconds    <- 1,000x slower than RAM
Round trip inside datacenter  ~500 microseconds
Read from hard disk (seek)    ~10 milliseconds     <- 100x slower than SSD
India to USA and back         ~150 milliseconds    <- the speed of light is the limit
```

**The lesson:** memory is free, disk is slow, the network is slower, and
crossing the planet is slowest. Good design means avoiding the bottom rows.

## 4. Scaling — handling more users

| | Vertical scaling | Horizontal scaling |
| --- | --- | --- |
| **What** | Make one server bigger | Add more servers |
| **Like** | Upgrading your laptop's RAM | Buying more laptops |
| **Good** | Simple, no code changes | Almost unlimited, survives failures |
| **Bad** | Has a hard ceiling. One server = one point of failure | Harder. Code must be stateless |

Real systems start vertical (it is cheap and easy) and go horizontal when
they must.

## 5. Load Balancer

Sits in front of your servers and spreads requests between them.

```
              +--> Server 1
Users --> LB  +--> Server 2
              +--> Server 3
```

**How it picks a server:**

| Method | How it works |
| --- | --- |
| Round robin | One after another, in order |
| Least connections | Whoever is least busy right now |
| IP hash | Same user always goes to the same server |

It also does **health checks**: if Server 2 stops replying, the load balancer
stops sending traffic there. This is how a server can die at 3 AM without
waking anyone up.

## 6. Stateless vs Stateful — the rule that makes scaling possible

**Stateful (bad for scaling):** the server remembers who you are in its own memory.

> You log in → Server 1 remembers you → next request goes to Server 2 →
> Server 2 has no idea who you are → you are logged out.

**Stateless (good):** the server remembers nothing. Identity travels with the
request (a token) or lives in shared storage (Redis).

> Any server can answer any request. Now you can add 100 servers freely.

**Rule: keep your servers stateless. Push state into a database or cache.**

## 7. Caching

Storing the answer so you do not have to compute it again.

> A user's profile is read 10,000 times a day but changes twice a year.
> Reading the database 10,000 times is wasteful. Save it in memory instead.

**Where caches live:**

```
Browser cache   -> on the user's device
CDN             -> in a city near the user
Server cache    -> in the app's own memory
Redis/Memcached -> a shared cache all servers use   <- most common
Database cache  -> inside the database
```

**Cache strategies:**

| Strategy | How it works | Use when |
| --- | --- | --- |
| **Cache-aside** | App checks cache; if missing, reads DB and fills cache | Most common. Default choice |
| **Write-through** | Write to cache and DB at the same time | You need the cache always correct |
| **Write-back** | Write to cache now, DB later | Very fast writes, risk of data loss |

**Eviction — the cache is full, what do we delete?**

- **LRU** (Least Recently Used) — delete what nobody touched for longest. Default choice.
- **LFU** (Least Frequently Used) — delete what is used least often.
- **TTL** (Time To Live) — delete after N seconds, no matter what.

**The hard part:** *cache invalidation*. If the data changes in the DB but the
cache still has the old copy, users see stale data. Options: short TTL, or
delete the cache entry whenever you update the DB.

## 8. Databases — SQL vs NoSQL

| | SQL (Postgres, MySQL) | NoSQL (MongoDB, Cassandra, DynamoDB) |
| --- | --- | --- |
| **Shape** | Tables, rows, fixed columns | Documents / key-value / wide column |
| **Schema** | Fixed. Every row looks the same | Flexible. Rows can differ |
| **Joins** | Yes, powerful | Usually no |
| **Guarantees** | ACID — money-safe | Often eventual consistency |
| **Scaling** | Hard to scale writes | Built to scale horizontally |
| **Use for** | Payments, orders, anything with relationships | Logs, feeds, chat, huge simple data |

**ACID** (what SQL gives you):

- **A**tomic — all of it happens, or none of it. A bank transfer never takes
  money from one account without adding it to the other.
- **C**onsistent — rules are never broken.
- **I**solated — two transactions do not corrupt each other.
- **D**urable — once saved, it survives a power cut.

**Honest advice:** default to SQL. Postgres handles far more load than beginners
think. Choose NoSQL for a specific reason you can name.

## 9. Indexes

A sorted lookup structure that makes reads fast.

> Finding one name in a 1,000-page book: reading every page = slow.
> Using the index at the back = instant.

```sql
CREATE INDEX idx_email ON users(email);
```

**The trade-off:** indexes make reads faster but writes slower (every write must
also update the index), and they use disk space. **Do not index everything.**

## 10. CDN (Content Delivery Network)

Copies of your images, CSS and videos stored in cities around the world.

> Your server is in Mumbai. A user in Brazil waits 300 ms for an image.
> With a CDN, the image is served from São Paulo in 20 ms.

Use it for static files that rarely change. Examples: Cloudflare, CloudFront.

---

# PART 2 — INTERMEDIATE

## 11. Replication — copies of your database

**Leader–Follower (most common):**

```
Writes --> LEADER
              |  copies changes to
              +--> Follower 1 --> serves reads
              +--> Follower 2 --> serves reads
```

- All writes go to the leader.
- Reads spread across followers → handles many more readers.
- If the leader dies, a follower is promoted.

**The catch — replication lag.** A follower may be a few hundred milliseconds
behind. A user posts a comment, then refreshes, and it is missing. Fix: read
that user's own data from the leader.

## 12. Sharding (Partitioning) — splitting your data

One database cannot hold 100 TB. So split it across machines.

```
users A-H  -> Database 1
users I-P  -> Database 2
users Q-Z  -> Database 3
```

| Method | How | Problem |
| --- | --- | --- |
| **Range** | Split by value range (A–H, I–P) | Uneven. Far more names start with S than X |
| **Hash** | `hash(user_id) % number_of_shards` | Even, but adding a shard reshuffles everything |
| **Directory** | A lookup table says where each user lives | Flexible, but the table is a new bottleneck |

**Costs of sharding:** joins across shards are painful, transactions across
shards are very hard, and one popular user can overload a single shard
(a "hot shard"). **Shard late, only when you must.**

## 13. Consistent Hashing

Fixes the "adding a shard reshuffles everything" problem.

Imagine servers placed around a circle. Each piece of data goes clockwise to
the next server. Add a new server and only the data between it and its
neighbour moves — not everything.

```
        Server A
       /        \
   data          Server B
       \        /
        Server C
```

Used by Cassandra, DynamoDB, and by load balancers that need sticky routing.

## 14. CAP Theorem

When the network breaks between your servers, you must pick **two of three**:

- **C**onsistency — everyone sees the same data
- **A**vailability — every request gets an answer
- **P**artition tolerance — the system survives network failures

Networks *do* fail, so **P is not optional**. The real choice is C or A:

| Pick | Meaning | Use for |
| --- | --- | --- |
| **CP** | Refuse to answer rather than give wrong data | Banking, inventory, bookings |
| **AP** | Always answer, even if slightly stale | Social feeds, likes, analytics |

> Instagram like counts: AP. If your count is briefly wrong, nobody cares.
> Your bank balance: CP. Better an error than a wrong number.

## 15. Consistency Models

| Model | Meaning |
| --- | --- |
| **Strong** | Once written, every read sees the new value. Slow but safe |
| **Eventual** | Reads may be stale, but all copies agree *eventually* |
| **Read-your-writes** | You always see your own changes; others may lag. Good middle ground |

## 16. Message Queues — doing work later

Instead of making the user wait, put the job in a queue.

**Without a queue:**
```
User signs up --> save to DB --> send email (2 sec) --> resize image (3 sec) --> reply
User waits 5+ seconds. If the email service is down, signup fails.
```

**With a queue:**
```
User signs up --> save to DB --> put 2 jobs in queue --> reply immediately (50 ms)
                                        |
                              Workers do the slow jobs in the background
```

**What you gain:** fast responses, survives spikes (the queue absorbs them), and
a failed email no longer breaks signup.

Tools: RabbitMQ, AWS SQS, Kafka (Kafka is more a log/stream than a plain queue).

## 17. Idempotency — safe retries

An operation you can run many times with the same result as running it once.

> A user taps "Pay" and the network hiccups. The phone retries.
> Without idempotency: charged twice.
> With it: the client sends a unique key; the server sees the key already
> processed and returns the original result.

Any operation that gets retried must be idempotent. This is a favourite
interview follow-up.

## 18. Rate Limiting

Stopping one user from overwhelming your system.

| Algorithm | How it works |
| --- | --- |
| **Fixed window** | Max 100 requests per minute. Simple, but allows bursts at the boundary |
| **Sliding window** | Counts the last 60 seconds continuously. Smoother |
| **Token bucket** | Tokens refill steadily; each request spends one. Allows short bursts. Most popular |
| **Leaky bucket** | Requests drain at a fixed rate. Very smooth output |

Return HTTP **429 Too Many Requests** when the limit is hit.

## 19. API Styles

| Style | Best for | Notes |
| --- | --- | --- |
| **REST** | Public APIs, general use | Simple, uses normal HTTP. The default |
| **GraphQL** | Apps that need flexible data | Client asks for exactly the fields it wants |
| **gRPC** | Service-to-service inside your system | Binary, very fast, not browser-friendly |
| **WebSockets** | Chat, live updates, games | Connection stays open both ways |

## 20. Proxies

- **Forward proxy** — sits in front of the *client*. Hides the user. (VPN)
- **Reverse proxy** — sits in front of the *server*. Hides your servers, does
  SSL, caching, rate limiting. (Nginx)

A load balancer is a kind of reverse proxy.

---

# PART 3 — ADVANCED

## 21. Monolith vs Microservices

| | Monolith | Microservices |
| --- | --- | --- |
| **What** | One app, one deploy | Many small apps, deployed separately |
| **Good** | Simple, easy to debug, fast to build | Teams work independently, scale each part separately |
| **Bad** | One team blocks another; scale all or nothing | Network failures, hard debugging, operational cost |

**Advice that interviewers respect:** start with a monolith. Split into
services when a specific team or scaling problem forces you to. Most companies
adopt microservices too early and regret it.

## 22. Event-Driven Architecture

Services do not call each other. They announce facts, and interested services
react.

```
Order Service --> publishes "OrderPlaced" --> [ Kafka ]
                                                 |
                              +------------------+-------------------+
                              |                  |                   |
                      Email Service      Inventory Service    Analytics Service
```

The Order Service does not know or care who listens. Add a new service later
without touching it.

**Event Sourcing** — store the list of events, not the current state.
Like a bank statement: you keep every transaction, and the balance is
calculated from them. You can replay history and see how any value came to be.

**CQRS** — use one model for writes and a different one for reads. Useful when
reads and writes have very different shapes and loads.

## 23. Distributed Transactions

Updating two services at once is genuinely hard.

**Two-Phase Commit (2PC):** a coordinator asks everyone "ready?", then tells
everyone "commit". Correct, but slow, and if the coordinator dies everything
freezes. Rarely used today.

**Saga (the practical answer):** break it into steps, each with an undo step.

```
Book flight   --> ok
Book hotel    --> ok
Book taxi     --> FAILED
                   |
               undo hotel, undo flight
```

You lose instant consistency but keep the system available.

## 24. Consensus — how servers agree

When the leader dies, who becomes the new leader? Everyone must agree, even
though the network is unreliable.

**Raft** and **Paxos** are the algorithms that solve this. Raft is the one
people actually implement because it is understandable.

The core idea: a **majority (quorum)** must agree. With 5 servers you need 3.
This is why clusters have odd numbers — so a majority always exists.

Used by: etcd, Consul, ZooKeeper, Kafka's controller.

## 25. Handling Failure

**Assume everything fails.** Design for it.

| Pattern | What it does |
| --- | --- |
| **Retry with exponential backoff** | Retry after 1s, 2s, 4s, 8s — not instantly |
| **Jitter** | Add randomness to retries, so 10,000 clients do not retry at the same instant |
| **Circuit breaker** | After many failures, stop calling the broken service for a while. Let it recover |
| **Timeout** | Never wait forever. Always set one |
| **Bulkhead** | Isolate resources so one failing part cannot drown the rest |
| **Graceful degradation** | Recommendations service down? Show popular items instead of an error page |

**Circuit breaker states:** `Closed` (normal) → too many errors →
`Open` (fail instantly, do not call) → after a wait → `Half-Open`
(try one request) → success → `Closed`.

## 26. Observability

You cannot fix what you cannot see.

- **Logs** — what happened. ("User 42 failed login at 10:03")
- **Metrics** — numbers over time. (requests/sec, error rate, p99 latency)
- **Traces** — one request's journey across all services. Shows which service was slow.

**Use percentiles, not averages.** An average of 100 ms can hide the fact that
1% of users wait 5 seconds. Watch **p99**: "99% of users are faster than this."

## 27. Security Basics

| Term | Meaning |
| --- | --- |
| **Authentication** | Who are you? (login) |
| **Authorization** | What are you allowed to do? (permissions) |
| **JWT** | A signed token carrying user info. Stateless — no DB lookup needed |
| **OAuth 2.0** | "Sign in with Google" — access without sharing passwords |
| **HTTPS/TLS** | Encrypts data in transit. Always on |
| **Hashing** | Store passwords with bcrypt or argon2, **never** plain text |

Also: validate all input, use parameterised SQL queries (stops SQL injection),
and encrypt sensitive data at rest.

## 28. Deployment Strategies

| Strategy | How |
| --- | --- |
| **Blue-Green** | Two identical environments. Switch traffic over at once. Instant rollback |
| **Canary** | Send 1% of users to the new version. Watch. Then 10%, 50%, 100% |
| **Rolling** | Replace servers a few at a time |
| **Feature flag** | Ship the code turned off, switch it on for chosen users |

---

# PART 4 — THE INTERVIEW

## 29. Back-of-the-envelope estimation

Interviewers want rough numbers, fast. Round aggressively.

**Data sizes:**
```
1 KB  = 1,000 bytes        char = 1 byte
1 MB  = 1,000 KB           a typical web page ~ 1 MB
1 GB  = 1,000 MB           an HD movie ~ 1 GB
1 TB  = 1,000 GB
```

**Time:**
```
1 day  = 86,400 seconds  -> just use 100,000 (10^5)
1 month = 2.5 million seconds
1 year  = 31 million seconds
```

**The QPS formula:**
```
QPS = daily requests / 100,000
Peak QPS = QPS x 2  (or x3 for spiky apps)
```

**Worked example — Twitter:**
```
300 million users, 50% active daily      = 150 million daily users
Each posts 2 tweets                      = 300 million tweets/day
Write QPS = 300,000,000 / 100,000        = 3,000 writes/sec
Reads are ~100x writes                   = 300,000 reads/sec
Storage: 300M tweets x 300 bytes         = 90 GB/day  -> ~33 TB/year
```

That is the whole skill. Round numbers, one step at a time, say your
assumptions out loud.

## 30. The 6-step framework

Use this for every question. **Do not start drawing boxes immediately.**

**1. Clarify (5 min)** — Ask questions first. Never assume.
> "Is this for 1,000 users or 100 million?" "Do we need real-time updates?"
> "Read-heavy or write-heavy?" "Do we need to support editing and deleting?"

**2. Define scope (2 min)** — Agree what you will build.
> "I will cover posting, the feed, and following. I will skip DMs and ads."

**3. Estimate (5 min)** — Users, QPS, storage. (Section 29.)

**4. High-level design (10 min)** — Draw the boxes.
> Client → Load balancer → App servers → Cache → Database, plus a queue and CDN.

**5. Deep dive (15 min)** — The interviewer picks one area. Go deep on the
database schema, the sharding key, or how the feed is built.

**6. Discuss trade-offs (5 min)** — Name bottlenecks and how you would fix them.
> "The database is the bottleneck. I would add read replicas, then shard by user_id."

**What interviewers are actually scoring:** do you ask questions before solving,
do you justify choices, do you spot your own bottlenecks, and can you explain
clearly. Silence is the biggest mistake — **think out loud.**

## 31. Worked example — design a URL shortener

The classic first question. Learn this one properly.

**Requirements**
- Shorten a long URL into a short one
- Visiting the short URL redirects to the original
- 100 million new URLs per month
- Read-heavy: ~100 reads per write

**Estimates**
```
Writes: 100M/month = 40 writes/sec
Reads:  40 x 100   = 4,000 reads/sec
Storage: 100M x 500 bytes x 12 months = 600 GB/year
```

**The short code**
Use base62 (`a-z A-Z 0-9`). 7 characters = 62^7 ≈ 3.5 trillion combinations.
Enough for decades.

How to generate it:
- **Counter + base62** — take an auto-incrementing number and convert it.
  Simple, no collisions. But codes are guessable, and the counter is a single
  point of failure. Fix: give each server a block of numbers to hand out.
- **Hash the URL, take 7 characters** — needs collision checking.

**Design**
```
                    +--> Cache (Redis) --- hit? redirect immediately
User --> LB --> App |
                    +--> Database  (short_code -> long_url)
```

**Schema**
```
urls
  short_code   VARCHAR(7)  PRIMARY KEY
  long_url     TEXT
  user_id      BIGINT
  created_at   TIMESTAMP
  expires_at   TIMESTAMP
```

**Why this works:** reads are 100x writes, and a URL never changes once created
— which makes it perfect for caching. Cache the hot 20% and the database
barely gets touched.

**Trade-offs to mention:**
- Redirect code: `301` (permanent) is cached by browsers, so you lose click
  analytics. `302` (temporary) gives you analytics but more traffic.
- Scaling: shard by `short_code`.
- Custom aliases: check availability before saving.

## 32. Common interview questions

**Start here:** URL shortener · Pastebin · Rate limiter · Parking lot

**Then:** Twitter feed · Instagram · WhatsApp chat · Dropbox · Web crawler ·
Notification system · Typeahead/autocomplete

**Hard:** YouTube/Netflix · Uber · Google Maps · Distributed cache ·
Payment system · Ticketmaster

---

# PART 5 — RESOURCES

## YouTube

**Two full free courses — start with one of these:**

| Video | Why |
| --- | --- |
| [System Design Concepts Course and Interview Prep](https://www.youtube.com/watch?v=F2FmTdLtb_4) — freeCodeCamp, by Hayk Simonyan | Best single starting point. Covers scalability, caching, databases, load balancers, replication, sharding, CDNs, plus DNS/TCP/HTTP and REST/GraphQL/gRPC |
| [System Design Interview Prep for Beginners (Full Course)](https://www.youtube.com/watch?v=oz5c88cO5P8) | Built around a reusable framework you can apply to any question |

**Channels, in the order you should use them:**

| Channel | Best for |
| --- | --- |
| [Gaurav Sen](https://www.youtube.com/@gkcs) | **Start here.** Assumes no distributed-systems knowledge. Builds up from fundamentals with analogies and drawings |
| [ByteByteGo](https://www.youtube.com/@ByteByteGo) | Short, polished animations of how real products are built. Excellent for revision |
| [Hussein Nasser](https://www.youtube.com/@hnasr) | Deep technical layer most content skips — TCP under load, Postgres internals, proxies, HTTP/2 vs HTTP/3 |
| CodeKarle | Full walkthroughs of real interview questions, by an ex-Facebook engineer |
| Exponent | Recorded mock interviews. Watch these to learn how to *talk* during the interview |

**Suggested path:** freeCodeCamp course → Gaurav Sen fundamentals →
ByteByteGo for revision → Exponent mocks before your interview.

## Reading

- **System Design Primer** (GitHub, free) — the most complete free resource
- **Designing Data-Intensive Applications** by Martin Kleppmann — the best book
  on this subject. Read it after you finish Part 2 here
- **ByteByteGo newsletter** — short weekly explainers
- **High Scalability** blog — real architectures from real companies

## 8-week study plan

| Week | Do this |
| --- | --- |
| 1 | Part 1 of this file. Watch the freeCodeCamp course |
| 2 | Caching and databases. Install Redis and actually use it |
| 3 | Part 2: replication, sharding, CAP |
| 4 | Queues and async. Try RabbitMQ or SQS |
| 5 | Practise estimation. Design a URL shortener and Pastebin yourself |
| 6 | Part 3: microservices, events, failure handling |
| 7 | Design Twitter, WhatsApp, Instagram — write your answers down |
| 8 | Mock interviews. Say everything out loud, on a timer |

**The one habit that matters:** after every topic, sketch it on paper from
memory. Reading gives you recognition; drawing gives you recall. Only recall
survives an interview.

---

# ONE-PAGE SUMMARY

```
Too many users?          -> add servers behind a load balancer
Servers must be          -> stateless
Reads too slow?          -> cache (Redis), then read replicas
Database too big?        -> shard it (but only when you must)
Writes too slow?         -> queue them, process in the background
Users far away?          -> CDN
Something will fail      -> timeouts, retries with backoff + jitter, circuit breakers
Cannot see the problem?  -> logs, metrics, traces. Watch p99, not averages
Need to pick C or A?     -> money = C, feeds and likes = A
```

**The five sentences worth remembering:**

1. Every design choice is a trade-off. Say what you are trading.
2. Cache reads, queue writes.
3. Keep servers stateless so you can add more.
4. Shard late. It is harder than it looks.
5. Ask questions before you answer.
