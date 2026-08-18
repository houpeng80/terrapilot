from langchain.tools import tool

from backend.sub_agent.code_generate.agents.code_agent.prompts import SKILLS, SUB_SKILLS

@tool
def skill_load(resource_type: str, skill_name: str):
    """加载指定技能的详细提示词时触发

    Args:
        resource_type: 资源类型，包括resource和data_source
        skill_name: 技能名称
    """
    if resource_type not in SKILLS:
        return f"resource type {resource_type} not exist"
    skills = SKILLS[resource_type]

    if skill_name not in skills:
        return f"skill {skill_name} not exist"
    return skills[skill_name]["content"]

@tool
def sub_skill_load(resource_type: str, skill_name: str):
    """加载指定子技能的详细提示词时触发

    Args:
        resource_type: 资源类型，包括resource和data_source
        skill_name: 技能名称
    """
    if resource_type not in SUB_SKILLS:
        return f"resource type {resource_type} not exist"
    skills = SUB_SKILLS[resource_type]

    if skill_name not in skills:
        return f"skill {skill_name} not exist"
    return skills[skill_name]["content"]