# Integration Tests — Crossing One Real Boundary

Integration tests catch the bugs unit tests cannot: wrong SQL, wrong serialization, wrong status codes, broken wiring at the seams. The win comes from using **real** dependencies — replace them with mocks and you've just written a slow unit test.

## Contents
- [Scope: one boundary at a time](#scope-one-boundary-at-a-time)
- [Real dependencies, not mocks](#real-dependencies-not-mocks)
- [Fixtures and test data](#fixtures-and-test-data)
- [Test isolation](#test-isolation)
- [The DB-test pattern](#the-db-test-pattern)
- [The HTTP-test pattern](#the-http-test-pattern)
- [The queue-test pattern](#the-queue-test-pattern)
- [Speed budget](#speed-budget)
- [Common mistakes](#common-mistakes)

## Scope: one boundary at a time

An integration test exercises a **small slice** of the system across **one** real boundary. Examples:

| Test type | Boundary crossed | What's real | What's mocked |
|---|---|---|---|
| Repository test | App ↔ DB | Real DB, real schema, real queries | Nothing inside the slice |
| HTTP handler test | Client ↔ App ↔ Service | Real HTTP framework, real routing, real serialization | External downstream APIs |
| Queue consumer test | Queue ↔ Consumer ↔ App | Real queue or local broker, real message format | External downstream APIs |
| Service-to-service contract | Service A ↔ Service B | Real network call (against a local instance of B) | Nothing inside |

Tests that cross **two or more** boundaries (e.g. HTTP + DB + external API + queue) become e2e tests by another name. Keep integration tests focused.

## Real dependencies, not mocks

The point of integration testing is to verify the **real** boundary works. Mocking that boundary defeats the test.

- **DB tests use a real DB**, ideally the same engine and version as prod (e.g. real Postgres in a container, not SQLite as a stand-in). SQLite-as-Postgres misses dialect differences and fails in prod.
- **HTTP tests use a real HTTP server** spun up in-process (or in a container) — not a fake `request` object.
- **Queue tests use a real queue** (local broker, in-memory equivalent that matches semantics).
- **Filesystem tests use a real temp directory** — not a mock filesystem unless you're testing OS-specific behaviour.

The cost: tests run in tens or hundreds of milliseconds instead of single-digit milliseconds. Accept it. The bugs you catch pay for the time.

## Fixtures and test data

Three patterns, in order of preference:

### 1. Build per test (best)

Each test creates exactly the data it needs, in code, using builders:

```
test("findActiveOrders returns only OPEN and PENDING") {
  arrange:
    db.save( anOrder().withStatus("OPEN") )
    db.save( anOrder().withStatus("PENDING") )
    db.save( anOrder().withStatus("CLOSED") )
  act:
    result = repo.findActive()
  assert:
    expect(result).toHaveSize(2)
}
```

Pros: explicit, self-contained, the test reads top-to-bottom without hunting for setup elsewhere.
Cons: more lines per test.

### 2. Per-suite fixtures (acceptable)

A small, well-named seed is loaded before all tests in a suite. Use only for **read-only reference data** (countries, currency codes) that no test mutates.

### 3. Shared "kitchen sink" fixtures (avoid)

One big fixture file that seeds 50 customers, 200 orders, etc. Tests pick rows from it. Looks efficient; produces ungrokkable tests where "test 7 fails" because someone added a row to the fixture.

Don't do this. The convenience compounds into chaos.

## Test isolation

Every integration test must leave the world how it found it.

**Strategies (pick one per suite):**

1. **Transaction rollback** — start a transaction at the test start, roll back at the end. Cheap, fast. Doesn't work if production code commits internally.
2. **Truncate-between-tests** — clear all tables after each test. Slower than rollback but bulletproof.
3. **Schema-per-test** or **DB-per-test** — strongest isolation, lets tests run in parallel. Slow setup; usually overkill.
4. **Ephemeral container per suite** — spin up a fresh container, run the suite, throw it away. Common in CI.

**Anti-strategy:** depending on test order. "Test A creates a user that test B uses." Now you can't run B alone. You can't run them in parallel. When B fails, was it B's fault or A's? Don't do this.

## The DB-test pattern

```
beforeEach:
  db.beginTransaction()

afterEach:
  db.rollback()

test("savePayment persists with correct status"):
  arrange:
    order = db.save( anOrder() )
  act:
    repo.savePayment(order.id, amount: 100)
  assert:
    payment = db.querySingle("SELECT * FROM payments WHERE order_id = ?", order.id)
    expect(payment.status).toEqual("PENDING")
    expect(payment.amount).toEqual(100)
```

Use the real schema. Assert by querying back, not by inspecting in-memory objects (which might be stale).

## The HTTP-test pattern

```
beforeAll:
  server = startTestServer()   // real framework, real routing
  client = httpClientFor(server)

test("GET /dashboards/:id returns 404 for unknown id"):
  act:
    response = client.get("/dashboards/does-not-exist")
  assert:
    expect(response.status).toEqual(404)
    expect(response.body).toEqual({ error: "not_found" })

test("POST /dashboards rejects invalid name"):
  act:
    response = client.post("/dashboards", body: { name: "" })
  assert:
    expect(response.status).toEqual(400)
    expect(response.body.error).toMatch(/name required/)
```

Test the **contract**: status codes, response bodies, headers, content types. Not internal control flow.

## The queue-test pattern

```
test("OrderShipped event triggers ShippingNotification consumer"):
  arrange:
    queue.publish( orderShippedEvent(orderId: 123) )
  act:
    consumer.runOnce()   // process one message
  assert:
    notifications = db.query("SELECT * FROM notifications WHERE order_id = 123")
    expect(notifications).toHaveSize(1)
    expect(notifications[0].type).toEqual("SHIPPING")
```

Test that publish-and-consume actually works through the real broker — wrong serialization or misnamed routing keys hide here.

## Speed budget

| Suite | Target |
|---|---|
| Whole integration suite | < 5 min in CI |
| Single test | < 200 ms median |
| Setup before each test | < 50 ms |

Above those numbers, the suite gets skipped or run only "occasionally" — and dies.

Speed-ups in order of impact:

1. **Parallelize.** Run integration suites with N workers. Requires test isolation.
2. **Reuse the DB connection / server** across tests in a suite.
3. **Transactional rollback** instead of truncate.
4. **Avoid container start in inner loop** — share a container across the suite.

## Common mistakes

- **Mocking the DB in an "integration" test.** That's a unit test.
- **Using SQLite to test Postgres code.** Dialect differences will bite in prod.
- **Tests that pass alone but fail together.** Symptom of poor isolation — fix isolation, not the symptom.
- **Tests that share state via "kitchen sink" fixtures.** Brittle and uninterpretable.
- **Hitting real external APIs in integration tests.** Flaky, expensive, polluting. Mock the external API at its HTTP boundary, but keep your DB / queue / framework real.
- **Asserting via the same code path you're testing.** If the code under test fetches an order, don't verify by calling the same fetch — query the DB directly.
- **No teardown.** Tests that leave rows behind eventually fail other tests in confusing ways.
