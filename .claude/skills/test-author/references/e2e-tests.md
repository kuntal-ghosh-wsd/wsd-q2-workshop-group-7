# End-to-End Tests — Few, Reliable, Critical

E2E tests are the most expensive tests in the suite — slow to run, slow to write, slow to debug, and the most likely to flake. Their value comes from one thing unit and integration tests cannot do: **prove the system works as a user sees it**.

Treat them like surgery, not vaccinations.

## Contents
- [What e2e is for (and what it isn't)](#what-e2e-is-for-and-what-it-isnt)
- [The critical-journey rule](#the-critical-journey-rule)
- [Anatomy of a reliable e2e](#anatomy-of-a-reliable-e2e)
- [Selectors — the source of most flake](#selectors--the-source-of-most-flake)
- [Waits — never sleep](#waits--never-sleep)
- [Test data — own it, don't share it](#test-data--own-it-dont-share-it)
- [Page objects (use sparingly)](#page-objects-use-sparingly)
- [Flake triage](#flake-triage)
- [Common mistakes](#common-mistakes)

## What e2e is for (and what it isn't)

**E2E is for:**

- Proving that the major user journeys work through real browser → real frontend → real backend → real DB.
- Catching integration regressions between components owned by different teams.
- Smoke testing a release before it ships.

**E2E is NOT for:**

- Form validation rules (those are unit tests).
- HTTP status codes (those are integration tests).
- Calculation correctness (those are unit tests).
- Coverage farming. An e2e suite that "covers" everything is unmaintainably slow and flaky.

If you can answer "yes" to "could this be tested at a lower level?" — test it lower. E2E should be the last resort.

## The critical-journey rule

Limit e2e to **the journeys that, if broken, mean the system is broken**. For a typical product, that's:

- Sign-up / log-in / log-out
- The one or two flows that produce revenue (checkout, subscription, conversion)
- The one or two flows central to the product's purpose (post a tweet, send a message, create a dashboard)

Total: ~5–15 e2e scenarios for most products. If you have 200 e2e tests, you've drifted from the rule.

## Anatomy of a reliable e2e

```
TEST: user can sign up, create a dashboard, and see it on reload

  // setup (unique data so tests can run in parallel)
  email = uniqueEmail()

  // act through the UI as a user would
  page.navigate("/signup")
  page.fillForm({ email, password })
  page.clickButton("Sign up")

  page.waitForUrl("/dashboards")
  page.clickButton("New dashboard")
  page.fillInput("name", "My first dashboard")
  page.clickButton("Save")

  page.reload()

  // assert at the UI level — that's what the user sees
  page.assertTextVisible("My first dashboard")
```

Notes:

- No internal API calls except where impossible to do via UI (e.g. delete a user via API in teardown).
- No assertions on internal state (DB rows, log messages) — that's an integration test pretending.
- Each test creates its own data; no test depends on another's leftover state.

## Selectors — the source of most flake

Bad selectors cause 80% of e2e flake. Good selectors are stable across UI changes.

**In order of preference:**

1. **Test-id attributes**: `[data-testid="new-dashboard-button"]`. Stable, intentional, machine-readable. Add them in the frontend.
2. **Accessible roles + names**: `button[aria-label="New dashboard"]` or `getByRole("button", { name: "New dashboard" })`. Survives CSS changes, doubles as accessibility check.
3. **Visible text**: `getByText("New dashboard")`. Brittle if translations change; otherwise OK for unique strings.
4. **CSS classes**: `.btn-primary`. **Bad** — classes change with restyles.
5. **XPath**: `//div[3]/div[2]/button[1]`. **Forbidden** — breaks on the slightest DOM change.
6. **Auto-generated IDs**: `#id_3a9f1b2c`. **Forbidden** — change on every render.

Add test IDs in the frontend code as part of the feature work, not as a retrofit when tests start flaking.

## Waits — never sleep

`sleep(2000)` is the single most common cause of e2e flake. Always wait for **a condition**, never for **a time**.

| Wrong | Right |
|---|---|
| `sleep(2000)` then click | `wait(button.toBeEnabled())` then click |
| `sleep(5000)` for the page | `wait(page.toMatchUrl("/dashboards"))` |
| `sleep(3000)` for spinner | `wait(spinner.toBeHidden())` then assert |
| `sleep(1000)` for network | `wait(request.toComplete())` |

Sleep wastes time on fast runs and still flakes on slow ones. Conditions adapt.

If a wait condition doesn't exist for what you need, ask the frontend to expose one (loaded state, idle state, etc.).

## Test data — own it, don't share it

Each test creates its data with a **unique key** (timestamp, UUID, counter) so tests can run in parallel without colliding.

```
email = "test-" + uuid() + "@example.com"
dashboardName = "Dashboard " + uuid()
```

**Cleanup strategies (pick one):**

1. **Cleanup at end of test** — most reliable; works in CI even when tests fail mid-way (use `afterEach` / `finally`).
2. **Ephemeral environment** — spin up a fresh stack per CI run, throw it away.
3. **Periodic cleaner** — background job deletes test data older than 24h. Belt-and-braces with strategy 1.

**Never:**

- Use a shared "test user" account across tests — state pollution.
- Hardcode IDs you expect to exist — they won't, eventually.
- Rely on test order — one test's success must not depend on another's.

## Page objects (use sparingly)

A page object wraps element lookups + actions for a page into a class/module:

```
class DashboardListPage:
  newDashboardButton = "[data-testid='new-dashboard']"
  clickNewDashboard()
  dashboardCardWithName(name)
```

Pros: encapsulation; selector changes are made in one place.
Cons: easy to over-engineer; the abstraction often outweighs the savings for small suites.

**Use page objects when:**

- A selector or action is used by 3+ tests.
- The UI is complex enough that inline tests become unreadable.

**Don't use page objects when:**

- The suite has < 10 tests.
- They become a parallel implementation of the UI (helper classes for every component).

A few small helper functions often beat a full page-object hierarchy.

## Flake triage

Flake is not a mystery — it has a small number of causes. When a test flakes:

1. **Re-run it 10 times.** Determine the flake rate.
2. **Check for sleeps and bad selectors first.** That's where 80% of flake comes from.
3. **Check for shared state** between tests. A test that flakes when run with others but passes alone is an isolation bug.
4. **Check for timing in the production code.** Some flake is real — a race condition in prod that tests sometimes hit.
5. **Quarantine the test, don't ignore it.** Move it to a separate suite that doesn't block PRs; fix it within the week or delete it.

Never disable a test "temporarily" without a calendar reminder to fix or delete it. Disabled tests rot.

## Common mistakes

- **Too many e2e tests.** Suite balloons to hours, flakes everywhere, teams stop trusting it.
- **`sleep`** instead of conditions. Always wait for a condition.
- **XPath or auto-generated selectors.** Brittle by design.
- **Shared "test user" or "test account".** State pollution kills parallelism and reproducibility.
- **Asserting internal state.** That's integration testing wearing an e2e label.
- **Skipping cleanup.** Pollution slowly degrades the suite.
- **Running e2e in CI only.** Developers don't notice flake until it blocks them.
- **No flake budget.** Without a target ("must stay below 1% flake rate"), the suite drifts.
