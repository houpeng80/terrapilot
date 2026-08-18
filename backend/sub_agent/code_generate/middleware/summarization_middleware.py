import logging

from langchain.agents.middleware import SummarizationMiddleware
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage, RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.runtime import Runtime

from backend.sub_agent.code_generate.agents.agent_state import CodeAgentState

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

    def before_model(self, state: CodeAgentState, runtime: Runtime) -> dict | None:
        return self._maybe_summarize(state)

    async def abefore_model(self, state: CodeAgentState, runtime: Runtime) -> dict | None:
        return await self._maybe_summarize(state)

    def _maybe_summarize(self, state: CodeAgentState) -> dict | None:
        messages = state["messages"]
        self._ensure_message_ids(messages)

        total_tokens = self.token_counter(messages)
        if not self._should_summarize(messages, total_tokens):
            return None

        logger.info(f" begin to summarization the context message, messages length: {messages.__len__()}")

        new_messages : list[HumanMessage|ToolMessage|AIMessage] = []
        length = messages.__len__()
        if length < 4:
            return None

        # 只保留最后的一个 ai_message 和 tool_message
        ai_message = None
        tool_message = None
        last_message = None
        i = 0
        for message in messages:
            if i == length - 1:
                break
            if isinstance(message, HumanMessage):
                new_messages.append(message)
            elif isinstance(message, AIMessage):
                if i == length - 1:
                    last_message = message
                else:
                    ai_message = message
            elif isinstance(message, ToolMessage):
                tool_message = message

        new_messages.append(ai_message)
        new_messages.append(tool_message)
        if last_message is not None:
            new_messages.append(last_message)

        logger.info(f" end summarization the context message, messages length: {new_messages.__len__()}")

        return {
            "messages": [
                RemoveMessage(id=REMOVE_ALL_MESSAGES),
                *new_messages
            ]
        }
