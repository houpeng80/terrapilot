import asyncio
import logging
from typing import override

from langchain.agents import AgentState
from langchain.agents.middleware import SummarizationMiddleware
from langchain_core.messages import HumanMessage, RemoveMessage
from langgraph.config import get_config
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.runtime import Runtime

from assistant.memory.message_processing import filter_messages_for_memory, detect_correction, detect_reinforcement
from assistant.memory.queue import get_memory_queue

logger = logging.getLogger(__name__)

class ContextSummarizationMiddleware(SummarizationMiddleware):

    def __init__(
            self,
            *args,
            agent_name: str | None = None,
            **kwargs,
    ):
        super().__init__(*args,**kwargs)
        self._agent_name = agent_name

    def before_model(self, state: AgentState, runtime: Runtime) -> dict | None:
        return self._maybe_summarize(state)

    async def abefore_model(self, state: AgentState, runtime: Runtime) -> dict | None:
        return await self._amaybe_summarize(state)

    def _maybe_summarize(self, state: AgentState) -> dict | None:
        messages = state["messages"]
        self._ensure_message_ids(messages)

        total_tokens = self.token_counter(messages)
        if not self._should_summarize(messages, total_tokens):
            return None

        cutoff_index = self._determine_cutoff_index(messages)
        if cutoff_index <= 0:
            return None

        logger.info(f" begin to summarization the context message, messages length: {messages.__len__()}")

        messages_to_summarize, preserved_messages = self._partition_messages(messages, cutoff_index)
        # summary = self._create_summary(messages_to_summarize)
        # new_messages = self._build_new_messages(summary)
        logger.info(f" end summarization the context message")

        # 将要压缩的messages异步更新持久记忆
        asyncio.run(self.aupdate_memory(messages_to_summarize))

        return {
            "messages": [
                RemoveMessage(id=REMOVE_ALL_MESSAGES),
                # *new_messages,
                *preserved_messages,
            ]
        }

    async def _amaybe_summarize(self, state: AgentState) -> dict | None:
        messages = state["messages"]
        self._ensure_message_ids(messages)

        total_tokens = self.token_counter(messages)
        if not self._should_summarize(messages, total_tokens):
            return None

        cutoff_index = self._determine_cutoff_index(messages)
        if cutoff_index <= 0:
            return None

        logger.info(" begin to summarization the context message, messages length: ", messages.__len__())

        messages_to_summarize, preserved_messages = self._partition_messages(messages, cutoff_index)
        # summary = await self._acreate_summary(messages_to_summarize)
        # new_messages = self._build_new_messages(summary)
        logger.info("end summarization the context message")

        # 将要压缩的messages异步更新持久记忆
        asyncio.run(self.aupdate_memory(messages_to_summarize))

        return {
            "messages": [
                RemoveMessage(id=REMOVE_ALL_MESSAGES),
                # *new_messages,
                *preserved_messages,
            ]
        }

    @override
    def _build_new_messages(self, summary: str) -> list[HumanMessage]:
        """Override the base implementation to let the human message with the special name 'summary'.
        And this message will be ignored to display in the frontend, but still can be used as context for the model.
        """
        return [HumanMessage(content=f"Here is a summary of the conversation to date:\n\n{summary}", name="summary")]

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
