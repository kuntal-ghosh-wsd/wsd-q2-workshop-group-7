# Client Documentation Hub — Product Requirements Document

**Status:** Draft
**Owner:** Kuntal Ghosh (kuntal.ghosh@wsd.com)
**Stakeholders:** WSD documentation owners, client success, security/compliance, AI platform team, client representatives
**Last updated:** 2026-06-03

> Derived from the upstream brief in `requirement.md` (root of repo, 2026-06-03).
> Target hosting: `docs.wsd.com`. MVP phasing reflected in requirement priorities
> (Phase 1 = must-have, Phase 2 = should-have, Phase 3 = out of scope).

---

## 1. Summary

Client Documentation Hub is a secure, AI-assisted client-facing documentation portal (`docs.wsd.com`) that automatically publishes approved Confluence pages to the right clients. Internal teams continue to author in Confluence as the single source of truth; the Hub mirrors approved, tagged pages in near real-time, enforces per-client access, keeps a version history, and uses AI to (a) screen content for sensitive data before publishing, (b) generate release notes and per-client change summaries, and (c) email clients when their documentation changes. The Hub replaces today's manual PDF export + email distribution and the unscalable guest-access pattern in Confluence.

## 2. Problem & Motivation

Today documentation lives in Confluence but reaches clients as PDFs. Every release the docs team exports new PDFs, emails them to a list of client contacts, and chases up which version each client is reading. Guest Confluence access and per-client Confluence spaces have been tried and do not scale (license cost, space sprawl, permission drift, no audit trail). Outcomes we see:

- Clients regularly raise support tickets against stale PDF versions.
- Doc owners spend hours per release on manual distribution and version chasing.
- Security cannot prove which client saw which version of a page at which time.
- "Source of truth" splits between Confluence (authoring) and the latest emailed PDF (consumption).

If unaddressed, this gets worse as the client base grows and as AI-generated content increases release cadence.

## 3. Goals & Non-Goals

**Goals**

- A client can self-serve the **current approved** version of their documentation at `docs.wsd.com` without contacting WSD support.
- Every release of an approved Confluence page reaches subscribed clients in **≤ 5 minutes** with zero manual PDF distribution.
- AI screening blocks any page containing secrets, internal URLs, Jira links, or other sensitive content from reaching a client portal.
- AI generates release notes, per-client change summaries, and notification emails that the docs team approves rather than writes from scratch.
- Confluence remains the single source of truth; nothing about authoring workflow changes for internal authors.
- Security can answer "which client saw which version of page X on date Y" from an audit log.

**Non-Goals**

- Replacing Confluence as the authoring tool.
- Two-way sync — the portal is read-only relative to Confluence; edits in the portal are not supported.
- A general public documentation site (open / unauthenticated).
- An in-portal AI chat assistant, advanced analytics, or per-client impact analysis (Phase 3, out of scope for this release).
- Migrating historical PDF archives into the portal's version history.

## 4. Target Users

- **Primary — Client End User:** an engineer, integrator, or operator at a WSD client company who needs to read product / API / integration documentation and be alerted to changes that affect them.
- **Primary — WSD Documentation Owner:** an internal product or technical writer who authors and tags pages in Confluence and approves them for publication.
- **Primary — WSD Release / Publishing Reviewer:** the person who reviews AI screening results and AI-generated release notes before they go live.
- **Secondary — Client Admin:** the contact at the client company who manages which of their team members can access their portal account.
- **Secondary — WSD Security / Compliance:** consumes audit logs to demonstrate access control and content review.

## 5. Success Metrics

- **≥ 95% reduction** in manual PDF distribution emails sent by the docs team within 90 days of launch.
- **Sync latency** from "page approved in Confluence" to "visible in client portal" — p95 **< 5 minutes**.
- **≥ 90%** of AI-screened pages clear review on first pass (no sensitive-content false negatives reaching publish; false-positive rate measured separately).
- **≥ 60%** of subscribed clients open at least one AI change-summary email per release cycle within 90 days.
- **Zero** unauthorized cross-client document accesses (target: maintained in security audit).
- Documentation-related support tickets attributable to "stale version" or "missing PDF" → **down ≥ 70%** in 90 days.

## 6. Requirements

> All IDs use the `REQ-` prefix to satisfy the RCF schema (`^REQ-\d{3,}$`).
> Functional REQs are numbered 001–055; non-functional / security NFRs are
> numbered 100–107. Downstream stories and the TAD must reference these IDs
> verbatim. The canonical machine-readable copy lives at
> `docs/specs/client-docs-hub/prd/PRD-001.json`.

### Theme: Confluence Sync & Publishing

