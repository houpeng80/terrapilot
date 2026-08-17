import threading
from typing import Any

from backend.sub_agent.oncall.oncall_agent import OncallAgent
from backend.sub_agent.script_generate.script_generate_agent import ScriptGenerateAgent
from backend.worker.workers import Worker

BUILTIN_WORKERS = [
    OncallAgent(),
    ScriptGenerateAgent()
]

WORKER_INTENTS = {
    "oncall_agent" : [
        "query_oncall",
        "query_reference_docs",
        "query_latest_version",
        "whether_support_special_region",
        "query_resource_by_name"
        "query_resource_by_api"
        "query_resource_by_content"
    ],
    "script_generate_agent" : [
        "generate_script"
    ],
    "code_generate_agent" : [
        "generate_code"
    ]
}

class WorkerRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self.workers: dict[str, Any] = {}
        self.intent_to_worker: dict[str, str] = {}
        self.init_builtin_worker_registry()
        self.init_intent_to_worker()

    def init_builtin_worker_registry(self) -> None:
        with self._lock:
            for worker in BUILTIN_WORKERS:
                self.register(worker.name, worker)

    def init_intent_to_worker(self) -> None:
        with self._lock:
            for worker, intents in WORKER_INTENTS.items():
                for intent in intents:
                    self.intent_to_worker[intent] = worker

    def register(self, name, agent):
        with self._lock:
            self.workers[name] = agent

    def unregister(self, name: str) -> None:
        with self._lock:
            if name not in self.workers:
                raise KeyError(f"Worker '{name}' not found")
            del self.workers[name]

    def get_worker(self, name: str) -> Any:
        with self._lock:
            return self.workers[name]

    def get_worker_by_intent(self, intent: str) -> Worker:
        with self._lock:
            return self.get_worker(self.intent_to_worker[intent])
