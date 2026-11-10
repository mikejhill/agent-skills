# ADR Template Reference

## Overview

This document defines the ADR template used by the adr-generation skill and provides field-by-field guidance for filling each section. The template synthesizes the strongest elements from Nygard's original format, MADR (Markdown Any Decision Records), and Merson's rationale-focused extensions into a single, practical structure.

## Complete Template

````markdown
---
type: decision
status: proposed
authority: informative
criticality: normal
review:
  status: unreviewed
extensions:
  decision_makers: []
  consulted: []
  informed: []
  supersedes: []
---

# ADR-NNNN: [Present-tense verb] [specific decision]

## Context and Problem Statement

[2–4 sentences describing the situation that requires a decision. State what part of the system is affected, what problem or opportunity exists, and why the decision must be made now. Make the scope explicit.]

## Decision Drivers

- [Specific, falsifiable force or constraint that shapes the decision]
- [Another driver — requirement, quality attribute, team constraint, timeline]
- [Continue as needed; 3–6 drivers is typical]

## Considered Options

1. [Option A — brief name]
2. [Option B — brief name]
3. [Option C — brief name]

## Decision Outcome

Chosen option: "[Option N]", because [1–2 sentence justification that traces back to specific decision drivers listed above].

### Consequences

- **Good**: [Specific benefit with mechanism — what improves, how, for whom]
- **Good**: [Another benefit]
- **Bad**: [Specific trade-off with mechanism — what degrades, what risk is accepted]
- **Neutral**: [Side-effect that is neither clearly positive nor negative]

### Confirmation

[How will compliance with this decision be verified? Examples: code review checklist item, automated linter rule, architectural fitness function, CI pipeline check, manual audit schedule. State "No automated verification practical" if none applies.]

## Options Detail

### [Option A]

[1–2 sentences describing the option.]

- **Good**: [Pro tied to a decision driver]
- **Good**: [Another pro]
- **Bad**: [Con tied to a decision driver]
- **Bad**: [Another con]

### [Option B]

[1–2 sentences describing the option.]

- **Good**: [Pro]
- **Bad**: [Con — include the specific reason this option was rejected]

### [Option C]

[1–2 sentences describing the option.]

- **Good**: [Pro]
- **Bad**: [Con]

## More Information

- **Related ADRs**: [Links to related decisions, e.g., "ADR-0012: Adopt event-driven messaging"]
- **Re-evaluate when**: [Specific trigger conditions, e.g., "if request volume exceeds 10K/sec" or "if the team adds a dedicated DBA"]
- **Implementation notes**: [Brief guidance for the implementing team, if applicable]
- **References**: [Links to external resources, RFCs, vendor docs, benchmark results]
````

## Minimal Template Variant

Use this for low-impact decisions where the full template adds unnecessary overhead. A decision qualifies as low-impact when it affects a single component, is easily reversible, and has no cross-team implications.

Decision Drivers MAY be omitted in the minimal template when they are implicit in the Context section. If drivers are not immediately obvious from context, include them.

````markdown
---
type: decision
status: proposed
authority: informative
criticality: normal
review:
  status: unreviewed
extensions:
  decision_makers: []
  consulted: []
  informed: []
  supersedes: []
---

# ADR-NNNN: [Present-tense verb] [specific decision]

## Context and Problem Statement

[2–4 sentences]

## Considered Options

1. [Option A]
2. [Option B]

## Decision Outcome

Chosen option: "[Option N]", because [justification].

### Consequences

- **Good**: [Benefit]
- **Bad**: [Trade-off]
````

## Field-by-Field Guidance

### Frontmatter

#### `status`

Records the current lifecycle state of the ADR. Set to `proposed` when drafting. Only the human team changes status to `accepted`.

| Status | Meaning | When to use |
| --- | --- | --- |
| `proposed` | Draft under discussion; not yet agreed upon | Initial creation, circulating for feedback |
| `accepted` | Team has agreed; decision is in effect | After team review and explicit approval |
| `superseded` | Replaced by a newer ADR | A new ADR explicitly replaces this one |
| `rejected` | Considered and explicitly not adopted | Decision was proposed but the team chose not to proceed |

When marking `superseded`, set `superseded_by` to a relative successor link and `authority: historical`. Rejected decisions are historical too. Proposed decisions are informative or exploratory; accepted decisions are informative or normative. Record retirement of a prior decision through a superseding record when needed; do not rewrite its rationale.

#### Chronology and review

Do not add timestamp metadata to new ADRs. Keep relevant historical dates and uncertainty in sourced Context text; preserve existing record facts. Apply the project-documentation metadata schema. `generated.by` identifies generation, not review. Add `verified` only for actual checks, evidence, and scope; acceptance alone does not verify implementation.

