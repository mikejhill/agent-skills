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

```text
python scripts/devtools.py <command> ...        # Windows: python or py -3; else python3
```

Paths below are relative to this skill's directory. Output is compact JSON (`--pretty` to
indent) except `text`, `net` and `body`, which print plain text. Errors go to stderr with
exit code 2 (3 = remote debugging not enabled).

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
3. **Work:** `targets` → pick a tab → act and read with `-t` (see *Fast navigation*).
4. **Stop:** `devtools.py stop` when the task is done, including after errors. Don't leave it to
   the idle timeout. Stopping removes the browser's "being debugged" banner.

## Fast navigation

Each tool call costs seconds of agent time; fixed sleeps cost more. So:

- **Never `sleep`.** `click`, `nav` and `wait` block until the page settles: no in-flight
  XHR/fetch, no visible spinner or "Loading...", and URL + visible text unchanged for
  `--quiet` (0.5 s). Add `--for-text`, `--for-selector`, `--for-gone` or `--for-url` to wait
  for a specific state. They return `"timeout"` instead of failing if the page never settles.
- **Read with `text`, not `innerText`.** `text` pierces shadow DOM and same-origin iframes
  (where `document.body.innerText` returns nothing on Angular/Lit/Salesforce portals), shows
  form state (`[x]`, `[value]`), and trims with `--after MARKER`, `--grep REGEX -C N`,
  `--max`/`--offset`.
- **Click by label:** `click --text Edit --within "Shipping address"` finds visible
  buttons, links and roles by text (also in shadow DOM). A miss lists the clickable labels.
- **Chain steps in one call** with `run` (one CLI command per line, `-t` applied to all,
  stops at the first error). Do one `run` per page transition, then read its output:

  ```text
  devtools.py run - -t shop <<'EOF'
  click --text Checkout
  click --text Continue --for-text "Order summary"
  text --after "Order summary" --max 6000
  EOF
  ```

  PowerShell: pipe a here-string, `@'...'@ | python $d run - -t shop`.
- **Prefer the app's JSON.** SPA data usually arrives by XHR: after any `click`/`nav`
  (they enable Network), `net -t T` lists responses and `body ID -t T -o orders.json` (or
  `body /api/orders --url`) saves one. Parse the file instead of scraping the DOM.
- In `eval`, the `__dt` helpers are always defined (no injection step, survives reloads):
  `__dt.text({after, grep, max})`, `__dt.qsa(css)`, `__dt.find({text, within})`,
  `__dt.click({text, index})` (DOM click), `__dt.deepText(el)`, `await __dt.sleep(ms)`.

## Commands

| Command | Does |
|---|---|
| `status` | Detected endpoints + broker state (never prompts) |
| `start [--idle SEC]` / `stop` | Start / stop broker |
| `targets [--all]` | Tabs: `id`, `title`, `url` (`--all` adds workers, iframes, extensions) |
| `open URL [--background]` | New tab → `targetId` |
| `nav URL -t T [--no-wait] [WAIT]` | Navigate; waits for `load` (not for hash routes), then settles |
| `click [CSS] [--text T] [--index N] [--within T] -t T [WAIT]` | Trusted click (falls back to DOM click if covered); settles |
| `type TEXT -t T [-s SELECTOR] [--replace]` | Trusted text input into focused / selected element |
| `key KEY... -t T [--settle]` | `Enter`, `Tab`, `Escape`, `ArrowDown`, `ctrl+a`, `x`, ... |
| `wait -t T [WAIT]` | Settle and/or wait for a condition |
| `text -t T [--after M] [--grep RE] [--max N]` | Visible text incl. shadow DOM, as plain lines |
| `eval EXPR -t T` | Run JS; returns JSON value (nodes described). Top-level `await`, `let`, `@file.js`, `-` |
| `net -t T [--grep S] [--since N] [--all]` | Recent XHR/fetch/document responses: `id status type mime url` |
| `body ID -t T [-o FILE]` / `body SUBSTR --url` | Response body (by requestId or URL substring) |
| `run FILE\|- [-t T] [--keep-going]` | Run CLI steps (one per line) in one process |
| `screenshot FILE -t T [--full]` | PNG/JPEG (by extension); `--full` = whole page |
| `pdf FILE -t T [-p k=v]` | Print to PDF |
| `send METHOD [JSON] [-p k=v ...] [-t T]` | **Any** CDP method. Prints `result` |
| `events [-t T] [-f PREFIXES] [--since N] [--wait S] [--count N]` | Buffered events (last 20000) |
| `mark` | Current `last_seq`, for `events --since` / `net --since` |
| `batch FILE\|- [-t T]` | Raw CDP: JSON lines `{"method","params","target"}` in one call |

`WAIT` = `--for-text T`, `--for-selector CSS`, `--for-gone T`, `--for-url S`, `--no-settle`,
`--quiet SEC`, `--timeout SEC` (15), `--show [MARKER]` (print visible text after waiting).

**Target (`-t`)**: full targetId, unique id prefix, or a case-insensitive substring of the
tab's URL or title (`-t github`). Ambiguous matches error with candidates. Omit `-t` only
for browser-level domains (`Target.*`, `Browser.*`, `Storage.*`, `SystemInfo.*`).
The broker attaches to each tab once and reuses the session.

**Params**: `-p` avoids shell-quoting JSON (PowerShell mangles inline JSON). Values parse
as JSON when possible (`*Id` keys stay strings unless integers), dotted keys nest:
`send Emulation.setDeviceMetricsOverride -p width=390 -p height=844 -p deviceScaleFactor=3 -p mobile=true -t T`.
Complex params: write a `.json` file and pass `@params.json`.

## Rules

- **It's the user's real browser.** Prefer read-only work. Ask before submitting forms,
  purchasing, sending messages, deleting, or changing settings. Prefer `open` for a new
  tab over navigating a tab the user is using; close tabs you opened
  (`send Target.closeTarget -p targetId=ID`).
- **Never print or store cookies, tokens or passwords** unless the user asked for them.
  Response bodies and headers can carry session tokens: save to a file and extract fields.
- Domains emit events only after `X.enable` on that tab (`Network.enable`, `Page.enable`,
  `Runtime.enable`, `Log.enable`; `click`/`nav`/`wait` enable Network themselves). Enables
  and the event buffer live in the broker: a restarted broker needs them again.
- Interact with `click` / `type` / `key` (real input events; work with React and
  `isTrusted` checks). Read with `text`, `net`/`body`, or `eval`. Details: `references/recipes.md`.
- Large outputs: narrow with `--after`/`--grep` or filter in JS rather than dumping whole
  DOMs/event logs.
- Unknown method or params: check <https://chromedevtools.github.io/devtools-protocol/>
  (tip-of-tree). Errors come back as `CDP error -32601/-32602 ...`.

## References

- `references/recipes.md`: clicking/typing, waiting, network/console capture, cookies,
  PDF, emulation, downloads, file upload, iframes.
- `references/troubleshooting.md`: detection, approval prompt, stale broker, logs,
  launching a separate debug browser.
- `tests/smoke_test.py`: end-to-end check against a throwaway headless browser.
