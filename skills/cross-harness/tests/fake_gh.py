#!/usr/bin/env python3
"""Stand-in for `gh` used by smoke_test.py: answers `pr view`, records `pr comment`."""
import json
import os
import sys

argv = sys.argv[1:]
if argv[:2] == ["pr", "view"]:
    num = int(argv[2]) if len(argv) > 2 and argv[2].isdigit() else 7
    print(json.dumps({"number": num, "baseRefName": "main"}))
elif argv[:2] == ["pr", "comment"]:
    body = open(argv[argv.index("--body-file") + 1], encoding="utf-8").read()
    with open(os.environ["FAKE_POSTS"], "a", encoding="utf-8") as f:
        f.write(json.dumps({"pr": argv[2], "body": body}) + "\n")
    print(f"https://github.example/pr/{argv[2]}#comment")
else:
    print("unsupported", argv, file=sys.stderr)
    sys.exit(1)
