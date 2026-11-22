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

    def test_single_family(self):
        r = sp.recommend(sh("bash", "posix", 5))
        self.assertIn("nothing to choose", r["recommendation"])


class Cache(unittest.TestCase):
    def run_probe(self, *args):
        p = subprocess.run([sys.executable, SCRIPT, "--runs", "1"] + list(args), capture_output=True,
                           text=True, env=self.env, timeout=120)
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout)

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
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
        c["measured_at"] = int(time.time()) - 31 * 86400
        with open(self.cache, "w", encoding="utf-8") as f:
            json.dump(c, f)
        self.assertFalse(self.run_probe()["cached"])
        self.assertFalse(self.run_probe("--force")["cached"])

    def test_other_host_cache_ignored(self):
        os.makedirs(os.path.dirname(self.cache))
        with open(self.cache, "w", encoding="utf-8") as f:
            json.dump({"v": 1, "host": "elsewhere", "measured_at": int(time.time()), "shells": {}}, f)
        self.assertFalse(self.run_probe()["cached"])


if __name__ == "__main__":
    unittest.main()
