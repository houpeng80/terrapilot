import logging

from langchain_core.messages import AIMessageChunk
from pydantic import BaseModel

from langgraph.types import Checkpointer
from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware
from langchain_core.runnables import RunnableConfig
from langchain.messages import HumanMessage
from langchain_openai.chat_models.base import BaseChatOpenAI

from backend.config.config import get_agent_config
from backend.sub_agent.code_generate.agents.agent_state import CodeAgentState
from backend.sub_agent.code_generate.tool.web_search_and_extract import web_search_and_extract

logger = logging.getLogger(__name__)

class CodeCheck:
    """check the code whether is correct or not."""

    def __init__(
            self,
            model: BaseChatOpenAI,
            config: RunnableConfig,
            check_pointer: Checkpointer,
            response_format: BaseModel,
            agent_name: str
    ):
        self.model = model
        self.agent_name = agent_name
        self.config = config
        self.check_pointer = check_pointer
        self.response_format = response_format
        self.agent_config = get_agent_config()

    def code_check(self, agent_state: CodeAgentState) -> BaseModel:
        request_message = agent_state['messages'][0]

        user_message = HumanMessage(
            content=f"{request_message.content}\n\n{agent_state["code_result"]}",
        )
        input_message = {
            "messages": user_message,
            "request_message": agent_state["request_message"],
            "code_retries_time": agent_state["code_retries_time"],
            "test_retries_time": agent_state["test_retries_time"],
            "doc_retries_time": agent_state["doc_retries_time"],
            "input_token_statistics": agent_state["input_token_statistics"],
            "output_token_statistics": agent_state["output_token_statistics"],
            "total_token_statistics": agent_state["total_token_statistics"],
            "current_step": agent_state["current_step"],
            "resource_type": agent_state["resource_type"],
        }

        agent = self.create_code_check_agent()

        try:
            stream = agent.stream(
                input=input_message,
                config=self.config,
                stream_mode=["messages", "updates"],
                version="v2",
            )
            print(f"\n--- begin to check {agent_state["resource_type"]} code ---")
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

            print(f"\n--- ✅ {agent_state["resource_type"]} code check complete ---")
        except Exception as e:
            print(f"\n--- ❌ {agent_state["resource_type"]} code check fail ---")

        return res

    def create_code_check_agent(self):
        agent = create_agent(
            name=self.agent_name,
            model=self.model,
            checkpointer=self.check_pointer,
            system_prompt=self.build_system_prompt_template(),
            tools=[web_search_and_extract],
            middleware=self.build_middlewares(),
            response_format=self.response_format,
        )
        return agent

    def build_system_prompt_template(self) -> str:
        pass

    def build_middlewares(self) -> list[AgentMiddleware]:
        pass