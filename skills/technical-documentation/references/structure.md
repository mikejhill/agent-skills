# Documentation structure and profiles

## Reserved directories

Create only when needed. Their meanings are fixed; profiles choose the exact tree and may add categories.

| Directory | Holds |
| --- | --- |
| `decisions/` | Decision rationale and lifecycle records (ADRs) |
| `architecture/` | Current system structure and relationships |
| `guides/` | Task-oriented usage and learning |
| `reference/` | Authoritative lookup material and contracts |
| `operations/` | Operating procedures, recovery, and operational orientation |
| `plans/` | Exploratory proposals and intended work, not current requirements |

An operations README gives orientation and canonical links. Link asset ownership, business ownership, and identifiers to their authoritative inventory instead of keeping a manual copy.

## Profiles

Profiles are explicit, scoped extensions: personal, repository, team, or enterprise. Record each profile's source, applicability, additions, and overrides in the project's existing guidance. Profiles can set exact folders, naming, owners, tools, and extra non-temporal metadata under `extensions`.

- Combine compatible rules. An applicable explicit override replaces a stated default.
- An organization label or a more polished document does not set precedence. Use a declared precedence policy.
- If two applicable mandatory rules conflict and no policy decides, show both with their sources before the dependent edit. Do not pick one silently.
- Direct user instructions control the requested scope.
- Extensions never weaken truthful verification, canonical authority, or lifecycle distinctions.
- Do not import a whole external framework or a private organizational taxonomy. This schema borrows selected knowledge-management ideas and does not claim OKF compliance.
