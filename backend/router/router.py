from sub_agent.intent_recognize.intent_recognize import IntentRecognize, IntentResult


class RouterManager:
    def __init__(self, intent_recognize: IntentRecognize):
        self.intent_recognize = intent_recognize

    def router(self, intent: IntentResult) -> :
        intent_ok, msg = self.intent_recognize.intent_res_check(intent.intent, intent.missing_params)
        if not intent_ok:
            message_parts = [f"\r\n❓ 参数缺失： ", f"{", ".join(intent.missing_params)}", msg,
                             f"reasoning: {intent_res.reasoning}"]
            formatted_message = "\n".join(message_parts)
            
        if intent.intent :
    