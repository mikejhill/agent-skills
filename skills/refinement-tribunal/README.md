# refinement-tribunal

Refines an existing document (a skill, prompt, spec, policy, or docs page) through repeated review by three independent subagents: a harsh critic, an advocate that protects what works, and a researcher that never sees the text. It stops when the content stops improving.

## Use

Runs only when you invoke it by name, with a file or text, for example: "Use refinement-tribunal on docs/runbook.md, focusing on actionability."

## Requirements

- A harness that can run subagents, and access to a top-tier model.

## Results

- The refined content, written back to the file only after you see a diff summary (where the harness can ask).
- A refinement log per iteration and the reason it stopped.

## Cost

About three top-tier subagent calls per iteration; 2-5 iterations, default 3. Long documents add calls per section.
