from backend.tool.builtins.base_tool import oncall_schedule, reference_docs
from backend.tool.builtins.file_tool import read_md
from backend.tool.builtins.github_tool import get_latest_provider_version
from backend.tool.builtins.search_tool import resource_search_tool, api_search_tool, rag_search_tool

BASE_TOOLS = [oncall_schedule, reference_docs]
FILE_TOOLS = [read_md]
GITHUB_TOOLS = [get_latest_provider_version]
SEARCH_TOOLS = [resource_search_tool, api_search_tool, rag_search_tool]

BUILTIN_TOOLS = [
    *BASE_TOOLS,
    *FILE_TOOLS,
    *GITHUB_TOOLS,
    *SEARCH_TOOLS,
]