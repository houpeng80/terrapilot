from leader_agent.agent_state import TerrapilotAgentState, Intent
from backend.sub_agent.intent_recognize.intent_recognize import IntentResult
from backend.sub_agent.sub_agent_scheduler import SubAgentExecutionResult

class SubAgent:
    def __init__(self, name: str):
        self.name = name

    def execute(self, intent: IntentResult) -> SubAgentExecutionResult:
        pass