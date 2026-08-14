from langchain_core.tools import tool

from backend.utils.github_utils import TERRAFORM_CODE_PATH

@tool
def read_md(resource_type: str, resource_name:str) -> str:
    """
    used to get the resource info by resource_type and resource_name
    triggered when get the resource info by resource_type and resource_name

    :param resource_type:  the type of resource
    :param resource_name: the name of the resource
    :return: the info of the resource info
    """
    file_name = resource_name.replace('huaweicloud_', '')
    file_path = "docs/{resource_type}/{file_name}.md"
    if resource_type == "data_source":
        file_path = file_path.replace("{resource_type}", "data-sources")
        file_path = file_path.replace("{file_name}", file_name)
    elif resource_type == "resource":
        file_path = file_path.replace("{resource_type}", "resources")
        file_path = file_path.replace("{file_name}", file_name)
    else:
        return "resource type error"

    try:
        with open(TERRAFORM_CODE_PATH / file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return f"error：file {file_path} not exist"
    except Exception as e:
        return f"error: read file {file_path} error: {e}"

    return content
