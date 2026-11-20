# Intent

Let any agent take control of the user's own running Chromium browser (Edge, Chrome, Brave)
to complete tasks in it, with their real tabs and logins, at minimum friction. CDP is the
implementation; DevTools-style inspection (cookies, network, emulation) is a feature, not
the purpose.

## Goals

1. One approval per broker run: a long-lived background broker holds the single WebSocket
   across tasks, because the in-browser remote-debugging toggle prompts the user on every
   new connection.
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
- 2026-11-14: [agent] Renamed `browser-devtools` → `browser-control` (script `browser.py`,
  state dir `browser-control`, env `BROWSER_CONTROL_HOME`). Reframed SKILL.md around controlling the browser for tasks;
  CDP moved to a "How it works" note.
- 2026-11-17: [agent] Existing-tab control (user ask: "take over the GitHub tab I have open"
  instead of opening new tabs). Ranked `-t` matching (exact URL > host/URL prefix > URL
  substring > title), `active`, `url:`/`title:` selectors, ambiguity errors listing
  candidates; `which`, `activate`, `close`, `targets --grep/--focus`, `open --reuse`;
  `run -t` pins the tab before steps that navigate. SKILL.md now tells agents to drive a
  tab the user names. Smoke test runs as root (`--no-sandbox`).
- 2026-11-17: [agent] Fixes from the first real run on Edge. `nav` on GitHub always hit the
  15 s timeout: a skeleton placeholder stays visible forever, so settle never passed. Busy
  indicators now count only while new (3 s), and GitHub navs settle in about 3.6 s. `-t active`
  failed with two Edge windows open (neither focused while the user is in another app); it
  now falls back to the tab last brought forward with `activate`.
- 2026-11-20: [agent] Broker lifetime from a timing study of 6 real sessions: 4 broker starts
  waited 32-127 s (405 s total) on the approval prompt, the largest single cost. Idle default
  900 s -> 3600 s, overridable with `BROWSER_CONTROL_IDLE`; `start --idle` also updates a running
  broker. SKILL.md no longer tells agents to `stop` after each task (only when the user is done,
  wants the banner gone, or to switch browsers) and says to start the broker first, in the
  background where possible, so the prompt overlaps planning. Goal 1 changed from "one
  approval per task" to "one approval per broker run" (operator decision). `start --idle`
  rejects values <= 0 and warns when the running broker is too old to update.
