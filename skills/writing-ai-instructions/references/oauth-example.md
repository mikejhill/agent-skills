# Complete Example: OAuth Implementation Plan (Agent Skill)

This example demonstrates the full 8-section template applied to a single
domain. The three input/output variants show graduated complexity (staging →
production → edge-case integration), demonstrating the few-shot strategy within
an instruction set.

**Objective:** Produce a step-by-step implementation plan for adding OAuth
login to an existing Node.js API.

**Scope:**

In-scope:

- Authentication flow for selected OAuth provider
- Required endpoints and route definitions
- Token storage and retrieval strategy
- Environment configuration and secrets management

Out-of-scope:

- UI/frontend changes
- Database migrations beyond token storage table
- Multi-provider OAuth support (one provider only)
- Refresh token rotation

**Inputs:**

Required:

- Repository path or GitHub URL
- Existing authentication middleware (code snippet or file name)
- Target OAuth provider (GitHub, Google, or Okta)

Optional:

- Preferred OAuth library (will suggest default if omitted)
- Target deployment environment (assumes staging if omitted)

Assumptions:

- Project uses Express.js
- Secrets are managed via environment variables (not hardcoded)
- PostgreSQL or similar for persistent token storage

**Outputs:**

Format: Markdown document titled "OAuth Implementation Plan"

Required sections:

- Overview (one paragraph)
- Endpoints (table with method, path, and purpose)
- Token storage (design, TTL, encryption)
- Configuration (environment variables and either sample .env or secrets
  manager notes)
- Implementation steps (numbered, with file names)
- Testing plan (unit and integration tests)
- Rollback strategy

**Constraints:**

- MUST NOT edit files; only provide code snippets and file changes.
- MUST NOT run commands; only provide shell commands that could be run.
- MUST reuse existing auth patterns in the codebase when applicable.
- MUST include security justification for token storage decisions.
- MUST specify all environment variables needed for the provider.

If constraints conflict, resolve in this order: security justification >
codebase reuse > variable completeness.

**Procedure:**

1. Read existing auth modules and identify extension points.
2. If an OAuth library is already in package.json, plan around that library;
   otherwise recommend one.
3. Identify the selected provider's endpoint URLs and required scopes.
4. Design token storage: table schema, TTL, and encrypted column strategy.
5. List all required environment variables and document their values (without
   secrets).
6. Write numbered implementation steps, naming specific files and functions.
7. Outline unit tests for token exchange and integration tests for the full
   flow.
8. Include a rollback plan (what to delete, what to revert).

**Validation:**

Pass conditions:

- Plan includes at least 5 implementation steps.
- All environment variables are listed and documented.
- Token storage design includes TTL and encryption strategy.
- Rollback plan is explicit and reversible.
- Testing plan covers both happy path and OAuth error responses.

Failure conditions:

- Plan does not include endpoint definitions.
- Plan does not specify the storage strategy.
- Plan does not list required environment variables.
- Rollback plan is missing or vague.

**Personas:**

Persona: Security-hardened backend architect with 7 years defending OAuth
implementations

You are paranoid about token exfiltration and treat every storage mechanism as
potentially compromised until cryptographically proven otherwise. You approach
all design decisions by asking "How does an attacker steal this?" and "What
forensic trail do we leave?" before addressing performance or convenience.

When facing tradeoffs between encryption overhead and feature velocity, you
choose hardening every time. You distrust in-memory caches and convenience but
trust hardware-backed key storage and immutable audit logs. You demand explicit
threat justification for every decision that touches credentials.

Persona details (years, titles) are illustrative; adapt them to the task.

**Examples:**

This section demonstrates few-shot prompting: each example shows complete input
and corresponding output so the agent learns the expected structure through
demonstration.

Example 1: Staging environment, existing Basic auth, GitHub provider

INPUT:

- Repository: github.com/company/api-service
- Existing auth: Basic auth middleware in routes/auth/basic.js
- Provider: GitHub
- Environment: staging (non-production)

OUTPUT:

````markdown
# OAuth Implementation Plan: GitHub

## Overview

Add GitHub OAuth to replace Basic auth in staging environment. GitHub provides
delegated authentication, reducing credential exposure. Staging environment
permits simplified token storage (in-memory cache with persistence).

## Endpoints

| Method | Path                 | Purpose                  |
| ------ | -------------------- | ------------------------ |
| GET    | /auth/login/github   | Initiate OAuth flow      |
| GET    | /auth/oauth/callback | GitHub callback receiver |
| POST   | /auth/logout         | Clear session and revoke |

