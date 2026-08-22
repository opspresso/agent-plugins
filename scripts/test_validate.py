#!/usr/bin/env python3
"""Regression tests for repository validation policy."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

import validate


class ValidateSkillTest(TestCase):
    def setUp(self) -> None:
        validate.problems.clear()
        validate.recommendations.clear()

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


if __name__ == "__main__":
    main()
