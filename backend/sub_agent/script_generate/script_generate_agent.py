import uuid
from typing import Any, Callable

from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage, AIMessageChunk, RemoveMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import REMOVE_ALL_MESSAGES

from backend.config.config import get_agent_config
from backend.middleware.cycle_check_middleware import CycleCheckMiddleware
from backend.middleware.log_middleware import LoggingMiddleware
from backend.middleware.summarization_middleware import ContextSummarizationMiddleware
from backend.middleware.todo_Middleware import TodoMiddleware
from backend.middleware.token_usage_middleware import TokenUsageMiddleware
from backend.model import get_model
from backend.sub_agent.script_generate.agent_state import ScriptAgentState
from backend.sub_agent.script_generate.prompt import apply_prompt_template
from backend.tool.builtins.file_tool import read_md
from backend.worker.workers import Worker, WorkerRequest

AGENT_NAME = "script_generate_agent"

class ScriptGenerateAgent(Worker):
    name: str = AGENT_NAME

    def __init__(self):
        super().__init__(AGENT_NAME)
        agent_config = get_agent_config()
        self.model = get_model(agent_config.model_type,True)
        self.config = {"configurable": {"thread_id": uuid.uuid4().hex}}
        self.check_pointer = InMemorySaver()
        self.agent_config = agent_config

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
        agent = self.create_generate_agent()

        try:
            stream = agent.stream(
                input=agent_state,
                config=self.config,
                stream_mode=["messages", "updates"],
                version="v2",
            )
            print(f"\n--- 开始生成脚本 ---")
            for chunk in stream:
                pass
                # if self.agent_config.print_thinking_process:
                #     if chunk["type"] == "messages" and chunk["data"] is not None and len(chunk["data"]) > 0:
                #         if isinstance(chunk["data"][0], AIMessageChunk) and chunk["data"][0].content is not None:
                #             print(chunk["data"][0].content, end="", flush=True)

        except Exception as e:
            raise e

        state = agent.get_state(self.config)
        # print("generate script", state)
        print(f"\n--- 生成脚本完成 ---")

        return f"生成的脚本信息：\r\n{state.values["messages"][-1].content}"

    def build_request_message(self, intent: WorkerRequest) -> str:
        if intent.intent == "generate_script":
            request_message = f"生成 {intent.params["resource_name"]} 这个{intent.params["resource_type"]}的terraform脚本"
            if intent.params["contain_reference"] == "true":
                request_message = request_message + "，生成依赖的资源信息"
            else:
                request_message = request_message + "，只生成当前的资源信息"
        else:
            request_message = ""

        return request_message

    def create_generate_agent(self):
        agent = create_agent(
            name=AGENT_NAME,
            model=self.model,
            checkpointer=self.check_pointer,
            system_prompt=self.build_system_prompt_template(),
            middleware=self.build_middlewares(),
            tools=self.build_tools(),
            state_schema=ScriptAgentState
        )
        return agent

    @staticmethod
    def build_system_prompt_template() -> str:
        return apply_prompt_template(agent_name=AGENT_NAME)

    def build_middlewares(self) -> list[AgentMiddleware]:
        middlewares: list[AgentMiddleware] = [
            LoggingMiddleware(agent_name=AGENT_NAME),
            TokenUsageMiddleware(agent_name=AGENT_NAME),
            CycleCheckMiddleware(agent_name=AGENT_NAME),
            ContextSummarizationMiddleware(
                model=self.model,
                agent_name=AGENT_NAME,
                trigger=[
                    ("messages", self.agent_config.code_generate_summarization_trigger_messages),
                    ("tokens", self.agent_config.code_generate_max_tokens)
                ],
                keep=("tokens", self.agent_config.code_generate_summarization_trigger_messages / 3)
            ),
            # TodoMiddleware(),
        ]
        return middlewares

    def build_tools(self) -> list[BaseTool | Callable[[Callable | Runnable], BaseTool]] | None:
        return [read_md]
