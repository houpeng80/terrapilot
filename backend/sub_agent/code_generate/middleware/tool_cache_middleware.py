import logging
from typing import Any
from collections.abc import Callable

from langchain.agents.middleware import AgentMiddleware
from langgraph.prebuilt.tool_node import ToolCallRequest
from langchain_core.messages import ToolMessage
from langgraph.types import Command

logger = logging.getLogger(__name__)

tool_cache = {}

class ToolCacheMiddleware(AgentMiddleware):

    def __init__(self, agent_name: str | None = None):
        super().__init__()
        self._agent_name = agent_name

    def wrap_tool_call(
            self,
            request: ToolCallRequest,
            handler: Callable[[ToolCallRequest],
            ToolMessage | Command[Any]]
    ) -> ToolMessage | Command[Any]:
        tool_name = request.tool_call["name"]
        tool_args = request.tool_call["args"]

        if tool_name == "web_search_and_extract":
            cache_key = f"{tool_name}:{tool_args}"
            if cache_key in tool_cache:
                cached_content = tool_cache[cache_key]
                logger.info("call tool hit tool cache: tool=%s args=%s", tool_name, tool_args)
                return ToolMessage(
                    content=cached_content,
                    tool_call_id=request.tool_call.get("id", ""),
                    name=tool_name,
                )

        # invoke tool
        result = handler(request)

        if tool_name == "web_search_and_extract":
            cache_key = f"{tool_name}:{tool_args}"
            # 存入缓存
            if hasattr(result, 'content'):
                tool_cache[cache_key] = result.content
                logger.info(" write tool message to tool cache: tool=%s args=%s", tool_name, tool_args)
                logger.debug("tool result=%s", result.content)

        return result
