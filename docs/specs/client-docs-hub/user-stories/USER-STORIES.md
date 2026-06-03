# Client Documentation Hub — User Stories
> Generated from `docs/specs/client-docs-hub/prd/PRD-001.json` v1.0.0. Canonical machine-readable copy lives at `docs/specs/client-docs-hub/user-stories/PRD-001-user-stories.json`. 64 stories, 192 acceptance criteria. AC format: Given / When / Then.
Coverage gate: every `must` REQ in the PRD has ≥ 1 story.

## Theme: Confluence Sync & Publishing

### US-001 — Manage sync allow-list
As a *documentation administrator*, I want *to manage the allow-list of Confluence labels and source spaces that are eligible to sync*, so that *only intentionally-tagged pages can ever be published to the client portal*.

**Covers:** REQ-001

**Acceptance criteria:**
- **AC-001** — Given an admin opens the sync configuration page, when they add a label to the allow-list and save, then the label appears in the active list and the change is audit-logged with the admin's identity and timestamp.
- **AC-002** — Given an admin removes a label from the allow-list, when the next sync cycle runs, then pages whose only allow-list match was that label are unpublished from the portal and the unpublish is audit-logged.
- **AC-003** — Given an unauthenticated user or a user without the admin role, when they request the sync configuration page, then they receive a 403 and the attempt is audit-logged.

### US-002 — Sync engine respects allow-list
As a *sync engine*, I want *to evaluate each candidate Confluence page against the active allow-list before considering it for publish*, so that *pages outside the configured tag/space scope never enter the publishing pipeline*.

**Covers:** REQ-001

**Acceptance criteria:**
- **AC-004** — Given a Confluence page that carries no allow-listed label and lives outside any allow-listed space, when the sync cycle runs, then the page is skipped and a debug-level log records the skip with the page ID.
- **AC-005** — Given a Confluence page that carries at least one allow-listed label, when the sync cycle runs, then the page proceeds to the approval-state check (REQ-002).
- **AC-006** — Given the allow-list is empty, when the sync cycle runs, then zero pages are published and an admin-visible warning is surfaced.

### US-003 — Approval-state gating
As a *publishing pipeline*, I want *to publish only Confluence pages whose configured approval signal is present*, so that *drafts and in-review pages never reach clients*.

**Covers:** REQ-002

**Acceptance criteria:**
- **AC-007** — Given a Confluence page with the configured approval signal absent (e.g. draft state, missing approval label), when the sync evaluates it, then publishing is blocked and the page does not appear on the portal.
- **AC-008** — Given a Confluence page with the configured approval signal present, when the sync evaluates it, then it proceeds to the AI document-review stage (REQ-040).
- **AC-009** — Given an admin reconfigures the approval signal, when the change is saved, then the active signal is logged and the next sync cycle applies the new rule.

### US-004 — Loss of approval triggers unpublish
As a *publishing pipeline*, I want *to unpublish a page that loses its approval state after publish*, so that *the portal never serves content that has reverted to draft*.

**Covers:** REQ-002

**Acceptance criteria:**
- **AC-010** — Given a previously published page, when its approval signal is removed in Confluence, then on the next sync cycle the page is unpublished from the portal within 5 minutes (p95).
- **AC-011** — Given a page is unpublished due to loss of approval, when a client navigates to its URL, then they receive a clear 'not available' message rather than a stale cached copy.
- **AC-012** — Given a page is unpublished due to loss of approval, when the unpublish completes, then the version history of that page is preserved and the unpublish event is audit-logged with cause = 'approval-state-loss'.

### US-005 — Webhook-driven sync within SLA
As a *sync engine*, I want *to receive Confluence page-change webhooks and publish updates within the SLA*, so that *approved changes reach the portal in near real-time without operator action*.

**Covers:** REQ-003

**Acceptance criteria:**
- **AC-013** — Given a webhook event arrives for an approved, allow-listed page, when the sync pipeline processes it, then the new version is visible on the portal within 5 minutes at p95 measured from webhook receipt to portal cache hit.
- **AC-014** — Given the webhook delivery is duplicated (Confluence retries), when the pipeline processes the duplicate, then no duplicate version is created and the duplicate is recorded as deduped in logs.
- **AC-015** — Given a webhook payload that fails schema validation, when received, then the event is rejected with a 400 and an alert is raised, with no partial publish.

### US-006 — Polling sync fallback
As a *sync engine*, I want *to fall back to a polling sync on a configurable interval when webhooks are unavailable*, so that *the portal stays in sync even if Confluence cannot deliver webhooks*.

**Covers:** REQ-003

**Acceptance criteria:**
- **AC-016** — Given webhooks have been disabled or have failed for longer than a configurable threshold, when the polling interval elapses, then the engine fetches the recently-changed page list from Confluence and processes eligible pages.
- **AC-017** — Given polling is active and a page has been updated since the last poll, when the engine processes it, then it follows the same allow-list → approval → AI-review path as webhook-driven sync.
- **AC-018** — Given webhooks recover, when the first webhook arrives after recovery, then polling continues for one additional cycle to backfill any missed events, then quiesces.

### US-007 — Sync latency observability
As a *platform engineer*, I want *to observe sync latency as a first-class metric with alerting*, so that *the SLA is enforced operationally and regressions are caught before clients notice*.

**Covers:** REQ-003

**Acceptance criteria:**
- **AC-019** — Given the sync pipeline is running, when a page completes publishing, then the end-to-end latency from approval to portal visibility is emitted as a histogram metric tagged by page and pipeline stage.
- **AC-020** — Given p95 sync latency exceeds 5 minutes over a rolling 15-minute window, when the threshold is breached, then a paging alert is fired to the on-call channel.
- **AC-021** — Given a platform engineer opens the sync dashboard, when they select a time range, then they see per-stage latency breakdowns (webhook receipt → allow-list → approval → AI review → publish).

### US-008 — Version history retention
As a *publishing pipeline*, I want *to persist each successful publish as an immutable version with at least the last 20 versions retained per page*, so that *clients and auditors can refer back to any recent published state*.

**Covers:** REQ-004

