import logging
from typing import override, Any, get_args

from langchain_core.messages import HumanMessage
from langgraph.runtime import Runtime
from langchain.agents.middleware import AgentMiddleware
from langgraph.typing import ContextT
from langchain.agents.middleware.types import hook_config

from backend.leader_agent.agent_state import TerrapilotAgentState
from backend.sub_agent.intent_recognize.intent_recognize import intent_literal, IntentRecognize

logger = logging.getLogger(__name__)

class IntentRecognizeMiddleware(AgentMiddleware[TerrapilotAgentState]):

    def __init__(self, config: dict[str, Any], agent_name: str | None = None):
        super().__init__()
        self._agent_name = agent_name
        self.config=config

    @hook_config(can_jump_to=["end"])
    @override
    def before_agent(self, state: TerrapilotAgentState, runtime: Runtime[ContextT]) -> dict[str, Any] | None:
        logger.info(" agent {%s} begin execute ", self._agent_name)
        logger.info(" state messages: %s ", state.get("messages"))
        return self.intent_recognize(state)

    @hook_config(can_jump_to=["end"])
    @override
    def abefore_agent(self, state: TerrapilotAgentState, runtime: Runtime) -> dict[str, Any] | None:
        logger.info(" agent {%s} begin execute ", self._agent_name)
        return self.intent_recognize(state)

    def intent_recognize(self, state: TerrapilotAgentState,) -> dict[str, Any] | None:
        intent_confidence = IntentRecognize(config=self.config)
        res = intent_confidence.intent_recognize(agent_state=state)
        intent = res.intent
        confidence = res.confidence
        params = res.params
        missing_params = res.missing_params
        reasoning = res.reasoning

        logger.info(f"识别到用户的意图：{res}", )

        check_res, msg =  self.intent_and_params_check(intent, missing_params)
        if not check_res:
            if intent == "unknow":
                print("请咨询terraform相关问题，禁止闲聊：", reasoning)
            else:
                message_parts = [f"\r\n❓ 参数缺失： ", f"{", ".join(missing_params)}", msg, f"reasoning: {reasoning}"]
                formatted_message = "\n".join(message_parts)
                print(formatted_message)
            return {
                "jump_to": "end"
            }

        intent = res.intent
        if intent == "history_record":
            return {
                "get_history" : True,
                "history_index" : res.params["history_index"],
            }

        new_request = {
            "intent": intent,
            "confidence": confidence,
            "params": params,
            "missing_params": missing_params,
            "reasoning": reasoning,
        }
        histories = state.get("histories")
        new_messages = HumanMessage(content=f"Here is a summary of the conversation to date:\n\n{summary}", name="summary")
        return {
            "messages": [],
            "histories": [*histories, new_request],
            "get_history": False,
        }


    def intent_and_params_check(self, intent: str, missing_params: list[str]) -> tuple[bool, str]:
        if intent not in get_args(intent_literal):
            return False, f"the intent {intent} is not recognized"

        if intent == "unknow":
            return False, ""

        if intent == "generate_script":
            if missing_params and len(missing_params) > 0:
                missing_params_str = ",".join(missing_params)
                return False, f"the params {missing_params_str} are missing"

        if intent == "generate_code":
            if missing_params and len(missing_params) > 0:
                missing_params_str = ",".join(missing_params)
                return False, f"the params {missing_params_str} are missing"

        if intent == "query_resource_by_name":
            if missing_params and len(missing_params) > 0:
                missing_params_str = ",".join(missing_params)
                return False, f"the params {missing_params_str} are missing"

        if intent == "query_resource_by_api":
            if missing_params and len(missing_params) > 0:
                missing_params_str = ",".join(missing_params)
                return False, f"the params {missing_params_str} are missing"

        if intent == "query_resource_by_content":
            if missing_params and len(missing_params) > 0:
                missing_params_str = ",".join(missing_params)
                return False, f"the params {missing_params_str} are missing"

        return True, "success"
