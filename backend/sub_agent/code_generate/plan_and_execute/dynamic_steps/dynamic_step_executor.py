import threading
from typing import List, Any

from langchain_core.runnables import RunnableConfig
from langchain_openai.chat_models.base import BaseChatOpenAI
from langgraph.types import Checkpointer

from backend.sub_agent.code_generate.agents.agent_state import CodeAgentState
from backend.sub_agent.code_generate.agents.generate import Generate
from backend.sub_agent.code_generate.plan_and_execute.executor import Executor

AGENT_NAME = "dynamic_step_executor_agent"

class DynamicStepExecutor(Executor):
    """执行器 - 负责将执行规划期规划的步骤"""

    lock = threading.Lock()

    def __init__(
            self,
            model: BaseChatOpenAI,
            config: RunnableConfig,
            check_pointer: Checkpointer,
    ):
        super(self.__class__, self).__init__(model, config, check_pointer, AGENT_NAME)

    def execute(self, agent_state: CodeAgentState, steps: List[Any]) -> CodeAgentState | None:
        """按计划执行任务"""
        print(f"\n--- begin to execute dynamic step plan: {[step.generate_type for step in steps]} ---")

        try:
            for step in steps:
                execute_result = step.generate(agent_state)
                agent_state = self.update_agent_state(agent_state, execute_result)

            print(f"\n ✅ execute dynamic step plan complete ")
        except Exception as e:
            print(f"\n ❌ execute dynamic step plan fail: {e}")
            return None

        return agent_state

    def update_agent_state(self, result_state: CodeAgentState, step_state: CodeAgentState) -> CodeAgentState:
        self.lock.acquire()
        try:
            result_state.code_result = step_state.code_result
            result_state.test_result = step_state.test_result
            result_state.doc_result = step_state.doc_result
            result_state.code_retries_time = step_state.code_retries_time
            result_state.test_retries_time = step_state.test_retries_time
            result_state.doc_retries_time = step_state.doc_retries_time

            result_state.current_step = f"{result_state.current_step}/{step_state.current_step}"
            result_state.input_token_statistics += step_state.input_token_statistics
            result_state.output_token_statistics += step_state.output_token_statistics
            result_state.total_token_statistics += step_state.total_token_statistics
        finally:
            self.lock.release()
            return result_state
