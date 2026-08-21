import logging
from typing import override, runtime_checkable, Protocol

from langchain.agents import AgentState
from langchain.agents.middleware import SummarizationMiddleware
from langchain_core.messages import HumanMessage, RemoveMessage, AnyMessage
from langgraph.config import get_config
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.runtime import Runtime

from backend.memory.summarization_hook import SummarizationEvent

logger = logging.getLogger(__name__)

@runtime_checkable
class BeforeSummarizationHook(Protocol):

    def __call__(self, event: SummarizationEvent) -> None: ...

class ContextSummarizationMiddleware(SummarizationMiddleware):

    def __init__(
        self,
        *args,
        agent_name: str | None = None,
        before_summarization: list[BeforeSummarizationHook] | None = None,
        **kwargs,
    ):
        super().__init__(*args,**kwargs)
        self._agent_name = agent_name
        self._before_summarization_hooks = before_summarization

    def before_model(self, state: AgentState, runtime: Runtime) -> dict | None:
        return self._maybe_summarize(state, runtime)

    async def abefore_model(self, state: AgentState, runtime: Runtime) -> dict | None:
        return await self._amaybe_summarize(state, runtime)

    def _maybe_summarize(self, state: AgentState, runtime: Runtime) -> dict | None:
        messages = state["messages"]
        self._ensure_message_ids(messages)

        total_tokens = self.token_counter(messages)
        if not self._should_summarize(messages, total_tokens):
            return None

        cutoff_index = self._determine_cutoff_index(messages)
        if cutoff_index <= 0:
            return None

        logger.info(f"begin to summarization the context message, messages length: {messages.__len__()}")

        messages_to_summarize, preserved_messages = self._partition_messages(messages, cutoff_index)
        summary = self._create_summary(messages_to_summarize)
        new_messages = self._build_new_messages(summary)
        logger.info(f"end summarization the context message")

        # 将要压缩的messages异步更新持久记忆
        self._fire_hooks(messages_to_summarize, preserved_messages, runtime)

        return {
            "messages": [
                RemoveMessage(id=REMOVE_ALL_MESSAGES),
                *new_messages,
                *preserved_messages,
            ]
        }

    async def _amaybe_summarize(self, state: AgentState, runtime: Runtime) -> dict | None:
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
        summary = await self._acreate_summary(messages_to_summarize)
        new_messages = self._build_new_messages(summary)
        logger.info("end summarization the context message")

        # 将要压缩的messages异步更新持久记忆
        self._fire_hooks(messages_to_summarize, preserved_messages, runtime)

        return {
            "messages": [
                RemoveMessage(id=REMOVE_ALL_MESSAGES),
                *new_messages,
                *preserved_messages,
            ]
        }

    @override
    def _build_new_messages(self, summary: str) -> list[HumanMessage]:
        """Override the base implementation to let the human message with the special name 'summary'.
        And this message will be ignored to display in the frontend, but still can be used as context for the model.
        """
        return [HumanMessage(content=f"Here is a summary of the conversation to date:\n\n{summary}", name="summary")]

    def _fire_hooks(
        self,
        messages_to_summarize: list[AnyMessage],
        preserved_messages: list[AnyMessage],
        runtime: Runtime,
    ) -> None:
        if not self._before_summarization_hooks:
            return

        thread_id = get_config().get("configurable", {}).get("thread_id")
        user_id = get_config().get("configurable", {}).get("user_id")
        event = SummarizationEvent(
            messages_to_summarize=tuple(messages_to_summarize),
            preserved_messages=tuple(preserved_messages),
            thread_id=thread_id,
            user_id=user_id,
            agent_name=self._agent_name,
            runtime=runtime,
        )

        for hook in self._before_summarization_hooks:
            try:
                hook(event)
            except Exception:
                hook_name = getattr(hook, "__name__", None) or type(hook).__name__
                logger.exception("before_summarization hook %s failed", hook_name)

