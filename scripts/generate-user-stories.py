#!/usr/bin/env python3
"""
One-shot generator for PRD-001 user stories.

Authors stories + ACs once and emits both the markdown view
(docs/specs/client-docs-hub/user-stories/USER-STORIES.md) and the RCF JSON
(docs/specs/client-docs-hub/user-stories/PRD-001-user-stories.json).

Run from repo root:  python3 scripts/generate-user-stories.py
"""

from __future__ import annotations
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

PRD_ID = "PRD-001"
VERSION = "1.0.0"
REPO = Path(__file__).resolve().parent.parent

STORIES: list[dict] = []
_ac_seq = 0


def s(req: str, asA: str, iWant: str, soThat: str, title: str, acs: list[str]) -> None:
    """Append a story; AC IDs are assigned sequentially across the file."""
    global _ac_seq
    us_id = f"US-{len(STORIES) + 1:03d}"
    ac_list = []
    for a in acs:
        _ac_seq += 1
        ac_list.append({"id": f"AC-{_ac_seq:03d}", "description": a, "testable": True})
    STORIES.append({
        "id": us_id,
        "reqId": req,
        "title": title,
        "description": f"As a {asA}, I want {iWant} so that {soThat}.",
        "asA": asA,
        "iWant": iWant,
        "soThat": soThat,
        "acceptanceCriteria": ac_list,
    })


# ---------------------------------------------------------------------------
# Theme: Confluence Sync & Publishing
# ---------------------------------------------------------------------------

s("REQ-001",
  "documentation administrator",
  "to manage the allow-list of Confluence labels and source spaces that are eligible to sync",
  "only intentionally-tagged pages can ever be published to the client portal",
  "Manage sync allow-list",
  [
    "Given an admin opens the sync configuration page, when they add a label to the allow-list and save, then the label appears in the active list and the change is audit-logged with the admin's identity and timestamp.",
    "Given an admin removes a label from the allow-list, when the next sync cycle runs, then pages whose only allow-list match was that label are unpublished from the portal and the unpublish is audit-logged.",
    "Given an unauthenticated user or a user without the admin role, when they request the sync configuration page, then they receive a 403 and the attempt is audit-logged.",
  ])

s("REQ-001",
  "sync engine",
  "to evaluate each candidate Confluence page against the active allow-list before considering it for publish",
  "pages outside the configured tag/space scope never enter the publishing pipeline",
  "Sync engine respects allow-list",
  [
    "Given a Confluence page that carries no allow-listed label and lives outside any allow-listed space, when the sync cycle runs, then the page is skipped and a debug-level log records the skip with the page ID.",
    "Given a Confluence page that carries at least one allow-listed label, when the sync cycle runs, then the page proceeds to the approval-state check (REQ-002).",
    "Given the allow-list is empty, when the sync cycle runs, then zero pages are published and an admin-visible warning is surfaced.",
  ])

s("REQ-002",
  "publishing pipeline",
  "to publish only Confluence pages whose configured approval signal is present",
  "drafts and in-review pages never reach clients",
  "Approval-state gating",
  [
    "Given a Confluence page with the configured approval signal absent (e.g. draft state, missing approval label), when the sync evaluates it, then publishing is blocked and the page does not appear on the portal.",
    "Given a Confluence page with the configured approval signal present, when the sync evaluates it, then it proceeds to the AI document-review stage (REQ-040).",
    "Given an admin reconfigures the approval signal, when the change is saved, then the active signal is logged and the next sync cycle applies the new rule.",
  ])

s("REQ-002",
  "publishing pipeline",
  "to unpublish a page that loses its approval state after publish",
  "the portal never serves content that has reverted to draft",
  "Loss of approval triggers unpublish",
  [
    "Given a previously published page, when its approval signal is removed in Confluence, then on the next sync cycle the page is unpublished from the portal within 5 minutes (p95).",
    "Given a page is unpublished due to loss of approval, when a client navigates to its URL, then they receive a clear 'not available' message rather than a stale cached copy.",
    "Given a page is unpublished due to loss of approval, when the unpublish completes, then the version history of that page is preserved and the unpublish event is audit-logged with cause = 'approval-state-loss'.",
  ])

s("REQ-003",
  "sync engine",
  "to receive Confluence page-change webhooks and publish updates within the SLA",
  "approved changes reach the portal in near real-time without operator action",
  "Webhook-driven sync within SLA",
  [
    "Given a webhook event arrives for an approved, allow-listed page, when the sync pipeline processes it, then the new version is visible on the portal within 5 minutes at p95 measured from webhook receipt to portal cache hit.",
    "Given the webhook delivery is duplicated (Confluence retries), when the pipeline processes the duplicate, then no duplicate version is created and the duplicate is recorded as deduped in logs.",
    "Given a webhook payload that fails schema validation, when received, then the event is rejected with a 400 and an alert is raised, with no partial publish.",
  ])

s("REQ-003",
  "sync engine",
  "to fall back to a polling sync on a configurable interval when webhooks are unavailable",
  "the portal stays in sync even if Confluence cannot deliver webhooks",
  "Polling sync fallback",
  [
    "Given webhooks have been disabled or have failed for longer than a configurable threshold, when the polling interval elapses, then the engine fetches the recently-changed page list from Confluence and processes eligible pages.",
    "Given polling is active and a page has been updated since the last poll, when the engine processes it, then it follows the same allow-list → approval → AI-review path as webhook-driven sync.",
    "Given webhooks recover, when the first webhook arrives after recovery, then polling continues for one additional cycle to backfill any missed events, then quiesces.",
  ])

s("REQ-003",
  "platform engineer",
  "to observe sync latency as a first-class metric with alerting",
  "the SLA is enforced operationally and regressions are caught before clients notice",
  "Sync latency observability",
  [
    "Given the sync pipeline is running, when a page completes publishing, then the end-to-end latency from approval to portal visibility is emitted as a histogram metric tagged by page and pipeline stage.",
    "Given p95 sync latency exceeds 5 minutes over a rolling 15-minute window, when the threshold is breached, then a paging alert is fired to the on-call channel.",
    "Given a platform engineer opens the sync dashboard, when they select a time range, then they see per-stage latency breakdowns (webhook receipt → allow-list → approval → AI review → publish).",
  ])

