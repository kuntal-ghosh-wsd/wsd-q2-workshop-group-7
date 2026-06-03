# Stage 3 — Acceptance Criteria

Acceptance Criteria turn a user story into something **testable** and **demonstrable**. They live inside the story document (`USER-STORIES.md`), nested under each story.

## Contents
- [Where ACs live](#where-acs-live)
- [Two acceptable formats](#two-acceptable-formats)
- [Wording bar — the testability test](#wording-bar--the-testability-test)
- [How many ACs per story?](#how-many-acs-per-story)
- [What ACs should cover](#what-acs-should-cover)
- [ID conventions](#id-conventions)
- [Iterating on ACs](#iterating-on-acs)
- [Common mistakes](#common-mistakes)

## Where ACs live

ACs are **not a separate document**. They are nested under each user story, inline:

```
### US-001 — Save dashboard with custom name
As a data analyst, I want to save a dashboard configuration to a custom name so that I can return to it later without rebuilding it.

**Covers:** REQ-001
**Priority:** must-have

**Acceptance criteria:**
- **AC-101** — Given a user with edit permission on a dashboard, when they click "Save as…" and enter a unique name, then the dashboard is persisted under that name and appears in their dashboard list within 2 seconds.
- **AC-102** — Given a user attempts to save with a name already used in their workspace, when they submit, then the form shows an inline error "A dashboard with this name already exists" and no save occurs.
- **AC-103** — Given a saved dashboard, when the user re-opens it, then all widgets, filters, and layout are restored exactly as saved.
```

Keep them with the story — splitting them into a separate file makes them rot.

## Two acceptable formats

Pick **one** format per document and use it consistently.

### Format A — Given / When / Then (Gherkin-style)

Best when behaviour depends on context (state, role, permission).

```
- **AC-101** — Given a user with edit permission, when they click "Save as…" and enter a unique name, then the dashboard is persisted and listed in their dashboards within 2 seconds.
```

Structure: `Given <context>, when <action>, then <observable outcome>`.

### Format B — Rule-based (declarative)

Best when behaviour is unconditional or list-like.

```
- **AC-101** — Saving requires a non-empty name between 1 and 80 characters.
- **AC-102** — Saving is idempotent: re-saving the same dashboard updates the existing record, not creates a new one.
- **AC-103** — Save latency is < 2 seconds at p95 under normal load.
```

Structure: a single concrete, observable rule per bullet.

### Choosing

| Story type | Format |
|---|---|
| User-flow with conditional branches | Given / When / Then |
| API contracts, validation rules, NFRs | Rule-based |
| UI behaviour with multiple states | Given / When / Then |
| Configuration, defaults, calculation rules | Rule-based |

Do not mix formats within a single story — pick one. Mixing forces the reader to re-orient mid-list.

## Wording bar — the testability test

For every AC, ask: **"Could a tester (or test script) tell pass from fail from this sentence alone?"** If no, rewrite.

### ✅ Pass
- "The API returns HTTP 403 with body `{ "error": "forbidden" }` when called by a user without `dashboards:write` permission."
- "Files larger than 50 MB are rejected with the message 'File too large (max 50 MB)' before upload begins."
- "p95 latency for `GET /dashboards/:id` is under 200 ms under 100 RPS sustained load."
- "When the network is unavailable, the UI shows the offline banner within 3 seconds and disables the Save button."

### ❌ Fail (and why)
- "Permissions should work properly." — no predicate, untestable.
- "The dashboard loads fast." — no threshold, no condition.
- "Errors are handled gracefully." — no observable behaviour specified.
- "The UI is intuitive." — subjective, not testable.
- "Performance is acceptable." — by what measure?

### Cheat sheet for measurability

| Weasel word | Concrete replacement |
|---|---|
| "fast" / "quickly" | "p95 < 200ms", "within 1 second" |
| "handle gracefully" | name the exact UI message + state |
| "properly" / "correctly" | name the exact rule or outcome |
| "large" / "small" | give the bound: "> 50 MB", "< 1000 chars" |
| "many users" | "100 concurrent users", "10k RPS" |

## How many ACs per story?

**2 to 6 is the healthy range.** One-AC stories are usually under-specified; 7+ usually means the story should be split.

A balanced AC set covers:

1. The happy path (mandatory)
2. At least one validation / error case
3. Non-functional concerns where relevant (latency, accessibility, permissions, audit)

If a story has 8+ ACs, look for natural split lines — usually two flows or two roles got conflated.

## What ACs should cover

For each story, walk this checklist when drafting ACs:

- [ ] **Happy path** — the main success scenario.
- [ ] **Boundary inputs** — empty, max length, max value, edge of valid range.
- [ ] **Invalid inputs** — what the system rejects, with what message.
- [ ] **Permission / role variants** — what each role sees / can do.
- [ ] **Network or upstream failure** — graceful degradation, retry, error state.
- [ ] **Concurrency / idempotency** — if two clients act simultaneously, what wins?
- [ ] **Performance** — at least one latency or throughput bound if the story touches a hot path.
- [ ] **Accessibility** — keyboard nav, screen reader, color contrast — at least one AC for any UI story.
- [ ] **Audit / observability** — what gets logged or emitted, when relevant.

Not every story needs every category — but each category should be considered.

## ID conventions

Use `AC-<story-number><sequence>` so the parent is obvious:

- `US-001` → `AC-101`, `AC-102`, `AC-103`
- `US-002` → `AC-201`, `AC-202`
- `US-042` → `AC-4201`, `AC-4202` (zero-pad if needed for sort stability)

Never renumber existing ACs — append new ones at the end of the story's AC list.

## Iterating on ACs

When the user asks to refine ACs, common moves:

- **Add an AC** — append to the story's AC list with the next sequence number.
- **Split an AC** — when one AC tests two distinct behaviours, break it into two, preserving the original ID for one half and adding a new ID for the other.
- **Tighten wording** — replace weasel words with measurable predicates (see cheat sheet above).
- **Remove an AC** — only if duplicative. Out-of-scope ACs are usually a signal the story is wrong, not the AC.

## Common mistakes

- **Treating ACs as a separate document.** They belong inline with the story.
- **One-AC stories.** Almost always under-specified. Add edge cases and NFRs.
- **ACs that restate the story.** "The user can save the dashboard." That's the story, not an AC — the AC must describe an observable, measurable outcome.
- **Weasel words.** "Properly", "correctly", "as expected", "fast" — all untestable. Replace with predicates.
- **ACs that describe implementation.** "The save handler must use a database transaction." That's a TAD concern, not an AC. The AC says: "Partial saves never occur — either the whole dashboard saves or nothing changes."
- **Mixing formats within one story.** Given/When/Then mixed with rule-based bullets confuses readers — pick one per story.
