# Browser control recipes

`C` = `python scripts/browser.py`, `T` = a target from `C targets`. All verified against Chromium.

## How it works

The broker speaks the Chrome DevTools Protocol (CDP) over the browser's remote-debugging
endpoint. That is an implementation detail; reach for it directly only through `send`,
`events` and `batch` when no command covers the task. Method reference:
<https://chromedevtools.github.io/devtools-protocol/> (tip-of-tree). Errors come back as
`CDP error -32601/-32602 ...`.

## Reading pages

```
C text -t T                                       # visible text, shadow DOM + iframes, one item per line
C text -t T --after "Search results" --max 6000  # skip nav chrome above a marker
C text -t T --grep "price|in stock" -C 2
C eval "document.title" -t T
C eval "__dt.qsa('a').map(a => ({text: __dt.label(a), href: a.href})).slice(0, 50)" -t T
C send Accessibility.getFullAXTree -t T          # semantic tree; large, prefer text/eval
```

`document.body.innerText` and `document.querySelectorAll` stop at shadow roots; on web
component portals (Salesforce, many Angular/Lit enterprise apps) use `text` and `__dt.qsa`.

## Waiting

```
C click --text Continue -t T                      # click, then settle (network + DOM quiet)
C click --text Continue -t T --for-text "Step 2"  # ...return once this text shows (no settle)
C nav URL -t T --for-selector "table.results"     # load event, then condition
C wait -t T --for-gone "Loading" --settle         # spinner gone, then settle too
C nav URL -t T --strict-settle                    # old rules: every request counts, no cap
```

Settled = for `--quiet` seconds (0.3; 0.5 after a `click`/`key` until anything changes):

- no busy request: a same-site XHR/fetch/document/script, the tab's own document, or a
  third-party XHR/fetch under 1.5 s old (requests open > 10 s are ignored)
- no visible spinner/`aria-busy`/"Loading..."
- URL, visible text length and completed same-site XHR/fetch count unchanged

Same-site = same registrable domain (`api.shop.com` ~ `www.shop.com`). Settling stops after
`--settle-max` (5 s): ok, plus `"settle": "capped"` and `"busy": ["host:count", ...]`.
A `--for-*` condition replaces settling (one 0.1 s confirmation poll) unless `--settle`.
Timeouts (`--timeout`, 15 s, for load and condition) return `"timeout": ...` with exit 0 for
`click`/`nav` and exit 1 for `wait`, so check the field. Capped and timed-out waits also
print a `warning:` line on stderr. Polling in-page is still possible:

```
C eval "await new Promise((ok, no) => { const t0 = Date.now(); (function f(){ const e = __dt.qsa('#result')[0]; if (e) ok(e.innerText); else if (Date.now() - t0 > 10000) no(new Error('timeout')); else setTimeout(f, 100); })(); })" -t T
```

## Extract

```
C extract -t T title=h1 price="#price" image="#main img@src"         # one object
C extract -t T --rows "li.result" --limit 20 name=h3 url="a@href" id=@data-id tags=".tag::all"
# {"rows": [{...}], "count": 37, "missing": {"price": 2}}
C extract -t T --rows "tr" --format tsv cells="td::all"              # header + one line per row
```

- Fields are scoped to each row; visible elements only unless `--hidden`.
- Text is whitespace-collapsed and cut at `--max-field` (200); `href`/`src` are absolute.
- A missing field is `null` and counted in `missing`; output is capped at 8000 chars
  (`truncated`: rows dropped).
- `--rows` matching nothing exits 2 and lists repeated containers to try.

## Change summaries

```
C click --text Save -t T
# {"clicked": "Save", ..., "changes": {"added": ["Saved"], "removed": 1, "alerts": ["Saved"]}}
C click --text Next -t T
# {"changes": {"url": ".../step2", "added": ["Step 2 of 3", ...], "more": "+40 more lines: text --after \"...\""}}
C text -t T --changed                             # only lines new since the last `text` read
```

A new document gives `url`, `title`, `head` (first 6 lines). Nothing changed gives
`{"changed": false}`. `"settled": false` means the page may still be loading. In `run`, only
the last `click`/`nav`/`key` step reports a summary unless `run --summary full`.

## Multi-step runs

`run` executes CLI lines in one process (shared `-t`, stops at the first failing step
unless `--keep-going`). Use it for each page transition: action, wait, read. By default
(`--echo last`) passing steps print one `## N ok ...` line; a failing step and the last
step print in full. `--expect-text`/`--expect-selector`/`--expect-url` on a step fail it
(exit 1) when the page doesn't show what you predicted, so a wrong click stops the batch.

```
C run - -t T <<'EOF'
click --text Edit --within "Shipping address"
text --after "Shipping address" --max 3000
click --text Back --no-settle --for-text "Discard changes"
click --text Yes --within "Discard changes"
EOF
```

