# mermaid-diagrams

Helps the agent write Mermaid diagrams that render correctly on GitHub and elsewhere, and export them to PNG, SVG, or PDF.

## Use

Loads automatically when the agent creates, edits, or reviews a Mermaid diagram. Examples:

- "Add a sequence diagram of the login flow to the README."
- "Export the diagrams in docs/architecture.md as PNGs."

## Requirements

- Export only: Node.js 18.19+. The first export downloads `@mermaid-js/mermaid-cli` and a headless Chromium through `npx` (network access needed), unless `mmdc` is already installed.

## Results

Diagrams are written inline in Markdown. Exports go to the output path you give; temporary files are deleted afterwards.
