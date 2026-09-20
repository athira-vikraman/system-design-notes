# Practice Problems

13 problems, easy to hard. **Every problem uses the same 6 boxes**, so you
learn one shape and reuse it.

> **How to practise:** cover the answer. Give yourself 30 minutes and a sheet
> of paper. Write your own version first, then compare. Reading these without
> attempting them teaches you almost nothing.

**The 6 boxes:**
`Requirements` → `Scale` → `Design` → `Key decision` → `Trade-off` → `Follow-ups`

---

## 1. URL Shortener
**Level:** Beginner · **Tests:** hashing, caching, read-heavy design

**Requirements** — Shorten a URL; redirect on visit. Optional: custom alias, expiry.

**Scale** — 100M new/month = 40 writes/sec. Reads 100x = 4,000/sec. 600 GB/year.

**Design**
```
User --> LB --> App --> Cache (Redis) --> DB (short_code -> long_url)
```

**Key decision** — Short code: a counter converted to base62, 7 chars = 3.5 trillion
options. No collisions, unlike hashing.

**Trade-off** — `301` redirect is cached by the browser (fast, but you lose click
analytics). `302` is not cached (slower, keeps analytics).

**Follow-ups** — How do you stop guessable codes? How do you expire old URLs?

---

## 2. Pastebin
**Level:** Beginner · **Tests:** blob storage, expiry

**Requirements** — Paste text, get a link. Text expires after a set time.

**Scale** — 1M pastes/day = 12 writes/sec. Average 10 KB = 10 GB/day.

**Design**
```
User --> LB --> App --> DB (metadata only)
                  |
                  +--> Object storage (S3) for the actual text
```

**Key decision** — Keep the text in object storage, not the database. Databases
are expensive per GB; S3 is cheap and built for blobs. The DB stores only the
id, the S3 path and the expiry time.

**Trade-off** — Two systems to keep in sync. A background job deletes expired
pastes from both.

**Follow-ups** — Private pastes? Syntax highlighting? How do you handle a paste
that goes viral?

---

## 3. Rate Limiter
**Level:** Beginner · **Tests:** algorithms, distributed counters

**Requirements** — Allow N requests per user per minute. Return `429` beyond it.

**Scale** — Must add under 1 ms to every request.

**Design**
```
User --> API Gateway --> [Rate limiter] --> Service
                              |
                          Redis (counter per user)
```

**Key decision** — **Token bucket.** Tokens refill at a steady rate; each request
spends one. Allows short bursts, which real users produce, unlike fixed windows.

**Trade-off** — The counter must be shared across all servers, so Redis becomes a
dependency on every request. Use Redis `INCR` with a TTL — it is atomic and fast.

**Follow-ups** — What if Redis goes down? (Fail open: allow traffic, do not break
the site.) How do you limit per-IP *and* per-user at once?

---

## 4. Notification System
**Level:** Intermediate · **Tests:** queues, fan-out, third-party failure

**Requirements** — Send push, SMS and email. Must not lose a notification.

**Scale** — 10M notifications/day = 120/sec, with sharp peaks.

**Design**
```
Service --> Queue --> Workers --> +--> APNs / FCM  (push)
                                  +--> Twilio      (SMS)
                                  +--> SendGrid    (email)
```

**Key decision** — A queue is mandatory. Third-party providers are slow and go
down. The queue absorbs the outage and retries; the caller never waits.

**Trade-off** — At-least-once delivery means duplicates are possible. Add a
dedupe key so the same notification is not sent twice.

**Follow-ups** — User preferences and opt-outs? Retry with exponential backoff?
How do you stop a bug from sending 10M wrong messages?

---

## 5. Twitter / News Feed
**Level:** Intermediate · **Tests:** fan-out, the celebrity problem

**Requirements** — Post a tweet; see a feed of people you follow.

**Scale** — 300M users, 300M tweets/day = 3,000 writes/sec, 300,000 reads/sec.

**Design**
```
Post --> Queue --> Fan-out workers --> write into each follower's feed cache
Read --> Feed cache (Redis list per user)  <- already built, instant
```

