from backend.leader_agent.agent_state import Intent
from backend.sub_agent.intent_recognize.intent_recognize import IntentRecognize, IntentResult

JUMP_TO_END = "jump_to_end"

class RouterManager:
    def __init__(self, intent_recognize: IntentRecognize):
        self.intent_recognize = intent_recognize

    def router(self, intent: IntentResult, histories: list[Intent]) -> tuple[str, str]:
        intent_ok, msg = self.intent_recognize.intent_res_check(intent.intent, intent.missing_params)
        if not intent_ok:
            message_parts = [f"\r\n❓ 参数缺失： ", f"{", ".join(intent.missing_params)}", msg, f"reasoning: {intent.reasoning}"]
            formatted_message = "\n".join(message_parts)
            return JUMP_TO_END, formatted_message

        if intent.intent == "unknown":
            return JUMP_TO_END, intent.reasoning
            
        if intent.intent == "history_record":
            history_index = intent.params["history_index"]
            if len(histories) < int(history_index):
                error_message = f"当前只有{len(histories)}个任务记录，您要查询的历史第{history_index}个任务不存在"
                return JUMP_TO_END, error_message

            history_intent_result = histories[int(history_index)-1]["result"]
            if not history_intent_result or len(history_intent_result) == 0:
                error_message = f"历史任务记录为空，需要重新生成"
                return JUMP_TO_END, error_message

            return JUMP_TO_END, history_intent_result

        return intent.intent, intent.reasoning

    