s("REQ-004",
  "publishing pipeline",
  "to persist each successful publish as an immutable version with at least the last 20 versions retained per page",
  "clients and auditors can refer back to any recent published state",
  "Version history retention",
  [
    "Given a page is successfully published, when the publish commits, then a new immutable version record is written containing the rendered content, publish timestamp, source Confluence version ID, and publisher identity.",
    "Given a page has 21 published versions, when the 22nd is published, then the oldest version is dropped from active storage but its metadata (timestamp, source version, publisher) is retained in the audit log.",
    "Given an attempt to modify an existing version record, when the write is issued, then the data layer rejects it and the attempt is audit-logged as a tamper attempt.",
  ])

s("REQ-004",
  "portal user",
  "to see metadata for each version of a page (when published, by whom, source Confluence revision)",
  "I can decide which version to read or cite",
  "Version metadata visible to clients",
  [
    "Given a portal user opens the version history view of a page, when the page renders, then each listed version shows publish timestamp, version number, and the source Confluence revision number.",
    "Given a portal user hovers / focuses a version row, when the row is active, then a tooltip / detail panel shows the publisher's name in a non-PII-leaking form (display name only).",
    "Given a version row is rendered, when no source Confluence revision is available (legacy import), then 'Source revision: unavailable' is shown rather than an empty field.",
  ])

s("REQ-005",
  "publishing pipeline",
  "to preserve Confluence page structure on publish for headings, lists, tables, code blocks, and inline images",
  "the portal reads as faithfully as the Confluence source",
  "Render fidelity for rich content",
  [
    "Given a Confluence page containing headings (h1–h4), lists, tables, code blocks (with language hint), and inline images, when the page is published, then the rendered portal page preserves the same structural elements with the same semantic markup.",
    "Given a code block in Confluence has a language hint, when the page is rendered on the portal, then the corresponding code block carries the matching language class for syntax highlighting.",
    "Given an inline image in Confluence, when the page is rendered on the portal, then the image is served from a per-page asset path with the same alt-text as the source.",
  ])

s("REQ-005",
  "publishing pipeline",
  "to rewrite cross-page links so links to published pages resolve and links to non-published pages do not leak",
  "clients never click into broken or unauthorized destinations",
  "Cross-link rewriting",
  [
    "Given a Confluence cross-link points to another page that is also published in the portal, when the source page renders, then the link target is rewritten to the portal URL of the destination version.",
    "Given a Confluence cross-link points to a page that is not published (not allow-listed, not approved, or unpublished), when the source page renders, then the link is rendered as inert text with a 'not available' tooltip rather than a live link.",
    "Given an external link (e.g. https://example.com) in Confluence, when the page is published, then the link is preserved verbatim and opens in a new tab with rel='noopener'.",
  ])

s("REQ-006",
  "documentation owner",
  "to manually re-trigger sync of an individual page or tag set from the admin UI",
  "I can recover from a missed automatic sync without filing a platform ticket",
  "Manual sync re-trigger",
  [
    "Given a doc owner opens the admin UI and selects a page, when they click 'Re-sync this page', then the page is enqueued for the sync pipeline with priority and the action is audit-logged with their identity.",
    "Given a doc owner selects a tag set and clicks 'Re-sync tag', when the action is submitted, then every approved, allow-listed page carrying that tag is re-evaluated by the pipeline.",
    "Given a re-sync action is in progress, when the doc owner returns to the admin UI, then they see the status (queued / running / complete / failed) for each enqueued page.",
  ])

s("REQ-007",
  "documentation owner",
  "to unpublish a page from the portal without deleting it from Confluence, supplying a reason",
  "I can quickly remove a page that was published in error and keep an auditable record",
  "Unpublish with audit reason",
  [
    "Given a doc owner selects a published page and clicks 'Unpublish', when they supply a non-empty reason and confirm, then the page is removed from portal browse and search within 60 seconds and the action is audit-logged with the supplied reason.",
    "Given a page has been unpublished, when the same page later receives an approved update in Confluence, then a re-publish requires an explicit re-publish action (it does not auto-recover) and the link between the unpublish and the re-publish is recorded in the audit trail.",
    "Given a doc owner attempts to unpublish without supplying a reason, when they submit, then the action is rejected with an inline error and no state changes.",
  ])

# ---------------------------------------------------------------------------
# Theme: Authentication & Access Control
# ---------------------------------------------------------------------------

s("REQ-010",
  "portal visitor",
  "to be redirected to a login screen whenever I try to access any portal page unauthenticated",
  "no portal content is reachable without a login",
  "Unauthenticated access redirects to login",
  [
    "Given an unauthenticated visitor requests any non-login URL on docs.wsd.com, when the request is received, then the server responds with a 302 to the login page carrying a signed redirect-back parameter for the original destination.",
    "Given an unauthenticated visitor requests a portal API endpoint, when the request is received, then the server responds with 401 and a JSON error body, not HTML.",
    "Given a visitor completes login from a deep-link redirect, when authentication succeeds, then they land on the originally-requested URL rather than the portal home.",
  ])

s("REQ-011",
  "portal user",
  "to log in with my password plus a second factor (TOTP or email magic link)",
  "my account is protected against password-only compromise",
  "Password plus second-factor login",
  [
    "Given a user with a valid password and an enrolled TOTP authenticator, when they enter both correctly, then a session is established and they are routed to their entitled home page.",
    "Given a user submits a valid password but no second factor is configured for their account, when login proceeds, then the system offers a one-time email magic-link as the second factor and blocks session establishment until it is consumed.",
    "Given a user submits a valid password but an incorrect or expired TOTP code, when they submit, then the login is rejected with a generic error message (no information about which factor failed) and the attempt is rate-limited.",
  ])

s("REQ-011",
  "portal user",
  "to have my session managed with HTTP-only Secure cookies, configurable timeout, and idempotent logout",
  "stolen cookies and stale tabs are not a path to account compromise",
  "Session lifecycle",
  [
    "Given a successful login, when the session cookie is set, then it has the Secure, HttpOnly, and SameSite=Strict attributes and is bound to the docs.wsd.com domain.",
    "Given a session has been idle longer than the configured timeout, when the user issues any request, then the session is invalidated server-side and they are redirected to login.",
    "Given a user clicks 'Log out', when the action is processed, then the session is invalidated server-side and the cookie is cleared client-side; repeated logout requests have no additional effect (idempotent).",
  ])

s("REQ-011",
  "platform operator",
  "to have password and second-factor brute-force attempts rate-limited and locked out",
  "credential stuffing campaigns are slowed and detectable",
  "Rate limiting and lockout",
  [
    "Given more than 5 failed login attempts for a single user identifier within 10 minutes, when the next attempt arrives, then the attempt is rejected with a generic error and the user receives an email notification of the lockout.",
    "Given a locked account, when the lockout window (configurable, default 15 minutes) elapses, then the lockout is lifted and the user may try again.",
    "Given a sustained pattern of failed logins across many user identifiers from a single IP, when the IP threshold is exceeded, then requests from that IP are 429-throttled for a configurable cooldown and the event is alerted to security.",
  ])

