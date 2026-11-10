# ADR Examples

## Overview

This document provides complete, annotated examples of well-structured ADRs. Each example demonstrates effective use of the template, with annotations explaining why specific choices were made. These preserved examples use a historical metadata format, including dates and legacy field names. Learn from their rationale, not their frontmatter: use adr-template.md and project-documentation for new metadata. Do not copy the example identities or dates into real records.

## Example 1: Full Template — Async Order Processing

This example demonstrates the full template with all sections populated. It shows how decision drivers trace through to the outcome and how consequences differ from option-level pros/cons.

````markdown
---
status: accepted
date: 2025-09-15
decision-makers:
  - Sarah Chen (Backend Tech Lead)
  - Marcus Rivera (Staff Engineer)
consulted:
  - Priya Patel (Database Specialist)
  - James Wu (SRE Lead)
informed:
  - Backend Team
  - Platform Team
supersedes: []
superseded-by: []
---

# ADR-0015: Adopt asynchronous processing for payment validation

## Context and Problem Statement

Our order service validates payments synchronously within the HTTP request
cycle. At current traffic (2K orders/hour), p99 latency is 850ms — within our
1-second SLA. Load testing against Q3 traffic projections (8K orders/hour)
shows p99 exceeding 2.4 seconds, breaching the SLA. We must decouple payment
validation from the request path before the Q3 traffic increase begins in
approximately 12 weeks.

## Decision Drivers

- Payment validation p99 must remain under 1 second at 8K orders/hour
  (SLA commitment to enterprise customers)
- PCI DSS compliance requires payment data to stay within the payment
  service's network boundary
- The team has no production experience with message queue systems;
  onboarding cost is a real factor
- Solution must be operational within 12 weeks (Q3 deadline)
- Infrastructure runs on AWS; new components must integrate with the
  existing VPC and monitoring stack

## Considered Options

1. Async processing with Amazon SQS
2. Async processing with self-managed RabbitMQ
3. Synchronous optimization (connection pooling, caching, query tuning)

## Decision Outcome

Chosen option: "Async processing with Amazon SQS", because it satisfies the
latency SLA at projected volume (Driver 1) without requiring the team to manage
message broker infrastructure (reducing risk given Driver 3 and Driver 4), and
SQS operates within the existing AWS VPC (Driver 5). PCI compliance is
maintained by keeping payment payloads within the service boundary and using
SQS server-side encryption (Driver 2).

### Consequences

- **Good**: HTTP response time drops to ~120ms (order acknowledgment only);
  payment validation runs asynchronously, keeping the overall flow within the
  1-second SLA at 8K+ orders/hour
- **Good**: SQS is a managed service — no broker patching, scaling, or failover
  management, freeing the team to focus on business logic during the 12-week
  timeline
- **Bad**: Introduces eventual consistency; order status shows "pending" for up
  to 30 seconds during async payment validation, requiring UI changes to
  communicate the processing state to customers
- **Bad**: Adds a new failure mode — SQS delivery failures or consumer
  processing lag could delay payment validation; requires dead-letter queue
  monitoring and alerting that does not currently exist
- **Neutral**: Adds SQS as an infrastructure dependency; operational surface
  area increases, but AWS's managed SLA (99.999% durability) offsets the risk

### Confirmation

- Integration test validates that order creation returns HTTP 202 and payment
  validation completes via SQS within 30 seconds under simulated load
- CloudWatch alarm on SQS dead-letter queue depth (threshold: >10 messages
  in 5 minutes)
- Load test at 8K orders/hour validates p99 < 1 second before production
  deployment

## Options Detail

### Async processing with Amazon SQS

Decouple payment validation by publishing order events to an SQS queue. A
dedicated consumer service processes payments asynchronously. Orders return
HTTP 202 (Accepted) immediately; clients poll or receive webhooks for payment
status updates.

- **Good**: Removes payment validation from the HTTP request path, keeping
  API p99 under 200ms at 8K orders/hour (satisfies the latency SLA — Driver 1)
- **Good**: Managed service with 99.999% durability; no infrastructure
  management overhead (supports the 12-week timeline constraint)
- **Good**: Native AWS integration with existing VPC, IAM, and CloudWatch
  (satisfies the AWS infrastructure constraint)
- **Good**: Built-in dead-letter queue for failed message handling
- **Bad**: Team must learn async messaging patterns — estimated 2-week
  ramp-up period
- **Bad**: Maximum message size is 256KB; unusually large payment payloads
  would require S3 offloading

### Async processing with self-managed RabbitMQ

Deploy RabbitMQ on EC2 or ECS. Same async pattern as SQS but with a
self-managed broker offering more routing flexibility.

- **Good**: Rich routing patterns (topic exchanges, headers-based routing)
  for potential future use cases beyond payment validation
