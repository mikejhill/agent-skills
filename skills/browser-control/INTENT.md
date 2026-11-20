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
- 2026-11-20: [agent] Smarter settling, from the same study: ad-heavy retail navs took
  10-26 s because third-party beacons and lazy images kept resetting the quiet window. Only
  same-site document/XHR/fetch/script requests (plus the tab's own document and third-party
  XHR/fetch under 1.5 s old) count as busy; the signature uses completed same-site XHR/fetch
  instead of every resource. `--quiet` 0.5 -> 0.3 s, but 0.5 s after a click/key until
  anything changes (timer-driven UI). New `--settle-max` (5 s, returns `"settle": "capped"`
  with `busy` hosts and a stderr warning), `--for-*` replaces settling unless `--settle`,
  `--strict-settle` keeps the old rules. Simple nav 0.66 -> 0.46 s on the fixture.
- 2026-11-20: [agent] Change summaries: 52 of 147 calls in the study only looked at the page,
  17 right after an action. `click`/`nav`/`key` now return `changes` (added lines, removed
  count, focus, new controls, alerts; capped at 1200 chars), computed in the settle call;
  click snapshots in its existing pick evaluate. `text --changed` diffs against the last
  `text` read. `--summary brief|full|none`, `BROWSER_CONTROL_SUMMARY`; `run` summarizes only
  its last action step. Dialog reporting from the design was left out (needs Page events on
  every tab).
- 2026-11-20: [agent] `extract`: 59 of 88 `eval` calls in the study carried 400+ char inline
  scrapers, and long commands cost ~0.34 s of model time per 100 chars. `extract NAME=SPEC
  [--rows CSS]` covers text, attributes (absolute URLs), `::all`, `::count` and `::html`, with
  `missing` counts, an 8000-char cap, `--format tsv`, and candidate containers when `--rows`
  matches nothing. One evaluate, no broker change.
- 2026-11-20: [agent] `run` refinements (modest win: agents already chain with `;`, and
  batching hides intermediate state). `--echo last` (default) prints one line per passing
  step and full output for a failing or last step; `--echo all` is the old output.
  `--expect-text`/`--expect-selector`/`--expect-url` on click/nav/key/wait fail the step
  (exit 1) when unmet, so a wrong click stops a batch. SKILL.md: one call per page
  transition, batch only predictable steps, never past a submit the user must confirm.
- 2026-11-20: [agent] Hidden tabs, found testing on local Edge: a tab in a covered,
  minimized or background window is "hidden", so timers throttle to 1/s or slower (settle
  declared quiet mid-chain; waits overran) and mouse clicks took ~5 s or were dropped. The
  broker now turns on focus emulation for each tab it attaches to, so driven tabs act
  visible and focused; `active`/`--focus` probes switch it off briefly to read the real
  state. Smoke test: UTF-8 subprocess output and full process-tree teardown on Windows.
