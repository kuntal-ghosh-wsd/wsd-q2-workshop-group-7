# Client Documentation Hub — Build Sequence

> Generated from `docs/specs/client-docs-hub/prd/PRD-001.json` v1.0.0, `docs/specs/client-docs-hub/user-stories/PRD-001-user-stories.json` v1.0.0, and `docs/specs/client-docs-hub/tad/TAD-001-001..004.json` v1.0.0.
> Canonical: `docs/specs/client-docs-hub/build-sequence/BS-001.json`. Strategy: dependency-first. 39 FBS covering 192 ACs across 64 stories. Total estimate: 227 hours.

## Coverage & DAG validation

- Every AC across every story is allocated to exactly one FBS (192/192 ACs).
- Every `dependencies[]` entry points to an earlier-numbered FBS (DAG).
- No FBS exceeds the 16 h hard cap; every FBS has 3–8 testable outcomes.

## At-a-glance table

| FBS | Title | Domain | Size | Hours | Risk | Deps |
|---|---|---|---|---|---|---|
| FBS-001 | Platform foundation, tenant data model, and Postgres Row-Level Security | Foundation | medium | 8 | high | — |
| FBS-002 | Auth Service — password + TOTP login, session lifecycle | Authentication & Access Control | medium | 8 | high | FBS-001 |
| FBS-003 | Auth — brute-force lockout and IP throttling | Authentication & Access Control | small | 3 | medium | FBS-002 |
| FBS-004 | Audit Service on QLDB + auth-event audit + tamper-evident retention | Audit & Compliance | medium | 6 | high | FBS-001, FBS-002 |
| FBS-005 | Document & DocumentVersion model with S3 immutable blobs | Confluence Sync & Publishing | medium | 8 | high | FBS-001 |
| FBS-006 | Document scoping — shared vs client-specific visibility | Authentication & Access Control | small | 4 | high | FBS-005, FBS-001 |
| FBS-007 | Renderer — Confluence storage format to portable HTML with cross-link rewriting | Confluence Sync & Publishing | medium | 8 | medium | FBS-005 |
| FBS-008 | Confluence allow-list management (admin) + sync filter | Confluence Sync & Publishing | small | 4 | medium | FBS-001 |
| FBS-009 | Sync Service — Confluence webhook receiver + HMAC verification + dedup | Confluence Sync & Publishing | medium | 6 | medium | FBS-008 |
| FBS-010 | Sync Service — polling fallback with cursor | Confluence Sync & Publishing | small | 4 | medium | FBS-009 |
| FBS-011 | AI Gateway — Bedrock integration, circuit breaker, fail-closed | AI Document Review | medium | 8 | high | FBS-001 |
| FBS-012 | AI Document Review — secrets and credentials detection | AI Document Review | medium | 6 | high | FBS-011 |
| FBS-013 | AI Document Review — internal URLs, Jira links, internal emails | AI Document Review | small | 4 | medium | FBS-011 |
| FBS-014 | AI Document Review — missing content (placeholders, empty sections, stubs) | AI Document Review | small | 4 | low | FBS-011 |
| FBS-015 | Approval-state gating | Confluence Sync & Publishing | small | 4 | medium | FBS-009 |
| FBS-016 | Publishing Pipeline orchestration (Step Functions) | Confluence Sync & Publishing | large | 12 | high | FBS-005, FBS-007, FBS-009, FBS-010, FBS-012, FBS-013, FBS-014, FBS-015, FBS-004 |
| FBS-017 | Hard publish block on high-severity AI findings | AI Document Review | small | 4 | high | FBS-016, FBS-012, FBS-013 |
| FBS-018 | Reviewer UI — AI findings in context + triage actions | AI Document Review | medium | 8 | medium | FBS-017, FBS-002 |
| FBS-019 | Admin — manual sync re-trigger and unpublish | Confluence Sync & Publishing | small | 4 | low | FBS-016 |
| FBS-020 | Portal Frontend — browse by product/category + latest version view | Client Portal | medium | 8 | medium | FBS-006, FBS-007, FBS-002 |
| FBS-021 | Portal — version history view + block-level diff | Client Portal | medium | 6 | medium | FBS-020, FBS-005 |
| FBS-022 | Search — OpenSearch indexing + scoped query gateway | Client Portal | medium | 8 | high | FBS-016, FBS-006 |
| FBS-023 | PDF download (on-demand render with 30-day cache) | Client Portal | medium | 6 | low | FBS-020, FBS-007 |
| FBS-024 | Per-user last-visited tracking | Client Portal | small | 3 | low | FBS-020 |
| FBS-025 | AI release notes — generate, reviewer approve, regenerate/edit/discard | AI Release Notes & Change Summary | medium | 8 | medium | FBS-011, FBS-018 |
| FBS-026 | AI 'Since your last visit' summary on landing page | AI Release Notes & Change Summary | small | 4 | medium | FBS-011, FBS-024 |
| FBS-027 | Notification Service — digest scheduling, scope-respecting assembly | Notifications | medium | 8 | medium | FBS-016, FBS-006 |
| FBS-028 | AI notification summaries + breaking-change reviewer approval | AI Client Notifications | medium | 6 | medium | FBS-027, FBS-011, FBS-025 |
| FBS-029 | Notification email — release highlights + deep links | Notifications | small | 3 | low | FBS-027, FBS-028 |
| FBS-030 | Self-service notification preferences | Notifications | small | 3 | low | FBS-020, FBS-027 |
| FBS-031 | AI documentation quality scoring + soft warning override | AI Documentation Quality Check | medium | 6 | low | FBS-011, FBS-016 |
| FBS-032 | AI quality trend view | AI Documentation Quality Check | small | 3 | low | FBS-031 |
| FBS-033 | Client-admin user lifecycle (invite / disable / remove) | Authentication & Access Control | medium | 8 | medium | FBS-002, FBS-004 |
| FBS-034 | Document view audit + admin action audit coverage | Audit & Compliance | small | 4 | low | FBS-004, FBS-020, FBS-019 |
| FBS-035 | Enterprise SSO via WorkOS | Authentication & Access Control | medium | 6 | medium | FBS-002 |
| FBS-036 | End-to-end sync + publish observability hardening (SLA dashboards) | Performance | small | 4 | low | FBS-016 |
| FBS-037 | Portal render p95 SLA + horizontal scaling validation | Performance | medium | 6 | medium | FBS-020 |
| FBS-038 | TLS enforcement + at-rest encryption hardening | Data Protection | medium | 6 | medium | FBS-001 |
| FBS-039 | Accessibility — keyboard navigation, focus trapping, screen reader, contrast | Accessibility | medium | 8 | medium | FBS-020, FBS-021, FBS-023 |

