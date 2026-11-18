#!/usr/bin/env python3
"""Lifecycle smoke test for xh.py against a fake agent CLI (no network, no auth).

Run: python tests/smoke_test.py   (Windows: py -3 tests\\smoke_test.py)
Checks: results and sessions, failure capture, grandchild reaping, cancel,
timeout, owner exit, supervisor crash sweep, nesting guard, state outside cwd.
"""
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
XH = HERE.parent / "scripts" / "xh.py"
FAKE = HERE / "fake_agent.py"
IS_WIN = os.name == "nt"
sys.path.insert(0, str(XH.parent))
import xh  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="xh-test-"))
WORK = TMP / "repo"
WORK.mkdir()
ENV = dict(os.environ, CROSS_HARNESS_HOME=str(TMP / "home"), FAKE_PIDS=str(TMP / "pids"))
ENV.pop("CROSS_HARNESS_DEPTH", None)


def fake_bin(flavor):
    """A launcher for the fake agent that the resolver accepts as-is."""
    if IS_WIN:
        return str(FAKE)  # .py is run with the current interpreter
    p = TMP / f"fake-{flavor}"
    p.write_text(f"#!/bin/sh\nFAKE_FLAVOR={flavor} exec {sys.executable} {FAKE} \"$@\"\n")
    p.chmod(0o755)
    return str(p)


ENV["CROSS_HARNESS_CODEX_BIN"] = fake_bin("codex")
ENV["CROSS_HARNESS_CLAUDE_BIN"] = fake_bin("claude")
if IS_WIN:
    ENV["FAKE_FLAVOR"] = "codex"

FAILS = []


def run(*args, env=None, check=None):
    r = subprocess.run([sys.executable, str(XH), *args], capture_output=True, text=True,
                       cwd=WORK, env=env or ENV, timeout=120)
    if check is not None and r.returncode != check:
        raise AssertionError(f"xh {' '.join(args)} -> {r.returncode}\n{r.stdout}\n{r.stderr}")
    return r


def start(*args, **kw):
    r = run(*args, "--no-owner", check=0, **kw)
    return json.loads(r.stdout)["job"]


def job(jid):
    return json.loads((TMP / "home" / "jobs" / jid / "job.json").read_text())


def pids(role):
    f = TMP / "pids"
    if not f.exists():
        return []
    return [int(l.split()[1]) for l in f.read_text().splitlines() if l.startswith(role + " ")]


def gone(pid, wait=10.0):
    end = time.time() + wait
    while time.time() < end:
        if xh.proc_start_time(pid) is None:
            return True
        time.sleep(0.2)
    return False


def case(name):
    def deco(fn):
        (TMP / "pids").unlink(missing_ok=True) if sys.version_info >= (3, 8) else None
        try:
            fn()
            print(f"PASS {name}")
        except Exception as e:  # noqa: BLE001
            FAILS.append(name)
            print(f"FAIL {name}: {e}")
        return fn
    return deco


@case("codex task returns result and session; supervisor cwd is the state home")
def _():
    jid = start("task", "-t", "codex", "hello")
    r = run("wait", jid, "--timeout", "30", check=0)
    assert "fake codex answer" in r.stdout, r.stdout
    j = job(jid)
    assert j["status"] == "succeeded" and j["session"], j
    assert "exec" in j["argv"] and "-s" in j["argv"] and "read-only" in j["argv"], j["argv"]
    assert f"cwd={WORK.resolve()}" in r.stdout


@case("claude review parses JSON result and uses read-only tools")
def _():
    env = dict(ENV, FAKE_FLAVOR="claude")
    jid = start("review", "-t", "claude", "--base", "main", "--adversarial", env=env)
    r = run("wait", jid, "--timeout", "30", check=0, env=env)
    j = job(jid)
    assert j["status"] == "succeeded" and j["cost_usd"] == 0.01, j
    assert "--no-session-persistence" in j["argv"] and "--disallowedTools" in j["argv"], j["argv"]
    assert "fake claude answer" in r.stdout


@case("codex plain review uses native 'exec review --base'")
def _():
    jid = start("review", "-t", "codex", "--base", "main")
    run("wait", jid, "--timeout", "30", check=0)
    a = job(jid)["argv"]
    assert a[a.index("exec") + 1] == "review" and "--base" in a and "--ephemeral" in a, a


