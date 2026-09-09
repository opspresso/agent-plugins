#!/usr/bin/env python3
"""Regression tests for repository validation policy."""

import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from unittest.mock import patch

import validate


class ValidateSkillTest(TestCase):
    def setUp(self) -> None:
        validate.problems.clear()
        validate.recommendations.clear()

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

    def test_frontmatter_matches_studio_scalar_boundaries(self) -> None:
        for marker in (">", "|", ">-", "|-"):
            with self.subTest(marker=marker):
                fields = validate.parse_frontmatter(
                    f"---\r\nNAME: 'sample'\r\ndescription: {marker}\r\n"
                    "  First line\r\n  second line\r\nmetadata:\r\n"
                    "  owner: team\r\n---"
                )
                self.assertEqual(
                    {"name": "sample", "description": "First line second line", "metadata": ""},
                    fields,
                )

    def test_frontmatter_preserves_unpaired_quotes_and_plain_values(self) -> None:
        for value in ("'til dawn", "\"mismatched'", "> plain value"):
            with self.subTest(value=value):
                fields = validate.parse_frontmatter(
                    f"---\nname: sample\ndescription: {value}\n  ignored continuation\n---\n"
                )
                self.assertEqual(value, fields["description"])

    def test_quoted_skill_name_is_accepted(self) -> None:
        with TemporaryDirectory() as temporary:
            skill_file = self.write_skill(Path(temporary), name='"sample"')
            validate.check_skill(skill_file)
        self.assertEqual([], validate.problems)

    def test_skill_rejects_description_lines_lost_by_runtime(self) -> None:
        for description in (
            ">\n  First line\nUnindented routing boundary",
            "First line\n  Ignored plain continuation",
            ">\n  First line\n\n  Ignored after blank line",
        ):
            with self.subTest(description=description), TemporaryDirectory() as temporary:
                validate.problems.clear()
                skill_file = self.write_skill(Path(temporary), description=description)
                validate.check_skill(skill_file)
                self.assertTrue(any("ignored by Agent Studio" in p for p in validate.problems))

    def test_frontmatter_allows_metadata_and_comments(self) -> None:
        with TemporaryDirectory() as temporary:
            skill_file = self.write_skill(
                Path(temporary), description=">-\n  Complete description",
                extra="# Operator comment\nmetadata:\n  owner: team\n",
            )
            validate.check_skill(skill_file)
        self.assertEqual([], validate.problems)

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
        for description in ("", '""', "''", '"   "', ">-", "|-"):
            with self.subTest(description=description), TemporaryDirectory() as temporary:
                validate.problems.clear()
                skill_file = self.write_skill(Path(temporary), description=description)
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

    def test_description_respects_studio_utf16_limit(self) -> None:
        for length in (512, 513):
            with self.subTest(length=length), TemporaryDirectory() as temporary:
                validate.problems.clear()
                skill = self.write_skill(Path(temporary), description="😀" * length)
                validate.check_skill(skill)
                self.assertEqual(length > 512, bool(validate.problems))

    def test_bundle_rejects_symlinks_even_when_dangling(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = self.write_skill(root).parent
            (root / "reference.md").write_text("outside the bundle")
            (skill / "linked.md").symlink_to(root / "reference.md")
            (skill / "missing.md").symlink_to(root / "missing.md")
            validate.check_bundle(skill)
            self.assertEqual(2, len(validate.problems))
            self.assertTrue(all("symlink" in problem for problem in validate.problems))

    def test_bundle_accepts_uppercase_extensions(self) -> None:
        with TemporaryDirectory() as temporary:
            skill = self.write_skill(Path(temporary)).parent
            (skill / "REFERENCE.MD").write_text("reference")
            validate.check_bundle(skill)
        self.assertEqual([], validate.problems)


class ValidateManifestTest(TestCase):
    def setUp(self) -> None:
        validate.problems.clear()
        validate.recommendations.clear()

    def write_json(self, path: Path, data: object) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))
        return path

    def test_mcp_names_must_be_addressable_by_studio(self) -> None:
        for name in ("valid-server", "Invalid", "invalid.name", "", "with space"):
            with self.subTest(name=name), TemporaryDirectory() as temporary:
                validate.problems.clear()
                manifest = self.write_json(Path(temporary) / "mcp.json", {
                    "$schema": validate.MCP_SCHEMA,
                    "mcpServers": {name: {"type": "streamable-http", "url": "https://example.com/mcp"}},
                })
                with patch.object(validate, "check_mcp_docs"):
                    validate.check_mcp(manifest)
                self.assertEqual(name != "valid-server", bool(validate.problems))

    def test_mcp_rejects_description_lines_lost_by_runtime(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            extension = root / "org.opspresso.agent-studio" / "mcp"
            extension.mkdir(parents=True)
            (extension / "server.md").write_text(
                "---\ndescription: >\n  Search data\nDo not write\n---\nNotes\n"
            )
            validate.check_mcp_docs(root, {"server"})
        self.assertTrue(any("ignored by Agent Studio" in p for p in validate.problems))

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

    def test_mcp_reports_malformed_urls_and_continues_validation(self) -> None:
        for url in ("https://[broken", "https://example.com:bad/mcp", "https://example.com:65536/mcp"):
            with self.subTest(url=url), TemporaryDirectory() as temporary:
                validate.problems.clear()
                root = Path(temporary)
                manifest = self.write_json(
                    root / "mcp.json",
                    {
                        "$schema": validate.MCP_SCHEMA,
                        "mcpServers": {
                            "server": {"type": "streamable-http", "url": url},
                            "second": [],
                        },
                    },
                )
                validate.check_mcp(manifest)
                self.assertTrue(any("invalid host or port" in p for p in validate.problems))
                self.assertTrue(any("second: server must be an object" in p for p in validate.problems))

    def test_mcp_url_policy_has_no_deployment_namespace_exception(self) -> None:
        cases = [
            ("http://service.agent-mcps.svc.cluster.local/mcp", False),
            ("http://service.other.svc.cluster.local/mcp", False),
            ("http://10.0.0.1/mcp", False),
            ("http://example.com/mcp", False),
            ("https://example.com/mcp", True),
            ("http://localhost:3000/mcp", True),
            ("http://127.0.0.1:3000/mcp", True),
            ("http://[::1]:3000/mcp", True),
        ]
        for url, accepted in cases:
            with self.subTest(url=url), TemporaryDirectory() as temporary:
                validate.problems.clear()
                manifest = self.write_json(Path(temporary) / "mcp.json", {
                    "$schema": validate.MCP_SCHEMA,
                    "mcpServers": {"server": {"type": "streamable-http", "url": url}},
                })
                with patch.object(validate, "check_mcp_docs"):
                    validate.check_mcp(manifest)
                self.assertEqual(accepted, not validate.problems)

    def test_mcp_rejects_quoted_empty_extension_description(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = self.write_json(
                root / "mcp.json",
                {
                    "$schema": validate.MCP_SCHEMA,
                    "mcpServers": {"server": {"type": "streamable-http", "url": "https://example.com/mcp"}},
                },
            )
            extension = root / "org.opspresso.agent-studio" / "mcp"
            extension.mkdir(parents=True)
            (extension / "server.md").write_text('---\ndescription: ""\n---\nNotes\n')
            validate.check_mcp(manifest)

        self.assertEqual(1, len(validate.problems))
        self.assertIn("description is required", validate.problems[0])

    def test_main_rejects_extension_without_mcp_manifest(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            plugin = root / "plugins" / "sample"
            self.write_json(
                plugin / "plugin.json",
                {"$schema": validate.PLUGIN_SCHEMA, "name": "sample"},
            )
            extension = plugin / "org.opspresso.agent-studio" / "mcp"
            extension.mkdir(parents=True)
            (extension / "server.md").write_text("---\ndescription: Server\n---\nNotes\n")

            with patch.object(validate, "__file__", str(root / "scripts" / "validate.py")):
                with redirect_stdout(StringIO()):
                    result = validate.main()

        self.assertEqual(1, result)
        self.assertEqual(1, len(validate.problems))
        self.assertIn("no matching 'server' server in mcp.json", validate.problems[0])

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

        with redirect_stdout(StringIO()):
            first_result = validate.main()
            second_result = validate.main()

        self.assertEqual(0, first_result)
        self.assertEqual(0, second_result)
        self.assertNotIn("stale problem", validate.problems)
        self.assertNotIn("stale recommendation", validate.recommendations)


class ValidateMarkdownLinksTest(TestCase):
    def setUp(self) -> None:
        validate.problems.clear()

    def test_local_references_resolve_relative_to_the_document(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            reference = root / "references" / "guide.md"
            reference.parent.mkdir()
            (root / "SKILL.md").write_text("Skill")
            (reference.parent / "data set.md").write_text("Data")
            reference.write_text(
                "[body](../SKILL.md#topic)\n[data](data%20set.md)\n"
                '[data](<data set.md> "title")\n[remote](https://example.com/a)\n'
                "[anchor](#topic)\n"
            )
            validate.check_markdown_links(reference, root)
        self.assertEqual([], validate.problems)

    def test_missing_and_cross_bundle_references_fail(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = root / "skill"
            skill.mkdir()
            (root / "other.md").write_text("Not in the skill payload")
            document = skill / "SKILL.md"
            document.write_text("[missing](missing.md)\n[other](../other.md)\n")
            validate.check_markdown_links(document, skill)
        self.assertEqual(2, len(validate.problems))
        self.assertTrue(any("does not exist" in p for p in validate.problems))
        self.assertTrue(any("leaves its bundle" in p for p in validate.problems))

    def test_fenced_examples_are_not_payload_references(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            document = root / "SKILL.md"
            document.write_text(
                "````markdown\n[example](missing.md)\n```\n"
                "[still example](missing.md)\n````\n"
                "~~~markdown\n[example](missing.md)\n~~~\n"
                "[real link](missing.md)\n"
            )
            validate.check_markdown_links(document, root)
        self.assertEqual(1, len(validate.problems))
        self.assertIn("line 9", validate.problems[0])

    def test_symlink_cannot_escape_the_payload(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = root / "skill"
            skill.mkdir()
            (root / "outside.md").write_text("Outside")
            (skill / "link.md").symlink_to(root / "outside.md")
            document = skill / "SKILL.md"
            document.write_text("[reference](link.md)")
            validate.check_markdown_links(document, skill)
        self.assertEqual(1, len(validate.problems))
        self.assertIn("leaves its bundle", validate.problems[0])


if __name__ == "__main__":
    main()