s("REQ-012",
  "portal user",
  "to only see documents scoped to my client tenant, even under direct URL access",
  "no UI manipulation or API guessing can reveal another client's documents",
  "Data-layer tenant scoping",
  [
    "Given an authenticated user whose tenant is 'acme', when they request a document URL whose scope is 'beta' (another tenant), then the response is 404 and the lookup is audit-logged as a cross-tenant attempt.",
    "Given an automated multi-tenant isolation test suite, when it runs on every release, then it asserts that every read endpoint enforces tenant scoping at the data-access layer (no relying on UI filtering).",
    "Given a user views a 'shared' document, when their tenant is resolved, then the access is permitted regardless of tenant; shared scope is the only public scope across tenants.",
  ])

s("REQ-013",
  "documentation owner",
  "to mark a Confluence page as 'shared' so it appears to every authenticated client tenant",
  "common product documentation is available to all clients without duplication",
  "Shared document visibility",
  [
    "Given a Confluence page carries the configured 'shared' label, when it is published, then the document is visible to every authenticated user across all client tenants.",
    "Given a previously-shared page has its 'shared' label removed, when the next sync runs, then the page is removed from all tenants except those explicitly named in client-specific scoping.",
    "Given a 'shared' page is unpublished, when the unpublish completes, then it disappears from every tenant's browse, search, and notification feeds.",
  ])

s("REQ-013",
  "documentation owner",
  "to mark a Confluence page as scoped to one or more named client tenants",
  "client-specific content (runbooks, integration secrets, commercial annexes) only reaches its intended audience",
  "Client-specific document visibility",
  [
    "Given a Confluence page carries one or more client-scope labels (e.g. 'client:acme'), when it is published, then the document is visible only to users whose tenant is one of the named clients.",
    "Given a user whose tenant is not in the page's client-scope list, when they access search or browse, then the page is omitted from results and a direct URL returns 404 (not 403, to avoid leaking existence).",
    "Given a documentation owner attempts to scope a page to a non-existent tenant, when the page syncs, then the publish is rejected with a clear error referencing the unknown tenant ID.",
  ])

s("REQ-014",
  "client admin",
  "to invite a new user to my client tenant by email",
  "I can onboard my own team without contacting WSD support",
  "Client-admin invites user",
  [
    "Given a client admin opens the user-management page and submits an invite for a valid email and role, when the form is submitted, then an invitation email is sent to the recipient with a single-use, time-limited acceptance link.",
    "Given an invited user clicks the acceptance link before it expires, when they set a password and enroll a second factor, then their account is created in the inviting admin's tenant with the assigned role.",
    "Given a client admin attempts to invite a user with a role outside their tenant's allowed role set, when they submit, then the action is rejected with an inline error and the attempt is audit-logged.",
  ])

s("REQ-014",
  "client admin",
  "to disable a user in my client tenant without deleting their audit history",
  "I can remove access immediately while keeping a record of what they did",
  "Client-admin disables user",
  [
    "Given a client admin selects a user in their tenant and clicks 'Disable', when they confirm, then the user's sessions are terminated within 60 seconds and subsequent logins are blocked, while the audit trail of that user's actions is preserved.",
    "Given a disabled user attempts to log in, when they submit credentials, then login is rejected with a generic message and the attempt is audit-logged.",
    "Given a client admin attempts to disable a user from a different tenant, when they submit, then the action is rejected with 403 and the attempt is audit-logged.",
  ])

s("REQ-014",
  "client admin",
  "to remove a user from my client tenant",
  "I can completely deprovision team members who leave my company",
  "Client-admin removes user",
  [
    "Given a client admin selects a user and clicks 'Remove', when they confirm with a typed confirmation, then the user record is anonymised (PII fields hashed/erased) and the user can no longer authenticate.",
    "Given a removed user's audit history exists, when they are removed, then the audit log is preserved but their displayable identity becomes 'Removed user (hash)' to satisfy data-protection while keeping accountability.",
    "Given a client admin attempts to remove the last admin in their tenant, when they submit, then the action is blocked with an error message instructing them to promote another admin first.",
  ])

s("REQ-015",
  "enterprise client",
  "to log in via my company's SAML 2.0 or OIDC identity provider",
  "I can use existing SSO and MFA infrastructure instead of a separate password",
  "Enterprise SSO",
  [
    "Given a tenant configured for SSO, when a user from that tenant lands on the login page, then they are presented with an 'SSO Login' button that initiates the configured SAML 2.0 or OIDC flow.",
    "Given a successful SSO assertion with a valid email and tenant claim, when the assertion is consumed, then a session is established with the role mapped from the assertion's group claim.",
    "Given a tenant has SSO enabled, when a user from that tenant attempts password+TOTP login, then the password login is disabled for their tenant and they are redirected to the SSO flow.",
  ])

s("REQ-016",
  "security analyst",
  "to query authentication events from an immutable audit log",
  "I can investigate suspicious access patterns and prove compliance",
  "Audit log of authentication events",
  [
    "Given any login attempt (success or failure), when it completes, then an audit entry is written containing user identifier, tenant, IP, user agent, factor used, outcome, and timestamp.",
    "Given an account lockout or rate-limit trigger, when it fires, then a discrete audit entry is written distinct from individual login attempts.",
    "Given a security analyst issues a query for authentication events filtered by user or tenant or IP within a date range, when the query runs, then results are returned within 5 seconds at p95 for the last 90 days.",
  ])

s("REQ-016",
  "security analyst",
  "to query every document view event from the audit log",
  "I can prove which client tenant saw which document version at which time",
  "Audit log of document views",
  [
    "Given an authenticated user opens a document page, when the page is served, then an audit entry is written with user identifier, tenant, document ID, version ID, and timestamp.",
    "Given a search request that returns titles, when the response is served, then an audit entry records the search query (or its hash if PII concern), the user, and the IDs of returned documents.",
    "Given the audit log retains document-view events ≥ 12 months, when a security analyst queries the log for a specific document and date range, then results are returned within the retention window.",
  ])

