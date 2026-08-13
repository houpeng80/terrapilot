from assistant.rag.doc_manager import load_documents, split_markdown_file, get_markdown_file_description

def load_docs():
    # "gaussdb", "rds", "dds", "compute", "geminidb", "taurusdb", "elb", "dcs", "ddm", "elb", "vpc", "cce", "dns", "dms_kafka", "dms_rocketmq", "dms_rabbitmq" "vpn"
    services = ["dms_rabbitmq", "vpn"]
    res = []
    for service in services:
        add_docs = load_documents(service)
        print(f"{service}: {len(add_docs)}")
        res = res + add_docs
    return res

def split_md_file(folder: str, file_name: str, resource_type: str):
    res = split_markdown_file(folder, file_name, resource_type)
    print(res)

def get_markdown_description(folder: str, file_name: str, resource_type: str):
    res = get_markdown_file_description(folder, file_name, resource_type)
    print(res)

if __name__ == '__main__':

    get_markdown_description("docs/resources", "rds_backup.md", "resource")