#!/usr/bin/env python3
"""Regression tests for repository validation policy."""

import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

import validate


class ValidateSkillTest(TestCase):
    def setUp(self) -> None:
        validate.problems.clear()
        validate.recommendations.clear()
        validate.deployment_exceptions.clear()

    def write_skill(
        self,
        root: Path,
        *,
        directory: str = "sample",
        name: str = "sample",
        description: str = "Sample skill",
        extra: str = "",
    ) -> Path:
        skill = root / directory
        skill.mkdir()
        skill_file = skill / "SKILL.md"
        skill_file.write_text(
            f"---\nname: {name}\ndescription: {description}\n{extra}---\nBody\n"
        )
        return skill_file

    def test_folded_description_is_joined(self) -> None:
        fields = validate.parse_frontmatter(
            "---\nname: sample\ndescription: >\n  First line\n  second line\n---\nBody\n"
        )

        self.assertEqual("First line second line", fields["description"])

    def test_skill_name_rejects_invalid_boundaries(self) -> None:
        invalid_names = ["", "-sample", "sample-", "sample--skill", "Sample", "a" * 65]
        with TemporaryDirectory() as temporary:
            for index, name in enumerate(invalid_names):
                with self.subTest(name=name):
                    validate.problems.clear()
                    root = Path(temporary) / str(index)
                    root.mkdir()
                    skill_file = self.write_skill(root, name=name)

                    validate.check_skill(skill_file)

                    self.assertTrue(validate.problems)

    def test_skill_rejects_empty_description(self) -> None:
        with TemporaryDirectory() as temporary:
            skill_file = self.write_skill(Path(temporary), description="")

            validate.check_skill(skill_file)

        self.assertEqual(1, len(validate.problems))
        self.assertIn("must not be empty", validate.problems[0])

    def test_skill_description_accepts_limit_and_rejects_overflow(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            at_limit = self.write_skill(
                root, directory="at-limit", name="at-limit", description="x" * validate.MAX_DESCRIPTION
            )
            validate.check_skill(at_limit)
            self.assertEqual([], validate.problems)

            validate.problems.clear()
            overflow = self.write_skill(
                root, directory="overflow", name="overflow", description="x" * (validate.MAX_DESCRIPTION + 1)
            )
            validate.check_skill(overflow)
            self.assertEqual(1, len(validate.problems))
            self.assertIn("over 1024", validate.problems[0])

    def test_skill_rejects_directory_mismatch_and_unknown_field(self) -> None:
        with TemporaryDirectory() as temporary:
            skill_file = self.write_skill(
                Path(temporary), directory="directory", name="different", extra="unknown: value\n"
            )

            validate.check_skill(skill_file)

        self.assertEqual(2, len(validate.problems))
        self.assertTrue(any("must match" in problem for problem in validate.problems))
        self.assertTrue(any("not a frontmatter field" in problem for problem in validate.problems))

    def test_attachment_limits_exclude_skill_body(self) -> None:
        with TemporaryDirectory() as temporary:
            skill = Path(temporary) / "sample"
            skill.mkdir()
            (skill / "SKILL.md").write_text("x" * (validate.MAX_SKILL_BYTES + 1))
            for index in range(validate.MAX_SKILL_FILES):
                (skill / f"reference-{index}.md").write_text("x")

            validate.check_bundle(skill)

        self.assertEqual([], validate.problems)

    def test_long_skill_is_a_recommendation_not_a_failure(self) -> None:
        with TemporaryDirectory() as temporary:
            skill = Path(temporary) / "sample"
            skill.mkdir()
            body = "\n".join("line" for _ in range(validate.MAX_BODY_LINES + 1))
            skill_file = skill / "SKILL.md"
            skill_file.write_text(
                f"---\nname: sample\ndescription: Sample skill\n---\n{body}\n"
            )

            validate.check_skill(skill_file)

        self.assertEqual([], validate.problems)
        self.assertEqual(1, len(validate.recommendations))

    def test_attachment_count_remains_a_failure(self) -> None:
        with TemporaryDirectory() as temporary:
            skill = Path(temporary) / "sample"
            skill.mkdir()
            (skill / "SKILL.md").write_text("skill")
            for index in range(validate.MAX_SKILL_FILES + 1):
                (skill / f"reference-{index}.md").write_text("x")

            validate.check_bundle(skill)

        self.assertEqual(1, len(validate.problems))
        self.assertIn("attachments", validate.problems[0])

    def test_attachment_size_and_total_boundaries(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            at_limit = root / "at-limit"
            at_limit.mkdir()
            (at_limit / "SKILL.md").write_text("skill")
            (at_limit / "a.md").write_bytes(b"x" * validate.MAX_FILE_BYTES)
            (at_limit / "b.md").write_bytes(b"x" * validate.MAX_FILE_BYTES)
            (at_limit / "c.md").write_bytes(b"x" * validate.MAX_FILE_BYTES)
            (at_limit / "d.md").write_bytes(
                b"x" * (validate.MAX_SKILL_BYTES - 3 * validate.MAX_FILE_BYTES)
            )
            validate.check_bundle(at_limit)
            self.assertEqual([], validate.problems)

            validate.problems.clear()
            overflow = root / "overflow"
            overflow.mkdir()
            (overflow / "SKILL.md").write_text("skill")
            (overflow / "reference.md").write_bytes(b"x" * (validate.MAX_FILE_BYTES + 1))
            validate.check_bundle(overflow)
            self.assertTrue(any("limit per file" in problem for problem in validate.problems))

            validate.problems.clear()
            total_overflow = root / "total-overflow"
            total_overflow.mkdir()
            (total_overflow / "SKILL.md").write_text("skill")
            for name in ("a.md", "b.md", "c.md"):
                (total_overflow / name).write_bytes(b"x" * validate.MAX_FILE_BYTES)
            (total_overflow / "d.md").write_bytes(
                b"x" * (validate.MAX_SKILL_BYTES - 3 * validate.MAX_FILE_BYTES + 1)
            )
            validate.check_bundle(total_overflow)
            self.assertTrue(any("attachment bytes" in problem for problem in validate.problems))

    def test_nested_unsupported_attachment_is_rejected(self) -> None:
        with TemporaryDirectory() as temporary:
            skill = Path(temporary) / "sample"
            nested = skill / "assets"
            nested.mkdir(parents=True)
            (skill / "SKILL.md").write_text("skill")
            (nested / "template.html").write_text("<html></html>")

            validate.check_bundle(skill)

        self.assertEqual(1, len(validate.problems))
        self.assertIn("is not carried by the sync", validate.problems[0])


class ValidateManifestTest(TestCase):
    def setUp(self) -> None:
        validate.problems.clear()
        validate.recommendations.clear()
        validate.deployment_exceptions.clear()

    def write_json(self, path: Path, data: object) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))
        return path

    def test_plugin_rejects_non_object_and_invalid_field_types(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            cases = [
                ([], "must be a JSON object"),
                ({"$schema": validate.PLUGIN_SCHEMA, "name": 1}, "name must be a string"),
                (
                    {"$schema": validate.PLUGIN_SCHEMA, "name": "plugin", "author": "person"},
                    "author must be an object",
                ),
                (
                    {"$schema": validate.PLUGIN_SCHEMA, "name": "plugin", "keywords": ["ok", 1]},
                    "keywords must be an array of strings",
                ),
            ]
            for index, (data, expected) in enumerate(cases):
                with self.subTest(data=data):
                    validate.problems.clear()
                    manifest = self.write_json(root / str(index) / "plugin.json", data)
                    validate.check_plugin(manifest)
                    self.assertTrue(any(expected in problem for problem in validate.problems))

    def test_mcp_rejects_non_object_servers_and_invalid_server_shape(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            cases = [
                ([], "must be a JSON object"),
                (
                    {"$schema": validate.MCP_SCHEMA, "mcpServers": []},
                    "mcpServers must be an object",
                ),
                (
                    {"$schema": validate.MCP_SCHEMA, "mcpServers": {"server": []}},
                    "server must be an object",
                ),
                (
                    {
                        "$schema": validate.MCP_SCHEMA,
                        "mcpServers": {"server": {"type": "stdio", "command": ""}},
                    },
                    "command must be a non-empty string",
                ),
                (
                    {
                        "$schema": validate.MCP_SCHEMA,
                        "mcpServers": {"server": {"type": "stdio", "command": "server"}},
                    },
                    "repository policy requires streamable-http",
                ),
            ]
            for index, (data, expected) in enumerate(cases):
                with self.subTest(data=data):
                    validate.problems.clear()
                    manifest = self.write_json(root / str(index) / "mcp.json", data)
                    validate.check_mcp(manifest)
                    self.assertTrue(any(expected in problem for problem in validate.problems))

    def test_unique_rejects_skill_and_mcp_name_collision(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            plugin_a = root / "plugin-a"
            skill = plugin_a / "skills" / "shared"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("skill")
            plugin_b = root / "plugin-b"
            self.write_json(
                plugin_b / "mcp.json",
                {"$schema": validate.MCP_SCHEMA, "mcpServers": {"shared": {"type": "stdio", "command": "x"}}},
            )

            validate.check_unique(root, [plugin_a, plugin_b])

        self.assertEqual(1, len(validate.problems))
        self.assertIn("is used by both", validate.problems[0])

    def test_main_clears_results_between_runs(self) -> None:
        validate.problems.append("stale problem")
        validate.recommendations.append("stale recommendation")
        validate.deployment_exceptions.append("stale exception")

        with redirect_stdout(StringIO()):
            first_result = validate.main()
            first_exceptions = list(validate.deployment_exceptions)
            second_result = validate.main()

        self.assertEqual(0, first_result)
        self.assertEqual(0, second_result)
        self.assertEqual(first_exceptions, validate.deployment_exceptions)
        self.assertNotIn("stale problem", validate.problems)
        self.assertNotIn("stale recommendation", validate.recommendations)
        self.assertNotIn("stale exception", validate.deployment_exceptions)


if __name__ == "__main__":
    main()
