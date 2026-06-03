#!/usr/bin/env python3
"""
One-shot generator for the PRD-001 TAD.

Emits:
  - docs/specs/client-docs-hub/tad/TAD.md   (human-readable single document)
  - docs/specs/client-docs-hub/tad/TAD-001-001.json  (overview & principles + extractedConcerns)
  - docs/specs/client-docs-hub/tad/TAD-001-002.json  (components)
  - docs/specs/client-docs-hub/tad/TAD-001-003.json  (data + integration)
  - docs/specs/client-docs-hub/tad/TAD-001-004.json  (security + deployment + ops + ADRs)
  - updates docs/specs/client-docs-hub/manifest.json
"""

from __future__ import annotations
import json
import re
from datetime import datetime, timezone
from pathlib import Path

PRD_ID = "PRD-001"
TAD_VERSION = "1.0.0"
REPO = Path(__file__).resolve().parent.parent
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# ---------------------------------------------------------------------------
# Read upstream artifacts
# ---------------------------------------------------------------------------
prd = json.loads((REPO / "docs/specs/client-docs-hub/prd/PRD-001.json").read_text())
stories_doc = json.loads((REPO / "docs/specs/client-docs-hub/user-stories/PRD-001-user-stories.json").read_text())

# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------

SYSTEM_OVERVIEW = {
    "executiveSummary": (
        "Client Documentation Hub is a multi-tenant, AI-assisted, read-only publishing portal that mirrors approved "
        "Confluence pages to docs.wsd.com under per-client access control. The system is composed of seven domain "
        "services running on AWS Fargate behind an API Gateway, fronted by a Next.js Server-Components frontend on "
        "CloudFront, with Aurora PostgreSQL as the system of record, OpenSearch for scoped search, ElastiCache Redis "
        "for read caching and sessions, S3 for immutable content blobs plus on-demand PDFs, QLDB for tamper-evident "
        "audit, Anthropic Claude via Amazon Bedrock for every AI function (pre-publish review, release notes, "
        "summaries, notification copy, quality scoring), SES for transactional email, and WorkOS for enterprise SSO. "
        "Confluence remains the single source of truth: the Hub is strictly read-replica with a webhook-driven sync "
        "pipeline (5-minute SLA at p95) and a polling fallback."
    ),
    "systemPurpose": (
        "Replace manual PDF distribution and unscalable Confluence guest access with a secure, auditable, AI-gated "
        "client documentation portal that publishes the latest approved Confluence content in near real-time, "
        "isolates per-client and shared content, and uses AI to screen sensitive material before publish and to "
        "generate release notes and notification copy after publish."
    ),
    "architecturalApproach": (
        "Service-oriented, multi-tenant SaaS on AWS. Confluence is the upstream authoring source; the Hub ingests "
        "approved pages via a webhook receiver (Lambda) plus a polling fallback (Fargate cron job), runs an AI "
        "review pipeline that fails closed on any provider error, and persists immutable per-page version records "
        "in S3 with relational metadata in Aurora. Read traffic is served by a Next.js frontend with React Server "
        "Components rendered on Fargate and aggressively cached at CloudFront and Redis. Cross-cutting concerns "
        "(authentication, tenant scoping, audit) are enforced at the data-access layer and validated by an "
        "automated isolation test suite on every release. AI behaviour is mediated through one internal AI gateway "
        "service so provider, model, and fail-closed semantics can be controlled in one place."
    ),
    "keyCapabilities": [
        "Webhook-driven and polling-fallback Confluence sync with p95 < 5 min approval-to-portal latency",
        "Pre-publish AI document review (secrets, internal URLs, internal tickets, internal emails, missing content) with hard block on high-severity findings",
        "Immutable per-page version history with on-demand PDF rendering",
        "Per-tenant authentication (password + TOTP and optional SAML/OIDC SSO via WorkOS), per-tenant access scoping enforced at the data-access layer",
        "AI-generated release notes (What's New / Breaking / Recommended) and per-client 'Since your last visit' summaries, gated by reviewer approval",
        "Scoped full-text search with tenant isolation guarantees",
        "Tamper-evident audit (auth, view, admin, AI review decisions) on QLDB with ≥ 12-month retention",
        "Email notifications via SES with per-user cadence preferences and AI-authored per-page summaries",
    ],
    "externalDependencies": [
        {"system": "Confluence (WSD instance)", "purpose": "Source of truth for all documentation; provides REST + change-event webhooks", "protocol": "HTTPS REST + webhook", "owner": "WSD Platform / Atlassian"},
        {"system": "Amazon Bedrock (Anthropic Claude)", "purpose": "All AI functions: review, release notes, summaries, notification copy, quality scoring", "protocol": "AWS SDK (HTTPS)", "owner": "AWS"},
        {"system": "Amazon SES", "purpose": "Transactional email delivery for notifications", "protocol": "AWS SDK (HTTPS) / SMTP", "owner": "AWS"},
        {"system": "WorkOS", "purpose": "Per-tenant SAML 2.0 / OIDC SSO mediation", "protocol": "HTTPS REST + SAML/OIDC", "owner": "WorkOS"},
        {"system": "Atlassian Confluence webhook delivery", "purpose": "Push notification of page changes", "protocol": "HTTPS POST", "owner": "Atlassian"},
        {"system": "Amazon CloudFront", "purpose": "Edge CDN in front of Next.js frontend", "protocol": "HTTPS", "owner": "AWS"},
        {"system": "Amazon QLDB", "purpose": "Tamper-evident audit log storage", "protocol": "AWS SDK (HTTPS)", "owner": "AWS"},
    ],
    "assumptionsAndConstraints": [
        "AWS account and platform-standard CDK/Terraform tooling are in place; deployment uses platform-supplied account structure (per-env accounts).",
        "Confluence webhooks are reachable from a public Lambda endpoint behind WAF; if not, sync degrades to polling only and the latency SLA must be relaxed.",
        "Anthropic Claude is accessed exclusively via Amazon Bedrock; direct Anthropic API access is not used (single network egress boundary for security + audit).",
        "WSD's identity directory provides the initial WSD-operator accounts; client tenants are operator-provisioned in v1.",
        "Email deliverability is DMARC-aligned for docs.wsd.com; DNS is owned by the marketing team and provisioned ahead of launch.",
        "AI provider failure is non-bypassable: the review pipeline fails closed, which means an AI outage stops publishes. This is an intentional trade-off (REQ-105).",
    ],
}

PRINCIPLES = [
    {
        "name": "Confluence is the single source of truth",
        "description": "The Hub is read-replica with respect to Confluence. No content is authored or edited inside the Hub; portal users cannot mutate documentation.",
        "rationale": "Eliminates dual-write reconciliation, preserves the existing author workflow, and keeps governance/compliance audit anchored in Confluence's history.",
        "implications": [
            "No portal-side editor or comment surface; client feedback is out of scope for v1.",
            "Two-way sync is explicitly out of scope; Confluence content changes win.",
            "Recovery from corruption is a re-sync from Confluence, not a backup restore.",
        ],
        "relatedReqs": ["REQ-001", "REQ-002", "REQ-003", "REQ-005"],
    },
    {
        "name": "Fail closed on AI and on access",
        "description": "On any AI-provider failure or any access-control ambiguity, the system blocks rather than degrades-open. Publishes never proceed without a clean AI review; reads never return cross-tenant content.",
        "rationale": "Both the secret-leak and cross-tenant-leak failure modes are catastrophic; the cost of a brief publish outage is small compared to either.",
        "implications": [
            "An AI Bedrock outage halts publishes until cleared.",
            "Every tenant-scoped query is rejected at the data-access layer unless an active tenant is bound to the session.",
            "Break-glass procedures for bypassing AI review require two-person approval and audit.",
        ],
        "relatedReqs": ["REQ-040", "REQ-041", "REQ-105", "REQ-103", "REQ-012"],
    },
    {
        "name": "Tenant isolation at the data layer, not the UI",
        "description": "All cross-tenant safety is enforced inside the data-access layer (PostgreSQL row-level security + tenant-bound query helpers, plus search-index tenant filters that are non-overridable).",
        "rationale": "UI-only filtering inevitably regresses; only data-layer enforcement survives refactors and accidental endpoint additions.",
        "implications": [
            "All Postgres reads/writes use a tenant-bound connection or an explicit shared-scope helper.",
            "OpenSearch queries always inject the tenant filter at the gateway, not at the caller.",
            "An automated cross-tenant isolation suite runs on every release; failures block deploy.",
        ],
        "relatedReqs": ["REQ-012", "REQ-013", "REQ-024", "REQ-103"],
    },
    {
        "name": "Immutable versions and append-only audit",
        "description": "Published page versions are immutable; the audit log is append-only and tamper-evident.",
        "rationale": "Lets security and clients answer 'who saw what when?' with confidence; underpins the compliance story.",
        "implications": [
            "Version records are written to S3 with object-lock; the metadata row in Postgres is referenced by version_id but the binary blob cannot be overwritten.",
            "Audit lives in QLDB; integrity is verified daily and on demand.",
            "Garbage collection of retired versions (oldest beyond 20) writes a metadata-preserved tombstone, never an in-place delete.",
        ],
        "relatedReqs": ["REQ-004", "REQ-016", "REQ-107"],
    },
    {
        "name": "AI is mediated by a single internal gateway",
        "description": "All AI calls (review, release notes, summaries, notifications, quality scoring) go through one AI Gateway service. Callers never speak Bedrock directly.",
        "rationale": "Centralises fail-closed semantics, prompt versioning, audit, token accounting, and provider/model swaps without touching every call site.",
        "implications": [
            "One choke point for AI provider outages — easier to alert, retry, and circuit-break.",
            "One place to enforce 'never log raw page content with secrets in plaintext' on AI request/response.",
            "Provider/model swap (e.g. Claude version bump) requires no change to caller code.",
        ],
        "relatedReqs": ["REQ-040", "REQ-050", "REQ-051", "REQ-053", "REQ-054", "REQ-105"],
    },
    {
        "name": "Idempotent, retry-safe pipelines",
        "description": "Every async stage (webhook receipt, AI review, persist, notification) is idempotent and re-runnable. Steps key off Confluence version IDs and per-step run IDs.",
        "rationale": "Confluence retries webhooks; AWS retries Lambdas; networks are unreliable. The cheapest defence is to make every step safe to repeat.",
        "implications": [
            "Webhook receiver deduplicates by (page_id, source_version_id).",
            "Persist step is a CAS on (page_id, source_version_id) — second writer is a no-op.",
            "Notification batch assembly uses a per-user 'last notified high-water mark' so re-runs don't duplicate emails.",
        ],
        "relatedReqs": ["REQ-003", "REQ-030", "REQ-103"],
    },
    {
        "name": "Observability is a product feature",
        "description": "Sync latency, AI review duration, publish success rate, cross-tenant isolation test outcomes, and AI-fail-closed events are all first-class metrics with alerts and dashboards from day one.",
        "rationale": "The SLAs in REQ-NFR-001..107 are only credible if they're measured continuously; reactive monitoring is too late.",
        "implications": [
            "Each service exports a standard set of histograms and counters (e.g. publish_latency_seconds, ai_review_failures_total).",
            "CloudWatch Synthetics probe the user-visible flows (login, browse, read, download PDF, search) every 60 s.",
            "PagerDuty alert rules version-controlled in the same repo as the services.",
        ],
        "relatedReqs": ["REQ-100", "REQ-101", "REQ-105"],
    },
]

