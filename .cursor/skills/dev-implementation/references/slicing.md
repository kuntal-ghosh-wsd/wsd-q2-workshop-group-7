# Slicing Work into Small, Shippable Changes

The unit of progress is the **smallest end-to-end slice that adds visible value**. Most stalled implementations are stalled because the first slice was too big.

## Contents
- [What "smallest end-to-end slice" means](#what-smallest-end-to-end-slice-means)
- [Slicing patterns](#slicing-patterns)
- [How small is small enough?](#how-small-is-small-enough)
- [Walking skeleton first](#walking-skeleton-first)
- [Anti-patterns](#anti-patterns)

## What "smallest end-to-end slice" means

End-to-end = it touches every layer the feature needs (UI → API → data → back), even if each layer is minimal. Smallest = the most stripped-down version that still does something a user could observe.

Example — story is "User can save a dashboard with a custom name":

| Slice | End-to-end? | Useful? |
|---|---|---|
| Add a `dashboards.name` column to the DB | No — backend only | No |
| Add a "Save as" button that does nothing | No — UI only | No |
| Add "Save as" → save name → fetch back on reload — hardcoded to one dashboard | ✅ | ✅ first slice |
| Generalize to all dashboards, with validation | ✅ | ✅ second slice |
| Permission checks, rate limiting, audit log | ✅ | ✅ third slice |

The first slice is intentionally embarrassing — that's the point. It proves the wiring works. Everything after is incremental polish.

## Slicing patterns

When a story or AC list is too big for one PR, split using one of these (rough order of preference):

| Pattern | Example |
|---|---|
| **Happy path first, edges later** | First PR: save with valid name. Next PR: duplicate-name error, empty-name error. |
| **One AC per PR** | If a story has 4 ACs and each is non-trivial, four PRs is fine. |
| **By role / permission** | First PR: feature works for one role. Next PR: extend to others. |
| **By data type / variant** | Search supports text first, then numbers, then dates. |
| **Read before write** | Display a dashboard before allowing edits. |
| **One screen at a time** | Settings page section A, then B, then C. |
| **By layer — only when forced** | Schema migration in PR 1, behaviour in PR 2. Only use when migration must land separately for ops reasons. |

Avoid **purely horizontal slices** ("PR 1: backend, PR 2: frontend") — they produce a long stretch with no user-visible progress and the integration risk hits at the end.

## How small is small enough?

Rules of thumb:

- **PR size**: aim for **< 300 lines of diff**, hard limit ~600. Above that, reviewers skim. A 1500-line PR will be merged with two emojis and no real review.
- **PR duration**: an implementer should be able to draft, self-review, and open the PR in under a day.
- **Commit count per PR**: 1–6 commits. More than that usually means the PR should be split.
- **Time on a single commit**: under 30 minutes. If you've been on one commit for two hours, slice further.

If a slice can't get under those bounds, the underlying story is too big — go back to the story author and split the story, not just the implementation.

## Walking skeleton first

For a new feature in a new area:

1. **PR 0** — Walking skeleton. Wire UI → API → data store with hardcoded everything. No business logic, no edge cases. Tests assert that the wires work.
2. **PR 1+** — Fill in real behaviour one AC at a time.

The skeleton PR is often the highest-risk one because it exposes integration questions. Land it first while you have appetite for big design discussions.

## Anti-patterns

- **"Big bang" PRs.** "Here is the whole feature." Reviewers can't meaningfully review. Defects slip. Split.
- **Horizontal slicing.** "Backend PR first, frontend PR second." Backend lives unused for days, integration bugs surface at the end.
- **Premature generalization.** First slice handles N=1 hardcoded; a reviewer asks "shouldn't this be parameterized?" — fine, do it in slice 2, not slice 1.
- **Refactor + feature in same PR.** Two reviews, two failure modes. Split into two PRs landed in order: refactor first, feature on top.
- **Migration + behaviour in same PR.** Schema changes have different rollback characteristics — keep them separate so you can revert one without the other.
- **"While I'm in here..."** Tangential cleanup. Note it in a TODO file and open a separate PR.