**Key decision** — **Fan-out on write.** Build the feed when someone posts, not
when someone reads. Reads are 100x more common, so do the work on the rare path.

**Trade-off** — *The celebrity problem.* A user with 100M followers would trigger
100M writes for one tweet. **Hybrid fix:** fan-out on write for normal users;
for celebrities, skip it and merge their tweets in at read time.

**Follow-ups** — Ranked feed instead of chronological? How do you handle a
deleted tweet already sitting in 10M feeds?

---

## 6. WhatsApp / Chat
**Level:** Intermediate · **Tests:** WebSockets, delivery guarantees, ordering

**Requirements** — 1-to-1 and group chat. Sent/delivered/read ticks. Work offline.

**Scale** — 50M daily users, 40 messages each = 2B/day = 23,000 messages/sec.

**Design**
```
Phone <--WebSocket--> Gateway --> Queue --> Message service --> DB
                          |
                    Presence service (who is online, in Redis)
```

**Key decision** — **WebSockets, not polling.** The connection stays open, so the
server can push instantly. Polling 50M phones every second would be wasteful.

**Trade-off** — Millions of open connections are expensive and stateful. You need
a connection registry mapping each user to the gateway holding their socket.

**Follow-ups** — Recipient offline? (Store the message, deliver on reconnect.)
How do you keep group message order consistent for everyone? End-to-end
encryption?

---

## 7. Instagram
**Level:** Intermediate · **Tests:** media storage, CDN, feed

**Requirements** — Upload photos, follow users, see a feed.

**Scale** — 500M daily users, 100M photos/day. At 2 MB each = 200 TB/day.

**Design**
```
Upload --> App --> S3 (original)
                    |
                 Queue --> Workers make thumbnails --> S3 --> CDN
Feed   --> Feed service (same fan-out as problem 5)
```

**Key decision** — Never serve images from your app servers. Store in S3, serve
through a CDN. Resize asynchronously so the upload returns immediately.

**Trade-off** — The user may briefly see a processing placeholder. Worth it —
the alternative is a 10-second upload.

**Follow-ups** — Which sizes do you pre-generate? How do you store the
follow graph? Stories that expire in 24 hours?

---

## 8. Typeahead / Autocomplete
**Level:** Intermediate · **Tests:** tries, caching, latency budget

**Requirements** — Suggest completions as the user types. Must feel instant.

**Scale** — 10B searches/day. Every keystroke is a request. Budget: under 100 ms.

**Design**
```
Keystroke --> LB --> Suggestion service --> Trie held in memory
                                              ^
                        Rebuilt hourly from search logs by a batch job
```

**Key decision** — A **trie** (prefix tree) with the top 5 results stored at each
node. No computation at request time — just walk the prefix and read the answer.

**Trade-off** — Suggestions are up to an hour stale. Fine for search, wrong for
trending topics, which need a faster update path.

**Follow-ups** — Debounce on the client (wait 200 ms after typing stops). How do
you personalise per user? How do you filter offensive suggestions?

---

## 9. Web Crawler
**Level:** Intermediate · **Tests:** queues, dedupe, politeness

**Requirements** — Crawl the web, extract links, store pages. Do not crawl the
same page twice. Do not overload any single site.

**Scale** — 1B pages/month = 400 pages/sec.

**Design**
```
Seed URLs --> Frontier queue --> Fetchers --> Parser --> Storage
                   ^                              |
                   +-------- new links -----------+
                                  |
                        Bloom filter (seen this URL?)
```

**Key decision** — A **Bloom filter** for dedupe. Storing 1B URLs in a set needs
far too much memory. A Bloom filter answers "seen it?" in ~1 GB. It can say
"maybe seen" wrongly, but never "not seen" wrongly — so at worst you skip a page.

**Trade-off** — *Politeness.* Never hammer one domain. Give each domain its own
queue with a delay, and respect `robots.txt`.

**Follow-ups** — Infinite URL loops (calendars)? How do you re-crawl pages that
change often? Distributing across machines?

