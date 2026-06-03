# Test Strategy — Picking the Right Level

Tests cost money to write and money to maintain. The level you choose determines both. Get this right and the rest of the suite stays healthy; get it wrong and the suite becomes an anchor.

## Contents
- [The pyramid (still right)](#the-pyramid-still-right)
- [Level definitions](#level-definitions)
- [How to choose: a 30-second decision tree](#how-to-choose-a-30-second-decision-tree)
- [Pyramid violations to watch for](#pyramid-violations-to-watch-for)
- [What NOT to test](#what-not-to-test)
- [Per-story coverage rubric](#per-story-coverage-rubric)
- [Common mistakes](#common-mistakes)

## The pyramid (still right)

```
        /\
       /  \      e2e         (few, slow, expensive, brittle)
      /----\
     /      \    integration  (some, medium speed, real boundaries)
    /--------\
   /          \  unit         (many, fast, cheap)
  /____________\
```

Rough ratio for a healthy suite:

- **70–80%** unit tests
- **15–25%** integration tests
- **5–10%** e2e tests

Inverted pyramid (mostly e2e) = slow CI, flaky pipelines, expensive debugging. Pyramid with no e2e = nobody knows if the system actually works end-to-end.

## Level definitions

### Unit test

- **Scope:** one function / class / module. No I/O, no network, no DB, no clock, no filesystem (except read-only fixtures).
- **Speed:** milliseconds. Whole suite < 30 seconds for a mid-sized service.
- **Stability:** must never flake. Deterministic by construction.
- **What it asserts:** pure logic — given input X, output Y. Branching behaviour. Edge cases.
- **What it does NOT assert:** that two units integrate correctly; that the DB is queried right; that an HTTP endpoint is wired up.

### Integration test

- **Scope:** a small slice of the system across **one** real boundary. E.g. service + DB. Or two cooperating services. Or HTTP handler + service + DB.
- **Speed:** tens to hundreds of milliseconds per test. Whole suite < 5 minutes.
- **Stability:** should not flake. Use real dependencies (real DB, real queue) in a controlled environment.
- **What it asserts:** wiring between components, contracts at boundaries (HTTP, DB, queue), real serialization/deserialization, real query behaviour.
- **What it does NOT assert:** every branch of pure logic — that belongs in unit tests.

### End-to-end test

- **Scope:** the whole system as a user (or external caller) sees it. Browser driving a real UI talking to a real API on a real DB.
- **Speed:** seconds per test. Whole suite < 15 minutes max.
- **Stability:** flake-prone — fight constantly. Aim for < 1% flake rate.
- **What it asserts:** the critical user journeys actually work end-to-end. Authentication, payment, the one or two flows that, if broken, mean "the site is down".
- **What it does NOT assert:** detail. E2e on every variant of every form field = pyramid inversion.

## How to choose: a 30-second decision tree

For each AC:

1. **Is the AC about pure logic** (calculation, validation, transformation)? → **Unit test.**
2. **Is the AC about a boundary** (DB query returns right rows, API endpoint returns right shape, queue consumer processes message)? → **Integration test.**
3. **Is the AC about a complete user journey** (user logs in, navigates, performs action, sees confirmation)? → **E2E test.**
4. **Is the AC about behaviour at scale or under load**? → **Performance test** (separate suite, separate cadence).

If a single AC needs assertions at multiple levels, **write multiple tests at different levels** — don't try to cover everything with one e2e.

## Pyramid violations to watch for

- **Logic in e2e.** "Click here, then check the discount is 12.5%." The discount calculation is unit-test territory. The e2e should assert the discount **appears in the UI** — the value belongs to the unit test.
- **No integration tests.** Unit + e2e with nothing in between = boundary bugs slip through (wrong column name, wrong serialization, wrong status code).
- **Integration tests using mocked DBs.** That's a unit test wearing the wrong label. Use the real DB (container, in-memory equivalent, or shared test instance).
- **Unit tests using real DBs.** That's an integration test wearing the wrong label. Slow, brittle, flaky.

## What NOT to test

These are common time-wasters:

- **Framework behaviour.** Trust your ORM to do SELECTs. Trust your HTTP client to send headers. Don't write tests that just exercise the framework.
- **Third-party library behaviour.** Write tests at your boundary with the library (does our code call it correctly), not inside the library.
- **Trivial getters / setters / pass-throughs.** Zero-logic code doesn't need a test.
- **Type guarantees the type system already gives you.** A type-checked argument can never be `null` — don't test for `null`.
- **Auto-generated code.** Tests on generated code rot every time the generator changes.
- **Configuration.** "Test that the config has key X" is a smoke test of YAML parsing; pointless.
- **UI styling / pixel exactness.** Use visual regression tooling if you need this — don't try to assert CSS values in unit tests.

## Per-story coverage rubric

For a story with N ACs, a healthy test set looks like:

- **N unit tests** minimum — one per AC that has any logic.
- **1–3 integration tests** — exercise the wiring across the story's main boundary.
- **0–1 e2e tests** — only if the story is on a critical user journey.

Skewing higher than that ratio (e.g. 5 e2e for one story) is almost always a smell that the test author isn't trusting the lower levels.

## Common mistakes

- **Writing only e2e tests** "because they catch everything". They do — slowly, flakily, with terrible failure messages. The pyramid exists because lower levels have better failure signal.
- **Writing only unit tests** with all dependencies mocked. Passes locally, breaks in prod when a boundary contract was wrong.
- **Measuring "coverage" only** as line coverage. Branch coverage and mutation testing tell you whether assertions are sharp; line coverage tells you whether code was *touched*.
- **Skipping integration tests because "they're slow"**. They're slow because they do something. Run them in parallel, run them in CI, don't skip them.
- **Writing the test plan after the code.** Tests written from code mirror the code's bugs.
