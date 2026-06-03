<!-- PR template — replace placeholders, delete sections that don't apply -->

## Summary

<One paragraph: what this PR does and why, in story+AC terms. Not a list of files changed.>

## Linked story / ACs

- <Story link or ID, e.g. US-042>
- ACs implemented: <AC-4201, AC-4202>
- ACs explicitly deferred: <AC-4203 — reason>

## How to verify

1. <Step 1: setup / branch / data needed>
2. <Step 2: action to take>
3. <Step 3: expected outcome>

(Reviewer should be able to follow these without asking questions.)

## Out of scope (deferred)

- <Thing reviewers might expect that isn't here, with reason or follow-up issue link>

## Risk & rollback

- **Risk:** <what could break, blast radius>
- **Monitoring:** <what to watch after deploy>
- **Rollback:** <revert this PR / feature-flag off / DB migration reversible? / etc.>

## Screenshots / artifacts

<UI before / after, query plans, perf numbers, etc. Delete this section if not applicable.>

## Checklist

- [ ] Tests cover every AC in this PR
- [ ] CI is green
- [ ] Self-reviewed in the PR UI (not just locally)
- [ ] PR description matches the actual diff
- [ ] No secrets, debug prints, or commented-out code in the diff