## Token Storage

- **Table**: `oauth_sessions` (new)
- **Columns**:
  - `user_id` (foreign key to users)
  - `provider` (text: "github")
  - `access_token` (text, encrypted)
  - `expires_at` (timestamp)
- **TTL**: 1 hour (auto-cleanup via scheduled job)
- **Encryption**: AES-256-GCM with `GITHUB_TOKEN_KEY` from environment
- **Rationale**: Staging environment; production-grade encryption not required,
  but encrypted at rest follows principle-of-least-surprise

## Environment Variables

Required in .env:

```bash
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
GITHUB_CALLBACK_URL='http://localhost:3000/auth/oauth/callback'
GITHUB_TOKEN_KEY=32-byte-base64-encoded-key
```

## Implementation Steps

1. Create oauth_sessions table:
   `migrations/20260203_create_oauth_sessions.sql`
2. Install library: `npm install passport-github2`
3. Create GitHub strategy: `lib/auth/github-strategy.js`
4. Add OAuth routes: `routes/auth/github.js`
5. Update middleware stack in app.js to use Passport authentication
6. Replace Basic auth header validation with Passport session check
7. Add .env.example with required variables (no secrets)

## Testing Plan

- Unit: Token encryption/decryption works with `GITHUB_TOKEN_KEY`
- Integration: GET /auth/login/github → redirect to GitHub → callback →
  session created → user authenticated
- Error: Invalid callback code → 401 response
- Error: Missing `GITHUB_CLIENT_SECRET` → startup fails with clear error

## Rollback Plan

If OAuth causes issues:

1. Restore routes/auth/basic.js from git
2. Revert app.js middleware changes
3. Delete oauth_sessions table: `DROP TABLE oauth_sessions;`
4. Redeploy previous version
````

Example 2: Production environment, no existing auth, Google provider
(conservative approach)

INPUT:

- Repository: internal-tools (private)
- Existing auth: None
- Provider: Google
- Environment: production (must be hardened)

OUTPUT:

````markdown
# OAuth Implementation Plan: Google

## Overview

Implement Google OAuth as primary authentication for internal tools. Production
environment requires encrypted token storage, audit logging, and rate limiting.

## Endpoints

| Method | Path                 | Purpose                           |
| ------ | -------------------- | --------------------------------- |
| GET    | /auth/login/google   | Initiate OAuth flow               |
| GET    | /auth/oauth/callback | Google callback receiver          |
| POST   | /auth/logout         | Revoke token and clear session    |
| GET    | /auth/status         | Check current session (debugging) |

## Token Storage

- **Table**: oauth_tokens (production-hardened)
- **Columns**:
  - `id` (UUID primary key)
  - `user_id` (foreign key, with audit logging on access)
  - `provider` (enum: "google")
  - `access_token` (encrypted with rotating key)
  - `refresh_token` (encrypted, stored separately from access_token)
  - `token_expires_at` (timestamp)
  - `last_accessed` (timestamp, updated on each request)
  - `created_at`, `updated_at` (for audit trail)
- **TTL**: None (user revocation model; manually deleted on logout)
- **Encryption**: AES-256-GCM with key from AWS KMS (not environment variable)
- **Audit**: Log all token access (not content, only timestamp/user/action) to
  separate `audit_log` table

## Environment Variables

Required in production secrets manager:

```bash
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_CALLBACK_URL='https://internal-tools.company.com/auth/oauth/callback'
GOOGLE_DISCOVERY_URL='https://accounts.google.com/.well-known/openid-configuration'
KMS_KEY_ID=arn:aws:kms:us-east-1:123456:key/...
RATE_LIMIT_TOKENS=10
RATE_LIMIT_WINDOW_MINUTES=1
```

## Implementation Steps

1. Create `oauth_tokens` table (with encryption column support):
   `migrations/20260203_oauth_tokens.sql`
2. Create `audit_log` table for token access:
   `migrations/20260203_audit_log.sql`
3. Install libraries: `npm install passport-google-oauth20 aws-sdk`
4. Create Google strategy with discovery: `lib/auth/google-strategy.js`
5. Create token encryption utility: `lib/auth/token-cipher.js` (uses KMS for
   key rotation)
6. Create rate limiter middleware: `middleware/rate-limit-oauth.js`
7. Add OAuth routes with audit logging: `routes/auth/google.js`
8. Add audit logging on every token access: middleware in auth check
9. Wire Passport into Express, replacing any existing session handling

## Testing Plan

