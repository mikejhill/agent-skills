# browser-control

Lets the agent use your own open Chrome, Edge, or Brave, with your real tabs and signed-in sessions, to do tasks: read and extract from pages, navigate, click, fill forms, run multi-step workflows, take screenshots or PDFs, and inspect cookies, network traffic, or the console.

## Use

Loads automatically when a task needs your browser. Examples:

- "Take over my GitHub tab and list the open PRs."
- "Download last month's invoices from the vendor portal I'm logged in to."

## Requirements

- Python 3.8+ (stdlib only).
- Chrome, Edge, or Brave with remote debugging allowed for the running instance: open `edge://inspect/#remote-debugging` or `chrome://inspect/#remote-debugging` and turn on **Allow remote debugging for this browser instance**. No restart is needed.
- The agent must run on the same machine as the browser.

## Security and side effects

- The browser asks you to approve the connection. One approval covers a background broker that keeps running across tasks until you say you are done, the browser closes, or it has been idle for 60 minutes. The browser shows a "being controlled" banner meanwhile.
- The agent acts with your logins. It reads first and confirms before actions with side effects such as submitting, buying, or deleting. It never prints cookies or tokens.
- Broker state lives in your user cache folder (`agent-skills/browser-control`), overridable with `BROWSER_CONTROL_HOME`.