COMPONENTS = [
    {
        "name": "Sync Service (Confluence ingestion)",
        "purpose": "Receive Confluence webhook events and run a polling fallback; emit one canonicalised 'page-change' event per (page, source-version) onto the publishing pipeline.",
        "location": "services/sync (Fargate workers) + lambda/webhook-receiver (Lambda)",
        "dependencies": ["Confluence REST API", "EventBridge", "SQS publish-queue", "Aurora PostgreSQL (sync_cursor table)"],
        "keyPatterns": [
            "Webhook deduplication keyed on (page_id, source_version_id)",
            "Polling fallback with a cursor stored in Postgres, triggered by EventBridge schedule",
            "Backoff-on-failure with DLQ for poison events",
        ],
        "interfaces": [
            {"name": "POST /webhooks/confluence", "type": "api", "description": "Confluence change webhook receiver; HMAC-verifies the payload and enqueues to SQS."},
            {"name": "page-change SQS message", "type": "event", "description": "Canonical change event consumed by the Publishing Pipeline."},
            {"name": "internal: sync-cursor reader", "type": "internal", "description": "Used by the polling-fallback Fargate task to resume after restart."},
        ],
        "responsibilities": [
            "Verify webhook authenticity and parse Confluence event payloads.",
            "Filter on allow-list (label + space) before forwarding.",
            "Run a periodic poll if webhooks haven't fired in N minutes.",
            "Dedupe duplicate change events.",
        ],
        "relatedReqs": ["REQ-001", "REQ-002", "REQ-003"],
    },
    {
        "name": "Publishing Pipeline",
        "purpose": "Orchestrate the per-page-change flow: allow-list filter → approval-state check → AI review → render → persist version → invalidate caches → enqueue notification.",
        "location": "services/publishing (Fargate workers, Temporal-style state machine via AWS Step Functions)",
        "dependencies": ["SQS publish-queue", "AI Gateway", "Renderer", "Aurora PostgreSQL (document_versions)", "S3 (content blobs)", "OpenSearch (index updates)", "Redis (cache invalidation)", "SQS notify-queue"],
        "keyPatterns": [
            "Step-Functions state machine for retry/visibility",
            "CAS-on-insert for version persistence (idempotent under retry)",
            "Fail-closed on AI Gateway error",
        ],
        "interfaces": [
            {"name": "consume page-change", "type": "event", "description": "Reads page-change events from SQS."},
            {"name": "emit publish-complete", "type": "event", "description": "Emitted on EventBridge for downstream consumers (notifications, audit)."},
            {"name": "internal: persist version", "type": "internal", "description": "Writes immutable version blob to S3 and metadata row to Postgres."},
        ],
        "responsibilities": [
            "Apply the configured approval-state rule.",
            "Call the AI Gateway for document review; halt on high-severity finding.",
            "Render Confluence storage format to portable HTML with cross-link rewriting.",
            "Persist version metadata + blob; update OpenSearch index; invalidate Redis cache.",
            "Enqueue notification job once publish succeeds.",
        ],
        "relatedReqs": ["REQ-002", "REQ-004", "REQ-005", "REQ-040", "REQ-041", "REQ-105"],
    },
    {
        "name": "AI Gateway",
        "purpose": "Single mediation surface for every AI call. Owns prompt templates, model selection, fail-closed semantics, audit, and token accounting.",
        "location": "services/ai-gateway (Fargate)",
        "dependencies": ["Amazon Bedrock (Anthropic Claude models)", "Postgres (prompt-version registry, AI-call audit)", "QLDB (decision audit)"],
        "keyPatterns": [
            "One narrow tool-shaped operation per AI function (review_page, release_notes, since_last_visit, notification_summary, quality_score)",
            "Per-operation circuit breaker with fail-closed default",
            "Prompt-version stamped on every output for reproducibility",
        ],
        "interfaces": [
            {"name": "POST /ai/review", "type": "api", "description": "Document review request; returns findings list or 'provider-unavailable' on failure."},
            {"name": "POST /ai/release-notes", "type": "api", "description": "Release notes generation; returns three-section draft."},
            {"name": "POST /ai/summary", "type": "api", "description": "Generates 'Since your last visit' or per-page notification summaries."},
            {"name": "POST /ai/quality", "type": "api", "description": "Quality scoring (completeness, readability, missing examples, missing API responses)."},
        ],
        "responsibilities": [
            "Build prompts from versioned templates; never inline page content into logs.",
            "Call Amazon Bedrock with the configured Claude model.",
            "Apply the per-operation timeout, retry, and circuit-breaker.",
            "Return a structured 'fail-closed' error if the provider is unavailable or the response fails schema validation.",
        ],
        "relatedReqs": ["REQ-040", "REQ-050", "REQ-051", "REQ-053", "REQ-054", "REQ-105"],
    },
    {
        "name": "Portal API",
        "purpose": "All authenticated read endpoints for the client portal: browse, read, version history, diff, PDF, search, notification preferences.",
        "location": "services/portal-api (Fargate, Node.js + Fastify)",
        "dependencies": ["Aurora PostgreSQL (read replicas)", "OpenSearch", "S3 (content blobs and PDFs)", "Redis (sessions, last-visited, render cache)"],
        "keyPatterns": [
            "Every request bound to a tenant via session middleware; data-layer rejects untenanted queries",
            "Read-through cache on Redis for hot document versions",
            "Pre-signed S3 URLs for PDF download",
        ],
        "interfaces": [
            {"name": "GET /api/v1/products", "type": "api", "description": "Tenant-scoped product/category navigation."},
            {"name": "GET /api/v1/pages/:id/version/:version", "type": "api", "description": "Read a specific version (latest by default)."},
            {"name": "GET /api/v1/pages/:id/diff", "type": "api", "description": "Compute a block-level diff between two versions."},
            {"name": "GET /api/v1/pages/:id/pdf", "type": "api", "description": "Generate or fetch a PDF for the requested version."},
            {"name": "GET /api/v1/search", "type": "api", "description": "Tenant-scoped full-text search."},
        ],
        "responsibilities": [
            "Authn/authz enforcement via Auth Service-issued session tokens.",
            "Compose read responses from Postgres metadata + S3 content + OpenSearch results.",
            "Track per-user last-visited timestamps in Redis (write-behind to Postgres).",
            "Render PDFs on demand via the PDF renderer worker.",
        ],
        "relatedReqs": ["REQ-012", "REQ-020", "REQ-021", "REQ-022", "REQ-023", "REQ-024", "REQ-025", "REQ-100", "REQ-103"],
    },
    {
        "name": "Portal Frontend (Next.js)",
        "purpose": "Server-rendered client portal at docs.wsd.com — browse, read, version history, search, PDF download, preferences.",
        "location": "apps/portal (Next.js 15 App Router on Fargate)",
        "dependencies": ["Portal API", "Auth Service (session cookies)", "CloudFront (CDN)"],
        "keyPatterns": [
            "React Server Components for primary read paths (no client JS for static content)",
            "ISR (Incremental Static Regeneration) for browse navigation with per-tenant cache key",
            "Accessibility-first component library (WCAG 2.1 AA)",
        ],
        "interfaces": [
            {"name": "HTTPS routes (/, /products, /pages/:id, /search, /preferences)", "type": "api", "description": "User-facing routes; all gated by session middleware."},
            {"name": "Server Action: 'mark visited'", "type": "internal", "description": "Server-side mutation that updates per-user last-visited via Portal API."},
        ],
        "responsibilities": [
            "Render the portal UX server-side, hydrating only interactive widgets.",
            "Enforce session presence at edge middleware; redirect to Auth Service login on absence.",
            "Embed AI-generated 'Since your last visit' summary on the landing page.",
            "Drive accessibility (keyboard, screen reader, contrast).",
        ],
        "relatedReqs": ["REQ-010", "REQ-020", "REQ-021", "REQ-025", "REQ-051", "REQ-100", "REQ-104"],
    },
    {
        "name": "Auth Service",
        "purpose": "Login (password + TOTP), session management, optional SAML/OIDC SSO via WorkOS, password-reset, lockout, client-admin user lifecycle.",
        "location": "services/auth (Fargate)",
        "dependencies": ["Aurora PostgreSQL (users, tenants, sessions)", "Redis (active sessions, rate limits)", "WorkOS (per-tenant SSO mediation)", "SES (password-reset, invitation emails)"],
        "keyPatterns": [
            "Argon2id password hashes; TOTP secret encrypted with KMS-bound DEK",
            "Per-tenant SSO mode flag; password login disabled when SSO is enabled",
            "Token-bound CSRF for cookie-auth endpoints",
        ],
        "interfaces": [
            {"name": "POST /auth/login", "type": "api", "description": "Password + TOTP login."},
            {"name": "POST /auth/sso/callback", "type": "api", "description": "WorkOS SAML/OIDC callback handler."},
            {"name": "POST /auth/users/invite", "type": "api", "description": "Client-admin invitation flow."},
            {"name": "POST /auth/logout", "type": "api", "description": "Idempotent logout (clears session in Redis + Postgres + cookie)."},
        ],
        "responsibilities": [
            "Authenticate users and establish/destroy sessions.",
            "Enforce rate limits and account lockouts.",
            "Mediate WorkOS SSO for tenants configured for SAML/OIDC.",
            "Manage tenant-scoped user lifecycle (invite/disable/remove) for client-admins.",
        ],
        "relatedReqs": ["REQ-010", "REQ-011", "REQ-014", "REQ-015"],
    },
    {
        "name": "Notification Service",
        "purpose": "Assemble per-user digest emails (cadence-aware, scope-respecting), generate AI summaries via the AI Gateway, send via SES, honour per-user preferences and reviewer approval for breaking changes.",
        "location": "services/notifications (Fargate workers + EventBridge schedules)",
        "dependencies": ["Aurora PostgreSQL (subscriptions, preferences, send-watermarks)", "AI Gateway", "SES", "EventBridge"],
        "keyPatterns": [
            "Per-user 'last notified high-water mark' for idempotent re-runs",
            "Breaking-change emails sit in 'pending-review' state until approved",
            "One-click unsubscribe links signed with a per-user HMAC",
        ],
        "interfaces": [
            {"name": "consume publish-complete", "type": "event", "description": "Reacts to publish-complete from EventBridge."},
            {"name": "cron: cadence batches", "type": "internal", "description": "EventBridge schedules daily/weekly digest assembly."},
            {"name": "POST /notifications/preferences", "type": "api", "description": "User-facing preference updates (proxied via Portal API)."},
        ],
        "responsibilities": [
            "Compute the per-user changed-pages set respecting access scope.",
            "Generate per-page summaries via AI Gateway with fallback to title-only.",
            "Send via SES with signed unsubscribe and source = 'email-digest' tracking.",
            "Suppress sends to disabled / removed users.",
        ],
        "relatedReqs": ["REQ-030", "REQ-031", "REQ-032", "REQ-053"],
    },
    {
        "name": "Admin UI",
        "purpose": "Doc-owner and reviewer surface for sync admin, AI review triage, release-notes approval, quality scoring view, unpublish.",
        "location": "apps/admin (Next.js on Fargate, behind WSD SSO)",
        "dependencies": ["Portal API (admin endpoints)", "Auth Service (WSD-staff identity)", "AI Gateway"],
        "keyPatterns": [
            "WSD-staff-only access (separate WorkOS connection to WSD's IdP)",
            "All actions audit-logged to QLDB",
        ],
        "interfaces": [
            {"name": "HTTPS routes (/sync, /reviews, /notes, /quality)", "type": "api", "description": "Admin surfaces."},
        ],
        "responsibilities": [
            "Allow doc owners to manage allow-list, re-trigger sync, unpublish.",
            "Allow reviewers to triage AI findings, approve release notes, approve breaking-change notifications.",
            "Surface quality scores and trends per page.",
        ],
        "relatedReqs": ["REQ-006", "REQ-007", "REQ-042", "REQ-050", "REQ-052", "REQ-054", "REQ-055"],
    },
    {
        "name": "Audit Log Service",
        "purpose": "Append-only, tamper-evident audit storage and query API. Backed by QLDB.",
        "location": "services/audit (Fargate)",
        "dependencies": ["Amazon QLDB", "EventBridge (audit-event consumer)"],
        "keyPatterns": [
            "QLDB journal verification (cryptographic digest) on schedule",
            "Read API constrained to security + admin roles",
            "Retention ≥ 12 months; cold-archive to S3 with object-lock thereafter",
        ],
        "interfaces": [
            {"name": "consume audit-event", "type": "event", "description": "EventBridge audit-event consumer."},
            {"name": "GET /audit/query", "type": "api", "description": "Security/admin query API for events by actor/tenant/document/date range."},
        ],
        "responsibilities": [
            "Persist every audit-relevant event with actor, action, target, before/after, timestamp.",
            "Verify journal integrity on schedule and on demand.",
            "Serve compliance queries with SLAs.",
        ],
        "relatedReqs": ["REQ-016", "REQ-107"],
    },
    {
        "name": "Renderer",
        "purpose": "Convert Confluence storage format to portable, accessible HTML and on-demand PDF.",
        "location": "services/renderer (Fargate; Playwright-headless for PDF)",
        "dependencies": ["S3 (content blobs, PDFs)", "Postgres (link-rewrite tables)"],
        "keyPatterns": [
            "Confluence-storage → AST → portal HTML (deterministic) → PDF (Playwright)",
            "Cross-link resolution against the published-pages index",
        ],
        "interfaces": [
            {"name": "POST /render/html", "type": "internal", "description": "Called by Publishing Pipeline at persist-version time."},
            {"name": "POST /render/pdf", "type": "internal", "description": "Called by Portal API on download."},
        ],
        "responsibilities": [
            "Faithful structural rendering of headings, lists, tables, code, images.",
            "Cross-link rewriting (live vs 'not available').",
            "Add audit footer (title, version, tenant identity) to every PDF.",
        ],
        "relatedReqs": ["REQ-005", "REQ-023"],
    },
]