@case("failure is recorded with stderr, not left running")
def _():
    jid = start("task", "-t", "codex", "FAIL")
    r = run("wait", jid, "--timeout", "30", check=1)
    assert job(jid)["status"] == "failed" and "simulated failure" in job(jid)["error"], r.stdout


@case("grandchildren are reaped when the job ends")
def _():
    jid = start("task", "-t", "codex", "GRANDCHILD")
    run("wait", jid, "--timeout", "30", check=0)
    gcs = pids("grandchild")
    assert gcs and all(gone(p) for p in gcs), gcs


@case("cancel ends the whole tree")
def _():
    jid = start("task", "-t", "codex", "GRANDCHILD SLEEP=120")
    time.sleep(3)
    run("cancel", jid, check=0)
    assert job(jid)["status"] == "cancelled", job(jid)
    assert all(gone(p) for p in pids("child") + pids("grandchild"))


@case("time limit ends the job")
def _():
    jid = start("task", "-t", "codex", "--timeout", "0.05", "SLEEP=120")
    r = run("wait", jid, "--timeout", "30", check=1)
    assert job(jid)["status"] == "timed_out", r.stdout
    assert all(gone(p) for p in pids("child"))


@case("wait returns 3 while running")
def _():
    jid = start("task", "-t", "codex", "SLEEP=6")
    r = run("wait", jid, "--timeout", "1", check=3)
    assert json.loads(r.stdout)["status"] == "running"
    run("wait", jid, "--timeout", "30", check=0)


@case("owner exit ends the job")
def _():
    if IS_WIN:
        owner = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(600)"])
    else:
        link = TMP / "codex"
        link.symlink_to(sys.executable)
        owner = subprocess.Popen([str(link), "-c", "import time; time.sleep(600)"])
    st = xh.proc_start_time(owner.pid)
    # Start a job, then point its owner record at our fake owner.
    jid = start("task", "-t", "codex", "SLEEP=120")
    rec = job(jid)
    rec["owner"] = {"pid": owner.pid, "start": st, "name": "codex"}
    (TMP / "home" / "jobs" / jid / "job.json").write_text(json.dumps(rec))
    time.sleep(2)
    owner.kill()
    owner.wait()
    run("wait", jid, "--timeout", "30", check=1)
    assert job(jid)["status"] == "orphaned", job(jid)
    assert all(gone(p) for p in pids("child"))


@case("supervisor crash: sweep marks lost and no process survives")
def _():
    jid = start("task", "-t", "codex", "GRANDCHILD SLEEP=120")
    time.sleep(3)
    sup = job(jid)["supervisor"]["pid"]
    if IS_WIN:
        subprocess.run(["taskkill", "/PID", str(sup), "/F"], capture_output=True)
    else:
        os.kill(sup, signal.SIGKILL)
    time.sleep(1)
    run("status", check=0)
    assert job(jid)["status"] == "lost", job(jid)
    assert all(gone(p) for p in pids("child") + pids("grandchild")), "leftover processes"


@case("nested hand-off is refused by default")
def _():
    env = dict(ENV, CROSS_HARNESS_DEPTH="1")
    r = run("task", "-t", "codex", "hi", env=env, check=2)
    assert "Nested" in r.stderr


@case("resume by job id passes the recorded session")
def _():
    jid = start("task", "-t", "codex", "first")
    run("wait", jid, "--timeout", "30", check=0)
    jid2 = start("task", "-t", "codex", "--resume", jid, "second")
    run("wait", jid2, "--timeout", "30", check=0)
    a = job(jid2)["argv"]
    assert "resume" in a and job(jid)["session"] in a, a


@case("no job holds the repo after completion")
def _():
    run("status", check=0)
    live = [j for j in (TMP / "home" / "jobs").iterdir()
            if json.loads((j / "job.json").read_text())["status"] in ("running", "starting")]
    assert not live, live
    shutil.rmtree(WORK)  # would fail on Windows if any process still had it as cwd
    WORK.mkdir()


print(f"\n{len(FAILS)} failed" if FAILS else "\nall passed")
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(1 if FAILS else 0)
