#!/usr/bin/env python3
"""Stand-in for `codex` and `claude` used by smoke_test.py.

Behavior is driven by the prompt text (stdin):
  SLEEP=<s>   sleep before answering
  FAIL        exit 1 with an error on stderr
  GRANDCHILD  start a long-lived grandchild and record its pid in $FAKE_PIDS
"""
import json
import os
import re
import subprocess
import sys
import time
import uuid

argv = sys.argv[1:]
flavor = os.environ.get("FAKE_FLAVOR", "codex")
if argv[:1] in (["--version"],):
    print(f"fake-{flavor} 0.0.0")
    sys.exit(0)
if argv[:2] in (["login", "status"], ["auth", "status"]):
    print("Logged in (fake)")
    sys.exit(0)

prompt = "" if sys.stdin is None or sys.stdin.closed else sys.stdin.read()
log = os.environ.get("FAKE_PROMPTS")
if log:
    with open(log, "a", encoding="utf-8") as f:
        f.write(json.dumps({"flavor": flavor, "argv": argv, "prompt": prompt}) + "\n")
pids = os.environ.get("FAKE_PIDS")
if pids:
    with open(pids, "a") as f:
        f.write(f"child {os.getpid()}\n")
if "GRANDCHILD" in prompt:
    gc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(600)"])
    with open(pids, "a") as f:
        f.write(f"grandchild {gc.pid}\n")
m = re.search(r"SLEEP=(\d+(?:\.\d+)?)", prompt)
if m:
    time.sleep(float(m.group(1)))
if "FAIL" in prompt:
    print("simulated failure", file=sys.stderr)
    sys.exit(1)

session = str(uuid.uuid4())
answer = f"fake {flavor} answer; args={' '.join(a for a in argv if not a.startswith('/'))}; cwd={os.getcwd()}"
if flavor == "codex":
    out = argv[argv.index("-o") + 1]
    print(json.dumps({"type": "thread.started", "thread_id": session}), flush=True)
    print(json.dumps({"type": "turn.completed"}), flush=True)
    with open(out, "w") as f:
        f.write(answer)
else:
    print(json.dumps({"type": "result", "is_error": False, "result": answer,
                      "session_id": session, "total_cost_usd": 0.01}))
