---
name: mermaid-diagrams
description: >-
  Create, edit, review, and export Mermaid diagrams that render correctly on
  GitHub and other renderers: type selection, syntax pitfalls, and PNG/SVG/PDF
  export. Use when a diagram is written as Mermaid or should be.
---

# Mermaid diagrams

Write focused diagrams (one concept each) with descriptive labels, avoiding the syntax that fails silently on GitHub.

## Pick the type

| Concept | Type |
| --- | --- |
| Process, decision tree, pipeline | `flowchart` (`LR` for flows, `TD` for hierarchies) |
| API calls, request and response, handshakes | `sequenceDiagram` |
| Class or interface relationships | `classDiagram` |
| State machine, lifecycle | `stateDiagram-v2` |
| Database schema | `erDiagram` |
| Schedule | `gantt` |
| Proportions | `pie` |
| Topic hierarchy | `mindmap` |
| Chronology, releases | `timeline` |
| Branch strategy | `gitGraph` |
| Priority or risk matrix | `quadrantChart` |
| Requirements traceability | `requirementDiagram` |
| Task board | `kanban` |
| Flow quantities, numeric charts, blocks, cloud topology, packets | `sankey-beta`, `xychart-beta`, `block-beta`, `architecture-beta`, `packet-beta` |

Beta types may not render on GitHub, which can lag the latest Mermaid release. Check the target renderer before using one.

## Rules

- Fence with ` ```mermaid `. Add a one-line text description near each diagram for accessibility.
- At most about 15 nodes. Split bigger systems into several diagrams.
- Descriptive labels (`Auth Service`, not `A`). Node IDs are ASCII letters, digits, and underscores.
- Quote labels containing special characters, parentheses, brackets, or braces: `A["100% done (est.)"]`. Use `<br/>` for line breaks; Mermaid does not wrap.
- ASCII only in syntax: no Unicode arrows, smart quotes, or em dashes.
- One statement per line. No semicolon terminators. Comments start with `%%`.
- `subgraph` and `end` on their own lines; nest at most two levels. For a display name with spaces: `subgraph build [Build Pipeline]`.
- On GitHub, do not rely on `%%{init:}%%` directives, `themeVariables`, or custom CSS. Built-in themes only (`default`, `dark`, `forest`, `neutral`).
- Preview on the target platform. The Live Editor accepts syntax GitHub rejects.

## Export to images

```bash
node "<skill-dir>/scripts/mermaid-export.mjs" input.mmd output.png
node "<skill-dir>/scripts/mermaid-export.mjs" input.mmd output.svg --theme dark --background transparent
node "<skill-dir>/scripts/mermaid-export.mjs" README.md out-dir/ --format png   # every mermaid block
```

It runs a global `mmdc` if present, otherwise `npx --yes @mermaid-js/mermaid-cli`, which downloads the CLI and a headless Chromium on first use. Set the theme with `--theme`, not an init directive. `--help` lists all options.

## References

- [syntax.md](references/syntax.md): read for node shapes, edge types, direction, and subgraph syntax.
- [diagram-types.md](references/diagram-types.md): read when writing a diagram type you have not used in this task. Annotated syntax per type.
- Official docs: [syntax reference](https://mermaid.js.org/intro/syntax-reference.html), [Live Editor](https://mermaid.live/), [mermaid-cli](https://github.com/mermaid-js/mermaid-cli).
