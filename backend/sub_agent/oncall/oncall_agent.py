import logging
import uuid
from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import HumanMessage, AIMessageChunk, ToolMessage, RemoveMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import REMOVE_ALL_MESSAGES

from backend.config.config import get_agent_config
from backend.middleware.cycle_check_middleware import CycleCheckMiddleware
from backend.middleware.summarization_middleware import ContextSummarizationMiddleware
from backend.model import get_model
from backend.middleware.log_middleware import LoggingMiddleware
from backend.middleware.token_usage_middleware import TokenUsageMiddleware
from backend.sub_agent.intent_recognize.agent_state import OncallAgentState
from backend.sub_agent.oncall.middleware.dynamic_tool_middleware import DynamicToolMiddleware
from backend.sub_agent.oncall.prompt import apply_prompt_template
from backend.tool.tool_registry import ToolRegistry
from backend.worker.workers import Worker, WorkerRequest

logger = logging.getLogger(__name__)

AGENT_NAME = "oncall_agent"

class OncallAgent(Worker):
    name:str = AGENT_NAME

    def __init__(self):
        super().__init__(AGENT_NAME)
        agent_config = get_agent_config()
        model = get_model(agent_config.model_type)
        self.model = model
        self.agent_config = agent_config
        self.config = {"configurable": {"thread_id": uuid.uuid4().hex}}
        self.check_pointer = InMemorySaver()
        self.tool_registry = ToolRegistry()
        self.agent = self.create_oncall_agent()

    def init_agent_state(self, intent:str, request_message:str) -> dict[str, Any]:
        initial_state = {
            "messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), HumanMessage(content=request_message)],
            "input_token_statistics": 0,
            "output_token_statistics": 0,
            "total_token_statistics": 0,
            "model_cycle_time": 1,
            "current_intent": intent,
        }
        return initial_state

    def execute(self, intent: WorkerRequest) -> str:
        agent_state = self.init_agent_state(intent.intent, self.build_request_message(intent))

        try:
            stream = self.agent.stream(
                input=agent_state,
                config=self.config,
                stream_mode=["messages", "updates"],
                version="v2",
            )
            for chunk in stream:
                pass
                # if self.agent_config.print_thinking_process:
                #     if chunk["type"] == "updates":
                #         for node_name, update in chunk["data"].items():
                #             pass
                #     elif chunk["type"] == "messages" and chunk["data"] is not None and len(chunk["data"]) > 0:
                #         if isinstance(chunk["data"][0], AIMessageChunk) and chunk["data"][0].content is not None:
                #             print(chunk["data"][0].content, end="", flush=True)

        except Exception as e:
            print(f"\n--- ❌ fail to deal question: {e}---")
            raise e

        state = self.agent.get_state(self.config)
        return state.values["messages"][-1].content

    def build_request_message(self, intent: WorkerRequest) -> str:
        if intent.intent == "query_oncall":
            request_message = f"获取当前oncall排班信息"
        elif intent.intent == "query_latest_version":
            request_message = f"获取huaweicloud terraform provider最新版本"
        elif intent.intent == "query_reference_docs":
            request_message = f"获取huaweicloud terraform提供者参考文档"
        elif intent.intent == "whether_support_special_region":
            request_message = intent.reasoning
        elif intent.intent == "query_resource_by_name":
            request_message = f"{intent.params["service_type"]}服务的{intent.params["resource_name"]}这个{intent.params["resource_type"]}支持吗"
        elif intent.intent == "query_resource_by_api":
            request_message = f"{intent.params["service_type"]}服务的{intent.params["api_method"]} {intent.params["api_url"]}这个API支持吗"
        elif intent.intent == "query_resource_by_content":
            request_message = f"{intent.params["service_type"]}服务支持{intent.params["context"]} 吗"
        else:
            request_message = ""

        return request_message


    def create_oncall_agent(self):
        agent = create_agent(
            name=AGENT_NAME,
            model=self.model,
            checkpointer=self.check_pointer,
            system_prompt=self.build_system_prompt_template(),
            middleware=self.build_middlewares(),
            state_schema=OncallAgentState
        )
        return agent

    def build_system_prompt_template(self) -> str:
        return apply_prompt_template(agent_name=AGENT_NAME)

    def build_middlewares(self) -> list[AgentMiddleware]:
        middlewares: list[AgentMiddleware|str] = [
            LoggingMiddleware(agent_name=AGENT_NAME),
            DynamicToolMiddleware(agent_name=AGENT_NAME,tool_registry=self.tool_registry),
            TokenUsageMiddleware(agent_name=AGENT_NAME),
            CycleCheckMiddleware(agent_name=AGENT_NAME),
            ContextSummarizationMiddleware(
                model=self.model,
                agent_name=AGENT_NAME,
                trigger=[
                    ("messages", self.agent_config.summarization_trigger_messages),
                    ("tokens", self.agent_config.summarization_trigger_tokens)
                ],
                keep=("tokens", self.agent_config.summarization_trigger_tokens/3)
            ),
        ]
        return middlewares