## FBS details

### FBS-001 — Platform foundation, tenant data model, and Postgres Row-Level Security

**Domain.** Foundation  
**Size.** medium (8 h)  
**Risk.** high  
**Dependencies.** none

Stand up the AWS baseline (per-env account, VPC, subnets, KMS, IAM, ECR, ALB, Aurora PostgreSQL Serverless v2). Introduce the Tenant and User core entities and the tenant-bound connection wrapper. Wire Postgres RLS policies on every tenant-scoped table; expose the lint/CI checks that fail builds touching tenant tables without the wrapper.

**Scope (story → ACs):**
- `US-018` → AC-052, AC-053, AC-054
- `US-059` → AC-175, AC-176, AC-177

**Testable outcomes:**
- A tenant-bound DB connection sets app.tenant_id at session start; queries without it are blocked by RLS.
- Every tenant-scoped read or write rejects requests where the session tenant does not match the row's tenant_id.
- Cross-tenant CI isolation test runs and passes for the seed read endpoints.
- An attempt to add a new read endpoint without tenant scoping fails the build via a lint rule.
- CDK app provisions the per-env account baseline with KMS keys and S3 default-encryption configured.

**Deliverables:**
- CDK stacks for VPC, KMS, IAM baseline, Aurora cluster, ALB
- tenant-bound DB connection helper (Node.js + TypeScript)
- Postgres RLS policies for all v1 tables
- ESLint rule + CI check rejecting unscoped queries
- Seed cross-tenant isolation test suite

**Context required:**
- prdSections: Authentication & Access Control, Data Protection
- tadSections: Architecture Principles, Components: Portal API, Data architecture, ADR-002
- schemas: Tenant, User

### FBS-002 — Auth Service — password + TOTP login, session lifecycle

**Domain.** Authentication & Access Control  
**Size.** medium (8 h)  
**Risk.** high  
**Dependencies.** FBS-001

Implement the primary login flow: password (Argon2id) plus TOTP, session creation in Postgres + Redis with HttpOnly/Secure/SameSite cookies, idle timeout, idempotent logout, and the unauthenticated-redirect middleware.

**Scope (story → ACs):**
- `US-014` → AC-040, AC-041, AC-042
- `US-015` → AC-043, AC-044, AC-045
- `US-016` → AC-046, AC-047, AC-048

**Testable outcomes:**
- POST /auth/login succeeds with valid password + TOTP, establishes a session, and sets a Secure HttpOnly SameSite=Strict cookie.
- Unauthenticated requests to any portal route are redirected to /login with a signed redirect-back parameter.
- Idle-timeout exceeded sessions are invalidated server-side on next request.
- POST /auth/logout is idempotent: repeated calls do not error.
- TOTP secrets are encrypted with a KMS-bound DEK and never logged.

**Deliverables:**
- services/auth (Fargate, Node.js + Fastify) with login, logout, session middleware
- Argon2id password hashing utilities
- TOTP enrolment + verification module
- Redis-backed session store with Postgres mirror

**Context required:**
- prdSections: Authentication & Access Control
- tadSections: Components: Auth Service, Security architecture: authentication

### FBS-003 — Auth — brute-force lockout and IP throttling

**Domain.** Authentication & Access Control  
**Size.** small (3 h)  
**Risk.** medium  
**Dependencies.** FBS-002

Rate-limit login attempts per user (5/10 min → 15-min lockout) and per source IP. Generate the lockout-notification email path. Surface metrics for security.

**Scope (story → ACs):**
- `US-017` → AC-049, AC-050, AC-051

**Testable outcomes:**
- 5 failed logins for one user within 10 minutes triggers a 15-minute lockout and an email notification.
- Per-IP throttling kicks in at the configured threshold and returns 429 cleanly.
- auth.lockouts_total metric increments on every lockout and feeds the security alert channel.

**Deliverables:**
- Redis-backed counter store for per-user and per-IP attempts
- Lockout-notification email template + SES send path
- Security alert rule for sustained lockout rate

**Context required:**
- prdSections: Authentication & Access Control
- tadSections: Security controls: brute-force lockout

### FBS-004 — Audit Service on QLDB + auth-event audit + tamper-evident retention

**Domain.** Audit & Compliance  
**Size.** medium (6 h)  
**Risk.** high  
**Dependencies.** FBS-001, FBS-002

Stand up the Audit Service, the QLDB ledger, and the EventBridge audit-event consumer. Add the daily QLDB digest integrity job. Wire the first audit producer (Auth Service) so authentication outcomes flow into the ledger.

**Scope (story → ACs):**
- `US-025` → AC-073, AC-074, AC-075
- `US-064` → AC-190, AC-191, AC-192

**Testable outcomes:**
- Every login attempt (success / failure / lockout) writes a typed audit entry to QLDB within 5 seconds.
- Daily QLDB digest verification runs on schedule and emits a signed report; mismatch pages security.
- An attempt to alter an existing audit row is rejected at write time and the rejection itself is logged.
- Audit query API returns events filtered by user / tenant / IP / date range within 5 s p95 for the last 90 days.

**Deliverables:**
- services/audit (Fargate)
- QLDB ledger + journal verification job (EventBridge schedule)
- EventBridge audit-event consumer
- Audit query API with role-restricted access

**Context required:**
- prdSections: Authentication & Access Control, Non-Functional
- tadSections: Components: Audit Log Service, ADR-003

### FBS-005 — Document & DocumentVersion model with S3 immutable blobs

**Domain.** Confluence Sync & Publishing  
**Size.** medium (8 h)  
**Risk.** high  
**Dependencies.** FBS-001

Define Document, DocumentVersion, and the S3-with-Object-Lock content blob pattern. Implement the version-persist CAS (idempotent under retry). Persist publisher identity and source Confluence revision.

