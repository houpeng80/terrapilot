import logging
from typing import override, Any

from langchain.agents.middleware import AgentMiddleware
from langgraph.runtime import Runtime

from assistant.lead_agent.agent_state import OncallAgentState

logger = logging.getLogger(__name__)

class TokenUsageMiddleware(AgentMiddleware[OncallAgentState]):
    """Logs token usage from model response usage_metadata."""

    state_schema = OncallAgentState

    def __init__(self, agent_name: str | None = None):
        super().__init__()
        self._agent_name = agent_name

    @override
    def after_model(self, state: OncallAgentState, runtime: Runtime) -> dict[str, Any] | None:
        return self._log_usage(state)

    @override
    async def aafter_model(self, state: OncallAgentState, runtime: Runtime) -> dict[str, Any] | None:
        return self._log_usage(state)

    def _log_usage(self, state: OncallAgentState) -> dict | None:
        messages = state.get("messages", [])
        if not messages:
            return None
        last = messages[-1]
        usage = getattr(last, "usage_metadata", None)
        if usage:
            state["input_token_statistics"] = state.get("input_token_statistics", 0) + usage.get("input_tokens", "?")
            state["output_token_statistics"] = state.get("output_token_statistics", 0) + usage.get("output_tokens", "?")
            state["total_token_statistics"] = state.get("total_token_statistics", 0) + usage.get("total_tokens", "?")

            logger.info(
                "agent {%s} invoke model token usage: input=%s output=%s total=%s",
                self._agent_name,
                usage.get("input_tokens", "?"),
                usage.get("output_tokens", "?"),
                usage.get("total_tokens", "?"),
            )
        return {
            "input_token_statistics": state["input_token_statistics"],
            "output_token_statistics": state["output_token_statistics"],
            "total_token_statistics": state["total_token_statistics"],
        }

    @override
    def after_agent(self, state: OncallAgentState, runtime: Runtime) -> dict[str, Any] | None:
        logger.info(
            "agent {%s} token usage statistics: input_statistics=%s output_statistics=%s total_statistics=%s",
            self._agent_name,
            state["input_token_statistics"],
            state["output_token_statistics"],
            state["total_token_statistics"],
        )
        return None

    @override
    async def aafter_agent(self, state: OncallAgentState, runtime: Runtime) -> dict[str, Any] | None:
        logger.info(
            "agent {%s} token usage statistics: input_statistics=%s output_statistics=%s total_statistics=%s",
            self._agent_name,
            state["input_token_statistics"],
            state["output_token_statistics"],
            state["total_token_statistics"],
        )
        return None
