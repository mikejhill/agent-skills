# web-auth-bridge

Guides the agent in using the [web-auth-bridge](https://github.com/mikejhill/web-auth-bridge) Python library, so skill CLIs can log in to websites that need a real browser (WAF challenges, SAML, MFA), cache the session, and then call the site's APIs directly.

## Use

Loads automatically when the agent builds a skill or CLI that must authenticate to such a site. Example: "Build a CLI that downloads my reports from the vendor portal."

## Requirements

- Python 3.11+ with uv, Playwright, and a Playwright browser (`playwright install chromium`).
- Network access to GitHub to install the library.

## Security and side effects

- You create the credentials file yourself; the agent never reads or writes it. Without stored credentials, a browser opens for you to log in.
- Session cookies and tokens are cached on disk with owner-only permissions, in the skill's cache folder.
