# Intent

Let Claude Code and Codex hand reviews, prompts, and tasks to each other on explicit
request, without the leaked processes, locked folders, and Windows breakage of the
Codex plugin for Claude Code (`openai/codex-plugin-cc`, unmaintained since 2026-07).

## Goals

1. Nothing outlives its job. A job's whole process tree ends when the job finishes,
   fails, is cancelled, hits its time limit, or its calling session exits, including
   crashes with no clean shutdown. No user directory stays held as a cwd.
2. Both directions with the same guarantees: Codex from Claude Code, and Claude Code
   from Codex.
3. Used only on request. The description stays neutral, and invocation comes from the
   user or their instruction files.
4. Reviews follow each harness's own review tool (`codex exec review`, Claude's
   `/code-review`), with its arguments passed through, including fixes. Posting to
   GitHub or GitLab is a common feature for every target.
5. Honest about value. Document that cross-model review and delegation help
   sometimes, and that this is not consistently proven.
6. A skill, not a plugin: progressive disclosure, no hooks, no session environment
   writes, harness-neutral layout, stdlib-only Python.
7. Files and images both ways (operator, 2026-11-25): the caller can hand the other
   agent images and files, have Codex generate images, and get the produced files back
   at a known path.
8. Thin over the CLIs: `codex exec` and `codex exec review`, `claude -p`. Pass models,
   efforts, and extra flags through unchanged, so CLI updates don't break the skill.

## Requirements

- A skill, not a plugin, replacing the Codex plugin for Claude Code, whose detached broker processes leaked and locked worktree folders on Windows.
- Neutral description: used only when the user or their instructions ask for the other agent.
- Reviews use each harness's native review tool by default (Codex `codex exec review`, Claude `/code-review` through `claude -p`), with arguments passed through verbatim; fixes allowed with `--fix`.
- Posting review results to GitHub or GitLab (`--post`) is a common feature for every target.
- Document that the benefit of cross-model review is unproven.
- No process outlives its job, on Windows and POSIX.
- "I would like to be able to use Codex from Claude in order to build images, among other multimodal features." (operator, 2026-11-25)

## Design decisions

- **No broker or daemon.** One CLI process per job. That rules out the largest class
  of upstream bugs: orphaned brokers, shared-broker teardown killing other sessions,
  stale broker reuse, and refresh-token burn from long-lived app-servers.
- **Supervisor per job**, with its cwd in the state home. Windows: the supervisor
  joins a Job Object with `KILL_ON_JOB_CLOSE`, so the OS ends the tree if it dies.
  POSIX: new process group, `PR_SET_PDEATHSIG` on Linux, and a sweep on every
  invocation that kills groups of jobs whose supervisor vanished.
- **Owner watchdog:** the nearest `claude` or `codex` ancestor, checked by pid and
  start time (guards against pid reuse).
- **Start, then wait.** Every caller's shell has a command time limit, so `wait` is a
  restartable poll and killing it never affects the job.
- **Prompts over stdin; the reviewer reads `git` itself.** No size limits, no
  command-line quoting, and no untracked-file or symlink crashes.
- **Per-job state** in the standard user cache (`<user-cache>/agent-skills/cross-harness`),
  keyed by job id and recording owner, target directory, and pids. Never keyed by cwd.
- **Native reviews by default** (user decision, 2026-11-18): the harness's reviewer runs
  as designed. Edit tools are granted only with `--fix`, and posting happens only with
  `--post`. Claude's native review gets unrestricted Bash (its pipelines need it), so it is
  not a hard read-only guarantee; prompt reviews are. Tasks are
  read-only unless `--write`. No `--trust` or bypass flags.
- **Media through the CLIs, not around them** (2026-11-25). Inputs: Codex `-i` for
  images, ended with `--` because `-i` is variadic, and a prompt preamble with absolute
  paths for everything else (Claude Code's Read tool views images). Outputs: Codex's
  image tool saves to `$CODEX_HOME/generated_images/<thread_id>/` from outside the
  model's sandbox, and `--json` carries no image event, so the supervisor copies that
  folder's new files after the run instead of asking the model to copy them (which
  needed sandbox escalation in a live test). Other files need `--write`, which makes
  `--out` writable. Read-only stays read-only: a scoped Claude allow rule could not
  override broader allows from the user's settings, so it was dropped for fail-closed
  denies. Outputs are found by comparing before and after snapshots, not timestamps,
  and copies are exclusive, link-free, and watched by the job's watchdog.
- **One nesting level** (`CROSS_HARNESS_DEPTH`), to stop ping-pong loops.

## Upstream problems addressed

Verified against the upstream source (1.0.6) and its issue tracker, against a user's
2026-11-14 session report, and on a Windows 11 machine on 2026-11-18. That check
found a leaked broker tree of 33 processes holding a deleted review worktree, plus 4
more orphaned trees.

