from langchain_chroma import Chroma
from langchain_core.documents import Document

from backend.config.config import get_agent_config
from backend.model import get_model
from backend.rag.chroma_manager import add_docs_to_chroma, similarity_search_docs_with_score_from_chroma, get_chroma_client
from backend.rag.doc_manager import load_document_descriptions

def add_doc_to_chromadb(client: Chroma):
    services = ["gaussdb", "rds", "dds", "compute", "geminidb", "taurusdb", "elb", "dcs", "ddm", "elb", "vpc", "cce",
                "dns", "dms_kafka", "dms_rocketmq", "dms_rabbitmq", "vpn", "evs", "dc", "smn", "compute"]
    for service in services:
        add_docs = load_document_descriptions(service)
        print(f"{service}: {len(add_docs)}")

        # 保存数据
        add_docs_to_chroma(client, add_docs)

def similarity_search_from_chromadb(client: Chroma, query:str, query_size: int) -> list[tuple[Document, float]]:
    search_res = similarity_search_docs_with_score_from_chroma(client, query, query_size=query_size)
    # final_res = [doc for doc in search_res if doc[1] > 0.5]
    search_res = sorted(search_res, key=lambda x: x[1], reverse=True)
    return search_res

if __name__ == '__main__':

    # docs = load_document_descriptions("rds")
    # print(docs[:5])

    embedding_model = get_model(get_agent_config().embedding_model_type)
    client = get_chroma_client(embedding_model)

    # add_doc_to_chromadb(client)

    query = "Manager ECS instance"
    res = similarity_search_from_chromadb(client, query, 10)
    for doc in res:
        print("===========================")
        # print(doc)
        print(f"res={doc[0]}")
        print(f"id={doc[0].id}")
        print(f"score={doc[1]}")
