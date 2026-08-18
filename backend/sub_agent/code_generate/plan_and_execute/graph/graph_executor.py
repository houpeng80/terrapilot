import logging

from langchain_core.runnables import RunnableConfig
from langchain_openai.chat_models.base import BaseChatOpenAI
from langgraph.graph import StateGraph
from langgraph.types import Checkpointer, StateT, OutputT
from langgraph.typing import ContextT, InputT

from backend.sub_agent.code_generate.agents.agent_state import CodeAgentState
from backend.sub_agent.code_generate.plan_and_execute.executor import Executor

logger = logging.getLogger(__name__)

AGENT_NAME = "graph_executor_agent"

class GraphExecutor(Executor):
    """执行器 - 负责将执行规划期规划的步骤"""

    def __init__(
            self,
            model: BaseChatOpenAI,
            config: RunnableConfig,
            check_pointer: Checkpointer,
    ):
        super(self.__class__, self).__init__(model, config, check_pointer, AGENT_NAME)

    def execute(self, agent_state: CodeAgentState, graph: StateGraph[StateT, ContextT, InputT, OutputT]) -> CodeAgentState | None:
        """按计划执行任务"""
        logger.info(" begin to execute graph plan ")
        print(f"\n--- begin to execute graph plan ---")

        try:
            agent = graph.compile(
                name=AGENT_NAME,
                checkpointer=self.check_pointer,
            )

            agent.invoke(agent_state, self.config)

            print(f"\n ✅ execute graph plan complete ")
            logger.info(" graph plan execute complete ")
        except Exception as e:
            print(f"\n ❌ execute graph plan fail: {e}")
            logger.info(" graph plan execute fail: {s} ", e)
            return None

        return agent.get_state(self.config).values
