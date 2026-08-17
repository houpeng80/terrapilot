import logging
import uuid
from typing import Any, Callable

from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import HumanMessage, AIMessageChunk, ToolMessage, AIMessage
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import InMemorySaver

from backend.config.config import get_agent_config
from backend.leader_agent.agent_state import TerrapilotAgentState, Intent
from backend.memory.queue import get_memory_queue
from backend.middleware.dynamic_tool_middleware import DynamicToolMiddleware
from backend.middleware.dynamic_system_porompt_middleware import build_system_prompt_template
from backend.middleware.intent_regonize_middleware import IntentRecognizeMiddleware
from backend.middleware.log_middleware import LoggingMiddleware
from backend.middleware.memory_middleware import MemoryMiddleware
from backend.middleware.summarization_middleware import ContextSummarizationMiddleware
from backend.middleware.token_usage_middleware import TokenUsageMiddleware
from backend.model import get_model
from backend.utils.github_utils import test_code_exists, clone_code, pull_code
from backend.utils.schedule_utils import stop_scheduler_sync_git_code, start_scheduler_sync_git_code
from backend.router.router import RouterManager, JUMP_TO_END
from backend.sub_agent.intent_recognize.intent_recognize import IntentRecognize
from backend.worker.worker_scheduler import WorkerScheduler
from backend.worker.workers import WorkerRequest

logger = logging.getLogger(__name__)

AGENT_NAME = "terraform-pilot"

def init_local_code():
    exists = test_code_exists()
    if not exists:
        logger.info("begin to clone code from github")
        clone_code()
    else:
        logger.info("begin to pull latest code from github")
        pull_code()

class LeaderAgent:
    def __init__(self, config: RunnableConfig):
        self.model = get_model(get_agent_config().model_type)
        self.agent_config = get_agent_config()
        self.config = config
        self.check_pointer = InMemorySaver()
        self.agent = self.create_terrapilot_agent()
        self.intent_recognize = IntentRecognize(config)
        self.router_manager = RouterManager(self.intent_recognize)
        self.worker_scheduler = WorkerScheduler()
        # init_local_code()
        # start_scheduler_sync_git_code()

    def __del__(self):
        # save thc cache queue to memory
        # get_memory_queue().flush()
        stop_scheduler_sync_git_code()

    def init_agent_state(self, question:str, histories: list[Intent]) -> TerrapilotAgentState:
        initial_state = {
            "messages": [HumanMessage(content=question)],
            "histories": histories,
            "input_token_statistics": 0,
            "output_token_statistics": 0,
            "total_token_statistics": 0,
            "model_cycle_time": 1,
        }
        return initial_state

    def invoke(self):
        while True:
            user_input = input("\nUser: ")
            if user_input.lower() in ["q", "quit"]:
                break

            self.run(user_input)

    def run(self, input_message: str):
        print("=================================")
        histories = []
        if "histories" in self.agent.get_state(self.config).values:
            histories = self.agent.get_state(self.config).values["histories"]
        leader_state = self.init_agent_state(input_message, histories)

        # 上下文压缩处理, 意图识别
        leader_state, intent_res = self.intent_recognize.intent_recognize(agent_state=leader_state)
        # 路由、判断、人工确认
        route, msg = self.router_manager.router(intent_res, histories)
        print("==================route: ",route)
        print("==================msg: ",msg)
        if route == JUMP_TO_END:
            result_input = msg
        else:
            # 子agent调度，保存结果到history
            worker_result = self.worker_scheduler.schedule(WorkerRequest(intent=intent_res.intent, params=intent_res.params, reasoning=intent_res.reasoning))
            if not worker_result.success:
                result_input = worker_result.error
            else:
                result_input = worker_result.result
                new_intent = {
                    "intent":intent_res.intent,
                    "confidence":intent_res.confidence,
                    "params":intent_res.params,
                    "missing_params":intent_res.missing_params,
                    "reasoning":intent_res.reasoning,
                    "result":result_input,
                }
                histories.insert(0, new_intent)
                self.agent.get_state(self.config).values["histories"] = histories

        # 主agent生成结果
        tool_call_id = [message.tool_calls[0]["id"] for message in leader_state["messages"] if isinstance(message, AIMessage) and len(message.tool_calls) > 0]
        tool_message = ToolMessage(
            id=uuid.uuid4().hex,
            content=result_input,
            tool_call_id=tool_call_id[0],
            name=f"deal_intent_{intent_res.intent}_tool_message",
        )
        leader_state = {
            "messages": [*leader_state["messages"], *[tool_message]],
            "input_token_statistics": leader_state["input_token_statistics"],
            "output_token_statistics": leader_state["output_token_statistics"],
            "total_token_statistics": leader_state["total_token_statistics"],
            "model_cycle_time": 1,
            "histories":histories,
        }
        try:
            stream = self.agent.stream(
                input=leader_state,
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

        # 保存intent到history

        state = self.agent.get_state(self.config)
        print("\nlast state: %s", state)
        print("\n=================================")
        # return state
        return state

    def create_terrapilot_agent(self):
        agent = create_agent(
            name=AGENT_NAME,
            model=self.model,
            checkpointer=self.check_pointer,
            # system_prompt=self.build_system_prompt_template(),
            middleware=self.build_middlewares(),
            tools=self.build_base_tools(),
            state_schema=TerrapilotAgentState
        )
        return agent

    # def build_system_prompt_template(self) -> str:
    #     return apply_prompt_template(user_id=self.config["configurable"]["user_id"], agent_name=AGENT_NAME)

    def build_middlewares(self) -> list[AgentMiddleware]:
        middlewares: list[AgentMiddleware|str] = [
            LoggingMiddleware(agent_name=AGENT_NAME),
            build_system_prompt_template,
            TokenUsageMiddleware(agent_name=AGENT_NAME),
            # CycleCheckMiddleware(agent_name=AGENT_NAME),
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
            # TodoMiddleware(),
        ]
        return middlewares

    def build_base_tools(self) -> list[BaseTool | Callable[[Callable | Runnable], BaseTool]] | None:
        tools = [
            # oncall_schedule,
            # get_latest_provider_version,
            # reference_docs,
            # read_md,
        ]
        return tools
