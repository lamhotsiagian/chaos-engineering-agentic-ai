"""
Memory: Short-Term Agent Memory & Scratchpad State.

Maintains the working conversational buffer and intermediate reasoning steps
for the active execution turn.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Message:
    role: str  # 'user', 'assistant', 'system', 'tool'
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class ShortTermMemory:
    """Manages short-term context window buffer for agent loops."""

    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages
        self.messages: List[Message] = []

    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Append a message, enforcing window pruning if max capacity exceeded."""
        self.messages.append(Message(role=role, content=content, metadata=metadata or {}))
        if len(self.messages) > self.max_messages:
            # Preserve system prompt if present, prune oldest user/assistant messages
            if self.messages and self.messages[0].role == "system":
                self.messages = [self.messages[0]] + self.messages[-(self.max_messages - 1):]
            else:
                self.messages = self.messages[-self.max_messages:]

    def get_formatted_prompt(self) -> str:
        """Serialize message history into a single prompt string."""
        lines = []
        for msg in self.messages:
            lines.append(f"[{msg.role.upper()}]: {msg.content}")
        return "\n".join(lines)

    def clear(self) -> None:
        """Clear memory buffer."""
        self.messages.clear()
