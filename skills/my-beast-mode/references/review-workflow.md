# Review and graph workflow

Read this file for code review, debugging, refactoring, or choosing a graph tool.

## Choose the cheapest sufficient source

| Need | First choice | Escalate when |
| --- | --- | --- |
| Exact changed lines | VCS diff | Base or working tree is ambiguous |
| Callers, imports, inheritance, tests | code-review-graph | Index is missing, stale, or unsupported |
| Cross-document rationale and concepts | Graphify | Existing semantic graph lacks needed sources |
| Runtime behavior | Focused test, logs, reproduction | Evidence remains inconclusive |
| Small local symbol lookup | Repository search | Results span many modules |

Do not build both graphs by default.

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

Use Graphify when code structure is not enough: product documents, ADRs, research papers, diagrams, screenshots, or relationships spanning code and prose.

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
