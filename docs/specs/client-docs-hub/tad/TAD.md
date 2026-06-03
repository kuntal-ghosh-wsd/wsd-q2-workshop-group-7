# Client Documentation Hub — Technical Architecture Document

> Generated from `docs/specs/client-docs-hub/prd/PRD-001.json` v1.0.0 and `docs/specs/client-docs-hub/user-stories/PRD-001-user-stories.json` v1.0.0.
> Canonical machine-readable copy split across `docs/specs/client-docs-hub/tad/TAD-001-001..004.json` (124959 bytes total).
> 10 components, 10 ADRs, status: draft.

## 1. System Overview

**Executive summary.** Client Documentation Hub is a multi-tenant, AI-assisted, read-only publishing portal that mirrors approved Confluence pages to docs.wsd.com under per-client access control. The system is composed of seven domain services running on AWS Fargate behind an API Gateway, fronted by a Next.js Server-Components frontend on CloudFront, with Aurora PostgreSQL as the system of record, OpenSearch for scoped search, ElastiCache Redis for read caching and sessions, S3 for immutable content blobs plus on-demand PDFs, QLDB for tamper-evident audit, Anthropic Claude via Amazon Bedrock for every AI function (pre-publish review, release notes, summaries, notification copy, quality scoring), SES for transactional email, and WorkOS for enterprise SSO. Confluence remains the single source of truth: the Hub is strictly read-replica with a webhook-driven sync pipeline (5-minute SLA at p95) and a polling fallback.

**System purpose.** Replace manual PDF distribution and unscalable Confluence guest access with a secure, auditable, AI-gated client documentation portal that publishes the latest approved Confluence content in near real-time, isolates per-client and shared content, and uses AI to screen sensitive material before publish and to generate release notes and notification copy after publish.

**Architectural approach.** Service-oriented, multi-tenant SaaS on AWS. Confluence is the upstream authoring source; the Hub ingests approved pages via a webhook receiver (Lambda) plus a polling fallback (Fargate cron job), runs an AI review pipeline that fails closed on any provider error, and persists immutable per-page version records in S3 with relational metadata in Aurora. Read traffic is served by a Next.js frontend with React Server Components rendered on Fargate and aggressively cached at CloudFront and Redis. Cross-cutting concerns (authentication, tenant scoping, audit) are enforced at the data-access layer and validated by an automated isolation test suite on every release. AI behaviour is mediated through one internal AI gateway service so provider, model, and fail-closed semantics can be controlled in one place.

