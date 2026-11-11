---
name: web-auth-bridge
description: "Use when building CLI tools or agent skills that need to authenticate against external websites protected by WAF, SAML, MFA, or complex browser-based login flows. Provides browser-based authentication via Playwright, token caching, httpx client injection, and parallel browser context pooling."
---

# Web Auth Bridge

## Objective

Enable agent skills and CLI tools to authenticate against external websites that require browser-based login flows (Cloudflare WAF, SAML, MFA, ASP.NET sessions) and then interact with their APIs using cached tokens — without re-authenticating on every execution.

## Scope

**In-scope:**

- Implementing `AuthCallback` classes that drive site-specific login flows
- Configuring `WebAuthBridge` for headless or headed authentication
- Using cached authentication results with `httpx` clients
- Spinning up parallel browser contexts for sites requiring continued browser interaction
- Implementing `SessionRenewalCallback` for stateful session management
- Integrating web-auth-bridge into skill CLIs

**Out-of-scope:**

- General HTTP client usage without browser authentication
- Playwright usage unrelated to authentication
- Credential file creation (operator responsibility per skill-cli-development)

## Library Location

The library is published at <https://github.com/mikejhill/web-auth-bridge> and is installed via:

```bash
uv add "web-auth-bridge @ git+https://github.com/mikejhill/web-auth-bridge"
```

Or from a skill CLI's `pyproject.toml`:

```toml
[project]
dependencies = ["web-auth-bridge"]

[tool.uv.sources]
web-auth-bridge = { git = "https://github.com/mikejhill/web-auth-bridge" }
```

For local development against a checkout, use `uv add --editable <path-to-web-auth-bridge>`.

## Core Concepts

### Architecture

```text
┌─────────────────────────────────────────────────────┐
│                   WebAuthBridge                     │
│  (facade: ties auth, cache, HTTP client, pool)      │
├──────────────┬──────────────┬───────────────────────┤
│ Authenticator│  AuthCache   │  BrowserContextPool   │
│ (browser +   │ (file-backed │ (N parallel contexts  │
│  callback)   │  persistence)│  with cloned cookies) │
├──────────────┴──────────────┴───────────────────────┤
│              BrowserManager (Playwright)            │
└─────────────────────────────────────────────────────┘
```

### Flow

1. **Auth stage**: Playwright browser runs consumer's `AuthCallback` → cookies/tokens extracted
2. **Cache stage**: `AuthResult` persisted to disk (file permissions `600`)
3. **API stage** (choose one):
   - **HTTP only**: `httpx.AsyncClient` or `httpx.Client` with cookies pre-injected
   - **Browser pool**: N parallel `BrowserContext` instances with cookies cloned in

### Key Classes

| Class                    | Import            | Purpose                                              |
| ------------------------ | ----------------- | ---------------------------------------------------- |
| `WebAuthBridge`          | `web_auth_bridge` | Main facade — authenticate, get clients, manage pool |
| `AuthResult`             | `web_auth_bridge` | Cookies, tokens, localStorage from auth              |
| `CookieData`             | `web_auth_bridge` | Single cookie with Playwright dict conversion        |
| `Credentials`            | `web_auth_bridge` | Username/password/extra for headless auth            |
| `AuthCallback`           | `web_auth_bridge` | Protocol: consumer implements `authenticate()`       |
| `SessionRenewalCallback` | `web_auth_bridge` | Protocol: per-context session renewal                |
| `StealthConfig`          | `web_auth_bridge` | Anti-detection settings (user-agent, viewport)       |

## Implementation Guide

### Step 1: Implement AuthCallback

Every target website needs its own `AuthCallback`. This is where the site-specific login logic lives.

```python
from web_auth_bridge import AuthCallback, AuthResult, CookieData, Credentials

from playwright.async_api import Page


class MyServiceAuth:
    """Drive login for my-service.example.com."""

    async def authenticate(self, page: Page, credentials: Credentials | None) -> AuthResult:
        await page.goto("https://my-service.example.com/login")

        if credentials:
            await page.fill("#username", credentials.username)
            await page.fill("#password", credentials.password)
            await page.click("#submit")
        else:
            # Manual entry: wait for user to complete login
            await page.wait_for_url("**/dashboard**", timeout=120_000)

        await page.wait_for_load_state("networkidle")

        # Extract cookies from the browser context
        cookies = await page.context.cookies()
        return AuthResult(
            cookies=[CookieData.from_playwright_dict(dict(c)) for c in cookies],
            tokens={"csrf": await page.evaluate("() => document.querySelector('meta[name=csrf]')?.content || ''")},
        )

    async def is_authenticated(self, auth_result: AuthResult) -> bool:
        return not auth_result.is_expired
```

### Step 2: Configure and Use WebAuthBridge

```python
import asyncio
from pathlib import Path

from web_auth_bridge import WebAuthBridge, Credentials


async def main() -> None:
    bridge = WebAuthBridge(
        auth_callback=MyServiceAuth(),
        cache_dir=Path("~/.config/copilot-skills/my-skill/cache"),
        credentials=Credentials(username="user@example.com", password="secret"),
        headless=True,
    )

    # Authenticate (uses cache if valid)
    result = await bridge.ensure_authenticated()

    # Option A: HTTP API calls (no browser needed)
    async with bridge.http_client() as client:
        resp = await client.get("https://my-service.example.com/api/data")
        print(resp.json())

    # Option B: Sync HTTP client
    with bridge.http_client_sync() as client:
        resp = client.get("https://my-service.example.com/api/data")
        print(resp.json())

    # Option C: Parallel browser contexts (for sites requiring browser)
    async with bridge.browser_pool(count=4) as contexts:
        pages = [await ctx.new_page() for ctx in contexts]
        for page in pages:
            await page.goto("https://my-service.example.com/reports")
            # ... scrape or interact

asyncio.run(main())
```

