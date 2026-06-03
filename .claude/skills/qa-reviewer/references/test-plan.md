# QA Test Plan

A QA test plan is a **structured agenda for finding problems** before a feature is released. It's derived from the PRD, Stories, and ACs — and identifies what to test, at what level, in what environment, with what data.

This is different from a developer's test plan (which goes alongside the code as automated tests). A QA test plan covers **what humans will check**, what **automated suites must pass**, and what **risk areas need extra attention**.

## Contents
- [Where the plan comes from](#where-the-plan-comes-from)
- [Standard plan structure](#standard-plan-structure)
- [Test matrix — the heart of the plan](#test-matrix--the-heart-of-the-plan)
- [Risk-based prioritization](#risk-based-prioritization)
- [Environment and data needs](#environment-and-data-needs)
- [Sign-off criteria](#sign-off-criteria)
- [Common mistakes](#common-mistakes)

## Where the plan comes from

A test plan is **derived**, not invented:

| Source | Drives |
|---|---|
| PRD success metrics | Non-functional tests (perf, accessibility, security) |
| User Stories | Functional scope — what scenarios to test |
| Acceptance Criteria | The pass/fail predicates for each scenario |
| TAD integrations | What external-system test data and stubs are needed |
| Build / change log | Risk-based prioritization — what changed gets extra attention |

If any of those upstream artifacts is missing or thin, the test plan inherits that thinness. Fix upstream, don't paper over.

## Standard plan structure

See [assets/test-plan-template.md](../assets/test-plan-template.md) for the copy-pasteable version. The skeleton:

```
# QA Test Plan — <Feature>

## 1. Scope
   - What's in, what's out, source PRD/Stories links

## 2. Test matrix
   - Per-AC: what test method covers it (automated unit / integration / e2e
     / manual / exploratory) and who runs it

## 3. Manual test cases
   - Step-by-step scenarios for what humans will check

## 4. Exploratory test charters
   - Time-boxed sessions on risk areas (see exploratory reference)

## 5. Non-functional tests
   - Performance, accessibility, security, compatibility

## 6. Regression scope
   - What from previous releases to re-verify

## 7. Environment & data
   - Where tests run, what data is needed, who provides it

## 8. Risks & assumptions
   - Areas we can't fully test and why

## 9. Sign-off criteria
   - When the plan is "passed"
```

## Test matrix — the heart of the plan

For every Acceptance Criterion in the feature, decide what covers it:

| AC ID | Auto unit | Auto integration | Auto e2e | Manual | Exploratory | Owner |
|---|---|---|---|---|---|---|
| AC-101 | ✅ | — | — | — | — | dev |
| AC-102 | ✅ | ✅ | — | — | — | dev |
| AC-103 | — | ✅ | — | — | — | dev |
| AC-104 | — | — | ✅ | ✅ | — | QA |
| AC-105 | — | — | — | ✅ | — | QA |
| AC-106 | — | — | — | — | ✅ | QA |

Rules:

- **Every AC must have at least one ✅** somewhere. Empty rows are gaps — either add coverage or document why it's untestable.
- **Prefer leftward coverage.** A unit test catching it is cheaper than e2e; e2e is cheaper than manual; manual is cheaper than exploratory.
- **Manual + exploratory are for what automation can't easily cover** — visual polish, multi-step user flows that change often, perception (does this feel right).

## Risk-based prioritization

Not everything gets equal attention. Focus QA effort on:

1. **What changed** — areas modified in this release get deepest coverage. Stable areas get a thinner regression pass.
2. **What's user-visible** — bugs users see hurt more than bugs they don't.
3. **What's hard to roll back** — data migrations, irreversible writes, payment flows. Over-test these.
4. **What broke before** — areas with a history of bugs deserve a longer look.
5. **What's at boundaries** — integrations with third parties, browser variants, mobile/desktop, edge cases of input.

Capture this as a brief **risk register** in the plan — three columns: *risk*, *likelihood*, *mitigation* (extra test scope, monitoring, feature flag, etc.).

## Environment and data needs

State what's required:

- **Environment**: staging URL, build version, feature flags to enable, time-of-day windows (e.g. avoid times when external sandbox APIs are unstable).
- **Test accounts**: roles needed (admin, viewer, guest), how to obtain credentials, cleanup after.
- **Test data**: seed data needed, how it's provided (script, fixtures, manual creation).
- **Sandboxes / third-party**: which third-party sandboxes are in scope (Stripe test mode, Twilio sandbox, etc.), with credentials reference.
- **Devices / browsers**: explicit list. "Latest Chrome and Safari on macOS" is fine; "all browsers" is not.

If any environment need is unmet, the plan is blocked — flag it before starting QA, not mid-session.

## Sign-off criteria

Define before testing starts. Sample criteria:

- [ ] 100% of automated suites pass on the release candidate.
- [ ] 100% of must-have ACs verified (any method).
- [ ] 0 open high-severity bugs (or all accepted by product owner with notes).
- [ ] All open medium-severity bugs have an assigned owner and ETA.
- [ ] Performance budget met (per PRD).
- [ ] Accessibility scan clean of WCAG AA violations.
- [ ] Exploratory session completed and findings triaged.

Sign-off is **a decision**, not a default. If criteria aren't met, the release waits or the criteria get explicitly waived.

## Common mistakes

- **Plans that just restate the ACs.** A test plan must add information (priority, methods, owners, environment), not echo the spec.
- **No risk register.** Effort gets spread evenly across low and high risk, missing the latter.
- **Vague sign-off criteria.** "All tests pass" — which tests? "Release-ready" — by what measure?
- **No regression scope.** New features get tested; old features quietly break.
- **Skipping exploratory.** Plans cover what you anticipated; exploration finds what you didn't.
- **Plan written after testing starts.** Then it's a chronicle, not a plan. Write first, execute against it.
- **Plan never updated.** Conditions change (env down, scope cut, bug found). Update the plan as you go.