DATA_ARCHITECTURE = {
    "dataStores": [
        {
            "name": "Primary RDBMS",
            "technology": "Amazon Aurora PostgreSQL 15 (Serverless v2)",
            "purpose": "System of record for tenants, users, documents metadata, version index, scope mappings, sync cursors, subscriptions, AI-review decisions.",
            "dataTypes": ["tenant", "user", "session", "document", "document_version (metadata)", "scope_grant", "sync_cursor", "subscription", "ai_finding", "review_decision"],
            "accessPatterns": [
                "Row-Level Security policies bind queries to the active tenant_id",
                "Read replicas serve Portal API hot reads",
                "Primary handles writes from Publishing Pipeline + Auth + Notification",
            ],
            "scalingStrategy": "Aurora Serverless v2 ACUs scale automatically; read replicas added per environment based on load tests."
        },
        {
            "name": "Content Blob Store",
            "technology": "Amazon S3 (Object Lock enabled, versioning ON)",
            "purpose": "Immutable rendered HTML per (document, version); generated PDFs (with TTL); original Confluence storage-format snapshots for audit.",
            "dataTypes": ["html_blob", "pdf_blob", "confluence_storage_snapshot"],
            "accessPatterns": [
                "Write-once at publish time; never modified",
                "Read via pre-signed URLs (short TTL) from Portal API",
                "Lifecycle: hot bucket → IA after 90 days for older versions",
            ],
            "scalingStrategy": "S3 elastic; no operational scaling work."
        },
        {
            "name": "Search Index",
            "technology": "Amazon OpenSearch managed",
            "purpose": "Full-text search index of all published document versions, scoped per tenant via a non-overridable filter at the search-gateway.",
            "dataTypes": ["document_search_doc"],
            "accessPatterns": [
                "Index update at publish-complete event",
                "Tenant filter injected at gateway; callers cannot bypass",
                "Boosting by recency + title match",
            ],
            "scalingStrategy": "Multi-AZ with auto-tune; capacity sized per load tests; shard per tenant family."
        },
        {
            "name": "Cache + Sessions",
            "technology": "Amazon ElastiCache (Redis 7)",
            "purpose": "Active sessions, rate-limit counters, per-user last-visited, hot document version render cache.",
            "dataTypes": ["session", "rate_limit_counter", "last_visited", "render_cache_entry"],
            "accessPatterns": [
                "Sessions: read on every authenticated request",
                "Render cache: read-through; invalidation event on publish-complete",
                "Last-visited: write-behind to Postgres",
            ],
            "scalingStrategy": "Cluster mode with read replicas; sized per p95 throughput targets."
        },
        {
            "name": "Audit Ledger",
            "technology": "Amazon QLDB",
            "purpose": "Tamper-evident append-only audit log for authentication, document view, admin action, AI review decision, sync re-trigger, unpublish.",
            "dataTypes": ["audit_event"],
            "accessPatterns": [
                "Write on every audit-relevant event via Audit Service",
                "Read constrained to security + admin roles",
                "Daily integrity verification job",
            ],
            "scalingStrategy": "QLDB managed; cold-archive to S3 with Object Lock after 12 months."
        },
    ],
    "coreEntities": [
        {
            "name": "Tenant",
            "description": "An isolated client workspace. The unit of access scope and billing.",
            "fields": [
                {"name": "tenant_id", "type": "uuid", "required": True, "description": "PK; surrogate; used as RLS key everywhere."},
                {"name": "slug", "type": "text", "required": True, "description": "Human-readable identifier used in Confluence scope labels (client:<slug>)."},
                {"name": "display_name", "type": "text", "required": True, "description": "Shown in UI and email footers."},
                {"name": "sso_mode", "type": "enum (none, saml, oidc)", "required": True, "description": "Drives login dispatch."},
                {"name": "created_at", "type": "timestamptz", "required": True, "description": "Provisioning timestamp."},
            ],
            "relationships": ["1:N → User", "1:N → ScopeGrant", "1:N → Subscription"],
            "indexes": ["pk(tenant_id)", "unique(slug)"],
        },
        {
            "name": "User",
            "description": "An authenticated principal bound to one tenant.",
            "fields": [
                {"name": "user_id", "type": "uuid", "required": True, "description": "PK."},
                {"name": "tenant_id", "type": "uuid", "required": True, "description": "FK to Tenant. Sets RLS scope."},
                {"name": "email", "type": "citext", "required": True, "description": "Login identifier; unique within tenant."},
                {"name": "role", "type": "enum (reader, client_admin, wsd_doc_owner, wsd_reviewer, wsd_security)", "required": True, "description": "Authorization role."},
                {"name": "password_hash", "type": "text (argon2id)", "required": False, "description": "Null when SSO mode is active."},
                {"name": "totp_enc", "type": "bytea (KMS DEK)", "required": False, "description": "Encrypted TOTP secret."},
                {"name": "status", "type": "enum (active, disabled, removed)", "required": True, "description": "Lifecycle state."},
            ],
            "relationships": ["N:1 → Tenant"],
            "indexes": ["pk(user_id)", "unique(tenant_id, email)", "idx(status)"],
        },
        {
            "name": "Document",
            "description": "A published Confluence page. The document is the long-lived identity; versions are immutable snapshots beneath it.",
            "fields": [
                {"name": "document_id", "type": "uuid", "required": True, "description": "PK; deterministic from Confluence page ID."},
                {"name": "confluence_page_id", "type": "text", "required": True, "description": "Upstream identity."},
                {"name": "product_label", "type": "text", "required": True, "description": "Drives portal navigation grouping."},
                {"name": "category_label", "type": "text", "required": False, "description": "Sub-grouping within a product."},
                {"name": "scope_mode", "type": "enum (shared, client_specific)", "required": True, "description": "Visibility scope."},
                {"name": "current_version_id", "type": "uuid", "required": False, "description": "Pointer to the latest published version."},
                {"name": "state", "type": "enum (published, unpublished, blocked_on_review)", "required": True, "description": "Lifecycle."},
            ],
            "relationships": ["1:N → DocumentVersion", "1:N → ScopeGrant (when client_specific)"],
            "indexes": ["pk(document_id)", "unique(confluence_page_id)", "idx(state, product_label)"],
        },
        {
            "name": "DocumentVersion",
            "description": "One immutable publish of a document. Binary content lives in S3.",
            "fields": [
                {"name": "version_id", "type": "uuid", "required": True, "description": "PK."},
                {"name": "document_id", "type": "uuid", "required": True, "description": "FK → Document."},
                {"name": "source_version_id", "type": "text", "required": True, "description": "Confluence revision number."},
                {"name": "html_blob_s3_key", "type": "text", "required": True, "description": "S3 key (immutable, object-lock)."},
                {"name": "snapshot_blob_s3_key", "type": "text", "required": True, "description": "Original Confluence storage format for audit."},
                {"name": "publisher_id", "type": "uuid", "required": True, "description": "FK → User (WSD doc owner)."},
                {"name": "published_at", "type": "timestamptz", "required": True, "description": "Publish timestamp."},
                {"name": "review_decision_id", "type": "uuid", "required": True, "description": "FK → ReviewDecision."},
                {"name": "quality_scores_jsonb", "type": "jsonb", "required": False, "description": "4-dimension scores."},
            ],
            "relationships": ["N:1 → Document", "N:1 → User (publisher)", "1:N → ReleaseNotes block"],
            "indexes": ["pk(version_id)", "unique(document_id, source_version_id)", "idx(document_id, published_at DESC)"],
        },
        {
            "name": "ScopeGrant",
            "description": "Joins a client-specific document to the tenant(s) entitled to read it. Shared documents do not have ScopeGrant rows.",
            "fields": [
                {"name": "grant_id", "type": "uuid", "required": True, "description": "PK."},
                {"name": "document_id", "type": "uuid", "required": True, "description": "FK → Document."},
                {"name": "tenant_id", "type": "uuid", "required": True, "description": "FK → Tenant."},
                {"name": "granted_at", "type": "timestamptz", "required": True, "description": "Provenance timestamp."},
            ],
            "relationships": ["N:1 → Document", "N:1 → Tenant"],
            "indexes": ["pk(grant_id)", "unique(document_id, tenant_id)"],
        },
        {
            "name": "AIFinding",
            "description": "A single AI-document-review finding raised against a document version.",
            "fields": [
                {"name": "finding_id", "type": "uuid", "required": True, "description": "PK."},
                {"name": "version_id", "type": "uuid", "required": True, "description": "FK → DocumentVersion."},
                {"name": "category", "type": "enum (secret, internal_url, internal_ticket, internal_email, missing_content, empty_section, stub)", "required": True, "description": "Finding category."},
                {"name": "severity", "type": "enum (low, medium, high)", "required": True, "description": "Drives publish gating."},
                {"name": "matched_span", "type": "jsonb", "required": True, "description": "Anchor location in the rendered HTML."},
                {"name": "decision_id", "type": "uuid", "required": False, "description": "FK → ReviewDecision when triaged."},
            ],
            "relationships": ["N:1 → DocumentVersion", "N:1 → ReviewDecision (optional)"],
            "indexes": ["pk(finding_id)", "idx(version_id, severity)"],
        },
        {
            "name": "ReviewDecision",
            "description": "A reviewer triage decision on a finding or release-notes block. Audit-logged.",
            "fields": [
                {"name": "decision_id", "type": "uuid", "required": True, "description": "PK."},
                {"name": "actor_user_id", "type": "uuid", "required": True, "description": "FK → User (reviewer)."},
                {"name": "decision", "type": "enum (ignore, acknowledge, block, approve_release_notes, reject_release_notes)", "required": True, "description": "Decision verb."},
                {"name": "rationale_text", "type": "text", "required": False, "description": "Reviewer-supplied note."},
                {"name": "decided_at", "type": "timestamptz", "required": True, "description": "Timestamp."},
            ],
            "relationships": ["1:1 ← AIFinding (when triaging a finding)"],
            "indexes": ["pk(decision_id)", "idx(actor_user_id, decided_at)"],
        },
    ],
    "dataFlowDescription": (
        "Sync flow: Confluence webhook → Lambda receiver verifies HMAC and enqueues into SQS publish-queue → Publishing Pipeline (Step Functions) pulls one event → applies "
        "allow-list + approval state → calls AI Gateway for document review → on clean review, renders HTML and writes the immutable blob to S3, the metadata row to Aurora, "
        "the search document to OpenSearch, and emits publish-complete on EventBridge → Notification Service consumes the event and assembles per-user digests. "
        "Read flow: client request hits CloudFront → Next.js Frontend (Fargate) → session validated via Auth Service → Portal API queries Aurora read replica for metadata, "
        "fetches the HTML blob from S3 (or Redis render cache), returns to the user. Per-user last-visited is written-behind to Postgres via Redis. "
        "Audit flow: every audit-relevant action across services emits an audit-event on EventBridge → Audit Service writes to QLDB. Daily integrity verification compares "
        "the QLDB digest against the prior recorded digest and pages security on mismatch."
    ),
    "cachingStrategy": (
        "Three layers: CloudFront edge (cache-key includes tenant_id from auth context — done via Lambda@Edge so cross-tenant cache poisoning is impossible); "
        "Redis read-through cache for hot document versions and rendered HTML (TTL 1h, invalidated on publish-complete); "
        "Aurora read replicas absorb metadata reads. Cache invalidation on publish-complete is pushed to both CloudFront and Redis simultaneously."
    ),
    "dataRetention": (
        "Document versions: last 20 retained per page in hot S3 storage; older versions metadata-only in Aurora with content garbage-collected. "
        "Audit log: ≥ 12 months in QLDB, then cold-archived to S3 Object-Lock-Compliance for the contractual retention window. "
        "Sessions: TTL bound to the session-timeout configuration. "
        "Last-visited per user: retained for the user's lifetime; erased on user removal."
    ),
}

