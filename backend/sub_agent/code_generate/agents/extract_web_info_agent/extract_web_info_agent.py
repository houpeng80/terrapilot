import logging

from typing import Any
from pydantic import BaseModel, Field

from langchain.agents import create_agent
from langchain.messages import HumanMessage

from backend.config.config import get_agent_config
from backend.middleware.log_middleware import LoggingMiddleware
from backend.middleware.token_usage_middleware import TokenUsageMiddleware
from backend.model import get_model
from backend.sub_agent.code_generate.agents.extract_web_info_agent.prompt import apply_prompt_template
from backend.sub_agent.code_generate.tool.web_search import web_search

logger = logging.getLogger(__name__)

AGENT_NAME = "web_search_and_extract_agent"

class WebSearchAndExtractInfo(BaseModel):
    is_global: bool = Field(description="Whether the service is global service.")
    service_name: str = Field(description="The service name")
    uri: str = Field(description="The URI address of the API")
    uri_params: Any = Field(description="The URI params of the API")
    query_params: Any = Field(description="The query params of the API")
    request_params: Any = Field(description="The request params of the API")
    response_params: Any = Field(description="The response params of the API")
    page_info: Any = Field(description="The page info of the API")


class ApiInfo(BaseModel):
    api_info: WebSearchAndExtractInfo = Field(default_factory=WebSearchAndExtractInfo, description="The API info extracted from the API")

class WebSearchAndExtract:
    """get web info and extra information."""

    def __init__(self):
        self.agent_name = AGENT_NAME

    def build_system_prompt_template(self) -> str:
        return apply_prompt_template(self.agent_name)

    def web_search_and_extract(self, request: str) -> Any:
        """
        从web中获取网页信息，并从中提取关键信息
        Args:
            request: 用户的需求

        Returns:
            提取到的API信息
        """
        logger.info("agent {%s} begin to get API info", AGENT_NAME)

        agent_config = get_agent_config()
        model = get_model(agent_config.model_type, True)
        user_message = HumanMessage(
            content=request
        )
        agent = create_agent(
            name=self.agent_name,
            model=model,
            system_prompt=self.build_system_prompt_template(),
            tools=[web_search],
            middleware=[
                LoggingMiddleware(agent_name=AGENT_NAME),
                TokenUsageMiddleware(agent_name=self.agent_name)
            ],
            response_format=ApiInfo,
        )

        try:
            result = agent.invoke(
                {"messages": [user_message]},
            )

            logger.info("agent {%s} get the API info complete", AGENT_NAME)

            return result["structured_response"].api_info
        except Exception as e:
            print(f"\n ❌ agent {AGENT_NAME} get the API info fail: {e}")
            return None

if __name__ == "__main__":
    url = "https://support.huaweicloud.com/api-gaussdb/gaussdb_api_107.html"
    result = WebSearchAndExtract().web_search_and_extract(url)
    print(result)
