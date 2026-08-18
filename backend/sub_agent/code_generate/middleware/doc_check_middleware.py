import logging
from typing import override, Any

from langchain.agents.middleware import AgentMiddleware, hook_config
from langchain_core.messages import AIMessage
from langgraph.runtime import Runtime

from backend.config.config import AgentConfig
from backend.sub_agent.code_generate.agents.agent_state import CodeAgentState

logger = logging.getLogger(__name__)

class DocCheckMiddleware(AgentMiddleware[CodeAgentState]):

    state_schema = CodeAgentState

    def __init__(
            self,
            agent_config: AgentConfig,
            agent_name: str | None = None
    ):
        """Initialize the CodeCheckMiddlewareState"""
        super().__init__()
        self._agent_name = agent_name
        self.agent_config = agent_config

    @hook_config(can_jump_to=["model"])
    @override
    def after_model(self, state: CodeAgentState, runtime: Runtime) -> dict[str, Any] | None:
        return self.doc_check(state)

    @hook_config(can_jump_to=["model"])
    @override
    def aafter_model(self, state: CodeAgentState, runtime: Runtime) -> dict[str, Any] | None:
        return self.doc_check(state)

    def doc_check(self, state: CodeAgentState) -> dict | None:
        latest_message = state['messages'][-1]

        if not self.agent_config.test_check:
            return None

        if isinstance(latest_message, AIMessage):
            if (latest_message.tool_calls and
                    latest_message.tool_calls[0]['name'] == "write_file" and
                    latest_message.tool_calls[0]['args']["content"]
            ):
                state["doc_result"] = latest_message.tool_calls[0]['args']["content"]
                return {
                    "doc_result": latest_message.tool_calls[0]['args']["content"],
                }
            elif latest_message.response_metadata["finish_reason"] and latest_message.response_metadata["finish_reason"]=="stop":
                # 这里添加 doc 校验功能，更新 doc_retries_time
                pass

        return None