#### `extensions.decision_makers`

People who had authority to approve or reject the decision. Include name and role. List only people who actually participated — do not pad the list for appearances.

**Use named individuals, not team names.** Decision-makers MUST be identified by name because:

- Accountability requires a person, not a group. "The backend team decided" provides no contact point when the decision needs re-evaluation.
- When revisiting a decision 18 months later, you need to talk to the person who weighed the trade-offs — not "the platform team," which may have entirely different members.
- Named individuals create a natural limit on the decision-maker list, preventing the anti-pattern of listing every team as a stakeholder.

**Exception:** The `informed` field MAY use team or group names (e.g., "Backend Team", "#platform-channel") because that field tracks communication, not authority.

**Guidance on who to include:**

- The person who proposed the decision
- Technical leads or architects with authority over the affected area
- Product owners, if the decision has product-level implications
- Do not list the entire team unless the entire team actively participated in the decision
- For enterprise-level ADRs, include the architect or engineering leader who owns the decision, not the committee name

Format: `Name (Role)` — e.g., `Alice Chen (Backend Tech Lead)`, `Bob Kim (Staff Engineer)`

#### `extensions.consulted`

People whose expertise informed the decision but who did not have final approval authority. These are domain experts, affected team members, or specialists who provided input.

**Guidance on who to include:**

- Domain experts with relevant technical knowledge
- Members of teams directly affected by the decision
- People who will implement or maintain the resulting system
- Security, compliance, or legal specialists when relevant

