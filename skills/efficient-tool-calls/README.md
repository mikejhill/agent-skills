# efficient-tool-calls

Makes agents spend fewer, cheaper tool calls on long multi-step work, such as browser automation or CLI sequences: batch predictable steps, keep commands short, bound output, avoid sleep-polling, and pick the shell that starts fastest on your machine.

## Use

Loads automatically when a task will need many shell or tool calls. The agent may run `scripts/shell_probe.py` once to time the shells on your machine.

## Requirements

- Python 3.8+ for the shell probe (stdlib only). A manual fallback works without Python.

## Results

- The probe result is cached for 7 days in your user cache folder (`agent-skills/efficient-tool-calls/shell-probe.json`), or at `EFFICIENT_TOOL_CALLS_CACHE`.
- The skill only recommends a shell. It never changes your harness settings.
- `--profiles` also times login shells, which runs your shell startup scripts several times.
