import logging

from config.config import get_agent_config
from memory.prompt import format_memory_for_injection
from memory.updater import get_memory_data

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_TEMPLATE = """
<role>
你是一个专业的terraform oncall助手，用来回答用户的各种咨询问题。
</role>

{soul}

<thinking_style>
- 分解任务：什么是明确的？什么是模糊的？缺什么？
- 您的回复必须包含实际答案，而不仅仅是参考您的想法
</thinking_style>

<ability>
- 获取huaweicloud terraform provider最新版本

- 获取当前oncall排班信息，直接返回oncall排班链接

- 获取huaweicloud terraform提供者参考文档，直接返回参考文档链接

- 检查特定区域是否支持该资源，返回固定答案：**terraform不区分区域**

- 判断某个字段是否被支持，直接返回参考文档链接

- 判断某个resource/data_source是否已被 terraform 支持

- 判断某个API是否已被 terraform 支持

- 判断用户的需求是否被resource/data_source支持
</ability>

<critical_reminders>
- 请严格根据“参考上下文”作答。禁止捏造和推理
- 仅使用上下文中明确给出的事实、数字和时间，不得添加上下文中不存在的信息
- 如果信息不充分，只需回答“我无法回答。请咨询人工服务"
- 当你有足够信息回答时，必须直接严格按照steps步骤执行，并输出最终答案，严禁再调用任何工具或生成额外的Thought或todos
- 你要严格按照steps步骤完成任务，只执行一次，不要循环执行
</critical_reminders>

<steps>
1. 从params中获取请求参数，根据意图，选择合适的工具去查询，如果是要搜做资源内容，那么选择工具按照以下规则：
    - 如果 intent 值为 query_resource_by_name，那么要使用工具 resource_search_tool
    - 如果 intent 值为 query_resource_by_api，那么要使用工具 api_search_tool
    - 如果 intent 值为 query_resource_by_content，那么要使用工具 rag_search_tool

2. 通过read_md工具获取详细文档信息

3. 根据查询结果，总结结论并回复
</steps>

<response_style>
- 清晰简洁：除非有要求，否则避免过度格式化
- 自然语气：默认使用段落和散文，而不是要点
- 以行动为导向：专注于交付结果，也给出解释流程
- 如果是查询资源，应同时返回官方文档链接
</response_style>
"""

def get_memory_context(user_id: str) -> str | None:
    """Get memory context for injection into system prompt.

    Args:
        agent_name: If provided, loads per-agent memory. If None, loads global memory.

    Returns:
        Formatted memory context string wrapped in XML tags, or empty string if disabled.
    """
    try:
        config = get_agent_config()
        if not config.user_memory:
            return None

        memory_data = get_memory_data(user_id=user_id)
        memory_content = format_memory_for_injection(memory_data, max_tokens=config.max_injection_tokens)

        if not memory_content.strip():
            return ""

        return f"""<memory>
{memory_content}
</memory>
"""
    except Exception as e:
        logger.error("Failed to load memory context: %s", e)
        return ""

def get_agent_soul() -> str:
    soul = """
    你回答问题时并且必须严格遵守以下规则：、
    1. 所有答案必须100%来自所提供的参考文件和上下文；请勿捏造文件中未包含的信息。
    2、如果文档中没有答案，则直接回复：“现有参考资料中没有该问题的信息，无法回答。”
    3. 不得推测、假设、补充外部常识、捏造数字、日期或专有名词。
    4. 尽可能引用每个关键结论的来源（具体文件摘录）。
    5. 不要混淆不同文档的内容或构建不存在的逻辑联系。
    6. 不得简化或改变原始数据、参数或过程描述。
    """
    if soul:
        return f"<soul>\n{soul}\n</soul>\n"
    return ""

def apply_prompt_template(
    user_id: str,
    agent_name: str | None = None,
) -> str:
    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        agent_name=agent_name or "Terraform oncall agent",
        soul=get_agent_soul(),
        # memory_context=get_memory_context(user_id),
    )

    return prompt