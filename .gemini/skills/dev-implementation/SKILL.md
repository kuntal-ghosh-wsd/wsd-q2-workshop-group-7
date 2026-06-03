---
name: dev-implementation
description: >
  Guide implementation work from a user story (with Acceptance Criteria)
  and a Technical Architecture Document into shippable, reviewable code.
  Tool- and stack-agnostic — works in any language or framework, produces
  guidance and templates, not code generation. Use when the user is about
  to write code for a specified story, asks how to break a story into
  commits or PRs, wants help slicing work, requests refactoring guidance,
  needs a PR description, or asks how to make a piece of code review-ready.
  Triggers on phrasing like "implement this story", "how do I split this
  into commits", "make this PR ready for review", "refactor this", "write
  a PR description", "what should I commit first", "how do I scope this
  change". Provides slicing strategies, code-quality heuristics,
  refactoring patterns, and PR hygiene templates.
---

# Developer Implementation

A guide for turning a story + AC + TAD into clean, reviewable code. Tool-agnostic — language- and framework-independent.

## When to use this skill

Trigger when the user is about to **build something**, **scope a code change**, or **prepare code for review**:

| Signal phrase | Topic |
|---|---|
| "implement story US-...", "let's build this feature", "where do I start" | Slicing & implementation loop |
| "this commit is too big", "how do I split this", "what's the first slice" | Slicing |
| "is this code good", "this feels messy", "should I refactor" | Code quality / refactoring |
| "write a PR description", "how should I title this PR", "make this PR ready" | PR hygiene |
| "what's a clean way to..." (asking about structure, not syntax) | Code quality |

**Do not use** for: pure syntax help, library lookups, debugging a failing test, fixing a specific bug. Those are direct coding tasks, not implementation guidance.

## Pre-flight (always run first)

Before writing code, gather the inputs that drive every implementation decision:

1. **Find the story and its ACs.** Without them, the work is unbounded — push back if they don't exist.
2. **Find the TAD section that covers the affected components.** Implementation decisions that contradict the TAD will get bounced in review.
3. **Find related existing code.** Grep for the relevant component/module — patterns already in the codebase usually beat anything you would invent.
4. **Identify the smallest first slice.** See [references/slicing.md](references/slicing.md).

If any of (1) (2) (3) is missing, surface the gap to the user before writing code. Don't invent answers.

## The implementation loop

```
1. Slice         → pick the smallest end-to-end change that adds value
2. Code          → implement only that slice; resist scope creep
3. Self-review   → run the quality checklist before pushing
4. Commit        → one logical change per commit (see assets/commit-message-template.md)
5. Open PR       → small PRs land faster (see references/pr-hygiene.md + assets/pr-template.md)
6. Iterate       → respond to review, repeat
```

The loop is the same regardless of stack. The hard part is discipline at step 1 (slicing) and step 3 (self-review).

## Topic selector

Load only the reference relevant to the current question. Do not load all upfront.

| Question | Reference |
|---|---|
| "How do I split this story into commits / PRs?" | [references/slicing.md](references/slicing.md) |
| "Is this code clean / well-named / well-structured?" | [references/code-quality.md](references/code-quality.md) |
| "Should I refactor this? How?" | [references/refactoring.md](references/refactoring.md) |
| "Write me a PR description / make this PR review-ready" | [references/pr-hygiene.md](references/pr-hygiene.md) |

## Self-review checklist (every commit)

Walk this before pushing. 90 seconds of self-review saves 30 minutes of reviewer time.

- [ ] **Maps to an AC** — this commit advances at least one specific AC. If not, ask why it exists.
- [ ] **Single concern** — diff covers one logical change. No drive-by refactors mixed with feature work.
- [ ] **Names communicate intent** — a reviewer can guess what each new identifier does without reading its body.
- [ ] **No dead code** — no commented-out blocks, no unused vars, no TODO without a tracking issue or ticket reference.
- [ ] **No new warnings** — linter, type checker, build all clean.
- [ ] **No secrets** — grep the diff for keys, tokens, passwords, `.env`-shaped strings before staging.
- [ ] **Tests reflect the AC** — at least one test asserts the AC's predicate, not just that "the code runs".
- [ ] **Commit message** — explains *why*, not *what*. The diff already shows *what*.

## Quality gates

These apply at PR boundaries, not commit boundaries:

- **AC coverage** — every AC in the story is exercised by at least one test in the PR (or explicitly deferred with reason).
- **No scope creep** — the PR description's bullet list matches the diff. If the diff has more, split or shrink.
- **CI green** — never request review on a red PR.
- **Reviewable size** — see [references/pr-hygiene.md](references/pr-hygiene.md). If the PR exceeds the threshold, split.

## Common mistakes

- **Starting at the deepest layer.** Writing the database schema first feels productive but the surface UX often forces schema changes — start from the user-visible slice and work inward.
- **One giant commit per story.** A reviewer cannot meaningfully review 800 lines in one go. Slice.
- **Bundling refactors with feature work.** Two commits, two diffs, two reviews. Mixing them hides both.
- **Writing the PR description from the diff.** Write it from the story+ACs — the diff is implementation, the PR description is intent.
- **Skipping self-review.** Reviewers will catch what you would have caught — but they will also start mistrusting your PRs.
- **Implementing past the AC.** "While I'm here, let me also add…" — that belongs in a separate story.