An empty `consulted` list is acceptable for decisions where a single decision-maker had sufficient expertise and no other teams were affected. For decisions with cross-team impact, an empty list is a red flag — the [Advice Process](adr-guide.md#the-advice-process) requires seeking input from affected parties.

#### `extensions.informed`

People or groups who were notified of the decision after it was made. This can include team names, mailing lists, or Slack channels. This field exists for traceability — it records who knows about the decision.

#### `extensions.supersedes` / `superseded_by`

`extensions.supersedes` lists relative links to replaced ADRs. `superseded_by` is the required top-level relative successor link when status is `superseded`. These are links, not duplicate decision facts. Profiles may define the non-temporal extension fields above; never invent participants or approval evidence.

### Title

Format: `ADR-NNNN: [Present-tense verb] [specific decision]`

The title is a complete statement of what was decided. It uses a present-tense imperative verb because the ADR describes the decision as it takes effect.

**Good titles:**

- `ADR-0015: Use PostgreSQL for transactional data storage`
- `ADR-0023: Adopt event-driven architecture for order processing`
- `ADR-0031: Replace custom auth with Auth0 for identity management`
- `ADR-0042: Store session data in Redis instead of database`

**Bad titles:**

- `ADR-0015: Database` (too vague — which aspect of the database?)
- `ADR-0023: Architecture decision` (tautological — every ADR is an architecture decision)
- `ADR-0031: We should probably switch to Auth0` (hedging, not a decision)
- `ADR-0042: Session management improvements` (describes a topic, not a decision)

### Context and Problem Statement

2–4 sentences that answer three questions:

1. **What is the current situation?** Describe the system state, project phase, or technical reality that frames the decision.
2. **What problem or opportunity exists?** State what needs to change or what question needs answering.
3. **Why must this be decided now?** State the trigger — a deadline, a dependency, a scaling limit, a new requirement.

The scope of the decision MUST be clear from this section. Name the specific components, services, or system boundaries affected. Do not leave the reader guessing whether this ADR applies to a single microservice or the entire platform.

**Example:**

> Our order processing service currently handles payment validation synchronously within the HTTP request cycle. At current traffic (2K orders/hour), p99 latency is 850ms — within our 1-second SLA. Traffic projections for Q3 show 8K orders/hour, which will push p99 beyond the SLA. We must decide how to decouple payment validation from the request path before the Q3 traffic increase.

### Decision Drivers

Specific, falsifiable forces or constraints that shape the decision. Each driver is a statement that can be evaluated as true or false against a given option.

**Strong drivers** (specific and falsifiable):

- "Payment validation must complete within the 1-second p99 SLA at 8K orders/hour"
- "The team has zero experience with message queues; onboarding time is a cost"
- "PCI compliance requires payment data to remain within the payment service boundary"
- "The solution must be operational before Q3 traffic increase (12 weeks)"

**Weak drivers** (vague, unfalsifiable):

- "Performance" (which metric? what threshold?)
- "Maintainability" (for whom? measured how?)
- "We need something scalable" (to what scale? by when?)
- "Best practices" (according to whom? applied to what?)

3–6 drivers is typical. Fewer than 3 suggests the decision is not well-understood. More than 8 suggests the problem needs decomposition.

### Considered Options

List 2–4 genuine alternatives. Each option must be a choice a reasonable, informed team could make. Do not include strawmen (options listed only to be rejected) or non-options (options that clearly violate a stated constraint).

If only one option exists, reconsider whether an ADR is the right artifact. A decision with no alternatives is a constraint — document it as a requirement, not a decision.

**When more than 4 options exist:** Too many options signal that the decision space has not been sufficiently narrowed. Group similar options (e.g., "Managed message queue" encompassing SQS, CloudAMQP, and Confluent Cloud), or add a constraint to eliminate infeasible options before writing the ADR. If 5+ genuinely distinct options remain after grouping, document the narrowing criteria in the Context section and present the top 3–4.

### Decision Outcome

State the chosen option and a 1–2 sentence justification that explicitly references decision drivers. The justification traces the choice back to the forces that shaped it.

**Good:** "Chosen option: 'Async processing with RabbitMQ', because it satisfies the latency SLA at projected volume (Driver 1) and keeps payment data within the service boundary (Driver 3), despite the team ramp-up cost (Driver 2)."

**Bad:** "Chosen option: 'RabbitMQ', because it's the best solution for our needs." (Vague. Which needs? How was "best" determined?)

### Consequences

Explicit trade-offs categorized as Good, Bad, or Neutral. Each consequence states a specific mechanism — not a vague claim.

| Category | What to write | Example |
| --- | --- | --- |
| **Good** | Specific benefit with mechanism | "Payment validation latency drops from the request-path p99 (850ms) to async processing, keeping the HTTP response under 200ms at 8K orders/hour" |
| **Bad** | Specific trade-off with accepted risk | "Introduces eventual consistency: order status may show 'pending' for up to 30 seconds while payment validates asynchronously" |
| **Neutral** | Side-effect that is neither positive nor negative | "Adds RabbitMQ as an infrastructure dependency, increasing operational surface area without changing reliability characteristics" |

Every ADR MUST have at least one Good and one Bad consequence. A decision with no downsides has not been analyzed honestly.

#### How Consequences differ from Options Detail

The Options Detail section and the Consequences section both use Good/Bad/Neutral labels, but they serve different purposes:

- **Options Detail** is a **comparative evaluation tool**. It lists the inherent pros and cons of each option in isolation, enabling side-by-side comparison during the decision process. These are properties of the option itself — "RabbitMQ supports flexible routing" is true regardless of which system adopts it.
- **Consequences** is a **commitment statement**. It documents what the team accepts by choosing this option *within this specific system context*. Consequences often include emergent effects that arise from the interaction between the option and the existing architecture — "Introduces eventual consistency in order status" is not an inherent property of SQS; it is a consequence of decoupling payment validation from the synchronous request path in *this* system.

In practice, some entries will overlap. An inherent "Good" of the chosen option in Options Detail may also appear as a "Good" consequence. This is acceptable. The key distinction: Options Detail informs the decision; Consequences document what the team is signing up for after making it. Consequences may also include second-order effects, operational changes, or organizational impacts that do not appear in any individual option's pros/cons list.

### Confirmation

How the team will verify that the decision is being followed. This is the bridge between deciding and doing. Confirmation appears under Decision Outcome for template compatibility with MADR; conceptually, it addresses post-decision verification. Options include:

- **Automated enforcement**: Linter rule, CI check, architectural fitness function
- **Code review checklist**: Specific item reviewers check for
- **Manual audit**: Periodic review on a defined schedule
- **Monitoring/alerting**: Metric threshold that detects drift from the decision
- **None practical**: State this explicitly rather than leaving the section empty

### Options Detail

Expanded analysis of each option. For each, provide:

- 1–2 sentences describing what the option entails
- Pros tagged as **Good** — each tied to a decision driver where possible
- Cons tagged as **Bad** — each tied to a decision driver where possible

Write each option's analysis independently. Do not frame the prose to make the chosen option look better or the rejected options look worse.

### More Information

Links, references, and forward-looking guidance:

- **Related ADRs**: Decisions that affect or are affected by this one
- **Re-evaluate when**: Specific trigger conditions for revisiting the decision (traffic thresholds, team changes, technology milestones, contract renewals)
- **Implementation notes**: Brief technical guidance for the implementing team (not a full design doc — just key pointers)
- **References**: External resources that informed the decision (vendor docs, benchmarks, RFCs, blog posts)
