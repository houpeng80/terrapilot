from typing import Any, Optional

class WorkerRequest:
    def __init__(self, intent: str, params: dict[str, str], reasoning: str):
        self.intent = intent
        self.params = params
        self.reasoning = reasoning

class WorkerExecutionResult:
    def __init__(self, success: bool, result: Any = None, error: Optional[str] = None, duration: float = 0.0):
        self.success = success
        self.result = result
        self.error = error
        self.duration = duration

class Worker:
    def __init__(self, name: str):
        self.name = name

    def execute(self, intent: WorkerRequest) -> str:
        pass

    def build_request_message(self, intent: WorkerRequest) -> str:
        pass