## Clicking and typing

Built-ins dispatch trusted input (`isTrusted: true`; work with React-controlled inputs):

```
C click --text "Show more" --index 2 -t T         # by visible label, 3rd match; pierces shadow DOM
C click --text Edit --within "Dental" -t T        # label match nearest to text "Dental"
C click "button[type=submit]" -t T                # CSS (also pierces shadow DOM); scrolls into view
C type "hello world" -s "#q" --replace -t T       # focus #q, overwrite its text
C key Enter -t T --settle                         # also Tab, Escape, ArrowDown, ctrl+a, x
```

`click` hit-tests the element's center; if something covers it, it falls back to
`element.click()` and reports `"via": "dom"`. `--dom` forces that.

DOM-level alternative (no focus/visibility needed):

```
C eval "document.querySelector('#btn').click()" -t T
```

Raw equivalents: `Input.dispatchMouseEvent` (mouseMoved/mousePressed/mouseReleased with
x, y, button, clickCount), `Input.insertText`, `Input.dispatchKeyEvent`.
Coordinates are CSS pixels relative to the viewport; scroll the element into view first
(`el.scrollIntoView({block: 'center'})`). Background tabs may not paint: bring the tab
forward with `send Target.activateTarget -p targetId=ID` (or `Page.bringToFront -t T`) for
screenshots and trusted input.

## Network capture

`click`, `nav` and `wait` enable Network on the tab before acting, so their XHRs are buffered.

```
C mark                                            # → {"last_seq": N}
C click --text Search -t T
C net -t T --since N                              # id status type mime url (XHR/fetch/document)
C body 1234.56 -t T -o results.json            # save a body; parse the file
C body /api/search --url -t T --max 2000          # latest response whose URL contains it
C send Network.getResponseBody -p requestId=<id> -t T   # raw; base64Encoded flag for binary
C events -t T -f Network.responseReceived --since N --limit 20
```

`-f` takes comma-separated **prefixes** (`Network.requestWillBeSent` also matches
`...ExtraInfo`). The broker buffers the last 20000 events across all tabs, so filter by `-t`.
Response headers can include session tokens: don't print them.

## Console and errors

```
C send Runtime.enable -t T     # replays existing console messages as events
C events -t T -f Runtime.consoleAPICalled,Runtime.exceptionThrown --limit 50
```

Each `consoleAPICalled` has `params.type` and `params.args[].value`/`description`.

## Cookies and storage

```
C send Storage.getCookies                         # all cookies in the browser (sensitive!)
C send Network.getCookies -p 'urls=["https://example.com"]' -t T
C eval "JSON.stringify(localStorage)" -t T
```

Never echo cookie values or tokens to the user unless asked.

## Screenshots and PDF

```
C screenshot page.png -t T          # viewport
C screenshot full.png -t T --full   # whole page
C pdf page.pdf -t T [-p landscape=true -p scale=0.8]   # Page.printToPDF, printBackground on
```

## Emulation (per tab; reset when done)

```
C send Emulation.setDeviceMetricsOverride -p width=390 -p height=844 -p deviceScaleFactor=3 -p mobile=true -t T
C send Emulation.clearDeviceMetricsOverride -t T
C send Emulation.setEmulatedMedia -p 'features=[{"name":"prefers-color-scheme","value":"dark"}]' -t T
C send Emulation.setUserAgentOverride -p userAgent="..." -t T
C send Network.emulateNetworkConditions -p offline=false -p latency=200 -p downloadThroughput=50000 -p uploadThroughput=20000 -t T
```

## Tabs

```
C targets --grep github                            # the user's open tabs matching "github"
C which -t https://github.com/                     # exact URL → id; ambiguity lists candidates
C which -t active                                  # tab in front
C open https://example.com --reuse                 # existing tab at that URL/host, else new
C open https://example.com --background           # → targetId
C activate -t ID                                   # focus tab
C close -t ID
```

## Files

```
# file upload into <input type=file>
C send DOM.getDocument -t T                        # root nodeId
C send DOM.querySelector -p nodeId=1 -p selector="input[type=file]" -t T
C send DOM.setFileInputFiles -p nodeId=<id> -p 'files=["C:\\path\\file.txt"]' -t T
# downloads to a folder
C send Browser.setDownloadBehavior -p behavior=allow -p downloadPath="C:\\Users\\me\\Downloads\\browser" -p eventsEnabled=true
```

## Iframes / workers

`C targets --all` lists cross-origin iframes (`type: iframe`) and workers; target them by id.
Same-origin iframes: reach via `document.querySelector('iframe').contentDocument` in `eval`.

## Raw protocol

Everything is `{method, params}` + optional session. The full method list:
<https://chromedevtools.github.io/devtools-protocol/tot/> . `send --raw` prints the whole
response envelope; `--timeout` raises the 30 s default.
