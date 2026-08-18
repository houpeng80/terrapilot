import logging

from langchain.agents.middleware import AgentMiddleware
from langchain_core.runnables import RunnableConfig
from langchain_openai.chat_models.base import BaseChatOpenAI
from langgraph.types import Checkpointer
from pydantic import BaseModel, Field

from backend.middleware.log_middleware import LoggingMiddleware
from backend.middleware.token_usage_middleware import TokenUsageMiddleware
from backend.sub_agent.code_generate.agents.check_agent.code_check.code_check import CodeCheck
from backend.sub_agent.code_generate.agents.check_agent.code_check.data_source.prompt import apply_prompt_template
from backend.sub_agent.code_generate.middleware.tool_cache_middleware import ToolCacheMiddleware

logger = logging.getLogger(__name__)

AGENT_NAME = "data_source_code_check_agent"

class DataSourceCodeCheckInfo(BaseModel):
    contain_description: bool = Field(description="Whether the code contain description, return yes or no")
    contain_force_new: bool = Field(description="Whether the code contain ForceNew, return yes or no")
    added_params: list[str] = Field(description="The params that the code contain, but the API query params and request params contain do not contain, return the params")
    deleted_params: list[str] = Field(description="The params that the code do not contain, but the API query params or request params contain, you must ignore the page params, return the params")
    validation_error: bool = Field(description="Whether the code contain ValidationFunc except the params which type is bool, return yes or no")
    bool_type_params_error: list[str] = Field(description="The params that the type is bool in API, but the type in code is not str or do not contain ValidationFunc, ignore response params return the params")
    region_param_error: bool = Field(description="If the service is global, region should not be contained, and if the service is not global, region should be contained, return yes or no")
    contain_api_comment: bool = Field(description="Whether the code API comment contain the API URI, return yes or no")
    page_right : bool = Field(description="If the API support page then the code should support, and if the API do not support page then the code should not support, return yes or no")

class DataSourceCodeCheck(CodeCheck):
    """check the code whether is correct or not."""

    def __init__(self, model: BaseChatOpenAI, config: RunnableConfig, check_pointer: Checkpointer):
        super(self.__class__, self).__init__(model, config, check_pointer, DataSourceCodeCheckInfo, AGENT_NAME)

    def build_system_prompt_template(self) -> str:
        return apply_prompt_template(self.agent_name)

    def build_middlewares(self) -> list[AgentMiddleware]:
        middlewares: list[AgentMiddleware] = [
            LoggingMiddleware(agent_name=AGENT_NAME),
            TokenUsageMiddleware(agent_name=AGENT_NAME),
            ToolCacheMiddleware(agent_name=AGENT_NAME),
        ]
        return middlewares
