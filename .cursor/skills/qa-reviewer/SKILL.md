---
name: qa-reviewer
description: >
  Plan, execute, and report quality assurance work on a feature that's
  reached staging or pre-release. Tool- and tracker-agnostic — works
  whether the team uses Jira, Linear, GitHub Issues, or none. Use when
  the user wants to write a QA test plan, draft an exploratory testing
  charter, file a high-quality bug report, decide whether a release is
  ready to ship, design a regression strategy, or build a release-gate
  checklist. Triggers on phrasing like "QA this feature", "write a test
  plan", "exploratory testing", "file a bug for ...", "is this ready to
  release", "what's our regression strategy", "go/no-go decision".
  Provides structures for test plans, exploratory charters, bug reports,
  and release-readiness reviews — distinct from `test-author` which writes
  the automated tests themselves.
---

# QA Reviewer

A guide for the QA pass on a feature that has been built and is approaching release. This skill is about **finding problems before users do** — through structured testing, exploration, and release-readiness review. Tool-agnostic; framework-agnostic.

## How this differs from `test-author`

| Skill | When | Output |
|---|---|---|
| `test-author` | Build phase — turning ACs into automated tests | Test code (unit / integration / e2e) |
| `qa-reviewer` | Pre-release phase — validating the built feature works | Test plans, exploratory findings, bug reports, release decisions |

Use `qa-reviewer` for **human-driven QA work**: test planning, manual and exploratory testing, bug reporting, release gates. Use `test-author` for **automated test design**.

## When to use this skill

| Signal phrase | Topic |
|---|---|
| "QA this story", "write a QA test plan", "what should we test before release" | [references/test-plan.md](references/test-plan.md) |
| "exploratory testing", "test charter", "session-based testing" | [references/exploratory-charters.md](references/exploratory-charters.md) |
| "file a bug", "write a bug report", "this is broken — log it" | [references/bug-reports.md](references/bug-reports.md) |
| "is this ready to ship", "go/no-go", "release checklist", "release gate" | [references/release-readiness.md](references/release-readiness.md) |

## Pre-flight

Before any QA pass, gather the four inputs that bound the work:

1. **The PRD or feature brief** — defines what the feature is supposed to do.
2. **The User Stories with Acceptance Criteria** — defines what "done" means at the story level.
3. **The build / change log** — what was actually changed in this release.
4. **The test environment access** — staging URL, credentials, sample data, any feature flags to flip.

If any of (1)(2)(3) is missing, the QA pass becomes guessing. Push back and get them first.

## The QA workflow

```
1. Plan         → derive a test plan from PRD + Stories + ACs
2. Execute      → run the planned tests + an exploratory session
3. Report bugs  → file every defect with full repro
4. Triage       → severity / priority calls, with the dev + PM
5. Re-verify    → confirm each fix actually fixes it
6. Sign off     → go/no-go on release readiness
```

Each step has a dedicated reference. Load only what the current task needs.

## Topic selector

| Task | Reference | Asset |
|---|---|---|
| Author a test plan for a feature | [references/test-plan.md](references/test-plan.md) | [assets/test-plan-template.md](assets/test-plan-template.md) |
| Run a focused exploratory session | [references/exploratory-charters.md](references/exploratory-charters.md) | [assets/exploratory-charter-template.md](assets/exploratory-charter-template.md) |
| File a bug report | [references/bug-reports.md](references/bug-reports.md) | [assets/bug-report-template.md](assets/bug-report-template.md) |
| Run the release-readiness gate | [references/release-readiness.md](references/release-readiness.md) | [assets/release-checklist-template.md](assets/release-checklist-template.md) |

## Severity vs priority (terminology that matters)

These are not synonyms. Confusing them produces bad triage.

- **Severity** = how bad the impact is when the bug occurs. Crash, data loss, security breach → high severity. Misaligned padding → low severity.
- **Priority** = how soon it should be fixed, relative to other work.

A bug can be high severity but low priority (rare crash on an obsolete browser) or low severity but high priority (typo on the front page of a launch).

Always set both. See [references/bug-reports.md](references/bug-reports.md).

## Quality gates

Before signing off on release:

- [ ] Every AC in every story has been executed (automated or manual). No AC is left "unknown".
- [ ] All bugs filed during QA are triaged (severity + priority + owner).
- [ ] All high-severity bugs are fixed and re-verified, or explicitly accepted by the product owner with a release-notes entry.
- [ ] Regression suite passed against the release candidate.
- [ ] No skipped or quarantined tests added during this cycle.
- [ ] Release checklist passed (deployment, monitoring, rollback plan, on-call). See [release-readiness.md](references/release-readiness.md).

## Common mistakes

- **Starting QA without a plan.** Random clicking misses systematically. Plan first, even briefly.
- **Filing vague bugs.** "It doesn't work" is not a bug report — see the bug-report reference.
- **Confusing severity and priority.** "Critical" is not a priority; it's a severity.
- **Skipping exploratory testing.** Plans only cover what you thought of. Exploration catches what you didn't.
- **Signing off without re-verifying fixes.** "Fixed" in a tracker doesn't mean fixed in the build.
- **Treating QA as a separate phase after dev "finishes".** QA scoping should happen alongside the implementation, not at the end.
- **No release rollback plan.** "We'll handle it if it goes wrong" — under pressure, with users complaining, you won't.
