<!-- Commit message template — Conventional Commits style, but the structure works regardless of convention -->

<type>(<scope>): <imperative one-line summary, ≤72 chars>

<Blank line above.>

<Body: explain *why* this change, not *what*. The diff already shows what.
Include trade-offs considered, references to story/AC IDs, links to
upstream issues or design docs. Wrap at 72 chars.>

<Blank line above, then optional trailers.>

Refs: US-042, AC-4201
Co-authored-by: <Name> <email>

<!--
Common <type> values (Conventional Commits):
  feat     — new user-visible capability
  fix      — bug fix
  refactor — change shape, not behaviour
  perf     — performance improvement
  test     — add or fix tests
  docs     — documentation only
  chore    — build, deps, tooling
  style    — formatting only (rare; usually rolled into the change it supports)

<scope> is optional — the area of code affected, e.g. `auth`, `dashboards-api`.

Example:
  feat(dashboards): allow saving with custom name

  Adds a "Save as" action that persists the dashboard under a
  user-chosen name. Implements AC-4201 and AC-4202; AC-4203
  (rename-on-conflict UX) is deferred to a follow-up.

  Persists via the existing dashboards repository; no schema
  migration needed because the `name` column already exists.

  Refs: US-042
-->
