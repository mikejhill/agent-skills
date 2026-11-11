# Boundary-safe TypeScript examples

## Decode before trusting

```typescript
/** A validated value returned by the user endpoint. */
export interface User {
  readonly id: string;
  readonly active: boolean;
}

/** Reject invalid external data before it enters the domain. */
export function decodeUser(value: unknown): User {
  if (typeof value !== "object" || value === null) {
    throw new TypeError("user must be an object");
  }
  if (
    !("id" in value) ||
    typeof value.id !== "string" ||
    value.id.trim() === "" ||
    !("active" in value) ||
    typeof value.active !== "boolean"
  ) {
    throw new TypeError("user requires a nonempty id and boolean active");
  }
  return { id: value.id, active: value.active };
}

/** Fetch and validate an endpoint response using the supplied decoder. */
export async function fetchDecoded<T>(
  url: string,
  decode: (value: unknown) => T,
): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`HTTP ${String(response.status)}`);
  const value: unknown = await response.json();
  return decode(value);
}
```

Unlike `response.json() as T`, this generic relates the actual decoder result to the return type. A caller cannot obtain a validated User by choosing a type parameter alone. For many nested schemas, use the project's schema library instead of hand-writing validators.

## Class-first orchestration without utility wrappers

```typescript
import type { User } from "./user.js";

/** Source adapter owns transport and boundary decoding. */
export interface UserSource {
  load(): Promise<readonly User[]>;
}

/** Coordinates domain work without depending on HTTP or stdout. */
export class UserService {
  constructor(private readonly source: UserSource) {}

  /** Return active users without mutating the source collection. */
  async activeUsers(): Promise<readonly User[]> {
    const users = await this.source.load();
    return users.filter((user) => user.active);
  }
}
```

Keep decodeUser in user.ts or a cohesive boundary module; inject a fetch adapter implementing UserSource at bootstrap. Unit-test UserService with an in-memory fake, and test the adapter separately for HTTP failure and malformed payloads. A static Validator class adds no useful state/lifecycle here.

## Exhaustiveness and useful generics

```typescript
export type Outcome<T> =
  | { readonly kind: "success"; readonly value: T }
  | { readonly kind: "failure"; readonly message: string };

/** Convert a result to a display value, handling every variant. */
export function display<T>(
  outcome: Outcome<T>,
  render: (value: T) => string,
): string {
  switch (outcome.kind) {
    case "success":
      return render(outcome.value);
    case "failure":
      return outcome.message;
    default: {
      const unexpected: never = outcome;
      throw new Error(`Unhandled outcome: ${String(unexpected)}`);
    }
  }
}
```

Add a negative compile test showing that a mismatched renderer fails; do not use casts to make it compile. Use a short described @ts-expect-error for that expected diagnostic only.

## Refactor a monolithic CLI

| Before | After |
| --- | --- |
| process.argv read inside a service | parseCli(argv) returns a Command union |
| JSON cast to a declared interface | decode unknown in the adapter |
| logger/config singleton imported everywhere | typed config and collaborators injected |
| output mixed with progress | results stdout, diagnostics stderr |
| broad catch returns success | specific known failure code, unexpected error boundary |
| tests invoke source only | unit tests plus built/packed consumer smoke tests |

Reuse [CLI patterns](cli-patterns.md) and [compiler/lint templates](templates.md); do not duplicate complete scaffolds or release workflows here.
