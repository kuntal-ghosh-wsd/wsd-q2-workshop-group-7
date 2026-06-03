# Stage 5 — Stories + ACs + TAD → Build Sequence (Implementation Detail)

A Build Sequence (BS) is an **ordered, dependency-aware task list** that turns approved stories, acceptance criteria, and the TAD into discrete implementation units called **FBS** (Feature Build Specifications). Each FBS is a self-contained slice of work the team can pick up, build, test, and ship.

The Build Sequence is the bridge between specification and execution. After Stage 5 hands off, downstream work uses the `dev-implementation` skill on individual FBS units; this skill does not produce the actual code.

## Contents
- [What is an FBS?](#what-is-an-fbs)
- [Inputs to gather](#inputs-to-gather)
- [Generation strategy](#generation-strategy)
- [FBS structure](#fbs-structure)
- [Sizing — how big is one FBS?](#sizing--how-big-is-one-fbs)
- [Dependencies and ordering](#dependencies-and-ordering)
- [Drafting procedure](#drafting-procedure)
- [Quality bar](#quality-bar)
- [Common mistakes](#common-mistakes)

## What is an FBS?

An FBS is one **testable, deployable** increment. After completing the FBS, a reasonable observer can verify the listed testable outcomes are true — without depending on later FBS work.

An FBS is **not** a Jira ticket, **not** a commit, **not** a single function. It's a coherent slice: typically one or two stories' worth of ACs that share a component, a domain, or a dependency root.

Concrete examples:

- ✅ "Confluence webhook receiver + dedup + persist raw event" — small/medium, covers US-003's webhook ACs end-to-end, deployable behind a flag.
- ✅ "Per-page PDF generation with audit footer" — medium, covers US-013's ACs, has clear testable outputs.
- ❌ "Implement Confluence sync" — too large, spans multiple stories and many ACs.
- ❌ "Add a `Page` table" — too small, not a testable increment on its own.

## Inputs to gather

Ask **only these** before drafting. Anything else, infer and confirm.

1. **Generation strategy.** One of: `vertical-slice`, `dependency-first`, `domain-grouped`, `risk-front-loaded`. Default = `dependency-first` unless the user names another. See [Generation strategy](#generation-strategy).
2. **Sizing preference.** Target FBS size (small / medium / large) and an upper hour bound per FBS (default ≤ 8h, hard cap 16h).
3. **Cross-cutting platform work the team already has.** E.g. an existing auth library, an existing observability framework — these may eliminate the need for FBS units the brief implies.
4. **Phasing / cut-line.** Which `priority: must` stories must reach a first ship, vs. what defers.

If the user did not specify, draft with defaults and call out the assumed strategy + sizing in the BS `buildPhilosophy` field.

## Generation strategy

Pick **one** strategy per Build Sequence and record it in the JSON's `generationStrategy` field. The strategy shapes the ordering, not the FBS content.

| Strategy | When to use | What it optimises |
|---|---|---|
| `dependency-first` | Default. New product or significant new subsystem. | Earliest reduction of unknowns; everything later builds on a stable foundation. |
| `vertical-slice` | Customer-visible product with a clear "thin slice" demo goal. | A demoable end-to-end path lands fast; depth fills in over later FBS. |
| `domain-grouped` | Multi-domain project where teams own different domains. | One team can drain its domain without waiting on cross-team handoffs. |
| `risk-front-loaded` | Project with a known high-risk unknown (novel integration, perf cliff, regulated component). | The thing that could derail the project is proven or killed first. |

**Mixing strategies** within one BS produces an incoherent order — pick one and live with the trade-off.

## FBS structure

Every FBS in the JSON's `buildSequence[]` carries the following fields. **Bold** = required by the schema.

- **`id`** — `FBS-XXX`, contiguous within the BS document.
- **`title`** — short, one-line, no period at end.
- **`summary`** — 1–3 sentences: what this delivers, why it's grouped this way.
- **`storyScope[]`** — array of `{ usId: "US-XXX", acIds: ["AC-XXX", ...] }`. The AC IDs covered must come from the named story. **Every AC must be allocated to exactly one FBS** across the whole BS — no orphan ACs, no double-counted ACs.
- **`testableOutcomes[]`** — 3–8 plain-English statements a reviewer can independently verify. **These must trace to the storyScope's ACs.** If an outcome doesn't map back to an AC, either remove it or add an AC upstream.
- **`status`** — one of `not-started` / `in-progress` / `complete` / `verified`. Initial value `not-started`.
- `dependencies[]` — array of FBS IDs this builds on. Must be earlier in the sequence and form a DAG.
- `domain` — string, optional. Often matches a PRD theme.
- `riskLevel` — `low` / `medium` / `high`. Drives review attention.
- `sessionMeta`:
  - `estimatedSize` — `small` / `medium` / `large`.
  - `estimatedHours` — 0.5–16. **Hard cap 16**; over that, split.
  - `contextRequirements` — what the implementer needs in their head: `prdSections[]`, `tadSections[]`, `existingModules[]`, `schemas[]`, `externalDocs[]`, `other[]`.
  - `deliverables[]` — the artefacts produced (modules, tests, docs, configs).
- `notes` — free-form caveats.

## Sizing — how big is one FBS?

| Size | Target hours | Roughly equals | When |
|---|---|---|---|
| small | ≤ 3 | A single contained change with a handful of ACs covered | A leaf module, a single endpoint, a config wiring |
| medium | 3–8 | One story end-to-end or two tightly related stories | Default size |
| large | 8–16 | A subsystem slice, multiple ACs across 2–3 stories | Use sparingly; prefer splitting |

**Anything > 16h must be split.** Two signs an FBS is too big: (1) you cannot list `testableOutcomes` without saying "and various other things"; (2) the deliverables list crosses three or more architectural components.

For sizing context: the reference RCF project's PRD-001 build sequence produced **~105 FBS across 13 BS documents** for ~40 must-have REQs. Your numbers should land in a similar order of magnitude — not 5, not 500.

## Dependencies and ordering

- An FBS may only depend on FBS that appear **earlier** in the same BS document's `buildSequence[]` array.
- Multiple FBS documents per PRD are allowed for very large projects (the reference uses `BS-001..BS-013` for one PRD). When splitting, use `partInfo.fbsRange` to label the FBS range each BS covers, and the global FBS ID space stays contiguous across documents.
- The full dependency graph across all BS documents must be a DAG. **Validate before stopping** — a cycle hidden across two BS documents is much harder to notice later.

### Detecting cycles by inspection

For a single BS document, scan top-to-bottom: each FBS's `dependencies[]` must contain only IDs that appeared earlier in the array. If any forward reference appears, either reorder or remove the dependency.

## Drafting procedure

1. **Re-read upstream.** Open the PRD JSON, the user stories JSON, and the TAD JSON. Make a mental map: REQ → US → AC → architectural component. This is the input to slicing.
2. **Pick a generation strategy** (see above) and record it.
3. **Enumerate every AC across every story.** This is the universe to allocate. Count them — that number is the floor for the total `testableOutcomes` across the BS.
4. **Group ACs into FBS candidates** using the chosen strategy. Default heuristic: group ACs that share both a story and an architectural component.
5. **Order the FBS** so dependencies only point backwards.
6. **Estimate size + hours per FBS.** Anything > 16h splits.
7. **Validate AC coverage.** Every AC ID appears in exactly one FBS's `storyScope`. Use a coverage table during drafting.
8. **Validate DAG.** Trace dependencies; no cycles.
9. **Show the user** the markdown view (table of FBS with title, scope, deps, size). Iterate.
10. **Mirror to JSON** and update the manifest.

## Quality bar

Scan for these before showing the draft:

- [ ] Every AC across every story is covered by exactly one FBS.
- [ ] Every FBS has 3–8 testable outcomes (not 1, not 30).
- [ ] No FBS estimates > 16h.
- [ ] No cyclic dependencies. Every FBS's `dependencies[]` points only to earlier FBS in the same `buildSequence[]`.
- [ ] Every FBS has a non-empty `summary` that explains *why* this grouping exists, not just *what* is in it.
- [ ] `generationStrategy` is set and consistent with the actual ordering.
- [ ] The BS JSON validates against `assets/schemas/build-sequence.schema.json` (key constraints: `^BS-\d{3,}$`, `^FBS-\d{3,}$`, `status` ∈ {not-started, in-progress, complete, verified}, `generationStrategy` ∈ {vertical-slice, dependency-first, domain-grouped, risk-front-loaded}, `estimatedHours` ∈ [0.5, 16]).
- [ ] First-pass FBS count is in a sensible range (~1–4 FBS per must REQ; ~5–30 FBS for a small/medium project, 30–150 for a large one).

## Common mistakes

- **Treating an FBS as a ticket.** Tickets are atomic units of work for one person/day; an FBS is a coherent testable increment that may span multiple tickets. Don't pre-shred the FBS — leave that for the `dev-implementation` skill.
- **Allocating ACs to multiple FBS for "thoroughness".** Every AC belongs to one FBS. Double-allocation hides the real coverage gap.
- **Listing testable outcomes that aren't testable.** "Code is clean" is not a testable outcome. "GET /pages/:id returns 200 for an entitled user and 403 for an out-of-tenant user" is.
- **No strategy picked.** The ordering then looks random and reviewers can't predict where new work goes. Always set `generationStrategy`.
- **Skipping the dependency graph.** Two FBS that look independent in their summaries may share an entity definition; if you never draw the graph, you discover the dependency at integration time.
- **Sizing every FBS as "medium" without thinking.** Sizing drives parallelism estimates. Be honest — at least 20% of FBS in a real project will be `small`, and there is usually one `large` cluster around a core domain entity.
- **Generating a BS before the TAD is approved.** Without the architecture, FBS boundaries default to story boundaries, which is rarely the right slicing.
