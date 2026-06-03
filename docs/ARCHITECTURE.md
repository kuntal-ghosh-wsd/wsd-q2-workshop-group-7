# Project architecture

This repo is a **product-spec pipeline**: an authoring system that turns a
plain-language brief into a stack of schema-validated specification artifacts
(PRD → User Stories → ACs → TAD → Build Sequence). The pipeline itself is
delivered as a Skill that is replicated across four agent harnesses
(`.claude`, `.codex`, `.cursor`, `.gemini`), backed by deterministic
generator scripts and JSON schemas, and writes its output into a per-feature
folder with per-stage subdirectories.

```mermaid
flowchart TB
  %% ─── Input ───────────────────────────────────────────────────
  brief["requirement.md<br/>(brief / raw requirements)"]:::input

  %% ─── Skill (replicated across 4 harnesses) ───────────────────
  subgraph SKILL["product-spec-pipeline Skill (distributed identically across 4 harnesses)"]
    direction LR
    claude[".claude/skills/<br/>product-spec-pipeline/"]:::skill
    codex[".codex/skills/<br/>product-spec-pipeline/"]:::skill
    cursor[".cursor/skills/<br/>product-spec-pipeline/"]:::skill
    gemini[".gemini/skills/<br/>product-spec-pipeline/"]:::skill

    subgraph SKILLBODY["Per-harness contents (identical)"]
      direction TB
      skillmd["SKILL.md<br/>(stage selector, quality gates, folder layout)"]
      refs["references/<br/>prd.md • user-stories.md • acceptance-criteria.md<br/>tad.md • build-sequence.md • review-bundle.md"]
      tmpl["assets/<br/>prd-template.md • user-stories-template.md<br/>tad-template.md • build-sequence-template.json<br/>review-bundle-template.json • review-viewer.html"]
      schemas["assets/schemas/<br/>prd.schema.json • user-stories.schema.json<br/>tad.schema.json • build-sequence.schema.json"]:::schema
    end
  end

  %% ─── 5-stage pipeline ────────────────────────────────────────
  subgraph PIPE["5-stage authoring pipeline"]
    direction TB
    s1["Stage 1 — PRD<br/>(what & why)"]:::stage
    s2["Stage 2 — User Stories<br/>(how users experience it)"]:::stage
    s3["Stage 3 — Acceptance Criteria<br/>(when it's done — extends Stage 2)"]:::stage
    s4["Stage 4 — TAD<br/>(how it's built)"]:::stage
    s5["Stage 5 — Build Sequence<br/>(ordered, testable FBS units)"]:::stage
    s1 --> s2 --> s3 --> s4 --> s5
  end

  %% ─── Generators ──────────────────────────────────────────────
  subgraph GEN["scripts/ — deterministic one-shot generators"]
    direction TB
    gus["generate-user-stories.py"]:::gen
    gtad["generate-tad.py"]:::gen
    gbs["generate-build-sequence.py"]:::gen
    grev["generate-review-bundle.py"]:::gen
  end

  %% ─── Output: per-feature folder ──────────────────────────────
  subgraph OUT["docs/specs/&lt;feature&gt;/ — per-feature output (current: client-docs-hub)"]
    direction TB
    manifest["manifest.json<br/>(index of every artifact's id + path)"]:::index

    subgraph PRDDIR["prd/"]
      prdmd["PRD.md"]:::md
      prdjson["PRD-NNN.json"]:::json
    end
    subgraph USDIR["user-stories/"]
      usmd["USER-STORIES.md"]:::md
      usjson["PRD-NNN-user-stories.json<br/>(stories + ACs)"]:::json
    end
    subgraph TADDIR["tad/"]
      tadmd["TAD.md"]:::md
      tadjson["TAD-NNN-001..004.json<br/>(1–4 parts)"]:::json
    end
    subgraph BSDIR["build-sequence/"]
      bsmd["BUILD-SEQUENCE.md"]:::md
      bsjson["BS-NNN.json<br/>(FBS DAG)"]:::json
    end

    review["client-docs-hub-requirements-review<br/>.html + .json (reviewer bundle)"]:::review
  end

  %% ─── Downstream hand-off ─────────────────────────────────────
  subgraph DOWN["Downstream skills (hand-off after Stage 5)"]
    direction LR
    dev["dev-implementation<br/>(slice FBS → commits & PRs)"]:::down
    test["test-author<br/>(ACs → executable tests)"]:::down
    qa["qa-reviewer<br/>(release-readiness review)"]:::down
  end

  %% ─── Wiring ──────────────────────────────────────────────────
  brief --> SKILL
  SKILL --> PIPE

  s1 -. validates against .-> schemas
  s2 -. validates against .-> schemas
  s4 -. validates against .-> schemas
  s5 -. validates against .-> schemas

  s2 --> gus
  s3 --> gus
  s4 --> gtad
  s5 --> gbs
  s1 --> grev
  s2 --> grev

  gus  --> USDIR
  gtad --> TADDIR
  gbs  --> BSDIR
  grev --> review

  s1 --> PRDDIR

  PRDDIR --> manifest
  USDIR  --> manifest
  TADDIR --> manifest
  BSDIR  --> manifest

  manifest --> DOWN
  bsjson   --> DOWN

  %% ─── Styling ─────────────────────────────────────────────────
  classDef input    fill:#fff4d6,stroke:#a37b00,color:#3a2a00
  classDef skill    fill:#e8f0ff,stroke:#3056a3,color:#10254e
  classDef stage    fill:#e9f7ec,stroke:#2f7a3a,color:#0e3b18
  classDef gen      fill:#f3e8ff,stroke:#6a3aa8,color:#2a0e4a
  classDef schema   fill:#ffe6e6,stroke:#a33030,color:#4a0e0e
  classDef md       fill:#f5f5f5,stroke:#666,color:#222
  classDef json     fill:#fffdf0,stroke:#a08a30,color:#3a2f0e
  classDef index    fill:#ffe8d6,stroke:#a35a00,color:#3a1d00
  classDef review   fill:#e0f7fa,stroke:#2a7d8c,color:#0e3a44
  classDef down     fill:#f0f0f0,stroke:#444,color:#111
```