**Acceptance criteria:**
- **AC-022** — Given a page is successfully published, when the publish commits, then a new immutable version record is written containing the rendered content, publish timestamp, source Confluence version ID, and publisher identity.
- **AC-023** — Given a page has 21 published versions, when the 22nd is published, then the oldest version is dropped from active storage but its metadata (timestamp, source version, publisher) is retained in the audit log.
- **AC-024** — Given an attempt to modify an existing version record, when the write is issued, then the data layer rejects it and the attempt is audit-logged as a tamper attempt.

### US-009 — Version metadata visible to clients
As a *portal user*, I want *to see metadata for each version of a page (when published, by whom, source Confluence revision)*, so that *I can decide which version to read or cite*.

**Covers:** REQ-004

**Acceptance criteria:**
- **AC-025** — Given a portal user opens the version history view of a page, when the page renders, then each listed version shows publish timestamp, version number, and the source Confluence revision number.
- **AC-026** — Given a portal user hovers / focuses a version row, when the row is active, then a tooltip / detail panel shows the publisher's name in a non-PII-leaking form (display name only).
- **AC-027** — Given a version row is rendered, when no source Confluence revision is available (legacy import), then 'Source revision: unavailable' is shown rather than an empty field.

### US-010 — Render fidelity for rich content
As a *publishing pipeline*, I want *to preserve Confluence page structure on publish for headings, lists, tables, code blocks, and inline images*, so that *the portal reads as faithfully as the Confluence source*.

**Covers:** REQ-005

**Acceptance criteria:**
- **AC-028** — Given a Confluence page containing headings (h1–h4), lists, tables, code blocks (with language hint), and inline images, when the page is published, then the rendered portal page preserves the same structural elements with the same semantic markup.
- **AC-029** — Given a code block in Confluence has a language hint, when the page is rendered on the portal, then the corresponding code block carries the matching language class for syntax highlighting.
- **AC-030** — Given an inline image in Confluence, when the page is rendered on the portal, then the image is served from a per-page asset path with the same alt-text as the source.

### US-011 — Cross-link rewriting
As a *publishing pipeline*, I want *to rewrite cross-page links so links to published pages resolve and links to non-published pages do not leak*, so that *clients never click into broken or unauthorized destinations*.

**Covers:** REQ-005

