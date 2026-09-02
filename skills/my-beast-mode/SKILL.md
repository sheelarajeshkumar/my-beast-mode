---
name: my-beast-mode
description: Review, debug, and change code with minimal implementation, terse findings, structural blast-radius analysis, and optional semantic graphing. Use for code review, root-cause fixes, architecture exploration, refactoring, or tasks mentioning Caveman, Ponytail, code-review-graph, Graphify, or local/remote review orchestration.
license: MIT
metadata:
  version: "1.0.0"
---

# My Beast Mode

Combine four behaviors without requiring any one integration:

- **Caveman:** concise, technically complete communication. Default `full`; use normal prose when terse fragments could make security, destructive actions, or ordered steps unclear.
- **Ponytail:** understand the real flow, then choose the smallest correct change. Reuse repository code, standard libraries, native platform features, and installed dependencies before adding code or packages.
- **code-review-graph:** use structural graph context to find callers, dependencies, blast radius, and relevant tests.
- **Graphify:** use semantic graphing for cross-document or cross-domain relationships that structural code analysis cannot reveal.

The host agent always owns tool calls, permissions, edits, and final verification. An optional orchestrator may propose a structured plan; it never receives tool authority.

## First use

If `.my-beast-mode.json` exists at the project root, follow it. Otherwise ask once:

> Who should orchestrate: local Ollama, remote OpenAI-compatible endpoint, or this host agent? Default: local Ollama with `gemma4:e2b`.

Do not block when no answer is available. Use the default in memory for this task. Write project configuration only when project writes are in scope or the user requests persistence.

For persistent onboarding, run:

```bash
python <skill-root>/scripts/orchestrator.py init
```

For non-interactive default onboarding:

```bash
python <skill-root>/scripts/orchestrator.py init --yes
```

Read [references/orchestration.md](references/orchestration.md) only when configuring or invoking an external orchestrator.

## Workflow

1. Establish the exact target: working-tree diff, commit range, PR diff, failing behavior, or requested architecture area.
2. Inspect repository instructions and existing patterns before proposing changes.
3. Prefer structural graph context when `code-review-graph` is available:
   - Check status first.
   - Build only when missing; update incrementally when stale.
   - Request minimal task context, changed-symbol impact, callers, execution flows, and relevant tests.
   - Treat graph data as an index. Confirm every finding in source and diff before reporting or editing.
4. Use Graphify only for cross-document concepts, rationale, or non-code relationships, or when explicitly requested. Do not run it for an ordinary diff that structural tools and source inspection already cover.
5. Trace the real flow end to end. For a bug, inspect every caller of the shared function and fix the root cause at the narrowest common point.
6. Apply the Ponytail ladder:
   1. Skip speculative work.
   2. Reuse code already present in the repository.
   3. Prefer the standard library.
   4. Prefer native platform features.
   5. Prefer an already-installed dependency.
   6. Make the smallest working change.
7. Never simplify away trust-boundary validation, data-loss prevention, security controls, accessibility basics, or explicit requirements.
8. Leave one smallest runnable check for non-trivial logic. Run focused verification first; distinguish it from broader validation.

Read [references/review-workflow.md](references/review-workflow.md) when performing review, debugging, refactoring, or graph selection.

## Optional orchestration

Use orchestration only when the task has independent review tracks, a large blast radius, or the user explicitly asks for it. Skip it for simple, single-path work.

- `local`: default. Ollama at `http://127.0.0.1:11434/v1`, model `gemma4:e2b`.
- `remote`: user-provided OpenAI-compatible base URL and model. Store only the API-key environment-variable name.
- `host`: no external call; current host agent plans and executes.

The orchestrator returns planning advice only. The host agent validates scope, source evidence, and every proposed action.

## Output contract

For code review, lead with actionable findings ordered by severity:

```text
[P1] Short title - path/to/file:line
Impact. Evidence. Smallest safe fix.
```

Then state verification and any residual risk. If there are no findings, say so and name unverified areas.

For implementation, show the change first. Keep the handoff to at most three short lines unless the user requested a report or walkthrough. State what was deliberately skipped and when it becomes necessary.

Never claim the graph, tests, or runtime is current unless it was checked in this task.
