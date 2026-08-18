import logging

from langchain.agents.middleware import AgentMiddleware
from langchain_core.runnables import RunnableConfig
from langchain_openai.chat_models.base import BaseChatOpenAI
from langchain_core.messages import HumanMessage, AIMessageChunk
from langgraph.types import Checkpointer

from backend.config.config import AgentConfig
from backend.middleware.log_middleware import LoggingMiddleware
from backend.middleware.summarization_middleware import ContextSummarizationMiddleware
from backend.middleware.token_usage_middleware import TokenUsageMiddleware
from backend.sub_agent.code_generate.agents.agent_state import CodeAgentState
from backend.sub_agent.code_generate.agents.code_agent.data_source_agent.data_source_code_generate import \
    DataSourceCodeGenerate
from backend.sub_agent.code_generate.agents.code_agent.resource_agent.resource_generate_code import ResourceCodeGenerate
from backend.sub_agent.code_generate.agents.docs_agents.data_source_agent.data_source_doc_generate import \
    DataSourceDocGenerate
from backend.sub_agent.code_generate.agents.docs_agents.resource_agent.resource_doc_generate import ResourceDocGenerate
from backend.sub_agent.code_generate.agents.test_agent.data_source_agent.data_source_test_generate import \
    DataSourceTestGenerate
from backend.sub_agent.code_generate.agents.test_agent.resource_agent.resource_test_generate import ResourceTestGenerate
from backend.sub_agent.code_generate.plan_and_execute.fixed_step.prompt import PLANNER_PROMPT_TEMPLATE
from backend.sub_agent.code_generate.plan_and_execute.fixed_step.response import FixedStepPlannerResponse
from backend.sub_agent.code_generate.plan_and_execute.planner import Planner
from backend.sub_agent.code_generate.plan_and_execute.response import PlannerResponse

logger = logging.getLogger(__name__)

AGENT_NAME = "fixed_step_planner_agent"

class FixedStepPlanner(Planner):
    """规划器 - 负责将复杂问题分解为简单步骤"""

    def __init__(
            self,
            model: BaseChatOpenAI,
            config: RunnableConfig,
            check_pointer: Checkpointer,
            agent_config: AgentConfig,
    ):
        super(self.__class__, self).__init__(model, config, check_pointer, agent_config, AGENT_NAME)

    def plan(self, agent_state: CodeAgentState) -> FixedStepPlannerResponse | None:
        """
        生成执行计划
        """
        print(f"\n--- begin to generate fixed step plan ---")

        try:
            input_message = {
                "messages": [HumanMessage(content=agent_state["request_message"])],
                "input_token_statistics": agent_state["input_token_statistics"],
                "output_token_statistics": agent_state["output_token_statistics"],
                "total_token_statistics": agent_state["total_token_statistics"],
                "current_step": "generating_plan",
            }
            agent = super().create_planner_agent(PlannerResponse)

            stream = agent.stream(
                input=input_message,
                config=self.config,
                stream_mode=["messages", "updates"],
                version="v2",
            )
            res = ""
            for chunk in stream:
                if self.agent_config.print_thinking_process:
                    if chunk["type"] == "updates":
                        for node_name, update in chunk["data"].items():
                            # 模型请求调用工具
                            if node_name == "model":
                                if "structured_response" in update:
                                    res = update["structured_response"]
                                elif update["messages"][-1].tool_calls:
                                    print(
                                        f"\n[ready to call tool]: name={update['messages'][-1].tool_calls[0]['name']}, args={update['messages'][-1].tool_calls[0]['args']}")
                            # 工具执行结果
                            elif node_name == "tool":
                                print(f"\n[tool return]: result={update['messages'][-1].content}")
                    elif chunk["type"] == "messages" and chunk["data"] is not None and len(chunk["data"]) > 0:
                        if isinstance(chunk["data"][0], AIMessageChunk) and chunk["data"][0].content is not None:
                            print(chunk["data"][0].content, end="", flush=True)

            resource_type = res.resource_type

            if not self.agent_config.generate_code and not self.agent_config.generate_test and not self.agent_config.generate_doc:
                print("\n ❌ 没有要生成的内容，请前往config.yaml中配置要生成的 code/test/doc")
                return None

            steps = []
            if resource_type == "data_source":
                if self.agent_config.generate_code:
                    steps.append(DataSourceCodeGenerate(self.model, self.config, self.check_pointer))
                if self.agent_config.generate_test:
                    steps.append(DataSourceTestGenerate(self.model, self.config, self.check_pointer))
                if self.agent_config.generate_doc:
                    steps.append(DataSourceDocGenerate(self.model, self.config, self.check_pointer))
            elif resource_type == "resource":
                if self.agent_config.generate_code:
                    steps.append(ResourceCodeGenerate(self.model, self.config, self.check_pointer))
                if self.agent_config.generate_test:
                    steps.append(ResourceTestGenerate(self.model, self.config, self.check_pointer))
                if self.agent_config.generate_doc:
                    steps.append(ResourceDocGenerate(self.model, self.config, self.check_pointer))
            else:
                print(f"\n ❌ resource type {resource_type} is not supported:")
                raise ValueError(f"not supported resource type：{resource_type}")

            print(f"\n ✅ generate fixed step plan complete ")

            return FixedStepPlannerResponse(resource_type=resource_type, steps=steps)

        except Exception as e:
            print(f"\n ❌ generate fixed step plan fail: {e}")
            return None

    def build_system_prompt_template(self) -> str:
        return PLANNER_PROMPT_TEMPLATE.format(agent_name = AGENT_NAME)

    def build_middlewares(self) -> list[AgentMiddleware]:
        middlewares: list[AgentMiddleware] = [
            LoggingMiddleware(agent_name=AGENT_NAME),
            TokenUsageMiddleware(agent_name=AGENT_NAME),
            ContextSummarizationMiddleware(model=self.model, agent_name=AGENT_NAME),
        ]
        return middlewares
