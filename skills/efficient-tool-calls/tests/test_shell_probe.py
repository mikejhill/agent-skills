#!/usr/bin/env python3
"""Tests for shell_probe.py: recommendation logic, caching, and a real measurement."""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest

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


class Cache(unittest.TestCase):
    def run_probe(self, *args):
        p = subprocess.run([sys.executable, SCRIPT, "--runs", "1"] + list(args), capture_output=True,
                           text=True, env=self.env, timeout=120)
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout)

    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.tmp = td.name
        self.cache = os.path.join(self.tmp, "sub", "probe.json")
        self.env = dict(os.environ, EFFICIENT_TOOL_CALLS_CACHE=self.cache)

    def test_measure_then_reuse_then_expire(self):
        first = self.run_probe()
        self.assertFalse(first["cached"])
        self.assertTrue(first["shells"], "no shell measured")
        for v in first["shells"].values():
            self.assertGreaterEqual(v["median_ms"], 0)
        self.assertTrue(os.path.isfile(self.cache))
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
        self.env["EFFICIENT_TOOL_CALLS_CACHE"] = "probe.json"
        p = subprocess.run([sys.executable, os.path.abspath(SCRIPT), "--runs", "1"], capture_output=True,
                           text=True, env=self.env, cwd=self.tmp, timeout=120)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("warning", p.stderr)
        self.assertTrue(os.path.isfile(os.path.join(self.tmp, "probe.json")))

    def write_cache(self, obj):
        os.makedirs(os.path.dirname(self.cache), exist_ok=True)
        with open(self.cache, "w", encoding="utf-8") as f:
            json.dump(obj, f)

    def test_other_platform_cache_ignored(self):
        import socket
        self.write_cache({"v": 1, "host": socket.gethostname(), "platform": "elsewhere",
                          "measured_at": int(time.time()), "shells": {}})
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

    def test_pwsh_failure_falls_back_to_51(self):
        orig_c, orig_t = sp.candidates, sp.time_one
        sp.candidates = lambda: [("bash", "posix", ["b"]), ("pwsh", "powershell", ["p"]),
                                 ("powershell", "powershell-5", ["w"])]
        sp.time_one = lambda argv, runs: None if argv == ["p"] else {"median_ms": 100 if argv == ["b"] else 400,
                                                                       "p90_ms": 1}
        try:
            r = sp.measure(1)
        finally:
            sp.candidates, sp.time_one = orig_c, orig_t
        self.assertEqual(r["failed"], ["pwsh"])
        self.assertEqual(r["fastest_powershell"], "powershell")
        self.assertIn("prefer bash", r["recommendation"])


if __name__ == "__main__":
    unittest.main()