---

## 10. Dropbox / File Sync
**Level:** Advanced · **Tests:** chunking, deduplication, conflicts

**Requirements** — Upload files, sync across devices, keep version history.

**Scale** — 500M users, 10 GB each = 5 EB raw, far less after dedupe.

**Design**
```
Client --> split file into 4 MB chunks --> hash each chunk
             |
      Only upload chunks the server does not already have
             |
      Metadata DB (file -> ordered list of chunk hashes)
      Chunk store (S3, keyed by hash)
```

**Key decision** — **Chunking plus content-addressed storage.** Change one line in
a 1 GB file and only one 4 MB chunk uploads. Identical chunks across all users
are stored once — a massive saving.

**Trade-off** — Metadata gets complex, and conflicts are hard. Two devices edit
offline: last-write-wins loses data, so keep both as conflicted copies.

**Follow-ups** — Delta sync inside a chunk? How do you sync efficiently to a
device that has been offline a month?

---

## 11. YouTube / Netflix
**Level:** Advanced · **Tests:** transcoding, CDN, adaptive streaming

**Requirements** — Upload video, watch anywhere, adapt to connection speed.

**Scale** — 500 hours uploaded/minute. Reads massively dominate.

**Design**
```
Upload --> S3 --> Queue --> Transcoding workers
                                |
                    Many versions: 240p 480p 720p 1080p 4K
                                |
                            CDN --> Viewers
```

**Key decision** — **Transcode once into many resolutions, split into segments.**
The player requests 10-second chunks and switches quality mid-stream as the
network changes (adaptive bitrate).

**Trade-off** — Transcoding is expensive and slow. Publish 480p first so the
video is watchable within minutes, and add higher resolutions as they finish.

**Follow-ups** — Which videos get pushed to CDN edges in advance? How do you
count views accurately at this scale? Live streaming instead of recorded?

---

## 12. Uber / Ride Matching
**Level:** Advanced · **Tests:** geospatial indexing, real-time matching

**Requirements** — Match a rider to a nearby driver. Live location updates.

**Scale** — 1M active drivers sending location every 4 seconds = 250,000 writes/sec.

**Design**
```
Driver app --> Location service --> Redis (geospatial index)
Rider request --> Matching service --> find drivers in nearby cells --> rank --> offer
```

**Key decision** — **Divide the map into grid cells** (QuadTree, Geohash or
Uber's H3). To find nearby drivers, search only the rider's cell and its
neighbours — not all 1M drivers.

**Trade-off** — Location writes are enormous. Keep them in memory only (Redis);
do not write every ping to a durable database.

**Follow-ups** — Surge pricing? What if two riders are matched to one driver?
(Locks, or offer sequentially.) Cells in dense city centres get hot.

---

## 13. Ticketmaster / Booking
**Level:** Advanced · **Tests:** concurrency, locking, consistency

**Requirements** — Book a seat. **Never** sell the same seat twice.

**Scale** — Normally quiet, then 1M people arrive the second tickets drop.

**Design**
```
User --> Queue (virtual waiting room) --> Booking service --> DB with row locks
                                                |
                                     Seat held for 10 min, then released
```

**Key decision** — This is a **CP** system (from CAP). Correctness beats
availability. Use a database transaction with `SELECT ... FOR UPDATE` on the
seat row. Showing an error is acceptable; double-booking is not.

**Trade-off** — Locking limits throughput, so a virtual waiting room throttles
the flood into a rate the database can survive.

**Follow-ups** — User abandons checkout? (Expire the hold.) How do you stop bots?
Why can't you just cache seat availability? (You can, but you must verify
against the DB before confirming.)

---

# Answer checklist

Before you call an answer finished, check you said all six:

- [ ] Asked clarifying questions **before** designing
- [ ] Stated the scale in numbers
- [ ] Drew the main components and how requests flow
- [ ] Named the one key decision and **why**
- [ ] Named the bottleneck and how you would fix it
- [ ] Mentioned what fails and what happens then
