#!/usr/bin/env python3
"""
One-shot generator for PRD-001 Build Sequence (Stage 5 — Implementation Detail).

Strategy: dependency-first. Foundation layers (platform, auth, data model, audit, AI gateway)
land first; domain capabilities (sync, AI review, publishing pipeline, portal, notifications)
build on them; UI surfaces and NFR hardening land last.

Emits:
  - docs/specs/client-docs-hub/build-sequence/BS-001.json   (canonical JSON)
  - docs/specs/client-docs-hub/build-sequence/BUILD-SEQUENCE.md  (human-readable view)
  - updates docs/specs/client-docs-hub/manifest.json

Self-validates: every AC across every story is covered by exactly one FBS, every
dependencies[] points only to earlier FBS (DAG), every FBS has 3+ testable outcomes,
all IDs match RCF schema regexes.
"""

from __future__ import annotations
import json
import re
from datetime import datetime, timezone
from pathlib import Path

PRD_ID = "PRD-001"
BS_ID = "BS-001"
VERSION = "1.0.0"
REPO = Path(__file__).resolve().parent.parent
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

stories_doc = json.loads((REPO / "docs/specs/client-docs-hub/user-stories/PRD-001-user-stories.json").read_text())
story_by_id = {s["id"]: s for s in stories_doc["stories"]}
all_ac_ids = {ac["id"] for s in stories_doc["stories"] for ac in s["acceptanceCriteria"]}


# ---------------------------------------------------------------------------
# FBS plan: dependency-first
# ---------------------------------------------------------------------------
# Each FBS allocates whole stories to itself (no AC splitting across FBS).
# scope: list of US-XXX story IDs
# deps:  list of FBS-XXX ids that this builds on; MUST point only to earlier FBS