- **REQ-001** *(must-have)* — The system shall sync Confluence pages to the portal selectively, driven by a configurable allow-list of Confluence labels / tags and source spaces, so that only intentionally-tagged pages are eligible for publication.
- **REQ-002** *(must-have)* — The system shall only publish pages that are in an "approved" state, determined by a configurable approval signal in Confluence (label, page status, or workflow state), and shall reject draft / in-review pages from publishing.
- **REQ-003** *(must-have)* — The system shall detect Confluence page changes and publish updates to the portal in near real-time, with p95 end-to-end latency under 5 minutes from approval to portal visibility.
- **REQ-004** *(must-have)* — The system shall maintain a version history for every published page, retaining at minimum the last 20 versions per page, each with its publish timestamp, source Confluence version ID, and the publisher's identity.
- **REQ-005** *(must-have)* — The system shall preserve Confluence page structure on publish: headings, lists, tables, code blocks, inline images, and internal cross-links between published pages.
- **REQ-006** *(should-have)* — The system shall allow a doc owner to manually re-trigger sync of an individual page or a tag set from an admin UI when an automatic sync is suspected to have been missed.
- **REQ-007** *(should-have)* — The system shall support unpublishing a page (removal from the portal) without deleting it from Confluence, with an audit-logged reason.

### Theme: Authentication & Access Control

- **REQ-010** *(must-have)* — The system shall require authenticated login for every portal page; no documentation content shall be reachable unauthenticated.
- **REQ-011** *(must-have)* — The system shall support a secure login flow with password + second factor (TOTP or email magic link), with industry-standard session handling (HTTP-only secure cookies, idempotent logout).
- **REQ-012** *(must-have)* — The system shall enforce per-client access scoping: a logged-in user belongs to one client, and the portal shall only render documents marked as shared or as scoped to that client.
- **REQ-013** *(must-have)* — The system shall support two document visibility scopes: "shared" (visible to all authenticated clients) and "client-specific" (visible only to the named client(s)), with scope set per Confluence page via a label or page property.
- **REQ-014** *(must-have)* — The system shall provide a client-admin role allowing a designated client contact to invite, disable, and remove users within their own client tenant without WSD intervention.
- **REQ-015** *(should-have)* — The system shall support SSO via SAML 2.0 / OIDC for client tenants that require enterprise login.
- **REQ-016** *(must-have)* — The system shall maintain an audit log of every authentication event, every document view, and every administrative action (invite, role change, scope change, unpublish), retained for at least 12 months.

### Theme: Client Portal (Browse, Read, Download)

- **REQ-020** *(must-have)* — The portal shall present a browsable navigation grouped by product and guide category, derived from the source Confluence label / page hierarchy.
- **REQ-021** *(must-have)* — The portal shall render the latest published version of a page as the default view, with the page's last-updated timestamp visible.
- **REQ-022** *(must-have)* — The portal shall expose a per-page version history view, allowing the user to read any previous published version and to diff it against the latest.
- **REQ-023** *(must-have)* — The portal shall provide a per-page "Download as PDF" action that generates a styled PDF of the currently-viewed version on demand.
- **REQ-024** *(must-have)* — The portal shall provide full-text search scoped to the documents the logged-in user is permitted to see, with results ranked by relevance and filterable by product.
- **REQ-025** *(should-have)* — The portal shall remember a per-user "last visited" timestamp per page so that the change-summary feature (REQ-042) can show "what's new since you last looked".

### Theme: Notifications

- **REQ-030** *(must-have)* — The system shall notify subscribed client users by email when documentation they are entitled to see has changed since the last digest, with a configurable digest cadence (immediate, daily, weekly).
- **REQ-031** *(must-have)* — Each notification email shall include a release-highlights summary and a deep link into the portal for each changed page.
- **REQ-032** *(should-have)* — Client users shall be able to manage their own notification preferences (cadence, per-product subscription) from a profile page.

### Theme: AI Document Review (pre-publish gate)

- **REQ-040** *(must-have)* — Before a page is published, the system shall run an AI document-review pass that flags: secrets / credentials / API keys, internal-only URLs, Jira / internal-ticket links, internal employee email addresses, and structurally missing content (e.g. empty sections, placeholders like "TODO" / "TBD" / "lorem ipsum").
- **REQ-041** *(must-have)* — A page that triggers any high-severity AI review finding (secrets, internal URLs, Jira links) shall be blocked from publishing until a reviewer either confirms a false positive or the page is corrected in Confluence and re-synced.
- **REQ-042** *(must-have)* — The AI review result shall be shown to the publishing reviewer with the matched span highlighted in context and a per-finding "ignore / acknowledge / block" action, with all decisions audit-logged.

### Theme: AI Release Notes & Change Summary

