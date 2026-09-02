# Orchestration

Read this file only for onboarding, configuration, or orchestrator calls.

## Roles

The **host agent** reads and writes files, invokes tools, requests permissions, verifies evidence, and answers the user.

The optional **orchestrator** receives only a task summary and explicitly selected context. It returns JSON planning advice. It cannot authorize changes, call host tools, or replace source verification.

## Onboarding choices

Run `scripts/orchestrator.py init` and select one mode:

| Mode | Use | Default values |
| --- | --- | --- |
| `local` | Private, local planning through Ollama | `http://127.0.0.1:11434/v1`, `gemma4:e2b` |
| `remote` | Shared or stronger OpenAI-compatible model | User supplies base URL, model, and API-key environment-variable name |
| `host` | No external orchestrator | Current agent plans directly |

The helper writes `.my-beast-mode.json` in the current project. It refuses to overwrite an existing file unless `--force` is passed.

## Local setup

```bash
ollama pull gemma4:e2b
ollama serve
python <skill-root>/scripts/orchestrator.py init --mode local --yes
python <skill-root>/scripts/orchestrator.py status --check
```

`gemma4:e2b` is the small default. Change `model` in configuration when local hardware supports another Gemma 4 tag.

## Remote setup

```bash
export MY_BEAST_MODE_API_KEY="..."
python <skill-root>/scripts/orchestrator.py init \
  --mode remote \
  --base-url https://example.invalid/v1 \
  --model provider-model-name \
  --api-key-env MY_BEAST_MODE_API_KEY
```

Do not put secret values in `.my-beast-mode.json`. Commit the config only if its endpoint and model names are safe to share.

## Request a plan

```bash
python <skill-root>/scripts/orchestrator.py plan \
  --task "Review the authentication change" \
  --context-file /path/to/selected-context.txt
```

Select context narrowly. Never send `.env` files, credentials, tokens, private keys, raw customer data, or an entire repository by default. Remote mode requires explicit user authorization before sending code or private context off-device.

Expected response fields:

- `summary`: short task restatement
- `scope`: files, symbols, or modules to inspect
- `graph_steps`: structural or semantic graph queries
- `review_focus`: correctness, security, performance, compatibility, or maintainability risks
- `checks`: smallest useful verification commands or behaviors
- `parallelism`: `sequential` or `parallel`
- `notes`: constraints or uncertainty

If the endpoint fails or returns invalid JSON, report the failure and continue with host-agent planning. Never weaken review gates because the optional orchestrator is unavailable.
