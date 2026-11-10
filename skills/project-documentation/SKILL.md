---
name: project-documentation
description: Organize and review project documentation, docs directories, README indexes, authority, and lifecycle metadata. Use for documentation conventions and profiles; technical-writing governs wording in any location.
---

# Project documentation

Make knowledge discoverable, its authority explicit, and its maintenance affordable. This is the convention layer between project principles and scoped profiles.

## Structure and discovery

- Inspect the existing documentation and profiles first. Prefer Markdown and lowercase-kebab-case document names; retain conventional names and paths required by tooling.
- Use root `README.md` as the project entrance. Put deeper knowledge in `docs/`, with topic directories only when content warrants them.
- Every documentation directory, including `docs/`, has `README.md` containing its primary area content and a relative-link index of its direct child documents/directories. A README is useful content, not merely a link list.
- Keep a topic in its directory README while it serves the area's main purpose. Split detail when it has a distinct audience, lifecycle, owner, procedure, or enough detail to obscure orientation. Link it from the README.
- Create reserved directories only when needed. Their meanings are stable; profiles choose the exact tree and may add categories:

| Directory | Reserved meaning |
| --- | --- |
| `decisions/` | Decision rationale and lifecycle records |
| `architecture/` | Current system structure and relationships |
| `guides/` | Task-oriented usage and learning |
| `reference/` | Authoritative lookup material and contracts |
| `operations/` | Operating procedures, recovery, and operational orientation |
| `plans/` | Exploratory proposals and intended work, not current requirements |

An operations README gives orientation and canonical links. Link technical asset ownership, business ownership, and identifiers to their authoritative inventory; do not maintain another manual copy.

## Trust and lifecycle

Read [references/metadata.md](references/metadata.md) when authoring or reviewing content metadata. Use [references/metadata.schema.json](references/metadata.schema.json) to validate parsed YAML frontmatter. Apply it to content-bearing READMEs too.

- Choose one canonical authority for each fact. Link to it rather than copying facts manually across pages.
- A deterministic generated region may reproduce sourced facts if it labels its generator, source, and regeneration method. It is a derivative view, never a second authority. Keep hand-edited content outside the generated region.
- Distinguish current requirements, observed behavior, historical decisions, and exploratory intent. Presentation quality, generation, or an accepted decision alone does not prove implementation or verification.
- Record verification only after checking evidence, by the identified reviewer, for the stated scope. Never fabricate a reviewer or mark content verified because a model wrote it.
- Keep accepted decision reasoning historical. Supersede it with a linked new decision when the choice changes. Preserve the old rationale; correct factual errors transparently.
- Review content when its source, behavior, owner, or scope changes. Clear or narrow stale verification claims. Do not add metadata timestamps.

## Profiles and conflicts

Profiles are explicit, scoped extensions: personal, repository, team, or enterprise. Record their source, applicability, additions, and specific overrides in the project's existing guidance. Profiles can define exact folders, naming, owners, tools, and extra non-temporal metadata under `extensions`.

Combine compatible rules. An applicable explicit override can replace a stated default; neither an organization label nor a more polished document establishes precedence. Use an already declared precedence policy. If two applicable mandatory rules conflict without one, surface both rules and their sources before the dependent edit. Do not silently adopt one. Direct user instructions control the requested scope. Preserve truthful verification, canonical authority, and lifecycle distinctions when extending profiles.

This lightweight schema borrows selected knowledge-management concepts. It does **not** adopt OKF or claim OKF compliance. Do not import an entire external framework or private organizational taxonomy.
