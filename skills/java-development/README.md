# java-development

Conventions for Gradle-built JVM projects (Java, Kotlin, Android): module and package naming, ports-and-adapters architecture, convention plugins, strict linting, a full test pyramid with coverage and mutation gates, and GitHub Actions CI.

## Use

Loads automatically when the agent creates, restructures, or reviews a JVM project or its build. Examples:

- "Start a new Kotlin Android app called spam-sweep."
- "Add a data module for the SQLite storage."

## Requirements

- A JDK and the Gradle wrapper. Android projects need the Android SDK and an emulator for device tests.

## Security and side effects

- Device and destructive tests run only on emulators, never on a personal device.
- The agent never accepts third-party terms (such as Build Scans), publishes, or pushes for you. Each such choice is a repository variable you set.
