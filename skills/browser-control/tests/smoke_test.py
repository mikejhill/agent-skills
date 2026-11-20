#!/usr/bin/env python3
"""End-to-end smoke test for browser.py against a throwaway headless browser.

Starts tests/fixture_server.py (an SPA built from shadow-DOM custom elements with timer
and fetch delays, like many enterprise Angular apps) and a headless Chromium with its own
profile, then drives it through the CLI with an isolated broker state directory, so the
user's real browser and broker are never touched.

    python tests/smoke_test.py [--chrome PATH]

Browser lookup: --chrome, $CHROME, Playwright's cached Chromium, then Chrome/Edge installs.
"""
import argparse
import glob
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "scripts", "browser.py")


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def find_chrome(explicit):
    cands = [explicit, os.environ.get("CHROME")]
    home = os.path.expanduser("~")
    for root in (os.path.join(home, "AppData", "Local", "ms-playwright"), os.path.join(home, ".cache", "ms-playwright"),
                 os.path.join(home, "Library", "Caches", "ms-playwright")):
        for exe in ("chrome.exe", "chrome"):
            cands += sorted(glob.glob(os.path.join(root, "chromium-*", "chrome-*", exe)), reverse=True)
        cands += sorted(glob.glob(os.path.join(root, "chromium-*", "chrome-*", "Chromium.app", "Contents", "MacOS", "Chromium")),
                        reverse=True)
    cands += [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              shutil.which("google-chrome") or "", shutil.which("chromium") or ""]
    for c in cands:
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    sys.exit("no Chromium found; pass --chrome PATH")


