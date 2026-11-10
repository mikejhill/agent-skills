---
name: browser-devtools
description: Drive the user's own running Chrome, Edge or Brave through the Chrome DevTools Protocol (CDP), using their real tabs, logins and cookies. Use for reading or automating pages in the user's browser, running JS in a tab, screenshots, capturing network or console traffic, cookies, emulation, or any raw CDP method. Keeps one approved WebSocket in a windowless background broker.
---

# Browser DevTools: drive the user's browser

`scripts/devtools.py` (Python 3.8+, stdlib only) is a thin CLI over a **broker**: a windowless
background process holding the **one** WebSocket to the browser. The browser asks the user
to approve each new debugging connection, so one broker = one approval for the whole task.
Every CLI call reuses it. The broker exits on `stop`, after 15 idle minutes, or when the
browser closes.

```
python scripts/devtools.py <command> ...        # Windows: python or py -3; else python3
```

Paths below are relative to this skill's directory. Output is JSON on stdout; errors go to
stderr with exit code 2 (3 = remote debugging not enabled).

## Workflow

1. **Check:** `devtools.py status`.
   - `endpoints` empty → remote debugging is off. Tell the user to open
     `edge://inspect/#remote-debugging` (Edge) or `chrome://inspect/#remote-debugging`
     (Chrome) and turn on **Allow remote debugging for this browser instance**. No restart
     needed. `devtools.py enable-help --launch edge|chrome` opens that page for them.
     Agents cannot toggle it; never try to relaunch the user's browser with flags.
   - Several endpoints → pass `--browser edge|chrome|brave|...` on every call.
2. **Warn, then start:** tell the user *"Your browser will ask to allow remote debugging;
   click Allow"*, then run `devtools.py start`. It blocks (up to 120 s) until they approve.
   Any command auto-starts the broker, but start explicitly so the prompt is expected.
3. **Work:** `targets` → pick a tab → `eval` / `nav` / `send` / `events` with `-t`.
4. **Stop:** `devtools.py stop` when the task is done, including after errors. Don't leave it to
   the idle timeout. Stopping removes the browser's "being debugged" banner.

## Commands

| Command | Does |
|---|---|
| `status` | Detected endpoints + broker state (never prompts) |
| `start [--idle SEC]` / `stop` | Start / stop broker |
| `targets [--all]` | Tabs: `id`, `title`, `url` (`--all` adds workers, iframes, extensions) |
| `open URL [--background]` | New tab → `targetId` |
| `nav URL -t T [--no-wait]` | Navigate, wait for `load` |
| `eval EXPR -t T` | Run JS; returns JSON value. Top-level `await`, `let` OK; `@file.js` or `-` (stdin) |
| `click SELECTOR -t T [--count 2]` | Trusted mouse click at element center (scrolls into view) |
| `type TEXT -t T [-s SELECTOR] [--replace]` | Trusted text input into focused / selected element |
| `key KEY... -t T` | `Enter`, `Tab`, `Escape`, `ArrowDown`, `ctrl+a`, `x`, ... |
| `screenshot FILE -t T [--full]` | PNG/JPEG (by extension); `--full` = whole page |
| `pdf FILE -t T [-p k=v]` | Print to PDF |
| `send METHOD [JSON] [-p k=v ...] [-t T]` | **Any** CDP method. Prints `result` |
| `events [-t T] [-f PREFIXES] [--since N] [--wait S] [--count N]` | Buffered events (last 5000) |
| `mark` | Current `last_seq`, for `events --since` |
| `batch FILE\|- [-t T]` | JSON lines `{"method","params","target"}` in one call |

**Target (`-t`)**: full targetId, unique id prefix, or a case-insensitive substring of the
tab's URL or title (`-t github`). Ambiguous matches error with candidates. Omit `-t` only
for browser-level domains (`Target.*`, `Browser.*`, `Storage.*`, `SystemInfo.*`).
The broker attaches to each tab once and reuses the session.

**Params**: `-p` avoids shell-quoting JSON (PowerShell mangles inline JSON). Values parse
as JSON when possible, dotted keys nest:
`send Emulation.setDeviceMetricsOverride -p width=390 -p height=844 -p deviceScaleFactor=3 -p mobile=true -t T`.
Complex params: write a `.json` file and pass `@params.json`.

## Rules

- **It's the user's real browser.** Prefer read-only work. Ask before submitting forms,
  purchasing, sending messages, deleting, or changing settings. Prefer `open` for a new
  tab over navigating a tab the user is using; close tabs you opened
  (`send Target.closeTarget -p targetId=ID`).
- **Never print or store cookies, tokens or passwords** unless the user asked for them.
- Domains emit events only after `X.enable` on that tab (`Network.enable`, `Page.enable`,
  `Runtime.enable`, `Log.enable`). Enables and the event buffer live in the broker: a
  restarted broker needs them again.
- Wait for an action's events race-free: `mark` → trigger → `events --since <mark> -f ... --wait 10 --count 1`.
- Interact with `click` / `type` / `key` (real input events; work with React and
  `isTrusted` checks). Read with `eval`. Details: `references/recipes.md`.
- Large outputs: filter in JS (`eval`) rather than dumping whole DOMs/event logs.
- Unknown method or params: check <https://chromedevtools.github.io/devtools-protocol/>
  (tip-of-tree). Errors come back as `CDP error -32601/-32602 ...`.

## References

- `references/recipes.md`: clicking/typing, waiting, network/console capture, cookies,
  PDF, emulation, downloads, file upload, iframes.
- `references/troubleshooting.md`: detection, approval prompt, stale broker, logs,
  launching a separate debug browser.
