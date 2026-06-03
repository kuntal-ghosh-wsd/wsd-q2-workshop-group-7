# Stage 1 — Brief → PRD

A Product Requirements Document captures **what we are building and why**, in terms a non-engineer can review. It is the source of truth that all downstream artifacts (stories, ACs, TAD) trace back to.

## Contents
- [Inputs to gather](#inputs-to-gather)
- [Standard PRD structure](#standard-prd-structure)
- [Requirement format](#requirement-format)
- [Depth — how many requirements?](#depth--how-many-requirements)
- [Prioritization (MoSCoW)](#prioritization-moscow)
- [Drafting procedure](#drafting-procedure)
- [Quality bar](#quality-bar)
- [Common mistakes](#common-mistakes)

## Inputs to gather

Ask **only these** before drafting. Anything else, infer and confirm.

1. **Product / feature name.**
2. **Problem statement** — one or two sentences on who hurts and how. Push back if vague: "Users want a better dashboard" is not a problem statement; "Data analysts spend 30+ minutes daily exporting CSVs and pivoting in Excel because they can't filter live dashboards" is.
3. **Target users / personas** — roles, not headcounts.
4. **Constraints** — budget, deadline, must-integrate-with, compliance, platform restrictions. Optional but valuable.
5. **What's explicitly out of scope** (if the user has an opinion).

If the user provided a brief that already covers these, do not re-ask — confirm your understanding in one paragraph and proceed.

## Standard PRD structure

```
# <Product/Feature> — PRD

## 1. Summary
   - One-paragraph elevator pitch
   - Status (Draft / Review / Approved)
   - Owner / stakeholders

## 2. Problem & Motivation
   - Who, what hurts, how do we know, what happens if we don't fix it

## 3. Goals & Non-Goals
   - 3–5 goals (outcome-oriented, measurable)
   - Explicit non-goals (prevents scope creep)

## 4. Target Users
   - Primary persona(s), secondary persona(s), one-line description each

## 5. Success Metrics
   - 2–4 metrics with target values (e.g. "p95 dashboard load < 2s", "≥40% WAU adoption in 90 days")

## 6. Requirements
   - Grouped by theme (see Requirement format below)

## 7. Constraints & Assumptions
   - Tech, business, regulatory, dependencies

## 8. Out of Scope
   - Explicitly excluded — prevents future "but we said…"

## 9. Open Questions
   - Things that block sign-off
```

For a small/internal feature, sections 4, 5, 7 can be one-liners or collapsed. Never skip 2, 3, 6, 8.

## Requirement format

Each requirement is one line plus optional acceptance hint. Use a stable ID.

```
### Theme: Dashboards

- **REQ-001** *(must-have)* — Users can create a dashboard from a blank template and save it under a custom name.
- **REQ-002** *(must-have)* — Users can add line, bar, and number widgets, configured against any connected data source.
- **REQ-003** *(should-have)* — Users can duplicate an existing dashboard as a starting point.
- **REQ-004** *(nice-to-have)* — Users can pin a dashboard to a shared workspace homepage.
```

Each REQ should:
- Start with a user-visible behaviour or a system property (not an implementation choice).
- Be testable in principle (you can imagine an AC for it).
- Be atomic — one capability per REQ. Split compound REQs ("users can create AND share AND export…") into separate ones.

## Depth — how many requirements?

| Scope | Target count |
|---|---|
| Spike / POC / internal tool | 8–15 REQs |
| Standard product feature | 20–30 REQs |
| Enterprise / regulated / multi-team | 40–60 REQs |

Going deeper than the scope needs creates filler REQs that pollute the downstream stories and TAD. Match depth to stakes.

## Prioritization (MoSCoW)

Use **must-have / should-have / nice-to-have / won't-have**. Apply ruthlessly:

- **must-have** — feature does not ship without this. If the user says "everything is must-have", push back: "If you had to cut 30% to hit the deadline, what would go?"
- **should-have** — high value, can defer by a release.
- **nice-to-have** — incremental value, easy to cut.
- **won't-have** — explicitly out of scope for this release (goes in section 8).

A healthy PRD looks roughly 40% must / 35% should / 25% nice. If 80%+ is must-have, the PRD is dishonest about priorities.

## Drafting procedure

1. **Group the brief into 3–6 themes** (e.g. "Dashboards", "Data Sources", "Sharing", "Admin"). Confirm themes with the user before drafting REQs — wrong themes = wrong groupings = expensive rewrite later.
2. **Draft 4–10 REQs per theme**, biasing toward must-have for core capability, then filling in should/nice.
3. **Fill the surrounding sections** (problem, goals, metrics, etc.) from the brief.
4. **Mark open questions** explicitly — do not invent answers to fill gaps.
5. **Show the full PRD** to the user. Do not summarize — they need to see exactly what they're approving.

## Quality bar

Scan for these before showing the draft:

- [ ] Every must-have REQ has a one-line user-visible outcome (not an implementation noun).
- [ ] No REQ contains "and" joining two independent capabilities.
- [ ] Success metrics are measurable (numbers + timeframes), not aspirations.
- [ ] Non-goals are present and specific.
- [ ] At least one non-functional requirement (perf, security, accessibility, scale) per applicable concern.
- [ ] No `TBD` on must-have REQs — those are open questions; either resolve them or move the REQ to should-have until resolved.

## Common mistakes

- **Solutioning in REQs.** "Use Redis to cache dashboard config" is not a requirement; it's an implementation choice. The REQ is "Dashboard config loads in < 100ms on repeat view". Tech goes in the TAD.
- **Vague success criteria.** "Users love the dashboard" is not measurable. "≥40% of weekly actives create at least one dashboard in their first week" is.
- **Missing non-functional requirements.** PRDs that only cover features produce TADs that ignore latency, scale, accessibility. Add NFRs as their own theme: "Performance", "Security", "Accessibility".
- **Themes that map to teams instead of user value.** "Frontend", "Backend" are bad themes. "Authoring", "Sharing", "Admin" are good — they group requirements by user journey.
