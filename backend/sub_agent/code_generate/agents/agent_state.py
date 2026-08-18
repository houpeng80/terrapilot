from langchain.agents import AgentState

class CodeAgentState(AgentState):
    """生成terraform代码的共享状态"""

    # 基础信息
    request_message: str  # 用户原始请求
    resource_type: str   #资源类型resource/data_source

    # 各阶段成果
    code_result: str  # 代码最终结果
    test_result: str  # test最终结果
    doc_result: str  # 文档最终结果

    # 记录重试的次数
    code_retries_time: int
    test_retries_time: int
    doc_retries_time: int

    # 流程控制 generating_code/generate_code_complete/generating_test/generate_test_complete/generating_doc/generate_doc_complete
    current_step: str  # 当前步骤

    input_token_statistics: int
    output_token_statistics: int
    total_token_statistics: int