# Repository instructions

`AGENTS.md` at the repository root is the portable file for rules that apply to every task in that repository. Most harnesses read it directly. Some, such as Claude Code, load a file under their own name instead.

## AGENTS.md

Plain Markdown, no frontmatter. Include only what an agent cannot infer from the code and would otherwise get wrong:

| Include | Example |
| --- | --- |
| Commands to build, test, lint, and run | `uv run pytest -q`; which checks CI requires |
| Layout that is not obvious | Where generated code lives, which folders are vendored |
| Conventions no tool enforces | Naming, placement, review or merge rules |
| Boundaries | Files never to edit, actions that need the owner |

- Keep it under about 150 lines. Link to longer docs in the repository instead of copying them.
- Do not restate what a formatter, linter, or CI check enforces; name the check.
- Do not include personal preferences or rules for all repositories. Those belong in the user's instruction files.
- Commands must work from a fresh clone. Update them in the same change that changes the build.
- In a large repository, add an `AGENTS.md` in a subfolder for rules that apply only there. The nearest file wins, so a subfolder file adds to or overrides the root, without repeating it.

## CLAUDE.md

Claude Code loads `CLAUDE.md`. Make it a thin pointer so the rules live in one place:

```markdown
@AGENTS.md
```

- Add lines below the import only for rules that apply to Claude Code alone.
- Never copy `AGENTS.md` content into it. Two copies drift.
- For each subfolder `AGENTS.md` whose rules Claude Code must follow, add a `CLAUDE.md` beside it that imports it (`@AGENTS.md`). Claude Code finds nested files only by its own name, so a root import loads only the root rules.
- The same pattern applies to any harness that reads its own file name: point it at `AGENTS.md`, plus that harness's deltas.

## Checklist

- [ ] Every line is repository-specific and not inferable from the code or tooling.
- [ ] Commands run from a fresh clone.
- [ ] Each `CLAUDE.md` imports the `AGENTS.md` beside it and holds only Claude-only deltas; every subfolder `AGENTS.md` has one.
