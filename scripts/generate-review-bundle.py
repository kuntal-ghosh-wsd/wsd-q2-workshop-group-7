#!/usr/bin/env python3
"""
One-shot generator for the client-docs-hub review bundle.

Builds:
  - docs/specs/client-docs-hub/client-docs-hub-requirements-review.json
  - docs/specs/client-docs-hub/client-docs-hub-requirements-review.html

The JSON is derived from prd/PRD-001.json + user-stories/PRD-001-user-stories.json (no hand
curation). The HTML is the generic viewer copied verbatim from
~/.claude/skills/product-spec-pipeline/assets/review-viewer.html.

When re-running, preserves any reviewer-added `reviewStatus`, `notes`,
story `note`, and AC `note` fields wherever the ID still exists in the
new derivation. Resets `reviewStatus` to `not-reviewed` only for REQs
whose `description` materially changed (string-diff).
"""

from __future__ import annotations
import json
import shutil
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FEATURE = "client-docs-hub"
SPEC = REPO / "docs/specs" / FEATURE
SKILL_VIEWER = Path.home() / ".claude/skills/product-spec-pipeline/assets/review-viewer.html"

# ---------------------------------------------------------------------------
# Read upstream artifacts
# ---------------------------------------------------------------------------
prd = json.loads((SPEC / "prd" / "PRD-001.json").read_text())
stories_doc = json.loads((SPEC / "user-stories" / "PRD-001-user-stories.json").read_text())

stories_by_req: dict[str, list] = {}
for s in stories_doc["stories"]:
    stories_by_req.setdefault(s["reqId"], []).append(s)

# Map PRD priority enum (must/should/could/wont) → viewer short form (must/should/nice)
PRIORITY_MAP = {"must": "must", "should": "should", "could": "nice", "wont": "nice"}

# Theme icons per PRD domain (the skill says "pick something meaningful")
DOMAIN_ICON = {
    "Confluence Sync & Publishing": "🔄",
    "Authentication & Access Control": "🔐",
    "Client Portal": "🖥️",
    "Notifications": "📧",
    "AI Document Review": "🛡️",
    "AI Release Notes & Change Summary": "🧠",
    "AI Client Notifications": "📨",
    "AI Documentation Quality Check": "📊",
    "Performance": "⚡",
    "Data Protection": "🔒",
    "Accessibility": "♿",
    "Scalability": "📈",
    "Audit & Compliance": "📜",
}

# Short theme descriptions
DOMAIN_DESC = {
    "Confluence Sync & Publishing": "Allow-list sync, approval gating, version history, rendering, and unpublish",
    "Authentication & Access Control": "Login, MFA/SSO, per-tenant scoping, client-admin lifecycle, audit",
    "Client Portal": "Browse, read latest, version history, diff, PDF, search, last-visited",
    "Notifications": "Email digests, scoped delivery, self-service preferences",
    "AI Document Review": "Pre-publish AI screening for secrets, internal refs, missing content",
    "AI Release Notes & Change Summary": "AI-authored release notes and per-client since-last-visit summaries",
    "AI Client Notifications": "AI-generated concise per-client email summaries with reviewer gate",
    "AI Documentation Quality Check": "AI quality scoring on publish, trend per page",
    "Performance": "Render p95 SLA, sync latency SLA, observability",
    "Data Protection": "TLS in transit, KMS-managed encryption at rest",
    "Accessibility": "WCAG 2.1 AA for primary client flows",
    "Scalability": "Horizontal scaling of the read tier",
    "Audit & Compliance": "Tamper-evident audit log with ≥ 12-month retention",
}

# ---------------------------------------------------------------------------
# Preserve existing reviewer fields when regenerating
# ---------------------------------------------------------------------------
out_path = SPEC / f"{FEATURE}-requirements-review.json"
prior_review: dict[str, dict] = {}  # by REQ id
prior_desc: dict[str, str] = {}
prior_story_notes: dict[str, str] = {}  # by US id
prior_ac_notes: dict[str, str] = {}  # by AC id
if out_path.exists():
    try:
        prior = json.loads(out_path.read_text())
        for page in prior.get("pages", []):
            for r in page.get("requirements", []):
                prior_review[r["id"]] = {
                    "reviewStatus": r.get("reviewStatus", "not-reviewed"),
                    "notes": r.get("notes", ""),
                }
                prior_desc[r["id"]] = r.get("description", "")
                for s in r.get("stories", []):
                    if "note" in s:
                        prior_story_notes[s["id"]] = s["note"]
                    for a in s.get("acs", []):
                        if "note" in a:
                            prior_ac_notes[a["id"]] = a["note"]
    except Exception:
        pass  # any parse error → treat as no prior

# ---------------------------------------------------------------------------
# Build pages from PRD domains in PRD-declared order
# ---------------------------------------------------------------------------
pages_by_slug: dict[str, dict] = {}
domain_order: list[str] = []  # preserve PRD declaration order

