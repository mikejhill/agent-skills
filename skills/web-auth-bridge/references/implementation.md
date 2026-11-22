# Implementation guide

`config_root()` and `user_cache()` stand for the standard config and cache locations. Ignore relative values of `XDG_CONFIG_HOME`, `XDG_CACHE_HOME`, and `LOCALAPPDATA`. The cache base is `%LOCALAPPDATA%` on Windows (or `%USERPROFILE%\AppData\Local` when it is unset or relative), `~/Library/Caches` on macOS, and `${XDG_CACHE_HOME:-~/.cache}` elsewhere: `${XDG_CONFIG_HOME:-~/.config}/agent-skills/<skill>/` and `<user-cache>/agent-skills/<skill>/`.

## Step 1: Implement AuthCallback

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

## Step 2: Configure and Use WebAuthBridge

```python
import asyncio
from pathlib import Path

from web_auth_bridge import WebAuthBridge, Credentials


async def main() -> None:
    credentials = _load_credentials(config_root("my-skill"))  # never hard-code
    bridge = WebAuthBridge(
        auth_callback=MyServiceAuth(),
        cache_dir=user_cache("my-skill"),  # see SKILL.md
        credentials=credentials,
        headless=credentials is not None,  # headed so a person can log in
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

## Step 3: Handle Stateful Sessions (Optional)

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

## Step 4: Headed Mode for Manual Auth

When credentials cannot be stored or the flow requires visual interaction:

```python
bridge = WebAuthBridge(
    auth_callback=MyServiceAuth(),
    cache_dir=user_cache("my-skill"),  # see SKILL.md
    credentials=None,  # No stored credentials
    headless=False,     # User sees the browser
)
```

## Skill CLI pattern

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
    config_dir = config_root("my-skill")      # ${XDG_CONFIG_HOME:-~/.config}/agent-skills/my-skill
    credentials = _load_credentials(config_dir)

    bridge = WebAuthBridge(
        auth_callback=MyServiceAuth(),
        cache_dir=user_cache("my-skill"),     # <user-cache>/agent-skills/my-skill
        credentials=credentials,
        headless=credentials is not None,  # Headed if no stored creds
    )

    await bridge.ensure_authenticated()

    async with bridge.http_client() as client:
        resp = await client.get("https://api.example.com/data")
        sys.stdout.write(resp.text)


def main() -> None:
    parser = argparse.ArgumentParser(description="My skill CLI")
    args = parser.parse_args()
    asyncio.run(_run(args))
```
