from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langchain_openai.chat_models.base import BaseChatOpenAI
from langchain_core.messages import HumanMessage, AIMessageChunk, RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.types import Checkpointer

from backend.config.config import get_agent_config
from backend.sub_agent.code_generate.agents.agent_state import CodeAgentState

class Generate:
    def __init__(
        self,
        model: BaseChatOpenAI,
        config: RunnableConfig,
        check_pointer: Checkpointer,
        agent_name: str
    ):
        self.model = model
        self.agent_name = agent_name
        self.config = config
        self.check_pointer = check_pointer
        self.agent_config = get_agent_config()

    def generate(self, agent_state: CodeAgentState) -> CodeAgentState:
        input_message = {
            "messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), HumanMessage(content=agent_state["request_message"])],
            "request_message": agent_state["request_message"],
            "code_retries_time": agent_state["code_retries_time"],
            "test_retries_time": agent_state["test_retries_time"],
            "doc_retries_time": agent_state["doc_retries_time"],
            "input_token_statistics": agent_state["input_token_statistics"],
            "output_token_statistics": agent_state["output_token_statistics"],
            "total_token_statistics": agent_state["total_token_statistics"],
            "current_step": self.get_current_step(),
            "resource_type": agent_state["resource_type"],
        }
        agent = self.create_generate_agent()

        try:
            stream = agent.stream(
                input=input_message,
                config=self.config,
                stream_mode=["messages", "updates"],
                version="v2",
            )
            print(f"\n--- begin to generate {agent_state["resource_type"]} {self.get_generate_type()} ---")
            for chunk in stream:
                if self.agent_config.print_thinking_process:
                    if chunk["type"] == "updates":
                        for node_name, update in chunk["data"].items():
                            # 模型请求调用工具
                            if node_name == "model" and update["messages"][-1].tool_calls:
                                print(f"\n[ready to call tool]: name={update['messages'][-1].tool_calls[0]['name']}, args={update['messages'][-1].tool_calls[0]['args']}")
                            # 工具执行结果
                            elif node_name == "tool" and update['messages'][-1].content:
                                print(f"\n[tool return]: result={update['messages'][-1].content}")
                    elif chunk["type"] == "messages" and chunk["data"] is not None and len(chunk["data"]) > 0:
                        if isinstance(chunk["data"][0], AIMessageChunk) and chunk["data"][0].content is not None:
                            print(chunk["data"][0].content, end="", flush=True)

            generate_result = f"generate_{self.get_generate_type()}_complete"
            print(f"\n--- ✅ generate {agent_state["resource_type"]} {self.get_generate_type()} complete ---")
        except Exception as e:
            generate_result = f"generate_{self.get_generate_type()}_error"
            print(f"\n--- ❌ generate {agent_state["resource_type"]} {self.get_generate_type()} fail: {e}---")

        state = agent.get_state(self.config).values
        state["current_step"] = generate_result
        print("=====================================================")
        print(f"{state}")
        return state

    def create_generate_agent(self):
        agent = create_agent(
            name=self.agent_name,
            model=self.model,
            checkpointer=self.check_pointer,
            system_prompt=self.build_system_prompt_template(),
            middleware=self.build_middlewares(),
            tools=self.build_tools(),
            state_schema=CodeAgentState
        )
        return agent

    def build_system_prompt_template(self) -> str:
        pass

    def build_middlewares(self) -> list[AgentMiddleware]:
        pass

    def build_tools(self) -> list[BaseTool]:
        pass

    def get_generate_type(self) -> str:
        pass

    def get_current_step(self) -> str:
        pass
