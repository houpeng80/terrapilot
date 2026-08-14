BUILTIN_SUB_AGENTS = [
]

SUB_AGENT_CONTAIN_INTENTS = {
    "oncall_agent" : [
        "query_oncall",
        "query_reference_docs",
        "query_latest_version",
        "whether_support_special_region",
        "query_resource_by_name"
        "query_resource_by_api"
        "query_resource_by_content"
    ],
    "generate_script" : [
        "script_generate_agent"
    ],
    "generate_code" : [
        "code_generate_agent"
    ]
}