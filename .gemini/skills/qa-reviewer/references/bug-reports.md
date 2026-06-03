# Bug Reports

A bug report is a **handoff document**. The cost of writing it well is ~5 minutes; the cost of writing it badly is multiple back-and-forths between QA, dev, and PM, plus delays in triage. Write it well.

## Contents
- [The job of a bug report](#the-job-of-a-bug-report)
- [Mandatory sections](#mandatory-sections)
- [Severity vs priority](#severity-vs-priority)
- [Writing a clear repro](#writing-a-clear-repro)
- [Evidence — screenshots, logs, recordings](#evidence--screenshots-logs-recordings)
- [Triaging your own report before filing](#triaging-your-own-report-before-filing)
- [Common mistakes](#common-mistakes)

## The job of a bug report

A reader (a dev, a PM, or future you) must be able to:

1. **Reproduce** the bug from the report alone.
2. **Understand the impact** — who hurts, how badly.
3. **Find related bugs** — the report uses consistent terms and references.
4. **Triage** it — decide severity, priority, owner without further investigation.

A report that fails any of those is a half-finished report. It will bounce.

## Mandatory sections

Every bug report has these. The template ([assets/bug-report-template.md](../assets/bug-report-template.md)) lays them out:

```
Title         — One short sentence that names the problem
Environment   — Build, version, OS, browser, account/role
Severity      — Impact when it happens (see below)
Priority      — When it must be fixed (see below)
Steps to reproduce — Numbered, minimal, deterministic
Expected behaviour — What should happen
Actual behaviour   — What does happen
Evidence      — Screenshots / video / logs / network trace
Frequency     — Always / sometimes (% if known) / once
Related       — Linked stories, ACs, prior bugs, dependencies
Workaround    — If any, for users / support team
```

Optional but valuable:

- **First seen** — what build / when first reported.
- **Regressed from** — if this used to work, what changed.
- **Affected users** — internal scope (one customer / many / all).
- **Hypothesis** — your best guess at the cause, clearly labelled as a hypothesis.

## Severity vs priority

These are not synonyms. Confusing them produces bad triage and wrong fix order.

### Severity — impact of the bug

| Severity | Definition | Examples |
|---|---|---|
| **S1 — Blocker** | System down, data loss, security breach, no workaround | Site fully down, payments charging twice, PII leak |
| **S2 — Critical** | Core feature broken, severe impact, workaround painful | Can't check out, can't log in for one auth method |
| **S3 — Major** | Important feature broken, workaround exists | Search returns wrong sort order; export missing one column |
| **S4 — Minor** | Cosmetic, edge case, or low-impact | Misaligned button on rare layout; typo in confirmation message |

### Priority — when it must be fixed

| Priority | Definition | Examples |
|---|---|---|
| **P0 — Now** | Fix immediately; everything else stops | Active production incident |
| **P1 — This release** | Block release until fixed | Severe bug found in release candidate |
| **P2 — Next release** | Schedule in the next sprint / cycle | Most major bugs |
| **P3 — Backlog** | Fix when convenient | Minor cosmetic, infrequent edge case |

**They are independent.** A typo on the launch homepage might be S4 (minor visual) but P0 (the CEO is announcing tomorrow). A rare crash in an obsolete Android version might be S2 (critical when it hits) but P3 (rare enough to wait).

Always set both.

## Writing a clear repro

A repro must be:

- **Deterministic** — anyone following it ends up at the same outcome.
- **Minimal** — every step is necessary; remove anything that doesn't affect the result.
- **Numbered** — easy to reference in discussion.
- **Specific** — exact values, exact URLs, exact button labels.

### Bad repro

> Sometimes when I try to save a dashboard it doesn't work.

Three things wrong: "sometimes" isn't deterministic, "doesn't work" isn't specific, no setup is shown.

### Good repro

```
1. Log in as a user in the "viewer" role.
2. Navigate to /dashboards/123 (any dashboard you have access to).
3. Click the "Edit" button in the top right.
4. Modify any widget (e.g. change the title).
5. Click "Save".

Expected: An error message "Insufficient permissions: viewers cannot
edit dashboards" appears, and the change is not persisted.

Actual: A green success toast appears ("Dashboard saved"), but on
page refresh the change is gone. Server returns 403 in the network
trace, but the UI shows success.

Frequency: 100% (10/10 attempts in build 1.42.0).
```

## Evidence — screenshots, logs, recordings

Attach the cheapest piece of evidence that proves the bug:

- **Screenshot** for visual / UI bugs. Annotate (arrow, circle) the issue.
- **Video / GIF** for flow bugs (something happens in sequence). Keep it short — 10–30 seconds.
- **Network trace (HAR)** for API / response bugs.
- **Console logs / server logs** for crashes or unexpected behaviour.
- **DB query result** for data bugs (after sanitizing any PII).

**Don't redact too much.** Screenshots with everything blacked out are useless. **Don't redact too little.** Real customer data has no place in a bug report.

## Triaging your own report before filing

5 minutes of self-triage saves an hour of clarification:

1. **Search for duplicates.** Use the most likely keywords from your title. If a dup exists, comment there instead.
2. **Minimize the repro.** Strip every step that isn't needed. If it still happens with fewer steps, use the shorter version.
3. **Verify in a clean environment.** Does it repro in incognito / a fresh account / a different browser? Note what was needed to repro.
4. **Sanity-check severity and priority.** Apply the matrices above.
5. **Re-read your steps from a stranger's perspective.** Would they understand?

## Common mistakes

- **Vague title.** "Bug in dashboards" — won't be found later, won't be triaged correctly.
- **No repro steps** or repro steps that don't actually reproduce.
- **Missing environment.** "It doesn't work" — on what build, on what browser, as what user?
- **Confusing severity with priority.** "Critical priority" — that's two words from two columns.
- **Treating "expected" as obvious.** Don't assume the reader knows. State it.
- **One bug, multiple issues.** "Save is broken AND the page loads slowly AND the icon is wrong" — three bugs, three reports. Otherwise one fix closes all three and the others are lost.
- **Filing without searching.** Duplicates pollute the tracker.
- **No evidence.** Especially for visual or hard-to-describe bugs.
- **Speculation framed as fact.** "The DB query is wrong" — unless you actually saw the query, that's a hypothesis. Label hypotheses as hypotheses.
