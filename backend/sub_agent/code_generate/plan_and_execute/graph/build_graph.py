from typing import  Any

from langchain_core.runnables import RunnableConfig
from langchain_openai.chat_models.base import BaseChatOpenAI
from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.types import StateT, Checkpointer
from langgraph.typing import ContextT, InputT, OutputT

from backend.config.config import AgentConfig
from backend.sub_agent.code_generate.agents.agent_state import CodeAgentState
from backend.sub_agent.code_generate.agents.code_agent.data_source_agent.data_source_code_generate import \
    DataSourceCodeGenerate
from backend.sub_agent.code_generate.agents.docs_agents.data_source_agent.data_source_doc_generate import \
    DataSourceDocGenerate
from backend.sub_agent.code_generate.agents.test_agent.data_source_agent.data_source_test_generate import \
    DataSourceTestGenerate


def build_data_source_graph(
        agent_config: AgentConfig,
        model: BaseChatOpenAI,
        config: RunnableConfig,
        check_pointer: Checkpointer,
) -> StateGraph[StateT, ContextT, InputT, OutputT] | None:
    print("📊 开始构建生成 data source 多Agent系统...")

    if not agent_config.generate_code and not agent_config.generate_test and not agent_config.generate_doc:
        print("\n ❌ 没有要生成的内容，请前往config.yaml中配置要生成的 code/test/doc")
        return None

    workflow = StateGraph(CodeAgentState)

    workflow.add_node("generate_code", DataSourceCodeGenerate(model, config, check_pointer).generate)
    workflow.add_node("generate_test", DataSourceTestGenerate(model, config, check_pointer).generate)
    workflow.add_node("generate_doc", DataSourceDocGenerate(model, config, check_pointer).generate)

    if agent_config.generate_code:
        workflow.set_entry_point("generate_code")
    elif agent_config.generate_test:
        workflow.set_entry_point("generate_test")
    elif agent_config.generate_doc:
        workflow.set_entry_point("generate_doc")

    def router(state: CodeAgentState) -> str:
        current_step = state.get("current_step", "")

        if current_step == "generate_code_complete":
            if agent_config.generate_test:
                return "generate_test"
            elif agent_config.generate_doc:
                return "generate_doc"
            else:
                return END
        if current_step == "generate_test_complete":
            if agent_config.generate_doc:
                return "generate_doc"
            else:
                return END
        if current_step == "generate_doc_complete":
            return END

        return END

    workflow.add_conditional_edges("generate_code", router, {
        "generate_test" : "generate_test",
        "generate_doc" : "generate_doc",
        END : END,
    })
    workflow.add_conditional_edges("generate_test", router, {
        "generate_doc": "generate_doc",
        END: END,
    })
    workflow.add_conditional_edges("generate_doc", router, {
        END: END,
    })

    print("✅  data source 多Agent系统构建完成...  ")

    return workflow

def build_resource_graph(self) -> Any:
    print("📊 开始构建生成 resource 多Agent系统...")