INTEGRATION_ARCHITECTURE = {
    "apiDesign": {
        "pattern": "REST + Server-Sent Events for live progress (publish status in Admin UI); JSON over HTTPS; OpenAPI 3.1 specs versioned with services.",
        "conventions": [
            "All client-facing endpoints are HTTPS only, TLS 1.2+, HSTS 1-year",
            "All endpoints carry an x-request-id; logs and audit join on this ID",
            "Pagination is cursor-based (no offset/limit)",
            "Error responses follow RFC 7807 Problem Details",
            "Mutation endpoints require an Idempotency-Key header",
        ],
        "requestResponseFormat": "application/json (UTF-8) with explicit schemaVersion field on every payload."
    },
    "integrationContracts": [
        {
            "systemName": "Atlassian Confluence",
            "purpose": "Source of truth; provides page content and change events.",
            "protocol": "HTTPS REST (Confluence Cloud REST v2) + webhook callbacks",
            "authentication": "OAuth 2.0 client credentials grant; rotating tokens stored in AWS Secrets Manager",
            "operations": [
                {"name": "Page fetch by id+version", "method": "GET", "endpoint": "/wiki/api/v2/pages/{id}", "requestSchema": "n/a", "responseSchema": "ConfluencePageV2"},
                {"name": "Page-changed webhook", "method": "POST", "endpoint": "(inbound to lambda/webhook-receiver)", "requestSchema": "ConfluenceChangeEvent", "responseSchema": "n/a"},
                {"name": "Page list since cursor (polling)", "method": "GET", "endpoint": "/wiki/api/v2/pages?since=...", "requestSchema": "n/a", "responseSchema": "ConfluencePageListV2"},
            ],
            "errorHandling": "Retry with exponential backoff on 5xx and 429; fail-closed (do not publish) on persistent error; dead-letter queue for poison events.",
            "circuitBreaker": {"enabled": True, "failureThreshold": 5, "resetTimeout": 60},
            "retryPolicy": {"maxAttempts": 4, "backoffType": "exponential", "backoffBase": 2},
        },
        {
            "systemName": "Amazon Bedrock (Anthropic Claude)",
            "purpose": "All AI functions: review, release notes, summaries, notifications, quality scoring.",
            "protocol": "AWS SDK / Bedrock Runtime InvokeModel + ConverseStream",
            "authentication": "IAM role with least-privilege Bedrock InvokeModel on the configured Claude model ARN(s)",
            "operations": [
                {"name": "Document review", "method": "POST", "endpoint": "(AI Gateway) /ai/review", "requestSchema": "DocumentReviewRequest", "responseSchema": "DocumentReviewFindings"},
                {"name": "Release notes", "method": "POST", "endpoint": "(AI Gateway) /ai/release-notes", "requestSchema": "ReleaseNotesRequest", "responseSchema": "ReleaseNotesDraft"},
                {"name": "Notification / since-last-visit summary", "method": "POST", "endpoint": "(AI Gateway) /ai/summary", "requestSchema": "SummaryRequest", "responseSchema": "SummaryText"},
                {"name": "Quality score", "method": "POST", "endpoint": "(AI Gateway) /ai/quality", "requestSchema": "QualityScoreRequest", "responseSchema": "QualityScoreResult"},
            ],
            "errorHandling": "Fail closed: any Bedrock 5xx, timeout, or response-schema-mismatch causes the AI Gateway to return a structured 'provider-unavailable' error; pipeline halts the publish.",
            "circuitBreaker": {"enabled": True, "failureThreshold": 10, "resetTimeout": 120},
            "retryPolicy": {"maxAttempts": 3, "backoffType": "exponential", "backoffBase": 2},
        },
        {
            "systemName": "Amazon SES",
            "purpose": "Send notification emails (digest and breaking-change) and operational mail (invitations, password reset).",
            "protocol": "AWS SDK (SendEmail / SendRawEmail)",
            "authentication": "IAM role with SES SendEmail on the docs.wsd.com identity",
            "operations": [
                {"name": "Send notification email", "method": "POST", "endpoint": "(SES) SendEmail", "requestSchema": "SesSendEmailRequest", "responseSchema": "SesSendEmailResponse"},
                {"name": "Send invitation email", "method": "POST", "endpoint": "(SES) SendEmail", "requestSchema": "SesSendEmailRequest", "responseSchema": "SesSendEmailResponse"},
            ],
            "errorHandling": "Retry transient throttling; dead-letter to SQS for manual investigation on persistent failure; bounces and complaints feed back to Notification Service to suppress affected addresses.",
            "circuitBreaker": {"enabled": True, "failureThreshold": 50, "resetTimeout": 60},
            "retryPolicy": {"maxAttempts": 5, "backoffType": "exponential", "backoffBase": 2},
        },
        {
            "systemName": "WorkOS",
            "purpose": "SAML 2.0 / OIDC SSO mediation for client tenants requiring enterprise login.",
            "protocol": "HTTPS REST",
            "authentication": "WorkOS API key in AWS Secrets Manager",
            "operations": [
                {"name": "Get authorization URL", "method": "GET", "endpoint": "(WorkOS) /sso/authorize", "requestSchema": "WorkOsAuthorizeRequest", "responseSchema": "WorkOsAuthorizeResponse"},
                {"name": "Exchange code for profile", "method": "POST", "endpoint": "(WorkOS) /sso/token", "requestSchema": "WorkOsTokenRequest", "responseSchema": "WorkOsProfile"},
            ],
            "errorHandling": "Surface a generic 'SSO unavailable' error to the user; fall back to support contact, never to password login on a SSO-enabled tenant.",
            "circuitBreaker": {"enabled": True, "failureThreshold": 5, "resetTimeout": 60},
            "retryPolicy": {"maxAttempts": 2, "backoffType": "linear", "backoffBase": 1},
        },
    ],
    "messagingPatterns": [
        "EventBridge for cross-service domain events (publish-complete, audit-event, user-disabled)",
        "SQS for ordered work-queues (publish-queue, notification-queue, dead-letter queues per consumer)",
        "Step Functions for the publishing pipeline state machine (visibility + retry semantics)",
    ],
    "eventDrivenArchitecture": {
        "enabled": True,
        "eventBus": "Amazon EventBridge (default + dedicated bus per env)",
        "eventTypes": [
            "page-change",
            "publish-complete",
            "publish-failed",
            "ai-review-pending-provider",
            "audit-event",
            "user-invited",
            "user-disabled",
            "user-removed",
            "breaking-change-notification-pending-review",
        ],
    },
}

SECURITY_ARCHITECTURE = {
    "securityBoundaries": (
        "Three concentric boundaries: (1) Edge — CloudFront + AWS WAF in front of every public route, with managed rule sets for OWASP Top 10 + bot control. "
        "(2) Service mesh — services live in private subnets; only ALB ingress per service is exposed; service-to-service traffic uses IAM-authenticated mTLS via the service mesh. "
        "(3) Data — Aurora, OpenSearch, ElastiCache, S3, QLDB all in private subnets, accessible only from the service VPC via VPC endpoints. "
        "Confluence is reached via an outbound NAT gateway with a static IP for Confluence allow-listing. Bedrock is reached via a VPC endpoint — no public internet egress for AI traffic."
    ),
    "authenticationPattern": {
        "type": "Cookie-bound session, signed in Auth Service; per-tenant flag selects between password+TOTP and WorkOS-mediated SAML/OIDC SSO",
        "flow": (
            "Password+TOTP: POST /auth/login with email+password → on success, Auth Service issues a TOTP challenge → on valid TOTP, Auth Service writes the session "
            "to Postgres + Redis and sets a Secure, HttpOnly, SameSite=Strict cookie scoped to docs.wsd.com. "
            "SSO: GET /auth/sso/start?tenant=… → WorkOS authorize URL → user authenticates at their IdP → callback to /auth/sso/callback with the WorkOS code → "
            "Auth Service exchanges code for a profile, maps the group claim to a role, writes the session, sets the same cookie."
        ),
        "tokenStructure": (
            "Session cookies carry an opaque 256-bit random session ID; the session record (in Redis + Postgres) holds tenant_id, user_id, role, factor, expiry, ip, ua. "
            "A separate token-bound CSRF token is set on form-bearing flows."
        ),
    },
    "authorizationModel": {
        "type": "Hybrid: tenant scope (data-layer RLS) + role-based authorization (application layer)",
        "roleMapping": [
            {"role": "reader", "permissions": ["read:document", "read:version", "create:pdf", "manage:own-prefs"]},
            {"role": "client_admin", "permissions": ["reader.*", "invite:user", "disable:user", "remove:user (within own tenant)"]},
            {"role": "wsd_doc_owner", "permissions": ["manage:allow-list", "manual:re-sync", "unpublish:page", "publish-override:on-quality-warning"]},
            {"role": "wsd_reviewer", "permissions": ["triage:ai-finding", "approve:release-notes", "approve:breaking-change-notification"]},
            {"role": "wsd_security", "permissions": ["query:audit-log", "verify:audit-integrity"]},
        ],
    },
    "securityControls": [
        {"control": "Tenant isolation at the data layer (PostgreSQL Row-Level Security)", "implementation": "Every tenant-scoped table carries a tenant_id column with an RLS policy that admits rows only when current_setting('app.tenant_id') matches; a tenant-bound connection sets app.tenant_id at session start.", "location": "Aurora PostgreSQL", "relatedReqs": ["REQ-012", "REQ-103"]},
        {"control": "Search index tenant filter injection", "implementation": "OpenSearch queries are routed through a thin gateway that injects the tenant filter at query-build time; callers cannot pass raw queries.", "location": "Portal API search adapter", "relatedReqs": ["REQ-024", "REQ-103"]},
        {"control": "AI review fail-closed gate", "implementation": "Publishing Pipeline halts on any AI Gateway 'provider-unavailable' error and emits ai-review-pending-provider on EventBridge.", "location": "services/publishing", "relatedReqs": ["REQ-040", "REQ-041", "REQ-105"]},
        {"control": "Append-only tamper-evident audit", "implementation": "Audit Service writes to QLDB; daily integrity job verifies the QLDB digest and alerts on mismatch.", "location": "services/audit", "relatedReqs": ["REQ-016", "REQ-107"]},
        {"control": "Encryption at rest (KMS)", "implementation": "All data stores use AWS-managed CMKs with annual rotation; TOTP secrets and other PII fields are wrapped with a per-tenant DEK.", "location": "All data stores", "relatedReqs": ["REQ-102"]},
        {"control": "WAF + managed rules", "implementation": "AWS WAF with the AWSManagedRulesCommonRuleSet, AWSManagedRulesKnownBadInputsRuleSet, plus tenant-aware rate limits.", "location": "CloudFront / ALB", "relatedReqs": ["REQ-010", "REQ-011"]},
        {"control": "Brute-force lockout", "implementation": "5 failed logins per user / 10 min → 15-min lockout; per-IP throttling on top.", "location": "services/auth + Redis counters", "relatedReqs": ["REQ-011"]},
        {"control": "Cross-tenant CI test", "implementation": "An automated test suite asserts on every release that read endpoints reject cross-tenant access; failures block deploy.", "location": "CI", "relatedReqs": ["REQ-012", "REQ-024", "REQ-103"]},
    ],
    "sensitiveDataHandling": [
        {"dataType": "Password hash", "classification": "Restricted", "handling": "Argon2id with platform-tuned cost; stored in Postgres; never logged."},
        {"dataType": "TOTP secret", "classification": "Restricted", "handling": "Encrypted with per-tenant DEK wrapped by KMS CMK; never logged."},
        {"dataType": "Session cookie value", "classification": "Restricted", "handling": "256-bit opaque ID; never logged in plaintext; only the prefix is logged for correlation."},
        {"dataType": "Email address", "classification": "Confidential (PII)", "handling": "Encrypted at rest via Aurora storage encryption; access scoped via RLS."},
        {"dataType": "Confluence storage-format snapshot", "classification": "Confidential (may contain client-specific text)", "handling": "Stored in S3 with object-lock; bucket policy restricts access to publishing pipeline + audit role."},
        {"dataType": "AI-pipeline prompt + response payloads", "classification": "Confidential", "handling": "Stored in a dedicated S3 bucket with KMS encryption; secret-shape strings redacted before logging."},
        {"dataType": "Audit log entries", "classification": "Restricted (forensic)", "handling": "Tamper-evident in QLDB; read access limited to wsd_security role; queries are themselves audit-logged."},
    ],
    "complianceRequirements": [
        "WCAG 2.1 AA for primary client-facing flows (REQ-104).",
        "≥ 12 month audit retention (REQ-016, REQ-107).",
        "Tamper-evident audit log (REQ-107).",
        "Per-tenant data isolation enforceable below the UI (REQ-012, REQ-103).",
        "TLS 1.2+ in transit; KMS-managed encryption at rest (REQ-102).",
    ],
}

