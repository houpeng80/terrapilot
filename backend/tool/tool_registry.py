import threading
from typing import Dict, Optional, List

from langchain_core.tools import BaseTool

from backend.tool.tools import BUILTIN_TOOLS

class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        self._lock = threading.RLock()
        self.intent_group_tools: dict[str, list[str]] = {
            "query_oncall": ["oncall_schedule"],
            "query_reference_docs": ["reference_docs"],
            "query_latest_version": ["get_latest_provider_version"],
            "whether_support_special_region": ["reference_docs"],
            "query_resource_by_name": ["resource_search_tool", "reference_docs", "read_md"],
            "query_resource_by_api": ["api_search_tool", "reference_docs", "read_md"],
            "query_resource_by_content": ["rag_search_tool", "reference_docs", "read_md"],
            "generate_script": [""],
            "generate_code": [""],
            "history_record": [""],
        }
        self.init_builtin_tools_registry()

    def init_builtin_tools_registry(self) -> None:
        with self._lock:
            for tool in BUILTIN_TOOLS:
                self.register(tool)

    def register(self, tool: BaseTool, name: Optional[str] = None) -> None:
        """注册一个工具，默认使用 tool.name 作为key"""
        tool_name = name or tool.name
        with self._lock:
            if tool_name in self._tools:
                raise ValueError(f"Tool '{tool_name}' already registered")
            self._tools[tool_name] = tool

    def unregister(self, name: str) -> None:
        with self._lock:
            if name not in self._tools:
                raise KeyError(f"Tool '{name}' not found")
            del self._tools[name]

    def get_tool(self, name: str) -> BaseTool:
        with self._lock:
            return self._tools[name]

    def get_tools(self) -> List[BaseTool]:
        with self._lock:
            return list(self._tools.values())

    def get_tools_by_names(self, names: list[str]) -> List[BaseTool]:
        with self._lock:
            return [self.get_tool(name) for name in names]

    def get_tools_by_intent(self, intent: str) -> List[BaseTool]:
        with self._lock:
            return self.get_tools_by_names(self.intent_group_tools[intent])

    def list_names(self) -> List[str]:
        with self._lock:
            return list(self._tools.keys())

    def __contains__(self, name: str) -> bool:
        with self._lock:
            return name in self._tools