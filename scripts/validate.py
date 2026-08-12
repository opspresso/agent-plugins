#!/usr/bin/env python3
"""Check every plugin in this repository against Agent Plugins 1.0.0.

Run it with no arguments from the repository root:

    python3 scripts/validate.py

Why this exists: a skill that breaks the Agent Skills spec is not an error. The
spec tells clients to **skip it and carry on loading**, so a mistyped `name` or a
directory renamed without its frontmatter does not fail anywhere — the skill just
stops existing, and the only symptom is a model that never calls it. This turns
that silence into a failed check.

Standard library only, and no network: the constraints below are transcribed from
the published schemas rather than fetched, so this runs in CI without depending
on agent-plugins.org being up.

  plugin.json  https://agent-plugins.org/schemas/1.0.0/plugin.schema.json
  mcp.json     https://agent-plugins.org/schemas/1.0.0/mcp.schema.json
  SKILL.md     https://agentskills.io/specification
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
MCP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"

PLUGIN_FIELDS = {
    "$schema", "name", "version", "description", "author",
    "homepage", "repository", "license", "keywords", "extensions",
}
AUTHOR_FIELDS = {"name", "email", "url"}
SKILL_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}

# `^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$` from the plugin schema.
PLUGIN_NAME = re.compile(r"^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")
# Agent Skills is stricter: no dots, and no consecutive hyphens.
SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
KEY = re.compile(r"^([A-Za-z0-9_-]+):\s*(.*)$")

MAX_DESCRIPTION = 1024
MAX_COMPATIBILITY = 500
MAX_BODY_LINES = 500

problems: list[str] = []


def fail(where: Path, message: str) -> None:
    problems.append(f"{where}: {message}")


def parse_frontmatter(text: str) -> dict[str, str] | None:
    """The flat `key: value` subset every client here actually reads.

    Folded scalars (`>` and `|`) are joined into one line, which is what a
    description written across three lines is. Nested mappings are returned as
    the empty string — only `metadata` may be one, and nothing checks its shape.
    """
    match = FRONTMATTER.match(text)
    if not match:
        return None
    fields: dict[str, str] = {}
    key: str | None = None
    for line in match.group(1).split("\n"):
        header = KEY.match(line)
        if header and not line.startswith((" ", "\t")):
            key = header.group(1)
            fields[key] = header.group(2).strip().lstrip(">|").strip()
        elif key and line.strip():
            fields[key] = f"{fields[key]} {line.strip()}".strip()
    return fields


def check_plugin(manifest: Path) -> None:
    directory = manifest.parent.name
    try:
        data = json.loads(manifest.read_text())
    except json.JSONDecodeError as error:
        fail(manifest, f"not valid JSON — {error}")
        return
    if data.get("$schema") != PLUGIN_SCHEMA:
        fail(manifest, "$schema is required and must be the 1.0.0 plugin schema")
    if "name" not in data:
        fail(manifest, "name is required")
    elif not PLUGIN_NAME.match(data["name"]) or not 1 <= len(data["name"]) <= 64:
        fail(manifest, f"name {data['name']!r} breaks the schema pattern")
    elif data["name"] != directory:
        fail(manifest, f"name {data['name']!r} does not match its directory {directory!r}")
    for extra in sorted(set(data) - PLUGIN_FIELDS):
        fail(manifest, f"{extra!r} is not a field the schema allows")
    author = data.get("author")
    if isinstance(author, dict):
        for extra in sorted(set(author) - AUTHOR_FIELDS):
            fail(manifest, f"author.{extra} is not a field the schema allows")


def check_mcp(manifest: Path) -> None:
    try:
        data = json.loads(manifest.read_text())
    except json.JSONDecodeError as error:
        fail(manifest, f"not valid JSON — {error}")
        return
    if data.get("$schema") != MCP_SCHEMA:
        fail(manifest, "$schema is required and must be the 1.0.0 mcp schema")
    if "mcpServers" not in data:
        fail(manifest, "mcpServers is required")
    for extra in sorted(set(data) - {"$schema", "mcpServers"}):
        fail(manifest, f"{extra!r} is not a field the schema allows")
    for name, server in (data.get("mcpServers") or {}).items():
        kind = server.get("type")
        if kind == "stdio":
            required, allowed = {"type", "command"}, {"type", "command", "args", "env", "cwd"}
        elif kind in ("streamable-http", "sse"):
            required, allowed = {"type", "url"}, {"type", "url", "headers"}
        else:
            fail(manifest, f"{name}: type must be stdio, streamable-http or sse (got {kind!r})")
            continue
        for missing in sorted(required - set(server)):
            fail(manifest, f"{name}: {missing} is required for a {kind} server")
        for extra in sorted(set(server) - allowed):
            fail(manifest, f"{name}: {extra!r} is not allowed on a {kind} server")


def check_skill(skill: Path) -> None:
    directory = skill.parent.name
    text = skill.read_text()
    fields = parse_frontmatter(text)
    if fields is None:
        fail(skill, "no YAML frontmatter")
        return

    name = fields.get("name", "")
    if "name" not in fields:
        fail(skill, "name is required by the Agent Skills spec")
    elif not SKILL_NAME.match(name) or not 1 <= len(name) <= 64:
        fail(skill, f"name {name!r} must be 1-64 chars of a-z, 0-9 and single hyphens")
    elif name != directory:
        fail(skill, f"name {name!r} must match its directory {directory!r}")

    description = fields.get("description", "")
    if not description:
        fail(skill, "description is required and must not be empty")
    elif len(description) > MAX_DESCRIPTION:
        fail(skill, f"description is {len(description)} chars, over {MAX_DESCRIPTION}")

    compatibility = fields.get("compatibility", "")
    if len(compatibility) > MAX_COMPATIBILITY:
        fail(skill, f"compatibility is {len(compatibility)} chars, over {MAX_COMPATIBILITY}")

    for extra in sorted(set(fields) - SKILL_FIELDS):
        fail(skill, f"{extra!r} is not a frontmatter field the spec defines")

    lines = text.count("\n") + 1
    if lines > MAX_BODY_LINES:
        fail(skill, f"{lines} lines, over the {MAX_BODY_LINES} the spec recommends")


def check_unique(root: Path, plugins: list[Path]) -> None:
    """No name twice, skill or server, anywhere in the repository.

    Not a spec rule — a rule of the side that installs these. Its registry is
    flat, so a plugin is a unit of distribution rather than a namespace, and two
    components sharing a name collide at install time rather than here.
    """
    seen: dict[str, str] = {}
    for plugin in plugins:
        names = []
        skills = plugin / "skills"
        if skills.is_dir():
            names += [(c.name, f"{plugin.name}/skills/{c.name}") for c in sorted(skills.glob("*")) if (c / "SKILL.md").is_file()]
        manifest = plugin / "mcp.json"
        if manifest.is_file():
            try:
                servers = json.loads(manifest.read_text()).get("mcpServers") or {}
            except json.JSONDecodeError:
                servers = {}
            names += [(name, f"{plugin.name}/mcp.json") for name in sorted(servers)]
        for name, where in names:
            if name in seen:
                fail(root, f"name {name!r} is used by both {seen[name]} and {where}")
            else:
                seen[name] = where


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    plugins = sorted(p for p in (root / "plugins").iterdir() if p.is_dir())
    if not plugins:
        print("no plugins found — is this the repository root?")
        return 1

    skills = 0
    for plugin in plugins:
        manifest = plugin / "plugin.json"
        if manifest.is_file():
            check_plugin(manifest)
        else:
            fail(plugin, "plugin.json is required")
        if (plugin / "mcp.json").is_file():
            check_mcp(plugin / "mcp.json")
        # One level only: the spec tells clients not to search deeper, so a skill
        # nested further down would pass a check nothing would ever load.
        for child in sorted((plugin / "skills").glob("*")) if (plugin / "skills").is_dir() else []:
            if (child / "SKILL.md").is_file():
                check_skill(child / "SKILL.md")
                skills += 1
            elif child.is_dir():
                fail(child, "a skills/ child with no SKILL.md is not a skill")

    check_unique(root, plugins)

    for problem in problems:
        print(f"  {problem}")
    print(
        f"\n{len(plugins)} plugins, {skills} skills — "
        + ("conform to Agent Plugins 1.0.0" if not problems else f"{len(problems)} problems")
    )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
