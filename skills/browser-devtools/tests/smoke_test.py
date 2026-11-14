#!/usr/bin/env python3
"""End-to-end smoke test for devtools.py against a throwaway headless browser.

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
CLI = os.path.join(HERE, "..", "scripts", "devtools.py")


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
                           capture_output=True, text=True, env=self.env, timeout=60)
        return p.returncode, p.stdout, p.stderr

    def check(self, name, cond, detail=""):
        print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  -> " + detail[:400]))
        self.failures += 0 if cond else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chrome")
    args = ap.parse_args()
    chrome = find_chrome(args.chrome)
    tmp = tempfile.mkdtemp(prefix="devtools-smoke-")
    web, cdp = free_port(), free_port()
    env = dict(os.environ, BROWSER_DEVTOOLS_HOME=os.path.join(tmp, "state"))
    procs = [subprocess.Popen([sys.executable, os.path.join(HERE, "fixture_server.py"), str(web)]),
             subprocess.Popen([chrome, "--headless=new", "--remote-debugging-port=%d" % cdp,
                               "--user-data-dir=" + os.path.join(tmp, "profile"), "--no-first-run",
                               "--no-default-browser-check", "about:blank"],
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
        code, o, e = r.cli("run", "-", "-t", tid, stdin=steps)
        r.check("run: hidden detail appears after settle", "Weight 1000 g" in o, o + e)
        r.check("run: dialog round trip", code == 0 and '"#home"' in o, o + e)
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
        r.cli("send", "Target.closeTarget", "-p", "targetId=" + tid)
    finally:
        r.cli("stop")
        for p in procs:
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