**Scope (story → ACs):**
- `US-008` → AC-022, AC-023, AC-024
- `US-009` → AC-025, AC-026, AC-027

**Testable outcomes:**
- A publish commit writes the rendered HTML blob to S3 (immutable, object-lock) and the metadata row to Postgres atomically.
- Two-times-in-a-row CAS-write with the same (document_id, source_version_id) is a no-op on the second write.
- Retiring the 21st version preserves its metadata + audit entry; the blob is GC'd from hot storage only after retention window.
- An attempt to overwrite an existing version blob is rejected by S3 Object Lock and the attempt is audit-logged.
- Version-history API returns publish timestamp, source version, and publisher identity for each retained version.

**Deliverables:**
- Document + DocumentVersion migrations
- S3 content-blob writer with Object Lock + KMS
- CAS-on-insert persistence helper
- Version-history read endpoint

**Context required:**
- prdSections: Confluence Sync & Publishing
- tadSections: Data architecture: Document, DocumentVersion, ADR-006
- schemas: Document, DocumentVersion

### FBS-006 — Document scoping — shared vs client-specific visibility

**Domain.** Authentication & Access Control  
**Size.** small (4 h)  
**Risk.** high  
**Dependencies.** FBS-005, FBS-001

Introduce ScopeGrant and the scope_mode field. Implement the label-driven scope inference and the read-time scope check at the data layer (extends FBS-001 RLS).

**Scope (story → ACs):**
- `US-019` → AC-055, AC-056, AC-057
- `US-020` → AC-058, AC-059, AC-060

**Testable outcomes:**
- A page labelled 'shared' becomes visible to every authenticated tenant on publish.
- A page labelled 'client:<slug>' is visible only to the named tenant(s); direct URL access from other tenants returns 404.
- Removing 'shared' from a previously-shared page hides it on the next sync from all tenants except those granted client-specific access.
- A publish that names a non-existent tenant in its scope label is rejected with a clear error.

**Deliverables:**
- ScopeGrant migration + RLS policy
- Scope-label parser for Confluence labels
- Scope-aware document read helper

**Context required:**
- prdSections: Authentication & Access Control
- tadSections: Data architecture: ScopeGrant, Security architecture: tenant isolation
- schemas: ScopeGrant

### FBS-007 — Renderer — Confluence storage format to portable HTML with cross-link rewriting

**Domain.** Confluence Sync & Publishing  
**Size.** medium (8 h)  
**Risk.** medium  
**Dependencies.** FBS-005

Implement deterministic Confluence-storage → AST → HTML rendering; preserve headings, lists, tables, code (with lang), inline images. Rewrite cross-page links: live for published, inert for non-published.

**Scope (story → ACs):**
- `US-010` → AC-028, AC-029, AC-030
- `US-011` → AC-031, AC-032, AC-033

**Testable outcomes:**
- Rendered HTML preserves headings (h1–h4), lists, tables, code blocks with language hint, and inline images.
- An inline image renders from a per-page asset path with the same alt-text as the source.
- A cross-link to a published page rewrites to the portal URL; a cross-link to a non-published page renders as inert text with a 'not available' tooltip.
- An external https link survives verbatim and opens in a new tab with rel='noopener'.

**Deliverables:**
- services/renderer (Fargate)
- Confluence storage parser + AST
- HTML serializer with cross-link rewriter
- Asset extractor that writes images to S3

**Context required:**
- prdSections: Confluence Sync & Publishing
- tadSections: Components: Renderer

### FBS-008 — Confluence allow-list management (admin) + sync filter

**Domain.** Confluence Sync & Publishing  
**Size.** small (4 h)  
**Risk.** medium  
**Dependencies.** FBS-001

Admin UI surface to manage the allow-list of Confluence labels and source spaces; sync engine consumes it as the first gate. Allow-list changes audit-logged.

**Scope (story → ACs):**
- `US-001` → AC-001, AC-002, AC-003
- `US-002` → AC-004, AC-005, AC-006

**Testable outcomes:**
- An admin can add or remove labels from the allow-list and the change is audit-logged with their identity.
- A page that does not match any allow-listed label or space is skipped by sync with a debug log entry.
- An empty allow-list publishes zero pages and surfaces an admin-visible warning.

**Deliverables:**
- allow-list table + admin CRUD endpoints
- Admin UI page for allow-list
- Sync filter middleware

**Context required:**
- prdSections: Confluence Sync & Publishing
- tadSections: Components: Sync Service

### FBS-009 — Sync Service — Confluence webhook receiver + HMAC verification + dedup

**Domain.** Confluence Sync & Publishing  
**Size.** medium (6 h)  
**Risk.** medium  
**Dependencies.** FBS-008

Lambda webhook receiver behind API Gateway with HMAC verification, Confluence-IP allow-list, dedup keyed on (page_id, source_version_id), and SQS publish-queue enqueue.

**Scope (story → ACs):**
- `US-005` → AC-013, AC-014, AC-015

**Testable outcomes:**
- POST /webhooks/confluence with a valid HMAC enqueues exactly one event onto the publish-queue.
- A duplicate Confluence webhook delivery does not produce a duplicate downstream version.
- An invalid HMAC or a non-allow-listed source IP returns 400 / 403 cleanly and the attempt is audit-logged.
- A webhook payload that fails schema validation is rejected with a 400 and an alert is raised.

**Deliverables:**
- lambda/webhook-receiver
- API Gateway + WAF + Confluence IP allow-list
- Dedup table in Postgres

**Context required:**
- prdSections: Confluence Sync & Publishing
- tadSections: Components: Sync Service, Integration architecture: Confluence, ADR-005

### FBS-010 — Sync Service — polling fallback with cursor

**Domain.** Confluence Sync & Publishing  
**Size.** small (4 h)  
**Risk.** medium  
**Dependencies.** FBS-009

Fargate cron-driven polling job that resumes from a Postgres sync_cursor when webhooks have been silent past the configured threshold; backfills one cycle after webhook recovery.

**Scope (story → ACs):**
- `US-006` → AC-016, AC-017, AC-018

