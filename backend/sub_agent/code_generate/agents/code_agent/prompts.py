from backend.sub_agent.code_generate.agents.code_agent.data_source_agent.prompt import SKILLS as DATA_SOURCE_SKILLS
from backend.sub_agent.code_generate.agents.code_agent.resource_agent.prompt import SKILLS as RESOURCE_SKILLS
from backend.sub_agent.code_generate.agents.code_agent.resource_agent.create_prompt import CREATE_SKILLS
from backend.sub_agent.code_generate.agents.code_agent.resource_agent.delete_prompt import DELETE_SKILLS
from backend.sub_agent.code_generate.agents.code_agent.resource_agent.read_prompt import READ_SKILLS
from backend.sub_agent.code_generate.agents.code_agent.resource_agent.update_prompt import UPDATE_SKILLS

SKILLS = {
    "data_source":DATA_SOURCE_SKILLS,
    "resource":RESOURCE_SKILLS,
}

SUB_SKILLS = {
    "resource": {**CREATE_SKILLS, **READ_SKILLS, **UPDATE_SKILLS, **DELETE_SKILLS},
}