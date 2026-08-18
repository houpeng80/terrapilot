import uuid
from pathlib import Path
from typing import Any, List

from langchain_core.messages import RemoveMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.types import StateT, OutputT
from langgraph.typing import ContextT, InputT

from backend.config.config import get_agent_config
from backend.model import get_model
from backend.sub_agent.code_generate.agents.agent_state import CodeAgentState
from backend.sub_agent.code_generate.agents.generate import Generate
from backend.sub_agent.code_generate.plan_and_execute.dynamic_steps.dynamic_step_executor import DynamicStepExecutor
from backend.sub_agent.code_generate.plan_and_execute.dynamic_steps.dynamic_step_planner import DynamicStepPlanner
from backend.sub_agent.code_generate.plan_and_execute.dynamic_steps.response import DynamicStepPlannerResponse
from backend.sub_agent.code_generate.plan_and_execute.fixed_step.fixed_step_executor import FixedStepExecutor
from backend.sub_agent.code_generate.plan_and_execute.fixed_step.fixed_step_planner import FixedStepPlanner
from backend.sub_agent.code_generate.plan_and_execute.fixed_step.response import FixedStepPlannerResponse
from backend.sub_agent.code_generate.plan_and_execute.graph.graph_executor import GraphExecutor
from backend.sub_agent.code_generate.plan_and_execute.graph.graph_planner import GraphPlanner
from backend.sub_agent.code_generate.plan_and_execute.graph.response import GraphPlannerResponse
from backend.worker.workers import Worker, WorkerRequest

AGENT_NAME = "code_generate_agent"

class CodeGenerateAgent(Worker):
    name = AGENT_NAME
    def __init__(self):
        super().__init__(AGENT_NAME)
        agent_config = get_agent_config()
        model = get_model(agent_config.model_type, code_generate=True)
        self.model = model
        self.agent_config = agent_config
        self.config = {"configurable": {"thread_id": uuid.uuid4().hex}}
        self.check_pointer = InMemorySaver()
        print(model)

        if self.agent_config.execute_type == "graph":
            self.planner = GraphPlanner(model, self.config, self.check_pointer, agent_config)
            self.executor = GraphExecutor(model, self.config, self.check_pointer)
        elif self.agent_config.execute_type == "fixed_step":
            self.planner = FixedStepPlanner(model, self.config, self.check_pointer, agent_config)
            self.executor = FixedStepExecutor(model, self.config, self.check_pointer)
        elif self.agent_config.execute_type == "dynamic_step":
            self.planner = DynamicStepPlanner(model, self.config, self.check_pointer, agent_config)
            self.executor = DynamicStepExecutor(model, self.config, self.check_pointer)
        else:
            raise ValueError(f"\n--- 任务终止： 执行任务的类型{self.agent_config.execute_type}不正确，请修改后重试 --- ")

    def init_agent_state(self, intent:str, request_message:str) -> CodeAgentState:
        initial_state = {
            "messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), HumanMessage(content=request_message)],
            "request_message": request_message,
            "code_retries_time": 0,
            "test_retries_time": 0,
            "doc_retries_time": 0,
            "input_token_statistics": 0,
            "output_token_statistics": 0,
            "total_token_statistics": 0,
            "current_intent": intent,
        }
        return initial_state

    def execute(self, intent: WorkerRequest) -> str:
        print(f"\n--- begin to generate code: {intent.params["input"]} ---")

        agent_state = self.init_agent_state(intent.intent, self.build_request_message(intent))
        plan_response = self.planner.plan(agent_state)
        if not plan_response:
            print(f"\n--- ❌ task end, can not generate an effective action plan ---")
            return f"\n--- ❌ task end, can not generate an effective action plan ---"

        if isinstance(plan_response, GraphPlannerResponse):
            agent_state = self.execute_with_graph(agent_state, plan_response.resource_type, plan_response.graph)
        elif isinstance(plan_response, FixedStepPlannerResponse):
            agent_state = self.execute_with_steps(agent_state, plan_response.resource_type, plan_response.steps)
        elif isinstance(plan_response, DynamicStepPlannerResponse):
            agent_state = self.execute_with_steps(agent_state, plan_response.resource_type, plan_response.steps)

        print(f"\n --- token usage statistics: "
              f"input_statistics={agent_state["input_token_statistics"]}, "
              f"output_statistics={agent_state["output_token_statistics"]}, "
              f"total_statistics={agent_state["total_token_statistics"]}",
        )
        print("\n--- ✅ task complete ---")

        return f"生成结果已经放到{Path(__file__).resolve().parents[4]}"

    def build_request_message(self, intent: WorkerRequest) -> str:
        if intent.intent == "generate_code":
            request_message = intent.params["input"]
        else:
            request_message = ""

        return request_message

    def execute_with_graph(self, agent_state: CodeAgentState, resource_type:str, graph: StateGraph[StateT, ContextT, InputT, OutputT]) -> CodeAgentState:
        agent_state["resource_type"] = resource_type
        return self.executor.execute(agent_state, graph)

    def execute_with_steps(self, agent_state: CodeAgentState, resource_type:str, steps: List[Generate]) -> CodeAgentState:
        agent_state["resource_type"] = resource_type
        return self.executor.execute(agent_state, steps)

if __name__ == "__main__":
    request_message = "根据https://support.huaweicloud.com/api-gaussdb/gaussdb_api_107.html，帮我生成一个data source"
    app = CodeGenerateAgent()
    app.execute(WorkerRequest(intent="generate_code", params={"input":request_message, "resource_type": "data_source"}, reasoning="生成一个data_source"))