**Testable outcomes:**
- When webhooks have not fired for N minutes, the polling job fetches recently-changed pages and enqueues eligible events.
- After webhook recovery, the polling cycle backfills one cycle before quiescing.
- Polled events follow the same allow-list → approval → AI-review path as webhook events.

**Deliverables:**
- Fargate polling task with sync_cursor logic
- EventBridge schedule

**Context required:**
- prdSections: Confluence Sync & Publishing
- tadSections: Components: Sync Service, ADR-005

### FBS-011 — AI Gateway — Bedrock integration, circuit breaker, fail-closed

**Domain.** AI Document Review  
**Size.** medium (8 h)  
**Risk.** high  
**Dependencies.** FBS-001

AI Gateway service with operations for review, release-notes, summary, quality. Wires Bedrock VPC endpoint, per-operation timeout + retry + circuit breaker, fail-closed semantics, prompt-version registry, and audit hooks.

**Scope (story → ACs):**
- `US-062` → AC-184, AC-185, AC-186

**Testable outcomes:**
- Bedrock 5xx / timeout / schema-mismatch causes AI Gateway to return 'provider-unavailable' with the operation context.
- Bedrock availability recovers and the circuit closes within the configured reset window.
- An operator cannot bypass the fail-closed gate in prod without the documented two-person break-glass procedure.

**Deliverables:**
- services/ai-gateway
- Bedrock VPC endpoint
- Prompt-version registry
- Circuit breaker + retry policy per operation
- Break-glass procedure documented + audit-logged

**Context required:**
- prdSections: AI Document Review, Non-Functional
- tadSections: Components: AI Gateway, ADR-001, ADR-007

### FBS-012 — AI Document Review — secrets and credentials detection

**Domain.** AI Document Review  
**Size.** medium (6 h)  
**Risk.** high  
**Dependencies.** FBS-011

Implement the secrets / credentials / API keys detection operation via AI Gateway. Raise high-severity findings on matches; raise medium-severity on low-confidence candidates.

**Scope (story → ACs):**
- `US-040` → AC-118, AC-119, AC-120

**Testable outcomes:**
- A page containing an AWS access key pattern triggers a finding with category=secret and severity=high.
- A low-confidence candidate triggers a finding with severity=medium routed to reviewer rather than ignored.
- A clean page produces a 'no-secret-findings' record on the version and proceeds.

**Deliverables:**
- AI review prompt: secrets
- Finding schema + persistence
- Test fixtures with synthetic secret patterns

**Context required:**
- prdSections: AI Document Review
- tadSections: Components: AI Gateway, ADR-007
- schemas: AIFinding

### FBS-013 — AI Document Review — internal URLs, Jira links, internal emails

**Domain.** AI Document Review  
**Size.** small (4 h)  
**Risk.** medium  
**Dependencies.** FBS-011

Three high-severity detectors over the configured internal-domain / Jira / internal-email allow-lists.

**Scope (story → ACs):**
- `US-041` → AC-121, AC-122, AC-123

**Testable outcomes:**
- A URL ending in an internal-domain triggers an internal-url finding with severity=high.
- A link or reference matching a Jira ticket URL pattern triggers an internal-ticket finding.
- An email at an internal domain triggers an internal-email finding (high for staff inboxes, medium for shared).

**Deliverables:**
- AI review prompts: internal URL / Jira / internal email
- Configurable allow-lists

**Context required:**
- prdSections: AI Document Review
- tadSections: Components: AI Gateway

### FBS-014 — AI Document Review — missing content (placeholders, empty sections, stubs)

**Domain.** AI Document Review  
**Size.** small (4 h)  
**Risk.** low  
**Dependencies.** FBS-011

Low/medium severity detectors for TODO/TBD/lorem ipsum placeholders, headings immediately followed by next heading, and pages shorter than configured minimum.

**Scope (story → ACs):**
- `US-042` → AC-124, AC-125, AC-126

**Testable outcomes:**
- Placeholder strings raise a missing-content finding with severity=medium.
- An empty section (heading immediately followed by another heading) raises an empty-section finding with severity=low.
- A page below the configured minimum-word threshold raises a stub finding with severity=low.

**Deliverables:**
- AI review prompt: missing content
- Configurable thresholds

**Context required:**
- prdSections: AI Document Review
- tadSections: Components: AI Gateway

### FBS-015 — Approval-state gating

**Domain.** Confluence Sync & Publishing  
**Size.** small (4 h)  
**Risk.** medium  
**Dependencies.** FBS-009

Configurable approval-signal evaluation (label / status / workflow). Pages without the signal are rejected; pages that lose the signal post-publish are unpublished on the next sync.

**Scope (story → ACs):**
- `US-003` → AC-007, AC-008, AC-009
- `US-004` → AC-010, AC-011, AC-012

**Testable outcomes:**
- A page missing the approval signal is blocked at the publish gate and does not appear on the portal.
- A previously-published page that loses its approval signal is unpublished within 5 minutes p95 on the next sync.
- An unpublish caused by loss of approval preserves the version history and is audit-logged with cause = 'approval-state-loss'.

**Deliverables:**
- Approval-signal evaluator with admin-config
- Loss-of-approval unpublish handler

**Context required:**
- prdSections: Confluence Sync & Publishing
- tadSections: Components: Publishing Pipeline

### FBS-016 — Publishing Pipeline orchestration (Step Functions)

**Domain.** Confluence Sync & Publishing  
**Size.** large (12 h)  
**Risk.** high  
**Dependencies.** FBS-005, FBS-007, FBS-009, FBS-010, FBS-012, FBS-013, FBS-014, FBS-015, FBS-004

Step Functions state machine that strings allow-list → approval → AI review → render → persist → OpenSearch index → Redis cache invalidate → notify. Per-stage retry + DLQ + observability. AC for sync latency observability (US-007) ships as part of this FBS.

**Scope (story → ACs):**
- `US-007` → AC-019, AC-020, AC-021

**Testable outcomes:**
- A page-change event flows through every stage in order and reaches the portal within 5 minutes p95.
- End-to-end sync latency is emitted as a histogram metric tagged by page and pipeline stage.
- p95 sync latency > 5 min for 15 min raises a paging alert.
- A failure at any stage routes the event to the DLQ for that stage with an actionable diagnostic.
- publish.complete emits on EventBridge for downstream consumers.

