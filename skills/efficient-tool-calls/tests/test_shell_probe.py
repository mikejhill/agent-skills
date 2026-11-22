#!/usr/bin/env python3
"""Tests for shell_probe.py: recommendation logic, caching, and a real measurement."""
import contextlib
import io
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
import shell_probe as sp  # noqa: E402

SCRIPT = os.path.join(HERE, "..", "scripts", "shell_probe.py")


def sh(name, fam, ms):
    return {name: {"median_ms": ms, "p90_ms": ms, "family": fam}}


class Recommend(unittest.TestCase):
    def test_posix_faster(self):
        r = sp.recommend({**sh("bash", "posix", 60), **sh("pwsh", "powershell", 400)})
        self.assertIn("prefer bash", r["recommendation"])

    def test_powershell_faster(self):  # e.g. slow Git Bash under antivirus
        r = sp.recommend({**sh("bash", "posix", 700), **sh("pwsh", "powershell", 350)})
        self.assertIn("prefer pwsh", r["recommendation"])
        self.assertIn("keep bash", r["recommendation"])

    def test_either_still_names_the_faster_shell(self):
        r = sp.recommend({**sh("bash", "posix", 76), **sh("pwsh", "powershell", 224)})
        self.assertTrue(r["recommendation"].startswith("either: bash starts 148 ms faster than pwsh"))

    def test_close_is_either(self):
        r = sp.recommend({**sh("bash", "posix", 300), **sh("pwsh", "powershell", 380)})
        self.assertTrue(r["recommendation"].startswith("either"))

    def test_profile_cost_reported(self):
        r = sp.recommend({**sh("bash", "posix", 60), **sh("pwsh", "powershell", 350),
                          **sh("pwsh (profile)", "powershell-profile", 1400)})
        self.assertEqual(r["profile_cost_ms"], 1050)

    def test_powershell_5_is_not_the_comparison(self):  # 5.1 starts faster than pwsh 7 on Windows
        r = sp.recommend({**sh("bash", "posix", 74), **sh("pwsh", "powershell", 245),
                          **sh("powershell", "powershell-5", 178)})
        self.assertEqual(r["fastest_powershell"], "pwsh")
        self.assertIn("prefer bash", r["recommendation"])

    def test_login_cost_reported(self):
        r = sp.recommend({**sh("bash", "posix", 60), **sh("bash (login)", "posix-login", 675)})
        self.assertEqual(r["login_cost_ms"], 615)

    def test_single_family(self):
        r = sp.recommend({**sh("bash", "posix", 5), **sh("zsh", "posix", 7)})
        self.assertIn("no PowerShell found to compare with; measured: bash, zsh", r["recommendation"])

    def test_cmd_only(self):
        r = sp.recommend(sh("cmd", "cmd", 40))
        self.assertIn("no POSIX shell or PowerShell found; measured: cmd", r["recommendation"])

    def test_profile_cost_without_posix(self):
        r = sp.recommend({**sh("pwsh", "powershell", 250), **sh("pwsh (profile)", "powershell-profile", 1200)})
        self.assertEqual(r["profile_cost_ms"], 950)

    def test_login_cost_is_same_executable(self):
        r = sp.recommend({**sh("bash", "posix", 50), **sh("bash (login)", "posix-login", 750),
                          **sh("zsh", "posix", 80), **sh("zsh (login)", "posix-login", 100)})
        self.assertEqual(r["fastest_posix"], "bash")
        self.assertEqual(r["login_cost_ms"], 700)


