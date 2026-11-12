# Browser control recipes

`C` = `python scripts/browser.py`, `T` = a target from `C targets`. All verified against Chromium.

## Reading pages

```
C eval "document.title" -t T
C eval "[...document.querySelectorAll('a')].map(a => ({text: a.innerText.trim(), href: a.href})).slice(0, 50)" -t T
C eval "document.body.innerText.slice(0, 20000)" -t T
C send Accessibility.getFullAXTree -t T          # semantic tree; large, prefer eval
```

## Waiting

```
C nav URL -t T                                   # waits for load event
# wait for an element (SPA): poll in-page
C eval "await new Promise((ok, no) => { const t0 = Date.now(); (function f(){ const e = document.querySelector('#result'); if (e) ok(e.innerText); else if (Date.now() - t0 > 10000) no(new Error('timeout')); else setTimeout(f, 100); })(); })" -t T
```

## Clicking and typing

Built-ins dispatch trusted input (`isTrusted: true`; work with React-controlled inputs):

```
C click "button[type=submit]" -t T                # scrolls into view, clicks center
C type "hello world" -s "#q" --replace -t T       # focus #q, overwrite its text
C key Enter -t T                                  # also Tab, Escape, ArrowDown, ctrl+a, x
```

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

```
C send Network.enable -t T
C mark                                            # → {"last_seq": N}
C nav URL -t T
C events -t T -f Network.responseReceived --since <last_seq> --methods-only
C events -t T -f Network.responseReceived --since <last_seq> --limit 20
C send Network.getResponseBody -p requestId=<id> -t T   # body; base64Encoded flag for binary
C send Network.disable -t T
```

`-f` takes comma-separated **prefixes** (`Network.requestWillBeSent` also matches
`...ExtraInfo`). The broker buffers the last 5000 events across all tabs, so filter by `-t`.

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
C open https://example.com --background           # → targetId
C send Target.activateTarget -p targetId=ID        # focus tab
C send Target.closeTarget -p targetId=ID
```

## Files

```
# file upload into <input type=file>
C send DOM.getDocument -t T                        # root nodeId
C send DOM.querySelector -p nodeId=1 -p selector="input[type=file]" -t T
C send DOM.setFileInputFiles -p nodeId=<id> -p 'files=["C:\\path\\file.txt"]' -t T
# downloads to a folder
C send Browser.setDownloadBehavior -p behavior=allow -p downloadPath="C:\\Users\\me\\Downloads\\devtools" -p eventsEnabled=true
```

## Iframes / workers

`C targets --all` lists cross-origin iframes (`type: iframe`) and workers; target them by id.
Same-origin iframes: reach via `document.querySelector('iframe').contentDocument` in `eval`.

## Raw protocol

Everything is `{method, params}` + optional session. The full method list:
<https://chromedevtools.github.io/devtools-protocol/tot/> . `send --raw` prints the whole
response envelope; `--timeout` raises the 30 s default.