class Runner:
    def __init__(self, port, env):
        self.port, self.env, self.failures = port, env, 0

    def cli(self, *a, stdin=None):
        p = subprocess.run([sys.executable, CLI, "--port", str(self.port)] + list(a), input=stdin,
                           capture_output=True, text=True, encoding="utf-8", env=self.env, timeout=60)
        return p.returncode, p.stdout, p.stderr

    def check(self, name, cond, detail=""):
        print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  -> " + detail[:400]))
        self.failures += 0 if cond else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chrome")
    args = ap.parse_args()
    chrome = find_chrome(args.chrome)
    tmp = tempfile.mkdtemp(prefix="browser-smoke-")
    web, cdp = free_port(), free_port()
    env = dict(os.environ, BROWSER_CONTROL_HOME=os.path.join(tmp, "state"))
    procs = [subprocess.Popen([sys.executable, os.path.join(HERE, "fixture_server.py"), str(web)]),
             subprocess.Popen([chrome, "--headless=new", "--remote-debugging-port=%d" % cdp,
                               "--user-data-dir=" + os.path.join(tmp, "profile"), "--no-first-run",
                               "--no-default-browser-check"]
                             + (["--no-sandbox"] if getattr(os, "geteuid", lambda: 1)() == 0 else [])  # root (CI containers)
                             + ["about:blank"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)]
    r = Runner(cdp, env)
    try:
        end = time.time() + 20
        while True:
            try:
                urllib.request.urlopen("http://127.0.0.1:%d/json/version" % cdp, timeout=1).close()
                break
            except OSError:
                if time.time() > end:
                    sys.exit("browser did not open its debug port: %s" % chrome)
                time.sleep(0.2)
        print("browser:", chrome)
        code, o, e = r.cli("start", "--idle", "120")
        r.check("start", code == 0 and '"connected"' in o, e)
        r.check("start --idle sets the timeout", json.loads(o).get("idle_timeout") == 120, o)
        code, o, e = r.cli("start", "--idle", "300")
        r.check("start --idle updates a running broker", code == 0 and json.loads(o).get("idle_timeout") == 300
                and "starting broker" not in e, o + e)
        code, o, e = r.cli("start", "--idle", "0")
        r.check("start --idle rejects 0", code == 2 and "positive" in e, o + e)
        code, o, e = r.cli("open", "http://127.0.0.1:%d/" % web)
        tid = json.loads(o)["targetId"]
        code, o, e = r.cli("wait", "-t", tid, "--for-text", "Browse")
        r.check("wait for text", code == 0 and json.loads(o)["ok"], o + e)
        code, o, e = r.cli("eval", "document.body.innerText.trim()", "-t", tid)
        r.check("plain innerText misses shadow DOM (fixture sanity)", json.loads(o) == "", o)
        code, o, e = r.cli("text", "-t", tid)
        r.check("text pierces shadow DOM", "The catalog is open." in o, o)
        code, o, e = r.cli("click", "--text", "Browse", "-t", tid, "--show", "Choose a Product")
        res = json.loads(o) if code == 0 else {}
        r.check("click --text settles past timer+fetch", "Item G" in res.get("text", ""), o + e)
        r.check("click returns a change summary with the new lines",
                "Item A" in res.get("changes", {}).get("added", []) and "Return to Home" in res["changes"].get("new_controls", [])
                and res["changes"].get("url", "").endswith("#items"), o + e)
        code, o, e = r.cli("net", "-t", tid, "--grep", "/api/items")
        r.check("net lists the XHR", "/api/items" in o and " 200 Fetch " in o, o + e)
        rid = o.split()[0]
        code, o, e = r.cli("send", "Network.getResponseBody", "-p", "requestId=" + rid, "-t", tid)
        r.check("-p keeps numeric-looking string ids", code == 0 and "Item A" in o, e)
        code, o, e = r.cli("body", "/api/items", "--url", "-t", tid)
        r.check("body --url", code == 0 and json.loads(o)["items"][6]["name"] == "Item G", o + e)
        steps = "\n".join([
            "click --text 'Show more' --index 1",
            "text --grep Weight",
            "click --text 'Return to Home' --for-text 'Discard your changes' --no-settle",
            "click --text Yes --within 'Discard your changes' --for-text Welcome",
            "eval location.hash",
        ])
        code, o, e = r.cli("run", "-", "-t", tid, "--echo", "all", stdin=steps)
        r.check("run: hidden detail appears after settle", "Weight 1000 g" in o, o + e)
        r.check("run: dialog round trip", code == 0 and '"#home"' in o, o + e)
        code, o, e = r.cli("run", "-", "-t", tid, stdin="click --text Browse --for-text 'Item G'\n"
                           "click --text 'Show more' --index 1\ntext --grep Weight")
        r.check("run --echo last: short output, last step in full", code == 0 and len(o) < 500
                and "## 1 ok " in o and "Weight 1000 g" in o, o + e)
        code, o, e = r.cli("run", "-", "-t", tid, stdin="click --text 'Add to cart' --expect-text 'Cart (1)'\n"
                           "eval 1")
        r.check("run: failed --expect-text stops the run", code == 1 and "expectation not met" in e
                and "## 2" not in o and '"expect_failed"' in o, o + e)
        code, o, e = r.cli("wait", "-t", tid, "--no-settle", "--expect-url", "#items", "--expect-selector", "x-card")
        r.check("--expect-* passes when met", code == 0 and "expect_failed" not in o, o + e)
        r.cli("nav", "http://127.0.0.1:%d/#home" % web, "-t", tid, "--for-text", "Welcome")
        code, o, e = r.cli("run", "-", "-t", tid, stdin="click --text Nope --no-settle\neval 1")
        r.check("run stops on first error with candidates", code == 2 and "Clickable labels: " in e
                and "## 2" not in o, o + e)
        code, o, e = r.cli("eval", "await __dt.sleep(5); __dt.qsa('x-card').slice(0, 2)", "-t", tid)
        r.check("eval awaits and describes nodes", code == 0 and "<x-card#c1>" in o, o + e)
        code, o, e = r.cli("eval", "let z = 1; z", "-t", tid)
        code2, o2, e2 = r.cli("eval", "let z = 2; z", "-t", tid)
        r.check("eval let redeclaration (replMode)", o.strip() == "1" and o2.strip() == "2", o + e + o2 + e2)
        code, o, e = r.cli("nav", "http://127.0.0.1:%d/#items" % web, "-t", tid, "--for-text", "Item G")
        r.check("nav hash route returns without load event", code == 0 and json.loads(o)["loaded"], o + e)
        # existing tabs: select by URL / host / title / active, reuse, activate, close
        base = "http://127.0.0.1:%d/" % web
        code, o, e = r.cli("open", base + "?second#items")
        tid2 = json.loads(o)["targetId"]
        code, o, e = r.cli("activate", "-t", tid)
        code, o, e = r.cli("which", "-t", base + "?second#items")
        r.check("which: exact URL beats substring", code == 0 and json.loads(o)["id"] == tid2, o + e)
        code, o, e = r.cli("which", "-t", "127.0.0.1")
        r.check("which: ambiguous host lists candidates", code == 2 and "ambiguous" in e and tid2[:8] in e, o + e)
        code, o, e = r.cli("targets", "--focus", "--grep", "127.0.0.1")
        rows = json.loads(o) if code == 0 else []
        r.check("targets --focus marks the front tab",
                [x["id"] for x in rows if x.get("visible")] == [tid], o + e)
        code, o, e = r.cli("which", "-t", "active")
        r.check("-t active is the front tab", code == 0 and json.loads(o)["id"] == tid, o + e)
        code, o, e = r.cli("activate", "-t", tid2)
        code, o, e = r.cli("eval", "location.hash", "-t", "active")
        r.check("activate + eval -t active", code == 0 and json.loads(o) == "#items", o + e)
        code, o, e = r.cli("send", "Target.createTarget", "-p", "url=about:blank", "-p", "newWindow=true")
        win2 = json.loads(o)["targetId"]
        code, o, e = r.cli("activate", "-t", tid2)
        code, o, e = r.cli("which", "-t", "active")
        r.check("-t active with two windows: last activated wins", code == 0 and json.loads(o)["id"] == tid2, o + e)
        r.cli("close", "-t", win2)
        code, o, e = r.cli("open", base + "?second#items", "--reuse")
        r.check("open --reuse returns the existing tab", code == 0 and json.loads(o).get("reused")
                and json.loads(o)["targetId"] == tid2, o + e)
        code, o, e = r.cli("run", "-", "-t", base + "?second#items",
                           stdin="nav %s#home --for-text Welcome\neval location.hash" % base)
        r.check("run pins the tab across a nav that changes its URL", code == 0 and '"#home"' in o, o + e)
        code, o, e = r.cli("close", "-t", tid2)
        code2, o2, e2 = r.cli("targets", "--grep", "127.0.0.1")
        r.check("close", code == 0 and tid2 not in o2, o + e + o2)
        code, o, e = r.cli("eval", "document.body.insertAdjacentHTML('beforeend', "
                           "'<div class=skeleton style=\"width:50px;height:9px\"></div>')", "-t", tid)
        code, o, e = r.cli("wait", "-t", tid, "--timeout", "8")
        w = json.loads(o) if code == 0 else {}
        r.check("a placeholder that never goes away stops blocking settle", w.get("ok") and w["waited"] < 5, o + e)
        # a tab in a background/covered window is "hidden" and throttles timers; driving it
        # must not be slowed by that
        code, o, e = r.cli("send", "Target.createTarget", "-p", "url=about:blank", "-p", "background=true")
        bg = json.loads(o)["targetId"]
        code, o, e = r.cli("eval", "[document.visibilityState, await new Promise(ok => { let n = 0; const t0 = Date.now(); "
                           "const i = setInterval(() => { if (++n === 5) { clearInterval(i); ok(Date.now() - t0); } }, 150); })]",
                           "-t", bg)
        v = json.loads(o) if code == 0 else [None, 99999]
        r.check("background tab acts visible, timers unthrottled", v[0] == "visible" and v[1] < 1500, o + e)
        r.cli("close", "-t", bg)
        # settling: third-party noise doesn't block, first-party chains do, --for-* returns fast
        code, o, e = r.cli("nav", base + "beacon", "-t", tid)
        res = json.loads(o) if code == 0 else {}
        r.check("nav settles despite endless third-party beacons and lazy images",
                res.get("waited", 99) < 1.5 and "busy" not in res and "timeout" not in res, o + e)
        code, o, e = r.cli("nav", base + "beacon", "-t", tid, "--strict-settle", "--timeout", "3")
        res = json.loads(o) if code == 0 else {}
        r.check("--strict-settle keeps the old rules (never quiet here)",
                res.get("timeout") == "page still busy" and res.get("busy") and "warning:" in e, o + e)
        code, o, e = r.cli("nav", base + "chain", "-t", tid, "--show")
        r.check("settle waits for a first-party fetch chain", code == 0 and "Chain done" in o, o + e)
        code, o, e = r.cli("nav", base + "chain", "-t", tid, "--settle-max", "0.3", "--show")
        res = json.loads(o) if code == 0 else {}
        r.check("--settle-max caps settling with ok + busy report", res.get("settle") == "capped"
                and res.get("busy") and "Chain done" not in res.get("text", "") and "warning:" in e, o + e)
        code, o, e = r.cli("nav", base + "late", "-t", tid, "--no-wait")
        t0 = time.time()
        code, o, e = r.cli("wait", "-t", tid, "--for-text", "Late text")
        res = json.loads(o) if code == 0 else {}
        r.check("--for-text returns within 0.3 s of the text appearing", res.get("ok") and
                0.6 < res.get("waited", 0) < 1.1 and "settle" not in res, o + e)
        # change summary and text --changed
        code, o, e = r.cli("nav", base + "long", "-t", tid)
        res = json.loads(o) if code == 0 else {}
        r.check("nav summary is url/title/head", res.get("changes", {}).get("title") == "Long"
                and res["changes"].get("head") == ["More"], o + e)
        code, o, e = r.cli("text", "-t", tid, "--max", "50")
        code, o, e = r.cli("click", "#more", "-t", tid)
        res = json.loads(o) if code == 0 else {}
        ch = res.get("changes", {})
        r.check("long summary stays under 1200 chars with a pointer to the rest",
                len(json.dumps(ch)) <= 1200 and "Row 0" in ch.get("added", [""])[0]
                and "more lines: text --after" in ch.get("more", ""), o + e)
        code, o, e = r.cli("text", "-t", tid, "--changed", "--max", "100000")
        r.check("text --changed lists only lines added since the last read",
                code == 0 and o.count("Row ") == 60 and "More" not in o, o + e)
        code, o, e = r.cli("text", "-t", tid, "--changed")
        r.check("text --changed with no change", "[no change since the last text read]" in o, o + e)
        code, o, e = r.cli("click", "#out p", "-t", tid)
        res = json.loads(o) if code == 0 else {}
        r.check("no-op click returns changed: false", res.get("changes") == {"changed": False}, o + e)
        code, o, e = r.cli("click", "#out p", "-t", tid, "--summary", "none")
        r.check("--summary none omits the summary", code == 0 and "changes" not in json.loads(o), o + e)
        code, o, e = r.cli("run", "-", "-t", tid, stdin="click '#out p'\nclick '#out p'")
        r.check("run: summary only on the last action step", o.count('"changes"') == 1
                and o.rindex('"changes"') > o.index("## 2"), o + e)
        # extract
        r.cli("nav", base + "list", "-t", tid, "--summary", "none")
        code, o, e = r.cli("extract", "-t", tid, "--rows", ".res", "--limit", "4", "sku=@data-sku",
                           "name=h2", "price=.price", "url=a@href", "tags=.tag::all", "n=.tag::count")
        res = json.loads(o) if code == 0 else {}
        row = (res.get("rows") or [{}])[0]
        r.check("extract rows: text, @attr, absolute href, ::all, ::count", res.get("count") == 6
                and len(res["rows"]) == 4 and row == {"sku": "S1", "name": "Product 1", "price": "$3.00",
                "url": base + "p/1", "tags": ["new", "sale"], "n": 2}, o + e)
        r.check("extract: missing fields are null and counted", res.get("missing") == {"price": 1}
                and res["rows"][2]["price"] is None, o + e)
        code, o, e = r.cli("extract", "-t", tid, "title=h1")
        r.check("extract without --rows", code == 0 and json.loads(o) == {"title": "Results"}, o + e)
        code, o, e = r.cli("extract", "-t", tid, "--rows", ".nope", "name=h2")
        r.check("extract: zero rows exits 2 with candidate containers", code == 2
                and "div[data-sku] (6)" in e, o + e)
        code, o, e = r.cli("extract", "-t", tid, "--rows", "div[", "name=h2")
        r.check("extract: bad selector exits 2 and names it", code == 2 and "'div['" in e, o + e)
        code, o, e = r.cli("extract", "-t", tid, "--rows", ".res", "--format", "tsv", "sku=@data-sku", "price=.price")
        r.check("extract --format tsv", code == 0 and o.splitlines()[:2] == ["sku\tprice", "S1\t$3.00"]
                and len(o.splitlines()) == 7, o + e)
        r.cli("send", "Target.closeTarget", "-p", "targetId=" + tid)
    finally:
        r.cli("stop")
        for p in procs:
            if os.name == "nt":  # terminate() leaves the browser's child processes running
                subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
            else:
                p.terminate()
        for p in procs:
            try:
                p.wait(10)
            except subprocess.TimeoutExpired:
                p.kill()
        shutil.rmtree(tmp, ignore_errors=True)
    print("%d failure(s)" % r.failures)
    return 1 if r.failures else 0


if __name__ == "__main__":
    sys.exit(main())
