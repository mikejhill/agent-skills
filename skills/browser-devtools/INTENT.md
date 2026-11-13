# Intent

Let any agent drive the user's own running Chromium browser (Edge, Chrome, Brave) through
the Chrome DevTools Protocol, with their real tabs and logins, at minimum friction.

## Goals

1. One approval per task: a background broker holds the single WebSocket, because the
   in-browser remote-debugging toggle prompts the user on every new connection.
2. Invisible and self-cleaning: the broker is windowless on Windows and exits on `stop`,
   idle timeout, or browser disconnect.
3. Full protocol reach: raw `send` passes any CDP method through; convenience verbs
   (`eval`, `nav`, `click`, `type`, `key`, `screenshot`, `pdf`, `events`) cover common work.
4. Guide the user when debugging is off (`edge://inspect/#remote-debugging`,
   `chrome://inspect/#remote-debugging`); never relaunch their browser.
5. Zero dependencies: one stdlib-only Python file, cross-platform.
6. Safe by default: real browser, so read-first, confirm side effects, never leak cookies.

## Log

- 2026-11-10: [agent] Created skill (as `cdp`, renamed `browser-devtools` same day): devtools.py (minimal RFC 6455 client, token-protected
  localhost broker, flat-session target attach, event buffer), SKILL.md, recipes and
  troubleshooting references. Verified on headless Chromium and on Edge (Windows) in
  toggle mode: one prompt per broker, pythonw with no window, `/json/*` returns 404.
- 2026-11-13: [agent] Speed pass from a real run (8 min of SPA navigation on a shadow-DOM
  enterprise SPA: 39 tool calls, 108 CLI invocations, 145 s of fixed sleeps, helpers
  re-injected 17 times). Added settle-waits in the broker (in-flight network + spinner +
  text stability) on `click`/`nav`/`wait`, shadow-DOM-piercing `text` and `click --text`,
  `run` for multi-step calls, `net`/`body` for XHR JSON, an always-present `__dt` helper
  library in `eval`, compact JSON by default, string-safe `*Id` params, hash-route `nav`,
  and a broker/endpoint mismatch guard. Added `tests/smoke_test.py` with a fixture SPA.
