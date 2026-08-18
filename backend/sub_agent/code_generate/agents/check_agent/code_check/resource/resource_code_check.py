import logging

from pydantic import BaseModel, Field

from langchain.agents.middleware import AgentMiddleware
from langchain_core.runnables import RunnableConfig
from langchain_openai.chat_models.base import BaseChatOpenAI
from langgraph.types import Checkpointer

from backend.middleware.log_middleware import LoggingMiddleware
from backend.middleware.token_usage_middleware import TokenUsageMiddleware
from backend.sub_agent.code_generate.agents.check_agent.code_check.code_check import CodeCheck
from backend.sub_agent.code_generate.agents.check_agent.code_check.resource.prompt import apply_prompt_template
from backend.sub_agent.code_generate.middleware.tool_cache_middleware import ToolCacheMiddleware

logger = logging.getLogger(__name__)

AGENT_NAME = "resource_code_check_agent"

class ResourceCodeCheckInfo(BaseModel):
    contain_description: bool = Field(description="Whether the code contain description, return yes or no")
    contain_force_new: bool = Field(description="Whether the code contain ForceNew, return yes or no")
    non_updatable_params_contain_updated_param: list[str] = Field(description="The params that the non updatable params list contain, but it is support updated, return the params")
    non_updatable_params_not_contain_non_updatable_param: list[str] = Field(description="The params that the non updatable params not contain, but it is not support updated, return the params")
    validation_error: bool = Field(description="Whether the code contain ValidationFunc except the params which type is bool, return yes or no")
    bool_type_params_error: list[str] = Field(description="The params that the type is bool in API, but the type in code is not str or do not contain ValidationFunc, ignore response params return the params")
    region_param_error: bool = Field(description="If the service is global, region should not be contained, and if the service is not global, region should be contained, return yes or no")
    contain_api_comment: bool = Field(description="Whether the code API comment contain the whole API URI, return yes or no")
    contain_import : bool = Field(description="If the code read func is not empty, then import func should be contained, return yes or no")
    contain_timeout : bool = Field(description="If the code contain wait func, then timeout should be contained, return yes or no")

class ResourceCodeCheck(CodeCheck):
    """check the code whether is correct or not."""

    def __init__(self, model: BaseChatOpenAI, config: RunnableConfig, check_pointer: Checkpointer):
        super(self.__class__, self).__init__(model, config, check_pointer, ResourceCodeCheckInfo, AGENT_NAME)

    def build_system_prompt_template(self) -> str:
        return apply_prompt_template(self.agent_name)

    def build_middlewares(self) -> list[AgentMiddleware]:
        middlewares: list[AgentMiddleware] = [
            LoggingMiddleware(agent_name=AGENT_NAME),
            TokenUsageMiddleware(agent_name=AGENT_NAME),
            ToolCacheMiddleware(agent_name=AGENT_NAME),
        ]
        return middlewares