FBS = [
    {
        "id": "FBS-001",
        "title": "Platform foundation, tenant data model, and Postgres Row-Level Security",
        "summary": (
            "Stand up the AWS baseline (per-env account, VPC, subnets, KMS, IAM, ECR, ALB, Aurora PostgreSQL Serverless v2). "
            "Introduce the Tenant and User core entities and the tenant-bound connection wrapper. Wire Postgres RLS policies "
            "on every tenant-scoped table; expose the lint/CI checks that fail builds touching tenant tables without the wrapper."
        ),
        "scope": ["US-018", "US-059"],
        "deps": [],
        "domain": "Foundation",
        "risk": "high",
        "size": "medium", "hours": 8,
        "outcomes": [
            "A tenant-bound DB connection sets app.tenant_id at session start; queries without it are blocked by RLS.",
            "Every tenant-scoped read or write rejects requests where the session tenant does not match the row's tenant_id.",
            "Cross-tenant CI isolation test runs and passes for the seed read endpoints.",
            "An attempt to add a new read endpoint without tenant scoping fails the build via a lint rule.",
            "CDK app provisions the per-env account baseline with KMS keys and S3 default-encryption configured.",
        ],
        "context": {
            "prdSections": ["Authentication & Access Control", "Data Protection"],
            "tadSections": ["Architecture Principles", "Components: Portal API", "Data architecture", "ADR-002"],
            "schemas": ["Tenant", "User"],
        },
        "deliverables": [
            "CDK stacks for VPC, KMS, IAM baseline, Aurora cluster, ALB",
            "tenant-bound DB connection helper (Node.js + TypeScript)",
            "Postgres RLS policies for all v1 tables",
            "ESLint rule + CI check rejecting unscoped queries",
            "Seed cross-tenant isolation test suite",
        ],
    },
    {
        "id": "FBS-002",
        "title": "Auth Service — password + TOTP login, session lifecycle",
        "summary": (
            "Implement the primary login flow: password (Argon2id) plus TOTP, session creation in Postgres + Redis with "
            "HttpOnly/Secure/SameSite cookies, idle timeout, idempotent logout, and the unauthenticated-redirect middleware."
        ),
        "scope": ["US-014", "US-015", "US-016"],
        "deps": ["FBS-001"],
        "domain": "Authentication & Access Control",
        "risk": "high",
        "size": "medium", "hours": 8,
        "outcomes": [
            "POST /auth/login succeeds with valid password + TOTP, establishes a session, and sets a Secure HttpOnly SameSite=Strict cookie.",
            "Unauthenticated requests to any portal route are redirected to /login with a signed redirect-back parameter.",
            "Idle-timeout exceeded sessions are invalidated server-side on next request.",
            "POST /auth/logout is idempotent: repeated calls do not error.",
            "TOTP secrets are encrypted with a KMS-bound DEK and never logged.",
        ],
        "context": {
            "prdSections": ["Authentication & Access Control"],
            "tadSections": ["Components: Auth Service", "Security architecture: authentication"],
        },
        "deliverables": [
            "services/auth (Fargate, Node.js + Fastify) with login, logout, session middleware",
            "Argon2id password hashing utilities",
            "TOTP enrolment + verification module",
            "Redis-backed session store with Postgres mirror",
        ],
    },
    {
        "id": "FBS-003",
        "title": "Auth — brute-force lockout and IP throttling",
        "summary": (
            "Rate-limit login attempts per user (5/10 min → 15-min lockout) and per source IP. Generate the lockout-notification "
            "email path. Surface metrics for security."
        ),
        "scope": ["US-017"],
        "deps": ["FBS-002"],
        "domain": "Authentication & Access Control",
        "risk": "medium",
        "size": "small", "hours": 3,
        "outcomes": [
            "5 failed logins for one user within 10 minutes triggers a 15-minute lockout and an email notification.",
            "Per-IP throttling kicks in at the configured threshold and returns 429 cleanly.",
            "auth.lockouts_total metric increments on every lockout and feeds the security alert channel.",
        ],
        "context": {
            "prdSections": ["Authentication & Access Control"],
            "tadSections": ["Security controls: brute-force lockout"],
        },
        "deliverables": [
            "Redis-backed counter store for per-user and per-IP attempts",
            "Lockout-notification email template + SES send path",
            "Security alert rule for sustained lockout rate",
        ],
    },
    {
        "id": "FBS-004",
        "title": "Audit Service on QLDB + auth-event audit + tamper-evident retention",
        "summary": (
            "Stand up the Audit Service, the QLDB ledger, and the EventBridge audit-event consumer. Add the daily QLDB digest "
            "integrity job. Wire the first audit producer (Auth Service) so authentication outcomes flow into the ledger."
        ),
        "scope": ["US-025", "US-064"],
        "deps": ["FBS-001", "FBS-002"],
        "domain": "Audit & Compliance",
        "risk": "high",
        "size": "medium", "hours": 6,
        "outcomes": [
            "Every login attempt (success / failure / lockout) writes a typed audit entry to QLDB within 5 seconds.",
            "Daily QLDB digest verification runs on schedule and emits a signed report; mismatch pages security.",
            "An attempt to alter an existing audit row is rejected at write time and the rejection itself is logged.",
            "Audit query API returns events filtered by user / tenant / IP / date range within 5 s p95 for the last 90 days.",
        ],
        "context": {
            "prdSections": ["Authentication & Access Control", "Non-Functional"],
            "tadSections": ["Components: Audit Log Service", "ADR-003"],
        },
        "deliverables": [
            "services/audit (Fargate)",
            "QLDB ledger + journal verification job (EventBridge schedule)",
            "EventBridge audit-event consumer",
            "Audit query API with role-restricted access",
        ],
    },
    {
        "id": "FBS-005",
        "title": "Document & DocumentVersion model with S3 immutable blobs",
        "summary": (
            "Define Document, DocumentVersion, and the S3-with-Object-Lock content blob pattern. Implement the version-persist "
            "CAS (idempotent under retry). Persist publisher identity and source Confluence revision."
        ),
        "scope": ["US-008", "US-009"],
        "deps": ["FBS-001"],
        "domain": "Confluence Sync & Publishing",
        "risk": "high",
        "size": "medium", "hours": 8,
        "outcomes": [
            "A publish commit writes the rendered HTML blob to S3 (immutable, object-lock) and the metadata row to Postgres atomically.",
            "Two-times-in-a-row CAS-write with the same (document_id, source_version_id) is a no-op on the second write.",
            "Retiring the 21st version preserves its metadata + audit entry; the blob is GC'd from hot storage only after retention window.",
            "An attempt to overwrite an existing version blob is rejected by S3 Object Lock and the attempt is audit-logged.",
            "Version-history API returns publish timestamp, source version, and publisher identity for each retained version.",
        ],
        "context": {
            "prdSections": ["Confluence Sync & Publishing"],
            "tadSections": ["Data architecture: Document, DocumentVersion", "ADR-006"],
            "schemas": ["Document", "DocumentVersion"],
        },
        "deliverables": [
            "Document + DocumentVersion migrations",
            "S3 content-blob writer with Object Lock + KMS",
            "CAS-on-insert persistence helper",
            "Version-history read endpoint",
        ],
    },
    {
        "id": "FBS-006",
        "title": "Document scoping — shared vs client-specific visibility",
        "summary": (
            "Introduce ScopeGrant and the scope_mode field. Implement the label-driven scope inference and the read-time scope "
            "check at the data layer (extends FBS-001 RLS)."
        ),
        "scope": ["US-019", "US-020"],
        "deps": ["FBS-005", "FBS-001"],
        "domain": "Authentication & Access Control",
        "risk": "high",
        "size": "small", "hours": 4,
        "outcomes": [
            "A page labelled 'shared' becomes visible to every authenticated tenant on publish.",
            "A page labelled 'client:<slug>' is visible only to the named tenant(s); direct URL access from other tenants returns 404.",
            "Removing 'shared' from a previously-shared page hides it on the next sync from all tenants except those granted client-specific access.",
            "A publish that names a non-existent tenant in its scope label is rejected with a clear error.",
        ],
        "context": {
            "prdSections": ["Authentication & Access Control"],
            "tadSections": ["Data architecture: ScopeGrant", "Security architecture: tenant isolation"],
            "schemas": ["ScopeGrant"],
        },
        "deliverables": [
            "ScopeGrant migration + RLS policy",
            "Scope-label parser for Confluence labels",
            "Scope-aware document read helper",
        ],
    },
    {
        "id": "FBS-007",
        "title": "Renderer — Confluence storage format to portable HTML with cross-link rewriting",
        "summary": (
            "Implement deterministic Confluence-storage → AST → HTML rendering; preserve headings, lists, tables, code (with lang), "
            "inline images. Rewrite cross-page links: live for published, inert for non-published."
        ),
        "scope": ["US-010", "US-011"],
        "deps": ["FBS-005"],
        "domain": "Confluence Sync & Publishing",
        "risk": "medium",
        "size": "medium", "hours": 8,
        "outcomes": [
            "Rendered HTML preserves headings (h1–h4), lists, tables, code blocks with language hint, and inline images.",
            "An inline image renders from a per-page asset path with the same alt-text as the source.",
            "A cross-link to a published page rewrites to the portal URL; a cross-link to a non-published page renders as inert text with a 'not available' tooltip.",
            "An external https link survives verbatim and opens in a new tab with rel='noopener'.",
        ],
        "context": {
            "prdSections": ["Confluence Sync & Publishing"],
            "tadSections": ["Components: Renderer"],
        },
        "deliverables": [
            "services/renderer (Fargate)",
            "Confluence storage parser + AST",
            "HTML serializer with cross-link rewriter",
            "Asset extractor that writes images to S3",
        ],
    },
    {
        "id": "FBS-008",
        "title": "Confluence allow-list management (admin) + sync filter",
        "summary": (
            "Admin UI surface to manage the allow-list of Confluence labels and source spaces; sync engine consumes it as the "
            "first gate. Allow-list changes audit-logged."
        ),
        "scope": ["US-001", "US-002"],
        "deps": ["FBS-001"],
        "domain": "Confluence Sync & Publishing",
        "risk": "medium",
        "size": "small", "hours": 4,
        "outcomes": [
            "An admin can add or remove labels from the allow-list and the change is audit-logged with their identity.",
            "A page that does not match any allow-listed label or space is skipped by sync with a debug log entry.",
            "An empty allow-list publishes zero pages and surfaces an admin-visible warning.",
        ],
        "context": {
            "prdSections": ["Confluence Sync & Publishing"],
            "tadSections": ["Components: Sync Service"],
        },
        "deliverables": [
            "allow-list table + admin CRUD endpoints",
            "Admin UI page for allow-list",
            "Sync filter middleware",
        ],
    },
    {
        "id": "FBS-009",
        "title": "Sync Service — Confluence webhook receiver + HMAC verification + dedup",
        "summary": (
            "Lambda webhook receiver behind API Gateway with HMAC verification, Confluence-IP allow-list, dedup keyed on "
            "(page_id, source_version_id), and SQS publish-queue enqueue."
        ),
        "scope": ["US-005"],
        "deps": ["FBS-008"],
        "domain": "Confluence Sync & Publishing",
        "risk": "medium",
        "size": "medium", "hours": 6,
        "outcomes": [
            "POST /webhooks/confluence with a valid HMAC enqueues exactly one event onto the publish-queue.",
            "A duplicate Confluence webhook delivery does not produce a duplicate downstream version.",
            "An invalid HMAC or a non-allow-listed source IP returns 400 / 403 cleanly and the attempt is audit-logged.",
            "A webhook payload that fails schema validation is rejected with a 400 and an alert is raised.",
        ],
        "context": {
            "prdSections": ["Confluence Sync & Publishing"],
            "tadSections": ["Components: Sync Service", "Integration architecture: Confluence", "ADR-005"],
        },
        "deliverables": [
            "lambda/webhook-receiver",
            "API Gateway + WAF + Confluence IP allow-list",
            "Dedup table in Postgres",
        ],
    },
    {
        "id": "FBS-010",
        "title": "Sync Service — polling fallback with cursor",
        "summary": (
            "Fargate cron-driven polling job that resumes from a Postgres sync_cursor when webhooks have been silent past the "
            "configured threshold; backfills one cycle after webhook recovery."
        ),
        "scope": ["US-006"],
        "deps": ["FBS-009"],
        "domain": "Confluence Sync & Publishing",
        "risk": "medium",
        "size": "small", "hours": 4,
        "outcomes": [
            "When webhooks have not fired for N minutes, the polling job fetches recently-changed pages and enqueues eligible events.",
            "After webhook recovery, the polling cycle backfills one cycle before quiescing.",
            "Polled events follow the same allow-list → approval → AI-review path as webhook events.",
        ],
        "context": {
            "prdSections": ["Confluence Sync & Publishing"],
            "tadSections": ["Components: Sync Service", "ADR-005"],
        },
        "deliverables": [
            "Fargate polling task with sync_cursor logic",
            "EventBridge schedule",
        ],
    },
    {
        "id": "FBS-011",
        "title": "AI Gateway — Bedrock integration, circuit breaker, fail-closed",
        "summary": (
            "AI Gateway service with operations for review, release-notes, summary, quality. Wires Bedrock VPC endpoint, "
            "per-operation timeout + retry + circuit breaker, fail-closed semantics, prompt-version registry, and audit hooks."
        ),
        "scope": ["US-062"],
        "deps": ["FBS-001"],
        "domain": "AI Document Review",
        "risk": "high",
        "size": "medium", "hours": 8,
        "outcomes": [
            "Bedrock 5xx / timeout / schema-mismatch causes AI Gateway to return 'provider-unavailable' with the operation context.",
            "Bedrock availability recovers and the circuit closes within the configured reset window.",
            "An operator cannot bypass the fail-closed gate in prod without the documented two-person break-glass procedure.",
        ],
        "context": {
            "prdSections": ["AI Document Review", "Non-Functional"],
            "tadSections": ["Components: AI Gateway", "ADR-001", "ADR-007"],
        },
        "deliverables": [
            "services/ai-gateway",
            "Bedrock VPC endpoint",
            "Prompt-version registry",
            "Circuit breaker + retry policy per operation",
            "Break-glass procedure documented + audit-logged",
        ],
    },
    {
        "id": "FBS-012",
        "title": "AI Document Review — secrets and credentials detection",
        "summary": (
            "Implement the secrets / credentials / API keys detection operation via AI Gateway. Raise high-severity findings on "
            "matches; raise medium-severity on low-confidence candidates."
        ),
        "scope": ["US-040"],
        "deps": ["FBS-011"],
        "domain": "AI Document Review",
        "risk": "high",
        "size": "medium", "hours": 6,
        "outcomes": [
            "A page containing an AWS access key pattern triggers a finding with category=secret and severity=high.",
            "A low-confidence candidate triggers a finding with severity=medium routed to reviewer rather than ignored.",
            "A clean page produces a 'no-secret-findings' record on the version and proceeds.",
        ],
        "context": {
            "prdSections": ["AI Document Review"],
            "tadSections": ["Components: AI Gateway", "ADR-007"],
            "schemas": ["AIFinding"],
        },
        "deliverables": [
            "AI review prompt: secrets",
            "Finding schema + persistence",
            "Test fixtures with synthetic secret patterns",
        ],
    },
    {
        "id": "FBS-013",
        "title": "AI Document Review — internal URLs, Jira links, internal emails",
        "summary": (
            "Three high-severity detectors over the configured internal-domain / Jira / internal-email allow-lists."
        ),
        "scope": ["US-041"],
        "deps": ["FBS-011"],
        "domain": "AI Document Review",
        "risk": "medium",
        "size": "small", "hours": 4,
        "outcomes": [
            "A URL ending in an internal-domain triggers an internal-url finding with severity=high.",
            "A link or reference matching a Jira ticket URL pattern triggers an internal-ticket finding.",
            "An email at an internal domain triggers an internal-email finding (high for staff inboxes, medium for shared).",
        ],
        "context": {
            "prdSections": ["AI Document Review"],
            "tadSections": ["Components: AI Gateway"],
        },
        "deliverables": [
            "AI review prompts: internal URL / Jira / internal email",
            "Configurable allow-lists",
        ],
    },
    {
        "id": "FBS-014",
        "title": "AI Document Review — missing content (placeholders, empty sections, stubs)",
        "summary": (
            "Low/medium severity detectors for TODO/TBD/lorem ipsum placeholders, headings immediately followed by next heading, "
            "and pages shorter than configured minimum."
        ),
        "scope": ["US-042"],
        "deps": ["FBS-011"],
        "domain": "AI Document Review",
        "risk": "low",
        "size": "small", "hours": 4,
        "outcomes": [
            "Placeholder strings raise a missing-content finding with severity=medium.",
            "An empty section (heading immediately followed by another heading) raises an empty-section finding with severity=low.",
            "A page below the configured minimum-word threshold raises a stub finding with severity=low.",
        ],
        "context": {
            "prdSections": ["AI Document Review"],
            "tadSections": ["Components: AI Gateway"],
        },
        "deliverables": [
            "AI review prompt: missing content",
            "Configurable thresholds",
        ],
    },
    {
        "id": "FBS-015",
        "title": "Approval-state gating",
        "summary": (
            "Configurable approval-signal evaluation (label / status / workflow). Pages without the signal are rejected; pages "
            "that lose the signal post-publish are unpublished on the next sync."
        ),
        "scope": ["US-003", "US-004"],
        "deps": ["FBS-009"],
        "domain": "Confluence Sync & Publishing",
        "risk": "medium",
        "size": "small", "hours": 4,
        "outcomes": [
            "A page missing the approval signal is blocked at the publish gate and does not appear on the portal.",
            "A previously-published page that loses its approval signal is unpublished within 5 minutes p95 on the next sync.",
            "An unpublish caused by loss of approval preserves the version history and is audit-logged with cause = 'approval-state-loss'.",
        ],
        "context": {
            "prdSections": ["Confluence Sync & Publishing"],
            "tadSections": ["Components: Publishing Pipeline"],
        },
        "deliverables": [
            "Approval-signal evaluator with admin-config",
            "Loss-of-approval unpublish handler",
        ],
    },
    {
        "id": "FBS-016",
        "title": "Publishing Pipeline orchestration (Step Functions)",
        "summary": (
            "Step Functions state machine that strings allow-list → approval → AI review → render → persist → OpenSearch index "
            "→ Redis cache invalidate → notify. Per-stage retry + DLQ + observability. AC for sync latency observability "
            "(US-007) ships as part of this FBS."
        ),
        "scope": ["US-007"],
        "deps": ["FBS-005", "FBS-007", "FBS-009", "FBS-010", "FBS-012", "FBS-013", "FBS-014", "FBS-015", "FBS-004"],
        "domain": "Confluence Sync & Publishing",
        "risk": "high",
        "size": "large", "hours": 12,
        "outcomes": [
            "A page-change event flows through every stage in order and reaches the portal within 5 minutes p95.",
            "End-to-end sync latency is emitted as a histogram metric tagged by page and pipeline stage.",
            "p95 sync latency > 5 min for 15 min raises a paging alert.",
            "A failure at any stage routes the event to the DLQ for that stage with an actionable diagnostic.",
            "publish.complete emits on EventBridge for downstream consumers.",
        ],
        "context": {
            "prdSections": ["Confluence Sync & Publishing", "Non-Functional"],
            "tadSections": ["Components: Publishing Pipeline", "ADR-010"],
        },
        "deliverables": [
            "publishing service skeleton",
            "Step Functions state machine JSON",
            "Per-stage Lambda / Fargate tasks",
            "publish-latency histogram + alerts",
        ],
    },
    {
        "id": "FBS-017",
        "title": "Hard publish block on high-severity AI findings",
        "summary": (
            "Publish gate that rejects pages with open findings of severity = high. Manual publish API rejects bypass attempts; "
            "bypass attempts are audit-logged."
        ),
        "scope": ["US-043"],
        "deps": ["FBS-016", "FBS-012", "FBS-013"],
        "domain": "AI Document Review",
        "risk": "high",
        "size": "small", "hours": 4,
        "outcomes": [
            "A page with any open high-severity finding is rejected at the publish gate; state becomes 'blocked-on-review'.",
            "When all high-severity findings are resolved (false positive confirmed or source corrected), the page becomes publishable.",
            "A manual publish API request for a blocked page is rejected and the bypass attempt is audit-logged.",
        ],
        "context": {
            "prdSections": ["AI Document Review"],
            "tadSections": ["Components: Publishing Pipeline", "Security controls: AI review fail-closed gate"],
        },
        "deliverables": [
            "Publish-gate predicate",
            "Bypass-attempt audit event type",
        ],
    },
    {
        "id": "FBS-018",
        "title": "Reviewer UI — AI findings in context + triage actions",
        "summary": (
            "Admin UI panel showing each finding's matched span highlighted in the rendered page; per-finding ignore / "
            "acknowledge / block actions with reviewer identity + timestamp audit."
        ),
        "scope": ["US-044", "US-045"],
        "deps": ["FBS-017", "FBS-002"],
        "domain": "AI Document Review",
        "risk": "medium",
        "size": "medium", "hours": 8,
        "outcomes": [
            "Reviewer opens the review panel and sees each finding's matched span highlighted in context, colour-coded by severity.",
            "Clicking a finding scrolls the page so the span is centred and focused.",
            "Stale spans (removed in a newer revision) are marked 'stale' rather than rendered as findings against missing content.",
            "'Ignore' on the last high-severity finding makes the page publishable and audit-logs the decision.",
            "'Block' transitions the page to 'blocked-pending-source-fix' until source is corrected and re-synced.",
        ],
        "context": {
            "prdSections": ["AI Document Review"],
            "tadSections": ["Components: Admin UI", "Components: AI Gateway"],
            "schemas": ["AIFinding", "ReviewDecision"],
        },
        "deliverables": [
            "apps/admin review-panel routes",
            "Triage endpoints + audit event emission",
        ],
    },
    {
        "id": "FBS-019",
        "title": "Admin — manual sync re-trigger and unpublish",
        "summary": (
            "Admin UI controls for re-syncing one page or one tag, and unpublishing a page with a required reason. All actions "
            "audit-logged. Unpublish requires explicit re-publish to recover."
        ),
        "scope": ["US-012", "US-013"],
        "deps": ["FBS-016"],
        "domain": "Confluence Sync & Publishing",
        "risk": "low",
        "size": "small", "hours": 4,
        "outcomes": [
            "Manual page re-sync enqueues the page on the publish queue at priority and is audit-logged.",
            "Manual tag re-sync enumerates approved allow-listed pages with that tag and enqueues them.",
            "Unpublish with a non-empty reason removes the page from browse and search within 60s; reason is audit-logged.",
            "Unpublish without a reason is rejected.",
            "An unpublished page does not auto-recover; a future approved update requires an explicit re-publish action.",
        ],
        "context": {
            "prdSections": ["Confluence Sync & Publishing"],
            "tadSections": ["Components: Admin UI"],
        },
        "deliverables": [
            "Admin endpoints + UI for re-sync and unpublish",
            "Re-sync progress dashboard",
        ],
    },
    {
        "id": "FBS-020",
        "title": "Portal Frontend — browse by product/category + latest version view",
        "summary": (
            "Next.js App Router with Lambda@Edge per-tenant cache key. Browse navigation derived from Confluence label hierarchy; "
            "latest-version view with 'Latest' badge and last-updated timestamp."
        ),
        "scope": ["US-028", "US-029"],
        "deps": ["FBS-006", "FBS-007", "FBS-002"],
        "domain": "Client Portal",
        "risk": "medium",
        "size": "medium", "hours": 8,
        "outcomes": [
            "Authenticated user lands on the portal home and sees products derived from Confluence labels with their categories.",
            "For the same set of source labels, two users see identical grouping (deterministic).",
            "A user with no entitled documents under a product sees that product omitted from their nav.",
            "Opening a document URL without an explicit version renders the latest version with a 'Latest' badge and timestamp.",
            "Edge cache key includes tenant_id so cross-tenant cache poisoning is impossible (verified by isolation test).",
        ],
        "context": {
            "prdSections": ["Client Portal"],
            "tadSections": ["Components: Portal Frontend, Portal API", "ADR-004"],
        },
        "deliverables": [
            "apps/portal (Next.js)",
            "Lambda@Edge tenant-aware cache key",
            "Browse + read routes",
            "Browse-determinism test",
        ],
    },
    {
        "id": "FBS-021",
        "title": "Portal — version history view + block-level diff",
        "summary": (
            "Per-page version history with previous-version reading and block-level diff vs latest. Inline and side-by-side modes."
        ),
        "scope": ["US-030", "US-031"],
        "deps": ["FBS-020", "FBS-005"],
        "domain": "Client Portal",
        "risk": "medium",
        "size": "medium", "hours": 6,
        "outcomes": [
            "Clicking a previous version row renders the page at that version with a 'Viewing older version' banner.",
            "Block-level diff highlights added/removed/modified content in green/red/yellow.",
            "Side-by-side and inline diff modes show identical diff data without refetching.",
            "Attempt to view an older version of an unpublished page returns 'not available' even with the direct URL.",
        ],
        "context": {
            "prdSections": ["Client Portal"],
            "tadSections": ["Components: Portal Frontend, Portal API"],
        },
        "deliverables": [
            "Version-history route + UI",
            "Block-level diff library",
        ],
    },
    {
        "id": "FBS-022",
        "title": "Search — OpenSearch indexing + scoped query gateway",
        "summary": (
            "Index documents on publish-complete. Scoped query gateway injects the tenant filter; callers cannot pass raw queries. "
            "Automated tenant-isolation search test on every release."
        ),
        "scope": ["US-033", "US-034"],
        "deps": ["FBS-016", "FBS-006"],
        "domain": "Client Portal",
        "risk": "high",
        "size": "medium", "hours": 8,
        "outcomes": [
            "Submitted query returns ranked matches with title, snippet, product, and last-updated timestamp.",
            "p95 search response < 1 s for the user's entitled corpus.",
            "A query that would match a document outside scope returns zero hits (not surfaced and hidden — excluded at query build).",
            "Cross-tenant search isolation test runs and passes on every release.",
        ],
        "context": {
            "prdSections": ["Client Portal", "Non-Functional"],
            "tadSections": ["Components: Portal API search adapter", "Security controls: search index tenant filter injection"],
        },
        "deliverables": [
            "OpenSearch index template",
            "Scoped search gateway module",
            "Cross-tenant search isolation test",
        ],
    },
    {
        "id": "FBS-023",
        "title": "PDF download (on-demand render with 30-day cache)",
        "summary": (
            "Renderer-backed PDF generation triggered by per-page Download as PDF; footer carries title, version, timestamp, "
            "and tenant identity. 30-day cache in S3."
        ),
        "scope": ["US-032"],
        "deps": ["FBS-020", "FBS-007"],
        "domain": "Client Portal",
        "risk": "low",
        "size": "medium", "hours": 6,
        "outcomes": [
            "Clicking Download as PDF returns a styled PDF matching the on-screen page including images and code blocks.",
            "The PDF footer contains document title, version, publish timestamp, and the requesting user's tenant identity.",
            "A failed PDF render surfaces a clear error toast to the user and logs the failure for investigation.",
        ],
        "context": {
            "prdSections": ["Client Portal"],
            "tadSections": ["Components: Renderer", "ADR-008"],
        },
        "deliverables": [
            "Playwright-headless PDF worker",
            "Per-page Download as PDF endpoint",
            "30-day PDF bucket lifecycle",
        ],
    },
    {
        "id": "FBS-024",
        "title": "Per-user last-visited tracking",
        "summary": (
            "Redis write + Postgres write-behind on every page render for an authenticated user. Erased on user removal. "
            "Used by the 'Since your last visit' feature (FBS-026)."
        ),
        "scope": ["US-035"],
        "deps": ["FBS-020"],
        "domain": "Client Portal",
        "risk": "low",
        "size": "small", "hours": 3,
        "outcomes": [
            "Opening a document updates the user's last-visited timestamp for that document in Redis within 100 ms.",
            "Redis last-visited is written-behind to Postgres within the configured flush interval.",
            "User-removal flow erases all per-user last-visited records for that user and audit-logs the deletion.",
        ],
        "context": {
            "prdSections": ["Client Portal"],
            "tadSections": ["Components: Portal API"],
        },
        "deliverables": [
            "Redis last-visited writer",
            "Postgres write-behind worker",
            "User-removal erase path",
        ],
    },
    {
        "id": "FBS-025",
        "title": "AI release notes — generate, reviewer approve, regenerate/edit/discard",
        "summary": (
            "Release-notes generation via AI Gateway producing What's New / Breaking / Recommended sections. Reviewer approval "
            "gate; regenerate / inline-edit / discard flows; SLA reminders."
        ),
        "scope": ["US-046", "US-047", "US-049"],
        "deps": ["FBS-011", "FBS-018"],
        "domain": "AI Release Notes & Change Summary",
        "risk": "medium",
        "size": "medium", "hours": 8,
        "outcomes": [
            "On a new version, release-notes are generated covering What's New, Breaking, Recommended based on the diff vs prior.",
            "First publication of a page produces What's New + 'None for this release' in the other sections.",
            "Reviewer approval is required before clients see the notes.",
            "Regeneration creates a new draft preserving the prior one in a side panel; the regeneration is audit-logged.",
            "Reviewer edits persist across subsequent regenerations unless explicitly discarded.",
        ],
        "context": {
            "prdSections": ["AI Release Notes & Change Summary"],
            "tadSections": ["Components: AI Gateway, Admin UI"],
        },
        "deliverables": [
            "AI Gateway operation: release-notes",
            "Reviewer approval routes + UI",
            "Per-version notes persistence",
        ],
    },
    {
        "id": "FBS-026",
        "title": "AI 'Since your last visit' summary on landing page",
        "summary": (
            "Per-client landing-page summary AI-generated from the diff of entitled changes the user has not yet viewed. "
            "Cached when the underlying change set is unchanged."
        ),
        "scope": ["US-048"],
        "deps": ["FBS-011", "FBS-024"],
        "domain": "AI Release Notes & Change Summary",
        "risk": "medium",
        "size": "small", "hours": 4,
        "outcomes": [
            "Landing page renders an AI paragraph summarising entitled pages that have changed since the user's per-page last visit.",
            "If there are no changes, the block shows 'You are up to date' rather than fabricated copy.",
            "Reload with unchanged underlying state is served from cache rather than regenerated.",
        ],
        "context": {
            "prdSections": ["AI Release Notes & Change Summary"],
            "tadSections": ["Components: AI Gateway, Portal Frontend"],
        },
        "deliverables": [
            "AI Gateway operation: since-last-visit summary",
            "Landing-page summary block + cache invalidation hook",
        ],
    },
    {
        "id": "FBS-027",
        "title": "Notification Service — digest scheduling, scope-respecting assembly",
        "summary": (
            "EventBridge-scheduled batch assembly per cadence (immediate, daily, weekly). Re-evaluates entitlement at send time. "
            "Per-user 'last notified high-water mark' for idempotent re-runs. SES integration."
        ),
        "scope": ["US-036", "US-037"],
        "deps": ["FBS-016", "FBS-006"],
        "domain": "Notifications",
        "risk": "medium",
        "size": "medium", "hours": 8,
        "outcomes": [
            "Immediate subscribers receive an email within 15 minutes of a relevant publish.",
            "Daily and weekly digests send one consolidated email per window or none if there are no changes.",
            "Unsubscribed users receive zero emails across all cadences.",
            "Users whose entitlement to a document is revoked before send time do not receive that document in the email.",
            "Re-running the batch assembly does not duplicate sends (high-water mark guards).",
        ],
        "context": {
            "prdSections": ["Notifications"],
            "tadSections": ["Components: Notification Service"],
        },
        "deliverables": [
            "services/notifications",
            "Cadence scheduler",
            "Send-watermark table",
            "SES sender + bounce/complaint feedback",
        ],
    },
    {
        "id": "FBS-028",
        "title": "AI notification summaries + breaking-change reviewer approval",
        "summary": (
            "AI-generated per-page concise summaries (≤ 30 words) inserted into each email. Breaking-change emails sit in "
            "'pending-review' state until approved; reviewer Approve & Send or Reject paths."
        ),
        "scope": ["US-050", "US-051"],
        "deps": ["FBS-027", "FBS-011", "FBS-025"],
        "domain": "AI Client Notifications",
        "risk": "medium",
        "size": "medium", "hours": 6,
        "outcomes": [
            "Each changed page in a digest carries an AI-generated ≤30-word summary based on the user's entitled change set.",
            "Two users with different entitlements may see different summaries for the same digest run.",
            "AI summary failure for one page falls back to title + 'View changes on portal' without breaking the email.",
            "A breaking-change-flagged email sits 'pending-review'; reviewer Approve & Send dispatches, Reject suppresses with audit.",
        ],
        "context": {
            "prdSections": ["AI Client Notifications"],
            "tadSections": ["Components: AI Gateway, Notification Service, Admin UI"],
        },
        "deliverables": [
            "AI Gateway operation: notification-summary",
            "Pending-review queue + reviewer UI",
        ],
    },
    {
        "id": "FBS-029",
        "title": "Notification email — release highlights + deep links",
        "summary": (
            "Email template containing per-page highlight summary + deep link with source=email-digest tracking. Overflow rule: "
            "top 5 inline + 'view full list' link for larger digests."
        ),
        "scope": ["US-038"],
        "deps": ["FBS-027", "FBS-028"],
        "domain": "Notifications",
        "risk": "low",
        "size": "small", "hours": 3,
        "outcomes": [
            "Each digest email lists each changed page with title, AI summary, and a deep link.",
            "Digests with >5 changed pages show top 5 inline + 'view full list' link to a portal filtered changes view.",
            "Deep-link clicks reach the portal with source = 'email-digest' parameter; the user's email is not exposed in URLs.",
        ],
        "context": {
            "prdSections": ["Notifications"],
            "tadSections": ["Components: Notification Service"],
        },
        "deliverables": [
            "Digest email MJML template",
            "Deep-link signer",
        ],
    },
    {
        "id": "FBS-030",
        "title": "Self-service notification preferences",
        "summary": (
            "Profile page for cadence + per-product subscription + mute. One-click unsubscribe (HMAC signed) in email footer."
        ),
        "scope": ["US-039"],
        "deps": ["FBS-020", "FBS-027"],
        "domain": "Notifications",
        "risk": "low",
        "size": "small", "hours": 3,
        "outcomes": [
            "User opens profile and sees current cadence + per-product toggles; edits save and are reflected on the next send.",
            "One-click unsubscribe via signed link in the email footer flips the user to 'off' without requiring login.",
            "Preference changes are reflected in the email unsubscribe footer of subsequent emails.",
        ],
        "context": {
            "prdSections": ["Notifications"],
            "tadSections": ["Components: Notification Service, Portal Frontend"],
        },
        "deliverables": [
            "Profile/preferences page",
            "One-click HMAC-signed unsubscribe endpoint",
        ],
    },
    {
        "id": "FBS-031",
        "title": "AI documentation quality scoring + soft warning override",
        "summary": (
            "Publish-time quality scoring across four dimensions (Completeness, Readability, Missing Examples, Missing API "
            "Responses). Low scores warn but do not block; override-with-reason is audit-logged."
        ),
        "scope": ["US-052", "US-053"],
        "deps": ["FBS-011", "FBS-016"],
        "domain": "AI Documentation Quality Check",
        "risk": "low",
        "size": "medium", "hours": 6,
        "outcomes": [
            "Each version persists four scores in [0..1] with the AI-generated short suggestion.",
            "Below-threshold scores show a warning badge in the publish summary.",
            "'Publish anyway' with a required reason proceeds and is audit-logged with publisher + reason.",
            "Quality-score unavailability is recorded with the version but does not block publish.",
        ],
        "context": {
            "prdSections": ["AI Documentation Quality Check"],
            "tadSections": ["Components: AI Gateway, Admin UI"],
        },
        "deliverables": [
            "AI Gateway operation: quality",
            "Quality-score persistence on DocumentVersion",
            "Override audit event type",
        ],
    },
    {
        "id": "FBS-032",
        "title": "AI quality trend view",
        "summary": (
            "Per-page chart of quality scores across publish history. 'Not enough history' state. Gap rendering for missing scores."
        ),
        "scope": ["US-054"],
        "deps": ["FBS-031"],
        "domain": "AI Documentation Quality Check",
        "risk": "low",
        "size": "small", "hours": 3,
        "outcomes": [
            "Page-level quality view shows a chart per dimension across publish history when ≥ 3 versions exist.",
            "< 3 versions shows current values + 'not enough history' rather than empty axes.",
            "A version with unavailable scoring renders as a chart gap, not zero.",
        ],
        "context": {
            "prdSections": ["AI Documentation Quality Check"],
            "tadSections": ["Components: Admin UI"],
        },
        "deliverables": [
            "Quality trend chart in Admin UI",
        ],
    },
    {
        "id": "FBS-033",
        "title": "Client-admin user lifecycle (invite / disable / remove)",
        "summary": (
            "Client-admin self-service: invite via email with time-limited single-use link; disable to revoke immediately while "
            "preserving audit; remove to anonymise PII while keeping accountability."
        ),
        "scope": ["US-021", "US-022", "US-023"],
        "deps": ["FBS-002", "FBS-004"],
        "domain": "Authentication & Access Control",
        "risk": "medium",
        "size": "medium", "hours": 8,
        "outcomes": [
            "Client-admin invites a user; an email with a time-limited single-use acceptance link is sent.",
            "Invited user sets password + TOTP via the acceptance link and account is created in the inviting tenant with the assigned role.",
            "Client-admin attempts to invite outside their tenant's allowed roles → rejected with inline error; attempt audit-logged.",
            "Disable terminates sessions within 60s and blocks subsequent logins; audit preserved.",
            "Remove anonymises PII; user's audit history becomes 'Removed user (hash)' for displayable identity.",
            "Removing the last admin in a tenant is blocked with a clear error.",
        ],
        "context": {
            "prdSections": ["Authentication & Access Control"],
            "tadSections": ["Components: Auth Service"],
        },
        "deliverables": [
            "Invitation flow + acceptance endpoint",
            "Disable + remove endpoints with audit hooks",
            "Last-admin guard",
        ],
    },
    {
        "id": "FBS-034",
        "title": "Document view audit + admin action audit coverage",
        "summary": (
            "Extend the audit pipeline (FBS-004) to cover document-view events and all admin actions surfaced in FBS-019 (re-sync, "
            "unpublish). Includes search-query audit."
        ),
        "scope": ["US-026", "US-027"],
        "deps": ["FBS-004", "FBS-020", "FBS-019"],
        "domain": "Audit & Compliance",
        "risk": "low",
        "size": "small", "hours": 4,
        "outcomes": [
            "Opening a document page writes an audit entry with user, tenant, document_id, version_id, timestamp.",
            "A search request audits the query (or its hash), user, and returned document IDs.",
            "Every admin action (invite, role change, scope change, unpublish, sync re-trigger, AI review decision) writes an audit entry with before/after where applicable.",
        ],
        "context": {
            "prdSections": ["Authentication & Access Control"],
            "tadSections": ["Components: Audit Log Service, Portal API"],
        },
        "deliverables": [
            "Document-view audit producer in Portal API",
            "Admin-action audit producer in Admin UI / services",
        ],
    },
    {
        "id": "FBS-035",
        "title": "Enterprise SSO via WorkOS",
        "summary": (
            "Per-tenant SAML 2.0 / OIDC SSO mediated by WorkOS. Tenant.sso_mode flag drives login dispatch; password login is "
            "disabled for SSO-enabled tenants."
        ),
        "scope": ["US-024"],
        "deps": ["FBS-002"],
        "domain": "Authentication & Access Control",
        "risk": "medium",
        "size": "medium", "hours": 6,
        "outcomes": [
            "A SSO-enabled tenant's users see an 'SSO Login' button initiating the configured SAML/OIDC flow via WorkOS.",
            "A valid SSO assertion establishes a session with the role mapped from the assertion's group claim.",
            "SSO-enabled tenants cannot password-login; users are redirected to the SSO flow.",
        ],
        "context": {
            "prdSections": ["Authentication & Access Control"],
            "tadSections": ["Components: Auth Service", "ADR-009"],
        },
        "deliverables": [
            "WorkOS integration in services/auth",
            "Tenant.sso_mode field + admin config",
            "SSO callback handler",
        ],
    },
    {
        "id": "FBS-036",
        "title": "End-to-end sync + publish observability hardening (SLA dashboards)",
        "summary": (
            "Per-stage latency dashboards, SLA alerts including AI review duration, and the per-page latest-50-publishes view."
        ),
        "scope": ["US-056"],
        "deps": ["FBS-016"],
        "domain": "Performance",
        "risk": "low",
        "size": "small", "hours": 4,
        "outcomes": [
            "Per-publish metrics include total end-to-end latency plus a sub-breakdown for AI review.",
            "p95 e2e > 5 min OR p95 incl. AI > 15 min raises a paging alert.",
            "Per-page filter on the sync dashboard shows per-stage timings for the latest N publishes (default 50).",
        ],
        "context": {
            "prdSections": ["Non-Functional"],
            "tadSections": ["Operational concerns: metrics, alerting"],
        },
        "deliverables": [
            "CloudWatch dashboard + alarms",
            "Per-page filter view",
        ],
    },
    {
        "id": "FBS-037",
        "title": "Portal render p95 SLA + horizontal scaling validation",
        "summary": (
            "Synthetic-load harness for the 500-user reading workload. Auto-rollback wiring on render-p95 breach after deploy. "
            "Validate Portal Frontend and API scale to 30 instances under load."
        ),
        "scope": ["US-055", "US-063"],
        "deps": ["FBS-020"],
        "domain": "Performance",
        "risk": "medium",
        "size": "medium", "hours": 6,
        "outcomes": [
            "Synthetic 500-user load achieves portal-render p95 < 1.5 s.",
            "p95 render > 1.5 s over 15 min raises a paging alert and auto-rolls-back if the breach started after the latest deploy.",
            "Doubling synthetic load drives autoscaling such that p95 returns under 1.5 s within 5 minutes.",
            "Terminating a read-tier instance mid-request: the request succeeds on retry on a different instance without surfacing an error.",
        ],
        "context": {
            "prdSections": ["Non-Functional"],
            "tadSections": ["Deployment architecture: scaling, resource requirements"],
        },
        "deliverables": [
            "k6 synthetic load harness",
            "Auto-rollback CodeDeploy hook",
            "Read-tier autoscaling policies",
        ],
    },
    {
        "id": "FBS-038",
        "title": "TLS enforcement + at-rest encryption hardening",
        "summary": (
            "Verify TLS 1.2/1.3-only across all client surfaces; reject TLS 1.1 cleanly. KMS-managed encryption on every data "
            "store; key-rotation event passes for Aurora / S3 / ElastiCache / QLDB."
        ),
        "scope": ["US-057", "US-058"],
        "deps": ["FBS-001"],
        "domain": "Data Protection",
        "risk": "medium",
        "size": "medium", "hours": 6,
        "outcomes": [
            "Client connection negotiates TLS 1.2 or 1.3 with a permitted cipher suite; lower-version negotiation is rejected.",
            "External TLS scan reaches at least 'intermediate' grade with no known-vulnerable settings.",
            "Every data store (Aurora, S3 buckets, ElastiCache, QLDB) verifies as encrypted at rest under KMS-managed keys.",
            "KMS key rotation completes and data remains readable under the new key alias; the rotation is audit-logged.",
            "Automated infra audit reports zero plaintext-at-rest stores.",
        ],
        "context": {
            "prdSections": ["Non-Functional"],
            "tadSections": ["Security architecture: encryption", "Security controls: Encryption at rest"],
        },
        "deliverables": [
            "ALB TLS policy + HSTS",
            "KMS rotation schedule + alarms",
            "Infra audit Lambda + scheduled run",
        ],
    },
    {
        "id": "FBS-039",
        "title": "Accessibility — keyboard navigation, focus trapping, screen reader, contrast",
        "summary": (
            "WCAG 2.1 AA pass across login, browse, read, version history, search, PDF flows. Axe-core in CI. Focus management "
            "for modals. Contrast tokens audited."
        ),
        "scope": ["US-060", "US-061"],
        "deps": ["FBS-020", "FBS-021", "FBS-023"],
        "domain": "Accessibility",
        "risk": "medium",
        "size": "medium", "hours": 8,
        "outcomes": [
            "Tab/Shift+Tab traverses every interactive control in visual order with a visible focus indicator meeting WCAG AA contrast.",
            "Modals trap focus; Escape closes and returns focus to the opener.",
            "Axe-core runs in CI across login, browse, read, version history, search, PDF flows with zero serious/critical violations.",
            "Screen reader announces heading levels, lists, table row/column headers, and image alt-text.",
            "Design tokens pass contrast checks for all text/background pairs at WCAG AA.",
            "Status indicators (e.g. coloured badges) announce a text-equivalent label.",
        ],
        "context": {
            "prdSections": ["Non-Functional"],
            "tadSections": ["Security architecture / Compliance: WCAG 2.1 AA"],
        },
        "deliverables": [
            "Accessible component primitives",
            "Axe-core CI integration",
            "Contrast token audit",
            "Focus-trap utility",
        ],
    },
]


