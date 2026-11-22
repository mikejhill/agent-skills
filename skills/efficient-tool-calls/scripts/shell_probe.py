#!/usr/bin/env python3
"""shell_probe.py - measure how long each local shell takes to start, and cache the answer.

Shell startup cost depends on the machine: Git Bash can start in 60 ms on one Windows box
and 600 ms on another (antivirus, MSYS fork emulation, network home dirs), and a PowerShell
profile can add a second. Agent harnesses spawn a fresh shell per tool call, so the faster
shell saves that difference on every call. Measure once per machine; reuse the result.

    python shell_probe.py                 cached result if under 7 days old, else measure
    python shell_probe.py --force         measure now
    python shell_probe.py --max-age-days N
    python shell_probe.py --runs N        timed runs per shell (default 5, plus 1 warm-up)

Prints one JSON object: per-shell median/p90 startup in ms, the fastest POSIX shell, the
fastest PowerShell, and a recommendation. Stdlib only, Python 3.8+. Cache:
$EFFICIENT_TOOL_CALLS_CACHE, else the user cache dir (efficient-tool-calls/shell-probe.json).
"""
import argparse
import json
import os
import shutil
import socket
import statistics
import subprocess
import sys
import time

IS_WIN = os.name == "nt"
CACHE_VERSION = 1
CLOSE_MS = 150  # differences below this are small next to model and harness time per call


def cache_path():
    if os.environ.get("EFFICIENT_TOOL_CALLS_CACHE"):
        return os.environ["EFFICIENT_TOOL_CALLS_CACHE"]
    if IS_WIN:
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Caches")
    else:
        base = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
    return os.path.join(base, "efficient-tool-calls", "shell-probe.json")


def win_bash():
    """Git Bash, not the WSL launcher in System32 (that starts a Linux VM)."""
    cands = []
    for root in (os.environ.get("ProgramFiles"), os.environ.get("ProgramW6432"),
                 os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs")):
        if root:
            cands.append(os.path.join(root, "Git", "bin", "bash.exe"))
    w = shutil.which("bash")
    if w:
        cands.append(w)
    for c in cands:
        if c and os.path.isfile(c) and "system32" not in c.lower():
            return c
    return None


def candidates():
    """(name, family, argv) for each shell found. argv runs an empty command."""
    out = []
    posix = [("bash", win_bash())] if IS_WIN else [(n, shutil.which(n)) for n in ("bash", "zsh")]
    for name, p in posix:  # what agent shell tools run (not sh)
        if p:
            out.append((name, "posix", [p, "-c", "true"]))
            out.append((name + " (login)", "posix-login", [p, "-lc", "true"]))
    # Windows PowerShell 5.1 only stands in when pwsh 7 is missing: agent tools run pwsh, and
    # 5.1 lacks `&&`, ternaries and UTF-8 defaults, so a faster 5.1 start is no reason to use it.
    pw = shutil.which("pwsh")
    for name in ("pwsh", "powershell") if IS_WIN else ("pwsh",):
        p = shutil.which(name)
        if p:
            fam = "powershell" if name == "pwsh" or not pw else "powershell-5"
            out.append((name, fam, [p, "-NoProfile", "-NonInteractive", "-Command", "exit"]))
            out.append((name + " (profile)", "powershell-profile" if fam == "powershell" else "powershell-5-profile",
                        [p, "-NonInteractive", "-Command", "exit"]))
    if IS_WIN:
        p = shutil.which("cmd")
        if p:
            out.append(("cmd", "cmd", [p, "/d", "/c", "exit"]))
    return out


def time_one(argv, runs):
    kw = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if IS_WIN:
        kw["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
    ts = []
    for i in range(runs + 1):
        t = time.perf_counter()
        try:
            subprocess.run(argv, timeout=30, **kw)
        except (OSError, subprocess.SubprocessError):
            return None
        if i:  # first run is a warm-up (disk cache)
            ts.append((time.perf_counter() - t) * 1000)
    ts.sort()
    return {"median_ms": round(statistics.median(ts)), "p90_ms": round(ts[min(len(ts) - 1, int(len(ts) * 0.9))])}


def recommend(shells):
    def best(fam):
        c = [(v["median_ms"], k) for k, v in shells.items() if v.get("family") == fam]
        return min(c) if c else None
    px, ps = best("posix"), best("powershell")
    r = {"fastest_posix": px[1] if px else None, "fastest_powershell": ps[1] if ps else None}
    if px and ps:
        diff = ps[0] - px[0]
        if abs(diff) < CLOSE_MS:
            r["recommendation"] = ("either: startup differs by %d ms; choose by task (POSIX tools vs cmdlets)"
                                   % abs(diff))
        else:
            fast, slow = (px[1], ps[1]) if diff > 0 else (ps[1], px[1])
            r["recommendation"] = ("prefer %s for general command-line work: %d ms faster to start per call "
                                   "than %s; keep %s for work only it can do" % (fast, abs(diff), slow, slow))
        prof = best("powershell-profile")
        if prof and prof[0] - ps[0] >= CLOSE_MS:
            r["profile_cost_ms"] = prof[0] - ps[0]
    elif px or ps:
        r["recommendation"] = "only %s found: nothing to choose" % (px or ps)[1]
    else:
        r["recommendation"] = "no shell found"
    login = best("posix-login")
    if px and login and login[0] - px[0] >= CLOSE_MS:
        r["login_cost_ms"] = login[0] - px[0]
    return r


def measure(runs):
    shells = {}
    for name, fam, argv in candidates():
        t = time_one(argv, runs)
        if t:
            shells[name] = dict(t, family=fam, path=argv[0])
    res = {"v": CACHE_VERSION, "host": socket.gethostname(), "platform": sys.platform,
           "measured_at": int(time.time()), "runs": runs, "shells": shells}
    res.update(recommend(shells))
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--force", action="store_true", help="measure even if a fresh cached result exists")
    ap.add_argument("--max-age-days", type=float, default=7, help="reuse a cached result up to this old (7)")
    ap.add_argument("--runs", type=int, default=5, help="timed runs per shell (5)")
    a = ap.parse_args(argv)
    path = cache_path()
    if not a.force:
        try:
            with open(path, encoding="utf-8") as f:
                c = json.load(f)
            fresh = time.time() - c.get("measured_at", 0) < a.max_age_days * 86400
            if c.get("v") == CACHE_VERSION and c.get("host") == socket.gethostname() and fresh:
                c["cached"] = True
                print(json.dumps(c))
                return 0
        except (OSError, ValueError):
            pass
    res = measure(max(1, a.runs))
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(res, f)
    except OSError as e:
        sys.stderr.write("warning: could not write cache %s: %s\n" % (path, e))
    res["cached"] = False
    print(json.dumps(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
