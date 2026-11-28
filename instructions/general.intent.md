# Intent

Give every agent, in every harness and repository, one uniform communication style: blunt, concise, analytically rigorous, and consistent in typography.

## Goals

1. Agent output is direct and free of filler, engagement language, and closures.
2. Agents ask questions only for genuinely blocking ambiguity, with specific choices.
3. Typography is consistent across agents and repositories.

## Requirements

- Applies to all work (`applyTo: "**"`); task-specific instructions win on conflict.
- [agent] Core principles: blunt phrasing, no filler, precise references, no engagement language, stop after delivering value.
- Oxford comma in lists of three or more.
- Title Case for titles, headings, and labels, as in "Why Shortcuts Get Lost" (user's example).
  - Lowercase only articles, conjunctions, and short prepositions that are not the first or last word.
  - Split a title with a colon, never a semicolon, as in "Set Brightness: Swap Low" (user's example).
  - Scope stays explicit: sentences, commit messages, and PR titles keep their own conventions, so the rule never recases prose or conflicts with commit conventions.
  - Each rule carries a concrete example, because a bare "use Title Case" gets ignored.
- [agent] Questions use the harness's structured ask tool, 2–6 specific choices, a recommended default when there is a basis, and never ask for inferable information.

## Log

- 2026-11-27: [agent] Created this intent file. Added the Title Case rule because agents kept writing titles and headers in sentence case ("Why shortcuts get lost") and splitting labels with semicolons ("Set brightness; swap low").
