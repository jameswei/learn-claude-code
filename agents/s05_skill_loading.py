#!/usr/bin/env python3
# Harness: on-demand knowledge -- domain expertise, loaded when the model asks.
"""
s05_skill_loading.py - Skills

Two-layer skill injection that avoids bloating the system prompt:

    Layer 1 (cheap): skill names in system prompt (~100 tokens/skill)
    Layer 2 (on demand): full skill body in tool_result

    skills/
      pdf/
        SKILL.md          <-- frontmatter (name, description) + body
      code-review/
        SKILL.md

    System prompt:
    +--------------------------------------+
    | You are a coding agent.              |
    | Skills available:                    |
    |   - pdf: Process PDF files...        |  <-- Layer 1: metadata only
    |   - code-review: Review code...      |
    +--------------------------------------+

    When model calls load_skill("pdf"):
    +--------------------------------------+
    | tool_result:                         |
    | <skill>                              |
    |   Full PDF processing instructions   |  <-- Layer 2: full body
    |   Step 1: ...                        |
    |   Step 2: ...                        |
    | </skill>                             |
    +--------------------------------------+

Key insight: "Don't put everything in the system prompt. Load on demand."
"""

import os
import re
import subprocess
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv(override=True)

if os.getenv("ANTHROPIC_BASE_URL"):
    os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)

WORKDIR = Path.cwd()
client = Anthropic(base_url=os.getenv("ANTHROPIC_BASE_URL"))
MODEL = os.environ["MODEL_ID"]
# where all skills are stored, each skill is structured as a directory with a `SKILL.md` file, which must follow a specific format like below:
# 1. a YAML frontmatter, which defines the skill's name and a short description about what it can do.
# 2. a MARKDOWN body, which contains the detailed description and usage instructions.
# skill, not like tools, only compact and summarized information are present in system prompt, then gradually load the full content into `tool_result` when needed. this approach consumes less tokens than bunch of tools schemas.
# for example, user asks to set up a new project with typescript and vue, which requires framework-specific knowledge.
# the model will try to load corresponding skills, like 'typescript.SKILL.md' and 'vue.SKILL.md'.
# then content will be injected as tool_result, next using skill-provided knowledge to set up the project.

SKILLS_DIR = WORKDIR / "skills"

# skill-loading follows a 2 layer architecture, in layer 1 only compact and summarized skill descriptions are injected into system prompt. while in layer 2, skills' full instructions are loaded on demand through tool_result.

# -- SkillLoader: scan skills/<name>/SKILL.md with YAML frontmatter --
class SkillLoader:
    def __init__(self, skills_dir: Path):
        # skills are files put together in a specific directory
        self.skills_dir = skills_dir
        # a dict to store all defined skills, key is skill name, value is a dict contains metadata and body.
        self.skills = {}
        self._load_all()

    # `_load_all` will recursively scan all `SKILL.md` files in given directory and load them into memory.
    def _load_all(self):
        if not self.skills_dir.exists():
            return
        # only find files named 'SKILL.md', like the following:
        # skills/<whatever_directory_name>/SKILL.md
        for f in sorted(self.skills_dir.rglob("SKILL.md")):
            # read file content
            text = f.read_text()
            # parse frontmatter
            meta, body = self._parse_frontmatter(text)
            # extra 'name' from 'SKILL.md' or use directory name as default
            name = meta.get("name", f.parent.name)
            self.skills[name] = {"meta": meta, "body": body, "path": str(f)}

    # `_parse_frontmatter` will parse the content written in YAML format between `---` delimeter in 'SKILL.md' file.
    # returns a dict as metadata defined as YAML frontmatter, and the rest of the content, which usually written in MARKDOWN format, as body.
    def _parse_frontmatter(self, text: str) -> tuple:
        """Parse YAML frontmatter between --- delimiters."""
        match = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
        if not match:
            return {}, text
        meta = {}
        for line in match.group(1).strip().splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                meta[key.strip()] = val.strip()
        return meta, match.group(2).strip()

    # `get_descriptions` only returns a summarized, short description for each skill.
    # the output will be append to system prompt to let the model know what skills are available.
    # this approach is very similar with passing tools schema to the model, but without any overhead of schema parsing and validation.
    def get_descriptions(self) -> str:
        """Layer 1: short descriptions for the system prompt."""
        if not self.skills:
            return "(no skills available)"
        lines = []
        # iterate all skills, put name and description together as a line
        for name, skill in self.skills.items():
            desc = skill["meta"].get("description", "No description")
            tags = skill["meta"].get("tags", "")
            line = f"  - {name}: {desc}"
            if tags:
                line += f" [{tags}]"
            lines.append(line)
        # finally, join all one-line summary of skill together
        return "\n".join(lines)

    def get_content(self, name: str) -> str:
        """Layer 2: full skill body returned in `tool_result`."""
        skill = self.skills.get(name)
        if not skill:
            return f"Error: Unknown skill '{name}'. Available: {', '.join(self.skills.keys())}"
        # similar with <reminder> tag, just let the model know here's a skill with name and what it can do.
        return f"<skill name=\"{name}\">\n{skill['body']}\n</skill>"


