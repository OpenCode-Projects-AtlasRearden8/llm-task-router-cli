import os

import yaml

from .classifier import DEEP, QUICK


DEFAULT_RULESET_NAME = "everyday-routing"

DEFAULT_QUICK_TASK_TYPES = [
    "summarize",
    "translate",
    "rewrite",
    "proofread",
    "format",
    "extract",
    "name-ideas",
    "subject-line",
]

DEFAULT_DEEP_TASK_TYPES = [
    "analyze",
    "design",
    "plan",
    "code-review",
    "compare",
    "strategy",
    "long-form",
    "investigate",
]

LANE_ORDER = [QUICK, DEEP]

DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_DEEP_BASE_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "llama3.2:3b"
DEFAULT_DEEP_MODEL = "qwen2.5:14b"


def deep_base_url_from_env(env=None):
    env = os.environ if env is None else env
    return env.get("LLM_TASK_ROUTER_DEEP_BASE_URL", DEFAULT_DEEP_BASE_URL)


def _lane_types(custom, defaults):
    return custom if custom else list(defaults)


def build_ruleset(name=DEFAULT_RULESET_NAME, quick_task_types=None, deep_task_types=None,
                  quick_base_url=DEFAULT_OLLAMA_BASE_URL, quick_model=DEFAULT_OLLAMA_MODEL,
                  deep_base_url=None, deep_model=DEFAULT_DEEP_MODEL):
    deep_base_url = deep_base_url if deep_base_url else deep_base_url_from_env()
    ruleset = {
        "version": 1,
        "name": name,
        "auth": "none",
        "notes": [
            "Local-first routing: no API keys required.",
            "Override the deep_think base_url with LLM_TASK_ROUTER_DEEP_BASE_URL.",
        ],
        "lanes": [
            {
                "name": QUICK,
                "match": {
                    "task_types": _lane_types(quick_task_types, DEFAULT_QUICK_TASK_TYPES),
                    "short_task_only": True,
                },
                "endpoint": {
                    "backend": "ollama",
                    "base_url": quick_base_url,
                    "model": quick_model,
                    "auth": "none",
                },
            },
            {
                "name": DEEP,
                "match": {
                    "task_types": _lane_types(deep_task_types, DEFAULT_DEEP_TASK_TYPES),
                    "short_task_only": False,
                },
                "endpoint": {
                    "backend": "openai-compatible",
                    "base_url": deep_base_url,
                    "model": deep_model,
                    "auth": "none",
                },
            },
        ],
    }
    return ruleset


def emit_yaml(ruleset):
    return yaml.safe_dump(ruleset, sort_keys=False, default_flow_style=False).strip() + "\n"


def route_task(ruleset, category):
    for lane in ruleset["lanes"]:
        if lane["name"] == category:
            return lane["endpoint"]
    raise KeyError("no lane named %r in ruleset" % category)


def route_or_default(ruleset, category):
    try:
        return route_task(ruleset, category)
    except KeyError:
        return ruleset["lanes"][-1]["endpoint"]