| Upstream problem | Evidence | Here |
|---|---|---|
| Detached broker with no idle timeout or parent watchdog; stopped only by `SessionEnd` with the same cwd | `broker-lifecycle.mjs` (`detached`, `unref`); #543, #605, #450, #791, #380, #782, #753 | No broker. Job Object or process group, owner watchdog, time limit |
| Broker and app-server hold the review directory as cwd, so Windows can't delete worktrees | session report; laptop check | Supervisor cwd is the state home; the child holds the directory only while it runs |
| App-server never reaps child shells or MCP servers | ~40 to 45 leaked descendants observed | Tree reaped at job end |
| `shell: SHELL \|\| true` on Windows, DEP0190, `.cmd` ENOENT | `app-server.mjs:194`; #32, #46, #67, #85, #832 | Direct spawn of `.exe`, or `node` plus the shim's script |
| `SessionStart` appends env exports without dedup, overflowing Windows' 8191-character limit | #528, #322, #254, #562 | No hooks; no env-file writes |
| Shared broker torn down by one session's end kills others' jobs | #540, #612 | Jobs are independent |
| Jobs stuck `running` after worker death | #164, #222, #517, #639, #698 | Supervisor records every exit path; sweep marks `lost` |
| Bash tool timeout kills foreground runs mid-turn | #542, #634 | Start and wait; the job is detached from the tool call |
| Unbounded prompts and diffs (ENOBUFS, 1 MB limit, EISDIR on untracked) | #11, #405, #69, #14, #65 | Reviewer reads `git` itself; prompt over stdin |
| Hard-coded model and effort lists go stale | #468, #751, #703 | Pass-through |
| Forced sandbox breaks on some platforms | #349, #482, #505, #240 | `--sandbox inherit` |
| Review sessions pollute the user's Codex history | #282 | `--ephemeral` and `--no-session-persistence` |
| Reviewing an untrusted branch loads its hooks and settings | sendbird/cc-plugin-codex#117 | `--isolate` |
| Long-lived app-server burns the single-use ChatGPT refresh token | #789 | Short-lived CLI per job |
| Cleanup needs agents to kill processes, which auto mode blocks | session report | `cancel`, `cleanup`, `status` |

## Fork survey (2026-11-18)

314 public forks were fetched; about 10 carry substantive changes. The most active
(CBEPX, Edo771977, Sjotie, y-cruce, ShallowDream724) spent hundreds of commits on:
broker idle self-termination and verified tree kills; pid-identity checks against
pid reuse; atomic state writes and dead-worker detection; Windows spawn without a
shell; env-file dedup; model and effort pass-through; sandbox overrides; and
declining MCP elicitations that hang headless runs. Most of that complexity
exists to keep a persistent broker alive and correct. This skill drops the broker
instead. The reverse-direction plugin (`sendbird/cc-plugin-codex`) already uses
one `claude -p` per job with the prompt on stdin, which this skill follows.

## Log

- 2026-11-18: [agent] Created from a user request and session report. Built `xh.py`
  (supervisor, containment, owner watchdog, sweep, start and wait, resume),
  review prompts, references, and `tests/smoke_test.py` with a fake agent
  (13 lifecycle cases). Live-tested the Claude Code target: adversarial review,
  write task, and resume.
- 2026-11-18: [agent] Verified on Windows 11 (Python 3.13, codex-cli 0.159, Claude Code
  2.1.322): smoke test 13/13; live Codex plain and adversarial reviews, Claude
  adversarial review, Codex write task. Cancelling a live Codex task ended all 16
  processes in its tree (codex.exe, MCP servers, shells, conhost), and the repo folder
  was deletable at once. Added a hint for rejected default models (`model_not_found`).
- 2026-11-18: [agent] Reviews reworked at the user's request: native reviewer by default
  (Claude `/code-review` via `claude -p`, verified headless; Codex `exec review`),
  `--native-args` passed through verbatim, `--fix` (native for Claude, a follow-up write
  step for Codex and for prompt reviews), `--post` (Claude `--comment`, otherwise
  `gh pr comment` or `glab mr note`), and `--pr`. Fixed two races found by repeated
  test runs: a shared write-probe file, and a sweep overwriting a just-finished job.
  Only the supervisor writes `job.json` while it lives.
- 2026-11-18: [agent] Windows retest at e7fb80d: smoke test 17/17 three times; live Claude
  native review (`/code-review low feat`) and Codex native review with `--fix` (fix step ran
  and reported; review found nothing to change).
