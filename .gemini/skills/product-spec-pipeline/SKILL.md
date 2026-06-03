---
name: product-spec-pipeline
description: >
  Produce the four upstream product-spec artifacts for any software project,
  in order: a Product Requirements Document (PRD), User Stories, Acceptance
  Criteria, and a Technical Architecture Document (TAD). Tool- and
  framework-agnostic — writes plain markdown into whatever folder the
  project uses for docs, no SaaS, no MCP server, no schema lock-in.
  Use whenever the user wants to turn a brief, idea, problem statement, or
  raw requirement list into structured specs; draft a PRD from scratch;
  expand a PRD into stories; write or refine acceptance criteria; or
  produce a TAD. Triggers on phrasing like "write a PRD", "draft user
  stories", "add acceptance criteria", "write the architecture doc",
  "spec this feature out", "turn this brief into requirements".
  Provides per-artifact structure, quality bars, and copy-pasteable
  markdown templates. Optionally produces a "Review Bundle" — a JSON file
  plus a self-contained HTML viewer — so stakeholders can click through
  requirements, set approval status, and add notes with auto-save to disk.
  Triggers on phrasing like "build a review bundle", "stakeholder review
  HTML", or "comparators-style review viewer".
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
        +-- [R] Review Bundle   (optional: JSON + HTML viewer for stakeholder sign-off)
        |
        v
  [4] Technical Architecture    (how it's built)
```

**Tool-agnostic.** This skill produces plain markdown files. It does not assume any tracker (Jira, Linear, GitHub Issues), spec framework (RCF, BDD, etc.), or hosted service. The user picks where the files live; the skill writes them.

## When to use this skill

Trigger when the user wants to **produce or advance** any of the four artifacts:

| Signal phrase | Stage |
|---|---|
| "draft a PRD", "write requirements for X", "spec this out" | Stage 1 |
| "break this PRD into user stories", "write stories for ..." | Stage 2 |
| "add acceptance criteria", "write ACs for US-...", "make this testable" | Stage 3 |
| "write the architecture doc", "TAD for this", "design the system" | Stage 4 |
| "build a review bundle", "review JSON", "stakeholder review HTML", "comparators-style review viewer" | Stage R |
| "go from this idea to an architecture", "full spec workflow" | Stages 1→4 |

Do **not** use this skill for already-written documents that just need editing for tone, length, or formatting — that's plain editing. Use this skill when the artifact is being **produced** or **expanded structurally**.

## Pre-flight (always run first)

1. **Find or choose the docs folder.** Look for an existing convention in this order, stop at first hit:
   - `docs/specs/`, `docs/product/`, `docs/`, `spec/`, `specs/`
   - Top-level `PRD.md` or `REQUIREMENTS.md` (suggests flat layout)
   - If nothing exists, **propose** `docs/specs/` and confirm with the user before creating.
2. **Decide layout.** For a single-feature project, flat files are fine (`PRD.md`, `USER-STORIES.md`, `TAD.md`). For a multi-feature project, use a per-feature folder (`docs/specs/<feature>/PRD.md`, etc.). Ask if unclear.
3. **Identify starting stage.** Check which artifacts already exist in the chosen folder:
   - No PRD → start at Stage 1
   - PRD exists, no stories → Stage 2
   - Stories exist but ACs thin → Stage 3
   - PRD + Stories exist, no TAD → Stage 4
4. **Read existing upstream artifacts before writing downstream.** A TAD that ignores the PRD is worthless; a story set that ignores the PRD drifts.

## Stage selector

Pick the matching stage and load only its reference file. Each reference has structure, quality bar, and worked examples.

| Stage | What it produces | Reference to load | Template to stamp out |
|---|---|---|---|
| 1. Brief → PRD | `PRD.md` with prioritized requirements (REQ-XXX) | [references/prd.md](references/prd.md) | [assets/prd-template.md](assets/prd-template.md) |
| 2. PRD → Stories | `USER-STORIES.md` with US-XXX items | [references/user-stories.md](references/user-stories.md) | [assets/user-stories-template.md](assets/user-stories-template.md) |
| 3. Stories → ACs | ACs added inside each story | [references/acceptance-criteria.md](references/acceptance-criteria.md) | (no separate file — edits the stories doc) |
| 4. PRD + Stories → TAD | `TAD.md` with components, data, NFRs, etc. | [references/tad.md](references/tad.md) | [assets/tad-template.md](assets/tad-template.md) |
| R. (Optional) PRD + Stories + ACs → Review Bundle | `<feature>-requirements-review.json` + matching `.html` viewer for stakeholder click-through | [references/review-bundle.md](references/review-bundle.md) | [assets/review-bundle-template.json](assets/review-bundle-template.json) + [assets/review-viewer.html](assets/review-viewer.html) |

**Load only the references the current request needs.** Do not load all four upfront.

## Identifier conventions (use unless the project already has its own)

| Artifact | Prefix | Example |
|---|---|---|
| Requirement | `REQ-` | `REQ-001` |
| User Story | `US-` | `US-001` |
| Acceptance Criterion | `AC-` | `AC-101` (`AC-<story-number><sequence>`) |
| TAD Decision Record | `ADR-` | `ADR-001` |

If the project already uses other prefixes (e.g. `FR-`, `R-`, `STORY-`), match those — do not impose new ones. Grep the existing docs folder before assuming.

## How to drive each stage

Every stage uses the same loop. Match the level of user involvement to the artifact's stakes.

```
1. Gather inputs        → ask the user only what is essential (see per-stage reference)
2. Draft                → write the markdown using the template, fill in real content
3. Present              → show the user the draft (full content, not just a summary)
4. Iterate              → take edits in natural language, revise the draft
5. Commit when approved → save the file and stop
```

**Default to drafting first, then iterating.** Long upfront Q&A sessions stall the work. For PRD and TAD where stakes are higher, ask 3–5 essential questions before drafting; for stories and ACs, draft directly from the upstream artifact.

## Quality gates between stages

Do not advance to the next stage until the gate passes.

- **After Stage 1 (before Stage 2):** Every requirement has a priority (`must-have` / `should-have` / `nice-to-have`) and a one-line success criterion. No `TBD` priorities on must-haves.
- **After Stage 2 (before Stage 4):** Every `must-have` requirement is covered by at least one user story. Grep `USER-STORIES.md` for each REQ ID — if any must-have REQ is unreferenced, add a story before generating the TAD.
- **After Stage 3 (before Stage 4):** Every story has at least 2 ACs. Each AC is testable (see the AC reference for the wording bar).
- **After Stage 4:** Every non-functional requirement in the PRD is addressed in the TAD's NFR section.

If a gate fails, fix the upstream artifact — do not paper over gaps in the downstream one.

## End-to-end happy path

For "go from this brief to an architecture" requests, run all four stages in one pass, **but show the user each artifact before moving on** so they can request edits.

```
1. Pre-flight: locate docs folder, decide layout
2. Stage 1 → PRD → show → confirm or iterate
3. Stage 2 → Stories → show → confirm or iterate
4. Run coverage gate (every must-have REQ covered by a story)
5. Stage 3 → ACs → show → confirm or iterate
6. Stage 4 → TAD → show → confirm or iterate
```

## Common mistakes

- **Asking 20 questions upfront.** Drains user patience. Ask only the essentials per stage, draft, then iterate.
- **Skipping the upstream read.** Generating stories without re-reading the PRD produces stories that drift from the requirements.
- **Vague acceptance criteria** ("works correctly", "is fast"). Always include a measurable predicate. See the AC reference.
- **Writing a TAD without a stack.** Confirm tech stack before drafting Stage 4 — wrong stack means rewriting most of the doc.
- **Imposing new ID prefixes when the project already has one.** Check `docs/` first.
- **Editing the artifact in place without preserving IDs.** Renumbering breaks every downstream reference.