**Acceptance criteria:**
- **AC-031** — Given a Confluence cross-link points to another page that is also published in the portal, when the source page renders, then the link target is rewritten to the portal URL of the destination version.
- **AC-032** — Given a Confluence cross-link points to a page that is not published (not allow-listed, not approved, or unpublished), when the source page renders, then the link is rendered as inert text with a 'not available' tooltip rather than a live link.
- **AC-033** — Given an external link (e.g. https://example.com) in Confluence, when the page is published, then the link is preserved verbatim and opens in a new tab with rel='noopener'.

### US-012 — Manual sync re-trigger
As a *documentation owner*, I want *to manually re-trigger sync of an individual page or tag set from the admin UI*, so that *I can recover from a missed automatic sync without filing a platform ticket*.

**Covers:** REQ-006

**Acceptance criteria:**
- **AC-034** — Given a doc owner opens the admin UI and selects a page, when they click 'Re-sync this page', then the page is enqueued for the sync pipeline with priority and the action is audit-logged with their identity.
- **AC-035** — Given a doc owner selects a tag set and clicks 'Re-sync tag', when the action is submitted, then every approved, allow-listed page carrying that tag is re-evaluated by the pipeline.
- **AC-036** — Given a re-sync action is in progress, when the doc owner returns to the admin UI, then they see the status (queued / running / complete / failed) for each enqueued page.

### US-013 — Unpublish with audit reason
As a *documentation owner*, I want *to unpublish a page from the portal without deleting it from Confluence, supplying a reason*, so that *I can quickly remove a page that was published in error and keep an auditable record*.

**Covers:** REQ-007

**Acceptance criteria:**
- **AC-037** — Given a doc owner selects a published page and clicks 'Unpublish', when they supply a non-empty reason and confirm, then the page is removed from portal browse and search within 60 seconds and the action is audit-logged with the supplied reason.
- **AC-038** — Given a page has been unpublished, when the same page later receives an approved update in Confluence, then a re-publish requires an explicit re-publish action (it does not auto-recover) and the link between the unpublish and the re-publish is recorded in the audit trail.
- **AC-039** — Given a doc owner attempts to unpublish without supplying a reason, when they submit, then the action is rejected with an inline error and no state changes.

## Theme: Authentication & Access Control

### US-014 — Unauthenticated access redirects to login
As a *portal visitor*, I want *to be redirected to a login screen whenever I try to access any portal page unauthenticated*, so that *no portal content is reachable without a login*.

**Covers:** REQ-010

**Acceptance criteria:**
- **AC-040** — Given an unauthenticated visitor requests any non-login URL on docs.wsd.com, when the request is received, then the server responds with a 302 to the login page carrying a signed redirect-back parameter for the original destination.
- **AC-041** — Given an unauthenticated visitor requests a portal API endpoint, when the request is received, then the server responds with 401 and a JSON error body, not HTML.
- **AC-042** — Given a visitor completes login from a deep-link redirect, when authentication succeeds, then they land on the originally-requested URL rather than the portal home.

### US-015 — Password plus second-factor login
As a *portal user*, I want *to log in with my password plus a second factor (TOTP or email magic link)*, so that *my account is protected against password-only compromise*.

**Covers:** REQ-011

**Acceptance criteria:**
- **AC-043** — Given a user with a valid password and an enrolled TOTP authenticator, when they enter both correctly, then a session is established and they are routed to their entitled home page.
- **AC-044** — Given a user submits a valid password but no second factor is configured for their account, when login proceeds, then the system offers a one-time email magic-link as the second factor and blocks session establishment until it is consumed.
- **AC-045** — Given a user submits a valid password but an incorrect or expired TOTP code, when they submit, then the login is rejected with a generic error message (no information about which factor failed) and the attempt is rate-limited.

### US-016 — Session lifecycle
As a *portal user*, I want *to have my session managed with HTTP-only Secure cookies, configurable timeout, and idempotent logout*, so that *stolen cookies and stale tabs are not a path to account compromise*.

**Covers:** REQ-011

**Acceptance criteria:**
- **AC-046** — Given a successful login, when the session cookie is set, then it has the Secure, HttpOnly, and SameSite=Strict attributes and is bound to the docs.wsd.com domain.
- **AC-047** — Given a session has been idle longer than the configured timeout, when the user issues any request, then the session is invalidated server-side and they are redirected to login.
- **AC-048** — Given a user clicks 'Log out', when the action is processed, then the session is invalidated server-side and the cookie is cleared client-side; repeated logout requests have no additional effect (idempotent).

### US-017 — Rate limiting and lockout
As a *platform operator*, I want *to have password and second-factor brute-force attempts rate-limited and locked out*, so that *credential stuffing campaigns are slowed and detectable*.

**Covers:** REQ-011

**Acceptance criteria:**
- **AC-049** — Given more than 5 failed login attempts for a single user identifier within 10 minutes, when the next attempt arrives, then the attempt is rejected with a generic error and the user receives an email notification of the lockout.
- **AC-050** — Given a locked account, when the lockout window (configurable, default 15 minutes) elapses, then the lockout is lifted and the user may try again.
- **AC-051** — Given a sustained pattern of failed logins across many user identifiers from a single IP, when the IP threshold is exceeded, then requests from that IP are 429-throttled for a configurable cooldown and the event is alerted to security.

### US-018 — Data-layer tenant scoping
As a *portal user*, I want *to only see documents scoped to my client tenant, even under direct URL access*, so that *no UI manipulation or API guessing can reveal another client's documents*.

**Covers:** REQ-012

**Acceptance criteria:**
- **AC-052** — Given an authenticated user whose tenant is 'acme', when they request a document URL whose scope is 'beta' (another tenant), then the response is 404 and the lookup is audit-logged as a cross-tenant attempt.
- **AC-053** — Given an automated multi-tenant isolation test suite, when it runs on every release, then it asserts that every read endpoint enforces tenant scoping at the data-access layer (no relying on UI filtering).
- **AC-054** — Given a user views a 'shared' document, when their tenant is resolved, then the access is permitted regardless of tenant; shared scope is the only public scope across tenants.

### US-019 — Shared document visibility
As a *documentation owner*, I want *to mark a Confluence page as 'shared' so it appears to every authenticated client tenant*, so that *common product documentation is available to all clients without duplication*.

**Covers:** REQ-013

**Acceptance criteria:**
- **AC-055** — Given a Confluence page carries the configured 'shared' label, when it is published, then the document is visible to every authenticated user across all client tenants.
- **AC-056** — Given a previously-shared page has its 'shared' label removed, when the next sync runs, then the page is removed from all tenants except those explicitly named in client-specific scoping.
- **AC-057** — Given a 'shared' page is unpublished, when the unpublish completes, then it disappears from every tenant's browse, search, and notification feeds.

### US-020 — Client-specific document visibility
As a *documentation owner*, I want *to mark a Confluence page as scoped to one or more named client tenants*, so that *client-specific content (runbooks, integration secrets, commercial annexes) only reaches its intended audience*.

**Covers:** REQ-013

**Acceptance criteria:**
- **AC-058** — Given a Confluence page carries one or more client-scope labels (e.g. 'client:acme'), when it is published, then the document is visible only to users whose tenant is one of the named clients.
- **AC-059** — Given a user whose tenant is not in the page's client-scope list, when they access search or browse, then the page is omitted from results and a direct URL returns 404 (not 403, to avoid leaking existence).
- **AC-060** — Given a documentation owner attempts to scope a page to a non-existent tenant, when the page syncs, then the publish is rejected with a clear error referencing the unknown tenant ID.

### US-021 — Client-admin invites user
As a *client admin*, I want *to invite a new user to my client tenant by email*, so that *I can onboard my own team without contacting WSD support*.

**Covers:** REQ-014

**Acceptance criteria:**
- **AC-061** — Given a client admin opens the user-management page and submits an invite for a valid email and role, when the form is submitted, then an invitation email is sent to the recipient with a single-use, time-limited acceptance link.
- **AC-062** — Given an invited user clicks the acceptance link before it expires, when they set a password and enroll a second factor, then their account is created in the inviting admin's tenant with the assigned role.
- **AC-063** — Given a client admin attempts to invite a user with a role outside their tenant's allowed role set, when they submit, then the action is rejected with an inline error and the attempt is audit-logged.

### US-022 — Client-admin disables user
As a *client admin*, I want *to disable a user in my client tenant without deleting their audit history*, so that *I can remove access immediately while keeping a record of what they did*.

**Covers:** REQ-014

**Acceptance criteria:**
- **AC-064** — Given a client admin selects a user in their tenant and clicks 'Disable', when they confirm, then the user's sessions are terminated within 60 seconds and subsequent logins are blocked, while the audit trail of that user's actions is preserved.
- **AC-065** — Given a disabled user attempts to log in, when they submit credentials, then login is rejected with a generic message and the attempt is audit-logged.
- **AC-066** — Given a client admin attempts to disable a user from a different tenant, when they submit, then the action is rejected with 403 and the attempt is audit-logged.

### US-023 — Client-admin removes user
As a *client admin*, I want *to remove a user from my client tenant*, so that *I can completely deprovision team members who leave my company*.

**Covers:** REQ-014

**Acceptance criteria:**
- **AC-067** — Given a client admin selects a user and clicks 'Remove', when they confirm with a typed confirmation, then the user record is anonymised (PII fields hashed/erased) and the user can no longer authenticate.
- **AC-068** — Given a removed user's audit history exists, when they are removed, then the audit log is preserved but their displayable identity becomes 'Removed user (hash)' to satisfy data-protection while keeping accountability.
- **AC-069** — Given a client admin attempts to remove the last admin in their tenant, when they submit, then the action is blocked with an error message instructing them to promote another admin first.

### US-024 — Enterprise SSO
As a *enterprise client*, I want *to log in via my company's SAML 2.0 or OIDC identity provider*, so that *I can use existing SSO and MFA infrastructure instead of a separate password*.

**Covers:** REQ-015

**Acceptance criteria:**
- **AC-070** — Given a tenant configured for SSO, when a user from that tenant lands on the login page, then they are presented with an 'SSO Login' button that initiates the configured SAML 2.0 or OIDC flow.
- **AC-071** — Given a successful SSO assertion with a valid email and tenant claim, when the assertion is consumed, then a session is established with the role mapped from the assertion's group claim.
- **AC-072** — Given a tenant has SSO enabled, when a user from that tenant attempts password+TOTP login, then the password login is disabled for their tenant and they are redirected to the SSO flow.

### US-025 — Audit log of authentication events
As a *security analyst*, I want *to query authentication events from an immutable audit log*, so that *I can investigate suspicious access patterns and prove compliance*.

**Covers:** REQ-016

**Acceptance criteria:**
- **AC-073** — Given any login attempt (success or failure), when it completes, then an audit entry is written containing user identifier, tenant, IP, user agent, factor used, outcome, and timestamp.
- **AC-074** — Given an account lockout or rate-limit trigger, when it fires, then a discrete audit entry is written distinct from individual login attempts.
- **AC-075** — Given a security analyst issues a query for authentication events filtered by user or tenant or IP within a date range, when the query runs, then results are returned within 5 seconds at p95 for the last 90 days.

### US-026 — Audit log of document views
As a *security analyst*, I want *to query every document view event from the audit log*, so that *I can prove which client tenant saw which document version at which time*.

**Covers:** REQ-016

**Acceptance criteria:**
- **AC-076** — Given an authenticated user opens a document page, when the page is served, then an audit entry is written with user identifier, tenant, document ID, version ID, and timestamp.
- **AC-077** — Given a search request that returns titles, when the response is served, then an audit entry records the search query (or its hash if PII concern), the user, and the IDs of returned documents.
- **AC-078** — Given the audit log retains document-view events ≥ 12 months, when a security analyst queries the log for a specific document and date range, then results are returned within the retention window.

### US-027 — Audit log of administrative actions
As a *security analyst*, I want *to query administrative actions from the audit log*, so that *I can prove who changed scoping, who unpublished, and who altered AI review decisions*.

**Covers:** REQ-016

**Acceptance criteria:**
- **AC-079** — Given any admin action (invite, role change, scope change, unpublish, manual sync re-trigger, AI review decision), when it completes, then an audit entry captures the actor, target, action type, before/after values where applicable, and timestamp.
- **AC-080** — Given an AI review decision (ignore / acknowledge / block), when the reviewer submits it, then an audit entry records the reviewer identity, the page version, the finding, and the chosen action.
- **AC-081** — Given an attempt to alter an existing audit entry, when the write is issued at any layer, then the write is rejected and the rejection itself is logged.

## Theme: Client Portal

### US-028 — Browse by product and category
As a *client end user*, I want *to browse the portal organised by product and guide category*, so that *I can find the documentation for the product I am integrating with*.

**Covers:** REQ-020

**Acceptance criteria:**
- **AC-082** — Given an authenticated user lands on the portal home, when the page renders, then the navigation shows a list of products derived from Confluence labels, each with its guide categories beneath it.
- **AC-083** — Given the same set of source labels, when navigation is rendered for two different users at the same time, then the resulting grouping is identical (deterministic).
- **AC-084** — Given a user has no entitled documents under a product (due to scoping), when navigation renders, then that product is omitted from their navigation rather than shown empty.

### US-029 — Latest version is the default view
As a *client end user*, I want *to land on the latest published version of a document by default*, so that *I never have to guess whether I am reading the current version*.

**Covers:** REQ-021

**Acceptance criteria:**
- **AC-085** — Given a user opens a document URL without an explicit version suffix, when the page renders, then the latest published version is shown with a 'Latest' badge and the publish timestamp.
- **AC-086** — Given a document has been updated since the user's last visit, when they open it, then the page is rendered from the latest version with no cached older version surfaced.
- **AC-087** — Given the latest version differs from the version the user was last reading, when the page renders, then a non-blocking banner offers a link to the diff against the previous version they viewed.

### US-030 — View previous version
As a *client end user*, I want *to open any previous published version of a document I have access to*, so that *I can refer back to documentation that matches an older integration*.

**Covers:** REQ-022

**Acceptance criteria:**
- **AC-088** — Given a user opens the version history panel, when they click a previous version row, then the document re-renders at that version with a clear 'Viewing older version' banner.
- **AC-089** — Given a user is viewing an older version, when they click 'Back to latest', then the page re-renders at the latest version and the banner clears.
- **AC-090** — Given an older version exists but the document is unpublished, when a user attempts to view it, then they receive a 'not available' message even if they have the direct URL.

### US-031 — Diff previous vs latest
As a *client end user*, I want *to diff a previous version against the latest*, so that *I can see exactly what changed between integrations*.

**Covers:** REQ-022

**Acceptance criteria:**
- **AC-091** — Given two version IDs of the same document the user is entitled to, when the user opens the diff view, then the rendered diff highlights added content in green, removed content in red, and modified blocks in yellow at the block level.
- **AC-092** — Given a diff is open, when the user toggles between 'side-by-side' and 'inline' modes, then both representations show the same diff data without re-fetching.
- **AC-093** — Given a diff cannot be computed (e.g. one of the versions is missing), when the view is requested, then a graceful error is shown rather than an empty page.

### US-032 — Per-page PDF download
As a *client end user*, I want *to download the currently-viewed document version as a styled PDF*, so that *I can read offline and distribute internally*.

**Covers:** REQ-023

**Acceptance criteria:**
- **AC-094** — Given a user clicks 'Download as PDF' on a document page, when the action completes, then a PDF is generated and downloaded that renders the same content as the on-screen page including images and code blocks.
- **AC-095** — Given the generated PDF, when inspected, then its footer contains the document title, version number, publish timestamp, and the requesting user's tenant identity (for audit traceability).
- **AC-096** — Given a PDF generation request fails (e.g. timeout), when the failure occurs, then the user sees a clear error toast and the failure is logged for operations to investigate.

### US-033 — Full-text search
As a *client end user*, I want *to search the portal full-text and find pages by phrase, term, or product*, so that *I can locate what I need without browsing through hierarchies*.

**Covers:** REQ-024

**Acceptance criteria:**
- **AC-097** — Given a user enters a query and submits, when results return, then matching documents are listed with title, snippet showing the matched terms in context, product, and last-updated timestamp, ranked by relevance.
- **AC-098** — Given a query returns more than 20 results, when the user reaches the bottom, then additional results page in (or scroll-paginate) without a full page reload.
- **AC-099** — Given a search query is submitted, when the search runs, then p95 response time is < 1 second for the user's entitled corpus.

### US-034 — Search respects scope
As a *client end user*, I want *to never see search results that include documents I am not entitled to read*, so that *the search bar cannot be used to discover the existence of out-of-scope documents*.

**Covers:** REQ-024

**Acceptance criteria:**
- **AC-100** — Given a user submits a query that would match a document outside their entitled scope, when results are computed, then the document is excluded from results entirely (not surfaced and then hidden).
- **AC-101** — Given a user submits a query that matches no entitled documents, when results render, then the response is 'No results' rather than counts or hints of out-of-scope hits.
- **AC-102** — Given an automated multi-tenant search isolation test, when it runs on every release, then it asserts a tenant A user querying for a known tenant-B-only title returns zero results.

### US-035 — Per-user last-visited tracking
As a *client end user*, I want *to have my last-visited timestamp per page tracked*, so that *the AI change-summary feature can show me what is new since I last looked*.

**Covers:** REQ-025

**Acceptance criteria:**
- **AC-103** — Given an authenticated user opens a document page, when the page renders, then the user's last-visited timestamp for that document is updated to the current time, scoped to that user.
- **AC-104** — Given a user opens the portal landing page, when 'Since your last visit' is computed (REQ-051), then the computation uses the per-user last-visited timestamps to determine what is new.
- **AC-105** — Given a user requests that their tracking data be deleted (data-protection right), when the request is honoured, then the per-user last-visited records for that user are erased within the configured timeframe and the deletion is audit-logged.

## Theme: Notifications

### US-036 — Digest email notifications
As a *client end user*, I want *to receive an email when documentation I am entitled to has changed, on a digest cadence I choose*, so that *I find out about relevant changes without checking the portal manually*.

**Covers:** REQ-030

**Acceptance criteria:**
- **AC-106** — Given a user has subscribed to immediate notifications, when an entitled document is published, then they receive an email within 15 minutes of publish with a deep link to the changed page.
- **AC-107** — Given a user has subscribed to a daily or weekly digest, when the configured cadence elapses, then they receive a single email summarising all entitled changes in that window (or no email if there are none).
- **AC-108** — Given a user is unsubscribed from notifications, when entitled documents change, then they receive no email and the unsubscribed state is honoured across all cadences.

### US-037 — Notifications respect scope
As a *client end user*, I want *to never receive an email about a page I am not entitled to read*, so that *notifications cannot leak the existence of out-of-scope content*.

**Covers:** REQ-030

**Acceptance criteria:**
- **AC-109** — Given a notification batch is being assembled, when a candidate page is being evaluated for inclusion in a user's email, then the user's tenant entitlement is re-evaluated at send time (not just at subscribe time).
- **AC-110** — Given a user's entitlement to a document is revoked between subscribe time and send time, when the email is sent, then the document is excluded from that user's email.
- **AC-111** — Given an automated email-scope test, when it runs on every release, then it asserts no email contains a deep link to a document the recipient cannot access.

### US-038 — Email contains release highlights
As a *client end user*, I want *to read a release-highlights summary in the notification email before clicking through to the portal*, so that *I can decide if a change needs my attention without opening the page*.

**Covers:** REQ-031

**Acceptance criteria:**
- **AC-112** — Given a notification email is rendered, when the user opens it, then for each changed page the email shows the page title, a 1–3 sentence AI-generated highlight summary (REQ-053), and a deep link to the page on the portal.
- **AC-113** — Given the digest contains more than 5 changed pages, when the email is rendered, then only the top 5 are shown inline with a 'view full list' link to the portal that takes the user to a filtered changes view.
- **AC-114** — Given a user clicks a deep link in the email, when they land on the portal, then the URL preserves the source = 'email-digest' parameter for analytics without exposing the user's email.

### US-039 — Manage notification preferences
As a *client end user*, I want *to manage my own notification preferences from a profile page*, so that *I do not have to contact WSD support to change my cadence or unsubscribe*.

**Covers:** REQ-032

**Acceptance criteria:**
- **AC-115** — Given a user opens the profile / preferences page, when it renders, then they see their current cadence (immediate / daily / weekly / off) and per-product subscription toggles, all editable.
- **AC-116** — Given a user changes their cadence or product subscriptions and saves, when the next eligible notification would fire, then the new preferences take effect; the change is also reflected in subsequent emails' unsubscribe footer.
- **AC-117** — Given a user uses the one-click 'unsubscribe' link in any email footer, when they confirm, then their cadence is set to 'off' for that product (or globally if the email was a cross-product digest) without requiring them to log in.

## Theme: AI Document Review

### US-040 — AI detects secrets and credentials
As a *publishing pipeline*, I want *to run the AI document-review pass and detect secrets, API keys, and credentials before publish*, so that *secret material never reaches the client portal*.

**Covers:** REQ-040

**Acceptance criteria:**
- **AC-118** — Given a candidate page contains a string matching a high-entropy secret pattern (e.g. AWS access key, generic API key shape), when the AI review runs, then the finding is raised with category = 'secret', severity = 'high', and the matched span is recorded.
- **AC-119** — Given the AI review is uncertain (confidence below threshold) about a candidate secret, when the review completes, then the finding is raised with severity = 'medium' rather than ignored, and routed to a reviewer.
- **AC-120** — Given the AI review detects no secrets, when the review completes, then a 'no-secret-findings' result is recorded for the page version and the page proceeds to the next gate.

### US-041 — AI detects internal URLs, Jira links, and internal emails
As a *publishing pipeline*, I want *to detect internal-only URLs, Jira/internal-ticket links, and internal employee email addresses*, so that *no internal references leak to clients*.

**Covers:** REQ-040

**Acceptance criteria:**
- **AC-121** — Given a candidate page contains a URL matching the configured internal-domain allow-list (e.g. ending in .internal.wsd.com), when review runs, then a finding is raised with category = 'internal-url', severity = 'high'.
- **AC-122** — Given a candidate page contains a link or reference matching the Jira / internal-ticket URL patterns, when review runs, then a finding is raised with category = 'internal-ticket', severity = 'high'.
- **AC-123** — Given a candidate page contains an email address whose domain matches the configured internal-email allow-list, when review runs, then a finding is raised with category = 'internal-email', severity = 'high' for staff inboxes and 'medium' for shared/team inboxes.

### US-042 — AI detects missing content
As a *publishing pipeline*, I want *to flag pages with structurally missing content such as empty sections or placeholder strings*, so that *clients never read documentation that says 'TODO' or 'lorem ipsum'*.

**Covers:** REQ-040

**Acceptance criteria:**
- **AC-124** — Given a candidate page contains placeholder strings (case-insensitive 'TODO', 'TBD', 'FIXME', 'lorem ipsum', 'xxx'), when review runs, then a finding is raised with category = 'missing-content', severity = 'medium'.
- **AC-125** — Given a candidate page contains a heading immediately followed by another heading at the same or deeper level (empty section), when review runs, then a finding is raised with category = 'empty-section', severity = 'low'.
- **AC-126** — Given a candidate page is shorter than a configurable minimum (default 100 words excluding boilerplate), when review runs, then a finding is raised with category = 'stub', severity = 'low'.

### US-043 — Hard block on high-severity findings
As a *publishing pipeline*, I want *to hard-block publishing of any page that has an unresolved high-severity AI finding*, so that *screening cannot be bypassed by deadline pressure*.

**Covers:** REQ-041

**Acceptance criteria:**
- **AC-127** — Given a page has at least one open finding with severity = 'high', when the publishing pipeline reaches the publish gate, then publish is rejected and the page state becomes 'blocked-on-review' with the open findings listed.
- **AC-128** — Given all high-severity findings on a page are either reviewer-confirmed false positives or the page has been corrected and re-synced, when the publishing pipeline reaches the publish gate, then publish proceeds.
- **AC-129** — Given a doc owner attempts to publish a page with open high-severity findings via the manual re-trigger API, when the request is processed, then it is rejected and the bypass attempt is audit-logged.

### US-044 — Reviewer sees findings in context
As a *publishing reviewer*, I want *to see AI findings displayed in context with the matched span highlighted*, so that *I can evaluate each finding without having to re-read the whole page*.

**Covers:** REQ-042

**Acceptance criteria:**
- **AC-130** — Given a reviewer opens a page that has AI findings, when the review panel renders, then the page content is shown with each finding's matched span highlighted, colour-coded by severity.
- **AC-131** — Given a reviewer clicks a finding in the side list, when the click is registered, then the page scrolls so the matched span is centred and focused.
- **AC-132** — Given the matched span has been removed in a newer Confluence revision after the finding was raised, when the reviewer opens the panel, then the finding is marked 'stale' rather than shown against missing content.

### US-045 — Reviewer triages each finding
As a *publishing reviewer*, I want *to triage each AI finding by choosing ignore / acknowledge / block, with my decision audit-logged*, so that *review decisions are traceable and defensible*.

**Covers:** REQ-042

**Acceptance criteria:**
- **AC-133** — Given a finding is open, when a reviewer selects 'ignore', then the finding is marked closed-as-false-positive, the reviewer identity and timestamp are audit-logged, and (if it was the last high-severity blocker) the page becomes publishable.
- **AC-134** — Given a finding is open, when a reviewer selects 'acknowledge' on a non-high-severity finding, then the finding is marked closed-as-acknowledged and the page becomes publishable.
- **AC-135** — Given a finding is open, when a reviewer selects 'block', then the page state becomes 'blocked-pending-source-fix' until the source page is corrected and re-synced (re-syncing creates a new review pass).

### US-062 — AI review fails closed
As a *publishing pipeline*, I want *to fail closed when the AI provider is unavailable rather than skipping screening*, so that *AI-provider outages cannot become a vector for unscreened content reaching clients*.

**Covers:** REQ-105

**Acceptance criteria:**
- **AC-184** — Given the AI document-review provider is unavailable (timeout, 5xx, or auth failure), when a page reaches the review step, then the page is queued in 'review-pending-provider' state and an alert is raised; the page is NOT published.
- **AC-185** — Given the AI provider becomes available again, when the queued page is retried, then review proceeds and (assuming clean findings) publish completes.
- **AC-186** — Given an operator attempts to bypass the review step via a configuration flag or API, when the attempt is made in production, then the action is blocked unless a documented two-person break-glass procedure is followed and recorded.

## Theme: AI Release Notes & Change Summary

### US-046 — Generate AI release notes
As a *publishing pipeline*, I want *to generate AI release notes covering What's New, Breaking Changes, and Recommended Actions when a page changes*, so that *release-note authoring stops being a manual cost on every release*.

**Covers:** REQ-050

**Acceptance criteria:**
- **AC-136** — Given a page is being published as a new version, when release-note generation runs, then it produces three sections — What's New, Breaking Changes, Recommended Actions — based on the diff against the prior published version.
- **AC-137** — Given a page has no prior published version, when release-note generation runs, then What's New describes the initial publication and the other two sections render 'None for this release'.
- **AC-138** — Given release-note generation fails (AI provider error), when the failure occurs, then the page enters 'release-notes-pending' state, an alert is raised, and the publish does not proceed until release notes exist or are explicitly waived.

### US-047 — Reviewer approves release notes
As a *publishing reviewer*, I want *to approve AI-generated release notes before clients see them*, so that *no AI-authored copy reaches clients without a human gate*.

**Covers:** REQ-050

**Acceptance criteria:**
- **AC-139** — Given release notes have been generated, when the reviewer opens the review panel, then they see the three sections side-by-side with the diff that produced them.
- **AC-140** — Given a reviewer clicks 'Approve', when the action is recorded, then the release notes become the published artefact for that version and the approval is audit-logged.
- **AC-141** — Given a reviewer takes no action longer than the configured SLA (default 24 hours for high-severity diffs, 72 hours otherwise), when the SLA elapses, then a reminder notification is sent and the timeout is surfaced on the dashboard.

### US-048 — Per-client since-last-visit summary
As a *client end user*, I want *to see a per-client 'Since your last visit' summary on the portal landing page*, so that *I orient quickly to what changed without scanning every product*.

**Covers:** REQ-051

**Acceptance criteria:**
- **AC-142** — Given an authenticated user opens the portal landing page, when the page renders, then a 'Since your last visit' block shows an AI-generated paragraph summarising the entitled pages that have changed since their last view per page.
- **AC-143** — Given a user has no changes since their last visit, when the landing page renders, then the block shows 'You are up to date' rather than fabricating change content.
- **AC-144** — Given the underlying change set has not changed since the last render, when the user reloads the landing page, then the summary is served from cache rather than regenerated.

### US-049 — Reviewer can regenerate, edit, or discard release notes
As a *publishing reviewer*, I want *to regenerate, edit inline, or discard any AI-generated release-notes block*, so that *I can quickly correct or override AI output without leaving the review UI*.

**Covers:** REQ-052

**Acceptance criteria:**
- **AC-145** — Given a reviewer clicks 'Regenerate' on a release-notes block, when the action runs, then a new draft replaces the current one (the previous draft remains accessible in the revision side-panel) and the regeneration is audit-logged.
- **AC-146** — Given a reviewer edits a release-notes block inline and clicks save, when the save succeeds, then their edits are persisted and any subsequent regeneration starts from the edited text unless the reviewer explicitly discards their edits.
- **AC-147** — Given a reviewer clicks 'Discard', when they confirm, then the release-notes block for this version is cleared and the publish gate now requires either an empty-but-approved or a regenerated release-notes block.

## Theme: AI Client Notifications

### US-050 — AI client-notification summaries
As a *notification pipeline*, I want *to insert AI-generated per-client concise summaries into each outgoing email*, so that *notification emails are short and tailored, not noisy*.

**Covers:** REQ-053

**Acceptance criteria:**
- **AC-148** — Given a notification email is being assembled for a user, when each changed page is processed, then a concise AI-generated summary (≤ 30 words) is generated per page based on the changes the user is entitled to see.
- **AC-149** — Given two users in the same tenant subscribe to the same digest, when their emails are assembled, then each user receives a summary generated against their per-user entitled change set (they may differ if entitlements differ).
- **AC-150** — Given AI summary generation fails for a page, when the failure occurs, then the email falls back to the page title plus 'View changes on portal' without sending a broken email.

### US-051 — Reviewer approves breaking-change notification summary
As a *publishing reviewer*, I want *to approve an AI notification summary before it sends when the underlying change is flagged as breaking*, so that *breaking-change notifications cannot be auto-sent without human sign-off*.

**Covers:** REQ-053

**Acceptance criteria:**
- **AC-151** — Given a release-notes pass has flagged at least one entry under 'Breaking Changes' for a page, when the notification email is being assembled, then the email sits in 'pending-review' state and is not sent until a reviewer approves.
- **AC-152** — Given a reviewer approves a pending breaking-change notification, when they click 'Approve & Send', then the email is dispatched to the digest recipients and the approval is audit-logged with reviewer identity and timestamp.
- **AC-153** — Given a reviewer rejects a pending breaking-change notification, when they click 'Reject', then the email is not sent for that change and the rejection plus reason are audit-logged.

## Theme: AI Documentation Quality Check

### US-052 — AI quality scoring on publish
As a *documentation owner*, I want *to see AI-generated quality scores (completeness, readability, missing examples, missing API responses) when I publish*, so that *I can catch documentation-quality regressions before clients do*.

**Covers:** REQ-054

**Acceptance criteria:**
- **AC-154** — Given a candidate page is about to enter the publish gate, when the quality scoring step runs, then four scores in [0..1] are produced for Completeness, Readability, Missing Examples, Missing API Responses and persisted with the page version.
- **AC-155** — Given a score is below the warning threshold for any dimension, when the doc owner views the publish summary, then a warning badge is shown next to the score with a short AI-generated suggestion.
- **AC-156** — Given quality scoring fails (provider error), when the failure occurs, then publishing is not blocked but a 'quality-score-unavailable' marker is recorded with the version.

### US-053 — Quality warning is overrideable with audit
As a *documentation owner*, I want *to override a low quality-score warning and publish anyway, with my decision recorded*, so that *quality scoring nudges but does not gate, and I keep the final say*.

**Covers:** REQ-054

**Acceptance criteria:**
- **AC-157** — Given a publish summary shows a low quality-score warning, when the doc owner clicks 'Publish anyway' and supplies an override reason, then publish proceeds and the override (reason + identity) is audit-logged with the version.
- **AC-158** — Given a publish summary shows a low quality-score warning, when the doc owner cancels and edits the source page in Confluence, then re-syncing the page re-runs scoring and shows the new scores in a fresh publish summary.
- **AC-159** — Given the published version was published under override, when a future reader views the version metadata, then the override marker is visible to internal staff (not to clients) so retro reviews can find quality-bypass cases.

### US-054 — Quality trend over time
As a *documentation owner*, I want *to see the trend of quality scores over time per page*, so that *I can spot pages that are getting worse and prioritise rewrites*.

**Covers:** REQ-055

**Acceptance criteria:**
- **AC-160** — Given a page has at least three published versions, when the doc owner opens the page's quality view, then a chart is shown for each of the four dimensions over the publish history.
- **AC-161** — Given a page has fewer than three published versions, when the quality view is opened, then the trend chart shows current values and a 'not enough history' notice rather than empty axes.
- **AC-162** — Given quality scoring was unavailable for a particular version, when the trend is rendered, then that version is shown as a gap in the line rather than as zero.

## Theme: Performance

### US-055 — Portal render p95 SLA
As a *platform operator*, I want *to have portal page render p95 under 1.5 s under expected client load*, so that *the portal feels responsive at launch and on a typical day*.

**Covers:** REQ-100

**Acceptance criteria:**
- **AC-163** — Given the synthetic-load test runs the standard 500-user reading workload, when results are collected, then portal page render p95 measured server-side from request to last byte of HTML is < 1.5 s.
- **AC-164** — Given p95 portal render exceeds 1.5 s over a rolling 15-minute window in production, when the threshold is breached, then a paging alert is fired and the deployment is auto-rolled-back if the breach started after the most recent deploy.
- **AC-165** — Given the read tier is healthy, when an authenticated user opens any document page, then the first contentful paint occurs within 1 s on a representative WSD client environment baseline.

### US-056 — End-to-end sync latency observability
As a *platform operator*, I want *to have sync latency observability covering Confluence approval through portal visibility, including AI review*, so that *the 5-minute SLA is enforced and AI review latency is visible*.

**Covers:** REQ-101

**Acceptance criteria:**
- **AC-166** — Given a publish run completes successfully, when metrics are emitted, then the total end-to-end latency from approval to portal visibility is recorded, plus a sub-breakdown for AI review duration.
- **AC-167** — Given p95 end-to-end latency exceeds 5 minutes OR p95 total (including AI review) exceeds 15 minutes over a rolling 15-minute window, when the threshold is breached, then a paging alert is raised.
- **AC-168** — Given an operator opens the sync dashboard, when they filter by a single page, then they see per-stage timings for the most recent N publishes (configurable, default 50).

## Theme: Data Protection

### US-057 — TLS enforced
As a *security engineer*, I want *to enforce TLS 1.2+ for all client-facing traffic*, so that *no plaintext data ever crosses the public network*.

**Covers:** REQ-102

**Acceptance criteria:**
- **AC-169** — Given a client connection is established, when the TLS handshake completes, then the negotiated protocol is TLS 1.2 or TLS 1.3 with a permitted cipher suite (no exportable, no RC4, no SHA-1).
- **AC-170** — Given a client attempts a connection with TLS 1.1 or lower, when the handshake begins, then the server rejects the connection cleanly.
- **AC-171** — Given the portal's TLS configuration is in production, when an external scan runs (e.g. Mozilla TLS observatory or equivalent), then the configuration achieves at minimum the 'intermediate' grade with no known-vulnerable settings.

### US-058 — Data encrypted at rest
As a *security engineer*, I want *to encrypt session tokens, audit logs, AI-pipeline payloads, and other sensitive at-rest data*, so that *even with disk or backup access, an attacker cannot read sensitive material in cleartext*.

**Covers:** REQ-102

**Acceptance criteria:**
- **AC-172** — Given any data store containing session tokens, audit log entries, or AI-pipeline payloads, when data is written to disk, then it is encrypted using platform-standard KMS-managed keys.
- **AC-173** — Given a KMS key rotation event, when the rotation completes, then existing data continues to be readable under the new key alias and the rotation is audit-logged.
- **AC-174** — Given a verifiable security check runs (e.g. automated infra audit), when it inspects each data store, then no store is found in plaintext-at-rest configuration.

### US-059 — Data-layer tenant isolation
As a *platform engineer*, I want *to enforce per-client data isolation at the data-access layer, validated by tests*, so that *no UI bug or API guess can produce a cross-tenant data leak*.

**Covers:** REQ-103

**Acceptance criteria:**
- **AC-175** — Given every read or write query against tenant-scoped tables, when issued by application code, then the query carries the active tenant ID and the data layer rejects queries without it or with a tenant ID inconsistent with the authenticated session.
- **AC-176** — Given the automated isolation test suite, when it runs as part of CI on every release, then for every read endpoint it asserts that requests authenticated as tenant A cannot retrieve data created as tenant B.
- **AC-177** — Given a developer attempts to add a new read endpoint without tenant scoping, when CI runs, then a lint/static-analysis check fails the build with a clear message pointing to the unscoped query.

## Theme: Accessibility

### US-060 — Keyboard navigation
As a *client end user with assistive technology*, I want *to navigate the entire portal by keyboard alone, with logical focus order and visible focus rings*, so that *I can use the portal without a pointing device*.

**Covers:** REQ-104

**Acceptance criteria:**
- **AC-178** — Given an authenticated user is on any portal page, when they use Tab and Shift+Tab to move focus, then every interactive control is reachable, the focus order matches the visual order, and every focused element has a visible focus indicator meeting WCAG AA contrast.
- **AC-179** — Given a modal or dialog is opened (e.g. PDF generation confirmation), when it is open, then focus is trapped inside it and Escape closes it returning focus to the opener.
- **AC-180** — Given an automated a11y test (e.g. axe-core) runs on every release across login, browse, read, version history, search, and PDF flows, when results are collected, then zero serious or critical violations are reported.

### US-061 — Screen reader and contrast
As a *client end user with assistive technology*, I want *to use a screen reader to read documents with correct semantic structure and image alt-text*, so that *I can consume documentation non-visually*.

**Covers:** REQ-104

**Acceptance criteria:**
- **AC-181** — Given a screen reader reads a document page, when it traverses the content, then headings are exposed with their semantic levels, lists as lists, tables with row/column headers, and images announce their alt-text.
- **AC-182** — Given a colour palette change is proposed, when a contrast check runs against text/background pairs in the design tokens, then all combinations meet WCAG AA contrast ratios.
- **AC-183** — Given a non-text status indicator (e.g. coloured badge), when a screen reader reaches it, then a text-equivalent label is announced (e.g. 'Status: blocked-on-review').

## Theme: Scalability

### US-063 — Horizontal scaling of read tier
As a *platform engineer*, I want *to scale the portal read tier horizontally so capacity grows with client headcount*, so that *onboarding a large client does not require an architectural rewrite*.

**Covers:** REQ-106

**Acceptance criteria:**
- **AC-187** — Given the portal read tier is deployed behind a load balancer, when a new read-tier instance is added, then it serves traffic within 60 seconds of becoming healthy without requiring a deploy of other tiers.
- **AC-188** — Given a synthetic load doubles, when read-tier autoscaling fires, then additional instances come online and p95 render latency returns under 1.5 s within 5 minutes.
- **AC-189** — Given any read-tier instance is terminated mid-request, when the request retries via the load balancer, then it succeeds on a different instance without surfacing an error to the user.

## Theme: Audit & Compliance

### US-064 — Audit log tamper-evident retention
As a *security analyst*, I want *to know that audit logs cannot be tampered with and are retained at least 12 months*, so that *audit evidence is admissible and complete*.

**Covers:** REQ-107

**Acceptance criteria:**
- **AC-190** — Given audit log entries (auth, view, admin, AI review) are written, when stored, then they live in an append-only or cryptographically signed log such that any subsequent edit or deletion is detectable at scan time.
- **AC-191** — Given an integrity scan runs on a schedule (at minimum daily), when it completes, then it verifies the audit chain has not been altered and emits a signed report; any verification failure pages security.
- **AC-192** — Given an audit log entry is older than 12 months and within retention policy, when retrieved, then it returns intact; entries beyond retention policy are archived to cold storage with the same tamper-evident properties.
