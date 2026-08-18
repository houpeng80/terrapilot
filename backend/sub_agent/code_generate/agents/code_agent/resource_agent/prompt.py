from backend.sub_agent.code_generate.agents.code_agent.resource_agent.create_prompt import apply_create_prompt_template
from backend.sub_agent.code_generate.agents.code_agent.resource_agent.delete_prompt import apply_delete_prompt_template
from backend.sub_agent.code_generate.agents.code_agent.resource_agent.import_prompt import apply_import_prompt_template
from backend.sub_agent.code_generate.agents.code_agent.resource_agent.read_prompt import apply_read_prompt_template
from backend.sub_agent.code_generate.agents.code_agent.resource_agent.update_prompt import apply_update_prompt_template
from backend.sub_agent.code_generate.agents.code_agent.resource_agent.utils import build_skills

SKILLS = {
    "create_step" : {
        "name": "create_step",
        "description": "生成创建resource步骤，当需要生成创建resource相关代码时触发",
        "content": apply_create_prompt_template(),
    },
    "read_step" : {
        "name": "read_step",
        "description": "生成查询resource步骤，当需要生成查询resource相关代码时触发",
        "content": apply_read_prompt_template(),
    },
    "update_step" : {
        "name": "update_step",
        "description": "生成更新resource步骤，当需要生成更新resource相关代码时触发",
        "content": apply_update_prompt_template(),
    },
    "delete_step" : {
        "name": "delete_step",
        "description": "生成删除resource步骤，当需要生成删除resource相关代码时触发",
        "content": apply_delete_prompt_template(),
    },
    "import_step" : {
        "name": "import_step",
        "description": "生成导入resource步骤，当需要生成导入resource相关代码时触发",
        "content": apply_import_prompt_template()
    }
}

RESOURCE_PROMPT_TEMPLATE = """
<role>
你是{agent_name}，一个terraform data source代码生成的超级agent。
</role>

<thinking_style>
- 在采取行动之前，请简洁而有策略地思考用户的请求。
- 将任务分解：哪些部分很明确？哪些部分含糊不清？缺少什么？
- 优先检查：如有任何不清楚、遗漏或存在多种解释的地方，您必须首先寻求澄清——请勿继续工作。
- 关键点：思考之后，你必须向用户提供实际的回复。思考是为了规划，回复是为了交付。
- 你的回答必须包含实际答案，而不仅仅是提及你的想法。
</thinking_style>

<available_skills>
    {skill_items}
</available_skills>

<note>
- 明令禁止直接去加载所有的API信息，只有等用到的时候再去加载
- 在执行以下步骤时，如果涉及到了具体技能，那么就先用skill_load工具去获取技能内容，资源类型为resource，然后再按照技能规范执行
- 执行时按步骤依次执行，每一步生成代买以后再执行下一步，每次只加载本步骤所需要的skill，然后就生成该步骤的代码
- 不要等所有的skill都加载进来才生成代码，也不要一次性加载所有的skill
- 最终输出结果只包含最终的完整代码，其他都不需要
</note>

<step>
1. 生成创建 resource 相关代码

2. 生成查询 resource 相关代码

3. 生成更新 resource 相关代码

4. 生成删除 resource 相关代码

5. 生成导入 resource 相关代码

6. 在生成结果前边添加包信息，以及引入所需要的包信息

7. 将最终生成的完整代码写到文件中，写入文件时分块写入，如果被截断就继续输出上一段未完成的内容，不要重复，不要总结，不要换行
   - 路径为{repo_root}\\huaweicloud\\services\\service_name\\resource_name.go, service_name为服务名，resource_name为资源名
   - 如果用户已经提供，就使用用户提供的名称，如果没提供就自动生成，格式为resource_SSS_XXX`，其中`SSS` 为该service_name, `XXX` 为该API要获取的功能信息
</step>
"""

def apply_prompt_template(agent_name: str, repo_root: str) -> str:
    prompt = RESOURCE_PROMPT_TEMPLATE.format(
        agent_name=agent_name or "Terraform code generate agent",
        skill_items=build_skills(SKILLS),
        create_step=SKILLS["create_step"]["description"],
        read_step=SKILLS["read_step"]["description"],
        update_step=SKILLS["update_step"]["description"],
        delete_step=SKILLS["delete_step"]["description"],
        import_step=SKILLS["import_step"]["description"],
        repo_root=repo_root,
    )
    return prompt

