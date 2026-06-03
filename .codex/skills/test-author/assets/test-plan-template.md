# Test Plan — <Story or Feature Name>

**Source story:** <US-XXX>
**Source ACs:** <AC-XXX, AC-XXX>
**Owner:** <name>
**Last updated:** <YYYY-MM-DD>

---

## 1. Scope

<One paragraph: what this plan covers, what's out of scope. Reference the
story and ACs being tested.>

## 2. Test matrix

For each AC, what level(s) cover it. See test-strategy reference for level
selection.

| AC | Unit | Integration | E2E | Notes |
|----|------|-------------|-----|-------|
| AC-101 | ✅ | — | — | Pure validation logic |
| AC-102 | ✅ | ✅ | — | Logic + DB persistence |
| AC-103 | — | ✅ | — | HTTP contract |
| AC-104 | ✅ | — | ✅ | Critical user journey, covered end-to-end too |

## 3. Unit tests

Behaviour-level outlines (not code):

- **<test name>** — Given <state>, when <action>, then <outcome>. (Covers AC-101)
- **<test name>** — Given <state>, when <action>, then <outcome>. (Covers AC-101, boundary case)
- **<test name>** — Given <state>, when <action>, then <outcome>. (Covers AC-102, error path)

## 4. Integration tests

| Test | Boundary | Real components | Mocked | Covers |
|------|----------|-----------------|--------|--------|
| <name> | App ↔ DB | App, Postgres | — | AC-102, AC-103 |
| <name> | HTTP handler | API server, DB | External payment API | AC-103 |

## 5. E2E tests

Only for critical journeys. Most stories should have 0 e2e additions.

- **<journey name>** — <user-perspective scenario>. (Covers AC-104)

## 6. Non-functional tests

| Concern | How tested | Target |
|---------|-----------|--------|
| Performance | Load test in staging | p95 < 200 ms at 100 RPS |
| Accessibility | Axe scan in e2e suite | 0 violations |
| Security | Pen test pre-launch | No high/critical findings |

## 7. Test data & fixtures

<What data is needed, how it's created (per-test builders / shared fixtures /
ephemeral environment).>

## 8. Out of scope (not tested here)

- <Thing that might be expected but isn't covered, with reason or follow-up link>

## 9. Risks & open questions

- <Risk 1 — mitigation or escalation>
- <Open question 1 — who decides, by when>
