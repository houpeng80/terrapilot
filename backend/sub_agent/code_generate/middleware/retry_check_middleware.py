import logging
from typing import override, Any

from langchain.agents.middleware import AgentMiddleware, hook_config
from langgraph.runtime import Runtime
from langgraph.typing import ContextT

from backend.config.config import AgentConfig
from backend.sub_agent.code_generate.agents.agent_state import CodeAgentState

logger = logging.getLogger(__name__)

class RetryCheckMiddleware(AgentMiddleware[CodeAgentState]):

    state_schema = CodeAgentState

    def __init__(
            self,
            agent_config: AgentConfig,
            agent_name: str | None = None
    ):
        """Initialize the CodeCheckMiddlewareState"""
        super().__init__()
        self.agent_name = agent_name
        self.agent_config = agent_config

    @hook_config(can_jump_to=["end"])
    @override
    def before_model(self, state: CodeAgentState, runtime: Runtime[ContextT]) -> dict[str, Any] | None:
        return self.retry_check(state)

    @hook_config(can_jump_to=["end"])
    @override
    def abefore_model(self, state: CodeAgentState, runtime: Runtime[ContextT]) -> dict[str, Any] | None:
        return self.retry_check(state)

    def retry_check(self, state: CodeAgentState) -> dict[str, Any] | None:
        if state["current_step"] == "generating_code":
            logger.info(" agent {%s} execute the {%s} time", self.agent_name, state["code_retries_time"])
            if state["code_retries_time"] >= self.agent_config.code_retries:
                return {
                    "jump_to": "end"
                }
        if state["current_step"] == "generating_test":
            logger.info(" agent {%s} execute the {%s} time", self.agent_name, state["test_retries_time"])
            if state["test_retries_time"] >= self.agent_config.test_retries:
                return {
                    "jump_to": "end"
                }

        if state["current_step"] == "generating_doc":
            logger.info(" agent {%s} execute the {%s} time", self.agent_name, state["doc_retries_time"])
            if state["doc_retries_time"] >= self.agent_config.doc_retries:
                return {
                    "jump_to": "end"
                }
        return None
