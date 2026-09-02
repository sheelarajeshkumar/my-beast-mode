# Review and graph workflow

Read this file for code review, debugging, refactoring, or choosing a graph tool.

## Detailed mapping contract

For architecture maps, end-to-end flows, cross-module impact, codebase onboarding, or security and data-flow analysis, use both LSP and Graphify when available:

1. Ask the language server for workspace symbols, definitions, references, implementations, call hierarchy, type hierarchy, and diagnostics relevant to the target.
2. Build or incrementally update Graphify for the smallest relevant source and documentation scope.
3. Query Graphify for the important concepts, paths, dependencies, and code-to-document relationships.
4. Use code-review-graph as complementary structural evidence when available.
5. Confirm the resulting map in current source and record any unavailable capability as a verification gap.

An unavailable integration is a fallback condition, not permission to invent results. Use repository search and direct source inspection, and tell the user which semantic evidence could not be collected.

## Choose the cheapest sufficient source

| Need | First choice | Escalate when |
| --- | --- | --- |
| Exact changed lines | VCS diff | Base or working tree is ambiguous |
| Symbol definitions, references, types | LSP | Server is absent or language is unsupported |
| Callers, imports, inheritance, tests | LSP plus code-review-graph | Index is missing, stale, or unsupported |
| Detailed code and document relationships | Graphify | Existing semantic graph lacks needed sources |
| Runtime behavior | Focused test, logs, reproduction | Evidence remains inconclusive |
| Small local symbol lookup | Repository search | Results span many modules |

Small diffs do not require every integration. Detailed mapping requires LSP and Graphify when available.

## LSP

Prefer semantic navigation over name-only search:

- workspace/document symbols to establish scope
- go-to-definition and implementation to find authoritative code
- references and call hierarchy to determine blast radius
- hover/type hierarchy for contracts and polymorphism
- diagnostics for current semantic errors

Search remains useful for configuration, generated files, string-based wiring, unsupported languages, and confirming that the LSP did not miss dynamic relationships.

## code-review-graph

When the CLI or MCP integration is available:

1. Check graph status.
2. Build once if absent; otherwise update incrementally.
3. Start with minimal task context.
4. Inspect changed-symbol impact, callers, callees, flows, communities, and related tests as needed.
5. Confirm claims in actual source and the selected diff.

Typical CLI fallback:

```bash
code-review-graph status --json
code-review-graph build
code-review-graph update --brief
code-review-graph detect-changes --brief
```

Generated `.code-review-graph/` data is local cache. Do not commit it.

## Graphify

Use Graphify for every detailed code-mapping or analysis task when it is available. Include product documents, ADRs, research, diagrams, or screenshots when they affect the requested flow; keep the graph scope narrow when code alone is sufficient.

Typical commands:

```bash
graphify <path>
graphify <path> --update
graphify query "<question>"
graphify path "<concept-a>" "<concept-b>"
```

Preserve edge confidence: extracted facts outrank inferred or ambiguous relationships. Confirm source locations before treating a graph edge as a review finding.

## Review gates

Check only axes relevant to the change, but never omit a clear risk:

- correctness and edge cases
- security and trust boundaries
- data loss, transactions, and idempotency
- concurrency and lifecycle behavior
- API, schema, and backward compatibility
- performance on affected paths
- observability and failure handling
- tests that would fail before the fix and pass after it

Avoid style-only findings unless they create a real maintenance or correctness cost.

## Finding quality

Every finding needs:

- exact source location
- concrete failure mode or impact
- evidence from source, diff, graph, or runtime
- smallest safe remediation

Do not report speculation as a defect. Put uncertain risks under residual risk or verification gaps.