- **Good**: No message size limitation; supports large payloads natively
- **Bad**: Requires cluster management, patching, and failover configuration
  — estimated 4 weeks of infrastructure work, which combined with ramp-up
  time risks the 12-week deadline
- **Bad**: Team has zero RabbitMQ experience; operational risk is higher
  than a managed service
- **Bad**: Self-managed availability (~99.9%) is lower than SQS (99.999%)
  without significant engineering investment in HA configuration

### Synchronous optimization

Keep the synchronous architecture but optimize: add connection pooling for the
payment gateway, cache frequently-used validation rules, and optimize database
queries in the payment path.

- **Good**: No architectural change; lowest ramp-up cost and risk
- **Good**: Can be implemented incrementally within the 12-week timeline
- **Bad**: Load testing shows optimization reduces p99 to ~1.8 seconds at
  8K orders/hour — still above the 1-second SLA (fails the primary driver)
- **Bad**: Optimization gains are fragile; adding new payment methods or
  validation rules could regress latency unpredictably

## More Information

- **Related ADRs**: ADR-0008 (AWS as primary cloud provider), ADR-0011
  (Payment service boundary definition)
- **Re-evaluate when**: Request volume exceeds 50K orders/hour (may need
  Kinesis or Kafka for higher throughput); if the team adopts event-driven
  architecture broadly (may consolidate on a different messaging platform)
- **Implementation notes**: Start with a single SQS standard queue. Use
  visibility timeout of 60 seconds for payment processing. Implement
  idempotency keys on the consumer to handle at-least-once delivery.
- **References**: AWS SQS documentation, internal load test results
  (wiki/load-test-q3-2025)
````

### Why this full-template example works

- **Context names specific metrics** (2K orders/hour, 850ms p99, 8K projected) and a concrete deadline (12 weeks). A reader in 2027 can evaluate whether these constraints still apply.
- **Decision drivers are falsifiable.** Each can be tested against an option: "Does Option X keep p99 under 1 second at 8K orders/hour?" Yes or no.
- **The rejected synchronous option has hard data.** Load testing showed 1.8 seconds — above the SLA. This prevents future re-litigation: the option was evaluated with evidence, not dismissed with opinion.
- **Consequences include system-level effects** beyond the option's inherent properties. "Introduces eventual consistency in order status" is a consequence of choosing async *in this system* — it would not appear as a generic "con" of SQS.
- **Confirmation is automated and specific.** Integration tests, CloudWatch alarms, and load tests — not "we'll review it in code review."
- **Re-evaluation triggers are concrete.** "50K orders/hour" and "team adopts event-driven architecture broadly" — not "if things change."

## Example 2: Minimal Template — State Management Library

This example demonstrates the minimal template variant for a lower-impact, easily-reversible decision affecting a single application.

````markdown
---
status: accepted
date: 2025-08-22
decision-makers:
  - Alex Torres (Frontend Lead)
consulted:
  - Jamie Park (Senior Frontend Engineer)
---

# ADR-0019: Use Zustand for client-side state management

## Context and Problem Statement

The customer portal React application (47 components, projected to exceed 100
by year-end) currently uses prop drilling and React Context for shared state.
State management logic is becoming duplicated across feature modules, and
tracing data flow through nested Context providers is increasingly difficult
during debugging. We need a dedicated state management solution for shared
application state (authenticated user, cart, feature flags).

## Considered Options

1. Zustand
2. Redux Toolkit

## Decision Outcome

Chosen option: "Zustand", because it provides centralized state management
with approximately 60% less boilerplate than Redux Toolkit for equivalent
functionality, and the team can adopt it incrementally (store-by-store) without
refactoring existing Context-based state. The application's state complexity
(primarily UI state and cached API responses) does not require Redux's
middleware ecosystem or devtools.

### Consequences

- **Good**: Store definitions are ~60% less code than equivalent Redux slices;
  new feature state can be added in minutes rather than requiring
  action/reducer/selector boilerplate
- **Good**: Incremental adoption allows migrating one Context provider at a
  time, reducing risk of a large-scale refactor
- **Bad**: Zustand's ecosystem is smaller than Redux's; if state complexity
  grows to require sagas, middleware chains, or time-travel debugging, we may
  need to reconsider
- **Bad**: Less community documentation and fewer Stack Overflow answers
  compared to Redux; onboarding junior developers may take slightly longer
````

### Why this minimal-template example works