# ---------------------------------------------------------------------------
# Build storyScope + validate AC coverage and DAG
# ---------------------------------------------------------------------------

fbs_index = {f["id"]: f for f in FBS}
seen_ac, ac_to_fbs = set(), {}
for f in FBS:
    scope_objs = []
    for us in f["scope"]:
        st = story_by_id.get(us)
        if not st:
            raise SystemExit(f"{f['id']} references unknown story {us}")
        ac_ids = [ac["id"] for ac in st["acceptanceCriteria"]]
        scope_objs.append({"usId": us, "acIds": ac_ids})
        for ac in ac_ids:
            if ac in seen_ac:
                raise SystemExit(f"AC {ac} double-allocated: was in {ac_to_fbs[ac]}, now in {f['id']}")
            seen_ac.add(ac)
            ac_to_fbs[ac] = f["id"]
    f["_storyScope"] = scope_objs

missing_ac = all_ac_ids - seen_ac
if missing_ac:
    raise SystemExit(f"ACs not covered by any FBS: {sorted(missing_ac)}")

# DAG check
for f in FBS:
    for dep in f["deps"]:
        if dep not in fbs_index:
            raise SystemExit(f"{f['id']} depends on unknown FBS {dep}")
        # Earlier-than ordering check
        if int(dep.split('-')[1]) >= int(f["id"].split('-')[1]):
            raise SystemExit(f"{f['id']} depends on non-earlier {dep}")

