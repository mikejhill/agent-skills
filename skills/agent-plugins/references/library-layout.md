# Library layout

How to add plugins to a library repository, especially one that already ships loose skills or other context to harnesses directly.

## Patterns

| Pattern | Layout | Fits |
| --- | --- | --- |
| Repository is one plugin | Root `plugin.json`, root `skills/`, catalogs listing source `./` | A small, cohesive library installed all or nothing |
| Plugins folder | `plugins/<name>/` each a full plugin; catalogs at the root | Several independent plugins with their own versions |
| Curated subsets of a shared folder | Root `skills/` stays the source; plugins select from it | A library that also distributes loose skills |

## Curated subsets

Agent Plugins 1.0 has fixed locations, so a 1.0 plugin cannot select skills from a shared folder by path. Choose one:

1. **Generate.** A build step copies the selected components into `plugins/<name>/` and writes its manifests. Commit the output or publish it from CI. Keep one source of truth and never hand-edit the copies; add a check that fails when they drift.
2. **Harness path fields.** Claude catalog entries with a `skills` list and no per-plugin `.claude-plugin/plugin.json`, or Copilot legacy path fields, can select from the shared folder without copies. This serves only those harnesses.
3. **Symlinks inside the plugin root.** Allowed by 1.0 only when the target stays inside the root, so they cannot reach a shared folder above it.

Prefer generating when 1.0 clients are targets.

## Coexisting with loose distribution

- Plugins and loose copies of the same skill conflict when both are installed: the harness loads two skills with the same description. Tell users to choose one channel per skill, and say so in the README.
- Plugin components are namespaced by plugin in some harnesses (`<plugin>:<skill>`), loose skills are not. Instructions that refer to a skill by name must work both ways, or avoid naming it.
- Keep harness-specific plugin content (extension namespaces, `.claude-plugin/`) out of the shared, harness-neutral folders.
- Content that a consumer project needs only for itself stays in that project, not in a library plugin.

## Repository checks

- Run the checker on the repository root in CI, plus each target harness's validator where one exists (`claude plugin validate --strict`).
- Lint every JSON manifest and catalog. Test one local install per target harness before a release.
