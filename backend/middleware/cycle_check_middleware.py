import logging
from typing import override, Any

from langgraph.runtime import Runtime
from langchain.agents.middleware import AgentMiddleware
from langgraph.typing import ContextT
from langchain.agents.middleware.types import hook_config

from backend.config.config import get_agent_config
from backend.leader_agent.agent_state import TerrapilotAgentState

logger = logging.getLogger(__name__)

class CycleCheckMiddleware(AgentMiddleware[TerrapilotAgentState]):

    def __init__(self, agent_name: str | None = None):
        super().__init__()
        self._agent_name = agent_name

    @hook_config(can_jump_to=["end"])
    @override
    def before_model(self, state: TerrapilotAgentState, runtime: Runtime[ContextT]) -> dict[str, Any] | None:
        logger.info("invoke the model for the %s time", state["model_cycle_time"])
        if state["model_cycle_time"] > get_agent_config().model_cycle_max:
            print("循环次数达到最大值，请确认是否要继续")
            return {
                "jump_to": "end"
            }
        return None

    @hook_config(can_jump_to=["end"])
    @override
    def abefore_model(self, state: TerrapilotAgentState, runtime: Runtime[ContextT]) -> dict[str, Any] | None:
        logger.info("invoke the model for the %s time", state["model_cycle_time"])
        if state["model_cycle_time"] > get_agent_config().model_cycle_max:
            print("循环次数达到最大值，请确认是否要继续")
            return {
                "jump_to": "end"
            }

        return None

    @override
    def after_model(self, state: TerrapilotAgentState, runtime: Runtime) -> dict[str, Any] | None:
        return {
            "model_cycle_time" : state["model_cycle_time"] + 1
        }

    @override
    def aafter_model(self, state: TerrapilotAgentState, runtime: Runtime) -> dict[str, Any] | None:
        return {
            "model_cycle_time": state["model_cycle_time"] + 1
        }

