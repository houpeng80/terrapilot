from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware
from langchain_core.runnables import RunnableConfig
from langchain_openai.chat_models.base import BaseChatOpenAI
from langgraph.graph.state import StateGraph
from langgraph.types import Checkpointer, StateT, OutputT
from langgraph.typing import ContextT, InputT
from pydantic import BaseModel

from backend.config.config import AgentConfig
from backend.sub_agent.code_generate.agents.agent_state import CodeAgentState


class Planner:
    """规划器 - 负责将复杂问题分解为简单步骤"""

    def __init__(
            self,
            model: BaseChatOpenAI,
            config: RunnableConfig,
            check_pointer: Checkpointer,
            agent_config: AgentConfig,
            agent_name: str
    ):
        self.model = model
        self.agent_name = agent_name
        self.config = config
        self.check_pointer = check_pointer
        self.agent_config = agent_config

    def plan(self, agent_state: CodeAgentState) ->  StateGraph[StateT, ContextT, InputT, OutputT] | None:
        pass

    def create_planner_agent(self, response_format: BaseModel):
        agent = create_agent(
            name=self.agent_name,
            model=self.model,
            checkpointer=self.check_pointer,
            system_prompt=self.build_system_prompt_template(),
            middleware=self.build_middlewares(),
            response_format=response_format
        )
        return agent

    def build_middlewares(self) -> list[AgentMiddleware]:
        pass

    def build_system_prompt_template(self) -> str:
        pass