import argparse
import sys

from . import __version__
from .classifier import DEEP, QUICK, classify
from .sample_tasks import SAMPLE_TASKS
from .yaml_ruleset import (
    build_ruleset,
    emit_yaml,
    route_or_default,
)


def read_task_lines(path):
    if path == "-":
        text = sys.stdin.read()
    else:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    tasks = [line.strip() for line in text.splitlines() if line.strip()]
    if not tasks:
        raise ValueError("no tasks found in %r; one task per line expected" % path)
    return tasks


def cmd_classify(args):
    try:
        tasks = read_task_lines(args.tasks)
    except (OSError, ValueError) as err:
        print("error: %s" % err, file=sys.stderr)
        return 1
    counts = {QUICK: 0, DEEP: 0}
    for task in tasks:
        result = classify(task)
        counts[result.category] += 1
        print("%-10s  %3d%%  %s" % (result.category, int(result.confidence * 100), result.task))
    print("")
    print("quick_job: %d   deep_think: %d   total: %d" % (counts[QUICK], counts[DEEP], len(tasks)))
    return 0


def cmd_emit(args):
    quick_types = _split_types(args.quick_task_types)
    deep_types = _split_types(args.deep_task_types)
    deep_base = args.deep_base_url
    if deep_base and "://" not in deep_base:
        print("error: --deep-base-url must look like a URL,"
              " e.g. http://localhost:11434", file=sys.stderr)
        return 1
    ruleset = build_ruleset(
        name=args.name,
        quick_task_types=quick_types,
        deep_task_types=deep_types,
        quick_base_url=args.quick_base_url,
        quick_model=args.quick_model,
        deep_base_url=deep_base,
        deep_model=args.deep_model,
    )
    text = emit_yaml(ruleset)
    if args.output and args.output != "-":
        try:
            with open(args.output, "w", encoding="utf-8") as handle:
                handle.write(text)
        except OSError as err:
            print("error: cannot write %r: %s" % (args.output, err), file=sys.stderr)
            return 1
        print("ruleset written to %s" % args.output)
    else:
        sys.stdout.write(text)
    return 0


def cmd_dryrun(args):
    winners = {QUICK: 0, DEEP: 0}
    ruleset = build_ruleset(
        quick_base_url=args.quick_base_url,
        quick_model=args.quick_model,
        deep_base_url=args.deep_base_url,
        deep_model=args.deep_model,
    )
    for task in SAMPLE_TASKS:
        result = classify(task)
        winners[result.category] += 1
        endpoint = route_or_default(ruleset, result.category)
        shown = "%s | %s | %s" % (endpoint["backend"], endpoint["base_url"], endpoint["model"])
        print("[dry-run] %-10s -> %-34s  %s" % (result.category, shown, task))
    print("")
    print("offline dry-run complete: %d quick_job, %d deep_think" % (
        winners[QUICK], winners[DEEP]))
    print("(no network was used)")
    return 0


def _split_types(value):
    if not value:
        return None
    return [part.strip() for part in value.split(",") if part.strip()]


def build_parser():
    parser = argparse.ArgumentParser(
        prog="llm-task-router",
        description="Sort everyday AI tasks into quick_job vs deep_think and emit a "
                    "local-first YAML routing ruleset. No API keys, ever.",
    )
    parser.add_argument("--version", action="version", version="llm-task-router %s" % __version__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_classify = sub.add_parser(
        "classify", help="sort your own tasks (one per line; - for stdin)")
    p_classify.add_argument("tasks", help="path to a tasks file, or - to read stdin")
    p_classify.set_defaults(func=cmd_classify)

    p_emit = sub.add_parser("emit", help="write the YAML routing ruleset")
    p_emit.add_argument("-o", "--output", default="-", help="output file, or - for stdout")
    p_emit.add_argument("--name", default="everyday-routing", help="ruleset name")
    p_emit.add_argument("--quick-task-types", default=None,
                        help="quick_job task types, comma-separated")
    p_emit.add_argument("--deep-task-types", default=None,
                        help="deep_think task types, comma-separated")
    p_emit.add_argument("--quick-base-url",
                        default="http://localhost:11434", help="Ollama base URL")
    p_emit.add_argument("--quick-model", default="llama3.2:3b", help="small local model name")
    p_emit.add_argument("--deep-base-url", default=None,
                        help="bigger endpoint base URL (default: LLM_TASK_ROUTER_DEEP_BASE_URL"
                             " env, else http://localhost:11434)")
    p_emit.add_argument("--deep-model", default="qwen2.5:14b", help="bigger model name")
    p_emit.set_defaults(func=cmd_emit)

    p_dry = sub.add_parser("dry-run", help="classify built-in sample tasks fully offline")
    p_dry.add_argument("--quick-base-url",
                       default="http://localhost:11434", help="Ollama base URL shown")
    p_dry.add_argument("--quick-model", default="llama3.2:3b", help="small model shown")
    p_dry.add_argument("--deep-base-url", default=None,
                       help="bigger endpoint base URL shown")
    p_dry.add_argument("--deep-model", default="qwen2.5:14b", help="bigger model shown")
    p_dry.set_defaults(func=cmd_dryrun)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
