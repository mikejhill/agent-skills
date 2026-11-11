# Modes and tooling profiles

## Existing repository first

- Read `package.json`, the lockfile, runtime pin, tsconfigs, lint/test configs, and exports/bin before choosing tools.
- Preserve supported consumers, existing framework structure, package manager, and API forms. Propose migrations explicitly with impact and validation.
- OneOff: keep it short (usually 1–10 lines), without an arbitrary cap that hides necessary validation. No scaffold.
- Script: reuse the repository's pinned runtime and local tools. Use tsx for full TypeScript when needed; Node native type stripping is an optional version-specific profile, not a type checker. It does not read tsconfig or rewrite aliases; verify erasable syntax and import extensions.
- FullProject: use source/test separation and only needed files. Reusable packages need metadata/public exports; scripts do not automatically need publishing configuration.

## Choose a profile

| Target | Default | Compatibility checks |
| --- | --- | --- |
| Node library | tsc, declarations, explicit exports | Minimum runtime + consumer TypeScript; install packed tarball outside source tree |
| Service/CLI | tsc emit, Node runtime; optional tsx dev | Run emitted entry point; executable bin/shebang, shutdown, streams |
| Browser | Vite/framework build, separate tsc --noEmit | Bundler resolution, DOM lib, framework JSX, browser target and actual browser behavior |
| Workspace | pnpm workspaces, explicit package dependencies | Build dependency order, exports, package boundaries and all package checks |
| CommonJS or dual library | Preserve required output contracts | Test require and import with distinct artifacts/types where necessary |

**ESM Node compilation:** `type: module`, matching `NodeNext` module and resolution, and relative `.js` specifiers in TypeScript source. tsc resolves them to source and leaves runtime-valid paths in emitted JavaScript.

**Bundled browser:** `module: ESNext`, `moduleResolution: Bundler`, `noEmit: true`, DOM libraries; bundle with Vite. Keep Node-only config/test files in an appropriately checked Node tsconfig. Do not copy bundler resolution into unbundled Node output.

**CommonJS/dual:** choose package `type`, `.cts/.mts` or build layout, exports conditions, and declaration paths for actual supported consumers. A single ESM build is not dual support. Adding exports or removing a deep import can break users. Verify both consumer modes before changing them.

`paths` affects TypeScript resolution, not emitted runtime imports. Use relative paths, real workspace package exports, supported package imports, or a verified bundler/runtime mapping. Do not solve unresolved runtime imports by disabling checks.

## Runtime and dependency management

- Choose a currently supported Node LTS compatible with deployment and tools; check the official release schedule. Do not freeze a stale major as a timeless default.
- Commit an exact development runtime pin in the repository's established format (e.g. `.node-version` consumed by fnm). Pin CI to that file; test minimum and other promised runtimes separately. `engines` expresses support; it does not install or switch Node.
- pnpm is the new-project default for its shared store and workspace support. It complements a runtime manager; it is not a literal replacement for Python uv.
- Commit one manager's lockfile. Pin an exact manager version with `packageManager`; ensure the bootstrap/CI actually honors it. Corepack availability varies and it stopped shipping with Node 25; inspect before using it. Use an existing approved setup or a locally scoped pinned manager, never silently install globally.
- Initial/dependency-change installs intentionally update the lockfile. Reproduction uses `pnpm install --frozen-lockfile`, `npm ci`, or the established Yarn immutable install. A mismatch is a failure, not permission to regenerate.
- Install tools as local devDependencies; distinguish shipped runtime dependencies from tooling. Declare dependencies in each owning package, not only at workspace root.
- npm/pnpm installation and pack/prepare lifecycle hooks can execute code. Review those hooks and version-specific build-approval settings. Prefer disabled install scripts for isolated checks that do not require native builds; approve only a justified dependency's build when authorized. A lockfile does not make scripts safe.
- Use Node helpers instead of shell-specific `rm`, `cp`, inline environment assignments, or glob assumptions. Resolve paths with node:path and URLs with node:url; no hard-coded user directories.

## Workspace rules

- Keep one root lockfile and a `pnpm-workspace.yaml`; use `workspace:*` for intentional local dependencies with pnpm.
- Each package owns source, exports, runtime dependencies, build and checks. Consumers import the package API, never another package's `src/`.
- A shared base tsconfig holds compatible compiler policy; package configs own rootDir, outDir, platform libs and module strategy. Relative include/exclude paths resolve from the config that defines them.
- Use recursive package scripts/topological builds, or project references with `composite` and `tsc -b` when scale warrants them. Do not add Nx/Turborepo merely because there are two packages.
- Typed ESLint projectService needs each checked file in its nearest tsconfig. Do not mask workspace omissions with broad parser exclusions.

## TypeScript release/build verification

- Clean/build through portable scripts; separately check types, lint, format and behavior.
- Library: emit declarations, constrain shipped files, inspect a local pack, and install that tarball in an isolated consumer. Exercise exports, declarations, runtime dependencies and supported import/require paths without source aliases.
- CLI: verify compiled bin from another working directory and from an installed package; preserve shebang/executable metadata.
- Browser: build assets and test browser behavior; jsdom is not a substitute for browser engine integration.
- Test on the minimum promised runtime and relevant OS in existing automation. Label unavailable platforms explicitly.
- Reuse existing release policy and threshold alerts; no new credentials, publication, workflow gate, or CI permissions follow from this skill.

## Authoritative references

Checked 2026-10-29; consult the pinned tool version's docs before upgrades.

- [TypeScript compiler options](https://www.typescriptlang.org/tsconfig/)
- [Node package/module contracts](https://nodejs.org/api/packages.html)
- [Node native TypeScript limitations](https://nodejs.org/api/typescript.html)
- [Node release support](https://nodejs.org/en/about/previous-releases)
- [pnpm installation](https://pnpm.io/installation), [frozen installs](https://pnpm.io/cli/install), [build approvals](https://pnpm.io/cli/approve-builds)
- [Corepack distribution and packageManager](https://github.com/nodejs/corepack)
- [npm lifecycle scripts](https://docs.npmjs.com/cli/v11/using-npm/scripts/)
