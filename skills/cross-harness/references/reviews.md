# Reviews

## Modes

| Mode | When | Codex | Claude Code |
|---|---|---|---|
| Native (default) | Plain review, optionally with `--native-args` | `codex exec review --base/--commit/--uncommitted` with Codex's own sandbox config | `/code-review [native args] [--fix] [--comment] [target]` over stdin to `claude -p` |
| Prompt | `--adversarial`, `--focus`, or `--no-native` (also Claude with `--commit`) | `codex exec -s read-only` with `assets/prompts/` | `claude -p` with the same prompt, read-only tools |

The native mode follows each harness's own review behavior. Claude's native review
runs with Bash allowed, because `/code-review` uses shell pipelines, and edit tools
denied unless `--fix` is given. That isn't a hard read-only boundary. Use
`--no-native` when the review must not be able to change anything. The skill passes the
arguments in `--native-args` through verbatim (for example `"high"`, `"xhigh
--max-findings all"`), so new review levels and flags work without changes here.
The skill does not validate them. Codex's `exec review` takes scope flags only and
no custom instructions, so custom instructions need the prompt mode. Set
`CROSS_HARNESS_CLAUDE_REVIEW_CMD` to use a different Claude command name (for
example `/review`) if it is renamed.

Verified on 2026-11-18 with codex-cli 0.159 and 0.170, and Claude Code 2.1.322
and 2.1.327.

## Scope

| Want | Options |
|---|---|
| A PR or MR | `--pr N`. It looks up the base with `gh` or `glab` and uses `origin/<base>` |
| The current branch's PR or MR | `--post` alone finds it |
| A branch against its base | `--base main` (for Claude native, the current branch is the target and `/code-review` picks its base) |
| One commit | `--commit SHA` |
| Uncommitted work | default, or `--uncommitted` |
| A different repository | `--cwd PATH` |

For a PR, check out its head branch or a worktree of it first. Fetch, so the base is
current, and fetch the PR head into a remote-tracking ref, not only `FETCH_HEAD`, so the
cleanup check below sees its commits as already on a remote: on GitHub
`git fetch origin refs/pull/<n>/head:refs/remotes/origin/pr/<n>`, on GitLab
`git fetch origin refs/merge-requests/<n>/head:refs/remotes/origin/mr/<n>`.

With no local clone, clone into `<scratch-root>/clone-<YYYYMMDD-HHMMSS>-<slug>/`. Use the
user's scratch location if their instructions define one. Otherwise:

| OS | Scratch root | Before creating or removing anything there |
| --- | --- | --- |
| Windows | `%TEMP%\agent-skills\scratch\` | `%TEMP%` is absolute and inside `%USERPROFILE%`; no component from `%USERPROFILE%` down to the clone is a junction or symlink |
| macOS, Linux | `${TMPDIR:-/tmp}/agent-skills-<uid>/scratch/` | the base is absolute and either owned by you and not group- or other-writable, or sticky and owned by you or `root`; `agent-skills-<uid>` is owned by you with mode `0700`; no component below the base is a symlink |

In both cases the resolved clone path must sit inside the scratch root. If a check fails,
stop and report it.

Reuse the clone for later review rounds. If it must outlive seven days, or the user asks to
keep it, create an empty `KEEP` file in it so stale-scratch sweeps skip it, and remove the
file when retention ends. When the review loop ends, also when it fails, remove the clone
only after confirming it holds no unique work: no working-tree edits, untracked files,
stashes, or unpushed commits (`git log HEAD --branches --not --remotes`). After a `--fix`
run, move the fixes to the intended checkout first. If any check finds unique work or
cannot run, keep the clone (with `KEEP`) and report its path.

## Fixing: `--fix`

- Claude native: `/code-review --fix`. Claude applies the fixes it judges sound
  inside its own review (edit permission is granted for this run).
- Every other case: after a successful review, a second step runs the same target
  with write access (`codex exec -s workspace-write`, or Claude with
  `acceptEdits`). Its brief is `assets/prompts/fix.txt` plus the findings. The step
  verifies each finding before fixing it, runs the tests, and never commits or
  pushes. `xh.py result JOB --fix-report` prints its report.

Edits land in `--cwd`. Use a worktree when you don't want them mixed with your own work.

## Posting: `--post`

- Claude native: `/code-review --comment <pr>`. Claude posts in its own format.
- Every other case: the skill posts one summary comment, the review plus the fix
  report if there was one, with `gh pr comment` (GitHub) or `glab mr note` (GitLab).
  The host comes from the `origin` remote. Set `CROSS_HARNESS_REVIEW_HOST` to
  override it.
- The poster's CLI must be installed and signed in. Posting is public and can't be
  quietly undone, so post only when the user or their instructions ask for it.

## Handling findings

The reviewer's output is a claim, not a fact.

1. Read every finding against the code. Confirm or refute it from the source, and
   run a test when that is cheap.
2. Report confirmed, refuted (with the reason), and unclear findings to the user.
   Don't drop a finding silently.
3. If the review also fixed or posted, say what changed and where it was posted.
4. A clean review is weak evidence. Name the scope that was reviewed, and don't
   present it as proof of correctness.

## Recurring review instructions

An instruction such as "run a Codex review on every PR before marking it ready, and
post it" means:

```text
xh.py review -t codex --pr <n> --post --label "PR #<n>"
xh.py wait <job> --timeout 90          # repeat while the exit code is 3
```

Then verify the findings, address the confirmed ones if the instruction says to, and
mark the PR ready.