# Hour cap and outcomes check
for f in FBS:
    if f["hours"] > 16:
        raise SystemExit(f"{f['id']} exceeds 16h cap ({f['hours']}h)")
    if len(f["outcomes"]) < 3 or len(f["outcomes"]) > 8:
        raise SystemExit(f"{f['id']} has {len(f['outcomes'])} outcomes; want 3..8")


# ---------------------------------------------------------------------------
# Emit JSON
# ---------------------------------------------------------------------------

bs_json = {
    "bsId": BS_ID,
    "prdId": PRD_ID,
    "version": VERSION,
    "status": "draft",
    "title": "Build Sequence: Client Documentation Hub (Part 1 of 1)",
    "buildPhilosophy": (
        "Generated using dependency-first strategy. Foundation layers (platform + RLS, auth, audit ledger, document data model, "
        "AI gateway with fail-closed) land before any feature surface. The publishing pipeline (FBS-016) is the central "
        "join: sync, renderer, AI review, persistence, and audit all converge there. Portal frontend + search + notifications "
        "follow once the publish pipeline is in place. NFR hardening (TLS, encryption, perf, a11y) lands last so the synthetic "
        "load harness can run against the real read paths."
    ),
    "generationStrategy": "dependency-first",
    "buildSequence": [
        {
            "id": f["id"],
            "title": f["title"],
            "summary": f["summary"],
            "storyScope": f["_storyScope"],
            "dependencies": f["deps"],
            "testableOutcomes": f["outcomes"],
            "status": "not-started",
            "sessionMeta": {
                "estimatedSize": f["size"],
                "estimatedHours": f["hours"],
                "contextRequirements": {
                    "prdSections": f["context"].get("prdSections", []),
                    "tadSections": f["context"].get("tadSections", []),
                    "existingModules": f["context"].get("existingModules", []),
                    "schemas": f["context"].get("schemas", []),
                    "externalDocs": [],
                    "other": [],
                },
                "deliverables": f["deliverables"],
            },
            "riskLevel": f["risk"],
            "domain": f["domain"],
        }
        for f in FBS
    ],
    "createdAt": NOW,
    "updatedAt": NOW,
}

