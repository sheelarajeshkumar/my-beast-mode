# RTK integration

Read this file when RTK must be installed, verified, bypassed, or troubleshot.

## Runtime rule

Check whether `rtk` is on `PATH`. When present, prefix shell commands with it:

```bash
rtk git status
rtk rg "pattern" src
rtk npm test
rtk docker compose ps
```

Do not add a second prefix to a command already beginning with `rtk`. If RTK is unavailable or lacks a wrapper for the command, run the native command. RTK is an output optimizer, not an authorization layer.

Use `rtk proxy <command>` when exact raw output matters but usage should still be tracked. Prefer raw or passthrough output for cryptographic material, security scanner details, byte-exact data, or evidence where filtering could remove relevant context.

## Verify

```bash
rtk --version
rtk gain
which rtk
```

`rtk gain` distinguishes Rust Token Killer from unrelated programs named `rtk`.

## Install

Homebrew:

```bash
brew install rtk-ai/tap/rtk
```

Cargo, avoiding the unrelated crates.io package with the same name:

```bash
cargo install --git https://github.com/rtk-ai/rtk --branch master rtk
```

Initialize only for the user's selected agent or project. Examples:

```bash
rtk init
rtk init -g --codex
rtk init -g --gemini
rtk init -g --agent cursor
```

Do not install RTK or modify global agent configuration unless the user requested it.

## Security

- Never print all environment variables merely to test RTK.
- Do not trust project-local RTK filters automatically. Inspect them before running `rtk trust`.
- Treat compact output as a navigation aid. Re-run with passthrough or native output when a failure, warning, or review finding needs exact evidence.
- Preserve the original command's permission and destructive-action checks.
