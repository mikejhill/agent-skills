# Intent

Make every file Claude references something the user can open with one click.

## Goals

1. File references in Claude's output are navigable links, not inline code.
2. Claude's output uses the clickable file paths Claude Code added in
   [anthropics/claude-code#13008](https://github.com/anthropics/claude-code/issues/13008):
   file paths are emitted as OSC 8 hyperlinks in supporting terminals, so a
   Cmd/Ctrl-click opens the file.

## Requirements

- Applies to Claude only. Other harnesses don't get this file (the local SkillSinc
  config excludes it from every non-Claude route).
- Line numbers are included when pointing at specific code.

## Log

- 2026-11-24: [operator] "Please include a note in my Claude-specific shared
  instructions to include links when creating references to files. This only applies
  to Claude."
- 2026-11-24: [agent] No Claude-only instructions file existed. Added this one,
  modeled on the Codex-only attribution file, and excluded it from non-Claude routes in
  the local SkillSinc config (PR #29).
- 2026-11-24: [operator] Purpose: Claude often references files in `code` spans
  instead of links, which makes them hard to navigate to. Use the clickable file paths
  from anthropics/claude-code#13008 instead.
- 2026-11-24: [agent] Added this intent file. The rule now says explicitly not to
  put file references only in inline code.
