# Intent

Let agent skills and CLI tools authenticate against websites that require browser-based login (WAF, SAML, MFA, ASP.NET sessions), then use their APIs with cached tokens, without re-authenticating on every run.

## Goals

1. A skill CLI can reach a browser-login site with one `ensure_authenticated()` call.
2. Authentication is reused from cache until it expires.
3. Credentials stay out of the agent's hands and out of the cache.

## Requirements

- Use the `web-auth-bridge` library (github.com/mikejhill/web-auth-bridge), installed with uv.
- Per-site `AuthCallback` implementations; headless with stored credentials, headed without.
- Cached results reused through `httpx` clients (sync and async) or parallel browser context pools; `SessionRenewalCallback` for stateful sessions.
- Credential isolation per the skill CLI conventions: the operator creates credential files; only tokens and cookies are cached.
- Out of scope: general HTTP use, Playwright use unrelated to authentication, creating credential files.

## Log

- 2026-11-10: Imported into the SkillSinc library layout. Requirements above are taken from the existing skill.
- 2026-11-22: [agent] Migrated to the `skill-development` standard. `SKILL.md` cut from 326 to about 50 lines; the implementation guide, CLI pattern, and API reference moved to `references/`. `cache_dir` moved from the config folder to the standard cache location (`<user-cache>/agent-skills/<skill>/`), since cached sessions are rebuildable state; existing caches are not migrated, so the first run after the change logs in again. Removed a hard-coded password from the example. Pointers to `skill-cli-development` now go to `skill-development`'s CLI reference, after that merge.
- 2026-11-22: [agent] Codex review fixes on the migration: fixed comma placement in two examples; the Step 2 example runs headed when no credentials exist.
- 2026-11-22: [agent] Removed named references to other skills and instruction files; adjacent concerns are now described by capability ("any ... standards the user has") so the skill stands alone.