- 2026-11-22: [agent] Migrated to the `skill-development` standard: README added, `compatibility` set (the skill only works between Claude Code and Codex), and a Requirements section added from the operator's recorded decisions. No changes to the body or script. Known deviation: job state lives in `<state-home>/cross-harness/` rather than under an `agent-skills/` parent; moving it would strand running jobs.
- 2026-11-22: [operator] "Do not worry about any existing resources, running brokers/jobs, orphaning content as it sits today, etc. Just make everything match the ideal end state." Job state moved to `<user-cache>/agent-skills/cross-harness/` on every OS (was `%LOCALAPPDATA%\cross-harness` or `${XDG_STATE_HOME:-~/.local/state}/cross-harness`); relative env roots ignored. Old job state is no longer read.
- 2026-11-22: [agent] Second Codex review fixes: home directory resolved only when the cache env root is missing or relative.
- 2026-11-22: [operator] "Some agent executions leave stale clones around, such as the agent-skills-review-20261122 directory. Figure out what causes these and devise a solution." [agent] Root cause: review delegation briefs cloned into the user's project folder and said to leave the clone in place, with no removal step; paths.md told skills to leave temp files in place. Added an agent scratch root (`<system-temp>/agent-skills/scratch/`) with dated names, removal at task end, and a 7-day sweep, defined in the `temp-storage` instruction.
- 2026-11-22: [agent] Codex round 1 on PR #25 (8 findings, all fixed): sweep selects by name timestamp, skips `KEEP` dirs and links, and validates the root; scratch excludes worktrees and state; uncommitted fixes are kept before removal; the no-tests advice moved to cross-harness troubleshooting; Unix uses `<scratch-root>`.
- 2026-11-22: [agent] Codex round 2 on PR #25 (6 findings, all fixed): the sweep also creates the root (private on Unix), rejects links along the whole Windows path, keeps Git checkouts with uncommitted or unpushed work, and compares full timestamps; the upstream-free check is `git log HEAD --branches --not --remotes`; troubleshooting says to report sandbox-owned folders, not escalate.
- 2026-11-22: [agent] Removed named references to other skills and instruction files; adjacent concerns are now described by capability ("any ... standards the user has") so the skill stands alone.
- 2026-11-22: [agent] Codex review: kept the safeguards that used to come from the removed references inline (review-clone cleanup checks and scratch defaults, credential file permissions, verifying release prerequisites).
- 2026-11-22: [agent] Codex round 2: inline scratch-path validation (absolute base, no links, resolved path inside root) and the remote-tracking fetch of PR heads, both previously supplied by the removed instruction reference.
- 2026-11-22: [agent] Codex round 3: the review-clone procedure is now fully self-contained. It covers per-OS scratch roots with trust checks, host-specific PR/MR refspecs, the `KEEP` retention marker, and the unique-work check before removal.
- 2026-11-22: [agent] Codex round 4: replaced the inline scratch-storage policy with composition. Clones go wherever the user's scratch rules say, preferring a worktree of their clone, and otherwise the agent asks. The skill keeps only review-specific steps: remote-tracking PR/MR fetch, a HEAD-matches-ref check each round, and unique-work checks (including submodules) before removing what it created.
- 2026-11-25: [operator] "I would like to be able to use Codex from Claude in order to build images, among other multimodal features. Does our cross-harness skill support images and other files or media as input and output? If not, please design an effective solution and implement it." [agent] It did not: prompts were text-only and only the final message came back. Probed codex-cli 0.170.0 on Windows: `-i/--image` is variadic and swallows a following `-` or prompt, and silently ignores missing files; `exec resume` accepts `-i`; `image_generation` is a stable, default-on feature; generated PNGs land in `generated_images/<thread_id>/` even under read-only, and the `--json` stream has no image event. Added `task --attach` and `--out`, automatic collection of Codex's generated images, an `artifacts` result field, `references/media.md`, and smoke tests.
- 2026-11-25: [agent] Live check on Windows: attach, resume, and `--out` worked; an image-only answer was reported as failed, and Codex's Windows `workspace-write` sandbox needed escalation to write. Astra review (9 findings) and fixes: read-only Claude keeps full write denies (no scoped allow); image-only answers succeed; exclusive, non-replacing copies with errors reported; snapshot-based output detection with a scan cap and watchdog checks; comma paths listed instead of `-i`; `--add-dir` instead of replacing writable roots, and no change under `--sandbox inherit`; TOML-safe paths.
- 2026-11-25: [agent] Astra round 2 (10 findings, all addressed): copies recheck the outputs folder and source identity and are created 0o666; scans count every entry, skip junctions, and warn when cut off; copies check the watchdog per chunk; `--add-dir` on the parent `exec` for resume instead of replacing writable roots; inherit-mode prompts name `--out`; thread-name resumes fall back to timestamps with a warning; docs say other files need `--write` and `--out`.
