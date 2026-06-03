# QA Test Plan — <Feature Name>

**Status:** Draft / In Review / Approved
**Release / build:** <version + commit>
**Owner:** <name>
**Source PRD:** <link>
**Source Stories:** <link>
**Last updated:** <YYYY-MM-DD>

---

## 1. Scope

<One paragraph: what this plan covers, what's explicitly out of scope.>

## 2. Test matrix

For each Acceptance Criterion, what testing method covers it and who runs it.

| AC ID | Auto unit | Auto integration | Auto e2e | Manual | Exploratory | Owner |
|---|---|---|---|---|---|---|
| AC-101 | ✅ | — | — | — | — | dev |
| AC-102 | — | ✅ | — | ✅ | — | dev / QA |
| AC-103 | — | — | ✅ | — | — | dev |
| AC-104 | — | — | — | ✅ | ✅ | QA |
| ... |   |   |   |   |   |   |

Rule: every AC must have at least one ✅.

## 3. Manual test cases

Step-by-step scenarios for what humans will execute.

### TC-001 — <descriptive name>

**Covers:** AC-104

**Preconditions:** <account role, data state, environment>

**Steps:**
1. <step>
2. <step>
3. <step>

**Expected:** <observable outcome>

---

### TC-002 — <…>

(repeat as needed)

## 4. Exploratory test charters

| Charter | Timebox | Tester |
|---|---|---|
| Explore <feature> with two browser sessions to discover concurrency / permission bypass bugs | 60 min | <name> |
| Explore <feature> on a slow 3G connection to discover responsiveness gaps | 60 min | <name> |
| Explore <feature> as each role (admin, editor, viewer) to discover access-control gaps | 90 min | <name> |

(See exploratory reference for charter wording guidance.)

## 5. Non-functional tests

| Concern | Method | Target |
|---|---|---|
| Performance | <Load test in staging at expected RPS> | <p95 < 200 ms> |
| Accessibility | <Automated axe scan + manual keyboard nav> | <WCAG AA, 0 violations> |
| Security | <Static scan + targeted pen test if security-relevant> | <No high/critical findings> |
| Compatibility | <Manual sweep on support matrix> | <Pass on listed browsers/devices> |

## 6. Regression scope

Areas to re-verify even though they weren't changed in this release.

- <Area 1 — what changed near it that justifies re-test>
- <Area 2>
- <Critical journeys: sign-in, checkout, etc.>

## 7. Environment & data

- **Environment:** <staging URL, build version, feature flags to enable>
- **Test accounts:** <roles needed, credential location>
- **Test data:** <what's needed, how it's provided>
- **Third-party sandboxes:** <which ones, credentials reference>
- **Devices / browsers:** <explicit support matrix>

## 8. Risks & assumptions

| Risk | Likelihood | Mitigation |
|---|---|---|
| <Risk 1> | <high/med/low> | <extra test scope / feature flag / monitoring> |
| <Risk 2> | <…> | <…> |

## 9. Sign-off criteria

- [ ] 100% of automated suites pass on the release candidate
- [ ] 100% of must-have ACs verified
- [ ] 0 open S1/S2 bugs (or explicitly accepted by owner)
- [ ] Regression suite passed
- [ ] Performance target met
- [ ] Accessibility scan clean
- [ ] Exploratory charters completed and findings triaged