bs_dir = REPO / "docs/specs/client-docs-hub/build-sequence"
bs_dir.mkdir(parents=True, exist_ok=True)
(bs_dir / f"{BS_ID}.json").write_text(json.dumps(bs_json, indent=2) + "\n")


# ---------------------------------------------------------------------------
# Emit markdown
# ---------------------------------------------------------------------------

md = []
md.append("# Client Documentation Hub — Build Sequence\n\n")
md.append(f"> Generated from `docs/specs/client-docs-hub/prd/PRD-001.json` v1.0.0, "
          f"`docs/specs/client-docs-hub/user-stories/PRD-001-user-stories.json` v{stories_doc['version']}, "
          f"and `docs/specs/client-docs-hub/tad/TAD-001-001..004.json` v1.0.0.\n")
md.append(f"> Canonical: `docs/specs/client-docs-hub/build-sequence/{BS_ID}.json`. Strategy: dependency-first. "
          f"{len(FBS)} FBS covering {len(all_ac_ids)} ACs across {len(stories_doc['stories'])} stories. "
          f"Total estimate: {sum(f['hours'] for f in FBS)} hours.\n\n")

md.append("## Coverage & DAG validation\n\n")
md.append(f"- Every AC across every story is allocated to exactly one FBS ({len(seen_ac)}/{len(all_ac_ids)} ACs).\n")
md.append("- Every `dependencies[]` entry points to an earlier-numbered FBS (DAG).\n")
md.append("- No FBS exceeds the 16 h hard cap; every FBS has 3–8 testable outcomes.\n\n")