### Step 3: Handle Stateful Sessions (Optional)

For sites with stateful server-side sessions (ASP.NET, etc.), implement `SessionRenewalCallback`:

```python
from web_auth_bridge import SessionRenewalCallback

from playwright.async_api import BrowserContext, Page


class AspNetSessionRenewal:
    async def renew(
        self,
        context: BrowserContext,
        page: Page,
        auth_cookies: list[dict[str, object]],
    ) -> None:
        await page.goto("https://portal.example.com/session/init")
        await page.wait_for_load_state("networkidle")
        # Server sets a unique ASP.NET_SessionId cookie automatically


# Use it:
async with bridge.browser_pool(count=4, session_renewal=AspNetSessionRenewal()) as contexts:
    ...
```

### Step 4: Headed Mode for Manual Auth

When credentials cannot be stored or the flow requires visual interaction:

```python
bridge = WebAuthBridge(
    auth_callback=MyServiceAuth(),
    cache_dir=Path("~/.config/copilot-skills/my-skill/cache"),
    credentials=None,  # No stored credentials
    headless=False,     # User sees the browser
)
```

## Integration with Skill CLIs

When building a skill CLI that uses web-auth-bridge, follow this pattern:

```python
"""CLI for my-skill that authenticates via web-auth-bridge."""

import argparse
import asyncio
import sys
from pathlib import Path

from web_auth_bridge import WebAuthBridge, Credentials


def _load_credentials(config_dir: Path) -> Credentials | None:
    creds_file = config_dir / "credentials.toml"
    if not creds_file.exists():
        return None
    import tomllib
    data = tomllib.loads(creds_file.read_text())
    return Credentials(
        username=data["username"],
        password=data["password"],
    )


async def _run(args: argparse.Namespace) -> None:
    config_dir = Path("~/.config/copilot-skills/my-skill").expanduser()
    credentials = _load_credentials(config_dir)

    bridge = WebAuthBridge(
        auth_callback=MyServiceAuth(),
        cache_dir=config_dir / "cache",
        credentials=credentials,
        headless=credentials is not None,  # Headed if no stored creds
    )

    await bridge.ensure_authenticated()

    async with bridge.http_client() as client:
        resp = await client.get("https://api.example.com/data")
        print(resp.text)


def main() -> None:
    parser = argparse.ArgumentParser(description="My skill CLI")
    args = parser.parse_args()
    asyncio.run(_run(args))
```

## API Reference

### WebAuthBridge

```python
WebAuthBridge(
    *,
    auth_callback: AuthCallback,
    cache_dir: Path,
    credentials: Credentials | None = None,
    headless: bool = True,
    browser_type: str = "chromium",
    stealth: StealthConfig | None = None,
    launch_kwargs: dict[str, Any] | None = None,
)
```

**Methods:**

| Method                                    | Returns                                     | Description                           |
| ----------------------------------------- | ------------------------------------------- | ------------------------------------- |
| `await ensure_authenticated()`            | `AuthResult`                                | Auth if needed, return valid result   |
| `await force_authenticate()`              | `AuthResult`                                | Force fresh auth, ignore cache        |
| `http_client(**kwargs)`                   | `httpx.AsyncClient`                         | Async HTTP client with auth cookies   |
| `http_client_sync(**kwargs)`              | `httpx.Client`                              | Sync HTTP client with auth cookies    |
| `cookies()`                               | `list[dict]`                                | Raw cookies as Playwright dicts       |
| `tokens()`                                | `dict[str, str]`                            | Token key-value pairs                 |
| `browser_pool(count, *, session_renewal)` | `AsyncContextManager[list[BrowserContext]]` | Parallel browser contexts             |
| `invalidate_cache()`                      | `None`                                      | Delete cache, force re-auth next time |

### AuthResult

| Field           | Type               | Description                     |
| --------------- | ------------------ | ------------------------------- |
| `cookies`       | `list[CookieData]` | Extracted browser cookies       |
| `local_storage` | `dict[str, str]`   | localStorage entries            |
| `tokens`        | `dict[str, str]`   | Arbitrary token key-value pairs |
| `expires_at`    | `datetime \| None` | When the auth expires           |
| `is_expired`    | `bool` (property)  | Whether auth has expired        |

### Credentials

| Field      | Type             | Description                           |
| ---------- | ---------------- | ------------------------------------- |
| `username` | `str`            | Login username/email                  |
| `password` | `str`            | Login password                        |
| `extra`    | `dict[str, str]` | Additional fields (MFA secrets, etc.) |

## Constraints

**MUST:**

- Implement `AuthCallback` for each target website
- Use `cache_dir` under the consuming skill's config directory
- Set `headless=False` when credentials are not stored (manual entry)
- Handle `AuthError` exceptions from `ensure_authenticated()`
- Follow skill-cli-development credential isolation rules

**MUST NOT:**

- Store credentials in the auth cache (only tokens/cookies are cached)
- Share browser contexts across asyncio tasks (Playwright limitation)
- Use web-auth-bridge for sites with simple API key authentication
- Hardcode credentials in `AuthCallback` implementations

**MAY:**

- Use `StealthConfig` to customize anti-detection settings per site
- Implement `is_authenticated()` with an active API check instead of expiry-based
- Pass `launch_kwargs` for site-specific browser configuration (e.g., proxy)
- Use `force_authenticate()` to bypass cache during debugging
