import threading
from typing import Any, List

from langchain_core.runnables import RunnableConfig
from langchain_openai.chat_models.base import BaseChatOpenAI
from langgraph.types import Checkpointer

from backend.sub_agent.code_generate.agents.agent_state import CodeAgentState
from backend.sub_agent.code_generate.plan_and_execute.executor import Executor

AGENT_NAME = "fixed_step_executor_agent"

class FixedStepExecutor(Executor):
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
        print(f"\n--- begin to execute fixed plan ---")

        try:
            for step in steps:
                execute_result = step.generate(agent_state)

            print(f"\n ✅ execute fixed step plan complete ")
        except Exception as e:
            print(f"\n ❌ execute fixed step plan fail: {e}")
            return execute_result

        return execute_result

    def update_agent_state(self, result_state: CodeAgentState, step_state: CodeAgentState) -> CodeAgentState:
        self.lock.acquire()
        try:
            if hasattr(step_state, "code_result"):
                result_state["code_result"] = step_state["code_result"]
            if hasattr(step_state, "test_result"):
                result_state["test_result"] = step_state["test_result"]
            if hasattr(step_state, "doc_result"):
                result_state["doc_result"] = step_state["doc_result"]

            if hasattr(result_state, "current_step"):
                result_state["current_step"] = f"{result_state["current_step"]}/{step_state["current_step"]}"
            else:
                result_state["current_step"] = step_state["current_step"]

            result_state["code_retries_time"] = step_state["code_retries_time"]
            result_state["test_retries_time"] = step_state["test_retries_time"]
            result_state["doc_retries_time"] = step_state["doc_retries_time"]
            result_state["input_token_statistics"] += step_state["input_token_statistics"]
            result_state["output_token_statistics"] += step_state["output_token_statistics"]
            result_state["total_token_statistics"] += step_state["total_token_statistics"]

        finally:
            self.lock.release()

        return result_state