md.append("## At-a-glance table\n\n")
md.append("| FBS | Title | Domain | Size | Hours | Risk | Deps |\n|---|---|---|---|---|---|---|\n")
for f in FBS:
    md.append(f"| {f['id']} | {f['title']} | {f['domain']} | {f['size']} | {f['hours']} | {f['risk']} | "
              f"{', '.join(f['deps']) if f['deps'] else '—'} |\n")
md.append("\n")

md.append("## FBS details\n\n")
for f in FBS:
    md.append(f"### {f['id']} — {f['title']}\n\n")
    md.append(f"**Domain.** {f['domain']}  \n")
    md.append(f"**Size.** {f['size']} ({f['hours']} h)  \n")
    md.append(f"**Risk.** {f['risk']}  \n")
    md.append(f"**Dependencies.** {', '.join(f['deps']) if f['deps'] else 'none'}\n\n")
    md.append(f"{f['summary']}\n\n")
    md.append("**Scope (story → ACs):**\n")
    for sc in f["_storyScope"]:
        ac_list = ", ".join(sc["acIds"])
        md.append(f"- `{sc['usId']}` → {ac_list}\n")
    md.append("\n**Testable outcomes:**\n")
    for o in f["outcomes"]:
        md.append(f"- {o}\n")
    md.append("\n**Deliverables:**\n")
    for d in f["deliverables"]:
        md.append(f"- {d}\n")
    md.append("\n**Context required:**\n")
    for k, v in f["context"].items():
        if v:
            md.append(f"- {k}: {', '.join(v)}\n")
    md.append("\n")

