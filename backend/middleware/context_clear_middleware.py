import logging
from typing import override, Any

from langchain_core.messages import RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.runtime import Runtime
from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import AgentState

logger = logging.getLogger(__name__)

class ContextClearMiddleware(AgentMiddleware):

    def __init__(self, agent_name: str | None = None):
        super().__init__()
        self.agent_name = agent_name

    @override
    def before_agent(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        return {
            "messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES)]
        }

    @override
    def abefore_agent(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        return {
            "messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES)]
        }