**Deliverables:**
- publishing service skeleton
- Step Functions state machine JSON
- Per-stage Lambda / Fargate tasks
- publish-latency histogram + alerts

**Context required:**
- prdSections: Confluence Sync & Publishing, Non-Functional
- tadSections: Components: Publishing Pipeline, ADR-010

### FBS-017 — Hard publish block on high-severity AI findings

**Domain.** AI Document Review  
**Size.** small (4 h)  
**Risk.** high  
**Dependencies.** FBS-016, FBS-012, FBS-013

Publish gate that rejects pages with open findings of severity = high. Manual publish API rejects bypass attempts; bypass attempts are audit-logged.

**Scope (story → ACs):**
- `US-043` → AC-127, AC-128, AC-129

**Testable outcomes:**
- A page with any open high-severity finding is rejected at the publish gate; state becomes 'blocked-on-review'.
- When all high-severity findings are resolved (false positive confirmed or source corrected), the page becomes publishable.
- A manual publish API request for a blocked page is rejected and the bypass attempt is audit-logged.

**Deliverables:**
- Publish-gate predicate
- Bypass-attempt audit event type

**Context required:**
- prdSections: AI Document Review
- tadSections: Components: Publishing Pipeline, Security controls: AI review fail-closed gate

### FBS-018 — Reviewer UI — AI findings in context + triage actions

**Domain.** AI Document Review  
**Size.** medium (8 h)  
**Risk.** medium  
**Dependencies.** FBS-017, FBS-002

Admin UI panel showing each finding's matched span highlighted in the rendered page; per-finding ignore / acknowledge / block actions with reviewer identity + timestamp audit.

**Scope (story → ACs):**
- `US-044` → AC-130, AC-131, AC-132
- `US-045` → AC-133, AC-134, AC-135

**Testable outcomes:**
- Reviewer opens the review panel and sees each finding's matched span highlighted in context, colour-coded by severity.
- Clicking a finding scrolls the page so the span is centred and focused.
- Stale spans (removed in a newer revision) are marked 'stale' rather than rendered as findings against missing content.
- 'Ignore' on the last high-severity finding makes the page publishable and audit-logs the decision.
- 'Block' transitions the page to 'blocked-pending-source-fix' until source is corrected and re-synced.

**Deliverables:**
- apps/admin review-panel routes
- Triage endpoints + audit event emission

**Context required:**
- prdSections: AI Document Review
- tadSections: Components: Admin UI, Components: AI Gateway
- schemas: AIFinding, ReviewDecision

### FBS-019 — Admin — manual sync re-trigger and unpublish

**Domain.** Confluence Sync & Publishing  
**Size.** small (4 h)  
**Risk.** low  
**Dependencies.** FBS-016

Admin UI controls for re-syncing one page or one tag, and unpublishing a page with a required reason. All actions audit-logged. Unpublish requires explicit re-publish to recover.

**Scope (story → ACs):**
- `US-012` → AC-034, AC-035, AC-036
- `US-013` → AC-037, AC-038, AC-039

**Testable outcomes:**
- Manual page re-sync enqueues the page on the publish queue at priority and is audit-logged.
- Manual tag re-sync enumerates approved allow-listed pages with that tag and enqueues them.
- Unpublish with a non-empty reason removes the page from browse and search within 60s; reason is audit-logged.
- Unpublish without a reason is rejected.
- An unpublished page does not auto-recover; a future approved update requires an explicit re-publish action.

**Deliverables:**
- Admin endpoints + UI for re-sync and unpublish
- Re-sync progress dashboard

**Context required:**
- prdSections: Confluence Sync & Publishing
- tadSections: Components: Admin UI

### FBS-020 — Portal Frontend — browse by product/category + latest version view

**Domain.** Client Portal  
**Size.** medium (8 h)  
**Risk.** medium  
**Dependencies.** FBS-006, FBS-007, FBS-002

Next.js App Router with Lambda@Edge per-tenant cache key. Browse navigation derived from Confluence label hierarchy; latest-version view with 'Latest' badge and last-updated timestamp.

**Scope (story → ACs):**
- `US-028` → AC-082, AC-083, AC-084
- `US-029` → AC-085, AC-086, AC-087

**Testable outcomes:**
- Authenticated user lands on the portal home and sees products derived from Confluence labels with their categories.
- For the same set of source labels, two users see identical grouping (deterministic).
- A user with no entitled documents under a product sees that product omitted from their nav.
- Opening a document URL without an explicit version renders the latest version with a 'Latest' badge and timestamp.
- Edge cache key includes tenant_id so cross-tenant cache poisoning is impossible (verified by isolation test).

**Deliverables:**
- apps/portal (Next.js)
- Lambda@Edge tenant-aware cache key
- Browse + read routes
- Browse-determinism test

**Context required:**
- prdSections: Client Portal
- tadSections: Components: Portal Frontend, Portal API, ADR-004

### FBS-021 — Portal — version history view + block-level diff

**Domain.** Client Portal  
**Size.** medium (6 h)  
**Risk.** medium  
**Dependencies.** FBS-020, FBS-005

Per-page version history with previous-version reading and block-level diff vs latest. Inline and side-by-side modes.

**Scope (story → ACs):**
- `US-030` → AC-088, AC-089, AC-090
- `US-031` → AC-091, AC-092, AC-093

**Testable outcomes:**
- Clicking a previous version row renders the page at that version with a 'Viewing older version' banner.
- Block-level diff highlights added/removed/modified content in green/red/yellow.
- Side-by-side and inline diff modes show identical diff data without refetching.
- Attempt to view an older version of an unpublished page returns 'not available' even with the direct URL.

**Deliverables:**
- Version-history route + UI
- Block-level diff library

**Context required:**
- prdSections: Client Portal
- tadSections: Components: Portal Frontend, Portal API

### FBS-022 — Search — OpenSearch indexing + scoped query gateway

**Domain.** Client Portal  
**Size.** medium (8 h)  
**Risk.** high  
**Dependencies.** FBS-016, FBS-006

Index documents on publish-complete. Scoped query gateway injects the tenant filter; callers cannot pass raw queries. Automated tenant-isolation search test on every release.

