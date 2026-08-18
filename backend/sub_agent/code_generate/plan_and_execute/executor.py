from typing import Any

from langchain_core.runnables import RunnableConfig
from langchain_openai.chat_models.base import BaseChatOpenAI
from langgraph.types import Checkpointer

from backend.sub_agent.code_generate.agents.agent_state import CodeAgentState

class Executor:
    """执行器 - 负责按计划执行步骤"""

    def __init__(
            self,
            model: BaseChatOpenAI,
            config: RunnableConfig,
            check_pointer: Checkpointer,
            agent_name: str
    ):
        self.model = model
        self.config = config
        self.agent_name = agent_name
        self.check_pointer = check_pointer

    def execute(self, agent_state: CodeAgentState, step: Any) -> CodeAgentState | None:
        pass