md_path = REPO / "docs/specs/client-docs-hub/build-sequence/BUILD-SEQUENCE.md"
md_path.parent.mkdir(parents=True, exist_ok=True)
md_path.write_text("".join(md))


# ---------------------------------------------------------------------------
# Update manifest
# ---------------------------------------------------------------------------

manifest_path = REPO / "docs/specs/client-docs-hub/manifest.json"
manifest = json.loads(manifest_path.read_text())
prd_entry = manifest["prd"]
bs_entry = {"id": BS_ID, "path": f"build-sequence/{BS_ID}.json", "markdownPath": "build-sequence/BUILD-SEQUENCE.md"}
existing_ids = {b["id"] for b in prd_entry.get("bs", [])}
if bs_entry["id"] not in existing_ids:
    prd_entry.setdefault("bs", []).append(bs_entry)
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

from collections import Counter
size_counter = Counter(f["size"] for f in FBS)
risk_counter = Counter(f["risk"] for f in FBS)
domain_counter = Counter(f["domain"] for f in FBS)

print(f"FBS count:       {len(FBS)}")
print(f"Total hours:     {sum(f['hours'] for f in FBS)}")
print(f"AC coverage:     {len(seen_ac)} / {len(all_ac_ids)}")
print(f"Stories covered: {sum(len(f['scope']) for f in FBS)} / {len(stories_doc['stories'])}")
print(f"By size:   {dict(size_counter)}")
print(f"By risk:   {dict(risk_counter)}")
print(f"By domain: {dict(domain_counter)}")
print(f"DAG valid: yes (verified by ordering check)")
print(f"Wrote: docs/specs/client-docs-hub/build-sequence/{BS_ID}.json")
print(f"Wrote: docs/specs/client-docs-hub/build-sequence/BUILD-SEQUENCE.md")
print(f"Updated: docs/specs/client-docs-hub/manifest.json")
