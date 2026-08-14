from typing import TypedDict

from langchain.agents import AgentState

class Intent(TypedDict):
    intent: str
    confidence: float
    params: dict[str, str]
    missing_params: dict[str, str]
    reasoning: str
    result: str

class TerrapilotAgentState(AgentState):
    # 基础信息
    request_message: str  # 用户原始请求

    # 实现历史需求
    histories: list[Intent]

    # 识别到要获取历史消息
    get_history: bool
    # 历史消息下标，1表示第0条，依次类推
    history_index : int

    # 当前model循环次数
    model_cycle_time: int

    # token消耗
    input_token_statistics: int
    output_token_statistics: int
    total_token_statistics: int