DEPLOYMENT_ARCHITECTURE = {
    "targetEnvironment": {
        "platform": "AWS — Fargate (services) + Lambda (webhook + cron) + Aurora Serverless v2 + ElastiCache + OpenSearch managed + S3 + QLDB + SES + Bedrock; per-environment AWS account (dev / staging / prod) under WSD organisation.",
        "topology": (
            "Per-env: 1× VPC, 2× AZ minimum; ALBs in public subnets; Fargate services in private subnets; data tier in isolated subnets with VPC endpoints to S3, KMS, SES, Bedrock. "
            "CloudFront in front of the Next.js frontend ALB and a separate distribution for static assets. "
            "Webhook receiver Lambda behind API Gateway + WAF + Confluence-IP allow-list."
        ),
        "environmentVariables": [
            {"name": "DATABASE_URL", "description": "Aurora connection string (Secrets Manager reference)", "sensitive": True},
            {"name": "REDIS_URL", "description": "ElastiCache endpoint", "sensitive": False},
            {"name": "OPENSEARCH_ENDPOINT", "description": "OpenSearch domain endpoint", "sensitive": False},
            {"name": "S3_CONTENT_BUCKET", "description": "Content blob bucket name", "sensitive": False},
            {"name": "S3_PDF_BUCKET", "description": "PDF bucket name", "sensitive": False},
            {"name": "QLDB_LEDGER_NAME", "description": "Audit ledger name", "sensitive": False},
            {"name": "BEDROCK_MODEL_ARN", "description": "Claude model ARN", "sensitive": False},
            {"name": "WORKOS_API_KEY", "description": "WorkOS API key (Secrets Manager)", "sensitive": True},
            {"name": "CONFLUENCE_OAUTH_CLIENT_SECRET", "description": "Confluence OAuth secret (Secrets Manager)", "sensitive": True},
            {"name": "SESSION_SIGNING_KEY", "description": "Per-env session signing key (Secrets Manager + KMS)", "sensitive": True},
            {"name": "AI_REVIEW_FAIL_CLOSED", "description": "Hard switch; must be 'true' in prod", "sensitive": False},
        ],
    },
    "scalingStrategy": [
        {"component": "Portal Frontend", "minInstances": 2, "maxInstances": 20, "scalingTrigger": "CPU > 60% or p95 latency > 1.2 s for 3 min"},
        {"component": "Portal API", "minInstances": 2, "maxInstances": 30, "scalingTrigger": "CPU > 60% or RPS-per-task > target"},
        {"component": "Publishing Pipeline workers", "minInstances": 1, "maxInstances": 10, "scalingTrigger": "SQS publish-queue depth > 50 or oldest message age > 60 s"},
        {"component": "AI Gateway", "minInstances": 2, "maxInstances": 10, "scalingTrigger": "Bedrock concurrent-call gauge"},
        {"component": "Notification Service workers", "minInstances": 1, "maxInstances": 8, "scalingTrigger": "Notification queue depth"},
        {"component": "Auth Service", "minInstances": 2, "maxInstances": 8, "scalingTrigger": "CPU > 60% or 5xx rate > 0.5%"},
        {"component": "Renderer", "minInstances": 1, "maxInstances": 6, "scalingTrigger": "PDF render queue depth"},
    ],
    "resourceRequirements": [
        {"component": "Portal Frontend", "cpuRequest": "500m", "cpuLimit": "2000m", "memoryRequest": "512Mi", "memoryLimit": "2Gi"},
        {"component": "Portal API", "cpuRequest": "500m", "cpuLimit": "2000m", "memoryRequest": "512Mi", "memoryLimit": "2Gi"},
        {"component": "Publishing Pipeline worker", "cpuRequest": "500m", "cpuLimit": "2000m", "memoryRequest": "1Gi", "memoryLimit": "4Gi"},
        {"component": "AI Gateway", "cpuRequest": "250m", "cpuLimit": "1000m", "memoryRequest": "512Mi", "memoryLimit": "2Gi"},
        {"component": "Notification Service", "cpuRequest": "250m", "cpuLimit": "1000m", "memoryRequest": "512Mi", "memoryLimit": "2Gi"},
        {"component": "Auth Service", "cpuRequest": "500m", "cpuLimit": "1500m", "memoryRequest": "512Mi", "memoryLimit": "2Gi"},
        {"component": "Audit Service", "cpuRequest": "250m", "cpuLimit": "1000m", "memoryRequest": "512Mi", "memoryLimit": "2Gi"},
        {"component": "Renderer", "cpuRequest": "500m", "cpuLimit": "2000m", "memoryRequest": "1Gi", "memoryLimit": "4Gi"},
    ],
    "containerization": {
        "enabled": True,
        "baseImage": "public.ecr.aws/docker/library/node:20-bookworm-slim",
        "buildStrategy": "Multi-stage Dockerfile per service; non-root user; healthcheck baked in; SBOM emitted; signed via Sigstore.",
    },
    "cicdPipeline": (
        "GitHub Actions: on push → lint + typecheck + unit + integration + cross-tenant isolation suite + container image build + SBOM + Sigstore signing → CDK deploy to dev. "
        "Promotion: tag triggers staging deploy → smoke tests + synthetic load test → manual approval gate (release manager) → prod deploy with progressive rollout (10% → 50% → 100%) "
        "and automatic rollback on SLO breach. CDK app per service; one IaC repo for shared infra (VPC, ALB, RDS, OpenSearch, ElastiCache, QLDB, KMS keys, IAM roles)."
    ),
}

OPERATIONAL_CONCERNS = {
    "configurationManagement": {
        "environmentVariables": [
            "DATABASE_URL", "REDIS_URL", "OPENSEARCH_ENDPOINT", "S3_CONTENT_BUCKET", "S3_PDF_BUCKET",
            "QLDB_LEDGER_NAME", "BEDROCK_MODEL_ARN", "WORKOS_API_KEY", "CONFLUENCE_OAUTH_CLIENT_SECRET",
            "SESSION_SIGNING_KEY", "AI_REVIEW_FAIL_CLOSED", "ALLOW_LIST_BOOTSTRAP_S3_KEY"
        ],
        "databaseConfiguration": "Aurora Serverless v2: minACU 0.5 dev / 2 staging / 8 prod; maxACU 4 / 16 / 64; storage encryption with KMS; automated snapshot retention 35 days.",
        "featureFlags": [
            "ai_release_notes_enabled (default on)",
            "ai_quality_score_enabled (default on; soft warning only)",
            "ai_since_last_visit_enabled (default on)",
            "sso_enabled_per_tenant (per-tenant)",
            "ai_review_fail_closed (default on in prod, override forbidden in prod)",
        ],
    },
    "healthChecks": [
        {"endpoint": "/health/live", "purpose": "Liveness — process is responding", "checks": ["process is up", "config loaded"]},
        {"endpoint": "/health/ready", "purpose": "Readiness — dependencies reachable", "checks": ["Aurora reachable", "Redis reachable", "downstream service reachable (per service)"]},
        {"endpoint": "/health/ai", "purpose": "AI Gateway only — Bedrock connectivity probe (no model call)", "checks": ["Bedrock client constructable", "configured model ARN exists"]},
    ],
    "logging": {
        "destination": "Amazon CloudWatch Logs (per-service log group) + S3 long-term archive (1 yr) via Kinesis Firehose; tracked queries in QLDB for audit events.",
        "retention": "CloudWatch: 30 days hot; Firehose-to-S3 with object-lock: 1 year. Audit events in QLDB ≥ 12 months then archived.",
        "keyEvents": [
            {"event": "publish.complete", "level": "info", "trigger": "Publishing Pipeline persisted a version", "fields": ["document_id", "version_id", "duration_ms", "ai_review_findings", "tenant_scope"]},
            {"event": "publish.failed", "level": "error", "trigger": "Publishing Pipeline failed at any stage", "fields": ["document_id", "stage", "reason", "retry_count"]},
            {"event": "ai.provider_unavailable", "level": "error", "trigger": "AI Gateway returned fail-closed", "fields": ["operation", "provider", "duration_ms", "error_class"]},
            {"event": "auth.login.success", "level": "info", "trigger": "Successful login", "fields": ["user_id", "tenant_id", "factor", "ip", "ua"]},
            {"event": "auth.login.failure", "level": "warn", "trigger": "Failed login", "fields": ["user_id_or_email_hash", "tenant_id", "reason", "ip"]},
            {"event": "audit.integrity_check", "level": "info", "trigger": "Daily QLDB digest verification", "fields": ["verified_at", "digest_match", "anomalies"]},
        ],
    },
    "metrics": [
        {"name": "sync.approval_to_portal_seconds", "type": "histogram", "description": "End-to-end sync latency", "alertThreshold": "p95 > 300s for 15m → page"},
        {"name": "sync.ai_review_seconds", "type": "histogram", "description": "AI review pass duration", "alertThreshold": "p95 > 30s for 15m → warn"},
        {"name": "publish.success_total", "type": "counter", "description": "Successful publishes", "alertThreshold": "rate-of-change < expected → warn"},
        {"name": "publish.failed_total", "type": "counter", "description": "Failed publishes by stage", "alertThreshold": "any > 5/min → page"},
        {"name": "ai.provider_unavailable_total", "type": "counter", "description": "Fail-closed events", "alertThreshold": "any > 0 sustained 5m → page"},
        {"name": "portal.render_seconds", "type": "histogram", "description": "Portal page render", "alertThreshold": "p95 > 1.5s for 15m → page"},
        {"name": "search.query_seconds", "type": "histogram", "description": "Search query latency", "alertThreshold": "p95 > 1s for 15m → warn"},
        {"name": "auth.lockouts_total", "type": "counter", "description": "Account lockouts", "alertThreshold": "rate > 10/min → security"},
        {"name": "tenancy.cross_tenant_test_pass", "type": "gauge", "description": "1 if last cross-tenant test passed, 0 otherwise", "alertThreshold": "value = 0 → page"},
    ],
    "tracing": {
        "implementation": "AWS X-Ray with OpenTelemetry-compatible SDK; propagation via W3C traceparent header",
        "traceContext": "Inbound HTTP → x-request-id + traceparent; propagated across SQS, EventBridge, and Bedrock SDK calls; persisted in audit-event payloads for correlation.",
    },
    "alerting": {
        "channels": ["PagerDuty (services)", "Slack #docs-hub-alerts (warnings)", "Email security@wsd.com (security-only)"],
        "criticalAlerts": [
            "ai.provider_unavailable_total sustained — fail-closed in effect, publishes halted",
            "sync.approval_to_portal_seconds p95 > 300s — SLA breach",
            "publish.failed_total > 5/min — pipeline degradation",
            "auth.lockouts_total > 10/min — possible credential stuffing",
            "tenancy.cross_tenant_test_pass = 0 — isolation regression — block deploys",
            "audit.integrity_check digest_match = false — tampering or corruption",
        ],
    },
}

