# Architecture

Use ports and adapters with a domain-driven core. Business rules must be testable without any
framework.

- **`-core-domain`** is pure language: entities, value objects, aggregates, and domain services. It
  has no framework or coroutine/reactive dependencies.
  - Value objects validate in constructors or factories that return null, so holding one means it's valid.
  - Aggregates change only through methods that check the transition, and return new values.
  - State machines (for example a multi-step protocol) are pure: events in, new state and commands out.
- **`-core-application`** holds the use cases, plus the **ports** (interfaces) they need:
  repositories, gateways, senders, schedulers, and the clock.
  - It depends only on the domain and on coroutines (Kotlin) or `CompletableFuture`/plain threads (Java).
  - Pass a `Clock` everywhere; never read the system time directly.
- **Adapter modules** (`-data-*`, `-platform-*`) implement ports, one technology each, named for
  it: `RoomTriageRepository`, `SmsTextMessageSender`. Adapters never depend on each other or on UI.
- **`-feature-*`** modules hold UI and view models, and depend only on the application layer.
- **`-app`** is the composition root: the one place that knows every concrete class. Prefer manual
  constructor injection in an `AppContainer` until the graph is genuinely large. Give it explicit
  seams (constructor parameters) for the things tests must replace.
- **`-core-testing`** provides an in-memory implementation of every port, plus a harness that wires
  the application layer the same way production does. Use these fakes instead of mocking frameworks.
- **Shared data used by several test suites** (fixtures, sample corpora) goes in its own
  dependency-free module (`-core-corpus`), never copied between suites.

Design side effects to survive process death and replays, because Android (and any server) kills
processes at arbitrary points:

- **Store intent before acting.** Persist the next state, then send the SMS or call the API. A
  crash then leaves an unsent step that a timeout can cover, never a duplicate.
- **Store waits as data, not as scheduler state.** Retry times and pacing gaps live in the
  aggregate. A scheduled job is only a wake-up call that recomputes what may happen now, so an
  early or duplicate wake-up can't skip a wait.
- **Make inputs idempotent.** Record the ids of events already applied, and reject any event older
  than the step it would answer. Notifications, webhooks and message histories get replayed.
- **Use a transaction port** (`TransactionRunner`) for multi-repository decisions. Re-read the
  aggregate inside the transaction, so two competing decisions can't both apply.
- **Version references to mutable external objects.** For example, carry a notification's key *and*
  its post time, and refuse to act on a newer posting than the one that was classified.
- **Codecs treat stored text as hostile.** Strip separator characters before encoding, and skip
  unreadable records instead of throwing, so one bad row never breaks a screen.

Write down decisions and their rejected alternatives in `docs/architecture.md`. A "key decisions"
table is enough.
