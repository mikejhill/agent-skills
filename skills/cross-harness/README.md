# cross-harness

Hands a code review, prompt, or task from Claude Code to Codex, or from Codex to Claude Code, and brings back the result. Every job runs as one short-lived process tree that is cleaned up when it finishes, fails, times out, or its caller exits.

Works only in Claude Code and Codex, because it drives those two CLIs.

## Use

Runs only when you or your instruction files ask for the other agent. Examples:

- "Have Codex review my uncommitted changes."
- "Ask Claude to try this prompt and compare."

The repository's optional Codex review gate (`instructions/codex-via-cross-harness.instructions.md`) and the `codex-*` prompts use this skill too.

## Requirements

- Python 3.8+ (stdlib only).
- The other agent's CLI (`codex` or `claude`) installed and signed in.

## Security and side effects

- Reviews are read-only unless you ask for fixes (`--fix`). `--post` publishes review results to GitHub or GitLab.
- Job state and logs live in your user cache folder under `agent-skills/cross-harness` (Windows `%LOCALAPPDATA%`, macOS `~/Library/Caches`, Linux `${XDG_CACHE_HOME:-~/.cache}`), overridable with `CROSS_HARNESS_HOME`.
- Each job uses the other agent's account and usage limits. Whether a second model's review helps is not consistently proven.
