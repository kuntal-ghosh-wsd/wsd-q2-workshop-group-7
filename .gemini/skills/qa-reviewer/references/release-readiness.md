# Release Readiness — the Go/No-Go Decision

A release is a decision, not a default. "Release readiness" is the discipline of making that decision **deliberately** — based on agreed criteria, with someone accountable, and with a rollback plan in place.

## Contents
- [Who decides](#who-decides)
- [The release-readiness checklist](#the-release-readiness-checklist)
- [Coverage gates](#coverage-gates)
- [Bug gates](#bug-gates)
- [Operational readiness](#operational-readiness)
- [Communication readiness](#communication-readiness)
- [Rollback plan](#rollback-plan)
- [Go / no-go meeting](#go--no-go-meeting)
- [Post-release verification](#post-release-verification)
- [Common mistakes](#common-mistakes)

## Who decides

A release decision has one accountable owner — usually the product owner / release manager, with input from QA, engineering, and ops. Not a committee.

The owner says "go" or "no-go" on the record. Other roles provide input but don't make the call.

## The release-readiness checklist

See [assets/release-checklist-template.md](../assets/release-checklist-template.md) for the full version. The skeleton groups checks into four buckets:

1. **Coverage** — has everything been tested?
2. **Bugs** — are open bugs acceptable?
3. **Operations** — is the system ready to be observed and rolled back?
4. **Communication** — do stakeholders know what's shipping?

Run all four. Skip none.

## Coverage gates

| Gate | Pass criterion |
|---|---|
| Automated suites | 100% pass on the release candidate, in CI, on the exact commit being released |
| AC verification | Every must-have AC in every story has been verified (auto or manual). No unknowns. |
| Regression scope | Regression test pass on the release candidate — not just on a previous build |
| Exploratory sessions | Planned charters executed; findings triaged and resolved or accepted |
| Performance | Latency / throughput targets met under expected load |
| Accessibility | Automated a11y scan clean for WCAG AA; manual a11y session if UI changed substantially |
| Security | If security-relevant: scan completed, findings triaged |
| Cross-browser / device | Tested on the explicit support matrix (not "should work everywhere") |

If any gate is unmet, it's either fixed or **explicitly waived** by the owner with a one-line rationale recorded.

## Bug gates

Open bugs at release time fall into three categories:

| Category | What's allowed |
|---|---|
| **Blockers (S1)** | Zero. Release waits. |
| **Critical (S2)** | Zero, unless explicitly accepted by the owner with a release-notes entry and a hotfix plan |
| **Major (S3)** | Allowed if triaged, owned, and scheduled |
| **Minor (S4)** | Allowed without action |

Track the bug list as part of the release notes — internal team should know what's known-broken in this release.

## Operational readiness

Code being "done" is not enough; the system has to be runnable, observable, and reversible.

- **Deployment plan** — what gets deployed, in what order, who triggers it, expected duration.
- **Feature flags** — new features behind a flag where possible. Default state documented.
- **Migrations** — DB migrations are reversible OR have a forward-fix plan; idempotency verified.
- **Monitoring** — new metrics, dashboards, and alerts in place **before** the release goes live.
- **On-call** — primary on-call is aware of the release window and on standby. Pager working.
- **Capacity** — infra is provisioned for expected load including launch spike. Verified, not assumed.
- **Dependencies** — any required upstream service / third-party change is in place.
- **Secrets / config** — any new env vars / secrets are deployed to the target environment.

## Communication readiness

| Stakeholder | What they need |
|---|---|
| Customers | Release notes / changelog / in-app announcement |
| Support team | What changed, what to expect, where the known issues are, how to escalate |
| Sales / CS | Talking points if customer-visible |
| Internal | Slack / email announcement, scope summary |
| Status page | Updated if maintenance window or expected disruption |

Skipping this turns a smooth release into a fire drill when users start asking questions.

## Rollback plan

**Every release has a rollback plan, even small ones.** The plan answers:

1. **What does "roll back" mean for this release?** (Revert the deploy / flip a feature flag off / run a forward fix.)
2. **Who can execute it?** (Names, not roles. With access.)
3. **How long does it take?** (Realistic minutes.)
4. **What about data?** (If the release wrote new schema or new data, is rollback safe?)
5. **What's the trigger?** (What signal — error rate, SLO burn, customer reports — initiates rollback?)

If you can't answer all five, don't release.

## Go / no-go meeting

A short meeting (15 minutes max) before release:

- **Attendees:** release owner, eng lead, QA lead, on-call, ops.
- **Agenda:**
  1. Walk the checklist out loud.
  2. Review open bugs and any waivers.
  3. Confirm rollback plan and on-call coverage.
  4. Owner says **go** or **no-go**.
  5. If go: confirm time, sequence, monitoring window.

Record the decision and any waivers in writing. Saying "go" in a meeting that wasn't recorded leaves no trail when things go wrong.

## Post-release verification

The release isn't done when the deploy finishes. Within the agreed monitoring window:

- **Smoke test** — critical user journeys verified live in production (real account, real flow).
- **Watch the dashboards** — error rate, latency, throughput, SLO budget burn. Don't just glance; sit with them for the monitoring window.
- **Watch support channels** — early customer reports often surface what monitoring misses.
- **Watch logs** for new error types not seen pre-release.

If anything looks off: execute the rollback plan or open an incident. Don't "wait and see".

After the monitoring window: **call it done** with an explicit message in the team channel. Otherwise on-call doesn't know when the heightened attention ends.

## Common mistakes

- **"It's mostly ready, ship it."** Without explicit gates, "mostly" becomes "we'll fix it after". You won't.
- **No rollback plan.** Under pressure, with users complaining, you'll improvise — and improvise badly.
- **No accountable owner.** Group decisions = no decisions. Name one person.
- **Confusing CI green with "ready to ship".** CI proves the code compiles and tests pass; it doesn't prove the release is operationally ready.
- **Skipping operational readiness.** "Code is done; ops can handle it" — ops needs the dashboards and alerts in place **before** the release, not after.
- **No post-release verification.** Deploy completes, everyone moves on, the bug surfaces 6 hours later when the on-call is asleep.
- **Implicit waivers.** "We're going to ship with that bug" — write it down, with a fix plan, in the release notes. Verbal waivers vanish.
- **Always saying "go".** A culture where "no-go" is socially impossible has no real gate.
