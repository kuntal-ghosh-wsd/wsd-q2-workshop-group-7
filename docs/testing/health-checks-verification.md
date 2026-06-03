# Local Dev: Keycloak Setup & Health-Check Verification

A self-contained guide for spinning up the full WAIF stack on a laptop — including a local Keycloak — and verifying the runtime behaviour of `/live`, `/ready`, and `/health`.

Useful when you're:
- Reviewing a PR that touches auth or health-check code
- Debugging a health-probe issue locally
- Onboarding to the WAIF auth flow without staging access
- Sanity-checking that `/ready` and `/health` behave correctly under upstream failure

No VPN required for the core flow. One optional step probes staging WSD Auth and needs network access to `staging-authentication.wallstreetdocs.com`.

---

## 0. Prerequisites

| Need | Why |
|---|---|
| Docker Desktop (or compatible) | Containers |
| `curl`, `jq` | Hitting endpoints, parsing JSON |
| Node.js 24.x + `npm` | Running the unit test suite (optional) |
| Repo checkout with the local-Keycloak setup (`docker/keycloak/`, `docker-compose.local.yml`) | Local Keycloak service |

Optional:
- VPN to `staging-authentication.wallstreetdocs.com` for the WSD Auth probe
- Incognito browser window for the SSO flow (avoids cookie carry-over)

---

## 1. Bring up the local stack

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build
```

This builds the WAIF image and starts four containers:

| Container | Host port → container port | Purpose |
|---|---|---|
| `waif-server` | `4444 → 4444` | WAIF API |
| `waif-mongodb` | `27020 → 27017` | App config + persistent state |
| `waif-redis` | `6390 → 6379` | Cache + rate-limit counters |
| `waif-keycloak` | `8081 → 8080` | Local Keycloak realm `waif-dev` |

Wait until all four show healthy (first boot ~60s, mostly Keycloak's schema migration):

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml ps
```

Expected: every row shows `Up (healthy)`.

> **Why two compose files?** `docker-compose.yml` is the production-shaped baseline (WAIF + Mongo + Redis only). `docker-compose.local.yml` layers on the Keycloak service plus dev-friendly env wiring (`env_file: .env`, inline Keycloak env vars). Running with only the first file gives you a clean stack without Keycloak; the second is a strict opt-in.

---

## 2. Understand the local Keycloak setup

The setup auto-imports a realm called `waif-dev` from `docker/keycloak/waif-dev-realm.json` on Keycloak's first boot.

### Pre-seeded realm contents

| Item | Value |
|---|---|
| Realm name | `waif-dev` |
| Client | `waif-api` (public, direct-access-grants enabled) |
| Client roles | `ROLE_WAIF_Admin`, `ROLE_WAIF_User`, `ROLE_WAIF_Pipeline_All` |
| Protocol mappers | `orgId` (long), `orgIds` (long, multivalued) |
| Test user (regular) | `tester` / `tester` — has `ROLE_WAIF_User`, `orgId=1` |
| Test user (admin) | `admin-tester` / `admin` — has all three client roles, `orgId=1` |
| Keycloak realm admin (admin console at `http://localhost:8081/admin`) | `admin` / `admin` |

### URL geometry: browser vs container

The compose configures two different views of the same Keycloak:

| Audience | URL | Why |
|---|---|---|
| Your browser (host) | `http://localhost:8081/realms/waif-dev/...` | Host port mapping |
| `waif-server` container (backchannel) | `http://keycloak:8080/realms/waif-dev/...` | Docker network DNS |

Keycloak is told `KC_HOSTNAME=localhost` + `KC_HOSTNAME_PORT=8081` so it advertises the **browser-facing URL** in form actions, redirects, and the `iss` claim of issued JWTs. `KC_HOSTNAME_STRICT_BACKCHANNEL=false` lets `waif-server` reach Keycloak via container DNS even though that hostname doesn't match.

WAIF picks up both URLs:

