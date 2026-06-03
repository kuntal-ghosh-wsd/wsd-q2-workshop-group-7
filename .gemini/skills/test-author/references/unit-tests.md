# Unit Tests — Structure, Mocking, Discipline

Unit tests should be **the cheapest tests to write and the cheapest to maintain**. If they aren't, something is wrong — usually the production code's structure, not the tests themselves.

## Contents
- [The shape of a unit test](#the-shape-of-a-unit-test)
- [Arrange / Act / Assert](#arrange--act--assert)
- [One behaviour per test](#one-behaviour-per-test)
- [Mocking — when, what, why not](#mocking--when-what-why-not)
- [Test data builders](#test-data-builders)
- [Parameterized tests](#parameterized-tests)
- [What good assertions look like](#what-good-assertions-look-like)
- [Common mistakes](#common-mistakes)

## The shape of a unit test

A unit test is a sentence:

> Given **<state>**, when **<action>**, then **<observable outcome>**.

A test that doesn't fit this shape is usually testing too much, or testing the wrong thing.

## Arrange / Act / Assert

Every test has three sections, in order:

```
TEST: discount applies when order qualifies for member rate

  // Arrange
  customer = newMember()
  order    = orderOf(items=[item(price=100)], customer=customer)

  // Act
  total = pricer.computeTotal(order)

  // Assert
  expect(total).toEqual(90)   // 10% member discount
```

Separate the three with a blank line or comment. Reviewers read **Arrange** to understand the setup, **Act** for the call under test, **Assert** for the predicate. Mixed AAA is unreadable.

**Arrange is the longest section in most tests.** That's fine — but if it's longer than ~10 lines, your data model is asking for a builder (see below).

**Act should be one line.** If "the action under test" requires four method calls, you're testing the integration of those four calls, which is an integration test.

**Assert should be 1–3 lines.** If you have ten assertions, you have ten tests pretending to be one.

## One behaviour per test

A test name is a promise. The body must keep exactly that promise. If the body proves three different things, it should be three tests with three names.

**Bad:**
```
TEST: order pricing
  // arranges 4 different scenarios
  // makes 12 assertions
```

**Good:**
```
TEST: applies member discount when customer is a member
TEST: applies bulk discount when item count > 10
TEST: stacks member + bulk discount when both apply
TEST: applies neither discount for non-member single-item order
```

Yes, that's more tests. They're cheaper to read, cheaper to maintain, and when one fails you know exactly what broke.

## Mocking — when, what, why not

A mock (or stub, fake, spy — the terminology varies) replaces a real collaborator with a controlled substitute. Mocks freeze a snapshot of the collaborator's behaviour; if the real one changes, your test still passes against the stale mock.

**Mock when:**

- The real dependency is **slow** (database, network, time-based) and the test isn't about that dependency.
- The real dependency is **non-deterministic** (random, clock, ID generator, external API).
- The real dependency has **dangerous side effects** (sends email, charges card).
- The real dependency is **hard to put into a specific state** (failure modes, edge cases).

**Don't mock when:**

- The dependency is **pure logic you own** — call it directly. Wrapping your own classes in mocks just to "isolate" them produces tests that lock in implementation.
- The dependency is **a value object / DTO**. Just construct one.
- The dependency is **trivial to use** (a function, a small utility).
- You're mocking **the system under test itself**. If you're doing this, you're not testing it.

**Mocking rules of thumb:**

- **Mock at the boundary**, not inside your own code. Mock the HTTP client, not the service that uses it.
- **Mock roles, not types.** Mock the "thing that sends email", not specifically `MailgunClient`.
- **Verify behaviour, not method calls.** Asserting "sendEmail was called once" is weaker than asserting "the resulting outbox contains one message to the right address".
- **A test with more than ~3 mocks** is usually a sign the system under test does too much. Split the production code, not the test.

## Test data builders

When tests need objects with many fields, the Arrange section bloats. Solve with builders:

```
order = anOrder()
         .withCustomer(aMember())
         .withItems(itemAt(100), itemAt(50))
         .build()
```

Default values fill the rest. Each test specifies only what matters to it.

Without a builder:
```
order = new Order(
  id: "ord_xxx",
  customer: new Customer(id: "cus_xxx", name: "Test", email: "t@t.com", tier: "MEMBER", ...),
  items: [new Item(...), new Item(...)],
  status: "OPEN",
  createdAt: someDate(),
  ...20 more fields
)
```

That's a maintenance burden waiting to happen. The day the `Order` constructor changes, 200 tests break. Builders are insulation.

## Parameterized tests

When the same logic must hold across many inputs, parameterize:

```
Table of cases:
  | input    | expected |
  | -3       | 0        |
  | 0        | 0        |
  | 1        | 1        |
  | 99       | 99       |
  | 100      | 100      |
  | 101      | 100      | // cap

TEST: clampToHundred(input) == expected
```

One test, N cases. The failure message names the case that broke.

Don't parameterize cases that have **different setup or different assertions** — those should be separate named tests.

## What good assertions look like

| Bad | Good |
|---|---|
| `expect(result).toBeTruthy()` | `expect(result).toEqual(42)` |
| `expect(items.length > 0)` | `expect(items).toContain(expectedItem)` |
| `expect(err).toBeDefined()` | `expect(err.code).toEqual("RATE_LIMIT")` |
| 12 assertions in a row | one test per behaviour |
| asserting against internal state | asserting against return value or observable behaviour |
| `expect(x).toEqual(y)` where both are computed similarly | hard-coded expected value |

**Specific, hard-coded expected values** are the gold standard. If the expected value is computed by mirroring the production logic, you're testing that "the code does what it does" — tautological.

## Common mistakes

- **Testing implementation details.** Tests that assert "method X was called twice" break every refactor. Test behaviour.
- **Conditionals in tests.** `if (env == 'prod') { ... }` in a test means you have two tests in one. Split.
- **Hidden setup.** A test that depends on a global `beforeAll` that's two files away is impossible to read. Inline what matters.
- **One assertion per test taken too literally.** "One behaviour" can require 2–3 assertions to fully express. The rule is "one reason to fail", not "one literal assert".
- **Mocking value objects.** `new Order(...)` is fine. Mocking `Order` is silly.
- **No failing test before the fix.** A test that has never been red can't be trusted.
- **Slow unit tests.** If a unit test takes 200ms, it isn't a unit test.
