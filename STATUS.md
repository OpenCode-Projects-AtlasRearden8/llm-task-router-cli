# STATUS.md

Project: **llm-task-router-cli** — Python CLI that sorts everyday AI tasks into
`quick_job` vs `deep_think` and emits a simple, local-first YAML routing ruleset.
No API keys, ever. Published by Asdale Dynamics, LLC.

## What was built

- `llm_task_router/classifier.py` — offline keyword-and-length heuristic classifier
  (`quick_job` vs `deep_think`) returning category, score, confidence (0–1), and
  human-readable reasons. Transparency first: no network, no model calls. Ties and
  no-signal tasks default to `quick_job` since quick calls are cheap to retry.
- `llm_task_router/yaml_ruleset.py` — builds the routing ruleset:
  - `quick_job` lane → Ollama backend, `http://localhost:11434`, small model (`llama3.2:3b`).
  - `deep_think` lane → OpenAI-compatible backend, configurable base URL
    (`--deep-base-url` or `LLM_TASK_ROUTER_DEEP_BASE_URL` env, default localhost),
    bigger model (`qwen2.5:14b`).
  - Ruleset is key-free (`auth: none` everywhere) and customizable per lane
    (task types, base URLs, model names).
- `llm_task_router/cli.py` — argparse CLI with three subcommands:
  - `classify FILE|-` — sort your own saved tasks (one per line, stdin supported).
  - `emit -o routes.yaml` — write the YAML ruleset (stdout by default).
  - `dry-run` — classify 18 built-in sample tasks fully offline and show which
    endpoint each would route to.
  - `--version` flag included.
- `llm_task_router/sample_tasks.py` — sample task set for dry-run and demos.
- Tests: `tests/test_classify.py`, `tests/test_yaml_output.py`, `tests/test_cli.py`.
- Docs/packaging: `README.md`, MIT `LICENSE`, `pyproject.toml` (console script
  `llm-task-router`), `setup.cfg` (flake8 config), `.gitignore`.

## How to run it

```bash
# install
python3 -m pip install .

# try it fully offline
llm-task-router dry-run

# sort your own saved tasks
llm-task-router classify tasks.txt
llm-task-router classify - < tasks.txt

# emit the YAML routing ruleset
llm-task-router emit -o routes.yaml

# point the deep lane at a bigger keyless OpenAI-compatible endpoint
llm-task-router emit --deep-base-url http://gpu-box.lan:8000/v1 -o routes.yaml

# run tests
python3 -m pip install -e .[dev]
python3 -m pytest
python3 -m flake8 llm_task_router tests
```

## Verification results

Environment: Linux, Python 3.13.5, PyYAML 6.0.3.

- `python3 -m pytest -q` → **32 passed** (classifier quick/deep cases, YAML
  round-trip, lane endpoint mapping, env override, no-secrets assertion, CLI
  stdout/file emit, stdin classify, dry-run-with-no-socket monkeypatch).
- `python3 -m flake8 llm_task_router tests` → clean (rc=0).
- `python3 -m pip install -e .[dev]` → succeeded (PEP 668 system env needed
  `--break-system-packages`; standard venv installs will not).
- `llm-task-router --version` → `llm-task-router 0.1.0`.
- `llm-task-router dry-run` → routes 8 quick / 10 deep sample tasks to
  `ollama | http://localhost:11434 | llama3.2:3b` vs
  `openai-compatible | ... | qwen2.5:14b`, asserts no network was used.
- `llm-task-router emit -o routes.yaml` → valid YAML verified by round-trip in tests.
- Secrets scan: no keys, tokens, or personal data in any file; ruleset emits
  `auth: none` for all lanes (covered by a unit test).

## Known gaps

- The classifier is a plain keyword heuristic, not an LLM: unusual phrasing will
  misroute (e.g., describe a quick edit at length and it may look deep). Confidence
  and reasons are exposed so users can sanity-check; keyword lists are easy to edit.
- `emit` only generates config; it does not interact with Ollama or any endpoint.
- The deep lane assumes an OpenAI-compatible API with no auth; authenticated or
  non-OpenAI backends are out of scope by design (no keys, ever).
- Default deep model (`qwen2.5:14b`) is a suggestion — users must have it pulled
  in Ollama or mirror it on their bigger endpoint.
- No CI workflow file yet; tests are local-only (`pytest`).
