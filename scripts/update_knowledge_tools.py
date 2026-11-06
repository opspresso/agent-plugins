#!/usr/bin/env python3
"""Refresh scripts/knowledge-tools.json from an agent-knowledge checkout.

    python3 scripts/update_knowledge_tools.py ../agent-knowledge [--ref origin/main]

agent-knowledge is private, so CI cannot read it. validate.py checks skills
against this committed snapshot instead. Run this after Agent Knowledge adds,
renames or removes an MCP tool, and commit the result.

The tool list is every `registerTool(...)` call under `src/`, with
`mcpToolNames.<key>` resolved through `src/lib/mcp-tool-names.ts`. Files are
read from the given Git ref, not the working tree, so local edits do not leak
into the snapshot.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SNAPSHOT = Path(__file__).resolve().parent / "knowledge-tools.json"
NAMES_FILE = "src/lib/mcp-tool-names.ts"
NAME_ENTRY = re.compile(r'(\w+):\s*"([a-z][a-z0-9_]*)"')
REGISTER = re.compile(r'registerTool\(\s*(?:"([a-z][a-z0-9_]*)"|mcpToolNames\.(\w+))')


def git(source: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(source), *args], check=True, capture_output=True, text=True).stdout


def extract(sources: dict[str, str]) -> list[str]:
    """Tool names registered in the given {path: text} sources."""
    names = dict(NAME_ENTRY.findall(sources.get(NAMES_FILE, "")))
    tools: set[str] = set()
    for path, text in sources.items():
        for literal, key in REGISTER.findall(text):
            if key and key not in names:
                raise ValueError(f"{path}: mcpToolNames.{key} is not defined in {NAMES_FILE}")
            tools.add(literal or names[key])
    if not tools:
        raise ValueError("no registerTool calls found; is this agent-knowledge?")
    return sorted(tools)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path, help="agent-knowledge checkout")
    parser.add_argument("--ref", default="origin/main", help="Git ref to read (default: origin/main)")
    args = parser.parse_args()

    commit = git(args.source, "rev-parse", "--verify", f"{args.ref}^{{commit}}").strip()
    paths = [p for p in git(args.source, "ls-tree", "-r", "--name-only", commit, "src").splitlines() if p.endswith(".ts")]
    sources = {path: git(args.source, "show", f"{commit}:{path}") for path in paths}
    tools = extract(sources)
    SNAPSHOT.write_text(json.dumps({"repository": "opspresso/agent-knowledge", "commit": commit, "tools": tools}, indent=2) + "\n")
    print(f"wrote {len(tools)} tools from agent-knowledge {commit[:7]} to {SNAPSHOT.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
