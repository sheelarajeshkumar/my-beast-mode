# My Beast Mode

[![skills.sh](https://skills.sh/b/sheelarajeshkumar/my-beast-mode)](https://skills.sh/sheelarajeshkumar/my-beast-mode)

Catalog: [my-beast-mode on skills.sh](https://skills.sh/sheelarajeshkumar/my-beast-mode/my-beast-mode)

This repository contains two portable Agent Skills:

- `my-beast-mode` for small, evidence-backed code changes and reviews
- `my-beast-mode-view` for a private local RTK token-optimization dashboard

Together they provide:

- Caveman-style concise communication
- Ponytail-style minimal implementation and YAGNI discipline
- RTK token-optimized shell execution
- code-review-graph structural impact analysis
- Graphify semantic and cross-document analysis
- optional local, remote, or host-agent orchestration
- per-project RTK savings, trends, and optimization-category analytics
- local cross-project usage memory with outcomes, duration, files, and checks

The default orchestrator is local Ollama with the small `gemma4:e2b` model. Orchestration is advisory and optional: the host coding agent keeps all tool access, permissions, edits, and verification.

## Why this shape

This repository uses the shared Agent Skills format: one `SKILL.md` with standard YAML frontmatter plus optional `scripts/` and `references/`. It avoids agent-specific tool names, hooks, and frontmatter, so the same package can be installed by skills.sh into any supported Agent Skills client.

RTK, code-review-graph, and Graphify remain optional external integrations. The skill still works with native shell commands, repository search, source inspection, diffs, and tests when any CLI is absent.

## Behavior

### Caveman

Responses stay short and technically complete. Review findings lead with severity, location, impact, evidence, and the smallest safe fix. Safety warnings and destructive procedures use full prose when terseness could be misunderstood.

### Ponytail

The agent reads the affected flow before editing, searches for an existing solution, and stops at the first sufficient option:

1. Skip speculative work.
2. Reuse repository code.
3. Use the standard library.
4. Use native platform features.
5. Use an existing dependency.
6. Write the minimum new code.

Root-cause fixes belong at the narrowest shared point, not in every caller. Non-trivial changes leave one focused runnable check.

### RTK

When Rust Token Killer is available, the agent prefixes shell commands with `rtk` so logs, diffs, tests, package-manager output, and VCS output consume less context. Commands keep their original intent and permission boundaries. Exact evidence can bypass filtering with `rtk proxy` or the native command.

### Dashboard

`/my-beast-mode-view` generates a self-contained local web page from RTK's history database and My Beast Mode memory. It shows raw versus optimized token estimates, saved tokens, savings percentage, averages, active days, daily trend, detailed project metrics, and the command categories responsible for savings. Filters cover 7, 30, 90, or all available days.

The dashboard uses Python and browser-native HTML, CSS, JavaScript, and SVG. It has no server, framework, package install, telemetry, or remote API. The RTK database is opened read-only, and raw command arguments, prompts, and source code are never included in the generated page.

### Local memory

Every `my-beast-mode` use records a small start and finish event in `~/.my-beast-mode/memory.jsonl`. Like Claude-memory's local-first model, the data stays on the machine and becomes useful across later sessions and projects. Unlike a transcript recorder, this store contains only sanitized summaries and metric counts:

- task type and selected orchestrator
- start, finish, and duration
- success, partial, failed, or incomplete outcome
- numbers of files changed and checks passed or failed
- a short high-level result summary

The memory deliberately excludes prompts, source code, raw commands, tool output, credentials, and personal data. Set `MY_BEAST_MODE_MEMORY` to move the store.

### code-review-graph

For code structure, the agent prefers an existing graph to broad file reads. It uses minimal context, blast radius, call relationships, execution flows, and relevant tests, then confirms findings in source. Generated graph data is an index, never the final authority.

### Graphify

For ADRs, research, diagrams, screenshots, product documents, or relationships spanning code and prose, the agent can use Graphify. It preserves extracted, inferred, and ambiguous confidence and verifies source locations before turning graph edges into findings.

### Orchestrator

The optional orchestrator returns a compact JSON plan. It never executes tools or authorizes actions.

| Choice | Description | Default |
| --- | --- | --- |
| Local | Ollama through its OpenAI-compatible API | `gemma4:e2b` at `http://127.0.0.1:11434/v1` |
| Remote | Any user-approved OpenAI-compatible endpoint | User supplies URL and model |
| Host | Current coding agent plans directly | No external service |

## Repository layout

```text
my-beast-mode-skill/
├── LICENSE
├── README.md
└── skills/
    ├── my-beast-mode/
    │   ├── SKILL.md
    │   ├── references/
    │   │   ├── orchestration.md
    │   │   ├── review-workflow.md
    │   │   └── rtk.md
    │   └── scripts/
    │       ├── memory.py
    │       └── orchestrator.py
    └── my-beast-mode-view/
        ├── SKILL.md
        └── scripts/
            └── dashboard.py
```

## Requirements

Core skill:

- an Agent Skills-compatible client
- Python 3.10 or newer for portable local-memory recording

Dashboard skill:

- Python 3.10 or newer
- RTK history tracking with at least one recorded command
- a modern web browser

Optional orchestration helper:

- Python 3.10 or newer
- Ollama for local mode, or an OpenAI-compatible HTTP endpoint for remote mode

Optional graph integrations:

- code-review-graph for structural code intelligence
- Graphify for semantic corpus graphs

Optional command-output integration:

- RTK (Rust Token Killer)

## Install with skills.sh

Install the published GitHub skill:

```bash
npx skills add sheelarajeshkumar/my-beast-mode --skill my-beast-mode
```

Install both skills:

```bash
npx skills add sheelarajeshkumar/my-beast-mode --all
```

Or select both explicitly:

```bash
npx skills add sheelarajeshkumar/my-beast-mode --skill my-beast-mode my-beast-mode-view
```

Install globally:

```bash
npx skills add sheelarajeshkumar/my-beast-mode --skill my-beast-mode -g -y
```

Install for selected agents:

```bash
npx skills add sheelarajeshkumar/my-beast-mode --skill my-beast-mode --agent codex claude-code cursor
```

Run `npx skills add --help` for the agent identifiers supported by the installed CLI version. The CLI can auto-detect installed agents when `--agent` is omitted.

Update later:

```bash
npx skills update my-beast-mode
```

Remove:

```bash
npx skills remove my-beast-mode
```

## Manual installation

Copy `skills/my-beast-mode/` into the skill directory used by the target agent. Common project-level locations include:

| Agent family | Typical project directory |
| --- | --- |
| Universal, Amp, Replit | `.agents/skills/` |
| Claude Code | `.claude/skills/` |
| Codex | `.agents/skills/` or the location configured by the client |
| GitHub Copilot | `.github/skills/` |
| Cursor, Cline, Gemini CLI, and others | Use the client path selected by the skills CLI |

Example:

```bash
mkdir -p .agents/skills
cp -R skills/my-beast-mode .agents/skills/
cp -R skills/my-beast-mode-view .agents/skills/
```

Restart or reload the agent if it does not discover newly installed skills automatically.

## First-run onboarding

The skill asks which agent should orchestrate:

1. local Ollama (default)
2. remote OpenAI-compatible endpoint
3. current host agent

The choice can stay session-only. To persist it in the current project, run the helper from the installed skill directory.

Interactive:

```bash
python scripts/orchestrator.py init
```

Accept local defaults without prompts:

```bash
python scripts/orchestrator.py init --yes
```

Use the host agent only:

```bash
python scripts/orchestrator.py init --mode host --yes
```

The helper creates `.my-beast-mode.json`. It refuses to overwrite an existing configuration unless `--force` is used.

### Local Ollama setup

Install Ollama using its platform instructions, then:

```bash
ollama pull gemma4:e2b
ollama serve
python scripts/orchestrator.py init --mode local --yes
python scripts/orchestrator.py status --check
```

Generated configuration:

```json
{
  "version": 1,
  "orchestrator": {
    "mode": "local",
    "base_url": "http://127.0.0.1:11434/v1",
    "model": "gemma4:e2b",
    "api_key_env": "",
    "timeout_seconds": 60
  }
}
```

Use another local model by passing `--model` during onboarding or editing the non-secret config.

### Remote setup

Remote mode accepts an OpenAI-compatible base URL. Put the secret in an environment variable, never in the config file:

```bash
export MY_BEAST_MODE_API_KEY="your-secret"
python scripts/orchestrator.py init \
  --mode remote \
  --base-url https://api.example.com/v1 \
  --model example-model \
  --api-key-env MY_BEAST_MODE_API_KEY
```

Remote mode must be explicitly authorized before private code or context leaves the device. The helper sends only the task plus the file passed through `--context-file`; it never scans the repository itself.

### Request a plan

```bash
python scripts/orchestrator.py plan \
  --task "Review changes since main and identify blast radius"
```

With deliberately selected context:

```bash
git diff --stat main...HEAD > /tmp/review-context.txt
python scripts/orchestrator.py plan \
  --task "Plan review of this branch" \
  --context-file /tmp/review-context.txt
```

The helper limits context files to 100,000 bytes and asks the model for JSON with scope, graph steps, focus areas, checks, and parallelism. If orchestration fails, the host agent continues without it.

## Install optional integrations

### RTK

Check first:

```bash
rtk --version
rtk gain
```

Install with Homebrew:

```bash
brew install rtk-ai/tap/rtk
```

Or build the correct RTK project with Cargo:

```bash
cargo install --git https://github.com/rtk-ai/rtk --branch master rtk
```

Initialize it for the chosen agent or project using the current RTK documentation. The skill does not auto-install RTK or modify global agent configuration.

### code-review-graph

Install it separately because it is a full CLI and MCP service, not content that should be copied into this skill:

```bash
pipx install code-review-graph
code-review-graph install
code-review-graph build
```

Typical review flow:

```bash
code-review-graph status --json
code-review-graph update --brief
code-review-graph detect-changes --brief
```

Use its MCP tools when the host agent exposes them. Start with minimal context and use the graph to narrow source reads. Keep `.code-review-graph/` out of version control.

### Graphify

Install Graphify's `graphifyy` package (double `y`), then build a semantic graph only when cross-document reasoning is useful:

```bash
pipx install graphifyy
graphify /path/to/corpus
graphify query "Which design decisions affect authentication?"
graphify path "Authentication" "Audit logging"
```

Graphify is not a required step for ordinary code review. code-review-graph covers structural code relationships more cheaply.

## Use the skill

Most agents select the skill automatically from its description. Explicit invocation is also possible:

```text
Use $my-beast-mode to review my working-tree changes.
```

Other examples:

```text
Use $my-beast-mode to diagnose this failure and fix the shared root cause.
```

```text
Use $my-beast-mode to review this diff. Use RTK for shell commands and raw output for security findings.
```

```text
Use $my-beast-mode to review main...HEAD. Use code-review-graph for blast radius, but do not modify files.
```

```text
Use $my-beast-mode to map relationships across the ADRs and implementation. Use Graphify only if structural analysis is insufficient.
```

```text
Use $my-beast-mode with remote orchestration. Send only the diff summary, not source files.
```

## View the token dashboard

In clients that expose skills as slash commands, run:

```text
/my-beast-mode-view
```

Portable explicit invocation for other Agent Skills clients:

```text
Use $my-beast-mode-view to generate and open my RTK savings dashboard.
```

The skill runs the installed generator and opens:

```text
<current-project>/.my-beast-mode/dashboard.html
```

You can run it directly from this repository:

```bash
python skills/my-beast-mode-view/scripts/dashboard.py --open
```

Choose another output file or RTK database:

```bash
python skills/my-beast-mode-view/scripts/dashboard.py \
  --db /path/to/history.db \
  --output /path/to/dashboard.html \
  --open
```

Database discovery order is `--db`, `RTK_DB_PATH`, the standard macOS RTK location, the standard Linux location, then Windows local application-data locations. If discovery fails, check the active location with `rtk config`.

### What the dashboard shows

| View | Meaning |
| --- | --- |
| Tokens saved | Estimated raw output tokens minus optimized output tokens |
| Compression | Saved tokens divided by raw tokens |
| Raw and optimized output | Estimated before-and-after token volume |
| Average saved | Saved tokens per optimized command |
| Commands optimized | RTK-tracked commands in the selected period |
| Active projects | Distinct project paths in the selected period |
| Active days | Dates containing RTK activity |
| Daily trend | Saved-token estimates by date |
| Project detail | Raw, optimized, saved, rate, average, commands, days, Beast runs, last activity, and top categories |
| How RTK optimized | Savings grouped by safe command family, such as `git`, `pytest`, or `docker` |
| Beast Mode memory | Run count, completion rate, average duration, passed checks, and recent sanitized activity |

Click a project row to change the “How” chart from all projects to that project. RTK estimates token counts from text size; these values describe output compression and are not an API invoice or exact model-token count.

### Memory lifecycle

At the beginning of each `my-beast-mode` task, the skill appends a `start` event and retains its generated session ID. Before the final response it appends the matching `finish` event. An interrupted task remains visible as `incomplete` instead of losing its history.

Manual recording is available for debugging or integrations:

```bash
SESSION_ID=$(python skills/my-beast-mode/scripts/memory.py start \
  --task-type review --orchestrator host --summary "Review authentication change")

python skills/my-beast-mode/scripts/memory.py finish \
  --session "$SESSION_ID" --outcome success \
  --summary "Review completed with focused checks" \
  --files-changed 2 --checks-passed 3 --checks-failed 0
```

The memory format is append-only JSON Lines so a partially written or malformed line can be skipped without losing earlier events. Dashboard generation never modifies this file.

### Expected review output

```text
[P1] Authorization check occurs after mutation - src/orders.ts:84
Unauthorized request can write before rejection. Move existing guard above update call.

Verification: focused authorization test passed.
Residual risk: integration suite not run.
```

No findings:

```text
No actionable findings.
Verified: changed unit tests and static checks.
Not verified: production integration and remote dependencies.
```

## Modes and overrides

The composite defaults are Caveman `full` and Ponytail `full`. A user can override them in a request:

```text
Use my-beast-mode with Caveman lite and Ponytail full.
```

```text
Use my-beast-mode, but give a full review report with explanations.
```

Requested reports, walkthroughs, and safety explanations are not shortened merely to preserve the terse style.

## Security and privacy

- The host agent retains permissions and execution authority.
- The orchestrator receives planning text only.
- Remote requests require user authorization for private context.
- API keys stay in environment variables.
- The helper does not scan the repository or read `.env` files.
- Graph claims are verified against source before edits or findings.
- Generated graph caches should not be committed.
- Project-local RTK filters must be inspected before they are trusted.
- The dashboard opens RTK history read-only and does not alter tracking data.
- Beast Mode memory is append-only and local at `~/.my-beast-mode/memory.jsonl` by default.
- Generated dashboards contain project labels and aggregate metrics, so `.my-beast-mode/` is ignored by Git.
- Prompts, source code, raw commands, command arguments, and tool output are excluded from memory and dashboard output.
- Review any third-party skill or CLI before installation.

## Cross-agent compatibility

The distributable skill uses only portable Agent Skills fields: `name`, `description`, `license`, and string-valued `metadata`. It does not require:

- agent-specific hooks
- `allowed-tools`
- forked skill context
- a particular subagent API
- an MCP server for core behavior
- a specific shell

Optional commands are examples. When a host lacks a command or tool, it follows the same decision rules with its native file search, VCS, and test capabilities.

Compatibility means the instruction package can load across conforming clients. It does not mean every optional integration is available on every operating system or host.

## Validate locally

Run the bundled offline check:

```bash
python skills/my-beast-mode/scripts/orchestrator.py self-test
python skills/my-beast-mode/scripts/memory.py self-test
python skills/my-beast-mode-view/scripts/dashboard.py --self-test
```

Validate the Agent Skills schema with `skills-ref` when installed:

```bash
skills-ref validate skills/my-beast-mode
skills-ref validate skills/my-beast-mode-view
```

You can also test discovery without installing globally:

```bash
npx skills add . --all
```

## Publish and update on skills.sh

Public source: [github.com/sheelarajeshkumar/my-beast-mode](https://github.com/sheelarajeshkumar/my-beast-mode)

skills.sh reads valid skills from public GitHub repositories. Both skill directories contain the required `SKILL.md`, `name`, and `description` fields.

To publish or refresh its catalog entry:

1. Push the current `main` branch to the public GitHub repository.
2. Install from the GitHub source with the skills CLI:

   ```bash
   npx skills add sheelarajeshkumar/my-beast-mode --all
   ```

3. Verify the [my-beast-mode catalog page](https://skills.sh/sheelarajeshkumar/my-beast-mode/my-beast-mode), the [my-beast-mode-view catalog page](https://skills.sh/sheelarajeshkumar/my-beast-mode/my-beast-mode-view), and their generated security audits.
4. After future pushes, users can retrieve the current skill with:

   ```bash
   npx skills update my-beast-mode
   ```

The install-count badge at the top of this README follows the official skills.sh badge format. Anonymous CLI telemetry affects leaderboard ranking; set `DISABLE_TELEMETRY=1` when installation telemetry is not wanted.

For an unlisted multi-skill bundle, create a [skills.sh pack](https://skills.sh/docs/packs) and add this GitHub skill. Packs provide their own installation URL.

## Skill descriptions

Short catalog description:

> Minimal, graph-aware code review with local usage memory, RTK-optimized shell output, and optional local or remote orchestration.

Full catalog description:

> Review, debug, and change code with Caveman brevity, Ponytail minimalism, RTK-optimized shell execution, code-review-graph blast-radius analysis, Graphify semantic mapping, and private cross-project usage memory. Uses optional advisory orchestration through local Ollama with Gemma 4, a remote OpenAI-compatible endpoint, or the current host agent.

Suggested repository description:

> Portable Agent Skill combining concise reviews, minimal fixes, token-efficient commands, structural and semantic graphs, and optional local-first orchestration.

Dashboard catalog description:

> Private local web dashboard for detailed RTK token optimization and My Beast Mode memory, with project metrics, trends, safe command categories, outcomes, duration, and verification counts.

Suggested topics:

```text
agent-skills code-review knowledge-graph rtk token-optimization ollama gemma4 skills-sh codex claude-code cursor copilot
```

## Troubleshooting

### Skill is not discovered

- Confirm the file name is exactly `SKILL.md`.
- Confirm the parent directory and frontmatter name are both `my-beast-mode`.
- Validate YAML frontmatter.
- Reinstall or reload the agent.
- Use the skills CLI with an explicit `--skill my-beast-mode` selector.

### RTK is unavailable or output is too compact

Use native commands when `rtk` is not installed. When exact output matters, run:

```bash
rtk proxy <command>
```

Never auto-trust repository-local RTK filters; inspect them first.

### Dashboard cannot find RTK history

Check RTK tracking and its configured database path:

```bash
rtk config
rtk gain --all
```

Then pass the reported database through `--db` or `RTK_DB_PATH`. The dashboard does not create tracking data; it visualizes commands already recorded by RTK.

### Dashboard opens with no recent projects

Select **All** in the time filter. If it remains empty, run normal shell work through RTK first, then regenerate the page. The HTML is a snapshot, so rerun `/my-beast-mode-view` to refresh it.

### Beast Mode memory is empty

Memory starts accumulating after the updated `my-beast-mode` skill is used. Confirm the file or custom location:

```bash
ls -l "${MY_BEAST_MODE_MEMORY:-$HOME/.my-beast-mode/memory.jsonl}"
```

If an agent cannot write there, set `MY_BEAST_MODE_MEMORY` to a writable private path. Reinstall or update both skills so the recorder and dashboard use the same schema.

### Ollama cannot be reached

```bash
ollama serve
python scripts/orchestrator.py status --check
```

Confirm the configured base URL ends in `/v1`. If local orchestration remains unavailable, select host mode; review behavior remains functional.

### Remote API returns an authentication error

Check that the configured `api_key_env` names an environment variable available to the agent process:

```bash
python scripts/orchestrator.py status
```

Do not paste the secret into the JSON config.

### Orchestrator returns invalid JSON

The helper accepts a plain JSON object or one surrounded by short model text. If parsing still fails, use host mode or choose a remote model with reliable JSON output.

### code-review-graph is stale

Run an incremental update before rebuilding:

```bash
code-review-graph update --brief
```

Rebuild only after a missing/corrupt graph, major branch shift, or tool recommendation.

### Graphify is expensive for a simple review

Skip it. Use the diff, code-review-graph, repository search, and focused tests. Graphify earns its cost only when semantic relationships across sources matter.

## License

MIT. External tools and named projects retain their own licenses and are not bundled here.

## References and acknowledgements

- [Agent Skills specification](https://agentskills.io/specification)
- [skills.sh documentation](https://skills.sh/docs)
- [code-review-graph](https://github.com/tirth8205/code-review-graph)
- [Graphify](https://github.com/safishamsi/graphify)
- [RTK - Rust Token Killer](https://github.com/rtk-ai/rtk)
- [Ollama Gemma 4 model library](https://ollama.com/library/gemma4)

This repository provides an original composite workflow. It does not vendor RTK, code-review-graph, Graphify, Ollama, Gemma 4, or their model weights.
