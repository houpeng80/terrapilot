import threading
from typing import Any

from backend.sub_agent.oncall.oncall_agent import OncallAgent
from backend.sub_agent.sub_agents import SubAgent

BUILTIN_SUB_AGENTS = [
    OncallAgent()
]

SUB_AGENT_CONTAIN_INTENTS = {
    "oncall_agent" : [
        "query_oncall",
        "query_reference_docs",
        "query_latest_version",
        "whether_support_special_region",
        "query_resource_by_name"
        "query_resource_by_api"
        "query_resource_by_content"
    ],
    "generate_script" : [
        "script_generate_agent"
    ],
    "generate_code" : [
        "code_generate_agent"
    ]
}

class SubAgentRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self.sub_agents: dict[str, Any] = {}  # name -> subagent实例
        self.intent_to_sub_agent: dict[str, str] = {}
        self.init_builtin_sub_agents_registry()
        self.init_intent_to_sub_agent()

    def init_builtin_sub_agents_registry(self) -> None:
        with self._lock:
            for sub_agent in BUILTIN_SUB_AGENTS:
                self.register(sub_agent.name, sub_agent)

    def init_intent_to_sub_agent(self) -> None:
        with self._lock:
            for sub_agent, intents in SUB_AGENT_CONTAIN_INTENTS.items():
                for intent in intents:
                    self.intent_to_sub_agent[intent] = sub_agent

    def register(self, name, agent):
        with self._lock:
            self.sub_agents[name] = agent

    def unregister(self, name: str) -> None:
        with self._lock:
            if name not in self.sub_agents:
                raise KeyError(f"Sub-Agent '{name}' not found")
            del self.sub_agents[name]

    def get_sub_agent(self, name: str) -> Any:
        with self._lock:
            return self.sub_agents[name]

    def get_sub_agent_by_intent(self, intent: str) -> SubAgent:
        with self._lock:
            return self.get_sub_agent(self.intent_to_sub_agent[intent])