| WAIF config field | Value | Used for |
|---|---|---|
| `auth.keycloak.issuer` | `http://localhost:8081/realms/waif-dev` | String-match against JWT `iss` claim |
| `auth.keycloak.jwksUri` | `http://keycloak:8080/realms/waif-dev/protocol/openid-connect/certs` | Server-side: fetch signing keys |
| `auth.keycloak.loginPageUrl` | `http://localhost:8081/realms/waif-dev/protocol/openid-connect/auth` | Browser redirect when "Sign in with Keycloak" is clicked |
| `auth.keycloak.generateTokenUrl` | `http://keycloak:8080/realms/waif-dev/protocol/openid-connect/token` | Server-side: code → token exchange on OAuth callback |
| `auth.keycloak.healthUrl` (override) **or** `${issuer}${healthPath}` | `http://keycloak:8080/realms/waif-dev/.well-known/openid-configuration` | Server-side: `/health` probe |

If `healthUrl` is set, it wins. If empty, WAIF computes `${issuer}${healthPath}`. In this split setup, `${issuer}` is `localhost:8081` which is unreachable from inside the container — so locally we use the `healthUrl` override. In production, `issuer` is directly reachable from waif-server pods and no override is needed.

For the full hostname/port rationale, see `docker/keycloak/README.md`.

### How env vars reach the running app

```
docker-compose.yml + docker-compose.local.yml (inline environment + env_file: .env)
                                │
                                ▼
                       container's process.env
                                │
                                ▼
        src/config/env-loader.ts reads on FIRST BOOT only
                                │
                                ▼
              writes to MongoDB collection `app_config`
                                │
                                ▼
              runtime: app reads from MongoDB (NOT process.env)
```

After first boot, MongoDB is the source of truth. Changing a compose env var alone doesn't change runtime config — you'd need to drop the `app_config` doc and restart, or PATCH the dynamic config via the admin API.

The `.env` file at the repo root is loaded into the container by the `env_file: .env` directive in `docker-compose.local.yml`. Inline `environment:` keys in the compose still win over `.env` on any conflict.

---

## 3. Authenticate as a test user

Two routes — pick whichever matches your testing style.

### 3a. Mint a token via curl (fastest, recommended for API testing)

```bash
TOKEN=$(curl -sS -X POST \
  "http://localhost:8081/realms/waif-dev/protocol/openid-connect/token" \
  -d "client_id=waif-api" \
  -d "grant_type=password" \
  -d "username=admin-tester" \
  -d "password=admin" \
  | jq -r '.access_token')

# macOS convenience — also copies to clipboard
echo -n "$TOKEN" | pbcopy
echo "Token length: ${#TOKEN}"
```

Sanity-check the token claims:

```bash
PAYLOAD=$(echo "$TOKEN" | cut -d. -f2)
while [ $((${#PAYLOAD} % 4)) -ne 0 ]; do PAYLOAD="${PAYLOAD}="; done
echo "$PAYLOAD" | base64 -d 2>/dev/null \
  | jq '{iss, preferred_username, orgId, orgIds, resource_access}'
```

Expected:
```json
{
  "iss": "http://localhost:8081/realms/waif-dev",
  "preferred_username": "admin-tester",
  "orgId": 1,
  "orgIds": [1],
  "resource_access": {
    "waif-api": {
      "roles": ["ROLE_WAIF_Pipeline_All", "ROLE_WAIF_User", "ROLE_WAIF_Admin"]
    }
  }
}
```

Use it against WAIF:
```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:4444/api/pipelines?orgId=1" | jq
```

For a non-admin user, swap `admin-tester`/`admin` → `tester`/`tester`.

Tokens expire (default ~30 min). Re-run the mint command for a fresh one.

### 3b. Browser SSO flow

1. Visit the WAIF Test Harness in your browser (e.g. `http://localhost:4444/` — exact harness URL may vary depending on which UI is bundled).
2. The harness fetches `/auth/providers` → discovers `keycloak` → shows a **Sign in with Keycloak** button.
3. Click it. Browser is redirected to `http://localhost:8081/realms/waif-dev/protocol/openid-connect/auth?...`.
4. Enter `admin-tester` / `admin` (or `tester` / `tester`) → submit.
5. Keycloak redirects back to `http://localhost:4444/auth/keycloak/callback?code=...`.
6. WAIF exchanges the code (via the backchannel — `http://keycloak:8080/.../token`) and establishes a session.
7. You land back at the harness, signed in.

If the browser flow fails, jump to the **Troubleshooting** section.

---

