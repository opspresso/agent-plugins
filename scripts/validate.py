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

import ipaddress
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

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
MCP_CWD = re.compile(r"^(?:\./|\$\{PLUGIN_ROOT\}(?:/|$)|\$\{PLUGIN_DATA\}(?:/|$))")

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
KEY = re.compile(r"^([A-Za-z0-9_-]+):\s*(.*)$")

MAX_DESCRIPTION = 1024
MAX_COMPATIBILITY = 500
MAX_BODY_LINES = 500

# What the sync carries out of a skill directory besides SKILL.md. Anything else
# is left behind silently — an executable script or a bundled asset is still in
# git, still passes every other check, and simply is not there at run time, so a
# body that tells the model to run or copy it gives an instruction that cannot be
# followed. These numbers are the same ones skill-writer documents.
SKILL_FILE_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml", ".csv"}
MAX_FILE_BYTES = 64 * 1024
MAX_SKILL_FILES = 20
MAX_SKILL_BYTES = 200 * 1024

problems: list[str] = []
recommendations: list[str] = []
deployment_exceptions: list[str] = []


def fail(where: Path, message: str) -> None:
    problems.append(f"{where}: {message}")


def recommend(where: Path, message: str) -> None:
    recommendations.append(f"{where}: {message}")


def deployment_exception(where: Path, message: str) -> None:
    deployment_exceptions.append(f"{where}: {message}")


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
    if not isinstance(data, dict):
        fail(manifest, "manifest must be a JSON object")
        return
    if data.get("$schema") != PLUGIN_SCHEMA:
        fail(manifest, "$schema is required and must be the 1.0.0 plugin schema")
    if "name" not in data:
        fail(manifest, "name is required")
    elif not isinstance(data["name"], str):
        fail(manifest, "name must be a string")
    elif not PLUGIN_NAME.match(data["name"]) or not 1 <= len(data["name"]) <= 64:
        fail(manifest, f"name {data['name']!r} breaks the schema pattern")
    elif data["name"] != directory:
        fail(manifest, f"name {data['name']!r} does not match its directory {directory!r}")
    for extra in sorted(set(data) - PLUGIN_FIELDS):
        fail(manifest, f"{extra!r} is not a field the schema allows")

    for field in ("version", "description", "homepage", "repository", "license"):
        if field in data and not isinstance(data[field], str):
            fail(manifest, f"{field} must be a string")

    author = data.get("author")
    if author is not None and not isinstance(author, dict):
        fail(manifest, "author must be an object")
    elif isinstance(author, dict):
        for extra in sorted(set(author) - AUTHOR_FIELDS):
            fail(manifest, f"author.{extra} is not a field the schema allows")
        for field, value in author.items():
            if field in AUTHOR_FIELDS and not isinstance(value, str):
                fail(manifest, f"author.{field} must be a string")

    keywords = data.get("keywords")
    if keywords is not None and (
        not isinstance(keywords, list) or any(not isinstance(value, str) for value in keywords)
    ):
        fail(manifest, "keywords must be an array of strings")

    extensions = data.get("extensions")
    if extensions is not None and (
        not isinstance(extensions, dict)
        or any(not isinstance(value, dict) for value in extensions.values())
    ):
        fail(manifest, "extensions must be an object whose values are objects")


