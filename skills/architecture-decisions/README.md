# architecture-decisions

Writes and reviews Architecture Decision Records (ADRs) that capture why a decision was made: the drivers, the real alternatives, and the trade-offs. It researches the codebase and critiques each draft with independent subagents, so the analysis is not shaped by a preferred answer.

## Use

Loads when you ask for an ADR, or invoke it with a topic. Examples:

- "Write an ADR for moving order processing to a queue."
- "Review docs/decisions/0007-use-postgres.md."

You make the decision. The agent confirms the framing with you before drafting, and confirms decision-makers before marking an ADR accepted.

## Results

One Markdown file, `NNNN-title-with-dashes.md`, in the project's ADR folder (default `docs/decisions/`), with status `proposed`.

## Requirements

- Works best in harnesses that can run subagents. Without them, research and critique run as separate passes.
