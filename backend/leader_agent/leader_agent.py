import logging
from typing import Any, Callable

from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import HumanMessage, AIMessageChunk, ToolMessage
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import InMemorySaver

from assistant.config.config import get_app_config
from assistant.lead_agent.agent_state import OncallAgentState
from assistant.lead_agent.prompt import apply_prompt_template
from assistant.memory.queue import get_memory_queue
from assistant.middleware.DynamicToolMiddleware import DynamicToolMiddleware
from assistant.middleware.cycle_check_middleware import CycleCheckMiddleware
from assistant.middleware.dynamic_system_porompt_middleware import build_system_prompt_template
from assistant.middleware.intent_regonize_middleware import IntentRecognizeMiddleware
from assistant.middleware.log_middleware import LoggingMiddleware
from assistant.middleware.memory_middleware import MemoryMiddleware
from assistant.middleware.summarization_middleware import ContextSummarizationMiddleware
from assistant.middleware.todo_Middleware import TodoMiddleware
from assistant.middleware.token_usage_middleware import TokenUsageMiddleware
from assistant.model.factory import get_model
from assistant.tool import oncall_schedule, get_latest_provider_version, reference_docs
from assistant.tool.file_tool import read_md
from assistant.utils.github_utils import clone_code, test_code_exists
from assistant.utils.schedule_utils import stop_scheduler_sync_git_code, start_scheduler_sync_git_code

logger = logging.getLogger(__name__)

AGENT_NAME = "terraform_oncall_assistant"

def init_local_code():
    exists = test_code_exists()
    if not exists:
        logger.info("begin to clone code from github")
        clone_code()
    else:
        logger.info("begin to pull latest code from github")
        # pull_code()

class LeaderAgent:
    def __init__(self, config: dict[str, Any]):
        agent_config = get_app_config()
        model = get_model(agent_config.model_type)
        self.model = model
        self.agent_config = agent_config
        self.config = config
        self.check_pointer = InMemorySaver()
        self.agent = self.create_assistant_agent()
        # init_local_code()
        # start_scheduler_sync_git_code()

    def __del__(self):
        stop_scheduler_sync_git_code()

    def init_agent_state(self, question:str) -> dict[str, Any]:
        initial_state = {
            "messages": [HumanMessage(content=question)],
            "input_token_statistics": 0,
            "output_token_statistics": 0,
            "total_token_statistics": 0,
            "model_cycle_time": 1,
        }
        return initial_state

    def deal_question(self):
        while True:
            user_input = input("\nUser: ")
            if user_input.lower() in ["q", "quit"]:
                # save thc cache queue to memory
                get_memory_queue().flush()
                break

            self.react(user_input)

    def react(self, question: str):
        input_message = self.init_agent_state(question)

        try:
            stream = self.agent.stream(
                input=input_message,
                config=self.config,
                stream_mode=["messages", "updates"],
                version="v2",
            )
            for chunk in stream:
                # print(chunk)
                if self.agent_config.print_thinking_process:
                    if chunk["type"] == "updates":
                        for node_name, update in chunk["data"].items():
                            # 打印中断消息
                            if node_name == "__interrupt__":
                                value = update[0].value
                                print(f"❓问题：{value['reason']}，\r\n原因：{value['course']}\r\n方案：{value['message']}")
                    elif chunk["type"] == "messages" and chunk["data"] is not None and len(chunk["data"]) > 0:
                        if isinstance(chunk["data"][0], AIMessageChunk) and chunk["data"][0].content is not None:
                            print(chunk["data"][0].content, end="", flush=True)
                        if isinstance(chunk["data"][0], ToolMessage) and chunk["data"][0].name == "ask_clarification" and chunk["data"][0].content is not None:
                            print(chunk["data"][0].content, end="", flush=True)

        except Exception as e:
            print(f"\n--- ❌ fail to deal question: {e}---")

        state = self.agent.get_state(self.config).values
        return state

    def create_assistant_agent(self):
        agent = create_agent(
            name=AGENT_NAME,
            model=self.model,
            checkpointer=self.check_pointer,
            # system_prompt=self.build_system_prompt_template(),
            middleware=self.build_middlewares(),
            tools=self.build_base_tools(),
            state_schema=OncallAgentState
        )
        return agent

    # def build_system_prompt_template(self) -> str:
    #     return apply_prompt_template(user_id=self.config["configurable"]["user_id"], agent_name=AGENT_NAME)

    def build_middlewares(self) -> list[AgentMiddleware]:
        middlewares: list[AgentMiddleware|str] = [
            LoggingMiddleware(agent_name=AGENT_NAME),
            IntentRecognizeMiddleware(agent_name=AGENT_NAME, config=self.config),
            DynamicToolMiddleware(agent_name=AGENT_NAME),
            build_system_prompt_template,
            TokenUsageMiddleware(agent_name=AGENT_NAME),
            CycleCheckMiddleware(agent_name=AGENT_NAME),
            MemoryMiddleware(agent_name=AGENT_NAME),
            ContextSummarizationMiddleware(
                model=self.model,
                agent_name=AGENT_NAME,
                trigger=[
                    ("messages", self.agent_config.summarization_trigger_messages),
                    ("tokens", self.agent_config.summarization_trigger_tokens)
                ],
                keep=("tokens", self.agent_config.summarization_trigger_tokens/3)
            ),
            TodoMiddleware(),
        ]
        return middlewares

    def build_base_tools(self) -> list[BaseTool | Callable[[Callable | Runnable], BaseTool]] | None:
        tools = [
            oncall_schedule,
            get_latest_provider_version,
            reference_docs,
            read_md,
        ]
        return tools