**Scope (story → ACs):**
- `US-033` → AC-097, AC-098, AC-099
- `US-034` → AC-100, AC-101, AC-102

**Testable outcomes:**
- Submitted query returns ranked matches with title, snippet, product, and last-updated timestamp.
- p95 search response < 1 s for the user's entitled corpus.
- A query that would match a document outside scope returns zero hits (not surfaced and hidden — excluded at query build).
- Cross-tenant search isolation test runs and passes on every release.

**Deliverables:**
- OpenSearch index template
- Scoped search gateway module
- Cross-tenant search isolation test

**Context required:**
- prdSections: Client Portal, Non-Functional
- tadSections: Components: Portal API search adapter, Security controls: search index tenant filter injection

### FBS-023 — PDF download (on-demand render with 30-day cache)

**Domain.** Client Portal  
**Size.** medium (6 h)  
**Risk.** low  
**Dependencies.** FBS-020, FBS-007

Renderer-backed PDF generation triggered by per-page Download as PDF; footer carries title, version, timestamp, and tenant identity. 30-day cache in S3.

**Scope (story → ACs):**
- `US-032` → AC-094, AC-095, AC-096

**Testable outcomes:**
- Clicking Download as PDF returns a styled PDF matching the on-screen page including images and code blocks.
- The PDF footer contains document title, version, publish timestamp, and the requesting user's tenant identity.
- A failed PDF render surfaces a clear error toast to the user and logs the failure for investigation.

**Deliverables:**
- Playwright-headless PDF worker
- Per-page Download as PDF endpoint
- 30-day PDF bucket lifecycle

**Context required:**
- prdSections: Client Portal
- tadSections: Components: Renderer, ADR-008

### FBS-024 — Per-user last-visited tracking

**Domain.** Client Portal  
**Size.** small (3 h)  
**Risk.** low  
**Dependencies.** FBS-020

Redis write + Postgres write-behind on every page render for an authenticated user. Erased on user removal. Used by the 'Since your last visit' feature (FBS-026).

**Scope (story → ACs):**
- `US-035` → AC-103, AC-104, AC-105

**Testable outcomes:**
- Opening a document updates the user's last-visited timestamp for that document in Redis within 100 ms.
- Redis last-visited is written-behind to Postgres within the configured flush interval.
- User-removal flow erases all per-user last-visited records for that user and audit-logs the deletion.

**Deliverables:**
- Redis last-visited writer
- Postgres write-behind worker
- User-removal erase path

**Context required:**
- prdSections: Client Portal
- tadSections: Components: Portal API

### FBS-025 — AI release notes — generate, reviewer approve, regenerate/edit/discard

**Domain.** AI Release Notes & Change Summary  
**Size.** medium (8 h)  
**Risk.** medium  
**Dependencies.** FBS-011, FBS-018

Release-notes generation via AI Gateway producing What's New / Breaking / Recommended sections. Reviewer approval gate; regenerate / inline-edit / discard flows; SLA reminders.

**Scope (story → ACs):**
- `US-046` → AC-136, AC-137, AC-138
- `US-047` → AC-139, AC-140, AC-141
- `US-049` → AC-145, AC-146, AC-147

**Testable outcomes:**
- On a new version, release-notes are generated covering What's New, Breaking, Recommended based on the diff vs prior.
- First publication of a page produces What's New + 'None for this release' in the other sections.
- Reviewer approval is required before clients see the notes.
- Regeneration creates a new draft preserving the prior one in a side panel; the regeneration is audit-logged.
- Reviewer edits persist across subsequent regenerations unless explicitly discarded.

**Deliverables:**
- AI Gateway operation: release-notes
- Reviewer approval routes + UI
- Per-version notes persistence

**Context required:**
- prdSections: AI Release Notes & Change Summary
- tadSections: Components: AI Gateway, Admin UI

### FBS-026 — AI 'Since your last visit' summary on landing page

**Domain.** AI Release Notes & Change Summary  
**Size.** small (4 h)  
**Risk.** medium  
**Dependencies.** FBS-011, FBS-024

Per-client landing-page summary AI-generated from the diff of entitled changes the user has not yet viewed. Cached when the underlying change set is unchanged.

**Scope (story → ACs):**
- `US-048` → AC-142, AC-143, AC-144

**Testable outcomes:**
- Landing page renders an AI paragraph summarising entitled pages that have changed since the user's per-page last visit.
- If there are no changes, the block shows 'You are up to date' rather than fabricated copy.
- Reload with unchanged underlying state is served from cache rather than regenerated.

**Deliverables:**
- AI Gateway operation: since-last-visit summary
- Landing-page summary block + cache invalidation hook

**Context required:**
- prdSections: AI Release Notes & Change Summary
- tadSections: Components: AI Gateway, Portal Frontend

### FBS-027 — Notification Service — digest scheduling, scope-respecting assembly

**Domain.** Notifications  
**Size.** medium (8 h)  
**Risk.** medium  
**Dependencies.** FBS-016, FBS-006

EventBridge-scheduled batch assembly per cadence (immediate, daily, weekly). Re-evaluates entitlement at send time. Per-user 'last notified high-water mark' for idempotent re-runs. SES integration.

**Scope (story → ACs):**
- `US-036` → AC-106, AC-107, AC-108
- `US-037` → AC-109, AC-110, AC-111

**Testable outcomes:**
- Immediate subscribers receive an email within 15 minutes of a relevant publish.
- Daily and weekly digests send one consolidated email per window or none if there are no changes.
- Unsubscribed users receive zero emails across all cadences.
- Users whose entitlement to a document is revoked before send time do not receive that document in the email.
- Re-running the batch assembly does not duplicate sends (high-water mark guards).

**Deliverables:**
- services/notifications
- Cadence scheduler
- Send-watermark table
- SES sender + bounce/complaint feedback

**Context required:**
- prdSections: Notifications
- tadSections: Components: Notification Service

### FBS-028 — AI notification summaries + breaking-change reviewer approval

**Domain.** AI Client Notifications  
**Size.** medium (6 h)  
**Risk.** medium  
**Dependencies.** FBS-027, FBS-011, FBS-025

AI-generated per-page concise summaries (≤ 30 words) inserted into each email. Breaking-change emails sit in 'pending-review' state until approved; reviewer Approve & Send or Reject paths.

