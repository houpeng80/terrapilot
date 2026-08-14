from elasticsearch import Elasticsearch

from backend.rag.doc_manager import load_documents
from backend.rag.es_manager import bulk_insert_es, create_es_client, es_keyword_search


def add_doc_to_es(client: Elasticsearch):
    # "gaussdb", "rds", "dds", "compute", "geminidb", "taurusdb", "elb", "dcs", "ddm", "elb", "vpc", "cce", "dns", "dms_kafka", "dms_rocketmq", "dms_rabbitmq", "vpn"
    services = ["gaussdb", "rds", "dds", "compute", "geminidb", "taurusdb", "elb", "dcs", "ddm", "elb", "vpc", "cce", "dns", "dms_kafka", "dms_rocketmq", "dms_rabbitmq", "vpn"]
    for service in services:
        add_docs = load_documents(service)
        print(f"{service}: {len(add_docs)}")

        # 保存数据
        bulk_insert_es(client, add_docs)

if __name__ == '__main__':
    es_client = create_es_client()

    # res = es_client.indices.exists(index=get_agent_config().es_index)
    # print(res)

    # create_index(client=es_client)

    # add_doc_to_es(es_client)

    query = "Manager RDS backup"
    final_res = es_keyword_search(es_client, query, top_k=10)
    for res in final_res:
        print("===========")
        print(res)
        print("===========")
