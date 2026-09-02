---
name: my-beast-mode-recall
description: Search private cross-session My Beast Mode memory by keyword, project, task type, outcome, agent, or date. Use when the user invokes /my-beast-mode-recall or $my-beast-mode-recall, asks whether similar work was done before, or wants prior Beast Mode outcomes.
license: MIT
metadata:
  version: "1.0.0"
---

# My Beast Mode Recall

Search the lightweight index first:

```bash
python <skill-root>/scripts/recall.py "authentication"
```

Apply filters before requesting more results:

```bash
python <skill-root>/scripts/recall.py "migration" --project api --outcome success --date-start 2026-08-01 --limit 20
```

Use `--format json` only when structured results are needed. Summarize the few relevant matches; do not dump the entire memory file into context.

The helper reads `~/.my-beast-mode/memory.jsonl`, or `MY_BEAST_MODE_MEMORY` when set. It requires the sibling `my-beast-mode` skill because that skill owns the memory schema and recorder. If unavailable, tell the user to install all skills with `npx skills add sheelarajeshkumar/my-beast-mode --all`.

Memory contains sanitized summaries and counts, not prompts, source code, raw commands, tool output, or credentials.
