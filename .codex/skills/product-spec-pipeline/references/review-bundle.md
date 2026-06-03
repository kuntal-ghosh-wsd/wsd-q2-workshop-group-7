# Stage R — Review Bundle (JSON + HTML viewer)

A **Review Bundle** packages the PRD requirements + their user stories + ACs into a single JSON file, paired with a self-contained HTML viewer. Stakeholders open the HTML in a browser, walk through every requirement, set Approved / Needs Changes / Rejected per requirement, and add structured notes at REQ, story, and AC level. All edits auto-save to the JSON file on disk via a PUT-capable local dev server.

This is an **optional output** of the pipeline, produced after Stage 3 (ACs) is complete. It does not replace the markdown artifacts — it derives from them.

## Contents
- [When to produce it](#when-to-produce-it)
- [What gets written](#what-gets-written)
- [JSON schema](#json-schema)
- [Building the JSON from PRD + Stories + ACs](#building-the-json-from-prd--stories--acs)
- [Filename convention (matched pair)](#filename-convention-matched-pair)
- [How the HTML viewer works](#how-the-html-viewer-works)
- [Serving the bundle (PUT-capable server)](#serving-the-bundle-put-capable-server)
- [Round-tripping reviewer notes back to markdown](#round-tripping-reviewer-notes-back-to-markdown)
- [Common mistakes](#common-mistakes)

## When to produce it

Produce the Review Bundle when **any** of these is true:

- The user asks for "a review document", "something stakeholders can click through", "a JSON for reviewers", or "the comparators-style review HTML".
- Stage 3 has completed (every must-have story has at least 2 testable ACs) and the project needs multi-stakeholder sign-off before Stage 4 (TAD).
- The user has the matching HTML viewer in the repo already (`*-requirements-review.html`) and asks to regenerate or update the JSON for it.

Do **not** produce it before Stage 3 — a review bundle without ACs is just a summary of titles, which adds noise instead of signal.

## What gets written

Two files in the same directory (typically the project root, or `docs/specs/<feature>/`):

| File | Source | Purpose |
|---|---|---|
| `<feature>-requirements-review.json` | Built from PRD + USER-STORIES (with ACs) | Reviewable data |
| `<feature>-requirements-review.html` | Copied verbatim from [assets/review-viewer.html](../assets/review-viewer.html) | Self-contained viewer |

The HTML is generic — it derives its own JSON filename from `location.pathname`. **Never rename the JSON without also renaming the HTML to the same basename**, or pairing breaks.

## JSON schema

See [assets/review-bundle-template.json](../assets/review-bundle-template.json) for a copy-pasteable starting point. Schema:

```
{
  "title": string,              // optional — defaults to a prettified filename
  "pages": [                    // each "page" is a theme from the PRD
    {
      "id": string,             // slug, used in DOM ids — must be unique
      "name": string,           // theme name
      "description": string,    // one-line theme description
      "icon": string,           // a single emoji
      "requirements": [
        {
          "id": "REQ-001",
          "title": string,
          "description": string,        // full requirement text from PRD bullet
          "priority": "must" | "should" | "nice",
          "domain": string,             // optional — subsystem / area
          "tags": string[],             // optional — free-form labels
          "stories": [
            {
              "id": "US-001",
              "title": string,
              "asA": string,            // role (the "As a X" part)
              "iWant": string,          // capability ("I want Y")
              "soThat": string,         // benefit ("so that Z")
              "acs": [
                {
                  "id": "AC-101",
                  "description": string  // full AC text, exactly as in markdown
                  // "note": optional — added by reviewers, do not pre-populate
                }
              ]
              // "note": optional — added by reviewers, do not pre-populate
            }
          ],
          "reviewStatus": "not-reviewed",  // initial value — reviewers change in UI
          "notes": ""                      // initial value — reviewers fill in UI
        }
      ]
    }
  ]
  // "_reviewMeta": automatically written by the viewer on save — do not generate
}
```

### Field-by-field rules

- **`priority`**: use the short forms `must` / `should` / `nice` (not the long `must-have` / `should-have` / `nice-to-have`). The viewer's CSS keys off these short values.
- **`reviewStatus`**: always seed with `"not-reviewed"`. The viewer cycles through `not-reviewed` → `approved` → `needs-changes` → `rejected`.
- **`notes`**, **`note`** (story and AC): seed as empty string `""` or omit entirely. Reviewers fill these in the UI.
- **`tags`**: optional. Useful for cross-cutting filters (e.g. `["frontend", "perf"]`). Keep to ≤ 4 per requirement.
- **`icon`**: a single emoji (no skin-tone modifiers). Pick something meaningful for the theme — `📋`, `🧩`, `⚙️`, `🏠`, `✏️`, `🔗`, etc.
- **`id` (page)**: lowercase, hyphen-separated slug. Must be unique across the bundle.
- **`id` (REQ/US/AC)**: must exactly match the IDs in `PRD.md` and `USER-STORIES.md` so reviewers can cross-reference.
- **`_reviewMeta`**: never include in the initial bundle. The HTML writes it automatically on first save.

## Building the JSON from PRD + Stories + ACs

The bundle is a **derived view**, not a separate source of truth. Build it programmatically; never hand-curate fields that already exist in markdown.

### Procedure

1. **Read `PRD.md` section 6.** Each theme becomes a `pages[]` entry. Each bullet `**REQ-XXX** *(priority)* — text` becomes a `requirements[]` entry with `title` (short summary, generated) and `description` (the bullet text).
2. **Read `USER-STORIES.md`.** For each `### US-XXX — <title>` block:
   - Parse `As a X, I want to Y, so that Z` into `asA`, `iWant`, `soThat`.
   - Follow `**Covers:** REQ-XXX` to attach the story to the right requirement.
   - Each `**AC-XXX** — <text>` bullet under the story becomes an `acs[]` entry.
3. **Group requirements into pages by theme.** The theme heading in the PRD = the page `name`. Slug the theme into the `id`. Add a one-line `description` (typically the first sentence of the theme in the PRD, or a generated summary).
4. **Pick an `icon` per page.** Match the user's domain. If unsure, default to `📋`.
5. **Seed reviewer fields**: `reviewStatus: "not-reviewed"`, `notes: ""`, no story/AC `note` keys.
6. **Validate**: every must-have REQ in the PRD appears in the JSON; every US/AC ID in the markdown appears under the right REQ.

### A note on `title`

`title` is a one-line summary, not a duplicate of `description`. If the PRD bullet is short ("Users can save a dashboard"), use it as the title; otherwise generate a 3–8 word summary from the description.

## Filename convention (matched pair)

The HTML auto-derives its sibling JSON filename. Both files must share the same basename:

```
<feature>-requirements-review.html
<feature>-requirements-review.json
```

Examples:
- `payments-requirements-review.html` + `payments-requirements-review.json`
- `comparators-requirements-review.html` + `comparators-requirements-review.json`

Drop them at the **repo root** (easiest for `pnpm dev`-style harnesses that serve from there) or inside `docs/specs/<feature>/` if the dev server's static root reaches that path. Same directory is mandatory.

## How the HTML viewer works

- On load: GETs the JSON via `fetch(JSON_FILENAME)`, parses, renders.
- On any edit (status change, note typed, status cycled): updates in-memory data → writes to `localStorage` immediately → debounced 1s → PUT to the JSON file via `fetch(JSON_FILENAME, { method: 'PUT', body: ... })`.
- On every PUT-save: a `_reviewMeta` object is added/updated with `lastSavedAt`, `lastSavedBy`, and progress counts.
- Conflict detection: before each PUT, the viewer re-fetches the JSON and compares hashes; if it changed externally (e.g. someone else committed a different version and the user pulled), it prompts the user to choose.
- Offline fallback: if PUT is unsupported (file:// or read-only server), the viewer still works — all edits persist to `localStorage` and the user can use **Export Copy** to download a snapshot.

The viewer is **self-contained** — no external JS/CSS, no build step. Drop it into any directory and serve.

## Serving the bundle (PUT-capable server)

The viewer needs a server that:
1. Serves the HTML and JSON via GET.
2. Accepts PUT on `*.json` and writes the body to disk.
3. Ideally responds 204 to OPTIONS so auto-connect works without prompting.

Most front-end dev harnesses (Vite plugins, custom Express middlewares, the project's own `pnpm dev`) can be configured for this in a few lines. If the user doesn't have one, suggest a minimal helper they can add — but do **not** invent and write one unless they ask.

If PUT is genuinely unavailable (static-file CDN, read-only mount), the bundle is still useful as a read-only summary; reviewers use **Export Copy** to download a per-session snapshot and share it.

## Round-tripping reviewer notes back to markdown

Reviewer notes live in the JSON. They are NOT a replacement for fixing the PRD / stories markdown — they are a **collection mechanism**. The expected flow:

1. Reviewers click through the HTML, set statuses, add notes.
2. JSON auto-saves to disk; reviewer commits and pushes.
3. The next pipeline pass reads the JSON, applies the notes (rewrite REQ description, split a story, add an AC, etc.) to `PRD.md` / `USER-STORIES.md` directly, then regenerates the JSON.
4. After regeneration, reset `reviewStatus` to `not-reviewed` only for requirements whose source changed materially — preserve approvals where the source is unchanged.

When regenerating the JSON, **preserve `notes`, story `note`, AC `note`, and `reviewStatus` from the prior JSON** wherever the ID still exists. Otherwise reviewers lose work on every regeneration.

## Common mistakes

- **Generating the bundle before ACs exist.** Reviewers can't validate testability without ACs. Wait for Stage 3 to finish.
- **Renaming JSON without renaming HTML.** Pairing breaks; viewer can't find the data. Rename both.
- **Hand-editing the JSON to add new requirements.** The JSON is derived. Add the REQ to `PRD.md` first, then regenerate the JSON. Hand-edits get clobbered on the next regen.
- **Using long-form priority values** (`must-have`, `should-have`). The viewer CSS expects the short forms (`must`, `should`, `nice`). Map down when serializing.
- **Including `_reviewMeta` in the initial bundle.** The viewer owns this field — generating it preempts the live counts.
- **Pre-populating `note` fields.** They are for reviewers, not authors. If authors have an annotation, it belongs in `description` or as a separate comment in the markdown.
- **Putting the HTML and JSON in different directories.** The viewer fetches relative to its own URL — they must be siblings.
- **Dropping fields the viewer expects** (like `priority` on a REQ, or `asA` on a story). The viewer renders defaults, but the result looks broken. Always include all required fields.
- **Generating a bundle for a one-off internal task.** Bundles are overkill if there's no stakeholder review loop. A markdown PRD is enough.