**Scope (story → ACs):**
- `US-050` → AC-148, AC-149, AC-150
- `US-051` → AC-151, AC-152, AC-153

**Testable outcomes:**
- Each changed page in a digest carries an AI-generated ≤30-word summary based on the user's entitled change set.
- Two users with different entitlements may see different summaries for the same digest run.
- AI summary failure for one page falls back to title + 'View changes on portal' without breaking the email.
- A breaking-change-flagged email sits 'pending-review'; reviewer Approve & Send dispatches, Reject suppresses with audit.

**Deliverables:**
- AI Gateway operation: notification-summary
- Pending-review queue + reviewer UI

**Context required:**
- prdSections: AI Client Notifications
- tadSections: Components: AI Gateway, Notification Service, Admin UI

### FBS-029 — Notification email — release highlights + deep links

**Domain.** Notifications  
**Size.** small (3 h)  
**Risk.** low  
**Dependencies.** FBS-027, FBS-028

Email template containing per-page highlight summary + deep link with source=email-digest tracking. Overflow rule: top 5 inline + 'view full list' link for larger digests.

**Scope (story → ACs):**
- `US-038` → AC-112, AC-113, AC-114

**Testable outcomes:**
- Each digest email lists each changed page with title, AI summary, and a deep link.
- Digests with >5 changed pages show top 5 inline + 'view full list' link to a portal filtered changes view.
- Deep-link clicks reach the portal with source = 'email-digest' parameter; the user's email is not exposed in URLs.

**Deliverables:**
- Digest email MJML template
- Deep-link signer

**Context required:**
- prdSections: Notifications
- tadSections: Components: Notification Service

### FBS-030 — Self-service notification preferences

**Domain.** Notifications  
**Size.** small (3 h)  
**Risk.** low  
**Dependencies.** FBS-020, FBS-027

Profile page for cadence + per-product subscription + mute. One-click unsubscribe (HMAC signed) in email footer.

**Scope (story → ACs):**
- `US-039` → AC-115, AC-116, AC-117

**Testable outcomes:**
- User opens profile and sees current cadence + per-product toggles; edits save and are reflected on the next send.
- One-click unsubscribe via signed link in the email footer flips the user to 'off' without requiring login.
- Preference changes are reflected in the email unsubscribe footer of subsequent emails.

**Deliverables:**
- Profile/preferences page
- One-click HMAC-signed unsubscribe endpoint

**Context required:**
- prdSections: Notifications
- tadSections: Components: Notification Service, Portal Frontend

### FBS-031 — AI documentation quality scoring + soft warning override

**Domain.** AI Documentation Quality Check  
**Size.** medium (6 h)  
**Risk.** low  
**Dependencies.** FBS-011, FBS-016

Publish-time quality scoring across four dimensions (Completeness, Readability, Missing Examples, Missing API Responses). Low scores warn but do not block; override-with-reason is audit-logged.

**Scope (story → ACs):**
- `US-052` → AC-154, AC-155, AC-156
- `US-053` → AC-157, AC-158, AC-159

**Testable outcomes:**
- Each version persists four scores in [0..1] with the AI-generated short suggestion.
- Below-threshold scores show a warning badge in the publish summary.
- 'Publish anyway' with a required reason proceeds and is audit-logged with publisher + reason.
- Quality-score unavailability is recorded with the version but does not block publish.

**Deliverables:**
- AI Gateway operation: quality
- Quality-score persistence on DocumentVersion
- Override audit event type

**Context required:**
- prdSections: AI Documentation Quality Check
- tadSections: Components: AI Gateway, Admin UI

### FBS-032 — AI quality trend view

**Domain.** AI Documentation Quality Check  
**Size.** small (3 h)  
**Risk.** low  
**Dependencies.** FBS-031

Per-page chart of quality scores across publish history. 'Not enough history' state. Gap rendering for missing scores.

**Scope (story → ACs):**
- `US-054` → AC-160, AC-161, AC-162

**Testable outcomes:**
- Page-level quality view shows a chart per dimension across publish history when ≥ 3 versions exist.
- < 3 versions shows current values + 'not enough history' rather than empty axes.
- A version with unavailable scoring renders as a chart gap, not zero.

**Deliverables:**
- Quality trend chart in Admin UI

**Context required:**
- prdSections: AI Documentation Quality Check
- tadSections: Components: Admin UI

### FBS-033 — Client-admin user lifecycle (invite / disable / remove)

**Domain.** Authentication & Access Control  
**Size.** medium (8 h)  
**Risk.** medium  
**Dependencies.** FBS-002, FBS-004

Client-admin self-service: invite via email with time-limited single-use link; disable to revoke immediately while preserving audit; remove to anonymise PII while keeping accountability.

**Scope (story → ACs):**
- `US-021` → AC-061, AC-062, AC-063
- `US-022` → AC-064, AC-065, AC-066
- `US-023` → AC-067, AC-068, AC-069

**Testable outcomes:**
- Client-admin invites a user; an email with a time-limited single-use acceptance link is sent.
- Invited user sets password + TOTP via the acceptance link and account is created in the inviting tenant with the assigned role.
- Client-admin attempts to invite outside their tenant's allowed roles → rejected with inline error; attempt audit-logged.
- Disable terminates sessions within 60s and blocks subsequent logins; audit preserved.
- Remove anonymises PII; user's audit history becomes 'Removed user (hash)' for displayable identity.
- Removing the last admin in a tenant is blocked with a clear error.

**Deliverables:**
- Invitation flow + acceptance endpoint
- Disable + remove endpoints with audit hooks
- Last-admin guard

**Context required:**
- prdSections: Authentication & Access Control
- tadSections: Components: Auth Service

### FBS-034 — Document view audit + admin action audit coverage

**Domain.** Audit & Compliance  
**Size.** small (4 h)  
**Risk.** low  
**Dependencies.** FBS-004, FBS-020, FBS-019

Extend the audit pipeline (FBS-004) to cover document-view events and all admin actions surfaced in FBS-019 (re-sync, unpublish). Includes search-query audit.

**Scope (story → ACs):**
- `US-026` → AC-076, AC-077, AC-078
- `US-027` → AC-079, AC-080, AC-081