**Key capabilities.**
- Webhook-driven and polling-fallback Confluence sync with p95 < 5 min approval-to-portal latency
- Pre-publish AI document review (secrets, internal URLs, internal tickets, internal emails, missing content) with hard block on high-severity findings
- Immutable per-page version history with on-demand PDF rendering
- Per-tenant authentication (password + TOTP and optional SAML/OIDC SSO via WorkOS), per-tenant access scoping enforced at the data-access layer
- AI-generated release notes (What's New / Breaking / Recommended) and per-client 'Since your last visit' summaries, gated by reviewer approval
- Scoped full-text search with tenant isolation guarantees
- Tamper-evident audit (auth, view, admin, AI review decisions) on QLDB with ≥ 12-month retention
- Email notifications via SES with per-user cadence preferences and AI-authored per-page summaries

**External dependencies.**

| System | Purpose | Protocol | Owner |
|---|---|---|---|
| Confluence (WSD instance) | Source of truth for all documentation; provides REST + change-event webhooks | HTTPS REST + webhook | WSD Platform / Atlassian |
| Amazon Bedrock (Anthropic Claude) | All AI functions: review, release notes, summaries, notification copy, quality scoring | AWS SDK (HTTPS) | AWS |
| Amazon SES | Transactional email delivery for notifications | AWS SDK (HTTPS) / SMTP | AWS |
| WorkOS | Per-tenant SAML 2.0 / OIDC SSO mediation | HTTPS REST + SAML/OIDC | WorkOS |
| Atlassian Confluence webhook delivery | Push notification of page changes | HTTPS POST | Atlassian |
| Amazon CloudFront | Edge CDN in front of Next.js frontend | HTTPS | AWS |
| Amazon QLDB | Tamper-evident audit log storage | AWS SDK (HTTPS) | AWS |

**Assumptions and constraints.**
- AWS account and platform-standard CDK/Terraform tooling are in place; deployment uses platform-supplied account structure (per-env accounts).
- Confluence webhooks are reachable from a public Lambda endpoint behind WAF; if not, sync degrades to polling only and the latency SLA must be relaxed.
- Anthropic Claude is accessed exclusively via Amazon Bedrock; direct Anthropic API access is not used (single network egress boundary for security + audit).
- WSD's identity directory provides the initial WSD-operator accounts; client tenants are operator-provisioned in v1.
- Email deliverability is DMARC-aligned for docs.wsd.com; DNS is owned by the marketing team and provisioned ahead of launch.
- AI provider failure is non-bypassable: the review pipeline fails closed, which means an AI outage stops publishes. This is an intentional trade-off (REQ-105).

## 2. Architectural Principles

### Confluence is the single source of truth
The Hub is read-replica with respect to Confluence. No content is authored or edited inside the Hub; portal users cannot mutate documentation.

**Rationale.** Eliminates dual-write reconciliation, preserves the existing author workflow, and keeps governance/compliance audit anchored in Confluence's history.

**Implications.**
- No portal-side editor or comment surface; client feedback is out of scope for v1.
- Two-way sync is explicitly out of scope; Confluence content changes win.
- Recovery from corruption is a re-sync from Confluence, not a backup restore.

**Related REQs.** REQ-001, REQ-002, REQ-003, REQ-005

### Fail closed on AI and on access
On any AI-provider failure or any access-control ambiguity, the system blocks rather than degrades-open. Publishes never proceed without a clean AI review; reads never return cross-tenant content.

**Rationale.** Both the secret-leak and cross-tenant-leak failure modes are catastrophic; the cost of a brief publish outage is small compared to either.

**Implications.**
- An AI Bedrock outage halts publishes until cleared.
- Every tenant-scoped query is rejected at the data-access layer unless an active tenant is bound to the session.
- Break-glass procedures for bypassing AI review require two-person approval and audit.

**Related REQs.** REQ-040, REQ-041, REQ-105, REQ-103, REQ-012

### Tenant isolation at the data layer, not the UI
All cross-tenant safety is enforced inside the data-access layer (PostgreSQL row-level security + tenant-bound query helpers, plus search-index tenant filters that are non-overridable).

**Rationale.** UI-only filtering inevitably regresses; only data-layer enforcement survives refactors and accidental endpoint additions.

**Implications.**
- All Postgres reads/writes use a tenant-bound connection or an explicit shared-scope helper.
- OpenSearch queries always inject the tenant filter at the gateway, not at the caller.
- An automated cross-tenant isolation suite runs on every release; failures block deploy.

**Related REQs.** REQ-012, REQ-013, REQ-024, REQ-103

### Immutable versions and append-only audit
Published page versions are immutable; the audit log is append-only and tamper-evident.

**Rationale.** Lets security and clients answer 'who saw what when?' with confidence; underpins the compliance story.

**Implications.**
- Version records are written to S3 with object-lock; the metadata row in Postgres is referenced by version_id but the binary blob cannot be overwritten.
- Audit lives in QLDB; integrity is verified daily and on demand.
- Garbage collection of retired versions (oldest beyond 20) writes a metadata-preserved tombstone, never an in-place delete.

**Related REQs.** REQ-004, REQ-016, REQ-107

### AI is mediated by a single internal gateway
All AI calls (review, release notes, summaries, notifications, quality scoring) go through one AI Gateway service. Callers never speak Bedrock directly.

**Rationale.** Centralises fail-closed semantics, prompt versioning, audit, token accounting, and provider/model swaps without touching every call site.

**Implications.**
- One choke point for AI provider outages — easier to alert, retry, and circuit-break.
- One place to enforce 'never log raw page content with secrets in plaintext' on AI request/response.
- Provider/model swap (e.g. Claude version bump) requires no change to caller code.

**Related REQs.** REQ-040, REQ-050, REQ-051, REQ-053, REQ-054, REQ-105

### Idempotent, retry-safe pipelines
Every async stage (webhook receipt, AI review, persist, notification) is idempotent and re-runnable. Steps key off Confluence version IDs and per-step run IDs.

**Rationale.** Confluence retries webhooks; AWS retries Lambdas; networks are unreliable. The cheapest defence is to make every step safe to repeat.

**Implications.**
- Webhook receiver deduplicates by (page_id, source_version_id).
- Persist step is a CAS on (page_id, source_version_id) — second writer is a no-op.
- Notification batch assembly uses a per-user 'last notified high-water mark' so re-runs don't duplicate emails.

**Related REQs.** REQ-003, REQ-030, REQ-103

### Observability is a product feature
Sync latency, AI review duration, publish success rate, cross-tenant isolation test outcomes, and AI-fail-closed events are all first-class metrics with alerts and dashboards from day one.

**Rationale.** The SLAs in REQ-NFR-001..107 are only credible if they're measured continuously; reactive monitoring is too late.

**Implications.**
- Each service exports a standard set of histograms and counters (e.g. publish_latency_seconds, ai_review_failures_total).
- CloudWatch Synthetics probe the user-visible flows (login, browse, read, download PDF, search) every 60 s.
- PagerDuty alert rules version-controlled in the same repo as the services.

**Related REQs.** REQ-100, REQ-101, REQ-105

## 3. Components

### Sync Service (Confluence ingestion)
**Purpose.** Receive Confluence webhook events and run a polling fallback; emit one canonicalised 'page-change' event per (page, source-version) onto the publishing pipeline.

**Location.** `services/sync (Fargate workers) + lambda/webhook-receiver (Lambda)`

**Dependencies.** Confluence REST API, EventBridge, SQS publish-queue, Aurora PostgreSQL (sync_cursor table)

**Key patterns.**
- Webhook deduplication keyed on (page_id, source_version_id)
- Polling fallback with a cursor stored in Postgres, triggered by EventBridge schedule
- Backoff-on-failure with DLQ for poison events

**Interfaces.**
- *api* — `POST /webhooks/confluence` — Confluence change webhook receiver; HMAC-verifies the payload and enqueues to SQS.
- *event* — `page-change SQS message` — Canonical change event consumed by the Publishing Pipeline.
- *internal* — `internal: sync-cursor reader` — Used by the polling-fallback Fargate task to resume after restart.

**Responsibilities.**
- Verify webhook authenticity and parse Confluence event payloads.
- Filter on allow-list (label + space) before forwarding.
- Run a periodic poll if webhooks haven't fired in N minutes.
- Dedupe duplicate change events.

**Related REQs.** REQ-001, REQ-002, REQ-003

### Publishing Pipeline
**Purpose.** Orchestrate the per-page-change flow: allow-list filter → approval-state check → AI review → render → persist version → invalidate caches → enqueue notification.

**Location.** `services/publishing (Fargate workers, Temporal-style state machine via AWS Step Functions)`

**Dependencies.** SQS publish-queue, AI Gateway, Renderer, Aurora PostgreSQL (document_versions), S3 (content blobs), OpenSearch (index updates), Redis (cache invalidation), SQS notify-queue

**Key patterns.**
- Step-Functions state machine for retry/visibility
- CAS-on-insert for version persistence (idempotent under retry)
- Fail-closed on AI Gateway error

**Interfaces.**
- *event* — `consume page-change` — Reads page-change events from SQS.
- *event* — `emit publish-complete` — Emitted on EventBridge for downstream consumers (notifications, audit).
- *internal* — `internal: persist version` — Writes immutable version blob to S3 and metadata row to Postgres.

**Responsibilities.**
- Apply the configured approval-state rule.
- Call the AI Gateway for document review; halt on high-severity finding.
- Render Confluence storage format to portable HTML with cross-link rewriting.
- Persist version metadata + blob; update OpenSearch index; invalidate Redis cache.
- Enqueue notification job once publish succeeds.

**Related REQs.** REQ-002, REQ-004, REQ-005, REQ-040, REQ-041, REQ-105

### AI Gateway
**Purpose.** Single mediation surface for every AI call. Owns prompt templates, model selection, fail-closed semantics, audit, and token accounting.

**Location.** `services/ai-gateway (Fargate)`

**Dependencies.** Amazon Bedrock (Anthropic Claude models), Postgres (prompt-version registry, AI-call audit), QLDB (decision audit)

**Key patterns.**
- One narrow tool-shaped operation per AI function (review_page, release_notes, since_last_visit, notification_summary, quality_score)
- Per-operation circuit breaker with fail-closed default
- Prompt-version stamped on every output for reproducibility

**Interfaces.**
- *api* — `POST /ai/review` — Document review request; returns findings list or 'provider-unavailable' on failure.
- *api* — `POST /ai/release-notes` — Release notes generation; returns three-section draft.
- *api* — `POST /ai/summary` — Generates 'Since your last visit' or per-page notification summaries.
- *api* — `POST /ai/quality` — Quality scoring (completeness, readability, missing examples, missing API responses).

**Responsibilities.**
- Build prompts from versioned templates; never inline page content into logs.
- Call Amazon Bedrock with the configured Claude model.
- Apply the per-operation timeout, retry, and circuit-breaker.
- Return a structured 'fail-closed' error if the provider is unavailable or the response fails schema validation.

**Related REQs.** REQ-040, REQ-050, REQ-051, REQ-053, REQ-054, REQ-105

### Portal API
**Purpose.** All authenticated read endpoints for the client portal: browse, read, version history, diff, PDF, search, notification preferences.

**Location.** `services/portal-api (Fargate, Node.js + Fastify)`

**Dependencies.** Aurora PostgreSQL (read replicas), OpenSearch, S3 (content blobs and PDFs), Redis (sessions, last-visited, render cache)

**Key patterns.**
- Every request bound to a tenant via session middleware; data-layer rejects untenanted queries
- Read-through cache on Redis for hot document versions
- Pre-signed S3 URLs for PDF download

**Interfaces.**
- *api* — `GET /api/v1/products` — Tenant-scoped product/category navigation.
- *api* — `GET /api/v1/pages/:id/version/:version` — Read a specific version (latest by default).
- *api* — `GET /api/v1/pages/:id/diff` — Compute a block-level diff between two versions.
- *api* — `GET /api/v1/pages/:id/pdf` — Generate or fetch a PDF for the requested version.
- *api* — `GET /api/v1/search` — Tenant-scoped full-text search.

**Responsibilities.**
- Authn/authz enforcement via Auth Service-issued session tokens.
- Compose read responses from Postgres metadata + S3 content + OpenSearch results.
- Track per-user last-visited timestamps in Redis (write-behind to Postgres).
- Render PDFs on demand via the PDF renderer worker.

**Related REQs.** REQ-012, REQ-020, REQ-021, REQ-022, REQ-023, REQ-024, REQ-025, REQ-100, REQ-103

### Portal Frontend (Next.js)
**Purpose.** Server-rendered client portal at docs.wsd.com — browse, read, version history, search, PDF download, preferences.

**Location.** `apps/portal (Next.js 15 App Router on Fargate)`

**Dependencies.** Portal API, Auth Service (session cookies), CloudFront (CDN)

**Key patterns.**
- React Server Components for primary read paths (no client JS for static content)
- ISR (Incremental Static Regeneration) for browse navigation with per-tenant cache key
- Accessibility-first component library (WCAG 2.1 AA)

**Interfaces.**
- *api* — `HTTPS routes (/, /products, /pages/:id, /search, /preferences)` — User-facing routes; all gated by session middleware.
- *internal* — `Server Action: 'mark visited'` — Server-side mutation that updates per-user last-visited via Portal API.

**Responsibilities.**
- Render the portal UX server-side, hydrating only interactive widgets.
- Enforce session presence at edge middleware; redirect to Auth Service login on absence.
- Embed AI-generated 'Since your last visit' summary on the landing page.
- Drive accessibility (keyboard, screen reader, contrast).

**Related REQs.** REQ-010, REQ-020, REQ-021, REQ-025, REQ-051, REQ-100, REQ-104

### Auth Service
**Purpose.** Login (password + TOTP), session management, optional SAML/OIDC SSO via WorkOS, password-reset, lockout, client-admin user lifecycle.

**Location.** `services/auth (Fargate)`

**Dependencies.** Aurora PostgreSQL (users, tenants, sessions), Redis (active sessions, rate limits), WorkOS (per-tenant SSO mediation), SES (password-reset, invitation emails)

**Key patterns.**
- Argon2id password hashes; TOTP secret encrypted with KMS-bound DEK
- Per-tenant SSO mode flag; password login disabled when SSO is enabled
- Token-bound CSRF for cookie-auth endpoints

**Interfaces.**
- *api* — `POST /auth/login` — Password + TOTP login.
- *api* — `POST /auth/sso/callback` — WorkOS SAML/OIDC callback handler.
- *api* — `POST /auth/users/invite` — Client-admin invitation flow.
- *api* — `POST /auth/logout` — Idempotent logout (clears session in Redis + Postgres + cookie).

**Responsibilities.**
- Authenticate users and establish/destroy sessions.
- Enforce rate limits and account lockouts.
- Mediate WorkOS SSO for tenants configured for SAML/OIDC.
- Manage tenant-scoped user lifecycle (invite/disable/remove) for client-admins.

**Related REQs.** REQ-010, REQ-011, REQ-014, REQ-015

### Notification Service
**Purpose.** Assemble per-user digest emails (cadence-aware, scope-respecting), generate AI summaries via the AI Gateway, send via SES, honour per-user preferences and reviewer approval for breaking changes.

**Location.** `services/notifications (Fargate workers + EventBridge schedules)`

**Dependencies.** Aurora PostgreSQL (subscriptions, preferences, send-watermarks), AI Gateway, SES, EventBridge

**Key patterns.**
- Per-user 'last notified high-water mark' for idempotent re-runs
- Breaking-change emails sit in 'pending-review' state until approved
- One-click unsubscribe links signed with a per-user HMAC

**Interfaces.**
- *event* — `consume publish-complete` — Reacts to publish-complete from EventBridge.
- *internal* — `cron: cadence batches` — EventBridge schedules daily/weekly digest assembly.
- *api* — `POST /notifications/preferences` — User-facing preference updates (proxied via Portal API).

**Responsibilities.**
- Compute the per-user changed-pages set respecting access scope.
- Generate per-page summaries via AI Gateway with fallback to title-only.
- Send via SES with signed unsubscribe and source = 'email-digest' tracking.
- Suppress sends to disabled / removed users.

**Related REQs.** REQ-030, REQ-031, REQ-032, REQ-053

### Admin UI
**Purpose.** Doc-owner and reviewer surface for sync admin, AI review triage, release-notes approval, quality scoring view, unpublish.

**Location.** `apps/admin (Next.js on Fargate, behind WSD SSO)`

**Dependencies.** Portal API (admin endpoints), Auth Service (WSD-staff identity), AI Gateway

**Key patterns.**
- WSD-staff-only access (separate WorkOS connection to WSD's IdP)
- All actions audit-logged to QLDB

**Interfaces.**
- *api* — `HTTPS routes (/sync, /reviews, /notes, /quality)` — Admin surfaces.

**Responsibilities.**
- Allow doc owners to manage allow-list, re-trigger sync, unpublish.
- Allow reviewers to triage AI findings, approve release notes, approve breaking-change notifications.
- Surface quality scores and trends per page.

**Related REQs.** REQ-006, REQ-007, REQ-042, REQ-050, REQ-052, REQ-054, REQ-055

### Audit Log Service
**Purpose.** Append-only, tamper-evident audit storage and query API. Backed by QLDB.

**Location.** `services/audit (Fargate)`

**Dependencies.** Amazon QLDB, EventBridge (audit-event consumer)

**Key patterns.**
- QLDB journal verification (cryptographic digest) on schedule
- Read API constrained to security + admin roles
- Retention ≥ 12 months; cold-archive to S3 with object-lock thereafter

**Interfaces.**
- *event* — `consume audit-event` — EventBridge audit-event consumer.
- *api* — `GET /audit/query` — Security/admin query API for events by actor/tenant/document/date range.

**Responsibilities.**
- Persist every audit-relevant event with actor, action, target, before/after, timestamp.
- Verify journal integrity on schedule and on demand.
- Serve compliance queries with SLAs.

**Related REQs.** REQ-016, REQ-107

### Renderer
**Purpose.** Convert Confluence storage format to portable, accessible HTML and on-demand PDF.

**Location.** `services/renderer (Fargate; Playwright-headless for PDF)`

**Dependencies.** S3 (content blobs, PDFs), Postgres (link-rewrite tables)

**Key patterns.**
- Confluence-storage → AST → portal HTML (deterministic) → PDF (Playwright)
- Cross-link resolution against the published-pages index

**Interfaces.**
- *internal* — `POST /render/html` — Called by Publishing Pipeline at persist-version time.
- *internal* — `POST /render/pdf` — Called by Portal API on download.

**Responsibilities.**
- Faithful structural rendering of headings, lists, tables, code, images.
- Cross-link rewriting (live vs 'not available').
- Add audit footer (title, version, tenant identity) to every PDF.

**Related REQs.** REQ-005, REQ-023

## 4. Data Architecture

### 4.1 Data stores

| Store | Technology | Purpose |
|---|---|---|
| Primary RDBMS | Amazon Aurora PostgreSQL 15 (Serverless v2) | System of record for tenants, users, documents metadata, version index, scope mappings, sync cursors, subscriptions, AI-review decisions. |
| Content Blob Store | Amazon S3 (Object Lock enabled, versioning ON) | Immutable rendered HTML per (document, version); generated PDFs (with TTL); original Confluence storage-format snapshots for audit. |
| Search Index | Amazon OpenSearch managed | Full-text search index of all published document versions, scoped per tenant via a non-overridable filter at the search-gateway. |
| Cache + Sessions | Amazon ElastiCache (Redis 7) | Active sessions, rate-limit counters, per-user last-visited, hot document version render cache. |
| Audit Ledger | Amazon QLDB | Tamper-evident append-only audit log for authentication, document view, admin action, AI review decision, sync re-trigger, unpublish. |

### 4.2 Core entities

#### Tenant
An isolated client workspace. The unit of access scope and billing.

| Field | Type | Required | Description |
|---|---|---|---|
| tenant_id | uuid | yes | PK; surrogate; used as RLS key everywhere. |
| slug | text | yes | Human-readable identifier used in Confluence scope labels (client:<slug>). |
| display_name | text | yes | Shown in UI and email footers. |
| sso_mode | enum (none, saml, oidc) | yes | Drives login dispatch. |
| created_at | timestamptz | yes | Provisioning timestamp. |

**Relationships.** 1:N → User, 1:N → ScopeGrant, 1:N → Subscription

**Indexes.** pk(tenant_id), unique(slug)

#### User
An authenticated principal bound to one tenant.

| Field | Type | Required | Description |
|---|---|---|---|
| user_id | uuid | yes | PK. |
| tenant_id | uuid | yes | FK to Tenant. Sets RLS scope. |
| email | citext | yes | Login identifier; unique within tenant. |
| role | enum (reader, client_admin, wsd_doc_owner, wsd_reviewer, wsd_security) | yes | Authorization role. |
| password_hash | text (argon2id) | no | Null when SSO mode is active. |
| totp_enc | bytea (KMS DEK) | no | Encrypted TOTP secret. |
| status | enum (active, disabled, removed) | yes | Lifecycle state. |

**Relationships.** N:1 → Tenant

**Indexes.** pk(user_id), unique(tenant_id, email), idx(status)

#### Document
A published Confluence page. The document is the long-lived identity; versions are immutable snapshots beneath it.

| Field | Type | Required | Description |
|---|---|---|---|
| document_id | uuid | yes | PK; deterministic from Confluence page ID. |
| confluence_page_id | text | yes | Upstream identity. |
| product_label | text | yes | Drives portal navigation grouping. |
| category_label | text | no | Sub-grouping within a product. |
| scope_mode | enum (shared, client_specific) | yes | Visibility scope. |
| current_version_id | uuid | no | Pointer to the latest published version. |
| state | enum (published, unpublished, blocked_on_review) | yes | Lifecycle. |

**Relationships.** 1:N → DocumentVersion, 1:N → ScopeGrant (when client_specific)

**Indexes.** pk(document_id), unique(confluence_page_id), idx(state, product_label)

#### DocumentVersion
One immutable publish of a document. Binary content lives in S3.

| Field | Type | Required | Description |
|---|---|---|---|
| version_id | uuid | yes | PK. |
| document_id | uuid | yes | FK → Document. |
| source_version_id | text | yes | Confluence revision number. |
| html_blob_s3_key | text | yes | S3 key (immutable, object-lock). |
| snapshot_blob_s3_key | text | yes | Original Confluence storage format for audit. |
| publisher_id | uuid | yes | FK → User (WSD doc owner). |
| published_at | timestamptz | yes | Publish timestamp. |
| review_decision_id | uuid | yes | FK → ReviewDecision. |
| quality_scores_jsonb | jsonb | no | 4-dimension scores. |

**Relationships.** N:1 → Document, N:1 → User (publisher), 1:N → ReleaseNotes block

**Indexes.** pk(version_id), unique(document_id, source_version_id), idx(document_id, published_at DESC)

#### ScopeGrant
Joins a client-specific document to the tenant(s) entitled to read it. Shared documents do not have ScopeGrant rows.

| Field | Type | Required | Description |
|---|---|---|---|
| grant_id | uuid | yes | PK. |
| document_id | uuid | yes | FK → Document. |
| tenant_id | uuid | yes | FK → Tenant. |
| granted_at | timestamptz | yes | Provenance timestamp. |

**Relationships.** N:1 → Document, N:1 → Tenant

**Indexes.** pk(grant_id), unique(document_id, tenant_id)

#### AIFinding
A single AI-document-review finding raised against a document version.

| Field | Type | Required | Description |
|---|---|---|---|
| finding_id | uuid | yes | PK. |
| version_id | uuid | yes | FK → DocumentVersion. |
| category | enum (secret, internal_url, internal_ticket, internal_email, missing_content, empty_section, stub) | yes | Finding category. |
| severity | enum (low, medium, high) | yes | Drives publish gating. |
| matched_span | jsonb | yes | Anchor location in the rendered HTML. |
| decision_id | uuid | no | FK → ReviewDecision when triaged. |

**Relationships.** N:1 → DocumentVersion, N:1 → ReviewDecision (optional)

**Indexes.** pk(finding_id), idx(version_id, severity)

#### ReviewDecision
A reviewer triage decision on a finding or release-notes block. Audit-logged.

| Field | Type | Required | Description |
|---|---|---|---|
| decision_id | uuid | yes | PK. |
| actor_user_id | uuid | yes | FK → User (reviewer). |
| decision | enum (ignore, acknowledge, block, approve_release_notes, reject_release_notes) | yes | Decision verb. |
| rationale_text | text | no | Reviewer-supplied note. |
| decided_at | timestamptz | yes | Timestamp. |

**Relationships.** 1:1 ← AIFinding (when triaging a finding)

**Indexes.** pk(decision_id), idx(actor_user_id, decided_at)

### 4.3 Data flow

Sync flow: Confluence webhook → Lambda receiver verifies HMAC and enqueues into SQS publish-queue → Publishing Pipeline (Step Functions) pulls one event → applies allow-list + approval state → calls AI Gateway for document review → on clean review, renders HTML and writes the immutable blob to S3, the metadata row to Aurora, the search document to OpenSearch, and emits publish-complete on EventBridge → Notification Service consumes the event and assembles per-user digests. Read flow: client request hits CloudFront → Next.js Frontend (Fargate) → session validated via Auth Service → Portal API queries Aurora read replica for metadata, fetches the HTML blob from S3 (or Redis render cache), returns to the user. Per-user last-visited is written-behind to Postgres via Redis. Audit flow: every audit-relevant action across services emits an audit-event on EventBridge → Audit Service writes to QLDB. Daily integrity verification compares the QLDB digest against the prior recorded digest and pages security on mismatch.

**Caching strategy.** Three layers: CloudFront edge (cache-key includes tenant_id from auth context — done via Lambda@Edge so cross-tenant cache poisoning is impossible); Redis read-through cache for hot document versions and rendered HTML (TTL 1h, invalidated on publish-complete); Aurora read replicas absorb metadata reads. Cache invalidation on publish-complete is pushed to both CloudFront and Redis simultaneously.

**Data retention.** Document versions: last 20 retained per page in hot S3 storage; older versions metadata-only in Aurora with content garbage-collected. Audit log: ≥ 12 months in QLDB, then cold-archived to S3 Object-Lock-Compliance for the contractual retention window. Sessions: TTL bound to the session-timeout configuration. Last-visited per user: retained for the user's lifetime; erased on user removal.

## 5. Integration Architecture

**API design.** REST + Server-Sent Events for live progress (publish status in Admin UI); JSON over HTTPS; OpenAPI 3.1 specs versioned with services.

Conventions:
- All client-facing endpoints are HTTPS only, TLS 1.2+, HSTS 1-year
- All endpoints carry an x-request-id; logs and audit join on this ID
- Pagination is cursor-based (no offset/limit)
- Error responses follow RFC 7807 Problem Details
- Mutation endpoints require an Idempotency-Key header

### Integration contracts

#### Atlassian Confluence
**Purpose.** Source of truth; provides page content and change events.

**Protocol.** HTTPS REST (Confluence Cloud REST v2) + webhook callbacks

**Auth.** OAuth 2.0 client credentials grant; rotating tokens stored in AWS Secrets Manager

**Operations.**
- `GET /wiki/api/v2/pages/{id}` — Page fetch by id+version
- `POST (inbound to lambda/webhook-receiver)` — Page-changed webhook
- `GET /wiki/api/v2/pages?since=...` — Page list since cursor (polling)

**Error handling.** Retry with exponential backoff on 5xx and 429; fail-closed (do not publish) on persistent error; dead-letter queue for poison events.

#### Amazon Bedrock (Anthropic Claude)
**Purpose.** All AI functions: review, release notes, summaries, notifications, quality scoring.

**Protocol.** AWS SDK / Bedrock Runtime InvokeModel + ConverseStream

**Auth.** IAM role with least-privilege Bedrock InvokeModel on the configured Claude model ARN(s)

**Operations.**
- `POST (AI Gateway) /ai/review` — Document review
- `POST (AI Gateway) /ai/release-notes` — Release notes
- `POST (AI Gateway) /ai/summary` — Notification / since-last-visit summary
- `POST (AI Gateway) /ai/quality` — Quality score

**Error handling.** Fail closed: any Bedrock 5xx, timeout, or response-schema-mismatch causes the AI Gateway to return a structured 'provider-unavailable' error; pipeline halts the publish.

#### Amazon SES
**Purpose.** Send notification emails (digest and breaking-change) and operational mail (invitations, password reset).

**Protocol.** AWS SDK (SendEmail / SendRawEmail)

**Auth.** IAM role with SES SendEmail on the docs.wsd.com identity

**Operations.**
- `POST (SES) SendEmail` — Send notification email
- `POST (SES) SendEmail` — Send invitation email

**Error handling.** Retry transient throttling; dead-letter to SQS for manual investigation on persistent failure; bounces and complaints feed back to Notification Service to suppress affected addresses.

#### WorkOS
**Purpose.** SAML 2.0 / OIDC SSO mediation for client tenants requiring enterprise login.

**Protocol.** HTTPS REST

**Auth.** WorkOS API key in AWS Secrets Manager

**Operations.**
- `GET (WorkOS) /sso/authorize` — Get authorization URL
- `POST (WorkOS) /sso/token` — Exchange code for profile

**Error handling.** Surface a generic 'SSO unavailable' error to the user; fall back to support contact, never to password login on a SSO-enabled tenant.


### Messaging patterns

- EventBridge for cross-service domain events (publish-complete, audit-event, user-disabled)
- SQS for ordered work-queues (publish-queue, notification-queue, dead-letter queues per consumer)
- Step Functions for the publishing pipeline state machine (visibility + retry semantics)

### Event-driven events

- `page-change`
- `publish-complete`
- `publish-failed`
- `ai-review-pending-provider`
- `audit-event`
- `user-invited`
- `user-disabled`
- `user-removed`
- `breaking-change-notification-pending-review`

## 6. Security Architecture

**Boundaries.** Three concentric boundaries: (1) Edge — CloudFront + AWS WAF in front of every public route, with managed rule sets for OWASP Top 10 + bot control. (2) Service mesh — services live in private subnets; only ALB ingress per service is exposed; service-to-service traffic uses IAM-authenticated mTLS via the service mesh. (3) Data — Aurora, OpenSearch, ElastiCache, S3, QLDB all in private subnets, accessible only from the service VPC via VPC endpoints. Confluence is reached via an outbound NAT gateway with a static IP for Confluence allow-listing. Bedrock is reached via a VPC endpoint — no public internet egress for AI traffic.

**Authentication.** Cookie-bound session, signed in Auth Service; per-tenant flag selects between password+TOTP and WorkOS-mediated SAML/OIDC SSO

Flow: Password+TOTP: POST /auth/login with email+password → on success, Auth Service issues a TOTP challenge → on valid TOTP, Auth Service writes the session to Postgres + Redis and sets a Secure, HttpOnly, SameSite=Strict cookie scoped to docs.wsd.com. SSO: GET /auth/sso/start?tenant=… → WorkOS authorize URL → user authenticates at their IdP → callback to /auth/sso/callback with the WorkOS code → Auth Service exchanges code for a profile, maps the group claim to a role, writes the session, sets the same cookie.

**Authorization.** Hybrid: tenant scope (data-layer RLS) + role-based authorization (application layer)

Role permissions:
- **reader** — read:document, read:version, create:pdf, manage:own-prefs
- **client_admin** — reader.*, invite:user, disable:user, remove:user (within own tenant)
- **wsd_doc_owner** — manage:allow-list, manual:re-sync, unpublish:page, publish-override:on-quality-warning
- **wsd_reviewer** — triage:ai-finding, approve:release-notes, approve:breaking-change-notification
- **wsd_security** — query:audit-log, verify:audit-integrity

### Security controls

| Control | Implementation | Location | Related REQs |
|---|---|---|---|
| Tenant isolation at the data layer (PostgreSQL Row-Level Security) | Every tenant-scoped table carries a tenant_id column with an RLS policy that admits rows only when current_setting('app.tenant_id') matches; a tenant-bound connection sets app.tenant_id at session start. | Aurora PostgreSQL | REQ-012, REQ-103 |
| Search index tenant filter injection | OpenSearch queries are routed through a thin gateway that injects the tenant filter at query-build time; callers cannot pass raw queries. | Portal API search adapter | REQ-024, REQ-103 |
| AI review fail-closed gate | Publishing Pipeline halts on any AI Gateway 'provider-unavailable' error and emits ai-review-pending-provider on EventBridge. | services/publishing | REQ-040, REQ-041, REQ-105 |
| Append-only tamper-evident audit | Audit Service writes to QLDB; daily integrity job verifies the QLDB digest and alerts on mismatch. | services/audit | REQ-016, REQ-107 |
| Encryption at rest (KMS) | All data stores use AWS-managed CMKs with annual rotation; TOTP secrets and other PII fields are wrapped with a per-tenant DEK. | All data stores | REQ-102 |
| WAF + managed rules | AWS WAF with the AWSManagedRulesCommonRuleSet, AWSManagedRulesKnownBadInputsRuleSet, plus tenant-aware rate limits. | CloudFront / ALB | REQ-010, REQ-011 |
| Brute-force lockout | 5 failed logins per user / 10 min → 15-min lockout; per-IP throttling on top. | services/auth + Redis counters | REQ-011 |
| Cross-tenant CI test | An automated test suite asserts on every release that read endpoints reject cross-tenant access; failures block deploy. | CI | REQ-012, REQ-024, REQ-103 |

### Sensitive data handling

| Data type | Classification | Handling |
|---|---|---|
| Password hash | Restricted | Argon2id with platform-tuned cost; stored in Postgres; never logged. |
| TOTP secret | Restricted | Encrypted with per-tenant DEK wrapped by KMS CMK; never logged. |
| Session cookie value | Restricted | 256-bit opaque ID; never logged in plaintext; only the prefix is logged for correlation. |
| Email address | Confidential (PII) | Encrypted at rest via Aurora storage encryption; access scoped via RLS. |
| Confluence storage-format snapshot | Confidential (may contain client-specific text) | Stored in S3 with object-lock; bucket policy restricts access to publishing pipeline + audit role. |
| AI-pipeline prompt + response payloads | Confidential | Stored in a dedicated S3 bucket with KMS encryption; secret-shape strings redacted before logging. |
| Audit log entries | Restricted (forensic) | Tamper-evident in QLDB; read access limited to wsd_security role; queries are themselves audit-logged. |

**Compliance.**
- WCAG 2.1 AA for primary client-facing flows (REQ-104).
- ≥ 12 month audit retention (REQ-016, REQ-107).
- Tamper-evident audit log (REQ-107).
- Per-tenant data isolation enforceable below the UI (REQ-012, REQ-103).
- TLS 1.2+ in transit; KMS-managed encryption at rest (REQ-102).

## 7. Deployment Architecture

**Platform.** AWS — Fargate (services) + Lambda (webhook + cron) + Aurora Serverless v2 + ElastiCache + OpenSearch managed + S3 + QLDB + SES + Bedrock; per-environment AWS account (dev / staging / prod) under WSD organisation.

**Topology.** Per-env: 1× VPC, 2× AZ minimum; ALBs in public subnets; Fargate services in private subnets; data tier in isolated subnets with VPC endpoints to S3, KMS, SES, Bedrock. CloudFront in front of the Next.js frontend ALB and a separate distribution for static assets. Webhook receiver Lambda behind API Gateway + WAF + Confluence-IP allow-list.

### Scaling per component

| Component | min | max | Trigger |
|---|---|---|---|
| Portal Frontend | 2 | 20 | CPU > 60% or p95 latency > 1.2 s for 3 min |
| Portal API | 2 | 30 | CPU > 60% or RPS-per-task > target |
| Publishing Pipeline workers | 1 | 10 | SQS publish-queue depth > 50 or oldest message age > 60 s |
| AI Gateway | 2 | 10 | Bedrock concurrent-call gauge |
| Notification Service workers | 1 | 8 | Notification queue depth |
| Auth Service | 2 | 8 | CPU > 60% or 5xx rate > 0.5% |
| Renderer | 1 | 6 | PDF render queue depth |

### Resource requirements

| Component | CPU req | CPU lim | Mem req | Mem lim |
|---|---|---|---|---|
| Portal Frontend | 500m | 2000m | 512Mi | 2Gi |
| Portal API | 500m | 2000m | 512Mi | 2Gi |
| Publishing Pipeline worker | 500m | 2000m | 1Gi | 4Gi |
| AI Gateway | 250m | 1000m | 512Mi | 2Gi |
| Notification Service | 250m | 1000m | 512Mi | 2Gi |
| Auth Service | 500m | 1500m | 512Mi | 2Gi |
| Audit Service | 250m | 1000m | 512Mi | 2Gi |
| Renderer | 500m | 2000m | 1Gi | 4Gi |

**CI/CD.** GitHub Actions: on push → lint + typecheck + unit + integration + cross-tenant isolation suite + container image build + SBOM + Sigstore signing → CDK deploy to dev. Promotion: tag triggers staging deploy → smoke tests + synthetic load test → manual approval gate (release manager) → prod deploy with progressive rollout (10% → 50% → 100%) and automatic rollback on SLO breach. CDK app per service; one IaC repo for shared infra (VPC, ALB, RDS, OpenSearch, ElastiCache, QLDB, KMS keys, IAM roles).

## 8. Operational Concerns

### Configuration

Environment variables (selection): `DATABASE_URL`, `REDIS_URL`, `OPENSEARCH_ENDPOINT`, `S3_CONTENT_BUCKET`, `S3_PDF_BUCKET`, `QLDB_LEDGER_NAME`, `BEDROCK_MODEL_ARN`, `WORKOS_API_KEY`, `CONFLUENCE_OAUTH_CLIENT_SECRET`, `SESSION_SIGNING_KEY`, `AI_REVIEW_FAIL_CLOSED`, `ALLOW_LIST_BOOTSTRAP_S3_KEY`

**Database.** Aurora Serverless v2: minACU 0.5 dev / 2 staging / 8 prod; maxACU 4 / 16 / 64; storage encryption with KMS; automated snapshot retention 35 days.

**Feature flags:**
- ai_release_notes_enabled (default on)
- ai_quality_score_enabled (default on; soft warning only)
- ai_since_last_visit_enabled (default on)
- sso_enabled_per_tenant (per-tenant)
- ai_review_fail_closed (default on in prod, override forbidden in prod)

### Health checks

- `/health/live` — Liveness — process is responding — checks: process is up, config loaded
- `/health/ready` — Readiness — dependencies reachable — checks: Aurora reachable, Redis reachable, downstream service reachable (per service)
- `/health/ai` — AI Gateway only — Bedrock connectivity probe (no model call) — checks: Bedrock client constructable, configured model ARN exists

### Logging

**Destination.** Amazon CloudWatch Logs (per-service log group) + S3 long-term archive (1 yr) via Kinesis Firehose; tracked queries in QLDB for audit events.

**Retention.** CloudWatch: 30 days hot; Firehose-to-S3 with object-lock: 1 year. Audit events in QLDB ≥ 12 months then archived.

**Key events.**

| Event | Level | Trigger | Fields |
|---|---|---|---|
| `publish.complete` | info | Publishing Pipeline persisted a version | document_id, version_id, duration_ms, ai_review_findings, tenant_scope |
| `publish.failed` | error | Publishing Pipeline failed at any stage | document_id, stage, reason, retry_count |
| `ai.provider_unavailable` | error | AI Gateway returned fail-closed | operation, provider, duration_ms, error_class |
| `auth.login.success` | info | Successful login | user_id, tenant_id, factor, ip, ua |
| `auth.login.failure` | warn | Failed login | user_id_or_email_hash, tenant_id, reason, ip |
| `audit.integrity_check` | info | Daily QLDB digest verification | verified_at, digest_match, anomalies |

### Metrics & alerts

| Metric | Type | Description | Alert |
|---|---|---|---|
| `sync.approval_to_portal_seconds` | histogram | End-to-end sync latency | p95 > 300s for 15m → page |
| `sync.ai_review_seconds` | histogram | AI review pass duration | p95 > 30s for 15m → warn |
| `publish.success_total` | counter | Successful publishes | rate-of-change < expected → warn |
| `publish.failed_total` | counter | Failed publishes by stage | any > 5/min → page |
| `ai.provider_unavailable_total` | counter | Fail-closed events | any > 0 sustained 5m → page |
| `portal.render_seconds` | histogram | Portal page render | p95 > 1.5s for 15m → page |
| `search.query_seconds` | histogram | Search query latency | p95 > 1s for 15m → warn |
| `auth.lockouts_total` | counter | Account lockouts | rate > 10/min → security |
| `tenancy.cross_tenant_test_pass` | gauge | 1 if last cross-tenant test passed, 0 otherwise | value = 0 → page |

**Tracing.** AWS X-Ray with OpenTelemetry-compatible SDK; propagation via W3C traceparent header; context: Inbound HTTP → x-request-id + traceparent; propagated across SQS, EventBridge, and Bedrock SDK calls; persisted in audit-event payloads for correlation.

**Alerting channels.** PagerDuty (services), Slack #docs-hub-alerts (warnings), Email security@wsd.com (security-only)

**Critical alerts.**
- ai.provider_unavailable_total sustained — fail-closed in effect, publishes halted
- sync.approval_to_portal_seconds p95 > 300s — SLA breach
- publish.failed_total > 5/min — pipeline degradation
- auth.lockouts_total > 10/min — possible credential stuffing
- tenancy.cross_tenant_test_pass = 0 — isolation regression — block deploys
- audit.integrity_check digest_match = false — tampering or corruption

## 9. Architectural Decision Records

### ADR-001 — Anthropic Claude via Amazon Bedrock (vs direct Anthropic API)
**Status.** accepted

**Context.** All AI functions need a high-quality LLM. The two realistic paths are direct Anthropic API and Claude via Amazon Bedrock. Both expose comparable model capability; the decision is operational.

**Options considered.**
- **Direct Anthropic API**
  - Pros: Newer model availability sometimes lands earlier; Simpler SDK
  - Cons: Public-internet egress for AI traffic; additional network boundary to audit; Separate billing relationship outside AWS; Harder to enforce 'no-cross-network leakage' guarantees
- **Amazon Bedrock InvokeModel**
  - Pros: VPC endpoint — AI traffic never leaves AWS network; Unified IAM / KMS / CloudWatch / billing; Tooling consistency with the rest of the stack; Easier audit story
  - Cons: Bedrock model versions can lag Anthropic releases by days–weeks; Slightly higher per-token cost

**Decision.** Use Amazon Bedrock InvokeModel for all Claude calls. Confine all AI traffic to a Bedrock VPC endpoint; no direct internet AI egress.

**Rationale.** The single-network-egress posture materially simplifies the security story for a client-data-handling system, and the AWS-native IAM/audit story outweighs the model-version-lag cost.

**Consequences.**
- AI Gateway only talks to Bedrock; provider abstraction is preserved so we can revisit if Bedrock lag becomes painful.
- Model upgrade requires a Bedrock model availability check first.
- All AI prompt+response audit lives within AWS — easier compliance review.

**Related REQs.** REQ-040, REQ-050, REQ-105
**Related decisions.** ADR-007

### ADR-002 — Multi-tenant PostgreSQL via tenant_id + RLS (vs schema-per-tenant or DB-per-tenant)
**Status.** accepted

**Context.** Tenant isolation must be enforced below the UI. The standard options are: tenant_id column with RLS, schema-per-tenant, or database-per-tenant.

**Options considered.**
- **tenant_id + Row-Level Security**
  - Pros: Operational simplicity; Cross-tenant analytics easy when needed; Single migration surface
  - Cons: RLS bypass risk if a query forgets to set the session var; Noisy-neighbour for query plans across tenants
- **Schema-per-tenant**
  - Pros: Hard logical boundary inside one DB; Per-tenant ALTER TABLE easier
  - Cons: Migration of N tenants is N× the work; Connection pool sizing complex; Search index still needs tenant filter
- **Database-per-tenant**
  - Pros: Strongest isolation; Per-tenant backup/restore
  - Cons: Operationally expensive (N RDS clusters); Cross-tenant features impossible; Slow client onboarding

**Decision.** tenant_id column on every tenant-scoped table with PostgreSQL Row-Level Security policies. A tenant-bound connection wrapper sets app.tenant_id at session start; queries without it are blocked by RLS.

**Rationale.** RLS + a single audit-able connection wrapper gives us hard data-layer enforcement while keeping operational cost linear, not multiplicative. We pair this with an automated cross-tenant CI test for defence-in-depth.

**Consequences.**
- Every read/write helper must use the tenant-bound connection; lint rule + code review enforce.
- Cross-tenant CI test failure blocks every deploy.
- If a future tenant requires strong physical isolation, we can move them to their own database without changing the application data model.

**Related REQs.** REQ-012, REQ-103
**Related decisions.** ADR-006

### ADR-003 — QLDB for tamper-evident audit (vs append-only PostgreSQL + signed log)
**Status.** accepted

**Context.** REQ-107 requires tamper-evident audit retained ≥ 12 months.

**Options considered.**
- **Amazon QLDB**
  - Pros: Cryptographic journal verification built-in; Purpose-built for this use case; Indexed query for compliance
  - Cons: Adds a managed service to operate; Schema/query model less familiar than SQL
- **Postgres append-only table + nightly signing**
  - Pros: No new infra; one less service to operate
  - Cons: Easier for a privileged DB user to silently edit; Signing is bolt-on, not built-in; Restore-from-backup path is murky for audit semantics
- **S3 object-lock + structured log**
  - Pros: Object-lock prevents deletion; Cheap
  - Cons: Query-by-actor or date-range is slow; No native digest verification — must roll our own chain

**Decision.** Use Amazon QLDB for audit. Cold-archive to S3 object-lock after 12 months for cost.

**Rationale.** Built-in cryptographic verification is the strongest control and the cheapest to defend in a compliance review.

**Consequences.**
- Audit Service is a small standalone service that owns the QLDB integration.
- Daily integrity job verifies the digest; any failure pages security.
- Cold archive workflow handled by an EventBridge schedule.

**Related REQs.** REQ-016, REQ-107

### ADR-004 — Next.js (App Router) for the portal frontend (vs static SPA)
**Status.** accepted

**Context.** The portal is documentation-heavy and read-dominant. Server-side rendering vs SPA has implications for latency, search, and accessibility.

**Options considered.**
- **Next.js 15 App Router with React Server Components**
  - Pros: Fast first contentful paint; Strong accessibility defaults; Per-tenant cache key at the edge via middleware; Co-located React SSR for the AI summary block
  - Cons: More moving parts than a static SPA; RSC learning curve
- **Static SPA (Vite + React)**
  - Pros: Operationally minimal; Easy to host
  - Cons: Worse initial paint; Worse a11y unless extra care; Per-tenant cache hard to get right at the edge; Need a separate read API anyway
- **Server-rendered Lit / web components**
  - Pros: Consistent with the existing WAIF stack
  - Cons: Smaller ecosystem for SSR; Internal team less experienced with deep SSR in Lit

**Decision.** Next.js 15 App Router with React Server Components, deployed on Fargate behind CloudFront with a Lambda@Edge middleware that derives the cache key from the session-bound tenant ID.

**Rationale.** The portal's read-dominant, accessibility-mandated workload is exactly Next.js's sweet spot. Per-tenant cache key at the edge is the critical safety feature that closes the cross-tenant CDN risk.

**Consequences.**
- We accept a heavier ops surface than a pure SPA.
- Per-tenant cache-key in Lambda@Edge is a critical security control and must be tested.
- The Admin UI also uses Next.js for stack consistency.

**Related REQs.** REQ-020, REQ-021, REQ-100, REQ-104

### ADR-005 — Webhook-driven sync with polling fallback (vs polling-only)
**Status.** accepted

**Context.** The 5-minute SLA in REQ-NFR-002 can be hit by either pattern, but each has different failure modes.

**Options considered.**
- **Webhook + polling fallback**
  - Pros: Lowest latency under steady state; Polling backs up missed events; Resilient to webhook delivery outages
  - Cons: Two code paths to maintain; Webhook receiver requires public ingress with HMAC + IP allow-list
- **Polling-only**
  - Pros: Single code path; No public ingress required
  - Cons: Floor latency = polling interval; lower interval drives Confluence API cost; Less suited to bursty publishing days

**Decision.** Webhook-driven, with a polling fallback triggered when webhooks have been silent for longer than a configurable threshold (default 5 min). The polling cursor is in Postgres.

**Rationale.** Steady-state latency target is best met by webhooks; reliability is best met by polling. The combination satisfies both at the cost of one extra code path.

**Consequences.**
- Webhook receiver runs as Lambda behind API Gateway with HMAC + Confluence IP allow-list.
- Polling Fargate task fires on EventBridge schedule with a backoff.
- Both paths converge on the same SQS publish-queue, so downstream code only sees one event type.

**Related REQs.** REQ-003

### ADR-006 — Immutable content blobs in S3 with Object Lock (vs in-DB CLOBs)
**Status.** accepted

**Context.** Each published page version has rendered HTML and an original Confluence storage-format snapshot. Two natural homes: Postgres CLOB columns or S3 objects.

**Options considered.**
- **S3 object-lock with versioning**
  - Pros: Built-in immutability via Object Lock; Cheap at scale; Lifecycle to IA for cold versions; Decoupled from DB row size
  - Cons: Two systems to reason about; Slightly more code for read path
- **Postgres CLOB**
  - Pros: Single store; transactional consistency with metadata
  - Cons: Bloats DB size and backup time; No native immutability; More expensive per GB

**Decision.** Rendered HTML and Confluence storage snapshot go to S3 with Object Lock (compliance mode for the snapshot, governance mode for the HTML). Postgres holds only the metadata row plus the S3 key.

**Rationale.** Immutability is a first-class requirement; S3 Object Lock is the cheapest and strongest way to enforce it. Decoupling blobs from the metadata DB also keeps DB performance predictable as the catalog grows.

**Consequences.**
- Publish step is a CAS write to S3 (with If-None-Match) plus a Postgres insert; both are required.
- Garbage collection of versions beyond 20 is a metadata-only operation; the S3 blobs lifecycle to IA but never delete during the retention window.
- PDF blobs live in a separate bucket with a TTL of 30 days; regenerated on demand if stale.

**Related REQs.** REQ-004, REQ-005, REQ-023

### ADR-007 — AI review fail-closed via queue + alert (vs fail-open with warning)
**Status.** accepted

**Context.** REQ-105 requires fail-closed. The decision is how the fail-closed state is presented operationally.

**Options considered.**
- **Halt publish; queue page in 'review-pending-provider'; alert security + on-call**
  - Pros: Strong guarantee; Clear operational signal; Backlog drains naturally when provider returns
  - Cons: Publish backlog grows during outages
- **Halt publish; surface an actionable banner to doc owners with a documented break-glass procedure**
  - Pros: Doc owners know what to do; Backlog visible to humans
  - Cons: Tempting to bypass
- **Fail-open with reviewer warning**
  - Pros: No publish backlog
  - Cons: Violates REQ-105; Catastrophic if the bypass becomes the default during an outage

**Decision.** Halt the publish; queue the page in 'review-pending-provider'; emit ai-review-pending-provider on EventBridge; show a clear banner in Admin UI; alert on-call. Bypass requires a documented two-person break-glass procedure with QLDB-audited justification, and is forbidden in prod by default config.

**Rationale.** REQ-105 makes fail-closed non-negotiable. Pairing it with clear operational visibility and an explicit (audited) break-glass path gives security teeth and operators a clear UX.

**Consequences.**
- An AI Bedrock outage stops publishes; SLA dashboards reflect this honestly.
- Two-person break-glass procedure exists, is documented, and rarely used.
- We monitor the break-glass usage as a counter metric.

**Related REQs.** REQ-040, REQ-041, REQ-105
**Related decisions.** ADR-001

### ADR-008 — Per-page on-demand PDF (vs per-version pre-rendered)
**Status.** accepted

**Context.** REQ-023 requires PDF download. Two extremes are 'render on every read' and 'pre-render every version'.

**Options considered.**
- **On-demand with 30-day cache**
  - Pros: No storage for unread versions; Renderer can include current user identity in footer for audit
  - Cons: First click for a given (version, requester) costs a render
- **Pre-render every version at publish**
  - Pros: Instant download
  - Cons: Renders we never serve; Footer cannot carry per-requester identity unless we render per-user

**Decision.** On-demand render with a 30-day TTL cache. Footer includes the requesting user's tenant identity (not username) for audit traceability.

**Rationale.** Reading is the dominant access pattern, not PDF download; pre-rendering would waste storage. The 30-day cache absorbs hotspots.

**Consequences.**
- Renderer service must be horizontally scalable for bursts.
- PDF bucket lifecycle: 30 days hot, then delete; regenerated if requested.
- Audit footer renders client tenant + version + timestamp; never embeds username.

**Related REQs.** REQ-023

### ADR-009 — WorkOS for enterprise SSO (vs Keycloak self-hosted vs Auth0)
**Status.** accepted

**Context.** Some launch clients require SAML 2.0 / OIDC SSO (REQ-015). We need a mediator that can host per-tenant connections without us writing SAML directly.

**Options considered.**
- **WorkOS**
  - Pros: Built specifically for B2B per-tenant SSO; Connection setup UX is good for client admins; No SAML library in our codebase
  - Cons: External dependency; Per-active-connection pricing
- **Keycloak self-hosted**
  - Pros: No vendor lock-in; No per-connection cost
  - Cons: Operational burden of running an identity server; Per-tenant configuration UX falls to us
- **Auth0**
  - Pros: Mature; Broad ecosystem
  - Cons: Heavier than we need for SSO-only; Pricing

**Decision.** WorkOS for SAML 2.0 / OIDC mediation. Password+TOTP login remains in-house. Per-tenant SSO mode is a Tenant.sso_mode flag.

**Rationale.** WorkOS's product surface is exactly the per-tenant-SSO problem; we get a clean UX and avoid hosting SAML primitives. The dependency is well-bounded — it only mediates SSO and is feature-flagged per tenant.

**Consequences.**
- Auth Service has two login paths; per-tenant flag selects.
- WorkOS is in the critical path only for SSO-enabled tenants; password+TOTP tenants are unaffected by WorkOS outage.
- We monitor WorkOS health as a dedicated SLO.

**Related REQs.** REQ-015

### ADR-010 — Step Functions for the publishing pipeline (vs in-process worker)
**Status.** accepted

**Context.** The publishing pipeline has 5+ retriable stages (allow-list, approval, AI review, render, persist, index, cache invalidate, notify). The orchestration choice affects visibility and retry semantics.

**Options considered.**
- **AWS Step Functions Standard**
  - Pros: Visual workflow + per-step audit; Retry/visibility per step; Free-tier covers small volumes
  - Cons: State-machine JSON to maintain; Cost scales with volume
- **In-process worker with per-stage try/retry**
  - Pros: Single deployable; No state-machine spec
  - Cons: Per-step visibility is logs-only; Retry semantics live in code

**Decision.** AWS Step Functions Standard for the publishing pipeline; the worker code per stage is a Fargate task or Lambda.

**Rationale.** The per-step visibility and retry semantics are worth the orchestration cost; SLA debugging is materially easier with a state-machine view.

**Consequences.**
- Each stage is a distinct Lambda or Fargate task with a clear input/output schema.
- Step Functions JSON spec lives in the publishing service repo and is reviewed alongside code changes.
- Per-stage metrics emit automatically; alerting is per-stage.

**Related REQs.** REQ-003, REQ-040, REQ-101

