import os
import tempfile
import unittest
from unittest import mock

import yaml

from llm_task_router.cli import main
from llm_task_router.classifier import DEEP, QUICK
from llm_task_router.yaml_ruleset import (
    DEFAULT_QUICK_TASK_TYPES,
    build_ruleset,
    emit_yaml,
    route_or_default,
    route_task,
)


class RulesetTests(unittest.TestCase):
    def test_ruleset_has_two_lanes(self):
        ruleset = build_ruleset()
        lane_names = [lane["name"] for lane in ruleset["lanes"]]
        self.assertEqual(lane_names, [QUICK, DEEP])

    def test_no_secrets_in_ruleset(self):
        ruleset = build_ruleset()
        self.assertEqual(ruleset["auth"], "none")
        for lane in ruleset["lanes"]:
            self.assertEqual(lane["endpoint"]["auth"], "none")
            self.assertNotIn("api_key", yaml.safe_dump(ruleset))

    def test_quick_lane_is_local_ollama(self):
        endpoint = route_task(build_ruleset(), QUICK)
        self.assertEqual(endpoint["backend"], "ollama")
        self.assertEqual(endpoint["base_url"], "http://localhost:11434")

    def test_deep_lane_uses_configurable_base_url(self):
        ruleset = build_ruleset(deep_base_url="http://box.lan:8000/v1")
        endpoint = route_task(ruleset, DEEP)
        self.assertEqual(endpoint["base_url"], "http://box.lan:8000/v1")

    def test_deep_base_url_env_override(self):
        with mock.patch.dict(os.environ,
                             {"LLM_TASK_ROUTER_DEEP_BASE_URL": "http://gpu-box:8000/v1"}):
            ruleset = build_ruleset()
        self.assertEqual(route_task(ruleset, DEEP)["base_url"], "http://gpu-box:8000/v1")

    def test_deep_base_url_default_is_local(self):
        ruleset = build_ruleset()
        self.assertEqual(route_task(ruleset, DEEP)["base_url"], "http://localhost:11434")

    def test_custom_task_types(self):
        ruleset = build_ruleset(quick_task_types=["shake-eggs"], deep_task_types=["contemplate"])
        self.assertEqual(route_task(build_ruleset(), QUICK)["model"], "llama3.2:3b")
        quick_lane = ruleset["lanes"][0]
        self.assertEqual(quick_lane["match"]["task_types"], ["shake-eggs"])
        self.assertEqual(ruleset["lanes"][1]["match"]["task_types"], ["contemplate"])

    def test_default_task_types_nonempty(self):
        self.assertGreater(len(DEFAULT_QUICK_TASK_TYPES), 0)


class YamlEmitTests(unittest.TestCase):
    def test_emitted_yaml_round_trips(self):
        ruleset = build_ruleset(name="roundtrip")
        text = emit_yaml(ruleset)
        parsed = yaml.safe_load(text)
        self.assertEqual(parsed["name"], "roundtrip")
        self.assertEqual([lane["name"] for lane in parsed["lanes"]], [QUICK, DEEP])

    def test_emitted_yaml_maps_task_types_to_endpoints(self):
        ruleset = build_ruleset()
        parsed = yaml.safe_load(emit_yaml(ruleset))
        quick = parsed["lanes"][0]
        self.assertIn("summarize", quick["match"]["task_types"])
        self.assertEqual(quick["endpoint"]["backend"], "ollama")

    def test_route_or_default_falls_back_to_last_lane(self):
        endpoint = route_or_default(build_ruleset(), "mystery-lane")
        self.assertEqual(endpoint["backend"], "openai-compatible")

    def test_unknown_lane_can_raise(self):
        with self.assertRaises(KeyError):
            route_task(build_ruleset(), "mystery-lane")


class CliEmitTests(unittest.TestCase):
    def emit_to_temp(self, extra_args=()):
        handle = tempfile.NamedTemporaryFile("w+", suffix=".yaml", delete=False)
        handle.close()
        rc = main(["emit", "-o", handle.name, *extra_args])
        with open(handle.name, encoding="utf-8") as fh:
            text = fh.read()
        os.unlink(handle.name)
        return rc, text

    def test_emit_writes_yaml_file(self):
        rc, text = self.emit_to_temp()
        self.assertEqual(rc, 0)
        parsed = yaml.safe_load(text)
        self.assertEqual(parsed["version"], 1)

    def test_emit_rejects_bad_deep_base_url(self):
        rc, _ = self.emit_to_temp(("--deep-base-url", "not a url at all"))
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