**Testable outcomes:**
- Opening a document page writes an audit entry with user, tenant, document_id, version_id, timestamp.
- A search request audits the query (or its hash), user, and returned document IDs.
- Every admin action (invite, role change, scope change, unpublish, sync re-trigger, AI review decision) writes an audit entry with before/after where applicable.

**Deliverables:**
- Document-view audit producer in Portal API
- Admin-action audit producer in Admin UI / services

**Context required:**
- prdSections: Authentication & Access Control
- tadSections: Components: Audit Log Service, Portal API

### FBS-035 — Enterprise SSO via WorkOS

**Domain.** Authentication & Access Control  
**Size.** medium (6 h)  
**Risk.** medium  
**Dependencies.** FBS-002

Per-tenant SAML 2.0 / OIDC SSO mediated by WorkOS. Tenant.sso_mode flag drives login dispatch; password login is disabled for SSO-enabled tenants.

**Scope (story → ACs):**
- `US-024` → AC-070, AC-071, AC-072

**Testable outcomes:**
- A SSO-enabled tenant's users see an 'SSO Login' button initiating the configured SAML/OIDC flow via WorkOS.
- A valid SSO assertion establishes a session with the role mapped from the assertion's group claim.
- SSO-enabled tenants cannot password-login; users are redirected to the SSO flow.

**Deliverables:**
- WorkOS integration in services/auth
- Tenant.sso_mode field + admin config
- SSO callback handler

**Context required:**
- prdSections: Authentication & Access Control
- tadSections: Components: Auth Service, ADR-009

### FBS-036 — End-to-end sync + publish observability hardening (SLA dashboards)

**Domain.** Performance  
**Size.** small (4 h)  
**Risk.** low  
**Dependencies.** FBS-016

Per-stage latency dashboards, SLA alerts including AI review duration, and the per-page latest-50-publishes view.

**Scope (story → ACs):**
- `US-056` → AC-166, AC-167, AC-168

**Testable outcomes:**
- Per-publish metrics include total end-to-end latency plus a sub-breakdown for AI review.
- p95 e2e > 5 min OR p95 incl. AI > 15 min raises a paging alert.
- Per-page filter on the sync dashboard shows per-stage timings for the latest N publishes (default 50).

**Deliverables:**
- CloudWatch dashboard + alarms
- Per-page filter view

**Context required:**
- prdSections: Non-Functional
- tadSections: Operational concerns: metrics, alerting

### FBS-037 — Portal render p95 SLA + horizontal scaling validation

**Domain.** Performance  
**Size.** medium (6 h)  
**Risk.** medium  
**Dependencies.** FBS-020

Synthetic-load harness for the 500-user reading workload. Auto-rollback wiring on render-p95 breach after deploy. Validate Portal Frontend and API scale to 30 instances under load.

**Scope (story → ACs):**
- `US-055` → AC-163, AC-164, AC-165
- `US-063` → AC-187, AC-188, AC-189

**Testable outcomes:**
- Synthetic 500-user load achieves portal-render p95 < 1.5 s.
- p95 render > 1.5 s over 15 min raises a paging alert and auto-rolls-back if the breach started after the latest deploy.
- Doubling synthetic load drives autoscaling such that p95 returns under 1.5 s within 5 minutes.
- Terminating a read-tier instance mid-request: the request succeeds on retry on a different instance without surfacing an error.

**Deliverables:**
- k6 synthetic load harness
- Auto-rollback CodeDeploy hook
- Read-tier autoscaling policies

**Context required:**
- prdSections: Non-Functional
- tadSections: Deployment architecture: scaling, resource requirements

### FBS-038 — TLS enforcement + at-rest encryption hardening

**Domain.** Data Protection  
**Size.** medium (6 h)  
**Risk.** medium  
**Dependencies.** FBS-001

Verify TLS 1.2/1.3-only across all client surfaces; reject TLS 1.1 cleanly. KMS-managed encryption on every data store; key-rotation event passes for Aurora / S3 / ElastiCache / QLDB.

**Scope (story → ACs):**
- `US-057` → AC-169, AC-170, AC-171
- `US-058` → AC-172, AC-173, AC-174

**Testable outcomes:**
- Client connection negotiates TLS 1.2 or 1.3 with a permitted cipher suite; lower-version negotiation is rejected.
- External TLS scan reaches at least 'intermediate' grade with no known-vulnerable settings.
- Every data store (Aurora, S3 buckets, ElastiCache, QLDB) verifies as encrypted at rest under KMS-managed keys.
- KMS key rotation completes and data remains readable under the new key alias; the rotation is audit-logged.
- Automated infra audit reports zero plaintext-at-rest stores.

**Deliverables:**
- ALB TLS policy + HSTS
- KMS rotation schedule + alarms
- Infra audit Lambda + scheduled run

**Context required:**
- prdSections: Non-Functional
- tadSections: Security architecture: encryption, Security controls: Encryption at rest

### FBS-039 — Accessibility — keyboard navigation, focus trapping, screen reader, contrast

**Domain.** Accessibility  
**Size.** medium (8 h)  
**Risk.** medium  
**Dependencies.** FBS-020, FBS-021, FBS-023

WCAG 2.1 AA pass across login, browse, read, version history, search, PDF flows. Axe-core in CI. Focus management for modals. Contrast tokens audited.

**Scope (story → ACs):**
- `US-060` → AC-178, AC-179, AC-180
- `US-061` → AC-181, AC-182, AC-183

**Testable outcomes:**
- Tab/Shift+Tab traverses every interactive control in visual order with a visible focus indicator meeting WCAG AA contrast.
- Modals trap focus; Escape closes and returns focus to the opener.
- Axe-core runs in CI across login, browse, read, version history, search, PDF flows with zero serious/critical violations.
- Screen reader announces heading levels, lists, table row/column headers, and image alt-text.
- Design tokens pass contrast checks for all text/background pairs at WCAG AA.
- Status indicators (e.g. coloured badges) announce a text-equivalent label.

**Deliverables:**
- Accessible component primitives
- Axe-core CI integration
- Contrast token audit
- Focus-trap utility

**Context required:**
- prdSections: Non-Functional
- tadSections: Security architecture / Compliance: WCAG 2.1 AA

