---
name: my-beast-mode-view
description: Generate and open a private local web dashboard showing detailed RTK token optimization and My Beast Mode memory across projects. Use when the user invokes /my-beast-mode-view or $my-beast-mode-view, asks how many tokens RTK saved, or wants per-project usage and optimization analytics.
license: MIT
metadata:
  version: "1.1.0"
---

# My Beast Mode View

Create the dashboard with the bundled script:

```bash
python <skill-root>/scripts/dashboard.py --open
```

The generated file is `.my-beast-mode/dashboard.html` in the current project. If the browser does not open, return that absolute path to the user.

The script discovers RTK's local history database automatically. If RTK uses a custom location, pass `--db PATH` or set `RTK_DB_PATH`.

The dashboard also reads the append-only My Beast Mode memory at `~/.my-beast-mode/memory.jsonl`. Use `--memory PATH` or `MY_BEAST_MODE_MEMORY` for a custom location. Missing memory is a valid empty state.

The dashboard must remain local. It reads SQLite in read-only mode, embeds only aggregate-safe fields, and never displays or copies raw command arguments, prompts, or source code. Explain that RTK token counts are estimates based on output size, not API billing records.

If no database is found, report the attempted locations and suggest:

```bash
rtk config
rtk gain --all
```

For a specific output location:

```bash
python <skill-root>/scripts/dashboard.py --output /path/to/dashboard.html --open
```

Run the bundled check after modifying the generator:

```bash
python <skill-root>/scripts/dashboard.py --self-test
```
