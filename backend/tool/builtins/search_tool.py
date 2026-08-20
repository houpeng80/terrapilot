from langchain_core.tools import tool, ToolException

from backend.utils.github_utils import get_latest_version, checkout_code, list_file, search_resource_by_key_word
from backend.rag.rag_manager import rag_keyword_search

@tool
def resource_search_tool(service_name: str, resource_type: str, resource_name: str) -> bool:
    """ this tool is used to check whether the resource/data_source is exist or not,
    triggered only when check whether the resource/data_source is exist or not"""

    service_name = service_name.lower()
    resource_name = resource_name.lower()
    resource_type = resource_type.lower()
    success, err_msg = resource_param_check(service_name, resource_type, resource_name)
    if not success:
        raise ValueError(err_msg)

    try:
        # 查询最新版本
        version = get_latest_version()
        # 切换到最新的tag
        checkout_code(version)
        # 查询
        file_list = list_file(f"huaweicloud/services/{service_name}/")
        if f"{resource_type}_{resource_name}.go" in file_list:
            return True
        # 如果不存在就切换到master
        checkout_code("master")
        # 查询
        file_list = list_file(f"huaweicloud/services/{service_name}/")
        if f"{resource_type}_{resource_name}.go" in file_list:
            return True
        return False
    except Exception as err:
        raise ToolException(err)

def resource_param_check(service_name: str, resource_type: str, resource_name: str) -> tuple[bool, str]:
    if not service_name:
        return False, "service_name is empty"
    if resource_type not in ["resource", "data_source"]:
        return False, "resource_type is invalid"
    if not resource_name:
        return False, "resource_name is empty"
    if not resource_name.startswith("huaweicloud_"):
        return False, "resource_name should start with `huaweicloud_`"
    return True, "success"

@tool
def api_search_tool(service_name: str, api_method: str, api_url: str) -> list[str] | None:
    """ this tool is used to get the resource and data_source which has support the API,
    triggered only when get the resource and data_source which has support the API"""

    service_name = service_name.lower()
    api_method = api_method.lower()
    api_url = api_url.lower()

    success, err_msg = api_param_check(service_name, api_method, api_url)
    if not success:
        raise ValueError(err_msg)

    try:
        # 查询最新版本
        version = get_latest_version()
        # 切换到最新的tag
        checkout_code(version)
        # 查询
        names = search_resource_by_key_word(f"// @API {service_name} {api_method} {api_url}", f"huaweicloud/services/{service_name}")
        if len(names) > 0:
            return [f"{service_name}_{name}" for name in names]
        # 如果不存在就切换到master
        checkout_code("master")
        # 查询
        names = search_resource_by_key_word(f"// @API {service_name} {api_method} {api_url}",f"huaweicloud/services/{service_name}")
        if len(names) > 0:
            return [f"{service_name}_{name}" for name in names]
        return None
    except Exception as err:
        raise ToolException(err)

def api_param_check(service_name: str, api_method: str, api_url: str) -> tuple[bool, str]:
    if not service_name:
        return False, "service_name is empty"
    if not api_method:
        return False, "api_method is empty"
    if not api_url:
        return False, "api_url is empty"
    return True, "success"

@tool
def rag_search_tool(resource_type: str, content: str) -> list[str]:
    """ this tool is used to get the related resource/data_source info by resource_type and context,
    triggered only when get the related resource/data_source info by resource_type and context"""

    resource_type = resource_type.lower()
    success, err_msg = rag_search_param_check(resource_type)
    if not success:
        raise ValueError(err_msg)

    query = ""
    if resource_type == "resource":
        query = f"Manager {content} resource"
    if resource_type == "data_source":
        query = f"Use this data source to get {content}"

    return rag_keyword_search(query, top_k=3)

def rag_search_param_check(resource_type: str) -> tuple[bool, str]:
    if not resource_type:
        return False, "resource_type is empty"
    return True, "success"

if "__main__" == __name__:
    res = resource_search_tool("RDS", "resource", "huaweicloud_rds_notify_replace_node")
    print(res)