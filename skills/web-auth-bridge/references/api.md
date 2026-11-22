# API Reference

## WebAuthBridge

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

## AuthResult

| Field           | Type               | Description                     |
| --------------- | ------------------ | ------------------------------- |
| `cookies`       | `list[CookieData]` | Extracted browser cookies       |
| `local_storage` | `dict[str, str]`   | localStorage entries            |
| `tokens`        | `dict[str, str]`   | Arbitrary token key-value pairs |
| `expires_at`    | `datetime \| None` | When the auth expires           |
| `is_expired`    | `bool` (property)  | Whether auth has expired        |

## Credentials

| Field      | Type             | Description                           |
| ---------- | ---------------- | ------------------------------------- |
| `username` | `str`            | Login username/email                  |
| `password` | `str`            | Login password                        |
| `extra`    | `dict[str, str]` | Additional fields (MFA secrets, etc.) |
