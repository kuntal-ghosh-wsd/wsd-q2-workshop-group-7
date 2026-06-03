# Stage 2 — PRD → User Stories

User stories translate PRD requirements into user-perspective slices of work. Each story is small enough to ship independently and clear enough that someone outside the conversation can pick it up.

## Contents
- [Pre-requisite](#pre-requisite)
- [Standard story format](#standard-story-format)
- [Document structure](#document-structure)
- [Traceability — every story links to a REQ](#traceability--every-story-links-to-a-req)
- [INVEST checklist](#invest-checklist)
- [Splitting heuristics](#splitting-heuristics)
- [Sizing — how many stories per PRD?](#sizing--how-many-stories-per-prd)
- [Coverage gate](#coverage-gate)
- [Common mistakes](#common-mistakes)

## Pre-requisite

The PRD must exist and be readable. Re-read it before drafting stories — do not work from a summary in conversation history. Drift between the PRD and stories is the #1 reason downstream artifacts fail review.

## Standard story format

Use the classic Connextra template:

```
**US-001** — As a *data analyst*, I want to *save a dashboard configuration to a custom name* so that *I can return to it later without rebuilding it*.

**Covers:** REQ-001
**Priority:** must-have
**Estimate:** S
```

Mandatory fields: ID, role, want, benefit, REQ link, priority.
Optional fields: estimate (S/M/L or points), notes.

Why all three of *role / want / benefit*? Drops the "want" and you have a feature description, not a story. Drops the "benefit" and reviewers can't tell why it matters.

## Document structure

```
# <Product/Feature> — User Stories

> Generated from PRD vN. Each story links to one or more REQs.

## Theme: <Theme name from PRD>

### US-001 — <one-line summary>
As a ..., I want to ..., so that ...
**Covers:** REQ-001, REQ-002
**Priority:** must-have
**Acceptance criteria:** *(filled in Stage 3)*

### US-002 — ...
```

Group stories by the same themes used in the PRD. Theme order should match the PRD's theme order for easy cross-reference.

## Traceability — every story links to a REQ

Each story must reference at least one `REQ-XXX`. This is what makes coverage analysis possible.

- One story → one REQ (most common, cleanest)
- One story → multiple REQs (acceptable when one slice naturally satisfies several closely-related REQs)
- Multiple stories → one REQ (common — a single REQ often takes 2–4 stories to fully cover)

Never have a story with no REQ link. If a story doesn't trace back, either the PRD is missing a REQ (go fix it) or the story is out of scope (drop it).

## INVEST checklist

Each story should be:

- **I**ndependent — can be developed without waiting on others. Cross-story dependencies should be the exception, not the rule.
- **N**egotiable — captures intent, not a contract on implementation details.
- **V**aluable — delivers something the user (or business) cares about. "Set up the database" is a task, not a story.
- **E**stimable — the team can size it. If they can't, the story is too vague or too big.
- **S**mall — fits in one sprint / iteration. If it can't, split (see next section).
- **T**estable — there's an obvious way to verify it works. If not, the story is too vague.

## Splitting heuristics

When a story is too big, split using one of these patterns (in rough order of preference):

| Pattern | Example |
|---|---|
| **By workflow step** | "Onboarding" → "User signs up" / "User verifies email" / "User completes profile" |
| **By data type / variant** | "Export data" → "Export CSV" / "Export JSON" / "Export PDF" |
| **By happy path vs edge cases** | "Upload file" → "Upload happy path" / "Upload with retry on failure" / "Upload with size limit error" |
| **By role / permission level** | "View reports" → "Viewer can view" / "Admin can view + edit + delete" |
| **By CRUD operation** | "Manage widgets" → "Create widget" / "Edit widget" / "Delete widget" |
| **By UI surface** | "Search" → "Search from header" / "Search from results page" |

Avoid splitting by technical layer ("backend API" + "frontend UI" + "database migration") — that produces stories with no independent user value.

## Sizing — how many stories per PRD?

Rule of thumb: **1.5× to 3× the requirement count.**

| PRD requirement count | Expected story count |
|---|---|
| 8–15 REQs | 12–25 stories |
| 20–30 REQs | 35–60 stories |
| 40–60 REQs | 70–120 stories |

If the ratio is much lower (e.g. 25 REQs → 25 stories), stories are likely too big — they will be hard to estimate and risky to ship. Split them.

If much higher (e.g. 25 REQs → 150 stories), stories are likely too small or the PRD is under-specified — consolidate stories or revisit the PRD.

## Coverage gate

Before moving on to ACs (Stage 3) or the TAD (Stage 4), verify every **must-have** REQ has at least one story.

Quick check from the command line:

```bash
# List all REQ IDs from the PRD
grep -oE 'REQ-[0-9]+' PRD.md | sort -u > /tmp/all-reqs.txt

# List all REQ IDs covered by stories
grep -oE 'REQ-[0-9]+' USER-STORIES.md | sort -u > /tmp/covered-reqs.txt

# Show uncovered REQs
comm -23 /tmp/all-reqs.txt /tmp/covered-reqs.txt
```

Anything that prints is uncovered. If any of those is `must-have` in the PRD, **add a story for it** before continuing. `should-have` and `nice-to-have` gaps are not blocking — flag them to the user and let them decide.

## Common mistakes

- **Stories that describe implementation, not user value.** "Add a Redis cache to the dashboard endpoint" is a task; the story is "As a user, I want dashboards to load in under 1 second so the UI feels responsive." Implementation belongs in the TAD.
- **Stories without REQ links.** Breaks traceability. If a story has no REQ, fix the PRD or drop the story.
- **One giant story per REQ.** Most REQs need 2–4 stories. A 1:1 ratio is a signal that stories haven't been split.
- **Stories that span the full feature.** "User can manage their account" is an epic, not a story. Split it.
- **Reordering or renumbering existing stories during edits.** Breaks every existing AC and TAD reference. Append new IDs (`US-042`, `US-043`), don't reshuffle.
- **Stories grouped by team instead of by theme.** "Frontend stories" / "Backend stories" hides the user journey. Group by the PRD's themes.
