import logging
import os
from pathlib import Path
from typing import override, Any
from collections.abc import  Callable

from langgraph.runtime import Runtime
from langchain.agents.middleware import AgentMiddleware
from langgraph.typing import ContextT
from langchain.agents.middleware.types import ModelCallResult, ModelRequest, ModelResponse
from langgraph.prebuilt.tool_node import ToolCallRequest
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from assistant.config.config import get_app_config
from assistant.lead_agent.agent_state import OncallAgentState

log_level = get_app_config().log_level

logging_level = str

if log_level == "info" :
    logging_level = logging.INFO
elif log_level == "debug" :
    logging_level = logging.DEBUG
elif log_level == "warning" :
    logging_level = logging.WARNING
elif log_level == "error" :
    logging_level = logging.ERROR

logging.basicConfig(level=logging_level,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    encoding='utf-8',
                    filename=Path(__file__).parents[2] / "terraform_oncall_assistant.log")
logger = logging.getLogger(__name__)

TOOL_CALL_TRACE_PATH = Path(__file__).parents[2] / "benckmark"

class LoggingMiddleware(AgentMiddleware):

    def __init__(self, agent_name: str | None = None):
        super().__init__()
        self.agent_name = agent_name

    @override
    def before_agent(self, state: OncallAgentState, runtime: Runtime[ContextT]) -> dict[str, Any] | None:
        logger.info(" agent {%s} begin execute ", self.agent_name)
        logger.info(" state messages: %s ", state.get("messages"))
        return None

    @override
    def abefore_agent(self, state: OncallAgentState, runtime: Runtime) -> dict[str, Any] | None:
        logger.info(" agent {%s} begin execute ", self.agent_name)
        return None

    @override
    def after_agent(self, state: OncallAgentState, runtime: Runtime) -> dict[str, Any] | None:
        logger.info(" agent {%s} execute complete ", self.agent_name)
        return None

    @override
    def aafter_agent(self, state: OncallAgentState, runtime: Runtime) -> dict[str, Any] | None:
        logger.info(" agent {%s} execute complete ", self.agent_name)
        return None

    @override
    def wrap_model_call(
            self,
            request: ModelRequest,
            handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelCallResult:
        model_name = request.model.model_name

        logger.info(" model {%s} begin execute", model_name)
        logger.debug("request info: {%s}", request)

        response = handler(request)

        logger.info(" model {%s} execute complete", model_name)
        logger.debug("response info: {%s}", response)

        return response

    @override
    def awrap_model_call(
            self,
            request: ModelRequest[ContextT],
            handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelCallResult:
        model_name = request.model.model_name

        logger.info(" model {%s} begin execute", model_name)
        logger.debug("request info: {%s}", request)

        response = handler(request)

        logger.info(" model {%s} execute complete", model_name)
        logger.debug("response info: {%s}", response)

        return response

    def wrap_tool_call(
            self,
            request: ToolCallRequest,
            handler: Callable[[ToolCallRequest],
            ToolMessage | Command[Any]]
    ) -> ToolMessage | Command[Any]:
        tool_name = request.tool_call["name"]
        tool_args = request.tool_call["args"]

        logger.info(" agent {%s} call tool: tool=%s args=%s",self.agent_name, tool_name, tool_args)
        if get_app_config().open_tool_call_trace:
            file_path = TOOL_CALL_TRACE_PATH / f"{self.agent_name}.txt"
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(f"tool_name: {tool_name}, args: {tool_args}\n")

        resource = handler(request)

        logger.info(" agent {%s} call response: %s ", self.agent_name, resource)
        return resource
