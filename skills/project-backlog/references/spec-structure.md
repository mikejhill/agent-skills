# Specification Structure

This document defines the canonical structure for `spec.md` files managed
by the `project-backlog` skill. All specifications follow this structure to
ensure consistency, completeness, and readability.

## Section Order

Sections appear in this order. Required sections are always present.
Optional sections are included when relevant and omitted when not
applicable.

| # | Section | Required | Purpose |
|---|---------|----------|---------|
| 1 | Problem / Purpose | Yes | Why this exists |
| 2 | Scope | Yes | What is and is not included |
| 3 | Goals | Yes | What success looks like |
| 4 | Use Cases | Yes | Who benefits and how |
| 5 | Requirements and Constraints | Yes | Hard boundaries that shape the design |
| 6 | Proposed Design | Yes | How the solution works |
| 7 | Cross-Cutting Concerns | Optional | Quality attributes and operational factors |
| 8 | Risks and Trade-offs | Optional | Known risks and accepted trade-offs |
| 9 | Open Questions | Optional | Unresolved decisions |
| 10 | Alternatives Considered | Optional | Rejected approaches and why |
| 11 | References | Optional | Prior art, links, related work |

## Section Guidance

### Problem / Purpose

State the problem being solved, the motivation for solving it, and the
value it provides. A reader should understand *why this spec exists* after
reading this section alone.

Write this as prose — one to three paragraphs. Avoid jumping into solution
details.

### Scope

#### In-Scope

What this specification covers. List the features, behaviors, or
deliverables that are part of this work.

#### Out-of-Scope

What is explicitly excluded and why. This prevents scope creep and sets
expectations for reviewers and implementers.

### Goals

Define what success looks like. These should be concrete and verifiable —
not vague aspirations. A goal is good if someone can look at the finished
implementation and say "yes, this was achieved" or "no, this was not."

Use a bulleted list. Each goal should be a single clear statement.

### Use Cases

Concrete scenarios that illustrate the intended behavior or usage patterns.
Each use case describes a user or system, what they do, and what outcome
they expect.

Use cases ground the design in reality. They also serve as the basis for
acceptance criteria during implementation.

### Requirements and Constraints

Hard requirements and boundaries that the design must satisfy. These are
non-negotiable conditions — technical limitations, business rules,
compatibility requirements, performance thresholds, or standards that must
be met.

This section comes before the design because the design should be read in
the context of what it must obey.

### Proposed Design

The core of the specification — how the solution works. This section
describes architecture, components, data flow, APIs, directory structures,
algorithms, or whatever is relevant to the solution.

The word "proposed" signals that this is the selected approach, not a
finalized contract. Designs evolve during implementation.

Structure this section with sub-headings as needed for clarity. For complex
designs, consider splitting detailed component descriptions into auxiliary
files and referencing them from here.

### Cross-Cutting Concerns

Quality attributes and operational factors that influence implementation
but are not hard constraints. Include only the subsections that are relevant
to this specification. Common concerns:

| Concern | When to include |
|---------|----------------|
| **Security** | Authentication, authorization, secrets, input validation |
| **Performance** | Latency, throughput, resource usage targets |
| **Scalability** | Growth expectations, horizontal/vertical scaling |
| **Compatibility** | OS support, version compatibility, migration from existing systems |
| **Reliability** | Failure modes, error handling, recovery, resilience |
| **Observability** | Logging, metrics, monitoring, debugging support |
| **Migration / Rollout** | How to transition from current state, phased rollout |
| **Maintenance / Operations** | Ongoing upkeep, configuration management |
| **Testing Strategy** | Test approach, coverage expectations, test types |
| **Accessibility** | CLI usability, documentation clarity, internationalization |
| **Usability / Developer Experience** | API ergonomics, CLI UX, documentation quality |

### Risks and Trade-offs

Known risks and accepted trade-offs. For each risk, describe the impact and
any mitigation strategy. For each trade-off, explain what was sacrificed
and why.

This section helps implementers and future readers understand the
deliberate compromises in the design.

### Open Questions

Unresolved decisions that need input before or during implementation. Each
question should be specific enough that it can be answered with a concrete
decision.

When a question is resolved, move the answer into the relevant section of
the spec and remove the question. An empty Open Questions section (or its
absence) signals that the spec is fully resolved.

### Alternatives Considered

Approaches that were evaluated and rejected, with a brief explanation of
why they were not chosen. This prevents future contributors from revisiting
decisions that have already been made and documents the reasoning behind
the selected design.

### References

Links to prior art, related projects, external documentation, standards,
or any material that informed or supports this specification.

## Template

```markdown
# [Title]

## Problem / Purpose

[Why this exists. The problem, the motivation, and the value.]

## Scope

### In-Scope

- [Feature or deliverable]
- [Feature or deliverable]

### Out-of-Scope

- [Exclusion and why]

## Goals

- [Concrete, verifiable goal]
- [Concrete, verifiable goal]

## Use Cases

### [Use Case Name]

[Actor] does [action] and expects [outcome].

## Requirements and Constraints

- [Hard requirement or boundary]
- [Hard requirement or boundary]

## Proposed Design

[Architecture, components, approach, key decisions.]

## Cross-Cutting Concerns

### [Relevant Concern]

[How this concern is addressed.]

## Risks and Trade-offs

- **[Risk]:** [Impact and mitigation.]
- **[Trade-off]:** [What was sacrificed and why.]

## Open Questions

- [Specific unresolved decision]

## Alternatives Considered

### [Alternative Name]

[What it was and why it was rejected.]

## References

- [Link or citation]
```