ADRS = [
    {
        "id": "ADR-001",
        "title": "Anthropic Claude via Amazon Bedrock (vs direct Anthropic API)",
        "status": "accepted",
        "context": "All AI functions need a high-quality LLM. The two realistic paths are direct Anthropic API and Claude via Amazon Bedrock. Both expose comparable model capability; the decision is operational.",
        "optionsConsidered": [
            {"option": "Direct Anthropic API", "pros": ["Newer model availability sometimes lands earlier", "Simpler SDK"], "cons": ["Public-internet egress for AI traffic; additional network boundary to audit", "Separate billing relationship outside AWS", "Harder to enforce 'no-cross-network leakage' guarantees"]},
            {"option": "Amazon Bedrock InvokeModel", "pros": ["VPC endpoint — AI traffic never leaves AWS network", "Unified IAM / KMS / CloudWatch / billing", "Tooling consistency with the rest of the stack", "Easier audit story"], "cons": ["Bedrock model versions can lag Anthropic releases by days–weeks", "Slightly higher per-token cost"]},
        ],
        "decision": "Use Amazon Bedrock InvokeModel for all Claude calls. Confine all AI traffic to a Bedrock VPC endpoint; no direct internet AI egress.",
        "rationale": "The single-network-egress posture materially simplifies the security story for a client-data-handling system, and the AWS-native IAM/audit story outweighs the model-version-lag cost.",
        "consequences": [
            "AI Gateway only talks to Bedrock; provider abstraction is preserved so we can revisit if Bedrock lag becomes painful.",
            "Model upgrade requires a Bedrock model availability check first.",
            "All AI prompt+response audit lives within AWS — easier compliance review.",
        ],
        "relatedReqs": ["REQ-040", "REQ-050", "REQ-105"],
        "relatedDecisions": ["ADR-007"],
    },
    {
        "id": "ADR-002",
        "title": "Multi-tenant PostgreSQL via tenant_id + RLS (vs schema-per-tenant or DB-per-tenant)",
        "status": "accepted",
        "context": "Tenant isolation must be enforced below the UI. The standard options are: tenant_id column with RLS, schema-per-tenant, or database-per-tenant.",
        "optionsConsidered": [
            {"option": "tenant_id + Row-Level Security", "pros": ["Operational simplicity", "Cross-tenant analytics easy when needed", "Single migration surface"], "cons": ["RLS bypass risk if a query forgets to set the session var", "Noisy-neighbour for query plans across tenants"]},
            {"option": "Schema-per-tenant", "pros": ["Hard logical boundary inside one DB", "Per-tenant ALTER TABLE easier"], "cons": ["Migration of N tenants is N× the work", "Connection pool sizing complex", "Search index still needs tenant filter"]},
            {"option": "Database-per-tenant", "pros": ["Strongest isolation", "Per-tenant backup/restore"], "cons": ["Operationally expensive (N RDS clusters)", "Cross-tenant features impossible", "Slow client onboarding"]},
        ],
        "decision": "tenant_id column on every tenant-scoped table with PostgreSQL Row-Level Security policies. A tenant-bound connection wrapper sets app.tenant_id at session start; queries without it are blocked by RLS.",
        "rationale": "RLS + a single audit-able connection wrapper gives us hard data-layer enforcement while keeping operational cost linear, not multiplicative. We pair this with an automated cross-tenant CI test for defence-in-depth.",
        "consequences": [
            "Every read/write helper must use the tenant-bound connection; lint rule + code review enforce.",
            "Cross-tenant CI test failure blocks every deploy.",
            "If a future tenant requires strong physical isolation, we can move them to their own database without changing the application data model.",
        ],
        "relatedReqs": ["REQ-012", "REQ-103"],
        "relatedDecisions": ["ADR-006"],
    },
    {
        "id": "ADR-003",
        "title": "QLDB for tamper-evident audit (vs append-only PostgreSQL + signed log)",
        "status": "accepted",
        "context": "REQ-107 requires tamper-evident audit retained ≥ 12 months.",
        "optionsConsidered": [
            {"option": "Amazon QLDB", "pros": ["Cryptographic journal verification built-in", "Purpose-built for this use case", "Indexed query for compliance"], "cons": ["Adds a managed service to operate", "Schema/query model less familiar than SQL"]},
            {"option": "Postgres append-only table + nightly signing", "pros": ["No new infra; one less service to operate"], "cons": ["Easier for a privileged DB user to silently edit", "Signing is bolt-on, not built-in", "Restore-from-backup path is murky for audit semantics"]},
            {"option": "S3 object-lock + structured log", "pros": ["Object-lock prevents deletion", "Cheap"], "cons": ["Query-by-actor or date-range is slow", "No native digest verification — must roll our own chain"]},
        ],
        "decision": "Use Amazon QLDB for audit. Cold-archive to S3 object-lock after 12 months for cost.",
        "rationale": "Built-in cryptographic verification is the strongest control and the cheapest to defend in a compliance review.",
        "consequences": [
            "Audit Service is a small standalone service that owns the QLDB integration.",
            "Daily integrity job verifies the digest; any failure pages security.",
            "Cold archive workflow handled by an EventBridge schedule.",
        ],
        "relatedReqs": ["REQ-016", "REQ-107"],
    },
    {
        "id": "ADR-004",
        "title": "Next.js (App Router) for the portal frontend (vs static SPA)",
        "status": "accepted",
        "context": "The portal is documentation-heavy and read-dominant. Server-side rendering vs SPA has implications for latency, search, and accessibility.",
        "optionsConsidered": [
            {"option": "Next.js 15 App Router with React Server Components", "pros": ["Fast first contentful paint", "Strong accessibility defaults", "Per-tenant cache key at the edge via middleware", "Co-located React SSR for the AI summary block"], "cons": ["More moving parts than a static SPA", "RSC learning curve"]},
            {"option": "Static SPA (Vite + React)", "pros": ["Operationally minimal", "Easy to host"], "cons": ["Worse initial paint", "Worse a11y unless extra care", "Per-tenant cache hard to get right at the edge", "Need a separate read API anyway"]},
            {"option": "Server-rendered Lit / web components", "pros": ["Consistent with the existing WAIF stack"], "cons": ["Smaller ecosystem for SSR", "Internal team less experienced with deep SSR in Lit"]},
        ],
        "decision": "Next.js 15 App Router with React Server Components, deployed on Fargate behind CloudFront with a Lambda@Edge middleware that derives the cache key from the session-bound tenant ID.",
        "rationale": "The portal's read-dominant, accessibility-mandated workload is exactly Next.js's sweet spot. Per-tenant cache key at the edge is the critical safety feature that closes the cross-tenant CDN risk.",
        "consequences": [
            "We accept a heavier ops surface than a pure SPA.",
            "Per-tenant cache-key in Lambda@Edge is a critical security control and must be tested.",
            "The Admin UI also uses Next.js for stack consistency.",
        ],
        "relatedReqs": ["REQ-020", "REQ-021", "REQ-100", "REQ-104"],
    },
    {
        "id": "ADR-005",
        "title": "Webhook-driven sync with polling fallback (vs polling-only)",
        "status": "accepted",
        "context": "The 5-minute SLA in REQ-NFR-002 can be hit by either pattern, but each has different failure modes.",
        "optionsConsidered": [
            {"option": "Webhook + polling fallback", "pros": ["Lowest latency under steady state", "Polling backs up missed events", "Resilient to webhook delivery outages"], "cons": ["Two code paths to maintain", "Webhook receiver requires public ingress with HMAC + IP allow-list"]},
            {"option": "Polling-only", "pros": ["Single code path", "No public ingress required"], "cons": ["Floor latency = polling interval; lower interval drives Confluence API cost", "Less suited to bursty publishing days"]},
        ],
        "decision": "Webhook-driven, with a polling fallback triggered when webhooks have been silent for longer than a configurable threshold (default 5 min). The polling cursor is in Postgres.",
        "rationale": "Steady-state latency target is best met by webhooks; reliability is best met by polling. The combination satisfies both at the cost of one extra code path.",
        "consequences": [
            "Webhook receiver runs as Lambda behind API Gateway with HMAC + Confluence IP allow-list.",
            "Polling Fargate task fires on EventBridge schedule with a backoff.",
            "Both paths converge on the same SQS publish-queue, so downstream code only sees one event type.",
        ],
        "relatedReqs": ["REQ-003"],
    },
    {
        "id": "ADR-006",
        "title": "Immutable content blobs in S3 with Object Lock (vs in-DB CLOBs)",
        "status": "accepted",
        "context": "Each published page version has rendered HTML and an original Confluence storage-format snapshot. Two natural homes: Postgres CLOB columns or S3 objects.",
        "optionsConsidered": [
            {"option": "S3 object-lock with versioning", "pros": ["Built-in immutability via Object Lock", "Cheap at scale", "Lifecycle to IA for cold versions", "Decoupled from DB row size"], "cons": ["Two systems to reason about", "Slightly more code for read path"]},
            {"option": "Postgres CLOB", "pros": ["Single store; transactional consistency with metadata"], "cons": ["Bloats DB size and backup time", "No native immutability", "More expensive per GB"]},
        ],
        "decision": "Rendered HTML and Confluence storage snapshot go to S3 with Object Lock (compliance mode for the snapshot, governance mode for the HTML). Postgres holds only the metadata row plus the S3 key.",
        "rationale": "Immutability is a first-class requirement; S3 Object Lock is the cheapest and strongest way to enforce it. Decoupling blobs from the metadata DB also keeps DB performance predictable as the catalog grows.",
        "consequences": [
            "Publish step is a CAS write to S3 (with If-None-Match) plus a Postgres insert; both are required.",
            "Garbage collection of versions beyond 20 is a metadata-only operation; the S3 blobs lifecycle to IA but never delete during the retention window.",
            "PDF blobs live in a separate bucket with a TTL of 30 days; regenerated on demand if stale.",
        ],
        "relatedReqs": ["REQ-004", "REQ-005", "REQ-023"],
    },
    {
        "id": "ADR-007",
        "title": "AI review fail-closed via queue + alert (vs fail-open with warning)",
        "status": "accepted",
        "context": "REQ-105 requires fail-closed. The decision is how the fail-closed state is presented operationally.",
        "optionsConsidered": [
            {"option": "Halt publish; queue page in 'review-pending-provider'; alert security + on-call", "pros": ["Strong guarantee", "Clear operational signal", "Backlog drains naturally when provider returns"], "cons": ["Publish backlog grows during outages"]},
            {"option": "Halt publish; surface an actionable banner to doc owners with a documented break-glass procedure", "pros": ["Doc owners know what to do", "Backlog visible to humans"], "cons": ["Tempting to bypass"]},
            {"option": "Fail-open with reviewer warning", "pros": ["No publish backlog"], "cons": ["Violates REQ-105", "Catastrophic if the bypass becomes the default during an outage"]},
        ],
        "decision": "Halt the publish; queue the page in 'review-pending-provider'; emit ai-review-pending-provider on EventBridge; show a clear banner in Admin UI; alert on-call. Bypass requires a documented two-person break-glass procedure with QLDB-audited justification, and is forbidden in prod by default config.",
        "rationale": "REQ-105 makes fail-closed non-negotiable. Pairing it with clear operational visibility and an explicit (audited) break-glass path gives security teeth and operators a clear UX.",
        "consequences": [
            "An AI Bedrock outage stops publishes; SLA dashboards reflect this honestly.",
            "Two-person break-glass procedure exists, is documented, and rarely used.",
            "We monitor the break-glass usage as a counter metric.",
        ],
        "relatedReqs": ["REQ-040", "REQ-041", "REQ-105"],
        "relatedDecisions": ["ADR-001"],
    },
    {
        "id": "ADR-008",
        "title": "Per-page on-demand PDF (vs per-version pre-rendered)",
        "status": "accepted",
        "context": "REQ-023 requires PDF download. Two extremes are 'render on every read' and 'pre-render every version'.",
        "optionsConsidered": [
            {"option": "On-demand with 30-day cache", "pros": ["No storage for unread versions", "Renderer can include current user identity in footer for audit"], "cons": ["First click for a given (version, requester) costs a render"]},
            {"option": "Pre-render every version at publish", "pros": ["Instant download"], "cons": ["Renders we never serve", "Footer cannot carry per-requester identity unless we render per-user"]},
        ],
        "decision": "On-demand render with a 30-day TTL cache. Footer includes the requesting user's tenant identity (not username) for audit traceability.",
        "rationale": "Reading is the dominant access pattern, not PDF download; pre-rendering would waste storage. The 30-day cache absorbs hotspots.",
        "consequences": [
            "Renderer service must be horizontally scalable for bursts.",
            "PDF bucket lifecycle: 30 days hot, then delete; regenerated if requested.",
            "Audit footer renders client tenant + version + timestamp; never embeds username.",
        ],
        "relatedReqs": ["REQ-023"],
    },
    {
        "id": "ADR-009",
        "title": "WorkOS for enterprise SSO (vs Keycloak self-hosted vs Auth0)",
        "status": "accepted",
        "context": "Some launch clients require SAML 2.0 / OIDC SSO (REQ-015). We need a mediator that can host per-tenant connections without us writing SAML directly.",
        "optionsConsidered": [
            {"option": "WorkOS", "pros": ["Built specifically for B2B per-tenant SSO", "Connection setup UX is good for client admins", "No SAML library in our codebase"], "cons": ["External dependency", "Per-active-connection pricing"]},
            {"option": "Keycloak self-hosted", "pros": ["No vendor lock-in", "No per-connection cost"], "cons": ["Operational burden of running an identity server", "Per-tenant configuration UX falls to us"]},
            {"option": "Auth0", "pros": ["Mature", "Broad ecosystem"], "cons": ["Heavier than we need for SSO-only", "Pricing"]},
        ],
        "decision": "WorkOS for SAML 2.0 / OIDC mediation. Password+TOTP login remains in-house. Per-tenant SSO mode is a Tenant.sso_mode flag.",
        "rationale": "WorkOS's product surface is exactly the per-tenant-SSO problem; we get a clean UX and avoid hosting SAML primitives. The dependency is well-bounded — it only mediates SSO and is feature-flagged per tenant.",
        "consequences": [
            "Auth Service has two login paths; per-tenant flag selects.",
            "WorkOS is in the critical path only for SSO-enabled tenants; password+TOTP tenants are unaffected by WorkOS outage.",
            "We monitor WorkOS health as a dedicated SLO.",
        ],
        "relatedReqs": ["REQ-015"],
    },
    {
        "id": "ADR-010",
        "title": "Step Functions for the publishing pipeline (vs in-process worker)",
        "status": "accepted",
        "context": "The publishing pipeline has 5+ retriable stages (allow-list, approval, AI review, render, persist, index, cache invalidate, notify). The orchestration choice affects visibility and retry semantics.",
        "optionsConsidered": [
            {"option": "AWS Step Functions Standard", "pros": ["Visual workflow + per-step audit", "Retry/visibility per step", "Free-tier covers small volumes"], "cons": ["State-machine JSON to maintain", "Cost scales with volume"]},
            {"option": "In-process worker with per-stage try/retry", "pros": ["Single deployable", "No state-machine spec"], "cons": ["Per-step visibility is logs-only", "Retry semantics live in code"]},
        ],
        "decision": "AWS Step Functions Standard for the publishing pipeline; the worker code per stage is a Fargate task or Lambda.",
        "rationale": "The per-step visibility and retry semantics are worth the orchestration cost; SLA debugging is materially easier with a state-machine view.",
        "consequences": [
            "Each stage is a distinct Lambda or Fargate task with a clear input/output schema.",
            "Step Functions JSON spec lives in the publishing service repo and is reviewed alongside code changes.",
            "Per-stage metrics emit automatically; alerting is per-stage.",
        ],
        "relatedReqs": ["REQ-003", "REQ-040", "REQ-101"],
    },
]


