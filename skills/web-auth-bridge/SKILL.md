---
name: web-auth-bridge
description: >-
  Authenticate skill CLIs against websites behind WAF, SAML, MFA, or other
  browser-only logins using the web-auth-bridge Python library: Playwright
  login callbacks, token caching, httpx clients, and parallel browser contexts.
  Use when a skill or CLI must call such a site.
---

# Web auth bridge

Log in once through a real browser, cache the cookies and tokens, then call the site's APIs with `httpx` or a pool of authenticated browser contexts, without logging in on every run.

## Install

```bash
uv add "web-auth-bridge @ git+https://github.com/mikejhill/web-auth-bridge"
```

For a checkout under development: `uv add --editable <path>`. Playwright needs a browser: `uv run playwright install chromium`.

## Flow

1. **Auth:** Playwright runs your `AuthCallback`, which drives the site's login and returns an `AuthResult` (cookies, tokens, localStorage).
2. **Cache:** the result is saved under `cache_dir` with owner-only permissions and reused until it expires.
3. **Use:** `bridge.http_client()` (async) or `http_client_sync()` gives an `httpx` client with cookies injected. `bridge.browser_pool(count=N)` gives N contexts with cookies cloned, for sites that need a browser throughout.

## Rules

- Write one `AuthCallback` per site, implementing `authenticate(page, credentials)` and `is_authenticated(result)`.
- Put `cache_dir` in the skill's cache location, `<user-cache>/agent-skills/<skill-name>/`.
- Load credentials inside the CLI from `${XDG_CONFIG_HOME:-~/.config}/agent-skills/<skill-name>/credentials.toml`. Never hard-code them; the user creates that file, and the agent never reads or writes it.
- With no stored credentials, run headed (`headless=False`) so the user can log in by hand.
- Catch `AuthError` from `ensure_authenticated()` and report it with a fix.
- Only tokens and cookies are cached, never credentials.
- Never share a browser context across asyncio tasks.
- For sites with server-side sessions (such as ASP.NET), pass a `SessionRenewalCallback` to `browser_pool`.
- Do not use this library for sites with plain API-key auth.
- `StealthConfig`, `launch_kwargs` (for example a proxy), an active-check `is_authenticated`, and `force_authenticate()` for debugging are available when needed.

Wrap it in a CLI that reads credentials itself and returns only results. The agent never reads, writes, or quotes credential files. Credential files are owner-only: mode `600` on Unix, an ACL limited to the current user on Windows.

## References

- [implementation.md](references/implementation.md): read when writing an `AuthCallback`, configuring the bridge, handling stateful sessions or headed login, or wiring it into a skill CLI.
- [api.md](references/api.md): read for constructor arguments, methods, and data classes.