s("REQ-016",
  "security analyst",
  "to query administrative actions from the audit log",
  "I can prove who changed scoping, who unpublished, and who altered AI review decisions",
  "Audit log of administrative actions",
  [
    "Given any admin action (invite, role change, scope change, unpublish, manual sync re-trigger, AI review decision), when it completes, then an audit entry captures the actor, target, action type, before/after values where applicable, and timestamp.",
    "Given an AI review decision (ignore / acknowledge / block), when the reviewer submits it, then an audit entry records the reviewer identity, the page version, the finding, and the chosen action.",
    "Given an attempt to alter an existing audit entry, when the write is issued at any layer, then the write is rejected and the rejection itself is logged.",
  ])

# ---------------------------------------------------------------------------
# Theme: Client Portal
# ---------------------------------------------------------------------------

s("REQ-020",
  "client end user",
  "to browse the portal organised by product and guide category",
  "I can find the documentation for the product I am integrating with",
  "Browse by product and category",
  [
    "Given an authenticated user lands on the portal home, when the page renders, then the navigation shows a list of products derived from Confluence labels, each with its guide categories beneath it.",
    "Given the same set of source labels, when navigation is rendered for two different users at the same time, then the resulting grouping is identical (deterministic).",
    "Given a user has no entitled documents under a product (due to scoping), when navigation renders, then that product is omitted from their navigation rather than shown empty.",
  ])

s("REQ-021",
  "client end user",
  "to land on the latest published version of a document by default",
  "I never have to guess whether I am reading the current version",
  "Latest version is the default view",
  [
    "Given a user opens a document URL without an explicit version suffix, when the page renders, then the latest published version is shown with a 'Latest' badge and the publish timestamp.",
    "Given a document has been updated since the user's last visit, when they open it, then the page is rendered from the latest version with no cached older version surfaced.",
    "Given the latest version differs from the version the user was last reading, when the page renders, then a non-blocking banner offers a link to the diff against the previous version they viewed.",
  ])

s("REQ-022",
  "client end user",
  "to open any previous published version of a document I have access to",
  "I can refer back to documentation that matches an older integration",
  "View previous version",
  [
    "Given a user opens the version history panel, when they click a previous version row, then the document re-renders at that version with a clear 'Viewing older version' banner.",
    "Given a user is viewing an older version, when they click 'Back to latest', then the page re-renders at the latest version and the banner clears.",
    "Given an older version exists but the document is unpublished, when a user attempts to view it, then they receive a 'not available' message even if they have the direct URL.",
  ])

s("REQ-022",
  "client end user",
  "to diff a previous version against the latest",
  "I can see exactly what changed between integrations",
  "Diff previous vs latest",
  [
    "Given two version IDs of the same document the user is entitled to, when the user opens the diff view, then the rendered diff highlights added content in green, removed content in red, and modified blocks in yellow at the block level.",
    "Given a diff is open, when the user toggles between 'side-by-side' and 'inline' modes, then both representations show the same diff data without re-fetching.",
    "Given a diff cannot be computed (e.g. one of the versions is missing), when the view is requested, then a graceful error is shown rather than an empty page.",
  ])

s("REQ-023",
  "client end user",
  "to download the currently-viewed document version as a styled PDF",
  "I can read offline and distribute internally",
  "Per-page PDF download",
  [
    "Given a user clicks 'Download as PDF' on a document page, when the action completes, then a PDF is generated and downloaded that renders the same content as the on-screen page including images and code blocks.",
    "Given the generated PDF, when inspected, then its footer contains the document title, version number, publish timestamp, and the requesting user's tenant identity (for audit traceability).",
    "Given a PDF generation request fails (e.g. timeout), when the failure occurs, then the user sees a clear error toast and the failure is logged for operations to investigate.",
  ])

s("REQ-024",
  "client end user",
  "to search the portal full-text and find pages by phrase, term, or product",
  "I can locate what I need without browsing through hierarchies",
  "Full-text search",
  [
    "Given a user enters a query and submits, when results return, then matching documents are listed with title, snippet showing the matched terms in context, product, and last-updated timestamp, ranked by relevance.",
    "Given a query returns more than 20 results, when the user reaches the bottom, then additional results page in (or scroll-paginate) without a full page reload.",
    "Given a search query is submitted, when the search runs, then p95 response time is < 1 second for the user's entitled corpus.",
  ])

s("REQ-024",
  "client end user",
  "to never see search results that include documents I am not entitled to read",
  "the search bar cannot be used to discover the existence of out-of-scope documents",
  "Search respects scope",
  [
    "Given a user submits a query that would match a document outside their entitled scope, when results are computed, then the document is excluded from results entirely (not surfaced and then hidden).",
    "Given a user submits a query that matches no entitled documents, when results render, then the response is 'No results' rather than counts or hints of out-of-scope hits.",
    "Given an automated multi-tenant search isolation test, when it runs on every release, then it asserts a tenant A user querying for a known tenant-B-only title returns zero results.",
  ])

s("REQ-025",
  "client end user",
  "to have my last-visited timestamp per page tracked",
  "the AI change-summary feature can show me what is new since I last looked",
  "Per-user last-visited tracking",
  [
    "Given an authenticated user opens a document page, when the page renders, then the user's last-visited timestamp for that document is updated to the current time, scoped to that user.",
    "Given a user opens the portal landing page, when 'Since your last visit' is computed (REQ-051), then the computation uses the per-user last-visited timestamps to determine what is new.",
    "Given a user requests that their tracking data be deleted (data-protection right), when the request is honoured, then the per-user last-visited records for that user are erased within the configured timeframe and the deletion is audit-logged.",
  ])

# ---------------------------------------------------------------------------
# Theme: Notifications
# ---------------------------------------------------------------------------

s("REQ-030",
  "client end user",
  "to receive an email when documentation I am entitled to has changed, on a digest cadence I choose",
  "I find out about relevant changes without checking the portal manually",
  "Digest email notifications",
  [
    "Given a user has subscribed to immediate notifications, when an entitled document is published, then they receive an email within 15 minutes of publish with a deep link to the changed page.",
    "Given a user has subscribed to a daily or weekly digest, when the configured cadence elapses, then they receive a single email summarising all entitled changes in that window (or no email if there are none).",
    "Given a user is unsubscribed from notifications, when entitled documents change, then they receive no email and the unsubscribed state is honoured across all cadences.",
  ])

