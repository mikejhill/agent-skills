---
name: browser-control
description: Take control of the user's own running browser (Chrome, Edge, Brave) to do tasks in it with their real tabs, logins and sessions. Use whenever a task needs the user's browser - reading or extracting from pages they are signed in to, navigating, clicking, filling forms, running multi-step web workflows, taking screenshots or PDFs - and for inspection work such as cookies, storage, network or console capture, and device emulation.
---

# Browser control

Operate the user's real, already-open browser as they would: open tabs, navigate, read,
click, type, and capture results, inside their existing logged-in sessions. Inspection
(cookies, storage, network, console, emulation) is available when a task needs it, but the
job is completing the task in the browser, not debugging it.

`scripts/browser.py` (Python 3.8+, stdlib only) is the CLI. It talks to a **broker**: a
windowless background process holding the **one** connection to the browser. The browser
asks the user to approve each new connection, so one broker = one approval for the whole
task. The broker exits on `stop`, after 15 idle minutes, or when the browser closes.

```
python scripts/browser.py <command> ...        # Windows: python or py -3; else python3
```

Paths below are relative to this skill's directory. Output is JSON on stdout; errors go to
stderr with exit code 2 (3 = browser control not enabled).

## Workflow

1. **Check:** `browser.py status`.
   - `endpoints` empty → control is off. Tell the user to open
     `edge://inspect/#remote-debugging` (Edge) or `chrome://inspect/#remote-debugging`
     (Chrome) and turn on **Allow remote debugging for this browser instance**. No restart
     needed. `browser.py enable-help --launch edge|chrome` opens that page for them.
     Agents cannot toggle it; never relaunch the user's browser with flags.
   - Several endpoints → pass `--browser edge|chrome|brave|...` on every call.
2. **Warn, then start:** tell the user *"Your browser will ask to allow remote debugging;
   click Allow"*, then run `browser.py start`. It blocks (up to 120 s) until they approve.
   Any command auto-starts the broker, but start explicitly so the prompt is expected.
3. **Work:** `targets` → pick a tab (or `open` a new one) → `nav` / `click` / `type` /
   `key` to act, `eval` / `screenshot` to read, with `-t`.
4. **Stop:** `browser.py stop` when the task is done, including after errors. Don't leave it
   to the idle timeout. Stopping removes the browser's "being controlled" banner.

## Commands

| Command | Does |
|---|---|
| `status` | Detected browsers + broker state (never prompts) |
| `start [--idle SEC]` / `stop` | Start / stop broker |
| `targets [--all]` | Tabs: `id`, `title`, `url` (`--all` adds workers, iframes, extensions) |
| `open URL [--background]` | New tab → `targetId` |
| `nav URL -t T [--no-wait]` | Navigate, wait for `load` |
| `click SELECTOR -t T [--count 2]` | Real mouse click at element center (scrolls into view) |
| `type TEXT -t T [-s SELECTOR] [--replace]` | Real text input into focused / selected element |
| `key KEY... -t T` | `Enter`, `Tab`, `Escape`, `ArrowDown`, `ctrl+a`, `x`, ... |
| `eval EXPR -t T` | Run JS in the page; returns JSON value. Top-level `await`, `let` OK; `@file.js` or `-` (stdin) |
| `screenshot FILE -t T [--full]` | PNG/JPEG (by extension); `--full` = whole page |
| `pdf FILE -t T [-p k=v]` | Print to PDF |
| `send METHOD [JSON] [-p k=v ...] [-t T]` | Any low-level browser command (cookies, storage, emulation, ...). Prints `result` |
| `events [-t T] [-f PREFIXES] [--since N] [--wait S] [--count N]` | Buffered browser events (last 5000) |
| `mark` | Current `last_seq`, for `events --since` |
| `batch FILE\|- [-t T]` | JSON lines `{"method","params","target"}` in one call |

**Target (`-t`)**: full targetId, unique id prefix, or a case-insensitive substring of the
tab's URL or title (`-t github`). Ambiguous matches error with candidates. Omit `-t` only
for browser-wide commands (`Target.*`, `Browser.*`, `Storage.*`, `SystemInfo.*`).

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
- Act with `click` / `type` / `key` (real input events; work with React and `isTrusted`
  checks). Read with `eval`. Details: `references/recipes.md`.
- Wait for results race-free: poll the page with `eval`, or `mark` → act →
  `events --since <mark> -f ... --wait 10 --count 1`.
- Events (network, console, page) arrive only after enabling that domain on the tab
  (`Network.enable`, `Page.enable`, `Runtime.enable`, `Log.enable`). A restarted broker
  needs them again.
- Large outputs: filter in JS (`eval`) rather than dumping whole DOMs or event logs.

## How it works

The broker speaks the Chrome DevTools Protocol (CDP) over the browser's remote-debugging
endpoint. That is an implementation detail; reach for it directly only through `send` and
`events` when no command covers the task. Method reference:
<https://chromedevtools.github.io/devtools-protocol/> (tip-of-tree). Errors come back as
`CDP error -32601/-32602 ...`.

## References

- `references/recipes.md`: reading pages, waiting, clicking/typing, tabs, file upload and
  downloads, iframes, screenshots/PDF, cookies and storage, network/console capture,
  emulation.
- `references/troubleshooting.md`: detection, approval prompt, stale broker, logs,
  launching a separate browser.