SKILL_LOADER = SkillLoader(SKILLS_DIR)

# Layer 1: skill metadata injected into system prompt
# in system prompt, skills are summarized, compact, and always present.
# each skill is a one-line summary with name and description.
SYSTEM = f"""You are a coding agent at {WORKDIR}.
Use load_skill to access specialized knowledge before tackling unfamiliar topics.
Skills available:
{SKILL_LOADER.get_descriptions()}"""


# -- Tool implementations --
def safe_path(p: str) -> Path:
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"Path escapes workspace: {p}")
    return path

def run_bash(command: str) -> str:
    dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
    if any(d in command for d in dangerous):
        return "Error: Dangerous command blocked"
    try:
        r = subprocess.run(command, shell=True, cwd=WORKDIR,
                           capture_output=True, text=True, timeout=120)
        out = (r.stdout + r.stderr).strip()
        return out[:50000] if out else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Timeout (120s)"

def run_read(path: str, limit: int = None) -> str:
    try:
        lines = safe_path(path).read_text().splitlines()
        if limit and limit < len(lines):
            lines = lines[:limit] + [f"... ({len(lines) - limit} more)"]
        return "\n".join(lines)[:50000]
    except Exception as e:
        return f"Error: {e}"

def run_write(path: str, content: str) -> str:
    try:
        fp = safe_path(path)
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content)
        return f"Wrote {len(content)} bytes"
    except Exception as e:
        return f"Error: {e}"

def run_edit(path: str, old_text: str, new_text: str) -> str:
    try:
        fp = safe_path(path)
        content = fp.read_text()
        if old_text not in content:
            return f"Error: Text not found in {path}"
        fp.write_text(content.replace(old_text, new_text, 1))
        return f"Edited {path}"
    except Exception as e:
        return f"Error: {e}"

# same tools but with one new tool `load_skill`, which is used to load specific skill by name.
# skill is actually domain knowledge, but not like tools, we only inject it via tool_result when needed.
TOOL_HANDLERS = {
    "bash":       lambda **kw: run_bash(kw["command"]),
    "read_file":  lambda **kw: run_read(kw["path"], kw.get("limit")),
    "write_file": lambda **kw: run_write(kw["path"], kw["content"]),
    "edit_file":  lambda **kw: run_edit(kw["path"], kw["old_text"], kw["new_text"]),
    # `load_skill` returns the skill full content, which then is injected into `tool_result`. the model will see in context and follow the instruction precisely, no any prompt explosion.
    "load_skill": lambda **kw: SKILL_LOADER.get_content(kw["name"]),
}

TOOLS = [
    {"name": "bash", "description": "Run a shell command.",
     "input_schema": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}},
    {"name": "read_file", "description": "Read file contents.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["path"]}},
    {"name": "write_file", "description": "Write content to file.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}},
    {"name": "edit_file", "description": "Replace exact text in file.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "old_text": {"type": "string"}, "new_text": {"type": "string"}}, "required": ["path", "old_text", "new_text"]}},
    # `load_skill` as a standard tool, which is used to load specialized knowledge by name.
    {"name": "load_skill", "description": "Load specialized knowledge by name.",
     "input_schema": {"type": "object", "properties": {"name": {"type": "string", "description": "Skill name to load"}}, "required": ["name"]}},
]


def agent_loop(messages: list):
    # still the same loop
    while True:
        response = client.messages.create(
            # system prompt contains a summarized list of skills
            # tools contains a standard tool to load specific skill
            model=MODEL, system=SYSTEM, messages=messages,
            tools=TOOLS, max_tokens=8000,
        )
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":
            return
        results = []
        for block in response.content:
            if block.type == "tool_use":
                # there's no any special logic for handling `load_skill`
                handler = TOOL_HANDLERS.get(block.name)
                try:
                    output = handler(**block.input) if handler else f"Unknown tool: {block.name}"
                except Exception as e:
                    output = f"Error: {e}"
                print(f"> {block.name}: {str(output)[:200]}")
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": str(output)})
        messages.append({"role": "user", "content": results})


if __name__ == "__main__":
    history = []
    while True:
        try:
            query = input("\033[36ms05 >> \033[0m")
        except (EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ("q", "exit", ""):
            break
        history.append({"role": "user", "content": query})
        agent_loop(history)
        response_content = history[-1]["content"]
        if isinstance(response_content, list):
            for block in response_content:
                if hasattr(block, "text"):
                    print(block.text)
        print()