- **REQ-050** *(must-have)* — When a published page changes, the system shall generate AI-authored release notes for that page covering: What's New, Breaking Changes, and Recommended Actions; the docs team approves before clients see them.
- **REQ-051** *(must-have)* — On a client's portal landing page, the system shall show a per-client "Since your last visit" summary, AI-generated from the diff of pages they are entitled to see and have not yet viewed in the latest version.
- **REQ-052** *(should-have)* — The system shall let a reviewer regenerate, edit inline, or discard any AI-generated release-notes block before it is published.

### Theme: AI Client Notifications

- **REQ-053** *(must-have)* — Notification emails sent under REQ-030 shall use AI-generated concise summaries (e.g. "Store API updated. New inventory APIs added. No action required."), generated per client based on the changes they are entitled to see, and approved by a reviewer when changes are flagged as breaking.

### Theme: AI Documentation Quality Check

- **REQ-054** *(should-have)* — Before publish, the system shall score each page on Completeness, Readability, Missing Examples, and Missing API Responses, surfacing the scores to the doc owner; low scores produce warnings, not hard blocks.
- **REQ-055** *(nice-to-have)* — The system shall trend quality scores over time per page so doc owners can see documentation health regressing or improving.

### Theme: Non-Functional

- **REQ-100** *(must-have)* — Portal page render p95 **< 1.5 s** under expected client load (target: 500 concurrent authenticated users at launch).
- **REQ-101** *(must-have)* — Sync latency p95 from Confluence approval to portal visibility **< 5 minutes**; max **< 15 minutes** including AI review.
- **REQ-102** *(must-have)* — All client data in transit shall be TLS 1.2+; all authentication tokens, session cookies, and AI-pipeline payloads shall be encrypted at rest.
- **REQ-103** *(must-have)* — Per-client data isolation shall be enforced at the data-access layer; no portal endpoint may return content scoped to a client other than the requesting user's client, even under URL manipulation.
- **REQ-104** *(must-have)* — The portal shall meet WCAG 2.1 AA for all primary client-facing reading and navigation flows.
- **REQ-105** *(must-have)* — The AI document-review pipeline shall fail closed: if an AI provider is unavailable, pages remain unpublished and a reviewer is alerted; pages do not bypass screening.
- **REQ-106** *(should-have)* — The system shall support horizontal scaling of the portal read tier so capacity grows linearly with client headcount with no architectural change.
- **REQ-107** *(must-have)* — Audit logs (auth, view, admin actions, AI review decisions) shall be tamper-evident (append-only or signed) and retained ≥ 12 months.

## 7. Constraints & Assumptions

- Authoring continues in the existing WSD Confluence instance; no change to the writer workflow beyond adopting the documented label / approval conventions.
- Confluence REST API access (read + webhook / change-events subscription) is available to the sync service.
- An AI provider (Claude on Anthropic or via Bedrock; final choice in TAD) is available for review, release-notes, summary, and notification generation; provider keys are managed by platform.
- Email delivery is via an existing transactional email provider (e.g. SES / SendGrid); the Hub does not run its own MTA.
- The portal will be hosted under `docs.wsd.com` on existing WSD cloud infrastructure; deployment platform is a TAD-stage decision but is assumed to be the standard WSD container platform.
- Initial client onboarding is operator-driven (WSD provisions the tenant); client-admin self-service for end users is in scope, tenant-self-creation is not.

## 8. Out of Scope

- In-portal AI chat assistant ("ask the docs") — Phase 3.
- Per-client usage analytics dashboards and client-impact analysis — Phase 3.
- Authoring or editing documentation from inside the portal.
- Public (unauthenticated) documentation pages.
- Multilingual translation of documentation — single-language (English) for the first release.
- Mobile-native applications; the portal targets responsive web only.
- Migration of historical PDF artefacts into the portal's version history.
- Integration with non-Confluence content sources (Notion, Google Docs, GitHub markdown) for the first release.

## 9. Open Questions

- Final Confluence convention for the publish signal: dedicated label (e.g. `client-published`), Confluence page-status workflow, or a property macro — owner: docs lead, by PRD review.
- Whether "client-specific" scope is set by a page label naming the client (e.g. `client:acme`) or via a separate routing rule maintained outside Confluence — owner: docs lead + security, by PRD review.
- Choice of AI provider and whether AI calls go through an existing internal AI gateway or directly to the provider — owner: AI platform team, by TAD draft.
- Whether SSO (REQ-015) needs to be in v1 for any committed launch client, or can defer to a follow-up — owner: client success, by sprint 0.
- PDF generation: per-page on-demand only (REQ-023) vs. also offering a whole-product PDF bundle — owner: docs lead, by PRD review.
- Notification email "from" identity and DMARC alignment requirements — owner: security + marketing, by TAD.