s("REQ-030",
  "client end user",
  "to never receive an email about a page I am not entitled to read",
  "notifications cannot leak the existence of out-of-scope content",
  "Notifications respect scope",
  [
    "Given a notification batch is being assembled, when a candidate page is being evaluated for inclusion in a user's email, then the user's tenant entitlement is re-evaluated at send time (not just at subscribe time).",
    "Given a user's entitlement to a document is revoked between subscribe time and send time, when the email is sent, then the document is excluded from that user's email.",
    "Given an automated email-scope test, when it runs on every release, then it asserts no email contains a deep link to a document the recipient cannot access.",
  ])

s("REQ-031",
  "client end user",
  "to read a release-highlights summary in the notification email before clicking through to the portal",
  "I can decide if a change needs my attention without opening the page",
  "Email contains release highlights",
  [
    "Given a notification email is rendered, when the user opens it, then for each changed page the email shows the page title, a 1–3 sentence AI-generated highlight summary (REQ-053), and a deep link to the page on the portal.",
    "Given the digest contains more than 5 changed pages, when the email is rendered, then only the top 5 are shown inline with a 'view full list' link to the portal that takes the user to a filtered changes view.",
    "Given a user clicks a deep link in the email, when they land on the portal, then the URL preserves the source = 'email-digest' parameter for analytics without exposing the user's email.",
  ])

s("REQ-032",
  "client end user",
  "to manage my own notification preferences from a profile page",
  "I do not have to contact WSD support to change my cadence or unsubscribe",
  "Manage notification preferences",
  [
    "Given a user opens the profile / preferences page, when it renders, then they see their current cadence (immediate / daily / weekly / off) and per-product subscription toggles, all editable.",
    "Given a user changes their cadence or product subscriptions and saves, when the next eligible notification would fire, then the new preferences take effect; the change is also reflected in subsequent emails' unsubscribe footer.",
    "Given a user uses the one-click 'unsubscribe' link in any email footer, when they confirm, then their cadence is set to 'off' for that product (or globally if the email was a cross-product digest) without requiring them to log in.",
  ])

# ---------------------------------------------------------------------------
# Theme: AI Document Review
# ---------------------------------------------------------------------------

s("REQ-040",
  "publishing pipeline",
  "to run the AI document-review pass and detect secrets, API keys, and credentials before publish",
  "secret material never reaches the client portal",
  "AI detects secrets and credentials",
  [
    "Given a candidate page contains a string matching a high-entropy secret pattern (e.g. AWS access key, generic API key shape), when the AI review runs, then the finding is raised with category = 'secret', severity = 'high', and the matched span is recorded.",
    "Given the AI review is uncertain (confidence below threshold) about a candidate secret, when the review completes, then the finding is raised with severity = 'medium' rather than ignored, and routed to a reviewer.",
    "Given the AI review detects no secrets, when the review completes, then a 'no-secret-findings' result is recorded for the page version and the page proceeds to the next gate.",
  ])

s("REQ-040",
  "publishing pipeline",
  "to detect internal-only URLs, Jira/internal-ticket links, and internal employee email addresses",
  "no internal references leak to clients",
  "AI detects internal URLs, Jira links, and internal emails",
  [
    "Given a candidate page contains a URL matching the configured internal-domain allow-list (e.g. ending in .internal.wsd.com), when review runs, then a finding is raised with category = 'internal-url', severity = 'high'.",
    "Given a candidate page contains a link or reference matching the Jira / internal-ticket URL patterns, when review runs, then a finding is raised with category = 'internal-ticket', severity = 'high'.",
    "Given a candidate page contains an email address whose domain matches the configured internal-email allow-list, when review runs, then a finding is raised with category = 'internal-email', severity = 'high' for staff inboxes and 'medium' for shared/team inboxes.",
  ])

s("REQ-040",
  "publishing pipeline",
  "to flag pages with structurally missing content such as empty sections or placeholder strings",
  "clients never read documentation that says 'TODO' or 'lorem ipsum'",
  "AI detects missing content",
  [
    "Given a candidate page contains placeholder strings (case-insensitive 'TODO', 'TBD', 'FIXME', 'lorem ipsum', 'xxx'), when review runs, then a finding is raised with category = 'missing-content', severity = 'medium'.",
    "Given a candidate page contains a heading immediately followed by another heading at the same or deeper level (empty section), when review runs, then a finding is raised with category = 'empty-section', severity = 'low'.",
    "Given a candidate page is shorter than a configurable minimum (default 100 words excluding boilerplate), when review runs, then a finding is raised with category = 'stub', severity = 'low'.",
  ])

s("REQ-041",
  "publishing pipeline",
  "to hard-block publishing of any page that has an unresolved high-severity AI finding",
  "screening cannot be bypassed by deadline pressure",
  "Hard block on high-severity findings",
  [
    "Given a page has at least one open finding with severity = 'high', when the publishing pipeline reaches the publish gate, then publish is rejected and the page state becomes 'blocked-on-review' with the open findings listed.",
    "Given all high-severity findings on a page are either reviewer-confirmed false positives or the page has been corrected and re-synced, when the publishing pipeline reaches the publish gate, then publish proceeds.",
    "Given a doc owner attempts to publish a page with open high-severity findings via the manual re-trigger API, when the request is processed, then it is rejected and the bypass attempt is audit-logged.",
  ])

s("REQ-042",
  "publishing reviewer",
  "to see AI findings displayed in context with the matched span highlighted",
  "I can evaluate each finding without having to re-read the whole page",
  "Reviewer sees findings in context",
  [
    "Given a reviewer opens a page that has AI findings, when the review panel renders, then the page content is shown with each finding's matched span highlighted, colour-coded by severity.",
    "Given a reviewer clicks a finding in the side list, when the click is registered, then the page scrolls so the matched span is centred and focused.",
    "Given the matched span has been removed in a newer Confluence revision after the finding was raised, when the reviewer opens the panel, then the finding is marked 'stale' rather than shown against missing content.",
  ])

s("REQ-042",
  "publishing reviewer",
  "to triage each AI finding by choosing ignore / acknowledge / block, with my decision audit-logged",
  "review decisions are traceable and defensible",
  "Reviewer triages each finding",
  [
    "Given a finding is open, when a reviewer selects 'ignore', then the finding is marked closed-as-false-positive, the reviewer identity and timestamp are audit-logged, and (if it was the last high-severity blocker) the page becomes publishable.",
    "Given a finding is open, when a reviewer selects 'acknowledge' on a non-high-severity finding, then the finding is marked closed-as-acknowledged and the page becomes publishable.",
    "Given a finding is open, when a reviewer selects 'block', then the page state becomes 'blocked-pending-source-fix' until the source page is corrected and re-synced (re-syncing creates a new review pass).",
  ])