# ---------------------------------------------------------------------------
# Build extractedConcerns (for TAD-001-001)
# ---------------------------------------------------------------------------

req_priority = {r["id"]: r["priority"] for r in prd["requirements"]}
must_req_ids = [r["id"] for r in prd["requirements"] if r["priority"] == "must"]

extracted_concerns = {
    "sourceDocuments": {
        "prdId": PRD_ID,
        "prdVersion": prd["version"],
        "userStoriesId": PRD_ID,
        "userStoriesVersion": stories_doc["version"],
        "extractedAt": NOW,
    },
    "productContext": {
        "productName": prd["productName"],
        "problemStatement": prd["problemStatement"],
        "targetUsers": prd["targetUsers"],
        "scope": {
            "inScope": prd["inScope"],
            "outOfScope": prd["outOfScope"],
        },
    },
    "functionalRequirements": [
        {
            "reqId": r["id"],
            "title": r["title"],
            "description": r["description"],
            "category": r["domain"],
            "priority": r["priority"],
            "architecturalImplications": [
                # Heuristic implications per domain — short list per REQ
            ],
        }
        for r in prd["requirements"] if r["category"] != "non-functional"
    ],
    "nonFunctionalRequirements": [
        {
            "reqId": r["id"],
            "title": r["title"],
            "description": r["description"],
            "category": r["domain"],
            "priority": r["priority"],
        }
        for r in prd["requirements"] if r["category"] in ("non-functional", "security")
    ],
}


# ---------------------------------------------------------------------------
# Emit JSON parts
# ---------------------------------------------------------------------------

def make_part(part_number: int, group_id: str, group_name: str, sections: list[str], extra: dict) -> dict:
    base = {
        "tadId": f"TAD-001-{part_number:03d}",
        "prdId": PRD_ID,
        "version": TAD_VERSION,
        "status": "draft",
        "architecturalDecisions": ADRS if part_number == 4 else [],
        "generationMetadata": {
            "comprehensiveness": "standard",
            "sectionsGenerated": sections,
            "totalLlmCalls": 0,
            "totalInputTokens": 0,
            "totalOutputTokens": 0,
            "generatedAt": NOW,
        },
        "partInfo": {
            "partNumber": part_number,
            "totalParts": 4,
            "groupId": group_id,
            "groupName": group_name,
            "sections": sections,
        },
        "createdAt": NOW,
        "updatedAt": NOW,
    }
    base.update(extra)
    return base

part1 = make_part(1, "overview", "Overview & Principles",
    ["systemOverview", "architecturePrinciples", "extractedConcerns"],
    {
        "extractedConcerns": extracted_concerns,
        "systemOverview": SYSTEM_OVERVIEW,
        "architecturePrinciples": PRINCIPLES,
    })

part2 = make_part(2, "components", "Components",
    ["components"],
    {"components": COMPONENTS})

part3 = make_part(3, "data", "Data & Integration",
    ["dataArchitecture", "integrationArchitecture"],
    {
        "dataArchitecture": DATA_ARCHITECTURE,
        "integrationArchitecture": INTEGRATION_ARCHITECTURE,
    })

part4 = make_part(4, "operations", "Security, Deployment, Operations & ADRs",
    ["securityArchitecture", "deploymentArchitecture", "operationalConcerns", "architecturalDecisions"],
    {
        "securityArchitecture": SECURITY_ARCHITECTURE,
        "deploymentArchitecture": DEPLOYMENT_ARCHITECTURE,
        "operationalConcerns": OPERATIONAL_CONCERNS,
    })

tad_dir = REPO / "docs/specs/client-docs-hub/tad"
tad_dir.mkdir(parents=True, exist_ok=True)
parts = [(part1, "TAD-001-001.json"), (part2, "TAD-001-002.json"), (part3, "TAD-001-003.json"), (part4, "TAD-001-004.json")]
for doc, name in parts:
    (tad_dir / name).write_text(json.dumps(doc, indent=2) + "\n")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_part(doc):
    for k in ("tadId","prdId","version","status","architecturalDecisions","generationMetadata","createdAt","updatedAt"):
        assert k in doc, f"missing top-level {k} in {doc.get('tadId')}"
    assert re.match(r"^TAD-\d{3,}(-\d{3,})?$", doc["tadId"])
    assert re.match(r"^PRD-\d{3,}$", doc["prdId"])
    assert re.match(r"^\d+\.\d+\.\d+$", doc["version"])
    assert doc["status"] == "draft"
    for adr in doc["architecturalDecisions"]:
        assert re.match(r"^ADR-\d{3,}$", adr["id"]), f"bad ADR id {adr['id']}"
        assert adr["status"] in ("proposed","accepted","deprecated","superseded")
        for k in ("title","context","optionsConsidered","decision","rationale","consequences"):
            assert k in adr, f"ADR {adr['id']} missing {k}"
        for opt in adr["optionsConsidered"]:
            assert all(k in opt for k in ("option","pros","cons"))

for doc, _ in parts:
    validate_part(doc)

# NFR coverage check
nfr_req_ids = {r["id"] for r in prd["requirements"] if r["category"] in ("non-functional","security")}
addressed_in_tad_text = json.dumps(part4) + json.dumps(part1)
unaddressed = [r for r in nfr_req_ids if r not in addressed_in_tad_text]
if unaddressed:
    raise SystemExit(f"NFR/security REQs not referenced in TAD security/ops/principles: {sorted(unaddressed)}")


# ---------------------------------------------------------------------------
# Emit markdown
# ---------------------------------------------------------------------------

md = []
md.append("# Client Documentation Hub — Technical Architecture Document\n\n")
md.append(f"> Generated from `docs/specs/client-docs-hub/prd/PRD-001.json` v{prd['version']} and `docs/specs/client-docs-hub/user-stories/PRD-001-user-stories.json` v{stories_doc['version']}.\n")
md.append(f"> Canonical machine-readable copy split across `docs/specs/client-docs-hub/tad/TAD-001-001..004.json` ({sum(((tad_dir / n).stat().st_size for _, n in parts))} bytes total).\n")
md.append(f"> {len(COMPONENTS)} components, {len(ADRS)} ADRs, status: draft.\n\n")

md.append("## 1. System Overview\n\n")
md.append(f"**Executive summary.** {SYSTEM_OVERVIEW['executiveSummary']}\n\n")
md.append(f"**System purpose.** {SYSTEM_OVERVIEW['systemPurpose']}\n\n")
md.append(f"**Architectural approach.** {SYSTEM_OVERVIEW['architecturalApproach']}\n\n")
md.append("**Key capabilities.**\n")
for c in SYSTEM_OVERVIEW["keyCapabilities"]:
    md.append(f"- {c}\n")
md.append("\n**External dependencies.**\n\n")
md.append("| System | Purpose | Protocol | Owner |\n|---|---|---|---|\n")
for d in SYSTEM_OVERVIEW["externalDependencies"]:
    md.append(f"| {d['system']} | {d['purpose']} | {d['protocol']} | {d.get('owner','')} |\n")
md.append("\n**Assumptions and constraints.**\n")
for a in SYSTEM_OVERVIEW["assumptionsAndConstraints"]:
    md.append(f"- {a}\n")

