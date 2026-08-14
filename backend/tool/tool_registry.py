from typing import Callable

from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool

from assistant.tool.search_tool import resource_search_tool, api_search_tool, rag_search_tool

def get_tools_by_intent(intent:str) ->list[BaseTool| Callable[[Callable | Runnable], BaseTool]]:
    if len(intent) == 0:
        return []

    if intent == "query_resource_by_name":
        return [resource_search_tool]
    if intent == "query_resource_by_api":
        return [api_search_tool]
    if intent == "query_resource_by_content":
        return [rag_search_tool]

    return []

class ToolRegistry:
    def __init__(self):
        pass