class Probe(unittest.TestCase):
    def test_p90_nearest_rank(self):
        orig = sp.run_once
        vals = iter([0.001] + [0.010] * 9 + [0.500])  # warm-up, nine fast, one slow
        sp.run_once = lambda argv, kw, limit=30: next(vals)
        try:
            r = sp.time_one(["x"], 10)
        finally:
            sp.run_once = orig
        self.assertEqual(r["p90_ms"], 10)

    @unittest.skipIf(os.name == "nt", "POSIX process groups")
    def test_timeout_kills_children(self):
        with tempfile.TemporaryDirectory() as d:
            mark = os.path.join(d, "child-alive")
            argv = ["/bin/sh", "-c", '(sleep 3; touch "$1") & sleep 30', "sh", mark]
            t = time.time()
            self.assertIsNone(sp.run_once(argv, {"stdout": subprocess.DEVNULL}, limit=1))
            self.assertLess(time.time() - t, 5)
            time.sleep(3)
            self.assertFalse(os.path.exists(mark), "child survived the timeout")


    @unittest.skipUnless(os.name == "nt", "Windows process tree")
    def test_timeout_kills_children_windows(self):
        t = time.time()
        self.assertIsNone(sp.run_once(["cmd", "/d", "/c", "ping -n 61 127.0.0.29 >nul"],
                                      {"stdout": subprocess.DEVNULL}, limit=2))
        self.assertLess(time.time() - t, 15)
        time.sleep(1)
        q = subprocess.run(["powershell", "-NoProfile", "-Command",
                            "$ErrorActionPreference = 'Stop'; "
                            "Get-CimInstance Win32_Process -Filter \"Name='PING.EXE'\" | "
                            "Where-Object { $_.CommandLine -like '*127.0.0.29*' } | ForEach-Object ProcessId"],
                           capture_output=True, text=True)
        self.assertEqual(q.returncode, 0, "process query failed: " + q.stderr)
        self.assertNotRegex(q.stdout, r"\d", "ping survived the timeout")


