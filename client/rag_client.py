from backend.config.config import get_agent_config
from backend.model import get_model
from backend.rag.chroma_manager import get_chroma_client
from backend.rag.es_manager import create_es_client, es_keyword_search
from backend.rag.rag_manager import reciprocal_rank_fusion_with_docs, rag_keyword_search
from backend.tool.builtins.search_tool import rag_search_tool
from client.chroma_client import similarity_search_from_chromadb

def get_reciprocal_rank_fusion_with_docs():
    embedding_model = get_model(get_agent_config().embedding_model_type)
    chroma_client = get_chroma_client(embedding_model)
    es_client = create_es_client()

    chroma_res = similarity_search_from_chromadb(chroma_client, query, 30)
    es_res = es_keyword_search(es_client, query, 30)

    merged = reciprocal_rank_fusion_with_docs(chroma_res + es_res)
    for merge in merged:
        print("==============")
        print(merge)
        print("==============")

if "__main__" == __name__:
    query = "Manager ECS instance"

    # embedding_model = get_model(get_agent_config().embedding_model_type)
    # chroma_client = get_chroma_client(embedding_model)
    # es_client = create_es_client()
    # chroma_res = similarity_search_from_chromadb(chroma_client, query, 10)
    # es_res = es_keyword_search(es_client, query, 10)
    #
    # rrf_res = reciprocal_rank_fusion_with_docs(chroma_res, es_res, 0.5, 0.5)
    # for rr in rrf_res:
    #     print("==============")
    #     print(rr)


    rerank_res = rag_keyword_search(query, 10)
    for rr in rerank_res:
        print("==============")
        print(rr)

    # rerank_res = rag_search_tool("resource", query)
    # print(rerank_res)
    # for rr in rerank_res:
    #     print("==============")
    #     print(rr)
