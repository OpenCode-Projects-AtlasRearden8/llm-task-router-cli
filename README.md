# llm-task-router-cli

Sort your everyday AI tasks into **quick-job** vs. **deep-think**, then emit a simple
YAML ruleset that maps each task type to the right endpoint — a small local model via
Ollama for quick jobs, a bigger endpoint (configurable base URL) for deep thinking.

No API keys, ever. Nothing leaves your machine unless you point it somewhere.

Part of Asdale Dynamics, LLC's beginner-friendly AI tooling. See
[dylanasdale.github.io](https://dylanasdale.github.io) for plain-English guides
and *The Massive AI Manual*.

## Why

Most requests you send to an AI are tiny: fix a typo, translate a paragraph, name
ten chess apps. Those don't need a giant model. A handful are genuinely heavy:
analyze, design, compare, plan. This tool gives you a starter ruleset that sends
each lane where it belongs:

| Lane         | Goes to                                  | Examples                                 |
| ------------ | ---------------------------------------- | ---------------------------------------- |
| `quick_job`  | small local model via Ollama             | summarize, translate, proofread, rename  |
| `deep_think` | bigger endpoint (configurable base URL)  | analyze, design, strategy, long-form     |

## Install

```bash
python3 -m pip install .
```

Requires Python 3.9+ and [PyYAML](https://pyyaml.org/). That's the only dependency.

## Use

### Try it first (fully offline dry-run)

Classify built-in sample tasks without touching the network or writing anything:

```bash
llm-task-router dry-run
```

### Sort your own saved tasks

Put one task per line in a file (or pipe from stdin):

```bash
llm-task-router classify tasks.txt
llm-task-router classify - < tasks.txt
```

Each line is labeled `quick_job` or `deep_think` with a confidence score
and a short explanation of the signals used.

### Emit the YAML routing ruleset

```bash
llm-task-router emit -o routes.yaml
```

which produces output like:

```yaml
version: 1
name: everyday-routing
auth: none
lanes:
- name: quick_job
  match:
    task_types:
    - summarize
    ...
    short_task_only: true
  endpoint:
    backend: ollama
    base_url: http://localhost:11434
    model: llama3.2:3b
    auth: none
- name: deep_think
  match:
    task_types:
    - analyze
    ...
    short_task_only: false
  endpoint:
    backend: openai-compatible
    base_url: http://localhost:11434
    model: qwen2.5:14b
    auth: none
```

Everything is configurable:

| Option               | Purpose                                   | Default                  |
| -------------------- | ----------------------------------------- | ------------------------ |
| `--quick-base-url`   | Ollama base URL for quick jobs            | `http://localhost:11434` |
| `--quick-model`      | small local model                         | `llama3.2:3b`            |
| `--deep-base-url`    | bigger endpoint base URL                  | `http://localhost:11434` |
| `--deep-model`       | bigger model                              | `qwen2.5:14b`            |
| `--quick-task-types` | comma-separated quick task types          | sensible defaults        |
| `--deep-task-types`  | comma-separated deep task types           | sensible defaults        |
| `--name`             | ruleset name                              | `everyday-routing`       |

Example: point the deep lane at a keyless OpenAI-compatible server on your LAN:

```bash
llm-task-router emit --deep-base-url http://gpu-box.lan:8000/v1 -o routes.yaml
```

The deep lane's base URL can also come from the
`LLM_TASK_ROUTER_DEEP_BASE_URL` environment variable, so you never have to put
an address (or anything secret) into the file itself.

## How the classifier works

It's a transparent, offline keyword-and-length heuristic — no network calls, no
model, no surprises. Signals like "analyze", "design", "strategy" push toward
deep-think; "typo", "translate", "summarize" plus a short task length push toward
quick-job. Ties go to quick-job because quick calls are cheap to retry. It's a
starting point, not an oracle.

## What this is (and isn't)

- **Is**: a simple, local-first ruleset generator — think config scaffolding and a
  plain-language heuristic.
- **Is not**: a model chooser (see ai-model-picker-cli) or a health-probe tool
  (see endpoint-health-checker-cli). It doesn't ping endpoints and never uses
  keys, so there are no credentials to leak.

## Privacy

- No API keys are ever read, stored, or emitted.
- Classification is 100% offline keyword matching.
- Default endpoints are localhost; you opt in to anything remote.
- No telemetry, no account, no personal data required.

## Development

```bash
python3 -m pip install -e .[dev]
python3 -m pytest
```

## License

MIT License. Copyright (c) 2026 Asdale Dynamics, LLC.