## 4. Health-check endpoint reference

WAIF exposes three Kubernetes-shaped probes. Knowing what each does is the foundation for any health-related testing.

| Endpoint | Audience | What it checks | k8s impact of failure |
|---|---|---|---|
| `/live` | Liveness probe | Process is alive (Node responding). Doesn't check anything else. | Pod restart. |
| `/ready` | Readiness probe | This pod can serve traffic **right now**. Pod-local checks only: in-process MongoDB + Redis connection pools. | Pod removed from the Service's endpoint list (no traffic). |
| `/health` | Operators, monitoring (Spring Boot Actuator format) | The full dependency picture: pod-local + every configured upstream HTTP service (LiteLLM, Digest, Ragas, Keycloak, WSD Auth). | None directly. Drives dashboards / alerts. |

The **critical design rule**: a correlated upstream blip (LiteLLM goes down, Keycloak hiccups, etc.) must not cause every WAIF replica to fail `/ready` simultaneously. That would pull every pod out of rotation and 503 all routes — even routes that don't touch the failing upstream. So upstream HTTP deps live on `/health` only.

The rationale is encoded as a comment at `src/api/v1.0/services/ietf-health.service.ts:153-155` and enforced by the unit test suite.

---

## 5. Verify health-check behaviour end-to-end

### 5.1 Confirm schema defaults seeded into MongoDB

WAIF's dynamic config has default values for each upstream's health-probe path:

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml exec mongodb \
  mongosh waif --quiet --eval '
const c = db.app_config.findOne({}).data;
print(JSON.stringify({
  keycloak_healthPath: c.auth.keycloak.healthPath,
  wsd_healthPath:      c.auth.wsd.healthPath,
  litellm_healthPath:  c.litellm.healthPath,
  digest_healthPath:   c.digest.healthPath,
  ragas_healthPath:    c.ragas.healthPath
}, null, 2));'
```

Expected on a fresh seed:
```json
{
  "keycloak_healthPath": "/.well-known/openid-configuration",
  "wsd_healthPath": "/api/v2.0/test/ping",
  "litellm_healthPath": "/health/liveliness",
  "digest_healthPath": "/health",
  "ragas_healthPath": "/health"
}
```

> **If different**, your MongoDB volume holds a stale seed from an older code version. Reseed:
> ```bash
> docker compose -f docker-compose.yml -f docker-compose.local.yml exec mongodb \
>   mongosh waif --quiet --eval 'db.app_config.deleteMany({}); db.app_config_history.deleteMany({})'
> docker compose -f docker-compose.yml -f docker-compose.local.yml restart waif-server
> ```

### 5.2 `/ready` registers only pod-local checks

`/ready` is auth-bypassed; no token needed:

```bash
curl -s http://localhost:4444/ready | jq '{status, checks: (.checks | keys)}'
```

Expected:
```json
{
  "status": "healthy",
  "checks": ["mongodb", "redis"]
}
```

The `checks` array must contain **exactly** `mongodb` and `redis` — no upstream HTTP deps.

### 5.3 Enable all upstream HTTP deps + verify they land on `/health` only

Reseed config to enable every upstream WAIF can probe (also loosens the strict auth rate limiter so testing isn't blocked):

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml exec mongodb \
  mongosh waif --quiet --eval '
db.app_config.updateOne({}, {
  $set: {
    "data.auth.enabled": true,
    "data.auth.keycloak.enabled": true,
    "data.auth.keycloak.healthUrl": "http://keycloak:8080/realms/waif-dev/.well-known/openid-configuration",
    "data.auth.wsd.enabled": true,
    "data.auth.wsd.tokenInfoUrl":     "https://staging-authentication.wallstreetdocs.com/oauth/tokeninfo",
    "data.auth.wsd.userInfoUrl":      "https://staging-authentication.wallstreetdocs.com/oauth/userinfo",
    "data.auth.wsd.generateTokenUrl": "https://staging-authentication.wallstreetdocs.com/oauth/token",
    "data.auth.wsd.clientId":         "waif-local-dev",
    "data.litellm.baseUrl": "https://staging-litellm.wsd.com",
    "data.digest.baseUrl":  "http://host.docker.internal:47823",
    "data.ragas.baseUrl":   "https://staging-litellm.wsd.com",
    "data.security.rateLimitAuthMax":    100,
    "data.security.rateLimitAuthWindow": 60
  },
  $inc: { version: 1 }
});'
docker compose -f docker-compose.yml -f docker-compose.local.yml exec redis redis-cli FLUSHALL
docker compose -f docker-compose.yml -f docker-compose.local.yml restart waif-server
```

