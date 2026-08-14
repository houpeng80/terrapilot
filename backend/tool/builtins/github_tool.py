from langchain_core.tools import tool

from backend.utils.github_utils import get_latest_version


@tool
def get_latest_provider_version()->str:
    """
    used to get the latest huaweicloud terraform provider latest version
    triggered only when get the latest huaweicloud terraform provider latest version
    :return:
    """
    version = get_latest_version()
    return version