## How to read it

- **Yellow** — input brief.
- **Blue** — the Skill itself: prompt knowledge (SKILL.md + references),
  templates, and schemas. Replicated identically across the four harness
  directories so the same authoring behavior runs under Claude Code,
  Codex, Cursor, and Gemini.
- **Green** — the five authoring stages. Stage 3 (Acceptance Criteria)
  extends Stage 2's output in place rather than producing a new file.
- **Purple** — Python generators in `scripts/`. They author content as
  Python data structures, validate against the schemas, then emit both
  the markdown and the JSON mirrors so the two views stay byte-aligned.
- **Red** — JSON schemas. Every generated JSON document is validated
  against the matching schema before the stage is considered complete.
- **Cream / grey** — the per-feature output folder, with per-stage
  subdirectories (`prd/`, `user-stories/`, `tad/`, `build-sequence/`).
  Each stage folder holds the markdown + JSON pair side-by-side.
- **Orange** — `manifest.json`, the per-feature index that downstream
  tooling reads to discover every artifact without filename guessing.
- **Teal** — the reviewer bundle (an HTML viewer + JSON state) derived
  from the PRD and User Stories so non-technical reviewers can mark
  REQs and ACs as reviewed without touching the source artifacts.
- **Grey (right)** — the downstream skills the pipeline hands off to
  after Stage 5: `dev-implementation` (implementation slicing),
  `test-author` (writing the executable tests for each AC), and
  `qa-reviewer` (release-readiness review).

## Key invariants

1. **Dual output per stage.** Every stage emits both markdown (for human
   review) and JSON (for tooling). Neither is shipped without the other.
2. **JSON is canonical.** When the two diverge, the JSON wins —
   downstream stages always read the JSON, never the markdown.
3. **Schema-gated.** No JSON file leaves a stage until it validates
   against `assets/schemas/<stage>.schema.json`.
4. **One feature folder, per-stage subdirectories.** All artifacts for
   a feature live under `docs/specs/<feature>/`, split into `prd/`,
   `user-stories/`, `tad/`, and `build-sequence/` subfolders. The
   manifest is the only file at the feature-folder root (alongside the
   reviewer bundle).
5. **Identifier conventions.** IDs follow strict regexes
   (`PRD-NNN`, `REQ-NNN`, `US-NNN`, `AC-NNN`, `ADR-NNN`, `TAD-NNN-NNN`,
   `BS-NNN`, `FBS-NNN`) so cross-references between stages are stable.
6. **Build Sequence is a DAG.** Every `FBS` covers ≥ 1 AC, every AC is
   covered by exactly one FBS, and `dependencies[]` between FBS units
   form a directed acyclic graph.