- Unit: Token encryption with KMS key rotation works
- Unit: Rate limiter blocks after 10 requests/minute
- Integration: GET /auth/login/google → redirect → callback → token stored
  encrypted → user session created
- Integration: Token access logged to `audit_log` table
- Error: Invalid `GOOGLE_CLIENT_SECRET` → startup fails immediately
- Error: KMS key unavailable → 503 Service Unavailable (not 500 Internal Error)
- Error: Rate limit exceeded → 429 Too Many Requests

## Rollback Plan

If OAuth must be disabled:

1. Set `GOOGLE_CLIENT_ID` to empty string (disables all Google routes)
2. Revert to previous auth method (or maintenance mode)
3. DO NOT delete `oauth_tokens` or `audit_log` (retain for forensics)
4. Export `oauth_tokens` and `audit_log` to S3 backup
5. Notify security team of rollback and audit log status
````

Example 3: Edge case—Okta with existing JWT token strategy (multi-tenant,
complex)

INPUT:

- Repository: internal-api (existing Express with JWT middleware)
- Existing auth: JWT bearer tokens in Authorization header
- Provider: Okta
- Environment: production (must integrate with existing JWT flow)

OUTPUT:

````markdown
# OAuth Implementation Plan: Okta

## Overview

Integrate Okta as OAuth provider without breaking existing JWT token flow. Okta
will issue JWT tokens; application continues to validate existing JWT schema.
This enables gradual migration from custom auth to Okta-managed auth.

## Endpoints

| Method | Path                 | Purpose                             |
| ------ | -------------------- | ----------------------------------- |
| GET    | /auth/login/okta     | Initiate Okta OAuth flow            |
| GET    | /auth/oauth/callback | Okta callback receiver              |
| POST   | /auth/logout         | Revoke Okta token and clear session |
| GET    | /auth/discovery      | Okta OIDC discovery endpoint        |

## Token Storage

- **Table**: `oauth_sessions` (minimal; Okta tokens live in Okta, not our
  database)
- **Columns**:
  - `user_id`
  - `provider` (text: "okta")
  - `okta_user_id` (external reference)
  - `refresh_token` (encrypted, short-lived)
  - `session_created_at`
- **TTL**: 30 minutes (sessions only; Okta manages token lifetime)
- **Encryption**: AES-256-GCM (refresh token only; access tokens validated
  server-side only)
- **Rationale**: Okta as authority; we validate tokens, not store them. Reduce
  token storage attack surface.

## Environment Variables

Required:

```bash
OKTA_DOMAIN=company.okta.com
OKTA_CLIENT_ID=your-client-id
OKTA_CLIENT_SECRET=your-client-secret
OKTA_CALLBACK_URL='https://api.company.com/auth/oauth/callback'
OKTA_DISCOVERY_URL='https://company.okta.com/.well-known/openid-configuration'
```

## Implementation Steps

1. Create `oauth_sessions` table (minimal schema):
   `migrations/20260203_oauth_sessions.sql`
2. Install: `npm install @okta/okta-sdk-nodejs passport-openidconnect`
3. Create Okta OIDC strategy: `lib/auth/okta-oidc-strategy.js`
4. Create token validator (validates Okta-issued tokens):
   `lib/auth/okta-token-validator.js`
5. Update JWT middleware to accept Okta-issued JWTs:
   `middleware/jwt-validator.js`
6. Add Okta OAuth routes: `routes/auth/okta.js`
7. Add discovery endpoint that returns Okta's OIDC metadata:
   `routes/auth/discovery.js`
8. Test existing JWT tokens still work (backward compatibility)

## Testing Plan

- Unit: Token validator accepts valid Okta JWTs
- Unit: Token validator rejects expired tokens
- Integration: Existing JWT tokens continue to authenticate
- Integration: GET /auth/login/okta → redirect to Okta → callback → Okta JWT
  validated → session created
- Integration: /auth/discovery returns Okta's OIDC metadata
- Error: Okta issues token but secret invalid → 401 Unauthorized
- Error: Okta unreachable (network failure) → 503 Service Unavailable, session
  stale
- Compatibility: Old app clients using JWT still work (no breaking change)

## Rollback Plan

If Okta integration must be removed:

1. Comment out Okta routes in routes/auth/okta.js
2. Remove Okta token validator from JWT middleware (revert to old logic)
3. Okta sessions and tokens become orphaned but harmless
4. Existing JWT tokens continue to work (backward compatible)
5. No database changes needed (`oauth_sessions` just unused)
````
