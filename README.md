# System Design

Notes to learn system design from scratch, up to interview level.
Plain English, short explanations, a real example for everything.

## Files

| File | What it is | When to read |
| --- | --- | --- |
| [SYSTEM_DESIGN_GUIDE.md](SYSTEM_DESIGN_GUIDE.md) | The theory. 32 topics, beginner to advanced | First. Start here |
| [DESIGN_PATTERNS.md](DESIGN_PATTERNS.md) | 14 reusable building blocks | After Part 1 of the guide |
| [PRACTICE_PROBLEMS.md](PRACTICE_PROBLEMS.md) | 13 problems with worked answers | Once patterns make sense |
| [CHEATSHEET.md](CHEATSHEET.md) | One page of recall | The morning of an interview |
| [practice_code/](practice_code/) | 10 runnable Python implementations + 39 tests | Alongside the patterns |

## Order to read them

```
SYSTEM_DESIGN_GUIDE.md   Parts 0-1     the basics
        |
DESIGN_PATTERNS.md       1-7           the common blocks
        |
SYSTEM_DESIGN_GUIDE.md   Part 2        replication, sharding, CAP
        |
practice_code/           01-06         implement what you just read
        |
PRACTICE_PROBLEMS.md     1-5           try the easy ones
        |
SYSTEM_DESIGN_GUIDE.md   Parts 3-4     advanced + the interview framework
        |
PRACTICE_PROBLEMS.md     6-13          the hard ones
        |
CHEATSHEET.md                          revise
```

## How to actually learn this

Reading system design feels productive and teaches very little. Three rules:

1. **Draw it from memory.** After each topic, close the file and sketch it on
   paper. If you cannot draw it, you have not learned it.
2. **Attempt before reading the answer.** In `PRACTICE_PROBLEMS.md`, cover the
   solution. 30 minutes, a sheet of paper, your own answer first.
3. **Say it out loud.** Interviews are spoken. Explaining to an empty room feels
   ridiculous and works better than anything else.
4. **Write the code.** [practice_code/](practice_code/) has runnable versions of
   the main patterns, plus exercises. Having written a rate limiter beats having
   read about one.

## Videos

| Resource | Why |
| --- | --- |
| [System Design Concepts Course](https://www.youtube.com/watch?v=F2FmTdLtb_4) — freeCodeCamp | Best starting point. Covers roughly Parts 1–2 of the guide |
| [System Design Interview Prep for Beginners](https://www.youtube.com/watch?v=oz5c88cO5P8) | A reusable framework for any question |
| [Gaurav Sen](https://www.youtube.com/@gkcs) | Fundamentals, assumes no prior knowledge |
| [ByteByteGo](https://www.youtube.com/@ByteByteGo) | Short animations. Good for revision |
| [Hussein Nasser](https://www.youtube.com/@hnasr) | The deep networking and database layer |

Full plan and reading list: Part 5 of [SYSTEM_DESIGN_GUIDE.md](SYSTEM_DESIGN_GUIDE.md).

## The short version

```
Cache reads. Queue writes. Keep servers stateless.
Shard late. Assume everything fails.
Ask questions before you answer.
```