Wait for healthy, then compare endpoints:

```bash
echo "=== /ready (should still be only pod-local) ==="
curl -s http://localhost:4444/ready | jq '{status, checks: (.checks | keys)}'

echo "=== /health (should now include all upstream deps) ==="
curl -s http://localhost:4444/health \
  | jq '{ status, connectivity: (.components | with_entries(select(.key | test("connectivity"))) | with_entries(.value |= .status)) }'
```

`/ready` should still be `["mongodb", "redis"]`. `/health` should now include `keycloak:connectivity`, `wsdAuth:connectivity`, `litellm:connectivity`, `digest:connectivity`, `ragas:connectivity` alongside the two pod-local ones.

Each upstream may be `UP` or `DOWN` depending on whether you have VPN; what matters here is that they're registered on `/health` and absent from `/ready`.

### 5.4 Keycloak probe end-to-end (default `healthPath` construction)

To prove the `healthPath` default actually drives the probe URL (not just the unit-test value), clear `healthUrl` and point `issuer` at container DNS so `${issuer}${healthPath}` becomes reachable:

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml exec mongodb \
  mongosh waif --quiet --eval '
db.app_config.updateOne({}, {
  $set: {
    "data.auth.keycloak.issuer":   "http://keycloak:8080/realms/waif-dev",
    "data.auth.keycloak.healthUrl": ""
  },
  $inc: { version: 1 }
});'
docker compose -f docker-compose.yml -f docker-compose.local.yml restart waif-server
```

Confirm the probe URL is now derived:

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml exec mongodb \
  mongosh waif --quiet --eval '
const k = db.app_config.findOne({}).data.auth.keycloak;
print(JSON.stringify({
  issuer: k.issuer,
  healthPath: k.healthPath,
  healthUrl: k.healthUrl,
  effective_probe_url: k.healthUrl || (k.issuer + k.healthPath)
}, null, 2));'
```

Expected:
```json
{
  "issuer": "http://keycloak:8080/realms/waif-dev",
  "healthPath": "/.well-known/openid-configuration",
  "healthUrl": "",
  "effective_probe_url": "http://keycloak:8080/realms/waif-dev/.well-known/openid-configuration"
}
```

And live:
```bash
curl -s http://localhost:4444/health | jq '.components["keycloak:connectivity"]'
```

Expected: `status: "UP"`, `responseTime` ~10-100ms.

> **Side effect**: this temporary change breaks the browser SSO flow (the issuer no longer matches the browser-facing URL). To restore SSO, put `issuer` back to `http://localhost:8081/realms/waif-dev` and set `healthUrl` back to the container-DNS URL.

### 5.5 WSD Auth probe end-to-end

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml exec mongodb \
  mongosh waif --quiet --eval '
const w = db.app_config.findOne({}).data.auth.wsd;
const origin = (() => { try { return new URL(w.tokenInfoUrl).origin; } catch { return null; }})();
print(JSON.stringify({
  enabled: w.enabled,
  tokenInfoUrl: w.tokenInfoUrl,
  healthPath: w.healthPath,
  effective_probe_url: origin + w.healthPath
}, null, 2));'
```

Expected:
```json
{
  "enabled": true,
  "tokenInfoUrl": "https://staging-authentication.wallstreetdocs.com/oauth/tokeninfo",
  "healthPath": "/api/v2.0/test/ping",
  "effective_probe_url": "https://staging-authentication.wallstreetdocs.com/api/v2.0/test/ping"
}
```

Live (requires VPN):
```bash
curl -s http://localhost:4444/health | jq '.components["wsdAuth:connectivity"]'
```

Expected: `status: "UP"`, `responseTime` few hundred ms (internet hop). If `responseTime` exceeds `degradedLatencyMs` (default 500), the underlying check reports `degraded` and the IETF wrapper maps it to `output: "Degraded"` but status stays `UP`.

### 5.6 Per-upstream blip simulation

The strongest demonstration of the `/ready` vs `/health` design: break each upstream individually and watch `/ready` stay green while `/health` flags only that component.

Save as `/tmp/blip-test.sh` and run:

```bash
cat > /tmp/blip-test.sh <<'EOF'
#!/usr/bin/env bash
set -e

