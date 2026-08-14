from langchain.agents import AgentState
from langchain.agents.middleware import dynamic_prompt
from langgraph.config import get_config

from backend.leader_agent.prompt import apply_prompt_template

@dynamic_prompt
def build_system_prompt_template(state: AgentState) -> str:
    """每次model call 都去动态的生成 system prompt，主要是为了使用用户最新的长期记忆，因为压缩会把摘要存放到文档，不动态的获取会丢失该部分长期记忆"""

    from backend.leader_agent.leader_agent import AGENT_NAME
    user_id = get_config().get("configurable", {}).get("user_id")
    return apply_prompt_template(user_id=user_id, agent_name=AGENT_NAME)