# ---------------------------------------------------------------------------
# Theme: AI Release Notes & Change Summary
# ---------------------------------------------------------------------------

s("REQ-050",
  "publishing pipeline",
  "to generate AI release notes covering What's New, Breaking Changes, and Recommended Actions when a page changes",
  "release-note authoring stops being a manual cost on every release",
  "Generate AI release notes",
  [
    "Given a page is being published as a new version, when release-note generation runs, then it produces three sections — What's New, Breaking Changes, Recommended Actions — based on the diff against the prior published version.",
    "Given a page has no prior published version, when release-note generation runs, then What's New describes the initial publication and the other two sections render 'None for this release'.",
    "Given release-note generation fails (AI provider error), when the failure occurs, then the page enters 'release-notes-pending' state, an alert is raised, and the publish does not proceed until release notes exist or are explicitly waived.",
  ])

s("REQ-050",
  "publishing reviewer",
  "to approve AI-generated release notes before clients see them",
  "no AI-authored copy reaches clients without a human gate",
  "Reviewer approves release notes",
  [
    "Given release notes have been generated, when the reviewer opens the review panel, then they see the three sections side-by-side with the diff that produced them.",
    "Given a reviewer clicks 'Approve', when the action is recorded, then the release notes become the published artefact for that version and the approval is audit-logged.",
    "Given a reviewer takes no action longer than the configured SLA (default 24 hours for high-severity diffs, 72 hours otherwise), when the SLA elapses, then a reminder notification is sent and the timeout is surfaced on the dashboard.",
  ])

s("REQ-051",
  "client end user",
  "to see a per-client 'Since your last visit' summary on the portal landing page",
  "I orient quickly to what changed without scanning every product",
  "Per-client since-last-visit summary",
  [
    "Given an authenticated user opens the portal landing page, when the page renders, then a 'Since your last visit' block shows an AI-generated paragraph summarising the entitled pages that have changed since their last view per page.",
    "Given a user has no changes since their last visit, when the landing page renders, then the block shows 'You are up to date' rather than fabricating change content.",
    "Given the underlying change set has not changed since the last render, when the user reloads the landing page, then the summary is served from cache rather than regenerated.",
  ])

s("REQ-052",
  "publishing reviewer",
  "to regenerate, edit inline, or discard any AI-generated release-notes block",
  "I can quickly correct or override AI output without leaving the review UI",
  "Reviewer can regenerate, edit, or discard release notes",
  [
    "Given a reviewer clicks 'Regenerate' on a release-notes block, when the action runs, then a new draft replaces the current one (the previous draft remains accessible in the revision side-panel) and the regeneration is audit-logged.",
    "Given a reviewer edits a release-notes block inline and clicks save, when the save succeeds, then their edits are persisted and any subsequent regeneration starts from the edited text unless the reviewer explicitly discards their edits.",
    "Given a reviewer clicks 'Discard', when they confirm, then the release-notes block for this version is cleared and the publish gate now requires either an empty-but-approved or a regenerated release-notes block.",
  ])

# ---------------------------------------------------------------------------
# Theme: AI Client Notifications
# ---------------------------------------------------------------------------

s("REQ-053",
  "notification pipeline",
  "to insert AI-generated per-client concise summaries into each outgoing email",
  "notification emails are short and tailored, not noisy",
  "AI client-notification summaries",
  [
    "Given a notification email is being assembled for a user, when each changed page is processed, then a concise AI-generated summary (≤ 30 words) is generated per page based on the changes the user is entitled to see.",
    "Given two users in the same tenant subscribe to the same digest, when their emails are assembled, then each user receives a summary generated against their per-user entitled change set (they may differ if entitlements differ).",
    "Given AI summary generation fails for a page, when the failure occurs, then the email falls back to the page title plus 'View changes on portal' without sending a broken email.",
  ])

s("REQ-053",
  "publishing reviewer",
  "to approve an AI notification summary before it sends when the underlying change is flagged as breaking",
  "breaking-change notifications cannot be auto-sent without human sign-off",
  "Reviewer approves breaking-change notification summary",
  [
    "Given a release-notes pass has flagged at least one entry under 'Breaking Changes' for a page, when the notification email is being assembled, then the email sits in 'pending-review' state and is not sent until a reviewer approves.",
    "Given a reviewer approves a pending breaking-change notification, when they click 'Approve & Send', then the email is dispatched to the digest recipients and the approval is audit-logged with reviewer identity and timestamp.",
    "Given a reviewer rejects a pending breaking-change notification, when they click 'Reject', then the email is not sent for that change and the rejection plus reason are audit-logged.",
  ])

# ---------------------------------------------------------------------------
# Theme: AI Documentation Quality Check
# ---------------------------------------------------------------------------

s("REQ-054",
  "documentation owner",
  "to see AI-generated quality scores (completeness, readability, missing examples, missing API responses) when I publish",
  "I can catch documentation-quality regressions before clients do",
  "AI quality scoring on publish",
  [
    "Given a candidate page is about to enter the publish gate, when the quality scoring step runs, then four scores in [0..1] are produced for Completeness, Readability, Missing Examples, Missing API Responses and persisted with the page version.",
    "Given a score is below the warning threshold for any dimension, when the doc owner views the publish summary, then a warning badge is shown next to the score with a short AI-generated suggestion.",
    "Given quality scoring fails (provider error), when the failure occurs, then publishing is not blocked but a 'quality-score-unavailable' marker is recorded with the version.",
  ])

s("REQ-054",
  "documentation owner",
  "to override a low quality-score warning and publish anyway, with my decision recorded",
  "quality scoring nudges but does not gate, and I keep the final say",
  "Quality warning is overrideable with audit",
  [
    "Given a publish summary shows a low quality-score warning, when the doc owner clicks 'Publish anyway' and supplies an override reason, then publish proceeds and the override (reason + identity) is audit-logged with the version.",
    "Given a publish summary shows a low quality-score warning, when the doc owner cancels and edits the source page in Confluence, then re-syncing the page re-runs scoring and shows the new scores in a fresh publish summary.",
    "Given the published version was published under override, when a future reader views the version metadata, then the override marker is visible to internal staff (not to clients) so retro reviews can find quality-bypass cases.",
  ])

s("REQ-055",
  "documentation owner",
  "to see the trend of quality scores over time per page",
  "I can spot pages that are getting worse and prioritise rewrites",
  "Quality trend over time",
  [
    "Given a page has at least three published versions, when the doc owner opens the page's quality view, then a chart is shown for each of the four dimensions over the publish history.",
    "Given a page has fewer than three published versions, when the quality view is opened, then the trend chart shows current values and a 'not enough history' notice rather than empty axes.",
    "Given quality scoring was unavailable for a particular version, when the trend is rendered, then that version is shown as a gap in the line rather than as zero.",
  ])

