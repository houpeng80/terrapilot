from __future__ import annotations

from dataclasses import dataclass

from langchain_core.messages import AnyMessage
from langgraph.runtime import Runtime

from backend.config.config import get_agent_config
from backend.memory.message_processing import filter_messages_for_memory, detect_correction, detect_reinforcement
from backend.memory.queue import get_memory_queue

@dataclass(frozen=True)
class SummarizationEvent:
    """Context emitted before conversation history is summarized away."""

    messages_to_summarize: tuple[AnyMessage, ...]
    preserved_messages: tuple[AnyMessage, ...]
    thread_id: str | None
    user_id: str | None
    agent_name: str | None
    runtime: Runtime

def memory_flush_hook(event: SummarizationEvent) -> None:
    """Flush messages about to be summarized into the memory queue."""
    if not get_agent_config().user_memory or not event.thread_id:
        return

    filtered_messages = filter_messages_for_memory(list(event.messages_to_summarize))
    user_messages = [message for message in filtered_messages if getattr(message, "type", None) == "human"]
    assistant_messages = [message for message in filtered_messages if getattr(message, "type", None) == "ai"]
    if not user_messages or not assistant_messages:
        return

    correction_detected = detect_correction(filtered_messages)
    reinforcement_detected = not correction_detected and detect_reinforcement(filtered_messages)
    queue = get_memory_queue()
    queue.add_nowait(
        thread_id=event.thread_id,
        user_id=event.user_id,
        messages=filtered_messages,
        agent_name=event.agent_name,
        correction_detected=correction_detected,
        reinforcement_detected=reinforcement_detected,
    )
