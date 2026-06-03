# Release Readiness Checklist — <Release Name / Version>

**Release owner:** <name — the one accountable person>
**Target date / time:** <YYYY-MM-DD HH:MM tz>
**Release candidate:** <build version + commit SHA>
**Rollback owner / on-call:** <name>

---

## 1. Coverage

- [ ] Automated suites (unit / integration / e2e) pass on the release candidate in CI
- [ ] Every must-have AC verified (auto or manual). No "unknown" status anywhere in the test matrix
- [ ] Regression suite passed on the release candidate (not on a previous build)
- [ ] Planned exploratory charters completed; findings triaged
- [ ] Performance targets met under expected load (per PRD)
- [ ] Accessibility scan clean (WCAG AA, or as defined in PRD)
- [ ] Security review completed if security-relevant; findings triaged
- [ ] Tested on the explicit cross-browser / device support matrix

## 2. Bugs

- [ ] Open S1 (Blocker) bugs: **0**
- [ ] Open S2 (Critical) bugs: 0, or each explicitly accepted by the release owner with note in release notes + hotfix plan
- [ ] All open S3 bugs have owner + scheduled fix release
- [ ] Bug list compiled for release notes (known issues)

## 3. Operations

- [ ] Deployment plan documented: what deploys, in what order, by whom, expected duration
- [ ] New features behind feature flags where feasible; default state documented
- [ ] DB migrations reversible OR documented forward-fix plan; idempotency verified
- [ ] New metrics / dashboards / alerts in place **before** the release goes live
- [ ] On-call aware of the release window and on standby; pager tested
- [ ] Infrastructure provisioned for expected load (incl. launch spike); capacity verified
- [ ] Any upstream / third-party dependency change is in place
- [ ] New env vars / secrets deployed to target environment

## 4. Communication

- [ ] Release notes / changelog written
- [ ] Customer-facing announcement prepared (if applicable)
- [ ] Support team briefed: what changed, known issues, escalation path
- [ ] Sales / CS briefed if customer-visible
- [ ] Internal announcement scheduled (Slack / email)
- [ ] Status page updated if maintenance window or expected disruption

## 5. Rollback plan

- [ ] "Roll back" defined for this release: <revert deploy / flip flag / forward-fix>
- [ ] Named person can execute rollback: <name>
- [ ] Realistic rollback duration: <minutes>
- [ ] Data implications handled (any new schema / data writes safe to roll back?)
- [ ] Rollback trigger defined: <error rate / SLO burn / customer reports / etc.>

## 6. Go / No-Go

- [ ] Walked this checklist out loud in the go/no-go meeting
- [ ] Open bugs and waivers reviewed
- [ ] **Decision:** GO / NO-GO
- [ ] Decision recorded by: <name>, at: <YYYY-MM-DD HH:MM>

## 7. Post-release verification (within agreed monitoring window)

- [ ] Critical user journeys smoke-tested live in production
- [ ] Error rate, latency, throughput dashboards watched for the monitoring window
- [ ] Support channels watched for early customer reports
- [ ] Logs scanned for new error types not seen pre-release
- [ ] **Release called done** in team channel, ending heightened on-call attention

## Notes / waivers

<Record any explicit waivers granted (which gate, why, with what fallback)
and any other context worth preserving for the post-mortem if one is needed.>
