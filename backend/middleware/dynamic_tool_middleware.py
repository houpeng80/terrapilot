import logging

from typing import override, Callable, Any

from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import ModelRequest, ModelResponse, ModelCallResult
from langchain_core.messages import ToolMessage
from langgraph.prebuilt.tool_node import ToolCallRequest
from langgraph.types import Command

from backend.config.config import get_agent_config
from backend.leader_agent.agent_state import TerrapilotAgentState
from backend.tool.tool_executor import ToolExecutor
from backend.tool.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)

class DynamicToolMiddleware(AgentMiddleware[TerrapilotAgentState]):

    state_schema = TerrapilotAgentState

    def __init__(self, agent_name: str, tool_registry: ToolRegistry):
        super().__init__()
        self._agent_name = agent_name
        self.tool_registry = tool_registry
        self.tool_executor = ToolExecutor(tool_registry, max_retries=get_agent_config().tool_max_retries)

    @override
    def wrap_model_call(
            self,
            request: ModelRequest,
            handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelCallResult:
        intent = request.state["intent"]
        tools = self.tool_registry.get_tools_by_intent(intent)
        updated_request = request.override(tools=[*request.tools, *tools])
        return handler(updated_request)

    @override
    def awrap_model_call(
            self,
            request: ModelRequest,
            handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelCallResult:
        intent = request.state["intent"]
        tools = self.tool_registry.get_tools_by_intent(intent)
        updated_request = request.override(tools=[*request.tools, *tools])
        return handler(updated_request)

    @override
    def wrap_tool_call(self, request: ToolCallRequest, handler: Callable[[ToolCallRequest], ToolMessage | Command[Any]]):
        intent = request.state["intent"]
        tools = self.tool_registry.get_tools_by_intent(intent)
        tool_map = {tool.name: tool for tool in tools}
        tool_call_name = request.tool_call["name"]
        if tool_call_name in tool_map:
            return handler(request.override(tool=tool_map[tool_call_name]))

        return handler(request)

    @override
    def awrap_tool_call(self, request: ToolCallRequest, handler: Callable[[ToolCallRequest], ToolMessage | Command[Any]]):
        intent = request.state["intent"]
        tools = self.tool_registry.get_tools_by_intent(intent)
        tool_map = {tool.name: tool for tool in tools}
        tool_call_name = request.tool_call["name"]
        if tool_call_name in tool_map:
            return handler(request.override(tool=tool_map[tool_call_name]))

        return handler(request)

    def handler_tool(self, tool_name: str, tool_args: Any) -> ToolMessage | Command[Any]:
        tool_executor =

