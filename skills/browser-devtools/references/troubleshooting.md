# Troubleshooting

## How detection works

`status` reads `DevToolsActivePort` (line 1 = port, line 2 = `/devtools/browser/<id>`) from
each known profile dir and keeps entries whose port accepts a TCP connection (the file
can be stale after a crash). Fallback: `http://127.0.0.1:9222|9229/json/version`.

| Browser | Windows (`%LOCALAPPDATA%\...`) | macOS (`~/Library/Application Support/...`) | Linux (`~/.config/...`) |
|---|---|---|---|
| Edge | `Microsoft\Edge\User Data` | `Microsoft Edge` | `microsoft-edge` |
| Chrome | `Google\Chrome\User Data` | `Google/Chrome` | `google-chrome` |
| Brave | `BraveSoftware\Brave-Browser\User Data` | `BraveSoftware/Brave-Browser` | `BraveSoftware/Brave-Browser` |

Beta/Dev/Canary channels are also checked (`--browser edge-beta`, `chrome-canary`, ...).
Custom port or profile: `--port N` (needs the classic `/json/version` endpoint).

## Two ways remote debugging gets enabled

1. **In-browser toggle** (`edge://inspect/#remote-debugging`, `chrome://inspect/#remote-debugging`):
   applies to the running browser, no restart, persists only for that browser session.
   Every new WebSocket shows an **"Allow remote debugging?"** prompt in the browser; the
   connection stalls until the user answers. The HTTP `/json/*` endpoints are not served,
   so only `DevToolsActivePort` reveals the URL. While connected, the browser shows a
   "being controlled by automated test software"/debugging banner.
2. **Launch flag** `--remote-debugging-port=9222`: no prompt, `/json/*` served. Chrome 136+
   ignores it for the default profile; it needs `--user-data-dir=<separate dir>` (a fresh
   profile without the user's logins). Only use this if the user asks for an isolated
   browser; never kill or relaunch the user's browser yourself.

## Symptoms

| Symptom | Cause / fix |
|---|---|
| `status` exit 3, no endpoints | Debugging off, or browser closed since. Ask user to enable it (above). |
| `start` hangs, then "timed out waiting for the browser" | Prompt not approved (maybe behind other windows). Ask the user to look at the browser, then retry. |
| "connection closed during handshake" | User clicked Deny, or the browser closed. |
| `broker exited` / `disconnected` | Browser closed or debugging toggled off. Next command restarts the broker (new prompt). |
| Second approval prompt mid-task | Broker restarted (idle timeout or browser restart). Raise `start --idle`. |
| Events missing | Domain not enabled on that tab, broker restarted, or `--since` wrong (use `mark`). |
| `no target matches` / ambiguous | Use `targets` and pass an id prefix. Tabs that navigated keep their id. |
| Screenshot blank/hangs on a background tab | `send Target.activateTarget -p targetId=ID` first. |
| `CDP error -32000 ... Not allowed` | Some methods are blocked on `chrome://`/`edge://` pages and extension pages. |
| PowerShell breaks JSON args | Use `-p key=value` or `@params.json`. |

## Broker internals

- State: `%LOCALAPPDATA%\browser-devtools\broker.json` (Windows), `~/Library/Caches/browser-devtools`
  (macOS), `~/.cache/browser-devtools` (Linux): port, random token, pid. Log: `broker.log` there.
- Listens on `127.0.0.1` random port; every request must carry the token from the
  state file (other local users can't drive the browser).
- Windows: spawned with `pythonw.exe` + `CREATE_NO_WINDOW | DETACHED_PROCESS`, so no console
  window appears and closing the caller's terminal doesn't kill it.
- Exits on: `stop`, idle timeout (default 900 s since the last CLI request), browser
  disconnect, or failed connect. It removes its state file on exit.
- One broker per user. To switch browsers: `stop`, then `--browser other start`.
- Stuck process (rare): find the pid in `broker.json` and kill it (`taskkill /PID n /F`,
  `kill n`), then delete `broker.json`.