declare -a CASES=(
  "keycloak|data.auth.keycloak.issuer|http://keycloak:8080/realms/waif-dev|http://blackhole.invalid|keycloak:connectivity"
  "wsdAuth|data.auth.wsd.tokenInfoUrl|https://staging-authentication.wallstreetdocs.com/oauth/tokeninfo|http://blackhole.invalid/x|wsdAuth:connectivity"
  "litellm|data.litellm.baseUrl|https://staging-litellm.wsd.com|http://blackhole.invalid|litellm:connectivity"
  "digest|data.digest.baseUrl|http://host.docker.internal:47823|http://blackhole.invalid|digest:connectivity"
  "ragas|data.ragas.baseUrl|https://staging-litellm.wsd.com|http://blackhole.invalid|ragas:connectivity"
)

for case in "${CASES[@]}"; do
  IFS='|' read -r name field orig bad component <<< "$case"
  echo ""
  echo "================================================================"
  echo "Blip: $name  (set ${field} → bad value)"
  echo "================================================================"
  docker compose -f docker-compose.yml -f docker-compose.local.yml exec mongodb mongosh waif --quiet --eval \
    "db.app_config.updateOne({}, { \$set: { '${field}': '${bad}' }, \$inc: { version: 1 } });" > /dev/null
  docker compose -f docker-compose.yml -f docker-compose.local.yml restart waif-server > /dev/null 2>&1
  while [ "$(docker inspect -f '{{.State.Health.Status}}' waif-server)" = "starting" ]; do sleep 2; done
  sleep 3

  ready_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:4444/ready)
  health_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:4444/health)
  component_status=$(curl -s http://localhost:4444/health | jq -r ".components[\"${component}\"].status // \"absent\"")

  echo "  /ready  → HTTP ${ready_status}"
  echo "  /health → HTTP ${health_status}"
  echo "  ${component} → ${component_status}"
  if [ "$ready_status" = "200" ] && [ "$component_status" = "DOWN" ]; then
    echo "  ✅ PASS"
  else
    echo "  ❌ FAIL"
  fi

  docker compose -f docker-compose.yml -f docker-compose.local.yml exec mongodb mongosh waif --quiet --eval \
    "db.app_config.updateOne({}, { \$set: { '${field}': '${orig}' }, \$inc: { version: 1 } });" > /dev/null
done

docker compose -f docker-compose.yml -f docker-compose.local.yml restart waif-server > /dev/null 2>&1
while [ "$(docker inspect -f '{{.State.Health.Status}}' waif-server)" = "starting" ]; do sleep 2; done
echo ""
echo "Baseline restored."
EOF
chmod +x /tmp/blip-test.sh
/tmp/blip-test.sh
```

Expected: five sections, each ending in `✅ PASS`. Every case demonstrates that:
- `/ready` returns **200** (k8s keeps the replica in the Service rotation)
- `/health` returns **503** (monitoring sees the issue)
- Only the targeted component shows `DOWN`; the other four upstreams stay `UP`

---

## 6. Run the unit suite

```bash
npm test
```

For just the health-related tests:
```bash
npm run test:unit:single -- tests/unit/api/v1.0/services/health-checks.test.ts
npm run test:unit:single -- tests/unit/api/v1.0/services/health.service.test.ts
npm run test:unit:single -- tests/unit/api/v1.0/controllers/probes.controller.test.ts
```

Notable suites:
- `health-checks.test.ts > schema defaults` — asserts the default `healthPath` values from the Zod schema
- `health.service.test.ts > readiness check policy: upstream HTTP deps are /health-only, never /ready` — asserts that even when all 5 upstream deps are configured, the `/ready` registry contains only `mongodb` and `redis`
- `health.service.test.ts > runReadinessChecks() > does not invoke fetch — /ready has no HTTP upstream checks` — defensive test that fails loudly if anything ever causes `/ready` to make an HTTP call

---

## 7. Cleanup

Stop the stack but keep data volumes:
```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml down
```

Stop and wipe volumes (next boot re-imports the realm from JSON and re-seeds MongoDB from env vars):
```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml down -v
```

---

## 8. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `/api/admin/config` returns **401** | `auth.enabled` is true and you're hitting it without a Bearer token | Mint a token (§3a) and pass `Authorization: Bearer <token>`; or set `auth.enabled=false` in MongoDB |
| `/api/admin/config` or `/auth/*` returns **429** | Strict auth rate limiter (`rateLimitAuthMax: 5` per 900s) | `docker compose ... exec redis redis-cli FLUSHALL` — or set higher `rateLimitAuthMax` in MongoDB |
| `keycloak:connectivity = DOWN` after enabling | Issuer is `http://localhost:8081/...` but probe runs inside container; container's `localhost` is itself, not the host | Use the `auth.keycloak.healthUrl` override pointing at `http://keycloak:8080/...` (§5.3), or change `issuer` to container DNS (§5.4) |
| `wsdAuth:connectivity = DOWN` | No VPN to staging | From the host: `curl -I https://staging-authentication.wallstreetdocs.com/api/v2.0/test/ping` — if that fails too, it's network, not WAIF |
| Schema defaults look wrong | Stale MongoDB seed predating the code change | Drop `app_config` (§5.1) and restart waif-server |
| Browser SSO redirects to `http://keycloak:8080/...` and browser shows "site can't be found" | `KC_HOSTNAME` is set to the container-DNS name `keycloak` — the browser can't resolve it | Compose should have `KC_HOSTNAME=localhost` and `KC_HOSTNAME_PORT=8081` — re-check `docker-compose.local.yml` |
| Browser SSO returns to `/auth/login/?error=callback_failed` | The token endpoint URL WAIF derives from `issuer` is unreachable from the container | Set `auth.keycloak.generateTokenUrl` to `http://keycloak:8080/realms/waif-dev/protocol/openid-connect/token` (container DNS) so the code-for-token exchange works |
| APIs return 403 with "Access denied to pipeline 'X'" | User's roles don't include the pipeline-access role (`ROLE_WAIF_Pipeline_<id>`, `ROLE_WAIF_Pipeline_All`, or `ROLE_WAIF_Admin`) | Decode the token (§3a). Verify the user has the **client roles** under `resource_access.waif-api.roles` (WAIF doesn't read realm roles) |
| APIs return 403 with "User does not have access to orgId 1" | Token has no `orgIds` claim, or `orgIds` doesn't include the requested org | Verify the realm JSON has the `orgId` / `orgIds` protocol mappers on the `waif-api` client, and the user has `orgIds: ["1"]` in their attributes |
| `printenv \| grep KEYCLOAK_` inside the container shows comment-like values (e.g. `KEYCLOAK_CLIENT_ID=# Keycloak client ID`) | Compose `env_file:` doesn't strip inline comments from `.env` lines | Either move comments to their own lines in `.env`, or quote the value: `KEY=""  # comment` |
| Token decoded with `cut -d. -f2 \| base64 -d` errors | Base64 needs padding | Pad it: `while [ $((${#PAYLOAD} % 4)) -ne 0 ]; do PAYLOAD="${PAYLOAD}="; done` |
| Tests fail with "Cache not initialized" / "MongoDB not initialized" | The test harness uses real connections | Make sure Mongo + Redis containers are up before running integration tests |

---

## 9. Related references

- `docker/keycloak/README.md` — deeper Keycloak hostname / admin-console / realm-import internals
- `src/api/v1.0/services/health-checks.ts` — probe implementations (`checkMongoDB`, `checkRedis`, `checkLiteLLM`, `checkDigest`, `checkRagas`, `checkKeycloak`, `checkWsdAuth`, `deriveKeycloakHealthUrl`)
- `src/api/v1.0/services/health.service.ts` — `/ready` registration (pod-local only)
- `src/api/v1.0/services/ietf-health.service.ts` — `/health` registration (full picture). The comment block at lines 153-155 spells out why upstream HTTP deps stay off `/ready`.
- `src/config/dynamic-config.schema.ts` — Zod defaults for every config field, including `healthPath` defaults