- **Uses the minimal template appropriately.** The decision affects one application, is reversible (swapping state libraries is work but not catastrophic), and has no cross-team implications. The full Options Detail section would add length without proportional value.
- **Decision Drivers are folded into Context.** The minimal template permits omitting a separate Decision Drivers section when drivers are implicit in the Context. Here, the drivers (duplicated state logic, difficult debugging, need for incremental adoption) are stated directly in the problem description. For a higher-impact decision using the minimal template, explicitly listing drivers would be preferable.
- **Context includes specific numbers** (47 components, projected 100) that justify why the decision is needed now.
- **The justification is specific.** "60% less boilerplate" and "incremental adoption" are concrete claims, not vague assertions about being "better."
- **Bad consequences are honest.** The smaller ecosystem and documentation gap are real trade-offs, not handwaved away.

## Example 3: Post-Hoc ADR — Documenting an Existing Decision

This example demonstrates honest documentation of a decision made without formal evaluation, written after the fact to preserve institutional knowledge.

````markdown
---
status: accepted
date: 2024-06-01
decision-makers:
  - David Okonkwo (CTO)
  - Lisa Huang (VP Engineering)
consulted: []
informed:
  - Engineering Organization
supersedes: []
superseded-by: []
---

# ADR-0001: Use Python as the primary backend language

## Context and Problem Statement

This ADR was written in February 2025 to document a decision made in
approximately June 2024 during the company's founding. The rationale below
reflects our best reconstruction of the original reasoning based on
conversations with David Okonkwo and Lisa Huang, and review of early commit
history and hiring documents.

When the company was founded, the two-person engineering team needed to choose
a primary backend language for the SaaS platform. The decision needed to
support rapid prototyping, hiring in a competitive market, and a data-heavy
product that processes customer analytics.

## Decision Drivers

- Rapid prototyping speed was critical: the team needed a working product
  within 3 months to secure Series A funding
- Both founders had extensive Python experience (5+ years each)
- The product involves significant data processing (pandas, NumPy) that
  benefits from Python's data science ecosystem
- Hiring pipeline needed to attract generalist backend engineers in a
  competitive market; Python has a large candidate pool

## Considered Options

1. Python
2. Go
3. TypeScript (Node.js)

## Decision Outcome

Chosen option: "Python", because both founders were highly productive in
Python (Driver 2), the data science ecosystem directly supported the product's
core functionality (Driver 3), and the 3-month timeline made familiarity the
decisive factor (Driver 1).

Note: This decision was made informally during the company's first week. No
structured evaluation of alternatives occurred at the time. The alternatives
listed above were discussed briefly but not evaluated with the rigor this
template suggests. We document them here for completeness and to support
future re-evaluation.

### Consequences

- **Good**: The founding team shipped a working product in 10 weeks, meeting
  the Series A timeline
- **Good**: Python's data ecosystem (pandas, NumPy, scikit-learn) enabled
  the analytics pipeline without external services or language bridges
- **Good**: Hiring pipeline has been strong; 80% of backend candidates in
  our market are comfortable with Python
- **Bad**: API response times average 45ms — adequate but not competitive
  with Go-based alternatives (relevant if we move toward real-time features)
- **Bad**: Dynamic typing has led to production type errors that a statically
  typed language would have caught at compile time; partially mitigated by
  adopting mypy in 2025
- **Neutral**: The team has grown to 12 Python engineers; switching languages
  now would be a multi-quarter effort regardless of technical merits

## More Information

- **Re-evaluate when**: If real-time features require sub-10ms response
  times; if the team grows beyond 30 engineers (type safety becomes more
  critical at scale); if a major service is being built from scratch
  (opportunity to introduce a second language for specific workloads)
- **References**: Early commit history (2024-06 through 2024-08), Series A
  pitch deck (internal drive)
````

### Why this post-hoc example works

- **Uses the full template with optional sections omitted.** This ADR includes Decision Drivers (full template) but omits Options Detail because the alternatives were not formally evaluated at the time (per the MAY clause in SKILL.md). Confirmation is omitted because no automated verification is practical for a language choice made months ago. Post-hoc is not a separate template — it is the full or minimal template with honest acknowledgment of the reconstructed rationale.
- **`consulted: []` is correct** even though the post-hoc author interviewed David and Lisa. The `consulted` field records who was consulted during the *original* decision, not during the ADR writing process. David and Lisa are listed as `decision-makers` because they made the original choice.
- **Honestly states it is post-hoc.** The first paragraph of Context explicitly says when the ADR was written vs. when the decision was made, and how the rationale was reconstructed.
- **Acknowledges the informal process.** The Decision Outcome section notes that no structured evaluation occurred. This is more valuable than pretending a formal process happened.
- **Consequences include hindsight observations.** The "Bad" consequences (response times, type errors) reflect what the team learned after living with the decision — this is one area where post-hoc ADRs can be *more* informative than upfront ones.
- **Re-evaluation triggers are specific and forward-looking.** Despite being a historical record, it still serves its purpose: telling future readers when to reconsider.