md.append("\n## 2. Architectural Principles\n\n")
for p in PRINCIPLES:
    md.append(f"### {p['name']}\n")
    md.append(f"{p['description']}\n\n")
    md.append(f"**Rationale.** {p['rationale']}\n\n")
    md.append("**Implications.**\n")
    for i in p["implications"]:
        md.append(f"- {i}\n")
    md.append(f"\n**Related REQs.** {', '.join(p.get('relatedReqs', []))}\n\n")

md.append("## 3. Components\n\n")
for c in COMPONENTS:
    md.append(f"### {c['name']}\n")
    md.append(f"**Purpose.** {c['purpose']}\n\n")
    md.append(f"**Location.** `{c.get('location','')}`\n\n")
    md.append(f"**Dependencies.** {', '.join(c.get('dependencies', []))}\n\n")
    md.append("**Key patterns.**\n")
    for k in c.get("keyPatterns", []):
        md.append(f"- {k}\n")
    md.append("\n**Interfaces.**\n")
    for i in c.get("interfaces", []):
        md.append(f"- *{i['type']}* — `{i['name']}` — {i['description']}\n")
    md.append("\n**Responsibilities.**\n")
    for r in c.get("responsibilities", []):
        md.append(f"- {r}\n")
    md.append(f"\n**Related REQs.** {', '.join(c.get('relatedReqs', []))}\n\n")

md.append("## 4. Data Architecture\n\n")
md.append("### 4.1 Data stores\n\n")
md.append("| Store | Technology | Purpose |\n|---|---|---|\n")
for ds in DATA_ARCHITECTURE["dataStores"]:
    md.append(f"| {ds['name']} | {ds['technology']} | {ds['purpose']} |\n")
md.append("\n### 4.2 Core entities\n\n")
for e in DATA_ARCHITECTURE["coreEntities"]:
    md.append(f"#### {e['name']}\n")
    md.append(f"{e['description']}\n\n")
    md.append("| Field | Type | Required | Description |\n|---|---|---|---|\n")
    for f in e["fields"]:
        md.append(f"| {f['name']} | {f['type']} | {'yes' if f['required'] else 'no'} | {f.get('description','')} |\n")
    md.append(f"\n**Relationships.** {', '.join(e['relationships'])}\n\n")
    md.append(f"**Indexes.** {', '.join(e['indexes'])}\n\n")
md.append("### 4.3 Data flow\n\n")
md.append(DATA_ARCHITECTURE["dataFlowDescription"] + "\n\n")
md.append(f"**Caching strategy.** {DATA_ARCHITECTURE['cachingStrategy']}\n\n")
md.append(f"**Data retention.** {DATA_ARCHITECTURE['dataRetention']}\n\n")

md.append("## 5. Integration Architecture\n\n")
md.append(f"**API design.** {INTEGRATION_ARCHITECTURE['apiDesign']['pattern']}\n\n")
md.append("Conventions:\n")
for c in INTEGRATION_ARCHITECTURE["apiDesign"]["conventions"]:
    md.append(f"- {c}\n")
md.append("\n### Integration contracts\n\n")
for ic in INTEGRATION_ARCHITECTURE["integrationContracts"]:
    md.append(f"#### {ic['systemName']}\n")
    md.append(f"**Purpose.** {ic['purpose']}\n\n")
    md.append(f"**Protocol.** {ic['protocol']}\n\n")
    md.append(f"**Auth.** {ic['authentication']}\n\n")
    md.append("**Operations.**\n")
    for op in ic["operations"]:
        md.append(f"- `{op['method']} {op['endpoint']}` — {op['name']}\n")
    md.append(f"\n**Error handling.** {ic['errorHandling']}\n\n")
md.append("\n### Messaging patterns\n\n")
for mp in INTEGRATION_ARCHITECTURE["messagingPatterns"]:
    md.append(f"- {mp}\n")
md.append("\n### Event-driven events\n\n")
for e in INTEGRATION_ARCHITECTURE["eventDrivenArchitecture"]["eventTypes"]:
    md.append(f"- `{e}`\n")

md.append("\n## 6. Security Architecture\n\n")
md.append(f"**Boundaries.** {SECURITY_ARCHITECTURE['securityBoundaries']}\n\n")
md.append(f"**Authentication.** {SECURITY_ARCHITECTURE['authenticationPattern']['type']}\n\n")
md.append(f"Flow: {SECURITY_ARCHITECTURE['authenticationPattern']['flow']}\n\n")
md.append(f"**Authorization.** {SECURITY_ARCHITECTURE['authorizationModel']['type']}\n\n")
md.append("Role permissions:\n")
for rm in SECURITY_ARCHITECTURE["authorizationModel"]["roleMapping"]:
    md.append(f"- **{rm['role']}** — {', '.join(rm['permissions'])}\n")
md.append("\n### Security controls\n\n")
md.append("| Control | Implementation | Location | Related REQs |\n|---|---|---|---|\n")
for sc in SECURITY_ARCHITECTURE["securityControls"]:
    md.append(f"| {sc['control']} | {sc['implementation']} | {sc['location']} | {', '.join(sc.get('relatedReqs', []))} |\n")
md.append("\n### Sensitive data handling\n\n")
md.append("| Data type | Classification | Handling |\n|---|---|---|\n")
for sd in SECURITY_ARCHITECTURE["sensitiveDataHandling"]:
    md.append(f"| {sd['dataType']} | {sd['classification']} | {sd['handling']} |\n")
md.append("\n**Compliance.**\n")
for c in SECURITY_ARCHITECTURE["complianceRequirements"]:
    md.append(f"- {c}\n")

md.append("\n## 7. Deployment Architecture\n\n")
md.append(f"**Platform.** {DEPLOYMENT_ARCHITECTURE['targetEnvironment']['platform']}\n\n")
md.append(f"**Topology.** {DEPLOYMENT_ARCHITECTURE['targetEnvironment']['topology']}\n\n")
md.append("### Scaling per component\n\n")
md.append("| Component | min | max | Trigger |\n|---|---|---|---|\n")
for sc in DEPLOYMENT_ARCHITECTURE["scalingStrategy"]:
    md.append(f"| {sc['component']} | {sc['minInstances']} | {sc['maxInstances']} | {sc['scalingTrigger']} |\n")
md.append("\n### Resource requirements\n\n")
md.append("| Component | CPU req | CPU lim | Mem req | Mem lim |\n|---|---|---|---|---|\n")
for rr in DEPLOYMENT_ARCHITECTURE["resourceRequirements"]:
    md.append(f"| {rr['component']} | {rr['cpuRequest']} | {rr['cpuLimit']} | {rr['memoryRequest']} | {rr['memoryLimit']} |\n")
md.append(f"\n**CI/CD.** {DEPLOYMENT_ARCHITECTURE['cicdPipeline']}\n\n")

md.append("## 8. Operational Concerns\n\n")
md.append("### Configuration\n\n")
md.append("Environment variables (selection): " + ", ".join("`"+v+"`" for v in OPERATIONAL_CONCERNS["configurationManagement"]["environmentVariables"]) + "\n\n")
md.append(f"**Database.** {OPERATIONAL_CONCERNS['configurationManagement']['databaseConfiguration']}\n\n")
md.append("**Feature flags:**\n")
for ff in OPERATIONAL_CONCERNS["configurationManagement"]["featureFlags"]:
    md.append(f"- {ff}\n")
md.append("\n### Health checks\n\n")
for hc in OPERATIONAL_CONCERNS["healthChecks"]:
    md.append(f"- `{hc['endpoint']}` — {hc['purpose']} — checks: {', '.join(hc['checks'])}\n")
md.append("\n### Logging\n\n")
md.append(f"**Destination.** {OPERATIONAL_CONCERNS['logging']['destination']}\n\n")
md.append(f"**Retention.** {OPERATIONAL_CONCERNS['logging']['retention']}\n\n")
md.append("**Key events.**\n\n")
md.append("| Event | Level | Trigger | Fields |\n|---|---|---|---|\n")
for ke in OPERATIONAL_CONCERNS["logging"]["keyEvents"]:
    md.append(f"| `{ke['event']}` | {ke['level']} | {ke['trigger']} | {', '.join(ke['fields'])} |\n")
md.append("\n### Metrics & alerts\n\n")
md.append("| Metric | Type | Description | Alert |\n|---|---|---|---|\n")
for mm in OPERATIONAL_CONCERNS["metrics"]:
    md.append(f"| `{mm['name']}` | {mm['type']} | {mm['description']} | {mm.get('alertThreshold','')} |\n")
md.append(f"\n**Tracing.** {OPERATIONAL_CONCERNS['tracing']['implementation']}; context: {OPERATIONAL_CONCERNS['tracing']['traceContext']}\n\n")
md.append("**Alerting channels.** " + ", ".join(OPERATIONAL_CONCERNS["alerting"]["channels"]) + "\n\n")
md.append("**Critical alerts.**\n")
for ca in OPERATIONAL_CONCERNS["alerting"]["criticalAlerts"]:
    md.append(f"- {ca}\n")

md.append("\n## 9. Architectural Decision Records\n\n")
for a in ADRS:
    md.append(f"### {a['id']} — {a['title']}\n")
    md.append(f"**Status.** {a['status']}\n\n")
    md.append(f"**Context.** {a['context']}\n\n")
    md.append("**Options considered.**\n")
    for o in a["optionsConsidered"]:
        md.append(f"- **{o['option']}**\n")
        md.append(f"  - Pros: {'; '.join(o['pros'])}\n")
        md.append(f"  - Cons: {'; '.join(o['cons'])}\n")
    md.append(f"\n**Decision.** {a['decision']}\n\n")
    md.append(f"**Rationale.** {a['rationale']}\n\n")
    md.append("**Consequences.**\n")
    for c in a["consequences"]:
        md.append(f"- {c}\n")
    md.append(f"\n**Related REQs.** {', '.join(a.get('relatedReqs', []))}\n")
    if a.get("relatedDecisions"):
        md.append(f"**Related decisions.** {', '.join(a['relatedDecisions'])}\n")
    md.append("\n")

md_path = REPO / "docs/specs/client-docs-hub/tad/TAD.md"
md_path.parent.mkdir(parents=True, exist_ok=True)
md_path.write_text("".join(md))


# ---------------------------------------------------------------------------
# Update manifest
# ---------------------------------------------------------------------------

manifest_path = REPO / "docs/specs/client-docs-hub/manifest.json"
manifest = json.loads(manifest_path.read_text())
prd_entry = manifest["prd"]
tad_entries = [
    {"id": "TAD-001-001", "name": "Overview & Principles", "path": "tad/TAD-001-001.json"},
    {"id": "TAD-001-002", "name": "Components", "path": "tad/TAD-001-002.json"},
    {"id": "TAD-001-003", "name": "Data & Integration", "path": "tad/TAD-001-003.json"},
    {"id": "TAD-001-004", "name": "Security, Deploy, Ops & ADRs", "path": "tad/TAD-001-004.json"},
]
existing_ids = {t["id"] for t in prd_entry.get("tad", [])}
for t in tad_entries:
    if t["id"] not in existing_ids:
        prd_entry.setdefault("tad", []).append(t)
prd_entry["tadMarkdownPath"] = "tad/TAD.md"
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print(f"Components: {len(COMPONENTS)}")
print(f"Principles: {len(PRINCIPLES)}")
print(f"ADRs: {len(ADRS)}")
print(f"Data stores: {len(DATA_ARCHITECTURE['dataStores'])}")
print(f"Core entities: {len(DATA_ARCHITECTURE['coreEntities'])}")
print(f"Integration contracts: {len(INTEGRATION_ARCHITECTURE['integrationContracts'])}")
print(f"NFR/security REQs referenced in TAD: {len(nfr_req_ids)} / {len(nfr_req_ids)}")
print("Wrote:")
for _, n in parts:
    print(f"  docs/specs/client-docs-hub/tad/{n}")
print("  docs/specs/client-docs-hub/tad/TAD.md")
print("  manifest updated")
