---
name: my-beast-mode-view
description: Generate and open a private local dashboard for RTK savings, missed coverage, trend warnings, session attribution, agent comparisons, data health, and My Beast Mode memory. Use when the user invokes /my-beast-mode-view or $my-beast-mode-view, asks how many tokens RTK saved, or wants cross-project optimization analytics.
license: MIT
metadata:
  version: "2.0.0"
---

# My Beast Mode View

Create the dashboard with the bundled script:

```bash
python <skill-root>/scripts/dashboard.py --open
```

The generated file is `.my-beast-mode/dashboard.html` in the current project. If the browser does not open, return that absolute path to the user.

The script discovers RTK's local history database automatically. If RTK uses a custom location, pass `--db PATH` or set `RTK_DB_PATH`.

The dashboard also reads the append-only My Beast Mode memory at `~/.my-beast-mode/memory.jsonl`. Use `--memory PATH` or `MY_BEAST_MODE_MEMORY` for a custom location. Missing memory is a valid empty state.

It runs `rtk discover --format json` for a safe missed-savings summary. It must discard unsupported-command examples and retain only normalized tool names, categories, counts, and estimates.

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

For a share-safe dashboard and aggregate JSON export:

```bash
python <skill-root>/scripts/dashboard.py --privacy --export-json /path/to/summary.json --open
```

Use `--aliases aliases.json` for friendly project names. The file must be a JSON object mapping exact paths to labels. The web dashboard also provides **Share PNG** and **Share JSON** buttons; both exclude paths, prompts, commands, and memory summaries.

Run the bundled check after modifying the generator:

```bash
python <skill-root>/scripts/dashboard.py --self-test
```
