---
name: browser-control
description: Take control of the user's own running browser (Chrome, Edge, Brave) to do tasks in it with their real tabs, logins and sessions. Use whenever a task needs the user's browser - reading or extracting from pages they are signed in to, navigating, clicking, filling forms, running multi-step web workflows, pulling an app's JSON data, taking screenshots or PDFs - and for inspection work such as cookies, storage, network or console capture, and device emulation.
---

# Browser control

Operate the user's real, already-open browser as they would: open tabs, navigate, read,
click, type, and capture results, inside their existing logged-in sessions. Inspection
(cookies, storage, network, console, emulation) is available when a task needs it, but the
job is completing the task in the browser, not debugging it.

`scripts/browser.py` (Python 3.8+, stdlib only) is the CLI. It talks to a **broker**: a
windowless background process holding the **one** connection to the browser. The browser
asks the user to approve each new connection, so one broker = one approval for as long as it
runs, across tasks. The broker exits on `stop`, after 60 idle minutes, or when the browser
closes.

```text
python scripts/browser.py <command> ...        # Windows: python or py -3; else python3
```

Paths below are relative to this skill's directory. Output is compact JSON (`--pretty` to
indent) except `text`, `net` and `body`, which print plain text. Errors go to stderr with
exit code 2 (3 = browser control not enabled).

## Workflow

1. **Check:** `browser.py status`.
   - `endpoints` empty → control is off. Tell the user to open
     `edge://inspect/#remote-debugging` (Edge) or `chrome://inspect/#remote-debugging`
     (Chrome) and turn on **Allow remote debugging for this browser instance**. No restart
     needed. `browser.py enable-help --launch edge|chrome` opens that page for them.
     Agents cannot toggle it; never relaunch the user's browser with flags.
   - Several endpoints → pass `--browser edge|chrome|brave|...` on every call.
2. **Start first, then plan:** if `status` shows the broker `connected`, skip this step: no
   prompt is needed. Otherwise tell the user *"Your browser will ask to allow remote
   debugging; click Allow"* and run `browser.py start` before anything else in the task. It
   blocks (up to 120 s) until they approve; if you can run it in the background, do, and
   prepare the rest of the task meanwhile. Any command auto-starts the broker, but start
   explicitly so the prompt is expected.
