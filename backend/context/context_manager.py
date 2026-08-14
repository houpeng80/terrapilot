import asyncio
import logging
from typing import cast

from langchain_core.messages import AnyMessage, ToolMessage, AIMessage, RemoveMessage
from langchain_openai import ChatOpenAI
from langgraph.config import get_config
from langgraph.graph.message import REMOVE_ALL_MESSAGES

from config.config import get_agent_config
from leader_agent.agent_state import TerrapilotAgentState
from memory.message_processing import filter_messages_for_memory, detect_correction, detect_reinforcement
from memory.queue import get_memory_queue

logger = logging.getLogger(__name__)

class ContextManager:
    def __init__(self, model: ChatOpenAI):
        self.model = model
        self.agent_config = get_agent_config()

    def should_summarize(self, messages: list[AnyMessage]) -> bool:
        if len(messages) == 0:
            return False

        token_nums = self.model.get_num_tokens_from_messages(messages)
        if token_nums >= self.agent_config.summarization_trigger_tokens:
            return True

        if len(messages) > self.agent_config.summarization_trigger_messages:
            return True

        return False

    def context_summarize(self, messages: list[AnyMessage]) -> list[AnyMessage|RemoveMessage] | None:
        cutoff_index = self._determine_cutoff_index(messages)
        if cutoff_index <= 0:
            return None

        logger.info(f" begin to summarization the context message, messages length: {messages.__len__()}")
        messages_to_summarize, preserved_messages = self._partition_messages(messages, cutoff_index)

        # 将要压缩的messages异步更新持久记忆
        asyncio.run(self.aupdate_memory(messages_to_summarize))

        return [RemoveMessage(id=REMOVE_ALL_MESSAGES), *preserved_messages]


    @staticmethod
    def _partition_messages(conversation_messages: list[AnyMessage],cutoff_index: int) -> tuple[list[AnyMessage], list[AnyMessage]]:
        """Partition messages into those to summarize and those to preserve."""
        messages_to_summarize = conversation_messages[:cutoff_index]
        preserved_messages = conversation_messages[cutoff_index:]

        return messages_to_summarize, preserved_messages


    def _determine_cutoff_index(self, messages: list[AnyMessage]) -> int:
        """Choose cutoff index respecting retention configuration."""
        target_token_count = self.agent_config.summarization_trigger_tokens
        target_message_count = self.agent_config.summarization_trigger_messages
        token_based_cutoff = self._find_token_based_cutoff(messages, target_token_count)
        if token_based_cutoff is not None:
            return token_based_cutoff

        # None cutoff -> model profile data not available (caught in __init__ but
        # here for safety), fallback to message count
        return self._find_safe_cutoff(messages, target_message_count)

    def _find_safe_cutoff(self, messages: list[AnyMessage], messages_to_keep: int) -> int:
        """Find safe cutoff point that preserves AI/Tool message pairs.

        Returns the index where messages can be safely cut without separating
        related AI and Tool messages. Returns `0` if no safe cutoff is found.

        This is aggressive with summarization - if the target cutoff lands in the
        middle of tool messages, we advance past all of them (summarizing more).
        """
        if len(messages) <= messages_to_keep:
            return 0

        target_cutoff = len(messages) - messages_to_keep
        return self._find_safe_cutoff_point(messages, target_cutoff)

    def _find_token_based_cutoff(self, messages: list[AnyMessage], target_token_count: int) -> int | None:
        if not messages:
            return 0

        # Use binary search to identify the earliest message index that keeps the
        # suffix within the token budget.
        left, right = 0, len(messages)
        cutoff_candidate = len(messages)
        max_iterations = len(messages).bit_length() + 1
        for _ in range(max_iterations):
            if left >= right:
                break

            mid = (left + right) // 2
            if self.model.get_num_tokens_from_messages(messages[mid:]) <= target_token_count:
                cutoff_candidate = mid
                right = mid
            else:
                left = mid + 1

        if cutoff_candidate == len(messages):
            cutoff_candidate = left

        if cutoff_candidate >= len(messages):
            if len(messages) == 1:
                return 0
            cutoff_candidate = len(messages) - 1

        # Advance past any ToolMessages to avoid splitting AI/Tool pairs
        return self._find_safe_cutoff_point(messages, cutoff_candidate)

    @staticmethod
    def _find_safe_cutoff_point(messages: list[AnyMessage], cutoff_index: int) -> int:
        """Find a safe cutoff point that doesn't split AI/Tool message pairs.

        If the message at `cutoff_index` is a `ToolMessage`, search backward for the
        `AIMessage` containing the corresponding `tool_calls` and adjust the cutoff to
        include it. This ensures tool call requests and responses stay together.

        Falls back to advancing forward past `ToolMessage` objects only if no matching
        `AIMessage` is found (edge case).
        """
        if cutoff_index >= len(messages) or not isinstance(messages[cutoff_index], ToolMessage):
            return cutoff_index

        # Collect tool_call_ids from consecutive ToolMessages at/after cutoff
        tool_call_ids: set[str] = set()
        idx = cutoff_index
        while idx < len(messages) and isinstance(messages[idx], ToolMessage):
            tool_msg = cast("ToolMessage", messages[idx])
            if tool_msg.tool_call_id:
                tool_call_ids.add(tool_msg.tool_call_id)
            idx += 1

        # Search backward for AIMessage with matching tool_calls
        for i in range(cutoff_index - 1, -1, -1):
            msg = messages[i]
            if isinstance(msg, AIMessage) and msg.tool_calls:
                ai_tool_call_ids = {tc.get("id") for tc in msg.tool_calls if tc.get("id")}
                if tool_call_ids & ai_tool_call_ids:
                    # Found the AIMessage - move cutoff to include it
                    return i

        # Fallback: no matching AIMessage found, advance past ToolMessages to avoid
        # orphaned tool responses
        return idx

    async def aupdate_memory(self, summary_messages):
        thread_id = get_config().get("configurable", {}).get("thread_id")
        user_id = get_config().get("configurable", {}).get("user_id")

        filtered_messages = filter_messages_for_memory(summary_messages)
        user_messages = [m for m in filtered_messages if getattr(m, "type", None) == "human"]
        assistant_messages = [m for m in filtered_messages if getattr(m, "type", None) == "ai"]
        if not user_messages or not assistant_messages:
            return

        correction_detected = detect_correction(filtered_messages)
        reinforcement_detected = not correction_detected and detect_reinforcement(filtered_messages)
        queue = get_memory_queue()
        queue.add_nowait(
            thread_id=thread_id,
            messages=filtered_messages,
            agent_name=self._agent_name,
            user_id=user_id,
            correction_detected=correction_detected,
            reinforcement_detected=reinforcement_detected,
        )