def check_mcp(manifest: Path) -> None:
    try:
        data = json.loads(manifest.read_text())
    except json.JSONDecodeError as error:
        fail(manifest, f"not valid JSON — {error}")
        return
    if not isinstance(data, dict):
        fail(manifest, "manifest must be a JSON object")
        return
    if data.get("$schema") != MCP_SCHEMA:
        fail(manifest, "$schema is required and must be the 1.0.0 mcp schema")
    if "mcpServers" not in data:
        fail(manifest, "mcpServers is required")
    for extra in sorted(set(data) - {"$schema", "mcpServers"}):
        fail(manifest, f"{extra!r} is not a field the schema allows")

    servers = data.get("mcpServers")
    if not isinstance(servers, dict):
        if "mcpServers" in data:
            fail(manifest, "mcpServers must be an object")
        return

    for name, server in servers.items():
        if not isinstance(server, dict):
            fail(manifest, f"{name}: server must be an object")
            continue
        kind = server.get("type")
        if kind in {"stdio", "sse"}:
            fail(
                manifest,
                f"{name}: repository policy requires streamable-http for Agent Studio",
            )
        if kind == "stdio":
            required, allowed = {"type", "command"}, {"type", "command", "args", "env", "cwd"}
            command = server.get("command")
            if "command" in server and (not isinstance(command, str) or not command):
                fail(manifest, f"{name}: command must be a non-empty string")
            args = server.get("args")
            if args is not None and (
                not isinstance(args, list) or any(not isinstance(value, str) for value in args)
            ):
                fail(manifest, f"{name}: args must be an array of strings")
            env = server.get("env")
            if env is not None:
                if not isinstance(env, dict) or any(
                    not isinstance(key, str) or not isinstance(value, str)
                    for key, value in env.items()
                ):
                    fail(manifest, f"{name}: env must be an object of string values")
                elif set(env) & {"PLUGIN_ROOT", "PLUGIN_DATA"}:
                    fail(manifest, f"{name}: env must not override PLUGIN_ROOT or PLUGIN_DATA")
            cwd = server.get("cwd")
            if cwd is not None and (not isinstance(cwd, str) or not MCP_CWD.match(cwd)):
                fail(
                    manifest,
                    f"{name}: cwd must start with ./, ${{PLUGIN_ROOT}} or ${{PLUGIN_DATA}}",
                )
        elif kind in ("streamable-http", "sse"):
            required, allowed = {"type", "url"}, {"type", "url", "headers"}
            if "headers" in server:
                fail(
                    manifest,
                    f"{name}: headers are forbidden by repository policy; configure them after install",
                )
            url = server.get("url")
            if not isinstance(url, str):
                fail(manifest, f"{name}: url must be a string")
            else:
                parsed = urlsplit(url)
                if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                    fail(manifest, f"{name}: url must be an absolute HTTP or HTTPS URL")
                elif parsed.username or parsed.password or parsed.fragment:
                    fail(manifest, f"{name}: url must not contain user information or a fragment")
                elif parsed.scheme == "http":
                    try:
                        loopback = ipaddress.ip_address(parsed.hostname).is_loopback
                    except ValueError:
                        loopback = parsed.hostname == "localhost"
                    if not loopback:
                        if parsed.hostname.endswith(".agent-mcps.svc.cluster.local"):
                            deployment_exception(
                                manifest,
                                f"{name}: private HTTP is an Agent Studio deployment exception; "
                                "portable Agent Plugins requires HTTPS",
                            )
                        else:
                            fail(manifest, f"{name}: a non-loopback endpoint must use HTTPS")
        else:
            fail(manifest, f"{name}: type must be stdio, streamable-http or sse (got {kind!r})")
            continue
        for missing in sorted(required - set(server)):
            fail(manifest, f"{name}: {missing} is required for a {kind} server")
        for extra in sorted(set(server) - allowed):
            fail(manifest, f"{name}: {extra!r} is not allowed on a {kind} server")

    extension = manifest.parent / "org.opspresso.agent-studio" / "mcp"
    docs = {path.stem: path for path in extension.glob("*.md")} if extension.is_dir() else {}
    for name in sorted(servers):
        doc = docs.get(name)
        if doc is None:
            fail(manifest, f"{name}: missing org.opspresso.agent-studio/mcp/{name}.md")
            continue
        fields = parse_frontmatter(doc.read_text())
        if fields is None or not fields.get("description"):
            fail(doc, "description is required in frontmatter for Agent Studio sync")
    for name, doc in sorted(docs.items()):
        if name not in servers:
            fail(doc, f"no matching {name!r} server in mcp.json")


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

    lines = len(text.splitlines())
    if lines > MAX_BODY_LINES:
        recommend(skill, f"{lines} lines, over the {MAX_BODY_LINES} the spec recommends")

    check_bundle(skill.parent)


def check_bundle(directory: Path) -> None:
    """Every attachment the sync carries alongside SKILL.md."""
    skill = directory / "SKILL.md"
    files = sorted(
        path for path in directory.rglob("*")
        if path.is_file() and path != skill
    )
    total = 0
    for path in files:
        size = path.stat().st_size
        total += size
        if path.suffix not in SKILL_FILE_SUFFIXES:
            allowed = " ".join(sorted(SKILL_FILE_SUFFIXES))
            fail(path, f"{path.suffix or 'no suffix'} is not carried by the sync — only {allowed}")
        if size > MAX_FILE_BYTES:
            fail(path, f"{size} bytes, over the {MAX_FILE_BYTES} limit per file")
    if len(files) > MAX_SKILL_FILES:
        fail(directory, f"{len(files)} attachments, over the {MAX_SKILL_FILES} a skill may carry")
    if total > MAX_SKILL_BYTES:
        fail(directory, f"{total} attachment bytes, over the {MAX_SKILL_BYTES} a skill may carry")


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
                data = json.loads(manifest.read_text())
            except json.JSONDecodeError:
                data = {}
            servers = data.get("mcpServers") if isinstance(data, dict) else {}
            if isinstance(servers, dict):
                names += [(name, f"{plugin.name}/mcp.json") for name in sorted(servers)]
        for name, where in names:
            if name in seen:
                fail(root, f"name {name!r} is used by both {seen[name]} and {where}")
            else:
                seen[name] = where


def main() -> int:
    problems.clear()
    recommendations.clear()
    deployment_exceptions.clear()

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
    for recommendation in recommendations:
        print(f"  warning: {recommendation}")
    for exception in deployment_exceptions:
        print(f"  warning: {exception}")
    print(
        f"\n{len(plugins)} plugins, {skills} skills — "
        + ("pass repository checks for Agent Plugins 1.0.0" if not problems else f"{len(problems)} problems")
        + (
            f" ({len(deployment_exceptions)} private-HTTP deployment exceptions)"
            if deployment_exceptions else ""
        )
    )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
