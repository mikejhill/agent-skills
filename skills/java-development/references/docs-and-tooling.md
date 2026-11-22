# Documentation and tooling

Every project has a `docs/` folder:

| Page | Covers |
|---|---|
| `README.md` | Index of the docs |
| `philosophy.md` | Problem, goal, principles in priority order, non-goals |
| `architecture.md` | Modules, dependency rule, ports, flows, key decisions |
| `testing.md` | Suite, how to run each kind, gates and their reasons |
| `development.md` | Toolchain, conventions, how to add things, release steps |
| `distribution.md` | Install, signing, publishing |
| `compatibility.md` | Supported platforms and versions |

Add domain-specific pages (for example privacy or protocol docs) as the project needs them.

- **Keep docs generic.** No personal devices, accounts, names or local paths. Real data used
  in tests or docs is anonymised: names, numbers, ZIP codes, and the paths of tracking links
  (which can identify the recipient). Never commit hashes of redacted values as a guard. Low-entropy
  values such as ZIP codes, phone numbers and first names can be recovered by brute force. Guard
  structurally instead, for example "every five-digit number is 00000".
- **Generate screenshots and animations from the real app with a script** (a scripted
  instrumented tour, plus an assembler that writes `docs/media/`). Regenerate them before each
  release. Never hand-edit them.
- **Ship an installer script for end users** in both bash and PowerShell. It:
  - asks before every step;
  - takes the same commands in both (install, update, setup, status, pair, uninstall);
  - supports `--yes`, `--dry-run` and device selection;
  - refuses to guess when several devices are connected;
  - answers "no" when there is no terminal;
  - fails with friendly errors that say what to check.
  Test it, don't just lint it: bats and Pester suites against a fake adb and a fake release
  server, on every OS and shell it claims to support, plus a run against the CI emulator
  (see [ci.md](ci.md)).