def slug(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s or "untitled"

def short_title(req_text: str, fallback: str) -> str:
    # Title is a 3–8 word summary. Prefer the requirement's `title` field;
    # fall back to first 8 words of the description.
    if fallback:
        return fallback
    words = req_text.split()
    return " ".join(words[:8]) + ("…" if len(words) > 8 else "")

for r in prd["requirements"]:
    domain = r["domain"]
    if domain not in pages_by_slug:
        sl = slug(domain)
        pages_by_slug[domain] = {
            "id": sl,
            "name": domain,
            "description": DOMAIN_DESC.get(domain, ""),
            "icon": DOMAIN_ICON.get(domain, "📋"),
            "requirements": [],
        }
        domain_order.append(domain)

    stories_for_req = stories_by_req.get(r["id"], [])
    story_entries = []
    for s in stories_for_req:
        ac_entries = []
        for ac in s["acceptanceCriteria"]:
            entry = {"id": ac["id"], "description": ac["description"]}
            if ac["id"] in prior_ac_notes and prior_ac_notes[ac["id"]]:
                entry["note"] = prior_ac_notes[ac["id"]]
            ac_entries.append(entry)
        st = {
            "id": s["id"],
            "title": s["title"],
            "asA": s["asA"],
            "iWant": s["iWant"],
            "soThat": s["soThat"],
            "acs": ac_entries,
        }
        if s["id"] in prior_story_notes and prior_story_notes[s["id"]]:
            st["note"] = prior_story_notes[s["id"]]
        story_entries.append(st)

    # Preserve prior reviewStatus if description hasn't changed
    prior = prior_review.get(r["id"])
    if prior and prior_desc.get(r["id"]) == r["description"]:
        review_status = prior["reviewStatus"]
        notes = prior["notes"]
    else:
        review_status = "not-reviewed"
        notes = prior["notes"] if prior else ""

    req_entry = {
        "id": r["id"],
        "title": short_title(r["description"], r.get("title", "")),
        "description": r["description"],
        "priority": PRIORITY_MAP.get(r["priority"], "nice"),
        "domain": r["domain"],
        "tags": r.get("tags", [])[:4],
        "stories": story_entries,
        "reviewStatus": review_status,
        "notes": notes,
    }
    pages_by_slug[domain]["requirements"].append(req_entry)


# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------
must_req_ids = {r["id"] for r in prd["requirements"] if r["priority"] == "must"}
seen_req_ids = {r["id"] for page in pages_by_slug.values() for r in page["requirements"]}
missing = must_req_ids - seen_req_ids
if missing:
    raise SystemExit(f"must REQs missing from bundle: {sorted(missing)}")

all_us_ids = {s["id"] for s in stories_doc["stories"]}
bundle_us_ids = {st["id"] for page in pages_by_slug.values() for r in page["requirements"] for st in r["stories"]}
missing_us = all_us_ids - bundle_us_ids
if missing_us:
    raise SystemExit(f"US not in bundle: {sorted(missing_us)}")

# Page slugs must be unique
slugs = [page["id"] for page in pages_by_slug.values()]
if len(slugs) != len(set(slugs)):
    raise SystemExit(f"duplicate page slugs: {slugs}")


# ---------------------------------------------------------------------------
# Emit JSON (theme/page order matches PRD declaration order)
# ---------------------------------------------------------------------------
bundle = {
    "title": f"{prd['productName']} — Requirements Review",
    "pages": [pages_by_slug[d] for d in domain_order],
}
out_path.write_text(json.dumps(bundle, indent=2) + "\n")


# ---------------------------------------------------------------------------
# Copy the viewer HTML (rename to the matched basename)
# ---------------------------------------------------------------------------
viewer_dst = SPEC / f"{FEATURE}-requirements-review.html"
if not SKILL_VIEWER.exists():
    raise SystemExit(f"Skill viewer asset missing: {SKILL_VIEWER}")
shutil.copy(SKILL_VIEWER, viewer_dst)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
total_req = sum(len(p["requirements"]) for p in bundle["pages"])
total_us = sum(len(r["stories"]) for p in bundle["pages"] for r in p["requirements"])
total_ac = sum(len(a["acs"]) for p in bundle["pages"] for r in p["requirements"] for a in r["stories"])
preserved_status = sum(
    1 for p in bundle["pages"] for r in p["requirements"]
    if r["reviewStatus"] != "not-reviewed"
)

from collections import Counter
prio = Counter(r["priority"] for page in bundle["pages"] for r in page["requirements"])
print(f"Pages (themes):     {len(bundle['pages'])}")
print(f"Requirements:       {total_req}")
print(f"User stories:       {total_us}")
print(f"Acceptance criteria:{total_ac}")
print(f"Priority breakdown: {dict(prio)}")
print(f"Reviewer state preserved on rerun: {preserved_status} REQs carry a non-default status")
print()
print(f"Wrote: {out_path.relative_to(REPO)}")
print(f"Wrote: {viewer_dst.relative_to(REPO)}")
print()
print("To review: open the HTML in a browser (or via a PUT-capable dev server")
print("if you want auto-save back to the JSON file).")
