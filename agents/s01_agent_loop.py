#!/usr/bin/env python3
# Harness: the loop -- the model's first connection to the real world.
"""
s01_agent_loop.py - The Agent Loop

The entire secret of an AI coding agent in one pattern:

    while stop_reason == "tool_use":
        response = LLM(messages, tools)
        execute tools
        append results

    +----------+      +-------+      +---------+
    |   User   | ---> |  LLM  | ---> |  Tool   |
    |  prompt  |      |       |      | execute |
    +----------+      +---+---+      +----+----+
                          ^               |
                          |   tool_result |
                          +---------------+
                          (loop continues)

This is the core loop: feed tool results back to the model
until the model decides to stop. Production agents layer
policy, hooks, and lifecycle controls on top.
"""

import os
import subprocess

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv(override=True)

if os.getenv("ANTHROPIC_BASE_URL"):
    os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)

client = Anthropic(base_url=os.getenv("ANTHROPIC_BASE_URL"))
MODEL = os.environ["MODEL_ID"]

SYSTEM = f"You are a coding agent at {os.getcwd()}. Use bash to solve tasks. Act, don't explain."

TOOLS = [{
    "name": "bash",
    "description": "Run a shell command.",
    "input_schema": {
        "type": "object",
        "properties": {"command": {"type": "string"}},
        "required": ["command"],
    },
}]

# actual execution of 'bash' tool
def run_bash(command: str) -> str:
    # dangerous commands are not allowed
    dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
    if any(d in command for d in dangerous):
        return "Error: Dangerous command blocked"
    try:
        # spawn 出一个 shell 子进程，以当前 path 为 workingdirectory，捕获子进程的 stdout 和 stderr，并设置超时为 120s
        # 但这种执行 shell 子进程的方式有一些安全风险：
        # * 子进程权限继承自父进程，如果父进程有 root 权限，子进程也有 root 权限
        # * 通常以 `run(["ls", "-a"], shell=False)` 的方式执行，避免 shell 注入
        # * 或者使用 shlex.quote() 来转义
        r = subprocess.run(command, shell=True, cwd=os.getcwd(),
                           capture_output=True, text=True, timeout=120)
        # 将 stdout 和 stderr 合并，并去除前后空格
        out = (r.stdout + r.stderr).strip()
        # 如果输出为空，返回 "(no output)"
        # 如果输出超过 50000 字符，截取前 50000 字符
        return out[:50000] if out else "(no output)"
    # 如果超时，返回 "Error: Timeout (120s)"
    except subprocess.TimeoutExpired:
        return "Error: Timeout (120s)"


# -- The core pattern: a while loop that calls tools until the model stops --
# here's the entire agent, although it's little bit simplified.
def agent_loop(messages: list):
    # loop until the model stops calling tools (tool_use)
    while True:
        # send messages and tools (definition or schema) to the model
        response = client.messages.create(
            model=MODEL, system=SYSTEM, messages=messages,
            tools=TOOLS, max_tokens=8000,
        )
        # Append assistant turn
        # let user see how the model responds
        messages.append({"role": "assistant", "content": response.content})
        # If the model didn't call a tool, we're done
        if response.stop_reason != "tool_use":
            return
        # Execute each tool call, collect results
        results = []
        for block in response.content:
            # execute tool if model want to use it
            if block.type == "tool_use":
                print(f"\033[33m$ {block.input['command']}\033[0m")
                output = run_bash(block.input["command"])
                # let use see the output
                print(output[:200])
                # also append the output to the messages
                results.append({"type": "tool_result", "tool_use_id": block.id,
                                "content": output})
        # finally, all the outputs are appended as user's input and will be sent to the model again
        # messages is a accumulating list, each time we append a new user message no matter it's the user query or the tool output, but the model will see the entire history.
        messages.append({"role": "user", "content": results})


if __name__ == "__main__":
    history = []
    # loop until user quits
    while True:
        try:
            query = input("\033[36ms01 >> \033[0m")
        except (EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ("q", "exit", ""):
            break
        # user's query is the first message
        history.append({"role": "user", "content": query})
        agent_loop(history)
        response_content = history[-1]["content"]
        if isinstance(response_content, list):
            for block in response_content:
                if hasattr(block, "text"):
                    print(block.text)
        print()