3. **Pick the tab:** when the user points at a tab they have open ("my GitHub tab", "the
   page I'm on"), take over that tab: `which -t github.com` (or `-t active`) to confirm
   the match, then use the returned `id`. Otherwise `open URL --reuse` (reuses a tab
   already at that URL) or `open URL`. See *Existing tabs*.
4. **Work:** act and read with `-t ID` (see *Working fast*).
5. **Keep it running between tasks:** every new broker costs the user another approval
   prompt, so don't `stop` just because one task finished. Run `browser.py stop` when the
   user says they are done with the browser or asks to remove the "being controlled"
   banner, or before switching to another browser. Otherwise the broker exits by itself
   after 60 idle minutes (`start --idle SEC` or `BROWSER_CONTROL_IDLE` changes that; it
   also updates a running broker).

## Existing tabs

Every targeted command works on any tab the user already has open; nothing needs to be
opened first. `-t` selectors, best match first:

| Selector | Matches |
|---|---|
| `active` | The tab in front: focused window's tab, else the only visible one; with several windows, the tab last brought forward with `activate` |
| `https://github.com/` | Exact URL (scheme, `www.` and trailing `/` ignored) |
| `github.com`, `github.com/org/repo` | Host (incl. subdomains) or URL prefix |
| `github` | Substring of URL, then of title |
| `url:/pull/`, `title:Inbox` | Substring of that field only |
| `3F2A`, full id | Target id or unique prefix |

Only the best-ranked group counts; if it holds several tabs the command fails and lists
them (id, URL, title). Then use the id. `targets --grep S` filters the list,
`targets --focus` adds `visible`/`focused` per tab.

Resolve once, then work by id: a URL selector stops matching after the tab navigates.
`run -t SELECTOR` pins the tab itself.

```text
browser.py which -t github.com           # → {"id": "3F2A...", "url": "https://github.com/", ...}
browser.py activate -t 3F2A              # bring it to the front so the user can watch
browser.py nav https://github.com/notifications -t 3F2A
browser.py text -t 3F2A --max 3000
```

## Working fast

Each tool call costs seconds of agent time; fixed sleeps cost more. So:

- **Never `sleep`.** `click`, `nav` and `wait` block until the page settles: no in-flight
  same-site XHR/fetch/document/script, no visible spinner or "Loading..." (one stuck on screen
  for 3 s is ignored), and URL + visible text unchanged for `--quiet` (0.3 s). Third-party
  beacons, ads and images don't count. Settling stops after `--settle-max` (5 s) with
  `"settle": "capped"`.
- **Wait for the state you need.** `--for-text`, `--for-selector`, `--for-gone` or
  `--for-url` return as soon as it holds (no settle unless `--settle`): the fastest wait.
- **Read action output; never discard it** (`>/dev/null`, `| Out-Null`). `"timeout"`,
  `"settle": "capped"` and `"busy": ["host:count"]` say the page may not be ready.
- **Read with `text`, not `innerText`.** `text` pierces shadow DOM and same-origin iframes
  (where `document.body.innerText` returns nothing on Angular/Lit/Salesforce portals), shows
  form state (`[x]`, `[value]`), and trims with `--after MARKER`, `--grep REGEX -C N`,
  `--max`/`--offset`.
- **Click by label:** `click --text Edit --within "Shipping address"` finds visible
  buttons, links and roles by text (also in shadow DOM). A miss lists the clickable labels.
- **Chain steps in one call** with `run` (one CLI command per line, `-t` applied to all,
  stops at the first error). Do one `run` per page transition, then read its output:

  ```text
  browser.py run - -t shop <<'EOF'
  click --text Checkout
  click --text Continue --for-text "Order summary"
  text --after "Order summary" --max 6000
  EOF
  ```

  PowerShell: pipe a here-string, `@'...'@ | python $b run - -t shop`.
- **Prefer the app's JSON.** SPA data usually arrives by XHR: after any `click`/`nav`
  (they enable network capture), `net -t T` lists responses and
  `body ID -t T -o orders.json` (or `body /api/orders --url`) saves one. Parse the file
  instead of scraping the page.
- In `eval`, the `__dt` helpers are always defined (no injection step, survives reloads):
  `__dt.text({after, grep, max})`, `__dt.qsa(css)`, `__dt.find({text, within})`,
  `__dt.click({text, index})` (DOM click), `__dt.deepText(el)`, `await __dt.sleep(ms)`.

## Commands

| Command | Does |
|---|---|
| `status` | Detected browsers + broker state (never prompts) |
| `start [--idle SEC]` / `stop` | Start broker (or reuse the running one; `--idle` resets its timeout) / stop it |
| `targets [--all] [--grep S] [--focus]` | Tabs: `id`, `title`, `url` (`--all` adds workers, iframes, extensions) |
| `which -t T` | The tab `T` resolves to (`id`, `title`, `url`); errors list candidates |
| `activate -t T` / `close -t T` | Bring tab to front / close it |
| `open URL [--background] [--reuse]` | New tab → `targetId`; `--reuse` returns an open tab at that URL/host instead |
| `nav URL -t T [--no-wait] [WAIT]` | Navigate; waits for `load` (not for hash routes), then settles |
| `click [CSS] [--text T] [--index N] [--within T] -t T [WAIT]` | Real click (falls back to DOM click if covered); settles |
| `type TEXT -t T [-s SELECTOR] [--replace]` | Real text input into focused / selected element |
| `key KEY... -t T [--settle]` | `Enter`, `Tab`, `Escape`, `ArrowDown`, `ctrl+a`, `x`, ... |
| `wait -t T [WAIT]` | Settle and/or wait for a condition |
| `text -t T [--after M] [--grep RE] [--max N]` | Visible text incl. shadow DOM, as plain lines |
| `eval EXPR -t T` | Run JS in the page; returns JSON value (nodes described). Top-level `await`, `let`, `@file.js`, `-` |
| `net -t T [--grep S] [--since N] [--all]` | Recent XHR/fetch/document responses: `id status type mime url` |
| `body ID -t T [-o FILE]` / `body SUBSTR --url` | Response body (by request id or URL substring) |
| `run FILE\|- [-t T] [--keep-going]` | Run CLI steps (one per line) in one process |
| `screenshot FILE -t T [--full]` | PNG/JPEG (by extension); `--full` = whole page |
| `pdf FILE -t T [-p k=v]` | Print to PDF |
| `send METHOD [JSON] [-p k=v ...] [-t T]` | Any low-level browser command (cookies, storage, emulation, ...). Prints `result` |
| `events [-t T] [-f PREFIXES] [--since N] [--wait S] [--count N]` | Buffered browser events (last 20000) |
| `mark` | Current `last_seq`, for `events --since` / `net --since` |
| `batch FILE\|- [-t T]` | Low-level: JSON lines `{"method","params","target"}` in one call |

`WAIT` = `--for-text T`, `--for-selector CSS`, `--for-gone T`, `--for-url S`, `--no-settle`,
`--settle`, `--quiet SEC` (0.3), `--settle-max SEC` (5), `--strict-settle`, `--timeout SEC`
(15, load and condition), `--show [MARKER]` (print visible text after waiting).

**Target (`-t`)**: any selector from *Existing tabs*. Omit `-t` only for browser-wide
commands (`Target.*`, `Browser.*`, `Storage.*`, `SystemInfo.*`).

**Params**: `-p` avoids shell-quoting JSON (PowerShell mangles inline JSON). Values parse
as JSON when possible (`*Id` keys stay strings unless integers), dotted keys nest:
`send Emulation.setDeviceMetricsOverride -p width=390 -p height=844 -p deviceScaleFactor=3 -p mobile=true -t T`.
Complex params: write a `.json` file and pass `@params.json`.

## Rules

- **It's the user's real browser.** Prefer read-only work. Ask before submitting forms,
  purchasing, sending messages, deleting, or changing settings.
- **Tabs:** drive a tab the user named or pointed to; that is the point of asking. Don't
  navigate other tabs of theirs away from their page: `open` (or `open --reuse`) a tab for
  your own work instead. Close only tabs you opened (`close -t ID`).
- **Never print or store cookies, tokens or passwords** unless the user asked for them.
  Response bodies and headers can carry session tokens: save to a file and extract fields.
- Act with `click` / `type` / `key` (real input events; work with React and `isTrusted`
  checks). Read with `text`, `net`/`body`, or `eval`. Details: `references/recipes.md`.
- Events (network, console, page) arrive only after enabling that domain on the tab
  (`Network.enable`, `Page.enable`, `Runtime.enable`, `Log.enable`; `click`/`nav`/`wait`
  enable Network themselves). A restarted broker needs them again.
- Large outputs: narrow with `--after`/`--grep` or filter in JS rather than dumping whole
  pages or event logs.

## How it works

The broker speaks the Chrome DevTools Protocol (CDP) over the browser's remote-debugging
endpoint. That is an implementation detail; reach for it directly only through `send`,
`events` and `batch` when no command covers the task. Method reference:
<https://chromedevtools.github.io/devtools-protocol/> (tip-of-tree). Errors come back as
`CDP error -32601/-32602 ...`.

## References

- `references/recipes.md`: reading pages, waiting, multi-step runs, clicking/typing,
  network/console capture, cookies and storage, screenshots/PDF, emulation, tabs, file
  upload and downloads, iframes.
- `references/troubleshooting.md`: detection, approval prompt, stale broker, logs,
  launching a separate browser.
- `tests/smoke_test.py`: end-to-end check against a throwaway headless browser.
