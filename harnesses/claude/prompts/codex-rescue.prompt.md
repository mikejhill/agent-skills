---
description: Hand an investigation or fix to Codex through cross-harness
argument-hint: "[--read-only] [--resume <job>] [--model <m>] [--effort <e>] [what Codex should investigate, solve, or continue]"
---

# Codex Rescue

Delegate this to Codex with the `cross-harness` skill (load it first). The script is
normally `~/.claude/skills/cross-harness/scripts/xh.py`.

Request: `$ARGUMENTS`

1. Write a self-contained brief from the request and this conversation: the goal,
   the relevant files and commands, what was already tried, and the answer shape
   you need back. Codex sees none of this conversation. Save it to a temporary file.
2. Run `xh.py task -t codex --prompt-file <brief>`. Add `--write` unless
   `--read-only` was given or the request is investigation only. Pass through
   `--resume`, `--model`, and `--effort`. For a large write task, suggest a separate
   git worktree first (see the skill's delegation reference).
3. Poll with `xh.py wait <job> --timeout 90`, repeating while the exit code is 3.
4. Show Codex's final message verbatim, then list the files it changed (`git status`),
   with your assessment.
