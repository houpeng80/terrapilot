from typing import Any, Optional

from backend.sub_agent.intent_recognize.intent_recognize import IntentResult

class SubAgentExecutionResult:
    def __init__(self, success: bool, result: Any = None, error: Optional[str] = None, duration: float = 0.0):
        self.success = success
        self.result = result
        self.error = error
        self.duration = duration

class SubAgent:
    def __init__(self, name: str):
        self.name = name

    def execute(self, intent: IntentResult) -> SubAgentExecutionResult:
        pass

    def build_request_message(self, intent: IntentResult) -> str:
        pass