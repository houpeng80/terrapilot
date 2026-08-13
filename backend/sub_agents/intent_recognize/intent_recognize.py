import time
from typing import Literal, Any
from pydantic import BaseModel, Field

from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage

from backend.config.config import get_app_config
from backend.leader_agent.agent_state import TerrapilotAgentState
from backend.middleware.log_middleware import LoggingMiddleware
from backend.middleware.token_usage_middleware import TokenUsageMiddleware
from backend.model import get_model
from backend.sub_agents.intent_recognize.prompt import apply_system_prompt

AGENT_NAME = "intent_recognize_agent"

intent_literal = Literal[
    "generate_script",
    "generate_code",
    "query_oncall",
    "query_latest_version",
    "query_reference_docs",
    "whether_support_special_region",
    "query_resource_by_name",
    "query_resource_by_api",
    "query_resource_by_content",
    "history_record",
    "unknow"
]

params_literal = Literal[
    "service_type",
    "resource_type",
    "resource_name",
    "api_method",
    "api_url",
    "content",
    "contain_reference",
    "input",
    "history_num"
]

class IntentResult(BaseModel):
    """意图识别结果的结构化输出模型"""
    intent: intent_literal = Field(description="用户输入所对应的业务意图")
    confidence: float = Field(
        description="模型对意图判断的置信度分数，取值范围 0 到 1",
        ge=0,
        le=1
    )
    params: dict[params_literal, str] = Field(description="用户要执行业务的参数",)
    missing_params: list[str] = Field(description="用户要执行业务缺失的参数")
    # contain_reference: bool = Field(description="生成脚本时是否要生成依赖资源信息，不生成为false，生成依赖资源为true")
    # input: str = Field(description="生成代码时的输入信息")
    reasoning: str = Field(description="简短说明做出该意图判断的理由")

class IntentRecognize:
    def __init__(self, config: dict[str, Any]):
        self.model = get_model(get_app_config().model_type)
        self.agent_config = get_app_config()
        self.check_pointer = InMemorySaver()
        self.config = config
        self.agent = self.create_intent_recognize_agent()

    def intent_recognize(self, agent_state: TerrapilotAgentState) -> IntentResult:
        i = 0
        while i < 3:
            result = self.agent.invoke(
                input=agent_state,
                config=self.config,
            )
            print("intent_recognize result=", result)
            if "structured_response" in result:
                return result["structured_response"]
            time.sleep(1)
        raise Exception("intent_recognize failed")

    def create_intent_recognize_agent(self):
        agent = create_agent(
            model=self.model,
            checkpointer=self.check_pointer,
            system_prompt=apply_system_prompt(),
            response_format=IntentResult,
            middleware=[
                LoggingMiddleware(agent_name=AGENT_NAME),
                TokenUsageMiddleware(agent_name=AGENT_NAME),
            ],
        )
        return agent

if __name__ == "__main__":
    config = {"configurable": {"thread_id": "user-001"}}

    query1 = "帮我查一下 RDS 服务的 huaweicloud_rds_notify_replace_node 这个资源支持吗"
    query2 = "RDS 服务的 POST /v3/{project_id}/instances/{instance_id}/db-jobs/{job_id}/switch 这个API支持吗"
    query3 = "帮我查一下 DCS 服务支持创建实例吗"
    query4 = "provider支持北京四这个region吗"
    query5 = "有没有provider的参考文档"
    query6 = "当前oncall是谁"
    query7 = "rds 实例这个支持name这个字段吗"
    query8 = "当前天气怎么样"
    query9 = "我好看吗"
    query10 = "帮我查一下 RDS 服务的 /v3/{project_id}/instances/{instance_id}/db-jobs/{job_id}/switch 这个API支持吗"
    query11 = "可以查询当前所有的规格吗"

    # input_message = {
    #     "messages": [HumanMessage(content=query1)],
    #     "input_token_statistics": 0,
    #     "output_token_statistics": 0,
    #     "total_token_statistics": 0,
    #     "model_cycle_time": 1,
    # }

    intent_confidence = IntentRecognize(config=config)
    # res = intent_confidence.intent_recognize(agent_state=input_message)
    # print("=====================")
    # print(f"识别意图: {res.intent}")
    # print(f"置信度: {res.confidence}")
    # print(f"参数: {res.params}")
    # print(f"推理理由: {res.reasoning}")
    # querys = [query1, query2, query3, query4, query5, query6, query7, query8,query9,query10,query11]
    # for query in querys:
    #     input_message = {
    #         "messages": [HumanMessage(content=query)],
    #         "input_token_statistics": 0,
    #         "output_token_statistics": 0,
    #         "total_token_statistics": 0,
    #         "model_cycle_time": 1,
    #     }
    #     res = intent_confidence.intent_recognize(agent_state=input_message)
    #     print("=====================")
    #     print(f"识别意图: {res.intent}")
    #     print(f"置信度: {res.confidence}")
    #     print(f"参数: {res.params}")
    #     print(f"推理理由: {res.reasoning}")

    while True:
        user_input = input("\nUser: ")
        if user_input.lower() in ["q", "quit"]:
            break

        input_message = {
            "messages": [HumanMessage(content=user_input)],
            "input_token_statistics": 0,
            "output_token_statistics": 0,
            "total_token_statistics": 0,
            "model_cycle_time": 1,
        }
        res = intent_confidence.intent_recognize(agent_state=input_message)
        print("=====================")
        print(f"识别意图: {res.intent}")
        print(f"置信度: {res.confidence}")
        print(f"参数: {res.params}")
        print(f"缺失的参数: {res.missing_params}")
        # print(f"是否包含依赖资源: {res.contain_reference}")
        # print(f"生成代码的原始请求: {res.input}")
        print(f"推理理由: {res.reasoning}")
