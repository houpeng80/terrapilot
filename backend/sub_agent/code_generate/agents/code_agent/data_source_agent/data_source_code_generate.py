import uuid
from pathlib import Path

from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langchain_openai.chat_models.base import BaseChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Checkpointer

from backend.config.config import get_agent_config
from backend.middleware.log_middleware import LoggingMiddleware
from backend.middleware.token_usage_middleware import TokenUsageMiddleware
from backend.model import get_model
from backend.sub_agent.code_generate.agents.code_agent.data_source_agent.prompt import apply_prompt_template
from backend.sub_agent.code_generate.agents.generate import Generate
from backend.sub_agent.code_generate.middleware.code_check_middleware import CodeCheckMiddleware
from backend.sub_agent.code_generate.middleware.retry_check_middleware import RetryCheckMiddleware
from backend.sub_agent.code_generate.middleware.summarization_middleware import ContextSummarizationMiddleware
from backend.sub_agent.code_generate.middleware.todo_Middleware import TodoMiddleware
from backend.sub_agent.code_generate.middleware.tool_cache_middleware import ToolCacheMiddleware
from backend.sub_agent.code_generate.tool.deal_file import write_file
from backend.sub_agent.code_generate.tool.skill_load import skill_load
from backend.sub_agent.code_generate.tool.web_search_and_extract import web_search_and_extract

AGENT_NAME = "data_source_code_generator"

class DataSourceCodeGenerate(Generate):
    def __init__(
        self,
        model: BaseChatOpenAI,
        config: RunnableConfig,
        check_pointer: Checkpointer
    ):
        super(self.__class__, self).__init__(model, config, check_pointer, AGENT_NAME)
        self.generate_type="code"
        self.current_step="generating_code"

    def build_system_prompt_template(self) -> str:
        # 项目根目录，用于放生成的文件
        repo_root = Path(__file__).resolve().parents[6]
        return apply_prompt_template(AGENT_NAME, repo_root.resolve())

    def build_middlewares(self) -> list[AgentMiddleware]:
        middlewares: list[AgentMiddleware] = [
            RetryCheckMiddleware(agent_name=AGENT_NAME, agent_config=self.agent_config),
            LoggingMiddleware(agent_name=AGENT_NAME),
            TokenUsageMiddleware(agent_name=AGENT_NAME),
            ToolCacheMiddleware(agent_name=AGENT_NAME),
            ContextSummarizationMiddleware(
                model=self.model,
                agent_name=AGENT_NAME,
                trigger=[
                    ("messages", self.agent_config.code_generate_summarization_trigger_messages),
                    ("tokens", self.agent_config.code_generate_summarization_trigger_tokens),
                ],
                keep=("tokens", self.agent_config.summarization_trigger_tokens / 3)
            ),
            TodoMiddleware(agent_name=AGENT_NAME),
            CodeCheckMiddleware(
                model=self.model,
                agent_name=AGENT_NAME,
                agent_config=self.agent_config,
                checkpointer =self.check_pointer,
                config=self.config,
            ),
        ]
        return middlewares

    def build_tools(self) -> list[BaseTool]:
        return [web_search_and_extract, skill_load, write_file]

    def get_generate_type(self) -> str:
        return self.generate_type

    def get_current_step(self) -> str:
        return self.current_step

if __name__ == "__main__":
    request_message = "根据https://support.huaweicloud.com/api-gaussdb/gaussdb_api_107.html，帮我生成一个data source"
    initial_state = {
        "messages": [ HumanMessage(content=request_message)],
        "request_message": request_message,
        "code_retries_time": 0,
        "test_retries_time": 0,
        "doc_retries_time": 0,
        "input_token_statistics": 0,
        "output_token_statistics": 0,
        "total_token_statistics": 0,
        "resource_type":"data_source"
    }
    config = {"configurable": {"thread_id": uuid.uuid4().hex}}
    model = get_model(get_agent_config().model_type)
    model.max_tokens=9012
    app = DataSourceCodeGenerate(model=model, config=config, check_pointer=InMemorySaver())
    app.generate(initial_state)
