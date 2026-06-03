---
name: product-spec-pipeline
description: >
  Produce the upstream product-spec artifacts for any software project, in
  order: a Product Requirements Document (PRD), User Stories with
  Acceptance Criteria, a Technical Architecture Document (TAD), and an
  Implementation Detail / Build Sequence (BS) that breaks the work into
  ordered, testable FBS units. Self-contained — emits two parallel
  artefacts per stage (a human-readable markdown document and a
  schema-validated JSON document) into a single feature folder under
  docs/specs/<feature>/, with the JSON schemas embedded as skill assets.
  No external MCP server, no SaaS, no schema registry is required.
  Use whenever the user wants to turn a brief, idea, problem statement, or
  raw requirement list into structured specs; draft a PRD from scratch;
  expand a PRD into stories; write or refine acceptance criteria; produce
  a TAD; or generate an implementation build sequence.
  Triggers on phrasing like "write a PRD", "draft user stories", "add
  acceptance criteria", "write the architecture doc", "spec this feature
  out", "turn this brief into requirements", "generate build sequence",
  "what's the implementation detail", "task list for this PRD".
  Provides per-artifact structure, quality bars, copy-pasteable markdown
  templates, and embedded JSON schemas (assets/schemas/*.schema.json).
---

# Product Spec Pipeline

A staged pipeline that turns an idea or brief into reviewable product specs. Each stage's output is the input to the next.

```
Idea / brief / raw requirements
        |
        v
  [1] PRD                       (what we're building and why)
        |
        v
  [2] User Stories              (how users experience it)
        |
        v
  [3] Acceptance Criteria       (when each story is "done")
        |
        v
  [4] Technical Architecture    (how it's built)
        |
        v
  [5] Implementation Detail     (ordered FBS task list — the build sequence)
        |
        v
  Implementation work (out of scope for this skill — see dev-implementation)
```

**Dual output per stage.** Each stage emits two parallel artefacts side-by-side in the **per-artifact subfolder** of the feature folder (one subfolder per stage: `prd/`, `user-stories/`, `tad/`, `build-sequence/`):

- A **markdown document** for humans to read and review.
- A **JSON document** validated against an embedded schema, for tooling and downstream stages.

The two must agree on IDs (PRD-/REQ-/US-/AC-/ADR-/TAD-/BS-/FBS-). The markdown is the readable mirror; the JSON is the canonical machine-readable copy.

**Self-contained.** This skill has no external dependencies — no MCP server, no hosted schema registry, no tracker integration. The four JSON schemas live in `assets/schemas/` and are loaded directly when validating output.

## When to use this skill

Trigger when the user wants to **produce or advance** any of the five artifacts:

| Signal phrase | Stage |
|---|---|
| "draft a PRD", "write requirements for X", "spec this out" | Stage 1 |
| "break this PRD into user stories", "write stories for ..." | Stage 2 |
| "add acceptance criteria", "write ACs for US-...", "make this testable" | Stage 3 |
| "write the architecture doc", "TAD for this", "design the system" | Stage 4 |
| "build sequence", "implementation detail", "FBS list", "task list for the PRD", "order the work" | Stage 5 |
| "go from this idea to an architecture", "full spec workflow" | Stages 1→5 |

Do **not** use this skill for already-written documents that just need editing for tone, length, or formatting — that's plain editing. Use this skill when the artifact is being **produced** or **expanded structurally**.

## Pre-flight (always run first)

1. **Find or choose the docs folder.** Look for an existing convention in this order, stop at first hit:
   - `docs/specs/`, `docs/product/`, `docs/`, `spec/`, `specs/`
   - Top-level `PRD.md` or `REQUIREMENTS.md` (suggests flat layout)
   - If nothing exists, **propose** `docs/specs/` and confirm with the user before creating.
2. **Decide layout.** This skill uses a **per-feature folder with per-artifact subfolders** — one subdirectory per pipeline stage. Each subfolder holds the markdown + JSON pair for that stage:
   ```
   docs/specs/<feature>/
   ├── prd/
   ├── user-stories/
   ├── tad/
   └── build-sequence/
   ```
   Confirm the `<feature>` slug with the user on the first call (e.g. `client-docs-hub`, `dashboards`). Use kebab-case. Create the four subfolders lazily — only when a stage actually writes its first artifact.
3. **Identify starting stage.** Check which artifacts already exist in the chosen folder:
   - No `prd/PRD-*.json` → start at Stage 1
   - `prd/PRD-*.json` exists, no `user-stories/*-user-stories.json` → Stage 2
   - User-stories exists but ACs thin → Stage 3
   - PRD + Stories exist, no `tad/TAD-*.json` → Stage 4
   - TAD exists, no `build-sequence/BS-*.json` → Stage 5
4. **Read existing upstream artifacts before writing downstream.** Re-read the JSON canonical copy (not the markdown) for downstream traceability; the JSON is the source-of-truth for IDs.
5. **Maintain the per-feature manifest.** On the first JSON write into a feature folder, create `docs/specs/<feature>/manifest.json` (single-PRD index). On every subsequent stage, append the new artifact's `id` and relative `path` to the matching array (`stories[]`, `tad[]`, `bs[]`) under the PRD entry. See [Manifest format](#manifest-format) below.

### Folder layout (per feature)

Everything for one feature lives under a single feature directory, but each pipeline stage gets its own subdirectory. No separate `rcf/` tree, no split between human and machine artifacts — both the markdown and JSON for a stage sit side-by-side inside that stage's subfolder.

```
docs/specs/<feature>/
├── manifest.json                              per-feature index (PRD entry + downstream paths)
├── prd/
│   ├── PRD.md                                 human-readable PRD
│   └── PRD-<NNN>.json                         canonical PRD JSON (validates against assets/schemas/prd.schema.json)
├── user-stories/
│   ├── USER-STORIES.md                        human-readable stories + ACs
│   └── PRD-<NNN>-user-stories.json            canonical stories JSON (validates against assets/schemas/user-stories.schema.json)
├── tad/
│   ├── TAD.md                                 human-readable TAD
│   ├── TAD-<NNN>-001.json                     TAD overview & principles
│   ├── TAD-<NNN>-002.json                     TAD components
│   ├── TAD-<NNN>-003.json                     TAD data & integration
│   └── TAD-<NNN>-004.json                     TAD security, deploy, ops, ADRs
└── build-sequence/
    ├── BUILD-SEQUENCE.md                      human-readable FBS task list
    └── BS-<NNN>.json                          canonical Build Sequence JSON (validates against assets/schemas/build-sequence.schema.json)
```

TADs may be a single `tad/TAD-<NNN>-001.json` for small features. **Split into up to 4 parts** for any PRD with > ~15 components, > ~25 ADRs, or > ~50 NFRs/integrations.

### Manifest format

`docs/specs/<feature>/manifest.json` is the per-feature index. One PRD per feature folder; the manifest exists so downstream tooling can discover artifacts without filename guessing.

```json
{
  "version": "1.0.0",
  "feature": "<feature-slug>",
  "description": "<one-line feature description>",
  "prd": {
    "id": "PRD-001",
    "name": "<product name>",
    "path": "prd/PRD-001.json",
    "markdownPath": "prd/PRD.md",
    "stories": [
      { "id": "STD-001", "path": "user-stories/PRD-001-user-stories.json", "markdownPath": "user-stories/USER-STORIES.md" }
    ],
    "tad": [
      { "id": "TAD-001-001", "name": "Overview & Principles", "path": "tad/TAD-001-001.json" },
      { "id": "TAD-001-002", "name": "Components", "path": "tad/TAD-001-002.json" },
      { "id": "TAD-001-003", "name": "Data & Integration", "path": "tad/TAD-001-003.json" },
      { "id": "TAD-001-004", "name": "Security, Deploy, Ops & ADRs", "path": "tad/TAD-001-004.json" }
    ],
    "tadMarkdownPath": "tad/TAD.md",
    "bs": [
      { "id": "BS-001", "path": "build-sequence/BS-001.json", "markdownPath": "build-sequence/BUILD-SEQUENCE.md" }
    ]
  }
}
```

Paths in the manifest are **relative to the feature folder**, not the repo root — every path begins with the stage subfolder (`prd/`, `user-stories/`, `tad/`, `build-sequence/`). This keeps the feature folder portable.

## Stage selector

Pick the matching stage and load only its reference file. Each reference has structure, quality bar, and worked examples.

| Stage | What it produces (markdown + JSON, both in the stage subfolder under `docs/specs/<feature>/`) | Reference to load | Markdown template | JSON schema |
|---|---|---|---|---|
| 1. Brief → PRD | `prd/PRD.md` + `prd/PRD-<NNN>.json` | [references/prd.md](references/prd.md) | [assets/prd-template.md](assets/prd-template.md) | [assets/schemas/prd.schema.json](assets/schemas/prd.schema.json) |
| 2. PRD → Stories | `user-stories/USER-STORIES.md` + `user-stories/PRD-<NNN>-user-stories.json` | [references/user-stories.md](references/user-stories.md) | [assets/user-stories-template.md](assets/user-stories-template.md) | [assets/schemas/user-stories.schema.json](assets/schemas/user-stories.schema.json) |
| 3. Stories → ACs | ACs added inside each story (both files in `user-stories/`) | [references/acceptance-criteria.md](references/acceptance-criteria.md) | (no separate file — edits the stories doc) | (extends the user-stories JSON; ACs go in `acceptanceCriteria[]`) |
| 4. PRD + Stories → TAD | `tad/TAD.md` + 1–4× `tad/TAD-<NNN>-<part>.json` | [references/tad.md](references/tad.md) | [assets/tad-template.md](assets/tad-template.md) | [assets/schemas/tad.schema.json](assets/schemas/tad.schema.json) |
| 5. Stories + ACs + TAD → Build Sequence | `build-sequence/BUILD-SEQUENCE.md` + `build-sequence/BS-<NNN>.json` | [references/build-sequence.md](references/build-sequence.md) | (embed in JSON template) | [assets/schemas/build-sequence.schema.json](assets/schemas/build-sequence.schema.json) + [assets/build-sequence-template.json](assets/build-sequence-template.json) |

**Load only the references the current request needs.** Do not load all five upfront.

### JSON-vs-markdown obligation

For every stage:

1. Write the **markdown** first (the human-review surface).
2. Immediately write the **JSON** mirror with the same content, validated against the schema in `assets/schemas/`.
3. Update `docs/specs/<feature>/manifest.json` with the new artifact's `id` and `path`.

Never ship only one of the two. If the user explicitly says "JSON only" or "markdown only", record that as a session preference but flag the absence of the other so it can be filled in later.

### Validating JSON before stopping

When emitting JSON for any stage, run the JSON through the matching schema before completing the turn. A minimal validation routine using Python `jsonschema` (or even just regex checks) is enough — the goal is to catch ID-pattern violations, enum mismatches, and missing required fields. The bare-minimum self-check the model should run inline:

- All ID strings match their regex (see [Identifier conventions](#identifier-conventions) below).
- All enum-valued fields (priority, category, status, riskLevel, generationStrategy, etc.) carry legal values.
- All required fields are present and non-empty.
- For Stage 5: every AC across every story is covered by exactly one FBS; `dependencies[]` forms a DAG.

## Identifier conventions

| Artifact | Prefix | Schema regex | Example |
|---|---|---|---|
| PRD | `PRD-` | `^PRD-\d{3,}$` | `PRD-001` |
| Requirement | `REQ-` | `^REQ-\d{3,}$` | `REQ-001` |
| User Story | `US-` | `^US-\d{3,}$` | `US-001` |
| Acceptance Criterion | `AC-` | `^AC-\d{3,}$` | `AC-101` |
| TAD Decision Record | `ADR-` | `^ADR-\d{3,}$` | `ADR-001` |
| TAD document | `TAD-` | `^TAD-\d{3,}(-\d{3,})?$` | `TAD-001-001` |
| Build Sequence document | `BS-` | `^BS-\d{3,}$` | `BS-001` |
| FBS (build unit inside a BS) | `FBS-` | `^FBS-\d{3,}$` | `FBS-001` |

**Schema constraint:** the JSON schemas reject `REQ-NFR-*` style sub-prefixes. If the markdown used them, renumber non-functional REQs into the plain `REQ-XXX` space (e.g. `REQ-100..199`) and keep markdown and JSON aligned. **Never** ship a JSON file whose IDs do not match the schema regex — it will fail validation.

**Priority enum mapping:** markdown commonly uses `must-have / should-have / nice-to-have`, but the PRD JSON schema's `priority` enum is `must / should / could / wont`. Map:

| Markdown | JSON |
|---|---|
| `must-have` | `must` |
| `should-have` | `should` |
| `nice-to-have` | `could` |
| `won't-have` (out of scope) | `wont` |

If the project already uses other prefixes for its markdown (e.g. `FR-`, `R-`, `STORY-`), match those for the markdown — but the JSON files must still satisfy the schema regexes, so introduce a mapping table at the top of the PRD if needed.

## How to drive each stage

Every stage uses the same loop. Match the level of user involvement to the artifact's stakes.

```
1. Gather inputs        → ask the user only what is essential (see per-stage reference)
2. Draft markdown       → write the markdown using the template, fill in real content
3. Present              → show the user the draft (full content, not just a summary)
4. Iterate              → take edits in natural language, revise the markdown
5. Mirror to JSON       → emit the JSON; reconcile IDs and enum values
6. Validate             → spot-check against the embedded schema (regex / enums / required fields)
7. Update manifest      → add the new artifact to docs/specs/<feature>/manifest.json
```

**Default to drafting first, then iterating.** Long upfront Q&A sessions stall the work. For PRD and TAD where stakes are higher, ask 3–5 essential questions before drafting; for stories, ACs, and the build sequence, draft directly from the upstream artifact.

### Tip: generator scripts for repetitive artefacts

User stories with ACs (Stage 2+3), TADs (Stage 4), and Build Sequences (Stage 5) all have substantial structural repetition between the markdown and JSON forms. A **one-shot Python generator** that authors the content as Python data structures and emits both forms is the standard pattern — it guarantees the two views stay byte-aligned and self-validates IDs and coverage before writing. Drop these into the project's `scripts/` folder; they're disposable but useful when iterating.

## Quality gates between stages

Do not advance to the next stage until the gate passes.

- **After Stage 1 (before Stage 2):** Every requirement has a priority (`must` / `should` / `could`) and a one-line user-visible outcome. No `TBD` priorities on must-haves. PRD JSON validates against `assets/schemas/prd.schema.json` (all required fields, IDs match regex, priority + category enum legal).
- **After Stage 2 (before Stage 4):** Every `must` requirement is covered by at least one user story. Grep the stories file for each REQ ID — if any must REQ is unreferenced, add a story before generating the TAD. User-stories JSON validates against `assets/schemas/user-stories.schema.json`.
- **After Stage 3 (before Stage 4):** Every story has at least 2 ACs. Each AC is testable (see the AC reference for the wording bar). Each AC has `testable: true` in the JSON.
- **After Stage 4 (before Stage 5):** Every non-functional requirement in the PRD is addressed in the TAD's NFR / operational / security section. Every ADR has `status`, `optionsConsidered[]`, `decision`, `rationale`, `consequences[]`. TAD JSON validates against `assets/schemas/tad.schema.json`.
- **After Stage 5:** Every story's ACs are covered by at least one FBS (no orphan ACs). The `dependencies` field across FBS forms a DAG (no cycles). Build-sequence JSON validates against `assets/schemas/build-sequence.schema.json`.

If a gate fails, fix the upstream artifact — do not paper over gaps in the downstream one.

## End-to-end happy path

For "go from this brief to a build sequence" requests, run all five stages in one pass, **but show the user each artifact (markdown view) before moving on** so they can request edits.

```
1. Pre-flight: confirm feature slug, init docs/specs/<feature>/manifest.json
2. Stage 1 → PRD.md → show → confirm or iterate → mirror to PRD-NNN.json → update manifest
3. Stage 2 → USER-STORIES.md → show → confirm or iterate → mirror to JSON → update manifest
4. Run coverage gate (every must REQ covered by a story)
5. Stage 3 → ACs → show → confirm or iterate → extend stories JSON
6. Stage 4 → TAD.md → show → confirm or iterate → mirror to TAD-NNN-XXX.json (1–4 parts) → update manifest
7. Stage 5 → BUILD-SEQUENCE.md → show → confirm or iterate → mirror to BS-NNN.json → update manifest
```

After Stage 5, hand off to the `dev-implementation` skill for slicing FBS units into commits and PRs.

## Common mistakes

- **Asking 20 questions upfront.** Drains user patience. Ask only the essentials per stage, draft, then iterate.
- **Skipping the upstream read.** Generating stories without re-reading the PRD produces stories that drift from the requirements.
- **Vague acceptance criteria** ("works correctly", "is fast"). Always include a measurable predicate. See the AC reference.
- **Writing a TAD without a stack.** Confirm tech stack before drafting Stage 4 — wrong stack means rewriting most of the doc.
- **Imposing new ID prefixes when the project already has one.** Check `docs/specs/` first.
- **Editing the artifact in place without preserving IDs.** Renumbering breaks every downstream reference.
- **Shipping JSON that fails the schema regex.** `REQ-NFR-001`, `REQ-1`, `req-001`, `must-have` — all rejected. Always run the JSON through the embedded schema before stopping.
- **Skipping the manifest update.** A new JSON file that isn't in `docs/specs/<feature>/manifest.json` is invisible to downstream tooling and future runs of this skill.
- **Putting JSON in a separate folder from markdown.** This skill keeps the markdown + JSON pair for each stage side-by-side inside the stage's subfolder (`prd/`, `user-stories/`, `tad/`, `build-sequence/`). Do not introduce a `docs/rcf/` or any other human-vs-machine split.
- **Splitting a TAD into 4 parts for a small feature.** Single-file TAD is fine until the schema-stretching limits kick in (>15 components, etc.).
- **Building a Stage 5 sequence without a TAD.** Stage 5 must reference architectural decisions and components, so it must read the TAD first.
- **FBS scope creep.** Each FBS should be one testable increment (target: small ≤ 3h, medium ≤ 8h, large ≤ 16h). If an FBS exceeds 16h estimated, split it.
- **Cyclic dependencies in the build sequence.** The `dependencies[]` field must form a DAG. Validate before stopping.
