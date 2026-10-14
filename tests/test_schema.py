import copy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schema/0.1.0/decision.schema.json").read_text())


def load_example(name):
    return json.loads((ROOT / "examples" / name).read_text())


class DecisionSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        checker = FormatChecker()
        for name in ("date-time", "uri"):
            if name not in checker.checkers:
                raise RuntimeError(f"Missing {name} checker; install requirements-dev.txt")
        cls.validator = Draft202012Validator(SCHEMA, format_checker=checker)

    def setUp(self):
        self.record = load_example("minimal.json")

    def assertInvalid(self, record):
        self.assertFalse(self.validator.is_valid(record))

    def test_schema_is_valid(self):
        Draft202012Validator.check_schema(SCHEMA)

    def test_all_examples(self):
        for path in sorted((ROOT / "examples").glob("*.json")):
            with self.subTest(example=path.name):
                self.validator.validate(load_example(path.name))

    def test_required_fields(self):
        for key in SCHEMA["required"]:
            with self.subTest(field=key):
                record = copy.deepcopy(self.record)
                del record[key]
                self.assertInvalid(record)

    def test_decided_requires_nonempty_choices_and_options(self):
        for field in ("selected_option_ids", "options"):
            with self.subTest(field=field):
                record = copy.deepcopy(self.record)
                record["decision"][field] = []
                self.assertInvalid(record)
        del self.record["decision"]["selected_option_ids"]
        self.assertInvalid(self.record)

    def test_other_statuses_forbid_selection(self):
        for status in ("proposed", "deferred", "abstained", "failed"):
            with self.subTest(status=status):
                self.record["status"] = status
                self.assertInvalid(self.record)

    def test_nonfinal_statuses_allow_no_options(self):
        for status in ("proposed", "deferred", "abstained"):
            with self.subTest(status=status):
                self.record["status"] = status
                self.record["decision"].pop("selected_option_ids", None)
                self.record["decision"]["options"] = []
                self.validator.validate(self.record)

    def test_error_only_on_failure(self):
        self.record["decision"]["error"] = {"code": "unavailable"}
        self.assertInvalid(self.record)
        self.record["status"] = "failed"
        del self.record["decision"]["selected_option_ids"]
        self.validator.validate(self.record)
        del self.record["decision"]["error"]
        self.assertInvalid(self.record)

    def test_ai_kind_requires_invocations(self):
        self.record["kind"] = "ai"
        self.assertInvalid(self.record)
        self.record["ai"] = {"invocations": []}
        self.assertInvalid(self.record)

    def test_versions_identifiers_and_revisions(self):
        for field, values in {
            "schema_version": ["0.2.0", 1],
            "revision": [0, -1, 1.5, True, 9007199254740992],
            "id": ["", "contains spaces", "x" * 257],
            "kind": ["llm"],
            "status": ["approved"],
        }.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    record = copy.deepcopy(self.record)
                    record[field] = value
                    self.assertInvalid(record)

    def test_formats_are_asserted(self):
        for value in ("2026-10-14", "yesterday", "2026-02-30T12:00:00Z", "2026-10-14T12:00:00"):
            with self.subTest(time=value):
                self.record["time"] = value
                self.assertInvalid(self.record)
        record = load_example("ai-agent.json")
        record["decision"]["evidence"][0]["uri"] = "not a URI"
        self.assertInvalid(record)

    def test_trace_context(self):
        for context in (
            {"span_id": "00f067aa0ba902b7"},
            {"trace_id": "0" * 32},
            {"trace_id": "A" * 32},
            {"trace_id": "a" * 31},
            {"trace_id": "a" * 32, "span_id": "0" * 16},
        ):
            with self.subTest(context=context):
                self.record["context"] = context
                self.assertInvalid(self.record)
        self.record["context"] = {"trace_id": "a" * 32}
        self.validator.validate(self.record)

    def test_unknown_core_fields_and_nulls(self):
        for path in ((), ("resource",), ("decision",), ("instrumentation_scope",)):
            with self.subTest(path=path):
                record = copy.deepcopy(self.record)
                target = record
                for key in path:
                    target = target[key]
                target["vendor_field"] = "not allowed"
                self.assertInvalid(record)
        self.record["context"] = None
        self.assertInvalid(self.record)

    def test_metadata_and_numeric_limits(self):
        self.record["extensions"] = {
            "org.example.custom": {"nested": [None, True, "text", 1, 0.5]}
        }
        self.validator.validate(self.record)
        for attributes in (
            {"unnamespaced": 1},
            {"Org.Example": 1},
            {"org.example.large": 9007199254740992},
            {"org.example.nested": {"large": -9007199254740992}},
        ):
            with self.subTest(attributes=attributes):
                self.record["extensions"] = attributes
                self.assertInvalid(self.record)

    def test_duplicate_selection(self):
        self.record["decision"]["selected_option_ids"] = ["technical", "technical"]
        self.assertInvalid(self.record)

    def test_ai_usage_and_confidence_bounds(self):
        for field in ("input_tokens", "output_tokens", "cached_input_tokens", "reasoning_output_tokens"):
            for value in (-1, 0.5, 9007199254740992):
                with self.subTest(field=field, value=value):
                    record = load_example("ai-agent.json")
                    record["ai"]["invocations"][0]["usage"][field] = value
                    self.assertInvalid(record)
        for value in (-0.1, 1.1):
            with self.subTest(confidence=value):
                record = load_example("ai-agent.json")
                record["decision"]["confidence"]["value"] = value
                self.assertInvalid(record)

    def test_semantic_reference_checks_are_outside_json_schema(self):
        self.record["decision"]["selected_option_ids"] = ["missing-option"]
        self.validator.validate(self.record)


if __name__ == "__main__":
    unittest.main()