# ---------------------------------------------------------------------------
# Theme: Non-Functional
# ---------------------------------------------------------------------------

s("REQ-100",
  "platform operator",
  "to have portal page render p95 under 1.5 s under expected client load",
  "the portal feels responsive at launch and on a typical day",
  "Portal render p95 SLA",
  [
    "Given the synthetic-load test runs the standard 500-user reading workload, when results are collected, then portal page render p95 measured server-side from request to last byte of HTML is < 1.5 s.",
    "Given p95 portal render exceeds 1.5 s over a rolling 15-minute window in production, when the threshold is breached, then a paging alert is fired and the deployment is auto-rolled-back if the breach started after the most recent deploy.",
    "Given the read tier is healthy, when an authenticated user opens any document page, then the first contentful paint occurs within 1 s on a representative WSD client environment baseline.",
  ])

s("REQ-101",
  "platform operator",
  "to have sync latency observability covering Confluence approval through portal visibility, including AI review",
  "the 5-minute SLA is enforced and AI review latency is visible",
  "End-to-end sync latency observability",
  [
    "Given a publish run completes successfully, when metrics are emitted, then the total end-to-end latency from approval to portal visibility is recorded, plus a sub-breakdown for AI review duration.",
    "Given p95 end-to-end latency exceeds 5 minutes OR p95 total (including AI review) exceeds 15 minutes over a rolling 15-minute window, when the threshold is breached, then a paging alert is raised.",
    "Given an operator opens the sync dashboard, when they filter by a single page, then they see per-stage timings for the most recent N publishes (configurable, default 50).",
  ])

s("REQ-102",
  "security engineer",
  "to enforce TLS 1.2+ for all client-facing traffic",
  "no plaintext data ever crosses the public network",
  "TLS enforced",
  [
    "Given a client connection is established, when the TLS handshake completes, then the negotiated protocol is TLS 1.2 or TLS 1.3 with a permitted cipher suite (no exportable, no RC4, no SHA-1).",
    "Given a client attempts a connection with TLS 1.1 or lower, when the handshake begins, then the server rejects the connection cleanly.",
    "Given the portal's TLS configuration is in production, when an external scan runs (e.g. Mozilla TLS observatory or equivalent), then the configuration achieves at minimum the 'intermediate' grade with no known-vulnerable settings.",
  ])

s("REQ-102",
  "security engineer",
  "to encrypt session tokens, audit logs, AI-pipeline payloads, and other sensitive at-rest data",
  "even with disk or backup access, an attacker cannot read sensitive material in cleartext",
  "Data encrypted at rest",
  [
    "Given any data store containing session tokens, audit log entries, or AI-pipeline payloads, when data is written to disk, then it is encrypted using platform-standard KMS-managed keys.",
    "Given a KMS key rotation event, when the rotation completes, then existing data continues to be readable under the new key alias and the rotation is audit-logged.",
    "Given a verifiable security check runs (e.g. automated infra audit), when it inspects each data store, then no store is found in plaintext-at-rest configuration.",
  ])

s("REQ-103",
  "platform engineer",
  "to enforce per-client data isolation at the data-access layer, validated by tests",
  "no UI bug or API guess can produce a cross-tenant data leak",
  "Data-layer tenant isolation",
  [
    "Given every read or write query against tenant-scoped tables, when issued by application code, then the query carries the active tenant ID and the data layer rejects queries without it or with a tenant ID inconsistent with the authenticated session.",
    "Given the automated isolation test suite, when it runs as part of CI on every release, then for every read endpoint it asserts that requests authenticated as tenant A cannot retrieve data created as tenant B.",
    "Given a developer attempts to add a new read endpoint without tenant scoping, when CI runs, then a lint/static-analysis check fails the build with a clear message pointing to the unscoped query.",
  ])

s("REQ-104",
  "client end user with assistive technology",
  "to navigate the entire portal by keyboard alone, with logical focus order and visible focus rings",
  "I can use the portal without a pointing device",
  "Keyboard navigation",
  [
    "Given an authenticated user is on any portal page, when they use Tab and Shift+Tab to move focus, then every interactive control is reachable, the focus order matches the visual order, and every focused element has a visible focus indicator meeting WCAG AA contrast.",
    "Given a modal or dialog is opened (e.g. PDF generation confirmation), when it is open, then focus is trapped inside it and Escape closes it returning focus to the opener.",
    "Given an automated a11y test (e.g. axe-core) runs on every release across login, browse, read, version history, search, and PDF flows, when results are collected, then zero serious or critical violations are reported.",
  ])

s("REQ-104",
  "client end user with assistive technology",
  "to use a screen reader to read documents with correct semantic structure and image alt-text",
  "I can consume documentation non-visually",
  "Screen reader and contrast",
  [
    "Given a screen reader reads a document page, when it traverses the content, then headings are exposed with their semantic levels, lists as lists, tables with row/column headers, and images announce their alt-text.",
    "Given a colour palette change is proposed, when a contrast check runs against text/background pairs in the design tokens, then all combinations meet WCAG AA contrast ratios.",
    "Given a non-text status indicator (e.g. coloured badge), when a screen reader reaches it, then a text-equivalent label is announced (e.g. 'Status: blocked-on-review').",
  ])

s("REQ-105",
  "publishing pipeline",
  "to fail closed when the AI provider is unavailable rather than skipping screening",
  "AI-provider outages cannot become a vector for unscreened content reaching clients",
  "AI review fails closed",
  [
    "Given the AI document-review provider is unavailable (timeout, 5xx, or auth failure), when a page reaches the review step, then the page is queued in 'review-pending-provider' state and an alert is raised; the page is NOT published.",
    "Given the AI provider becomes available again, when the queued page is retried, then review proceeds and (assuming clean findings) publish completes.",
    "Given an operator attempts to bypass the review step via a configuration flag or API, when the attempt is made in production, then the action is blocked unless a documented two-person break-glass procedure is followed and recorded.",
  ])

