import logging
from typing import override, Any

from langchain.agents.middleware import AgentMiddleware, hook_config
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai.chat_models.base import BaseChatOpenAI
from langgraph.runtime import Runtime
from langgraph.types import  Checkpointer

from backend.config.config import AgentConfig
from backend.sub_agent.code_generate.agents.agent_state import CodeAgentState
from backend.sub_agent.code_generate.agents.check_agent.code_check.data_source.data_source_code_check import \
    DataSourceCodeCheck, DataSourceCodeCheckInfo
from backend.sub_agent.code_generate.agents.check_agent.code_check.resource.resource_code_check import \
    ResourceCodeCheck, ResourceCodeCheckInfo

logger = logging.getLogger(__name__)

class CodeCheckMiddleware(AgentMiddleware[CodeAgentState]):

    state_schema = CodeAgentState

    def __init__(
            self,
            agent_config: AgentConfig,
            model: BaseChatOpenAI,
            config: RunnableConfig,
            checkpointer: Checkpointer,
            agent_name: str | None = None
    ):
        """Initialize the CodeCheckMiddlewareState"""
        super().__init__()
        self.model = model
        self._agent_name = agent_name
        self.agent_config = agent_config
        self.checkpointer = checkpointer
        self.config = config

    @hook_config(can_jump_to=["model"])
    @override
    def after_model(self, state: CodeAgentState, runtime: Runtime) -> dict[str, Any] | None:
        return self.code_check(state)

    @hook_config(can_jump_to=["model"])
    @override
    def aafter_model(self, state: CodeAgentState, runtime: Runtime) -> dict[str, Any] | None:
        return self.code_check(state)

    def code_check(self, state: CodeAgentState) -> dict[str, Any] | None:
        latest_message = state['messages'][-1]

        if not self.agent_config.code_check:
            return None

        if isinstance(latest_message, AIMessage):
            if (latest_message.tool_calls and
                    latest_message.tool_calls[0]['name'] == "write_file" and
                    latest_message.tool_calls[0]['args']["content"]
            ):
                state["code_result"] = latest_message.tool_calls[0]['args']["content"]
                return {
                    "code_result": latest_message.tool_calls[0]['args']["content"],
                }
            elif "finish_reason" in latest_message.response_metadata and latest_message.response_metadata["finish_reason"] in ["stop", "length"]:
                if state["resource_type"] == "resource":
                    check_result = ResourceCodeCheck(self.model, self.config, self.checkpointer).code_check(agent_state=state)
                    fix_message = self.build_resource_code_review_message(check_result)
                else:
                    check_result = DataSourceCodeCheck(self.model, self.config, self.checkpointer).code_check(agent_state=state)
                    fix_message = self.build_data_source_code_review_message(check_result)

                logger.info(f"\ncode check result={fix_message}")
                print(f"\ncode check result={fix_message}")
                if len(fix_message) > 0:
                    if self.agent_config.code_fix:
                        fix_human_message = HumanMessage(
                            content=fix_message,
                        )
                        messages = state["messages"] + [fix_human_message]
                        return {
                            "messages": messages,
                            "code_retries_time": state['code_retries_time'] + 1,
                            "jump_to": "model"
                        }

        return state

    def build_data_source_code_review_message(self, check_result: DataSourceCodeCheckInfo):
        res = ""
        if check_result.contain_description:
            res = res + f"不要包含 Description\n"
        if check_result.contain_force_new:
            res = res + f"不要包含 ForceNew\n"
        if len(check_result.added_params):
            items = ""
            for param in check_result.added_params:
                items += param + ", "
            res = res + f"不要包含API中不存在的参数{items}\n"
        if len(check_result.deleted_params):
            items = ""
            for param in check_result.deleted_params:
                items += param + ", "
            res = res + f"缺少参数{items}\n"
        if check_result.validation_error:
            res = res + f"不要包含 ValidateFunc\n"
        if check_result.bool_type_params_error:
            res = res + f"bool类型参数要转换为string类型，并且使用ValidateFunc校验\n"
        if check_result.region_param_error:
            res = res + f"region参数不正确，要根据服务是否全局决定要不要添加region参数\n"
        if not check_result.contain_api_comment:
            res = res + f"缺少API注释\n"
        if not check_result.page_right:
            res = res + f"分页不正确，根据api的分页信息选择正确的分页方式\n"

        return res

    def build_resource_code_review_message(self, check_result: ResourceCodeCheckInfo):
        res = ""
        if check_result.contain_description:
            res = res + f"不要包含 Description\n"
        if check_result.contain_force_new:
            res = res + f"不要包含 ForceNew\n"
        if len(check_result.non_updatable_params_contain_updated_param):
            items = ""
            for param in check_result.non_updatable_params_contain_updated_param:
                items += param + ", "
            res = res + f"NonUpdatable列表中不要包含参数{items}\n"
        if len(check_result.non_updatable_params_not_contain_non_updatable_param):
            items = ""
            for param in check_result.non_updatable_params_not_contain_non_updatable_param:
                items += param + ", "
            res = res + f"NonUpdatable列表中要包含参数{items}\n"
        if check_result.validation_error:
            res = res + f"不要包含 ValidateFunc\n"
        if check_result.bool_type_params_error:
            res = res + f"bool类型参数要转换为string类型，并且使用ValidateFunc校验\n"
        if check_result.region_param_error:
            res = res + f"region参数不正确，要根据服务是否全局决定要不要添加region参数\n"
        if not check_result.contain_api_comment:
            res = res + f"缺少API注释\n"
        if not check_result.contain_import:
            res = res + f"缺少导入函数\n"
        if not check_result.contain_import:
            res = res + f"缺少超时时间n"

        return res
