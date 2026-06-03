# PR Hygiene

A well-shaped pull request lands faster than a poorly-shaped one of the same size. The shape carries most of the cost.

## Contents
- [What a good PR looks like](#what-a-good-pr-looks-like)
- [Sizing](#sizing)
- [PR description structure](#pr-description-structure)
- [Commit hygiene](#commit-hygiene)
- [Self-review before requesting review](#self-review-before-requesting-review)
- [Responding to review](#responding-to-review)
- [Common mistakes](#common-mistakes)

## What a good PR looks like

- **One change.** Either a feature slice, a refactor, a bug fix, or a dependency bump. Never a mix.
- **Small.** Diff fits in a reviewer's head (see [Sizing](#sizing)).
- **CI green** at the moment review is requested.
- **Description matches the diff** — no surprises in the file tree.
- **Title** reads like a commit message: imperative mood, one short sentence.
- **Self-reviewed** before request — the author has left inline comments explaining non-obvious choices.

## Sizing

| Diff size (lines added + removed) | Reviewer experience |
|---|---|
| < 100 | Reviewed thoughtfully in one sitting |
| 100–300 | Sweet spot for most PRs |
| 300–600 | Acceptable for routine work (e.g. config migration) |
| 600–1000 | Reviewers skim. Bugs slip through. |
| > 1000 | Functionally unreviewable. Split. |

Lines counted exclude auto-generated files (lockfiles, snapshots, formatter changes). If those dominate the diff, isolate them in their own commit so reviewers can skip them.

## PR description structure

Use a consistent shape so reviewers know where to look. See [assets/pr-template.md](../assets/pr-template.md) for a copy-pasteable starter. The skeleton:

```
## Summary
<One paragraph: what this PR does and why, in story+AC terms, not in implementation terms.>

## Linked story / ACs
- US-042
- AC-4201, AC-4202

## How to verify
1. <Reviewer-runnable step>
2. <Reviewer-runnable step>
3. <Expected outcome>

## Out of scope (deferred)
- <Thing reviewers might expect that isn't here, with reason>

## Risk & rollback
- <What could break, what to monitor, how to roll back>

## Screenshots / artifacts
- <If UI changes, include before/after>
```

**The PR description is written from the story, not the diff.** Reviewers can read the diff themselves; they need help understanding intent.

## Commit hygiene

Within a PR, commit history should tell a story.

**Good:**
1. `Refactor: extract OrderPricer from OrderService`
2. `Add discount calculation to OrderPricer`
3. `Expose discount in order summary API`
4. `Update API consumer tests for discount field`

Each commit is independently understandable, builds and passes tests, makes one logical change.

**Bad:**
- `WIP`
- `fix`
- `address review comments`
- `more stuff`
- `oops`

Squash the bad ones before requesting review (`git rebase -i`). The merge commit is forever.

**Commit message format** — see [assets/commit-message-template.md](../assets/commit-message-template.md). Imperative subject ≤72 chars, body explains *why*.

## Self-review before requesting review

Before clicking "Request review", spend 5 minutes:

1. **Read the diff in the PR UI**, not your IDE. A different view catches different mistakes.
2. **Leave inline comments** on non-obvious choices: "Using a Set here because the input may have duplicates and order doesn't matter."
3. **Verify the description matches the diff** — re-read the description, then scan the file tree. Surprises = description out of date.
4. **Run the verification steps** from the description. If you can't, neither can the reviewer.
5. **Check CI is green** before adding reviewers.

This is the single highest-leverage habit. The 5 minutes you spend save the reviewer 30 minutes of context-building.

## Responding to review

- **Address every comment**, even with a brief `done` or `won't fix because <reason>`. Silence is rude.
- **Push fixups as separate commits** during review (don't force-push during active review — reviewers lose the thread). Squash before merge.
- **If you disagree, say why.** Reviewers are not always right. A thoughtful disagreement is fine. "I'll do X instead because Y" is fine. Quiet override is not.
- **Don't argue about taste.** If a reviewer asks for a name change and you have a slight preference for the original, change it. Save your political capital for substance.
- **Re-request review** explicitly after changes — don't assume reviewers see the new commits.

## Common mistakes

- **Bundled PR.** Feature + refactor + dependency bump in one. Split, every time.
- **Description from the diff.** Lists every changed file instead of explaining intent.
- **No "how to verify"** section. Reviewer has to guess what to test.
- **Force-push during review.** Reviewer loses the thread of what changed since their last look.
- **CI red when requesting review.** Wastes everyone's time. Fix first.
- **Adding scope after review starts.** "Reviewer asked about X so I also added Y, Z." Open a new PR for Y, Z.
- **Long PR description that contradicts the diff.** Description was written at the start of the work and never updated.
- **No screenshots for UI changes.** Reviewers won't run your branch locally — show them.
