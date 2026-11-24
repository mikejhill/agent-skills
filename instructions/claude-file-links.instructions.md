---
name: Claude File Links
description: Link every file Claude references so the user can open it directly.
applyTo: "**"
---

# Claude file links

When Claude references a file in a reply, plan, review, or summary:

- Make the reference a clickable link to the file. Never put a file reference only in inline code (backticks); the user cannot open it from there.
- Use a Markdown link with a relative path, or a bare `path:line` reference that the terminal turns into a hyperlink.
- Include the line number when pointing at specific code.
