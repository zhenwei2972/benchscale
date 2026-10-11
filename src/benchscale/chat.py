"""The built-in chat: Claude drives the same tools as the MCP server.

Needs Anthropic credentials (ANTHROPIC_API_KEY, or a profile from
`ant auth login`). Without them, use the MCP server from Claude Desktop or
Claude Code instead - same tools, no key needed here.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from . import tools
from .mcp_server import INSTRUCTIONS

MODEL = "claude-opus-5-5"


def credentials_available() -> tuple[bool, str]:
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        return True, "environment"
    if (Path.home() / ".config" / "anthropic").exists():
        return True, "ant auth profile"
    return False, ("No Anthropic credentials found. Set ANTHROPIC_API_KEY (or run `ant auth login`), "
                   "or chat from Claude Desktop / Claude Code through the benchscale MCP server.")


def _tool_set(made: list[str]):
    from anthropic import beta_tool

    def wrap(fn):
        def run(**kwargs):
            result = fn(**kwargs)
            if isinstance(result, dict) and result.get("design_id"):
                made.append(result["design_id"])
            return json.dumps(result, default=str)
        run.__name__, run.__doc__ = fn.__name__, fn.__doc__
        run.__signature__ = __import__("inspect").signature(fn)
        run.__annotations__ = getattr(fn, "__annotations__", {})
        return beta_tool(run)

    return [wrap(f) for f in (tools.search_references, tools.get_reference, tools.add_measured_reference,
                              tools.list_templates, tools.describe_template, tools.design_part,
                              tools.list_base_models, tools.render_base_model)]


class ChatSession:
    """One conversation. History is kept append-only, as the API expects."""

    def __init__(self) -> None:
        import anthropic
        self.client = anthropic.Anthropic()
        self.messages: list = []

    def send(self, text: str) -> dict:
        made: list[str] = []
        self.messages.append({"role": "user", "content": text})
        runner = self.client.beta.messages.tool_runner(
            model=MODEL,
            max_tokens=16000,
            system=INSTRUCTIONS,
            tools=_tool_set(made),
            messages=self.messages,
            output_config={"effort": "high"},
            betas=["server-side-fallback-2026-07-01"],
            extra_body={"fallbacks": "default"},     # retry on a fallback model if a turn is declined
        )
        last = None
        for message in runner:
            last = message
            self.messages.append({"role": "assistant", "content": message.content})
            response = runner.generate_tool_call_response()
            if response is not None:
                self.messages.append(response)
        reply = ""
        if last is not None:
            if last.stop_reason == "refusal":
                reply = "The model declined this request."
            else:
                reply = "\n".join(b.text for b in last.content if b.type == "text")
        return {"reply": reply, "designs": made}
