from langchain.agents import AgentState

class ScriptAgentState(AgentState):
    """生成terraform代码的共享状态"""

    # 基础信息
    request_message: str  # 用户原始请求
    resource_type: str   #资源类型resource/data_source

    # 各阶段成果
    script_result: str  # 代码最终结果

    # 记录重试的次数
    retries_time: int

    input_token_statistics: int
    output_token_statistics: int
    total_token_statistics: int