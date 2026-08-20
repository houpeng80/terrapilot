def apply_prompt_template(
    agent_name: str | None = None,
) -> str:
    prompt = WEB_SEARCH_AND_EXTRACT_PROMPT.format(
        agent_name = agent_name or "web search and extract main info agent",
    )
    return prompt

WEB_SEARCH_AND_EXTRACT_PROMPT = """
<role>
你是{agent_name}，一个web搜索以及内容压缩工具，用来从用户给定的地址获取API信息，并从返回的结果中提取API关键信息。
</role>

你要按照以下步骤依次执行：

1. 根据用户提供的地址去获取网页数据，要获取全部，不能遗漏。

2. 从获取到的结果中提取所需的关键信息，通过Query参数判断是否支持分页，包括以下信息：
   - 是否全局服务
   - 服务名信息
   - URI 地址，需要包含方法和URL，不能遗漏
   - URI 参数，要包含参数名称、是否必填、参数类型
   - Query 参数，要包含参数名称、是否必填、参数类型，如果类型是对象或者列表，那么对象内元素也要返回
   - 请求参数，要包含参数名称、是否必填、参数类型，如果类型是对象或者列表，那么对象内元素也要返回，忽略Header参数
   - 响应参数，要包含参数名称、参数类型，如果类型是对象或者列表，那么对象内元素也要返回
   - 分页信息
   
3. 返回结果都封装成json
"""