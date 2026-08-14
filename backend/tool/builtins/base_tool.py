from langchain_core.tools import tool

@tool
def oncall_schedule()->str:
    """ this tool is used to get the on-call personnel info,
    triggered only when querying on-call information"""
    return "https://onebox.huawei.comv/v/29f3e6bf2c40905380d59c25b09387?type=0"

@tool
def reference_docs()->str:
    """ this tool is used to get huaweicloud terraform provider reference docs,
    Triggered only when querying the provider reference docs"""
    return "https://registry.terraform.io/providers/huaweicloud/huaweicloud/latest/docs"