s("REQ-106",
  "platform engineer",
  "to scale the portal read tier horizontally so capacity grows with client headcount",
  "onboarding a large client does not require an architectural rewrite",
  "Horizontal scaling of read tier",
  [
    "Given the portal read tier is deployed behind a load balancer, when a new read-tier instance is added, then it serves traffic within 60 seconds of becoming healthy without requiring a deploy of other tiers.",
    "Given a synthetic load doubles, when read-tier autoscaling fires, then additional instances come online and p95 render latency returns under 1.5 s within 5 minutes.",
    "Given any read-tier instance is terminated mid-request, when the request retries via the load balancer, then it succeeds on a different instance without surfacing an error to the user.",
  ])

s("REQ-107",
  "security analyst",
  "to know that audit logs cannot be tampered with and are retained at least 12 months",
  "audit evidence is admissible and complete",
  "Audit log tamper-evident retention",
  [
    "Given audit log entries (auth, view, admin, AI review) are written, when stored, then they live in an append-only or cryptographically signed log such that any subsequent edit or deletion is detectable at scan time.",
    "Given an integrity scan runs on a schedule (at minimum daily), when it completes, then it verifies the audit chain has not been altered and emits a signed report; any verification failure pages security.",
    "Given an audit log entry is older than 12 months and within retention policy, when retrieved, then it returns intact; entries beyond retention policy are archived to cold storage with the same tamper-evident properties.",
  ])


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

prd_path = REPO / "docs/specs/client-docs-hub/prd/PRD-001.json"
prd = json.loads(prd_path.read_text())
all_req_ids = {r["id"] for r in prd["requirements"]}
must_reqs = {r["id"] for r in prd["requirements"] if r["priority"] == "must"}
covered = {s["reqId"] for s in STORIES}
missing_must = must_reqs - covered
if missing_must:
    raise SystemExit(f"Coverage gate FAIL: must REQs uncovered: {sorted(missing_must)}")
bad_req = covered - all_req_ids
if bad_req:
    raise SystemExit(f"Stories reference unknown REQs: {sorted(bad_req)}")
for st in STORIES:
    if not re.match(r"^US-\d{3,}$", st["id"]): raise SystemExit(f"bad US id {st['id']}")
    if not re.match(r"^REQ-\d{3,}$", st["reqId"]): raise SystemExit(f"bad REQ ref {st['reqId']}")
    if len(st["acceptanceCriteria"]) < 2: raise SystemExit(f"{st['id']} has < 2 ACs")
    for ac in st["acceptanceCriteria"]:
        if not re.match(r"^AC-\d{3,}$", ac["id"]): raise SystemExit(f"bad AC id {ac['id']}")


# ---------------------------------------------------------------------------
# Emit JSON
# ---------------------------------------------------------------------------

now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
doc = {
    "prdId": PRD_ID,
    "version": VERSION,
    "status": "draft",
    "stories": STORIES,
    "createdAt": now,
    "updatedAt": now,
}
json_path = REPO / "docs/specs/client-docs-hub/user-stories/PRD-001-user-stories.json"
json_path.parent.mkdir(parents=True, exist_ok=True)
json_path.write_text(json.dumps(doc, indent=2) + "\n")


# ---------------------------------------------------------------------------
# Emit markdown view (themes follow PRD order)
# ---------------------------------------------------------------------------

req_to_domain = {r["id"]: r["domain"] for r in prd["requirements"]}
# Theme order matching PRD reading order
theme_order = [
    "Confluence Sync & Publishing",
    "Authentication & Access Control",
    "Client Portal",
    "Notifications",
    "AI Document Review",
    "AI Release Notes & Change Summary",
    "AI Client Notifications",
    "AI Documentation Quality Check",
    "Performance",
    "Data Protection",
    "Accessibility",
    "Scalability",
    "Audit & Compliance",
]

def theme_of(story):
    d = req_to_domain.get(story["reqId"], "Other")
    return d

by_theme: dict[str, list] = {t: [] for t in theme_order}
for st in STORIES:
    by_theme.setdefault(theme_of(st), []).append(st)

md = []
md.append("# Client Documentation Hub — User Stories\n")
md.append(f"> Generated from `docs/specs/client-docs-hub/prd/PRD-001.json` v{prd['version']}. Canonical machine-readable copy lives at `docs/specs/client-docs-hub/user-stories/PRD-001-user-stories.json`. {len(STORIES)} stories, {sum(len(s['acceptanceCriteria']) for s in STORIES)} acceptance criteria. AC format: Given / When / Then.\n")
md.append("Coverage gate: every `must` REQ in the PRD has ≥ 1 story.\n")
for theme in theme_order:
    items = by_theme.get(theme, [])
    if not items:
        continue
    md.append(f"\n## Theme: {theme}\n")
    for st in items:
        md.append(f"\n### {st['id']} — {st['title']}\n")
        md.append(f"As a *{st['asA']}*, I want *{st['iWant']}*, so that *{st['soThat']}*.\n")
        md.append(f"\n**Covers:** {st['reqId']}\n")
        md.append("\n**Acceptance criteria:**\n")
        for ac in st["acceptanceCriteria"]:
            md.append(f"- **{ac['id']}** — {ac['description']}\n")

md_path = REPO / "docs/specs/client-docs-hub/user-stories/USER-STORIES.md"
md_path.parent.mkdir(parents=True, exist_ok=True)
md_path.write_text("".join(md))


# ---------------------------------------------------------------------------
# Update manifest
# ---------------------------------------------------------------------------

manifest_path = REPO / "docs/specs/client-docs-hub/manifest.json"
manifest = json.loads(manifest_path.read_text())
prd_entry = manifest["prd"]
new_story_entry = {
    "id": "STD-001",
    "path": "user-stories/PRD-001-user-stories.json",
    "markdownPath": "user-stories/USER-STORIES.md",
}
existing_ids = {s["id"] for s in prd_entry.get("stories", [])}
if new_story_entry["id"] not in existing_ids:
    prd_entry.setdefault("stories", []).append(new_story_entry)
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")


# ---------------------------------------------------------------------------
# Print summary
# ---------------------------------------------------------------------------

from collections import Counter
by_req = Counter(st["reqId"] for st in STORIES)
ac_count = sum(len(st["acceptanceCriteria"]) for st in STORIES)
print(f"Stories: {len(STORIES)}")
print(f"ACs:     {ac_count}")
print(f"REQs covered: {len(set(by_req))} / {len(all_req_ids)}")
print(f"Must REQs covered: {len(must_reqs & set(by_req))} / {len(must_reqs)}")
print(f"Stories per REQ (range): {min(by_req.values())}..{max(by_req.values())}")
print(f"Wrote: {json_path.relative_to(REPO)}")
print(f"Wrote: {md_path.relative_to(REPO)}")
print(f"Updated: {manifest_path.relative_to(REPO)}")