class Launch(unittest.TestCase):
    def test_failed_launch_is_not_timed(self):
        self.assertIsNone(sp.time_one([sys.executable, "-c", "raise SystemExit(1)"], 1))
        self.assertIsNone(sp.time_one([os.path.join(tempfile.gettempdir(), "no-such-shell-xyz")], 1))
        self.assertIsNotNone(sp.time_one([sys.executable, "-c", "pass"], 1))

    def test_directories_under_workspace_are_not_searched(self):
        with tempfile.TemporaryDirectory() as d:
            sub = os.path.join(d, ".venv", "bin")
            os.makedirs(sub)
            exe = os.path.join(sub, "fakeshell-xyz" + (".exe" if os.name == "nt" else ""))
            with open(exe, "w") as f:
                f.write("#!/bin/sh\n")
            os.chmod(exe, 0o755)
            old, oldpath = os.getcwd(), os.environ.get("PATH", "")
            os.chdir(d)
            os.environ["PATH"] = os.pathsep.join([sub, oldpath])
            try:
                self.assertIsNone(sp.find_exe("fakeshell-xyz"))
            finally:
                os.chdir(old)
                os.environ["PATH"] = oldpath

    def test_user_installs_found_when_run_from_home(self):
        with tempfile.TemporaryDirectory() as d:
            sub = os.path.join(d, "AppData", "Programs", "bin")
            os.makedirs(sub)
            exe = os.path.join(sub, "fakeshell-xyz" + (".exe" if os.name == "nt" else ""))
            with open(exe, "w") as f:
                f.write("#!/bin/sh\n")
            os.chmod(exe, 0o755)
            old, oldpath = os.getcwd(), os.environ.get("PATH", "")
            oldhome = {k: os.environ.get(k) for k in ("HOME", "USERPROFILE")}
            os.chdir(d)
            os.environ["PATH"] = os.pathsep.join([sub, oldpath])
            os.environ["HOME"] = os.environ["USERPROFILE"] = d
            try:
                self.assertEqual(os.path.realpath(sp.find_exe("fakeshell-xyz")), os.path.realpath(exe))
            finally:
                os.chdir(old)
                os.environ["PATH"] = oldpath
                for k, v in oldhome.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v

    def test_current_directory_is_not_searched(self):
        with tempfile.TemporaryDirectory() as d:
            exe = os.path.join(d, "fakeshell-xyz" + (".exe" if os.name == "nt" else ""))
            with open(exe, "w") as f:
                f.write("#!/bin/sh\n")
            os.chmod(exe, 0o755)
            old, oldpath = os.getcwd(), os.environ.get("PATH", "")
            os.chdir(d)
            os.environ["PATH"] = os.pathsep.join([".", "", oldpath])
            try:
                self.assertIsNone(sp.find_exe("fakeshell-xyz"))
            finally:
                os.chdir(old)
                os.environ["PATH"] = oldpath


    @unittest.skipUnless(os.name == "nt", "PATHEXT lookup is Windows-only")
    def test_exact_lookup_ignores_wrappers(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as ws:
            with open(os.path.join(d, "fakeshell-xyz.cmd"), "w") as f:  # e.g. a bash.cmd forwarding to WSL
                f.write("@exit /b 0\n")
            old, oldpath = os.getcwd(), os.environ.get("PATH", "")
            os.chdir(ws)
            os.environ["PATH"] = os.pathsep.join([d, oldpath])
            try:
                self.assertIsNotNone(sp.find_exe("fakeshell-xyz"))
                self.assertIsNone(sp.find_exe("fakeshell-xyz.exe", exact=True))
            finally:
                os.chdir(old)
                os.environ["PATH"] = oldpath

    @unittest.skipIf(os.name == "nt", "POSIX signals")
    def test_sigterm_ends_the_running_sample(self):
        import signal as sg
        with tempfile.TemporaryDirectory() as bindir, tempfile.TemporaryDirectory() as ws:
            pidfile = os.path.join(ws, "pid")
            with open(os.path.join(bindir, "bash"), "w") as f:  # a shell whose startup hangs
                f.write("#!/bin/sh\necho $$ > '%s'\nexec sleep 60\n" % pidfile)
            os.chmod(os.path.join(bindir, "bash"), 0o755)
            env = dict(os.environ, PATH=bindir + os.pathsep + "/usr/bin:/bin",
                       EFFICIENT_TOOL_CALLS_CACHE=os.path.join(ws, "c.json"))
            p = subprocess.Popen([sys.executable, os.path.abspath(SCRIPT), "--force"], cwd=ws, env=env,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                deadline = time.time() + 20
                while not os.path.exists(pidfile) and time.time() < deadline:
                    time.sleep(0.05)
                time.sleep(0.2)
                with open(pidfile) as f:
                    child = int(f.read())
                p.send_signal(sg.SIGTERM)
                p.wait(timeout=20)
                time.sleep(0.3)
                with self.assertRaises(OSError):
                    os.kill(child, 0)
            finally:
                if p.poll() is None:
                    p.kill()

    def test_whole_repository_is_skipped_from_a_subdirectory(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, ".git"))
            work = os.path.join(d, "src", "pkg")
            sub = os.path.join(d, ".venv", "bin")  # an env elsewhere in the same repository
            os.makedirs(work)
            os.makedirs(sub)
            exe = os.path.join(sub, "fakeshell-xyz" + (".exe" if os.name == "nt" else ""))
            with open(exe, "w") as f:
                f.write("#!/bin/sh\n")
            os.chmod(exe, 0o755)
            old, oldpath = os.getcwd(), os.environ.get("PATH", "")
            os.chdir(work)
            os.environ["PATH"] = os.pathsep.join([sub, oldpath])
            try:
                self.assertIsNone(sp.find_exe("fakeshell-xyz"))
            finally:
                os.chdir(old)
                os.environ["PATH"] = oldpath

    def test_current_subtree_skipped_in_home_rooted_repo(self):
        with tempfile.TemporaryDirectory() as home:
            os.makedirs(os.path.join(home, ".git"))  # e.g. a dotfiles repository at ~
            work = os.path.join(home, "proj")
            sub = os.path.join(work, ".venv", "bin")
            user = os.path.join(home, ".local", "bin")
            os.makedirs(sub)
            os.makedirs(user)
            ext = ".exe" if os.name == "nt" else ""
            for d, n in ((sub, "fakeshell-xyz"), (user, "usershell-xyz")):
                with open(os.path.join(d, n + ext), "w") as f:
                    f.write("#!/bin/sh\n")
                os.chmod(os.path.join(d, n + ext), 0o755)
            old, oldpath = os.getcwd(), os.environ.get("PATH", "")
            oldhome = {k: os.environ.get(k) for k in ("HOME", "USERPROFILE")}
            os.chdir(work)
            os.environ["PATH"] = os.pathsep.join([sub, user, oldpath])
            os.environ["HOME"] = os.environ["USERPROFILE"] = home
            try:
                self.assertIsNone(sp.find_exe("fakeshell-xyz"))  # the project's env
                self.assertIsNotNone(sp.find_exe("usershell-xyz"))  # user installs still count
            finally:
                os.chdir(old)
                os.environ["PATH"] = oldpath
                for k, v in oldhome.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v

    def test_signal_during_sample_setup_is_deferred(self):
        sp._DEFER.update(on=True, pending=None)
        try:
            sp._exit_on_signal(15, None)  # arrives before the sample can be cleaned up: recorded only
            self.assertEqual(sp._DEFER["pending"], 15)
            with self.assertRaises(SystemExit):
                sp._raise_pending()
        finally:
            sp._DEFER.update(on=False, pending=None)
        with self.assertRaises(SystemExit):
            sp._exit_on_signal(15, None)

    def test_profiles_are_opt_in(self):
        names = [n for n, _f, _a in sp.candidates()]
        self.assertFalse([n for n in names if "(" in n], names)

    @unittest.skipIf(os.name == "nt", "symlinks need privileges on Windows")
    def test_link_into_workspace_is_skipped(self):
        with tempfile.TemporaryDirectory() as ws, tempfile.TemporaryDirectory() as out:
            exe = os.path.join(ws, "fakeshell-xyz")
            with open(exe, "w") as f:
                f.write("#!/bin/sh\n")
            os.chmod(exe, 0o755)
            os.symlink(exe, os.path.join(out, "fakeshell-xyz"))
            old, oldpath = os.getcwd(), os.environ.get("PATH", "")
            os.chdir(ws)
            os.environ["PATH"] = os.pathsep.join([out, oldpath])
            try:
                self.assertIsNone(sp.find_exe("fakeshell-xyz"))
            finally:
                os.chdir(old)
                os.environ["PATH"] = oldpath


class Cache(unittest.TestCase):
    """Cache behaviour with stand-in shells and timings: fast, and runs no real shell or profile."""
    def run_probe(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(sp.main(["--runs", "1"] + list(args)), 0)
        return json.loads(out.getvalue())

    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.tmp = td.name
        self.cache = os.path.join(self.tmp, "sub", "probe.json")
        for sig in ("SIGINT", "SIGTERM", "SIGHUP"):  # main() installs handlers; put the test runner's back
            if hasattr(signal, sig):
                self.addCleanup(signal.signal, getattr(signal, sig), signal.getsignal(getattr(signal, sig)))
        old_env = os.environ.get("EFFICIENT_TOOL_CALLS_CACHE")
        os.environ["EFFICIENT_TOOL_CALLS_CACHE"] = self.cache
        self.addCleanup(lambda: os.environ.__setitem__("EFFICIENT_TOOL_CALLS_CACHE", old_env) if old_env
                        else os.environ.pop("EFFICIENT_TOOL_CALLS_CACHE", None))
        orig_c, orig_t = sp.candidates, sp.time_one
        self.addCleanup(setattr, sp, "candidates", orig_c)
        self.addCleanup(setattr, sp, "time_one", orig_t)
        sp.candidates = lambda *a: [("bash", "posix", ["/fake/bash", "-c", "true"]),
                                 ("pwsh", "powershell", ["/fake/pwsh", "-Command", "exit"])]
        sp.time_one = lambda argv, runs, env=None: {"median_ms": 80 if "bash" in argv[0] else 300, "p90_ms": 400}

    def test_measure_then_reuse_then_expire(self):
        first = self.run_probe()
        self.assertFalse(first["cached"])
        self.assertEqual(set(first["shells"]), {"bash", "pwsh"})
        self.assertTrue(os.path.isfile(self.cache))
        self.assertEqual([f for f in os.listdir(os.path.dirname(self.cache)) if f.endswith(".tmp")], [])
        second = self.run_probe()
        self.assertTrue(second["cached"])
        self.assertEqual(second["measured_at"], first["measured_at"])
        with open(self.cache, encoding="utf-8") as f:
            c = json.load(f)
        c["measured_at"] = int(time.time()) - 8 * 86400
        with open(self.cache, "w", encoding="utf-8") as f:
            json.dump(c, f)
        self.assertFalse(self.run_probe()["cached"])
        self.assertFalse(self.run_probe("--force")["cached"])

    def test_bare_filename_cache(self):
        os.environ["EFFICIENT_TOOL_CALLS_CACHE"] = "probe.json"
        old = os.getcwd()
        os.chdir(self.tmp)
        err = io.StringIO()
        try:
            with contextlib.redirect_stderr(err):
                self.run_probe()
        finally:
            os.chdir(old)
        self.assertNotIn("warning", err.getvalue())
        self.assertTrue(os.path.isfile(os.path.join(self.tmp, "probe.json")))

    def write_cache(self, obj):
        os.makedirs(os.path.dirname(self.cache), exist_ok=True)
        with open(self.cache, "w", encoding="utf-8") as f:
            json.dump(obj, f)

    def test_other_platform_cache_ignored(self):
        good = self.run_probe()
        self.assertTrue(self.run_probe()["cached"])
        good["platform"] = "elsewhere"  # only the platform differs
        self.write_cache(good)
        self.assertFalse(self.run_probe()["cached"])

    def test_more_runs_than_cached_remeasures(self):
        self.run_probe()  # --runs 1
        self.assertTrue(self.run_probe()["cached"])
        self.assertFalse(self.run_probe("--runs", "2")["cached"])

    def test_changed_inventory_remeasures(self):
        good = self.run_probe()
        name = next(iter(good["shells"]))
        good["shells"][name]["path"] = "/elsewhere/" + name  # another install than PATH finds now
        self.write_cache(good)
        self.assertFalse(self.run_probe()["cached"])

    def test_malformed_cache_is_a_miss(self):
        import socket
        for bad in (None, [], {"v": 1, "host": socket.gethostname(), "platform": sys.platform,
                                "measured_at": "yesterday", "shells": {}}):
            self.write_cache(bad)
            self.assertFalse(self.run_probe()["cached"])

    def test_other_host_cache_ignored(self):
        good = self.run_probe()
        self.assertTrue(self.run_probe()["cached"])
        good["host"] = "elsewhere"  # only the host differs
        self.write_cache(good)
        self.assertFalse(self.run_probe()["cached"])

    def test_incomplete_or_empty_cache_is_a_miss(self):
        good = self.run_probe()
        for k in ("recommendation", "fastest_posix"):  # derived fields are recomputed, not trusted
            bad = dict(good); bad.pop(k)
            self.write_cache(bad)
            r = self.run_probe()
            self.assertTrue(r["cached"])
            self.assertEqual(r["recommendation"], good["recommendation"])
        bad = json.loads(json.dumps(good)); next(iter(bad["shells"].values()))["median_ms"] = "fast"
        self.write_cache(bad)
        self.assertFalse(self.run_probe()["cached"])
        bad = dict(good, shells={})
        self.write_cache(bad)
        self.assertFalse(self.run_probe()["cached"])

    def test_malformed_entries_are_a_miss_not_a_crash(self):
        good = self.run_probe()
        name = next(iter(good["shells"]))
        for mutate in (lambda c: c["shells"].__setitem__(name, None),
                       lambda c: c.__setitem__("failed", 5),
                       lambda c: c.__setitem__("failed", [None]),
                       lambda c: c.pop("inventory"),
                       lambda c: c.__setitem__("inventory", [])):
            bad = json.loads(json.dumps(good))
            mutate(bad)
            self.write_cache(bad)
            self.assertFalse(self.run_probe()["cached"])

    def test_failed_shell_with_new_path_remeasures(self):
        orig = sp.inventory
        cached = {"v": sp.CACHE_VERSION, "host": __import__("socket").gethostname(), "platform": sys.platform,
                  "measured_at": int(time.time()), "runs": 5, "failed": ["pwsh"],
                  "shells": {"bash": {"median_ms": 80, "p90_ms": 90, "family": "posix", "path": "/b"}},
                  "inventory": {"bash": "/b", "pwsh": "/old/pwsh"}}
        try:
            sp.inventory = lambda *a: {"bash": "/b", "pwsh": "/old/pwsh"}
            self.assertIsNotNone(sp.valid_cache(json.loads(json.dumps(cached)), 5))
            sp.inventory = lambda *a: {"bash": "/b", "pwsh": "/new/pwsh"}  # a working install now first on PATH
            self.assertIsNone(sp.valid_cache(json.loads(json.dumps(cached)), 5))
        finally:
            sp.inventory = orig

    def test_profile_mode_has_its_own_record(self):
        base = self.run_probe()
        self.assertTrue(self.run_probe("--profiles")["v"])  # writes the -profiles record
        r = self.run_probe()
        self.assertTrue(r["cached"])
        self.assertEqual(r["measured_at"], base["measured_at"])
        self.assertTrue(self.run_probe("--profiles")["cached"])

    def test_all_launches_failing_exits_nonzero(self):
        sp.time_one = lambda argv, runs, env=None: None
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(sp.main(["--runs", "1"]), 1)
        r = json.loads(out.getvalue())
        self.assertIn("failed to start", r["recommendation"])
        self.assertEqual(sorted(r["failed"]), ["bash", "pwsh"])

    def test_failed_refresh_drops_old_success(self):
        self.run_probe()
        self.assertTrue(os.path.isfile(self.cache))
        sp.time_one = lambda argv, runs, env=None: None  # same shells, now none starts
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(sp.main(["--runs", "1", "--force"]), 1)
        self.assertFalse(os.path.exists(self.cache))

    def test_baseline_bash_ignores_bash_env(self):
        seen = {}
        def fake(argv, runs, env=None):
            seen[argv[0]] = env
            return {"median_ms": 1, "p90_ms": 1}
        sp.time_one = fake
        with mock.patch.dict(os.environ, {"BASH_ENV": "/tmp/user-startup.sh"}):
            sp.measure(1)
        self.assertNotIn("BASH_ENV", seen["/fake/bash"])

    def test_pwsh_failure_falls_back_to_51(self):
        sp.candidates = lambda *a: [("bash", "posix", ["b"]), ("pwsh", "powershell", ["p"]),
                                 ("powershell", "powershell-5", ["w"])]
        sp.time_one = lambda argv, runs, env=None: None if argv == ["p"] else {"median_ms": 100 if argv == ["b"] else 400,
                                                                       "p90_ms": 1}
        r = sp.measure(1)
        self.assertEqual(r["failed"], ["pwsh"])
        self.assertEqual(r["fastest_powershell"], "powershell")
        self.assertIn("prefer bash", r["recommendation"])



class RealShells(unittest.TestCase):
    """One end-to-end run against this machine's shells (a minimal system may have none)."""
    def test_probe_runs_and_caches(self):
        with tempfile.TemporaryDirectory() as d:
            env = dict(os.environ, EFFICIENT_TOOL_CALLS_CACHE=os.path.join(d, "probe.json"))
            outs = []
            for _ in range(2):
                p = subprocess.run([sys.executable, SCRIPT, "--runs", "1"], capture_output=True, text=True,
                                   env=env, timeout=300)
                self.assertEqual(p.returncode, 0, p.stderr)
                outs.append(json.loads(p.stdout))
            if not outs[0]["shells"]:
                self.assertFalse(outs[0].get("inventory"), "shells found but every launch failed: %s"
                                 % outs[0].get("failed"))
                self.skipTest("no shell on this machine")
            for v in outs[0]["shells"].values():
                self.assertGreaterEqual(v["median_ms"], 0)
            self.assertTrue(outs[1]["cached"])


if __name__ == "__main__":
    unittest.main()
