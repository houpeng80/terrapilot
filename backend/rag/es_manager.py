import warnings
from datetime import datetime

from elasticsearch import Elasticsearch, helpers, ElasticsearchWarning
from langchain_core.documents import Document

from assistant.config.config import get_app_config

warnings.filterwarnings("ignore", category=ElasticsearchWarning)

def create_es_client(address:str=get_app_config().es_address) -> Elasticsearch:
    return Elasticsearch(
        address,
        request_timeout=30
    )

def create_index(client: Elasticsearch):
    if client.indices.exists(index=get_app_config().es_index):
        print(f"index {get_app_config().es_index} has exists，skip creating")
        return

    index_mapping = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "analyzer": {
                    "ik_cn": {
                        "tokenizer": "ik_smart",
                        "filter": ["lowercase"]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "chunk_id": {"type": "keyword"},
                "source": {"type": "keyword"},
                "title": {
                    "type": "text",
                    "analyzer": "ik_cn",
                    "fields": {"kw": {"type": "keyword", "ignore_above": 256}}
                },
                "content": {"type": "text", "analyzer": "ik_cn"},
                "file_type": {"type": "keyword"},
                "chunk_index": {"type": "integer"},
                "update_time": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss"},
            }
        }
    }
    client.indices.create(index=get_app_config().es_index, body=index_mapping)
    print(f"index {get_app_config().es_index} create successful")

def build_es_bulk_actions(documents: list[tuple[str, Document]]) -> list[dict]:
    actions =[]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for index, document in enumerate(documents):
        chunk_id = document[0]
        doc = document[1]
        source = doc.metadata["source"]

        action = {
            "_index": get_app_config().es_index,
            "_id": chunk_id,  # ES文档id直接使用chunk_id，方便更新删除
            "_source": {
                "chunk_id": chunk_id,
                "source": source,
                "title": "",  # 如需提取标题可自行解析md填充
                "content": doc.page_content.strip(),
                "file_type": doc.metadata["file_type"],
                "chunk_index": index,
                "update_time": now,
            }
        }
        actions.append(action)
    return actions

def bulk_insert_es(client: Elasticsearch, documents: list[tuple[str, Document]]):
    if not documents:
        print("无有效分片，跳过写入")
        return

    batch_size = 10
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        actions = build_es_bulk_actions(batch)
        # helpers.bulk 高性能批量写入
        success, fail = helpers.bulk(
            client=client,
            actions=actions,
            stats_only=True
        )
        print(f"ES批量写入完成：成功{success}条，失败{fail}条")

def es_keyword_search(client: Elasticsearch, query: str, top_k: int = 10) -> list[tuple[Document, float]]:
    """ES全文关键词检索，返回chunk_id、content、得分"""
    dsl = {
        "size": top_k,
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["title^2", "content"],
                "analyzer": "ik_smart"
            }
        }
    }
    resp = client.search(index=get_app_config().es_index, body=dsl)
    result_list : list[tuple[Document, float]] = []
    for hit in resp["hits"]["hits"]:
        src = hit["_source"]
        doc = Document(
            id=src["chunk_id"],
            page_content = src["content"]
        )
        result_list.append((doc, hit["_score"]))
    return result_list
