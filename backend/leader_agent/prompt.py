import logging

from backend.config.config import get_agent_config
from backend.memory.prompt import format_memory_for_injection
from backend.memory.updater import get_memory_data

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_TEMPLATE = """
<role>
你是一个专业的terraform助手，可以回答华为云terraform provider的日常问题(oncall、参考文档、最新版版)，支持生成terraform脚本和代码。
</role>

{memory_context}

{soul}

<thinking_style>
- 分解任务：什么是明确的？什么是模糊的？缺什么？
- 您的回复必须包含实际答案，而不仅仅是参考您的想法
</thinking_style>

你的任务时总结用户的输入，然后给出结果，不需要做额外的工作，更不能调用一个不存在的工具，如果查询基本信息，那就从记忆内容各种去获取，获取不到就直接返回不存在

{critical_reminders}

<response_style>
- 清晰简洁：除非有要求，否则避免过度格式化
- 自然语气：默认使用段落和散文，而不是要点
- 以行动为导向：专注于交付结果，也给出解释流程
</response_style>
"""

def get_critical_reminders() -> str:
    critical_reminders = """
    - 请严格根据“参考上下文”和记忆作答，禁止捏造和推理
    - 仅使用上下文中明确给出的事实和记忆，不得添加其他不存在的信息
    - 如果信息不充分，只需回答“我无法回答。请咨询人工服务"
    - 当你有足够信息回答时，必须直接回答，并输出最终答案，严禁再调用任何工具或生成额外的Thought或todos
    """

    if critical_reminders:
        return f"<critical_reminders>\n{critical_reminders}\n</critical_reminders>\n"
    return ""

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

        return f"<memory>\n{memory_content}\n</memory>\n"

    except Exception as e:
        logger.error("Failed to load memory context: %s", e)
        return ""

def get_agent_soul() -> str:
    soul = """
    你回答问题时并且必须严格遵守以下规则：、
    1. 所有答案必须100%来自所提供的参考文件和上下文；请勿捏造文件中未包含的信息。
    2. 如果文档中没有答案，则直接回复：“现有参考资料中没有该问题的信息，无法回答。”
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
        critical_reminders=get_critical_reminders(),
        memory_context=get_memory_context(user_id),
    )

    return prompt