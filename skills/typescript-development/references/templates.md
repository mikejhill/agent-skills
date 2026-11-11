# Strict project configuration

These are **reference configurations**, not a mandate to replace an existing framework setup. They target compiled Node ESM; adapt the package name, runtime support, and output surface. Browser/CommonJS/workspace adaptations follow below.

## Local tool selection

For a new project with an approved pinned pnpm available:

```text
pnpm add -D -E typescript eslint @eslint/js typescript-eslint prettier vitest @types/node
```

Check peer compatibility and the selected Node engine before resolving versions; commit the resulting manifest/lockfile. Optional: `tsx` for development, matching `@vitest/coverage-v8` for coverage. Do not add tools to existing projects unless they serve a requirement.

The executable validation baseline uses TypeScript 6.0.3, ESLint 10.13.0/@eslint/js 10.0.1, typescript-eslint 8.72.1, Prettier 3.7.3, Vitest 4.0.14, @types/node 24.10.1 and pnpm 10.24.0. These are compatibility pins for validation, not claims about latest versions; see the final validation status in [INTENT.md](../INTENT.md). Consult current docs on upgrades.

## package.json: ESM library example

```json
{
  "name": "typed-example",
  "version": "0.1.0",
  "type": "module",
  "packageManager": "pnpm@10.24.0",
  "engines": { "node": ">=24" },
  "files": ["dist"],
  "types": "./dist/index.d.ts",
  "exports": {
    ".": {
      "types": "./dist/index.d.ts",
      "import": "./dist/index.js"
    }
  },
  "scripts": {
    "typecheck": "tsc --noEmit",
    "lint": "eslint src tests --max-warnings 0",
    "lint:fix": "eslint src tests --fix",
    "format": "prettier --check .",
    "format:fix": "prettier --write .",
    "test": "vitest run",
    "build": "tsc -p tsconfig.build.json",
    "check": "pnpm run typecheck && pnpm run lint && pnpm run format && pnpm run test && pnpm run build"
  }
}
```

Add the actual resolved devDependencies. For applications set `private: true` unless publishing is intended. CLI: add `"bin": { "typed-example": "./dist/main.js" }` and use the entry-point pattern in [cli-patterns](cli-patterns.md). Services do not need library exports. The illustrative `>=24` range is valid only if those consumers are actually supported; use the project's real minimum.

Commit an exact `.node-version` matching the approved development runtime (the validation environment used `24.7.0`); an exact pin is not a claim that an old patch is current. Apply runtime security updates deliberately.

## tsconfig.json: check source and tests

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022"],
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,
    "noFallthroughCasesInSwitch": true,
    "noImplicitReturns": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "forceConsistentCasingInFileNames": true,
    "verbatimModuleSyntax": true,
    "isolatedModules": true,
    "noEmit": true,
    "types": ["node"]
  },
  "include": ["src/**/*.ts", "tests/**/*.ts"]
}
```

Types for the minimum supported runtime should match that runtime; adding newer @types/node does not make those APIs available on an older Node. Include additional TypeScript config files explicitly or check them in a separate config; do not accidentally leave them unchecked.

## tsconfig.build.json: emit only shipped source

```json
{
  "extends": "./tsconfig.json",
  "compilerOptions": {
    "noEmit": false,
    "rootDir": "src",
    "outDir": "dist",
    "declaration": true,
    "sourceMap": true
  },
  "include": ["src/**/*.ts"],
  "exclude": ["tests", "dist", "node_modules"]
}
```

Use relative `.js` imports in this profile. No `allowImportingTsExtensions` for ordinary unchanged tsc emission. Clean obsolete output before release using a portable Node helper; tsc does not remove files whose sources were deleted.

## eslint.config.mjs

```javascript
import js from "@eslint/js";
import { defineConfig } from "eslint/config";
import tseslint from "typescript-eslint";

export default defineConfig(
  { ignores: ["dist/**", "node_modules/**", "coverage/**"] },
  {
    files: ["**/*.ts"],
    extends: [js.configs.recommended, ...tseslint.configs.strictTypeChecked],
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {
      "@typescript-eslint/explicit-function-return-type": [
        "error",
        { allowExpressions: true, allowTypedFunctionExpressions: true },
      ],
      "@typescript-eslint/switch-exhaustiveness-check": "error",
    },
  },
);
```

This configuration uses `import.meta.dirname`, supported by the example Node 24 profile; older tooling runtimes need a fileURLToPath-based root calculation. Default exports here are required by the tool's convention. Source and tests are typed; extend the files/scripts deliberately for framework TSX or checked configuration files.

`strictTypeChecked` includes unsafe-flow and promise rules; its rule set can change outside a major version. Pin tools, review upgrades and keep specific justified exceptions local.

## Formatter

`.prettierignore`:

```text
node_modules/
dist/
coverage/
pnpm-lock.yaml
```

Use the project's existing formatting preferences; no new formatting options are necessary. Prettier does not replace lint or types.

## Intentional Biome alternative

Keep an existing working Biome setup when suitable. A Biome 2 minimal config is:

```json
{
  "formatter": { "enabled": true },
  "linter": {
    "enabled": true,
    "rules": { "recommended": true }
  },
  "assist": {
    "actions": { "source": { "organizeImports": "on" } }
  }
}
```

Use `biome lint --error-on-warnings src tests` and `biome format src tests` as separate non-mutating checks; `biome check --write` is a separate fix task. Verify rule coverage, ignored/generated files and configuration against the installed schema. Do not copy Biome 1 `organizeImports`/files.ignore keys into Biome 2 or describe this minimal profile as equivalent to typed ESLint.

## Other profiles

| Profile | Adaptation |
| --- | --- |
| Browser/Vite | App tsconfig: ESNext + Bundler, noEmit, DOM/DOM.Iterable libs, framework JSX as needed. Check Node config files separately; build with Vite and typecheck separately. |
| CommonJS consumers | Retain the project's CommonJS module strategy; design and test separate outputs if dual support is required. Do not paste ESM metadata above unchanged. |
| Workspace | Share strict policy only; each package owns include/rootDir/outDir and scripts, explicit dependency/export contracts. Root tasks recurse across packages. |
| Lean Node-only | node:test may replace Vitest; retain strict checking and tests of emitted/package behavior. |

These adaptations describe choices, not independently certified complete templates. Verify the exact resolved framework/runtime combinations before delivery.
