"""Display state for Tau's Textual TUI."""

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Literal

from tau_agent.messages import AgentMessage
from tau_agent.types import JSONValue

ChatItemRole = Literal["user", "assistant", "tool", "error", "status"]


@dataclass(slots=True)
class ChatItem:
    """One rendered item in the TUI transcript."""

    role: ChatItemRole
    text: str


@dataclass(slots=True)
class TuiState:
    """Mutable display state for the interactive TUI."""

    items: list[ChatItem] = field(default_factory=list)
    assistant_buffer: str = ""
    running: bool = False
    error: str | None = None

    def add_item(self, role: ChatItemRole, text: str) -> None:
        """Append a transcript item."""
        self.items.append(ChatItem(role=role, text=text))

    def clear(self) -> None:
        """Clear visible transcript state without modifying durable session history."""
        self.items.clear()
        self.assistant_buffer = ""
        self.error = None

    def load_messages(self, messages: Iterable[AgentMessage]) -> None:
        """Populate the transcript from restored session messages."""
        for message in messages:
            if message.role == "user":
                self.add_item("user", message.content)
            elif message.role == "assistant":
                if message.content:
                    self.add_item("assistant", message.content)
                for tool_call in message.tool_calls:
                    self.add_item("tool", f"→ {tool_call.name} {tool_call.arguments}")
            elif message.role == "tool":
                self.add_item(
                    "tool",
                    format_tool_result_block(
                        name=message.name,
                        ok=message.ok,
                        content=message.content,
                        data=message.data,
                    ),
                )


def format_tool_result_block(
    *,
    name: str,
    ok: bool,
    content: str,
    data: dict[str, JSONValue] | None = None,
) -> str:
    """Format a tool result for live and restored transcript blocks."""
    status = "✓" if ok else "✗"
    lines = [f"{status} {name}"]
    if content:
        lines.append(content)
    patch = _result_patch(name=name, ok=ok, data=data)
    if patch:
        lines.extend(["", "Patch:", patch])
    return "\n".join(lines)


def _result_patch(
    *,
    name: str,
    ok: bool,
    data: dict[str, JSONValue] | None,
) -> str | None:
    if name != "edit" or not ok or data is None:
        return None
    patch = data.get("patch")
    return patch if isinstance(patch, str) and patch.strip() else None
