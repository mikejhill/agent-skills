---
name: technical-documentation
description: >-
  Standards for technical writing and project documentation: clear wording,
  procedures, docs/ structure, README indexes, authority, and lifecycle
  metadata. Use when writing or reviewing documentation, specs, reports, or
  procedures in any format, or organizing a docs directory.
---

# Technical documentation

Put the key result, required action, or decisive constraint first, so a reader finds what matters without reading every sentence. Make each fact's authority explicit and its maintenance cheap.

## Writing

- Choose the form by content: numbered steps for procedures, bullets for parallel points, tables for comparisons and mappings, diagrams for relationships, flows, and states. Keep a short paragraph when it explains cause or an exception better than bullets.
- Split documents into review-sized units with one purpose. Start each section with its key point. No repeated summaries or boilerplate.
- Short sentences, active voice, imperatives for instructions, one action per procedural step, condition before action.
- Familiar words, one term per meaning, defined once. No idioms, marketing claims, vague pronouns, or stacked nouns.
- Do not shorten until meaning or uncertainty is lost. Keep needed articles, subjects, and qualifiers.
- Separate requirements, recommendations, observations, and examples. Say who acts and what counts as done. State uncertainty honestly.
- Diagrams answer a concrete question, with consistent labels and a short text equivalent.

## Procedures

1. State purpose, prerequisites, permissions, and inputs before the first step.
2. Put warnings before the hazardous step: hazard, consequence, avoidance.
3. Give exact commands, UI labels, units, and identifiers, with named placeholders.
4. State expected results at checkpoints, plus stop conditions and recovery.
5. Check commands and claims against evidence. Report what was not validated. Never claim a run or review that did not happen.

## Markdown

One title, logical heading levels, descriptive relative links, fenced code with a language, longer outer fences for nested examples. Follow the repository's lint config, and check rendering, links, and diagrams.

## Repository documentation

- Inspect existing docs and conventions first. Keep tool-required names and paths.
- Root `README.md` is the entrance: purpose, audience, quick start, links. Deeper knowledge goes in `docs/`.
- Every docs directory has a `README.md` with real area content plus a relative-link index of its direct children.
- Split a topic out of its README when it has a distinct audience, lifecycle, owner, or procedure, or enough detail to obscure orientation.
- Reserved directories, created only when needed: `decisions/`, `architecture/`, `guides/`, `reference/`, `operations/`, `plans/` ([structure.md](references/structure.md)).
- Lowercase-kebab-case file names.

## Trust and lifecycle

- One canonical source per fact. Link to it instead of copying.
- Generated regions name their generator, source, and regeneration method, and stay a derived view. Keep hand edits outside them.
- Distinguish current requirements, observed behavior, historical decisions, and exploratory plans. Polish, generation, or an accepted decision does not prove implementation.
- Record verification only after checking evidence, by the named reviewer, for a stated scope. Never mark content verified because a model wrote it.
- Supersede an accepted decision with a new linked one. Keep the old rationale.
- Use the frontmatter in [metadata.md](references/metadata.md) for docs that need lifecycle tracking. No timestamp fields.

## References

- [structure.md](references/structure.md): read when creating or reorganizing a `docs/` tree, or applying team or enterprise documentation profiles.
- [metadata.md](references/metadata.md): read when writing or reviewing documentation frontmatter. Validate with [metadata.schema.json](assets/metadata.schema.json).
- [writing.md](references/writing.md): read when a task needs formal Simplified Technical English rules or sources.
