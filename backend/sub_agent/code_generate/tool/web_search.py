import vipertls

from langchain.tools import tool

@tool
def web_search(url: str):
    """从指定url地址查询所需要的数据。
    当需要根据api地址获取网页信息时触发。

    Args:
        url: 要查询的地址
    """
    client = vipertls.Client(impersonate="chrome_145", timeout=30)
    response = client.get(url)
    return response.text
    # return response.content.decode('utf-8')
