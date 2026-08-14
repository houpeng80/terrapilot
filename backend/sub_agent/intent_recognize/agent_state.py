from langchain.agents import AgentState

class OncallAgentState(AgentState):
    # 基础信息
    request_message: str  # 用户原始请求

    # 意图识别信息
    intent: str
    confidence: float
    params: dict[str, str]
    missing_params: dict[str, str]
    reasoning: str

    # 记录当前model循环次数
    model_cycle_time: int

    # 记录总的token消耗
    input_token_statistics: int
    output_token_statistics: int
    total_token_statistics: int